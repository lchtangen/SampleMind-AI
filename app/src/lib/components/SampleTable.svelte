<script lang="ts">
  /**
   * SampleTable.svelte — Sortable sample library table.
   *
   * Reads samples from the library store and renders them as a table.
   * Supports row selection (click) and emits a "select" event with the sample.
   * Energy values are rendered as colour-coded badges.
   */
  import { library } from "$lib/stores/library.svelte";
  import type { Sample } from "$lib/stores/library.svelte";

  let { onselect }: { onselect?: (s: Sample) => void } = $props();

  let selected = $state<number | null>(null);

  const ENERGY_COLOR: Record<string, string> = {
    low:  "#4ade80",
    mid:  "#facc15",
    high: "#f87171",
  };

  function selectRow(s: Sample) {
    selected = s.id;
    onselect?.(s);
  }

  function fmt(v: number | null, decimals = 1): string {
    return v != null ? v.toFixed(decimals) : "—";
  }

  function label(v: string | null): string {
    return v ?? "—";
  }
</script>

<div class="table-container">
  <div class="table-meta">
    {library.total} sample{library.total === 1 ? "" : "s"}
  </div>

  {#if library.samples.length === 0}
    <div class="empty-state">No samples match the current filters.</div>
  {:else}
    <table class="sample-table">
      <thead>
        <tr>
          <th>Filename</th>
          <th>BPM</th>
          <th>Key</th>
          <th>Type</th>
          <th>Energy</th>
          <th>Mood</th>
          <th>Genre</th>
        </tr>
      </thead>
      <tbody>
        {#each library.samples as s (s.id)}
          <tr
            class="sample-row"
            class:selected={selected === s.id}
            onclick={() => selectRow(s)}
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === "Enter" && selectRow(s)}
          >
            <td class="filename" title={s.path}>{s.filename}</td>
            <td>{fmt(s.bpm, 0)}</td>
            <td>{label(s.key)}</td>
            <td>{label(s.instrument)}</td>
            <td>
              {#if s.energy}
                <span class="badge" style="background: {ENERGY_COLOR[s.energy] ?? '#888'}">
                  {s.energy}
                </span>
              {:else}
                —
              {/if}
            </td>
            <td>{label(s.mood)}</td>
            <td>{label(s.genre)}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</div>

<style>
  .table-container {
    flex: 1;
    overflow-y: auto;
    background: var(--bg, #121212);
  }

  .table-meta {
    padding: 0.4rem 1rem;
    font-size: 0.8rem;
    color: var(--text-muted, #888);
    border-bottom: 1px solid var(--border, #2a2a2a);
  }

  .empty-state {
    padding: 3rem 1rem;
    text-align: center;
    color: var(--text-muted, #666);
    font-size: 0.95rem;
  }

  .sample-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  thead th {
    position: sticky;
    top: 0;
    background: var(--surface, #1a1a1a);
    color: var(--text-muted, #aaa);
    font-weight: 600;
    text-align: left;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid var(--border, #333);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .sample-row td {
    padding: 0.45rem 0.75rem;
    border-bottom: 1px solid var(--border, #222);
    color: var(--text, #ddd);
    cursor: pointer;
    white-space: nowrap;
  }

  .sample-row:hover td {
    background: var(--hover, #1f1f2e);
  }

  .sample-row.selected td {
    background: var(--selected, #2a2050);
  }

  .filename {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
    font-family: monospace;
    font-size: 0.83rem;
  }

  .badge {
    display: inline-block;
    padding: 0.1rem 0.5rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #111;
  }
</style>
