//! commands.rs — All Tauri IPC commands for SampleMind AI.
//!
//! Every function tagged `#[tauri::command]` here must also be registered in:
//!   - `main.rs` → `.invoke_handler(tauri::generate_handler![...])`
//!   - `capabilities/default.json` (custom commands are allowed by `core:default`)

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

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;

    // ── is_directory ──────────────────────────────────────────────────────────

    #[test]
    fn is_directory_returns_false_for_nonexistent_path() {
        assert!(!is_directory(
            "/this/path/absolutely/does/not/exist/xyz123abc".to_string()
        ));
    }

    #[test]
    fn is_directory_returns_false_for_a_regular_file() {
        use std::io::Write;
        let dir = tempfile::tempdir().expect("tempdir");
        let file_path = dir.path().join("test.wav");
        let mut f = std::fs::File::create(&file_path).expect("create file");
        f.write_all(b"RIFF").expect("write");
        assert!(!is_directory(file_path.to_string_lossy().to_string()));
    }

    #[test]
    fn is_directory_returns_true_for_a_real_directory() {
        let dir = tempfile::tempdir().expect("tempdir");
        assert!(is_directory(dir.path().to_string_lossy().to_string()));
    }

    // ── AuthTokenStore ────────────────────────────────────────────────────────

    #[test]
    fn token_store_roundtrip() {
        let store = AuthTokenStore(Mutex::new(None));

        // Initially empty
        assert!(store.0.lock().unwrap().is_none());

        // Store a token
        *store.0.lock().unwrap() = Some("eyJhbGciOiJIUzI1NiJ9.test".to_string());
        assert_eq!(
            *store.0.lock().unwrap(),
            Some("eyJhbGciOiJIUzI1NiJ9.test".to_string())
        );

        // Clear it
        *store.0.lock().unwrap() = None;
        assert!(store.0.lock().unwrap().is_none());
    }

    #[test]
    fn token_store_overwrites_previous_token() {
        let store = AuthTokenStore(Mutex::new(None));
        *store.0.lock().unwrap() = Some("token-v1".to_string());
        *store.0.lock().unwrap() = Some("token-v2".to_string());
        assert_eq!(*store.0.lock().unwrap(), Some("token-v2".to_string()));
    }
}
