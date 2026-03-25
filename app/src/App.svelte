<script lang="ts">
  /**
   * App.svelte — Root component for SampleMind AI desktop app.
   *
   * Layout:
   *   ┌─────────────────────────────────┐
   *   │  SearchBar  (top)               │
   *   ├─────────────────────────────────┤
   *   │  SampleTable  (main, scrollable)│
   *   ├─────────────────────────────────┤
   *   │  ImportPanel  (bottom bar)      │
   *   └─────────────────────────────────┘
   *
   * The app loads the sample library on mount.
   * When the Tauri WebView navigates to the Flask server URL (127.0.0.1:5174),
   * the Svelte app is replaced by the Flask HTML — the Svelte frontend is
   * the Tauri-only experience (used when Flask isn't serving HTML).
   */
  import { onMount }    from "svelte";
  import SearchBar      from "$lib/components/SearchBar.svelte";
  import SampleTable    from "$lib/components/SampleTable.svelte";
  import ImportPanel    from "$lib/components/ImportPanel.svelte";
  import { loadSamples } from "$lib/stores/library.svelte";
  import type { Sample } from "$lib/stores/library.svelte";

  let selectedSample = $state<Sample | null>(null);

  onMount(() => {
    loadSamples();
  });

  function handleSelect(s: Sample) {
    selectedSample = s;
  }
</script>

<div class="app-shell">
  <SearchBar />

  <main class="main-area">
    <SampleTable onselect={handleSelect} />
  </main>

  <ImportPanel />
</div>

<style>
  :global(*) {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  :global(body) {
    background: var(--bg, #121212);
    color: var(--text, #e0e0e0);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    height: 100vh;
    overflow: hidden;
  }

  :global(:root) {
    --bg:         #121212;
    --surface:    #1a1a1a;
    --input-bg:   #252525;
    --border:     #2e2e2e;
    --text:       #e0e0e0;
    --text-muted: #888;
    --accent:     #7c3aed;
    --hover:      #1f1f2e;
    --selected:   #2a2050;
  }

  .app-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }

  .main-area {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
</style>
