<script lang="ts">
  /**
   * ExportPanel.svelte — Export filtered samples to FL Studio.
   *
   * POSTs to Flask /api/export-to-fl with optional energy/instrument filters.
   * Shows inline status ("Copied N sample(s) to FL Studio") or error message.
   * Styled as a second bottom bar alongside ImportPanel.
   */

  const ENERGY_OPTIONS = ["", "low", "mid", "high"] as const;
  const INSTRUMENT_OPTIONS = [
    "", "kick", "snare", "hihat", "bass", "pad", "lead", "loop", "sfx",
  ] as const;

  let exporting  = $state(false);
  let statusMsg  = $state("");
  let errorMsg   = $state<string | null>(null);
  let energy     = $state("");
  let instrument = $state("");

  async function handleExport() {
    errorMsg  = null;
    statusMsg = "";
    exporting = true;

    try {
      const body: Record<string, string> = {};
      if (energy)     body.energy     = energy;
      if (instrument) body.instrument = instrument;

      const res  = await fetch("/api/export-to-fl", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? `Server error ${res.status}`);

      statusMsg =
        `Copied ${data.copied} sample(s) to FL Studio` +
        (data.skipped > 0 ? ` (${data.skipped} skipped)` : "");
    } catch (e) {
      errorMsg  = e instanceof Error ? e.message : String(e);
      statusMsg = "";
    } finally {
      exporting = false;
    }
  }
</script>

<div class="export-panel">
  <select
    class="filter-select"
    bind:value={energy}
    disabled={exporting}
    aria-label="Energy filter"
  >
    <option value="">All energy</option>
    {#each ENERGY_OPTIONS.slice(1) as e}
      <option value={e}>{e}</option>
    {/each}
  </select>

  <select
    class="filter-select"
    bind:value={instrument}
    disabled={exporting}
    aria-label="Instrument filter"
  >
    <option value="">All types</option>
    {#each INSTRUMENT_OPTIONS.slice(1) as i}
      <option value={i}>{i}</option>
    {/each}
  </select>

  <button
    class="export-btn"
    onclick={handleExport}
    disabled={exporting}
  >
    {exporting ? "Exporting…" : "Export to FL Studio"}
  </button>

  {#if statusMsg}
    <span class="status-done">{statusMsg}</span>
  {/if}

  {#if errorMsg}
    <span class="error-msg">Error: {errorMsg}</span>
  {/if}
</div>

<style>
  .export-panel {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.5rem 1rem;
    background: var(--surface, #1a1a1a);
    border-top: 1px solid var(--border, #333);
    min-height: 48px;
  }

  .filter-select {
    padding: 0.4rem 0.5rem;
    background: var(--input-bg, #2a2a2a);
    border: 1px solid var(--border, #444);
    border-radius: 4px;
    color: var(--text, #e0e0e0);
    font-size: 0.85rem;
    cursor: pointer;
  }

  .filter-select:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .export-btn {
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

  .export-btn:hover:not(:disabled) {
    opacity: 0.85;
  }

  .export-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

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
