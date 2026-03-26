<script lang="ts">
  /**
   * WaveformPlayer.svelte — Phase 6 audio player with waveform visualisation.
   *
   * Uses wavesurfer.js 7 to render an interactive waveform from the Flask
   * /audio/<id> streaming endpoint and provides play/pause/seek controls.
   *
   * Lifecycle: $effect() reacts to `sample` prop changes.
   *   - Cleanup return destroys the previous WaveSurfer before creating a new one.
   *   - This prevents stacked instances if rows are clicked rapidly.
   */
  import WaveSurfer from "wavesurfer.js";
  import type { Sample } from "$lib/stores/library.svelte";

  let { sample }: { sample: Sample | null } = $props();

  let container = $state<HTMLDivElement | undefined>(undefined);
  let isPlaying = $state(false);
  let currentTime = $state(0);
  let duration = $state(0);
  let isReady = $state(false);
  let isLoading = $state(false);

  let ws: WaveSurfer | null = null;

  $effect(() => {
    // Both container and sample must be present before creating a waveform.
    if (!container || !sample) return;

    // Destroy previous instance (cleanup runs synchronously before next render).
    ws?.destroy();
    ws = null;
    isPlaying = false;
    isReady = false;
    isLoading = true;
    currentTime = 0;
    duration = 0;

    ws = WaveSurfer.create({
      container,
      waveColor:     "#7c3aed",
      progressColor: "#4ade80",
      cursorColor:   "#555",
      url:           `/audio/${sample.id}`,
      height:        56,
      barWidth:      2,
      barGap:        1,
      normalize:     true,
      interact:      true,
    });

    ws.on("ready",        () => { isReady = true; isLoading = false; duration = ws!.getDuration(); });
    ws.on("audioprocess", () => { currentTime = ws!.getCurrentTime(); });
    ws.on("play",         () => { isPlaying = true; });
    ws.on("pause",        () => { isPlaying = false; });
    ws.on("finish",       () => { isPlaying = false; currentTime = 0; ws!.seekTo(0); });
    ws.on("error",        () => { isLoading = false; });

    // Cleanup: called before next $effect run or on component destroy.
    return () => {
      ws?.destroy();
      ws = null;
    };
  });

  function togglePlay() {
    if (isReady) ws?.playPause();
  }

  function fmt(s: number): string {
    const m   = Math.floor(s / 60);
    const sec = Math.floor(s % 60).toString().padStart(2, "0");
    return `${m}:${sec}`;
  }
</script>

<section class="player" aria-label="Waveform player">
  <!-- Info strip -->
  <div class="player-info">
    <span class="player-filename">{sample?.filename ?? "—"}</span>
    {#if sample?.bpm}
      <span class="player-meta">{Math.round(sample.bpm)} BPM</span>
    {/if}
    {#if sample?.key}
      <span class="player-meta">{sample.key}</span>
    {/if}
    {#if sample?.energy}
      <span class="player-meta energy-{sample.energy}">{sample.energy}</span>
    {/if}
  </div>

  <!-- Waveform canvas (wavesurfer renders into this div) -->
  <div class="waveform-wrap" bind:this={container}>
    {#if isLoading}
      <div class="loading-bar"></div>
    {/if}
  </div>

  <!-- Playback controls -->
  <div class="controls">
    <button
      class="play-btn"
      onclick={togglePlay}
      disabled={!isReady}
      aria-label={isPlaying ? "Pause" : "Play"}
    >
      {isPlaying ? "⏸" : "▶"}
    </button>
    <span class="time">{fmt(currentTime)} / {fmt(duration)}</span>
  </div>
</section>

<style>
  section.player {
    background: var(--surface, #1a1a1a);
    border-top: 1px solid var(--border, #2e2e2e);
    padding: 0.5rem 1rem 0.4rem;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    outline: none;
  }

  .player-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-size: 0.8rem;
  }

  .player-filename {
    font-family: monospace;
    color: var(--text, #e0e0e0);
    font-weight: 600;
    max-width: 340px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .player-meta {
    color: var(--text-muted, #888);
    font-size: 0.75rem;
  }

  .energy-low  { color: #4ade80; }
  .energy-mid  { color: #facc15; }
  .energy-high { color: #f87171; }

  .waveform-wrap {
    position: relative;
    min-height: 56px;
  }

  /* Shimmer loading bar shown while wavesurfer decodes audio */
  .loading-bar {
    position: absolute;
    inset: 0;
    background: linear-gradient(90deg, var(--border, #2e2e2e) 25%, #3a3a4a 50%, var(--border, #2e2e2e) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.2s infinite;
    border-radius: 4px;
  }

  @keyframes shimmer {
    0%   { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .play-btn {
    background: var(--accent, #7c3aed);
    color: #fff;
    border: none;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    font-size: 11px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: opacity 0.15s;
  }

  .play-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .play-btn:not(:disabled):hover { opacity: 0.8; }

  .time {
    font-size: 0.75rem;
    color: var(--text-muted, #888);
    font-variant-numeric: tabular-nums;
  }
</style>
