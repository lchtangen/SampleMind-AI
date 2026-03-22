// build.rs — required by tauri-build to generate platform-specific glue code.
// This runs at compile time, not at runtime.
fn main() {
    tauri_build::build()
}
