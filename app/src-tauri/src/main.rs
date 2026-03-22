// Hides the Windows console window in release builds.
// Has no effect on Linux/macOS — safe to leave here.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tauri::Manager;

/// The port Flask will listen on. Using 5174 avoids conflicts with
/// common dev tools (5173 = Vite, 5000 = common Flask default).
const FLASK_PORT: u16 = 5174;
const FLASK_URL: &str = "http://127.0.0.1:5174";

// ── Path resolution ──────────────────────────────────────────────────────────

/// Find the repo root by walking up from the `app/` directory.
///
/// Dev layout:
///   SampleMind-AI/
///   ├── .venv/bin/python
///   ├── src/main.py
///   └── app/         ← `tauri dev` is run from here (cwd)
///
/// So repo root = parent of current working directory.
fn repo_root() -> PathBuf {
    let cwd = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    // cwd is app/  →  parent is SampleMind-AI/
    cwd.parent()
        .map(|p| p.to_path_buf())
        .unwrap_or(cwd)
}

fn python_exe(root: &PathBuf) -> PathBuf {
    let venv = root.join(".venv").join("bin").join("python");
    if venv.exists() {
        venv
    } else {
        PathBuf::from("python3") // fall back to system Python
    }
}

fn main_py(root: &PathBuf) -> PathBuf {
    root.join("src").join("main.py")
}

// ── Port polling ─────────────────────────────────────────────────────────────

/// Block until port is accepting TCP connections, or timeout_secs passes.
/// Uses std::net::TcpStream — no HTTP library needed.
fn wait_for_port(port: u16, timeout_secs: u64) -> bool {
    let addr = format!("127.0.0.1:{}", port);
    let deadline = Instant::now() + Duration::from_secs(timeout_secs);
    while Instant::now() < deadline {
        if TcpStream::connect(&addr).is_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    false
}

// ── Loading screen ───────────────────────────────────────────────────────────

/// Update the status text on the loading screen.
/// Called from the background thread via window.eval().
fn set_status(window: &tauri::WebviewWindow, msg: &str) {
    let js = format!(
        "document.getElementById('status') && (document.getElementById('status').textContent = '{}')",
        msg.replace('\'', "\\'")
    );
    let _ = window.eval(&js);
}

// ── Main entry point ─────────────────────────────────────────────────────────

fn main() {
    // Arc<Mutex<Option<Child>>> lets us share the Python process handle
    // between the setup thread (which creates it) and the window-close
    // handler (which needs to kill it).
    //
    // Arc  = reference-counted pointer, safe to clone across threads
    // Mutex = mutual-exclusion lock, ensures only one thread touches the child at a time
    // Option<Child> = Some(child) while running, None before start or after kill
    let server: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));

    let server_setup = Arc::clone(&server);
    let server_close = Arc::clone(&server);

    tauri::Builder::default()
        .setup(move |app| {
            let window = app.get_webview_window("main")
                .expect("window 'main' not found — check tauri.conf.json");

            // Show the window with a loading screen right away so the
            // user sees something while Python starts up.
            window.show().ok();

            // Clone the window handle so we can use it inside the thread.
            // Tauri WebviewWindow implements Clone and is Send + Sync.
            let win = window.clone();

            std::thread::spawn(move || {
                let root   = repo_root();
                let python = python_exe(&root);
                let script = main_py(&root);

                // Validate paths before trying to spawn
                if !script.exists() {
                    set_status(&win, "❌ main.py not found. Is the repo structure intact?");
                    eprintln!("[SampleMind] main.py not found at {:?}", script);
                    return;
                }

                set_status(&win, "Starting Python server…");
                eprintln!("[SampleMind] Spawning: {:?} {:?} serve --port {}", python, script, FLASK_PORT);

                // Spawn Flask. Command::new() creates a new child process.
                // The child inherits stdout/stderr so server logs appear in
                // the terminal where you ran `tauri dev`.
                let child = Command::new(&python)
                    .arg(&script)
                    .arg("serve")
                    .arg("--port")
                    .arg(FLASK_PORT.to_string())
                    .spawn();

                match child {
                    Err(e) => {
                        let msg = format!("❌ Failed to start Python: {}", e);
                        set_status(&win, &msg);
                        eprintln!("[SampleMind] {}", msg);
                    }
                    Ok(proc) => {
                        // Store the child process handle for cleanup on exit.
                        if let Ok(mut lock) = server_setup.lock() {
                            *lock = Some(proc);
                        }

                        set_status(&win, "Waiting for server to be ready…");

                        // Poll TCP port 5174 — blocks until Flask is accepting connections.
                        if wait_for_port(FLASK_PORT, 30) {
                            set_status(&win, "Ready! Loading UI…");
                            // Navigate the webview to the Flask web UI.
                            // window.navigate() would be cleaner but eval() works in all Tauri versions.
                            let _ = win.eval(&format!(
                                "window.location.replace('{}')",
                                FLASK_URL
                            ));
                        } else {
                            set_status(&win, "❌ Server timed out after 30 seconds.");
                            eprintln!("[SampleMind] Flask server failed to start within 30s on port {}", FLASK_PORT);
                        }
                    }
                }
            });

            Ok(())
        })
        // Kill Python when the main window is closed.
        // CloseRequested fires before the window actually closes.
        .on_window_event(move |_window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                if let Ok(mut lock) = server_close.lock() {
                    if let Some(mut child) = lock.take() {
                        eprintln!("[SampleMind] Shutting down Python server…");
                        let _ = child.kill();
                        let _ = child.wait(); // reap the zombie process
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error running tauri application");
}
