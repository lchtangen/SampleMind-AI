<script lang="ts">
  /**
   * ImportPanel.svelte — Folder picker + SSE import progress panel.
   *
   * Flow:
   *   1. User clicks "Import Folder" → pick_folder Tauri command opens OS dialog
   *   2. JS POSTs the folder path to Flask /api/import
   *   3. Flask streams SSE events: start → progress × N → done
   *   4. On done, reload the library store to refresh the table
   */
  import { pickFolder } from "$lib/utils/tauri";
  import { library } from "$lib/stores/library.svelte";

  let importing  = $state(false);
  let progress   = $state(0);
  let total      = $state(0);
  let statusMsg  = $state("");
  let errorMsg   = $state<string | null>(null);

  async function handleImport() {
    errorMsg = null;
    statusMsg = "";

    // 1. Open OS folder picker via Tauri
    let folder: string | null = null;
    try {
      folder = await pickFolder();
    } catch (e) {
      // Fallback to prompt() in browser/dev mode when Tauri isn't available
      folder = window.prompt("Enter folder path containing WAV files:");
    }

    if (!folder) return; // user cancelled

    importing = true;
    progress  = 0;
    total     = 0;
    statusMsg = `Scanning ${folder}…`;

    try {
      // 2. POST to Flask SSE import endpoint
      const res = await fetch("/api/import", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ folder }),
      });

      if (!res.ok || !res.body) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error ?? `Server error ${res.status}`);
      }

      // 3. Read SSE stream line by line
      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let   buffer  = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          const payload = JSON.parse(line.slice(5).trim()) as Record<string, unknown>;

          if ("total" in payload && "imported" in payload === false) {
            // start event
            total     = payload.total as number;
            statusMsg = `Importing 0 / ${total}…`;
          } else if ("current" in payload) {
            // progress event
            progress  = payload.current as number;
            total     = payload.total as number;
            statusMsg = `Importing ${progress} / ${total} — ${payload.filename}`;
          } else if ("imported" in payload) {
            // done event
            statusMsg = `Done — ${payload.imported} of ${payload.total} imported`;
            progress  = total;
            // Send native OS notification (Tauri only — no-op in browser)
            if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
              const { sendNotification } = await import(
                "@tauri-apps/plugin-notification"
              );
              sendNotification({
                title: "SampleMind — Import Complete",
                body: `${payload.imported} of ${payload.total} samples imported`,
              });
            }
          } else if ("error" in payload && "filename" in payload) {
            // per-file error — continue streaming
            console.warn("Import error:", payload);
          }
        }
      }

      // 4. Reload library
      await library.loadSamples();
    } catch (e) {
      errorMsg = e instanceof Error ? e.message : String(e);
      statusMsg = "";
    } finally {
      importing = false;
    }
  }

  let pct = $derived(total > 0 ? Math.round((progress / total) * 100) : 0);
</script>

<div class="import-panel">
  <button
    class="import-btn"
    onclick={handleImport}
    disabled={importing}
  >
    {importing ? "Importing…" : "+ Import Folder"}
  </button>

  {#if importing}
    <div class="progress-wrap" aria-label="Import progress {pct}%">
      <div class="progress-bar" style="width: {pct}%"></div>
    </div>
    <span class="status-msg">{statusMsg}</span>
  {:else if statusMsg}
    <span class="status-done">{statusMsg}</span>
  {/if}

  {#if errorMsg}
    <span class="error-msg">Error: {errorMsg}</span>
  {/if}
</div>

<style>
  .import-panel {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 1rem;
    background: var(--surface, #1a1a1a);
    border-top: 1px solid var(--border, #333);
    min-height: 48px;
  }

  .import-btn {
    padding: 0.45rem 1rem;
    background: var(--accent, #7c3aed);
    border: none;
    border-radius: 5px;
    color: white;
    font-weight: 600;
    font-size: 0.875rem;
    cursor: pointer;
    white-space: nowrap;
    transition: opacity 0.15s;
  }

  .import-btn:hover:not(:disabled) {
    opacity: 0.85;
  }

  .import-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .progress-wrap {
    flex: 1;
    max-width: 240px;
    height: 6px;
    background: var(--border, #333);
    border-radius: 3px;
    overflow: hidden;
  }

  .progress-bar {
    height: 100%;
    background: var(--accent, #7c3aed);
    transition: width 0.2s ease;
  }

  .status-msg,
  .status-done {
    font-size: 0.8rem;
    color: var(--text-muted, #aaa);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 320px;
  }

  .error-msg {
    font-size: 0.8rem;
    color: #f87171;
  }
</style>
