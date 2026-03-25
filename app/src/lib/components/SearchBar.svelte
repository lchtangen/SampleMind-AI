<script lang="ts">
  /**
   * SearchBar.svelte — Live search + filter bar.
   *
   * Debounces the text query (300ms) then calls setFilter() from the library
   * store. Dropdown changes fire immediately (no debounce needed).
   */
  import { filters, setFilter, clearFilters, isLoading } from "$lib/stores/library.svelte";

  const ENERGY_OPTIONS = ["", "low", "mid", "high"] as const;
  const MOOD_OPTIONS   = ["", "dark", "chill", "aggressive", "euphoric", "melancholic", "neutral"] as const;
  const INSTRUMENT_OPTIONS = ["", "kick", "snare", "hihat", "bass", "pad", "lead", "loop", "sfx"] as const;

  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  function onQueryInput(e: Event) {
    const value = (e.target as HTMLInputElement).value;
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => setFilter("query", value), 300);
  }

  function onEnergyChange(e: Event) {
    setFilter("energy", (e.target as HTMLSelectElement).value);
  }

  function onMoodChange(e: Event) {
    setFilter("mood", (e.target as HTMLSelectElement).value);
  }

  function onInstrumentChange(e: Event) {
    setFilter("instrument", (e.target as HTMLSelectElement).value);
  }
</script>

<div class="search-bar" class:loading={isLoading}>
  <input
    class="search-input"
    type="text"
    placeholder="Search by filename or tag…"
    value={filters.query}
    oninput={onQueryInput}
  />

  <select class="filter-select" value={filters.energy} onchange={onEnergyChange}>
    <option value="">All energy</option>
    {#each ENERGY_OPTIONS.slice(1) as e}
      <option value={e}>{e}</option>
    {/each}
  </select>

  <select class="filter-select" value={filters.mood} onchange={onMoodChange}>
    <option value="">All moods</option>
    {#each MOOD_OPTIONS.slice(1) as m}
      <option value={m}>{m}</option>
    {/each}
  </select>

  <select class="filter-select" value={filters.instrument} onchange={onInstrumentChange}>
    <option value="">All types</option>
    {#each INSTRUMENT_OPTIONS.slice(1) as i}
      <option value={i}>{i}</option>
    {/each}
  </select>

  {#if filters.query || filters.energy || filters.mood || filters.instrument}
    <button class="clear-btn" onclick={clearFilters}>Clear</button>
  {/if}

  {#if isLoading}
    <span class="spinner" aria-label="Loading…">⏳</span>
  {/if}
</div>

<style>
  .search-bar {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    padding: 0.75rem 1rem;
    background: var(--surface, #1e1e1e);
    border-bottom: 1px solid var(--border, #333);
  }

  .search-input {
    flex: 1;
    min-width: 200px;
    padding: 0.4rem 0.75rem;
    background: var(--input-bg, #2a2a2a);
    border: 1px solid var(--border, #444);
    border-radius: 4px;
    color: var(--text, #e0e0e0);
    font-size: 0.9rem;
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

  .clear-btn {
    padding: 0.4rem 0.75rem;
    background: var(--accent, #7c3aed);
    border: none;
    border-radius: 4px;
    color: white;
    font-size: 0.85rem;
    cursor: pointer;
  }

  .clear-btn:hover {
    opacity: 0.85;
  }

  .spinner {
    font-size: 0.9rem;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
  }
</style>
