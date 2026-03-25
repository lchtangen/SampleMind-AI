/**
 * library.svelte.ts — Svelte 5 Runes store for the sample library.
 *
 * Reactive state for the full sample list and filter criteria.
 * Calls Flask /api/samples to load data; reacts to filter changes.
 *
 * Usage in a component:
 *   import { samples, loadSamples, query, energyFilter } from "$lib/stores/library.svelte";
 */

export interface Sample {
  id: number;
  filename: string;
  path: string;
  bpm: number | null;
  key: string | null;
  energy: string | null;
  mood: string | null;
  instrument: string | null;
  genre: string | null;
  tags: string | null;
}

export interface LibraryFilters {
  query: string;
  energy: string;
  mood: string;
  instrument: string;
  bpm_min: string;
  bpm_max: string;
}

// ── Reactive state (Svelte 5 Runes) ──────────────────────────────────────────

export let samples = $state<Sample[]>([]);
export let isLoading = $state(false);
export let error = $state<string | null>(null);
export let total = $state(0);

export let filters = $state<LibraryFilters>({
  query: "",
  energy: "",
  mood: "",
  instrument: "",
  bpm_min: "",
  bpm_max: "",
});

// ── API functions ─────────────────────────────────────────────────────────────

/**
 * Load samples from Flask /api/samples with current filters.
 * Called on startup and whenever any filter changes.
 */
export async function loadSamples(): Promise<void> {
  isLoading = true;
  error = null;

  try {
    const params = new URLSearchParams();
    if (filters.query)      params.set("q",          filters.query);
    if (filters.energy)     params.set("energy",     filters.energy);
    if (filters.mood)       params.set("mood",        filters.mood);
    if (filters.instrument) params.set("instrument", filters.instrument);
    if (filters.bpm_min)    params.set("bpm_min",    filters.bpm_min);
    if (filters.bpm_max)    params.set("bpm_max",    filters.bpm_max);

    const res = await fetch(`/api/samples?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data: Sample[] = await res.json();
    samples = data;
    total = data.length;
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
    samples = [];
    total = 0;
  } finally {
    isLoading = false;
  }
}

/**
 * Update a single filter key and reload.
 */
export function setFilter(key: keyof LibraryFilters, value: string): void {
  filters[key] = value;
  loadSamples();
}

/**
 * Clear all filters and reload.
 */
export function clearFilters(): void {
  filters.query = "";
  filters.energy = "";
  filters.mood = "";
  filters.instrument = "";
  filters.bpm_min = "";
  filters.bpm_max = "";
  loadSamples();
}
