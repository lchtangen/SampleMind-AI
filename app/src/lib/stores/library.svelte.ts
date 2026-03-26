/**
 * library.svelte.ts — Svelte 5 Runes reactive store for the sample library.
 *
 * Uses the closure-based store pattern required by Svelte 5 module rules:
 * state lives in a function closure so internal reassignments are allowed,
 * and consumers access values through getter properties on the exported object.
 *
 * Usage in a component:
 *   import { library } from "$lib/stores/library.svelte";
 *   import type { Sample } from "$lib/stores/library.svelte";
 *
 *   library.samples         // reactive Sample[]
 *   library.filters.query   // reactive string
 *   library.loadSamples()   // async refresh
 *   library.setFilter(key, value)
 *   library.clearFilters()
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

// ── Closure-based reactive store ─────────────────────────────────────────────
//
// Internal variables can be reassigned freely; only the returned object is
// exported, so Svelte's "no-reassign exported state" rule is satisfied.

function createLibraryStore() {
  let samples   = $state<Sample[]>([]);
  let isLoading = $state(false);
  let error     = $state<string | null>(null);
  let total     = $state(0);
  let filters   = $state<LibraryFilters>({
    query:      "",
    energy:     "",
    mood:       "",
    instrument: "",
    bpm_min:    "",
    bpm_max:    "",
  });

  async function loadSamples(): Promise<void> {
    isLoading = true;
    error     = null;

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
      total   = data.length;
    } catch (e) {
      error   = e instanceof Error ? e.message : String(e);
      samples = [];
      total   = 0;
    } finally {
      isLoading = false;
    }
  }

  function setFilter(key: keyof LibraryFilters, value: string): void {
    filters[key] = value;
    loadSamples();
  }

  function clearFilters(): void {
    filters.query      = "";
    filters.energy     = "";
    filters.mood       = "";
    filters.instrument = "";
    filters.bpm_min    = "";
    filters.bpm_max    = "";
    loadSamples();
  }

  return {
    get samples()   { return samples;   },
    get isLoading() { return isLoading; },
    get error()     { return error;     },
    get total()     { return total;     },
    get filters()   { return filters;   },
    loadSamples,
    setFilter,
    clearFilters,
  };
}

export const library = createLibraryStore();
