/**
 * tauri.ts — Typed wrappers for all Tauri IPC commands.
 *
 * Each function here corresponds to a #[tauri::command] in main.rs.
 * Using wrappers centralises error handling and keeps components clean.
 */
import { invoke } from "@tauri-apps/api/core";

/**
 * Open the OS native folder-picker dialog.
 * Returns the selected path string, or null if the user cancelled.
 */
export async function pickFolder(): Promise<string | null> {
  return invoke<string | null>("pick_folder");
}

/**
 * Check if the given path is a directory.
 * Used after drag-drop to decide whether to call /api/import or /api/import-files.
 */
export async function isDirectory(path: string): Promise<boolean> {
  return invoke<boolean>("is_directory", { path });
}

/**
 * Store a JWT access token in Rust process memory.
 * Call after a successful FastAPI /api/v1/auth/login response.
 */
export async function storeToken(token: string): Promise<void> {
  return invoke<void>("store_token", { token });
}

/**
 * Retrieve the stored JWT access token.
 * Returns null if not logged in via FastAPI.
 */
export async function getToken(): Promise<string | null> {
  return invoke<string | null>("get_token");
}

/**
 * Clear the stored JWT token (call on logout).
 */
export async function clearToken(): Promise<void> {
  return invoke<void>("clear_token");
}
