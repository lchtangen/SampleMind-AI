/// commands.rs — All Tauri IPC commands for SampleMind AI.
///
/// Every function tagged `#[tauri::command]` here must also be registered in:
///   - `main.rs` → `.invoke_handler(tauri::generate_handler![...])`
///   - `capabilities/default.json` (custom commands are allowed by `core:default`)

use crate::state::AuthTokenStore;

// ── File system commands ──────────────────────────────────────────────────────

/// Open the native OS folder-picker dialog and return the selected path.
///
/// Returns `None` if the user cancels the dialog.
/// JS: `const path = await invoke("pick_folder")`
#[tauri::command]
pub fn pick_folder(app: tauri::AppHandle) -> Option<String> {
    use tauri_plugin_dialog::DialogExt;
    app.dialog()
        .file()
        .blocking_pick_folder()
        .map(|p| p.to_string())
}

/// Return `true` if the given path is a directory.
///
/// Used after drag-drop to route to `/api/import` vs `/api/import-files`.
/// JS: `const isDir = await invoke("is_directory", { path })`
#[tauri::command]
pub fn is_directory(path: String) -> bool {
    std::path::Path::new(&path).is_dir()
}

// ── JWT token bridge commands ─────────────────────────────────────────────────
//
// These three commands let the Svelte/JS frontend pass the FastAPI JWT token
// into Rust process memory so future native Rust→FastAPI calls can include it.

/// Store the JWT access token in process memory.
///
/// Call after a successful FastAPI `/api/v1/auth/login` response.
#[tauri::command]
pub fn store_token(
    token: String,
    state: tauri::State<'_, AuthTokenStore>,
) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|e| e.to_string())?;
    *guard = Some(token);
    Ok(())
}

/// Retrieve the stored JWT access token.
///
/// Returns `None` if no token has been stored (user not logged in via FastAPI).
#[tauri::command]
pub fn get_token(state: tauri::State<'_, AuthTokenStore>) -> Result<Option<String>, String> {
    let guard = state.0.lock().map_err(|e| e.to_string())?;
    Ok(guard.clone())
}

/// Clear the stored JWT token (call on logout).
#[tauri::command]
pub fn clear_token(state: tauri::State<'_, AuthTokenStore>) -> Result<(), String> {
    let mut guard = state.0.lock().map_err(|e| e.to_string())?;
    *guard = None;
    Ok(())
}
