#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::net::TcpStream;
use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tauri::Manager;

const FLASK_PORT: u16 = 5174;
const FLASK_URL: &str = "http://127.0.0.1:5174";

// ── Path resolution ──────────────────────────────────────────────────────────

fn repo_root() -> PathBuf {
    // When running `pnpm tauri dev` from app/, cwd = app/
    // Repo root = parent of app/
    let cwd = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    cwd.parent().map(|p| p.to_path_buf()).unwrap_or(cwd)
}

fn python_exe(root: &PathBuf) -> PathBuf {
    let venv = root.join(".venv").join("bin").join("python");
    if venv.exists() { venv } else { PathBuf::from("python3") }
}

fn main_py(root: &PathBuf) -> PathBuf {
    root.join("src").join("main.py")
}

/// Resolve how to spawn the backend server.
///
/// Two modes:
///
/// DEV  (debug build): spawn Python from the local venv + src/main.py
///      This is what `pnpm tauri dev` uses — fast iteration, no bundling.
///
/// PROD (release build): use the bundled `samplemind-server` sidecar binary
///      produced by PyInstaller. No Python installation required on the user's machine.
///      Tauri puts sidecar binaries next to the app executable.
///
/// Returns (executable, optional_script_arg)
fn resolve_server(app: &tauri::AppHandle) -> (PathBuf, Option<PathBuf>) {
    #[cfg(debug_assertions)]
    {
        // Debug: use venv python + src/main.py
        let root = repo_root();
        (python_exe(&root), Some(main_py(&root)))
    }
    #[cfg(not(debug_assertions))]
    {
        // Release: use the PyInstaller sidecar bundled with the app
        let binary = app
            .path()
            .resolve("binaries/samplemind-server", tauri::path::BaseDirectory::Resource)
            .unwrap_or_else(|_| PathBuf::from("samplemind-server"));
        (binary, None)
    }
}

// ── Port polling ─────────────────────────────────────────────────────────────

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

fn set_status(window: &tauri::WebviewWindow, msg: &str) {
    let safe = msg.replace('\\', "\\\\").replace('\'', "\\'");
    let _ = window.eval(&format!(
        "document.getElementById('status') && (document.getElementById('status').textContent = '{safe}')"
    ));
}

// ── Tauri command: native folder picker ─────────────────────────────────────

/// Opens a native OS folder-picker dialog and returns the selected path.
///
/// Called from JavaScript via:
///   const path = await window.__TAURI__.core.invoke('pick_folder')
///
/// Returns null if the user cancels. Returns a string path if they pick a folder.
/// The JS then POSTs this path to Flask /api/import.
#[tauri::command]
fn pick_folder(app: tauri::AppHandle) -> Option<String> {
    use tauri_plugin_dialog::DialogExt;

    // blocking_pick_folder() opens the OS dialog and blocks until
    // the user picks a folder or dismisses the dialog.
    // This is safe to call here because Tauri runs commands on a thread pool,
    // not the main UI thread.
    app.dialog()
        .file()
        .blocking_pick_folder()
        .map(|path| path.to_string())
}

// ── Tauri command: path info ─────────────────────────────────────────────────

/// Check if a path is a directory.
/// Called from JS after a drag-drop to decide whether to use /api/import
/// (folder) or /api/import-files (list of WAV paths).
///
/// JS can't access the filesystem directly — it has to ask Rust.
#[tauri::command]
fn is_directory(path: String) -> bool {
    std::path::Path::new(&path).is_dir()
}

// ── System tray ──────────────────────────────────────────────────────────────

fn setup_tray(app: &tauri::App) -> tauri::Result<()> {
    use tauri::menu::{Menu, MenuItem};
    use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};

    // Build the right-click context menu
    let show_item = MenuItem::with_id(app, "show",  "Show SampleMind AI", true, None::<&str>)?;
    let sep       = tauri::menu::PredefinedMenuItem::separator(app)?;
    let quit_item = MenuItem::with_id(app, "quit",  "Quit",               true, None::<&str>)?;

    let menu = Menu::with_items(app, &[&show_item, &sep, &quit_item])?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .tooltip("SampleMind AI")
        .menu(&menu)
        // Right-click menu item handler
        .on_menu_event(|app, event| {
            match event.id.as_ref() {
                "show" => show_main_window(app),
                "quit" => app.exit(0),
                _ => {}
            }
        })
        // Left-click on the tray icon toggles the window
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event {
                show_main_window(tray.app_handle());
            }
        })
        .build(app)?;

    Ok(())
}

fn show_main_window(app: &tauri::AppHandle) {
    if let Some(win) = app.get_webview_window("main") {
        win.show().ok();
        win.set_focus().ok();
    }
}

// ── Main ──────────────────────────────────────────────────────────────────────

fn main() {
    let server: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));
    let server_setup = Arc::clone(&server);
    let server_close = Arc::clone(&server);

    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())   // register the dialog plugin
        .invoke_handler(tauri::generate_handler![pick_folder, is_directory])
        .setup(move |app| {
            // ── System tray ───────────────────────────────────────────────
            setup_tray(app)?;

            // ── Flask server ──────────────────────────────────────────────
            let window = app.get_webview_window("main")
                .expect("window 'main' not found");
            window.show()?;

            let win        = window.clone();
            let app_handle = app.handle().clone();
            std::thread::spawn(move || {
                let (exe, script) = resolve_server(&app_handle);

                // In dev mode, verify main.py exists before spawning
                if let Some(ref s) = script {
                    if !s.exists() {
                        set_status(&win, "❌ main.py not found — check repo structure");
                        return;
                    }
                }

                set_status(&win, "Starting Python server…");
                eprintln!("[SampleMind] Spawning: {:?} serve --port {}", exe, FLASK_PORT);

                let mut cmd = Command::new(&exe);
                if let Some(ref s) = script {
                    cmd.arg(s);
                }
                let child = cmd
                    .arg("serve")
                    .arg("--port")
                    .arg(FLASK_PORT.to_string())
                    .spawn();

                match child {
                    Err(e) => {
                        set_status(&win, &format!("❌ Failed to start Python: {e}"));
                    }
                    Ok(proc) => {
                        if let Ok(mut lock) = server_setup.lock() {
                            *lock = Some(proc);
                        }
                        set_status(&win, "Waiting for server…");
                        if wait_for_port(FLASK_PORT, 30) {
                            set_status(&win, "Ready!");
                            let _ = win.eval(&format!(
                                "window.location.replace('{FLASK_URL}')"
                            ));
                        } else {
                            set_status(&win, "❌ Server timed out after 30s");
                        }
                    }
                }
            });

            Ok(())
        })
        // Hide the window on close instead of quitting — use tray to quit
        .on_window_event(move |window, event| {
            match event {
                tauri::WindowEvent::CloseRequested { api, .. } => {
                    // Prevent default close behaviour (which would exit the app)
                    api.prevent_close();
                    window.hide().ok();
                }
                tauri::WindowEvent::Destroyed => {
                    // Window is truly gone — kill Flask
                    if let Ok(mut lock) = server_close.lock() {
                        if let Some(mut child) = lock.take() {
                            let _ = child.kill();
                            let _ = child.wait();
                        }
                    }
                }
                _ => {}
            }
        })
        .run(tauri::generate_context!())
        .expect("error running tauri application");
}
