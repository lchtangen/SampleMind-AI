/// state.rs — Managed application state shared across all Tauri commands.
///
/// `AuthTokenStore` holds the JWT access token issued by the FastAPI auth layer.
/// It lives in process memory only — never written to disk or the WebView.
///
/// Registered via `.manage(AuthTokenStore::default())` in `main.rs`.
/// Commands access it with `state: tauri::State<'_, AuthTokenStore>`.

use std::sync::Mutex;

/// In-process store for the FastAPI JWT access token.
///
/// Flask web-UI auth is handled via session cookies automatically.
/// This store is only for Rust→FastAPI calls that need a Bearer token.
#[derive(Default)]
pub struct AuthTokenStore(pub Mutex<Option<String>>);
