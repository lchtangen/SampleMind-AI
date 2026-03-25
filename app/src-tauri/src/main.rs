#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod state;

use commands::{clear_token, get_token, is_directory, pick_folder, store_token};
use state::AuthTokenStore;

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
        let root = repo_root();
        (python_exe(&root), Some(main_py(&root)))
    }
    #[cfg(not(debug_assertions))]
    {
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

// ── System tray ──────────────────────────────────────────────────────────────

fn setup_tray(app: &tauri::App) -> tauri::Result<()> {
    use tauri::menu::{Menu, MenuItem};
    use tauri::tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent};

    let show_item = MenuItem::with_id(app, "show", "Show SampleMind AI", true, None::<&str>)?;
    let sep       = tauri::menu::PredefinedMenuItem::separator(app)?;
    let quit_item = MenuItem::with_id(app, "quit", "Quit",               true, None::<&str>)?;

    let menu = Menu::with_items(app, &[&show_item, &sep, &quit_item])?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .tooltip("SampleMind AI")
        .menu(&menu)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => show_main_window(app),
            "quit" => app.exit(0),
            _      => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
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
        .plugin(tauri_plugin_dialog::init())
        // Register all IPC commands — must match capabilities/default.json
        .invoke_handler(tauri::generate_handler![
            pick_folder,
            is_directory,
            store_token,
            get_token,
            clear_token,
        ])
        .manage(AuthTokenStore::default())
        .setup(move |app| {
            setup_tray(app)?;

            let window = app
                .get_webview_window("main")
                .expect("window 'main' not found");
            window.show()?;

            let win        = window.clone();
            let app_handle = app.handle().clone();
            std::thread::spawn(move || {
                let (exe, script) = resolve_server(&app_handle);

                if let Some(ref s) = script {
                    if !s.exists() {
                        set_status(&win, "main.py not found -- check repo structure");
                        return;
                    }
                }

                set_status(&win, "Starting Python server...");
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
                        set_status(&win, &format!("Failed to start Python: {e}"));
                    }
                    Ok(proc) => {
                        if let Ok(mut lock) = server_setup.lock() {
                            *lock = Some(proc);
                        }
                        set_status(&win, "Waiting for server...");
                        if wait_for_port(FLASK_PORT, 30) {
                            set_status(&win, "Ready!");
                            let _ = win.eval(&format!(
                                "window.location.replace('{FLASK_URL}')"
                            ));
                        } else {
                            set_status(&win, "Server timed out after 30s");
                        }
                    }
                }
            });

            Ok(())
        })
        .on_window_event(move |window, event| match event {
            tauri::WindowEvent::CloseRequested { api, .. } => {
                api.prevent_close();
                window.hide().ok();
            }
            tauri::WindowEvent::Destroyed => {
                if let Ok(mut lock) = server_close.lock() {
                    if let Some(mut child) = lock.take() {
                        let _ = child.kill();
                        let _ = child.wait();
                    }
                }
            }
            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("error running tauri application");
}
