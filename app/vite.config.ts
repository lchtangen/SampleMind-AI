import { defineConfig } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [svelte()],

  // Vite dev server must match tauri.conf.json devUrl
  server: {
    port: 1420,
    strictPort: true,
  },

  // Output to dist/ so tauri.conf.json frontendDist = "../dist" resolves correctly
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },

  // Prevent Vite from obscuring Rust errors
  clearScreen: false,
});

