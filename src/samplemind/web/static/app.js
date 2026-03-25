/**
 * app.js — SampleMind AI frontend
 *
 * 1. Live search   — /api/samples as you type (AJAX, no page reload)
 * 2. Tag modal     — POST /api/tag to update metadata
 * 3. Audio playback — stream WAV from /audio/<id>
 * 4. Import folder — native OS dialog (Tauri) or path prompt (browser)
 *    then POST /api/import with the chosen folder path
 */

// ── Tauri IPC bridge ─────────────────────────────────────────────────────────
//
// window.__TAURI__ is injected by Tauri when withGlobalTauri=true.
// ?? fallbacks mean the UI still works in a plain browser for debugging.
//
// invoke(cmd, args) — call a Rust #[tauri::command]
// listen(event, cb) — subscribe to a Tauri event (like drag-drop)
const invoke = window.__TAURI__?.core?.invoke  ?? (() => Promise.resolve(null));
const listen  = window.__TAURI__?.event?.listen ?? (() => Promise.resolve(() => {}));

// ── Grab elements we'll reuse ───────────────────────────────────────────────
const searchInput      = document.getElementById("search-input");
const genreFilter      = document.getElementById("genre-filter");
const energyFilter     = document.getElementById("energy-filter");
const instrumentFilter = document.getElementById("instrument-filter");
const bpmMin           = document.getElementById("bpm-min");
const bpmMax           = document.getElementById("bpm-max");
const tbody            = document.getElementById("sample-tbody");
const modal            = document.getElementById("tag-modal");
const playerBar        = document.getElementById("player-bar");
const audioPlayer      = document.getElementById("audio-player");
const playerName       = document.getElementById("player-filename");
const importBtn        = document.getElementById("import-btn");
const importToast      = document.getElementById("import-toast");
const libraryCount     = document.getElementById("library-count");

let currentPlayBtn = null;


// ── Toast helper ─────────────────────────────────────────────────────────────

function showToast(msg, type = "loading", autoDismiss = 0) {
  importToast.textContent = msg;
  importToast.className   = `toast ${type}`;
  if (autoDismiss > 0) {
    setTimeout(() => { importToast.classList.add("hidden"); }, autoDismiss);
  }
}


// ── Import folder ─────────────────────────────────────────────────────────────
//
// How this works end-to-end:
// 1. User clicks "+ Import Folder"
// 2. If running in Tauri: invoke('pick_folder') → Rust opens native OS dialog
//    If running in browser: prompt() asks for a folder path (dev/debug mode)
// 3. JS POSTs the path to Flask /api/import
// 4. Flask runs import_samples(path) and returns { imported, log }
// 5. Toast shows result, table refreshes

importBtn.addEventListener("click", async () => {
  importBtn.disabled = true;
  showToast("Opening folder picker…");

  let folderPath = null;

  if (window.__TAURI__) {
    // Running inside Tauri desktop app — use native OS dialog
    try {
      folderPath = await invoke("pick_folder");
    } catch (err) {
      showToast(`❌ Dialog error: ${err}`, "error", 4000);
      importBtn.disabled = false;
      return;
    }
  } else {
    // Running in a browser — prompt for path (debugging only)
    folderPath = window.prompt("Enter folder path containing WAV files:");
  }

  if (!folderPath) {
    // User cancelled the dialog
    importToast.classList.add("hidden");
    importBtn.disabled = false;
    return;
  }

  showToast(`⏳ Importing from ${folderPath}…`);

  try {
    const res  = await fetch("/api/import", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ folder: folderPath }),
    });
    const data = await res.json();

    if (res.ok) {
      showToast(`✅ Imported ${data.imported} sample(s)`, "success", 4000);
      fetchSamples();          // refresh the table
      updateLibraryCount();    // update header count
    } else {
      showToast(`❌ ${data.error}`, "error", 5000);
    }
  } catch (err) {
    showToast(`❌ Network error: ${err}`, "error", 5000);
  }

  importBtn.disabled = false;
});

async function updateLibraryCount() {
  try {
    const res  = await fetch("/api/status");
    const data = await res.json();
    if (libraryCount) libraryCount.textContent = `${data.total} samples in library`;
  } catch {}
}


// ── Live search ─────────────────────────────────────────────────────────────

// Debounce: wait 300ms after the user stops typing before firing the request.
// Without this, we'd fire a request on every single keypress.
let debounceTimer;
function onFilterChange() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(fetchSamples, 300);
}

[searchInput, genreFilter, energyFilter, instrumentFilter, bpmMin, bpmMax].forEach(el => {
  el.addEventListener("input", onFilterChange);
});

async function fetchSamples() {
  // Build query string from current filter values
  const params = new URLSearchParams();
  if (searchInput.value)      params.set("q",          searchInput.value);
  if (genreFilter.value)      params.set("genre",      genreFilter.value);
  if (energyFilter.value)     params.set("energy",     energyFilter.value);
  if (instrumentFilter.value) params.set("instrument", instrumentFilter.value);
  if (bpmMin.value)           params.set("bpm_min",    bpmMin.value);
  if (bpmMax.value)           params.set("bpm_max",    bpmMax.value);

  // fetch() is the modern way to make HTTP requests from JS
  // await pauses execution until the response arrives
  const res     = await fetch(`/api/samples?${params}`);
  const samples = await res.json();

  renderTable(samples);
}

function renderTable(samples) {
  if (samples.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty">No samples matched.</td></tr>`;
    return;
  }

  tbody.innerHTML = samples.map(s => `
    <tr data-path="${escHtml(s.path)}" data-id="${s.id}">
      <td class="filename">${escHtml(s.filename)}</td>
      <td>${s.bpm ?? "—"}</td>
      <td>${escHtml(s.key ?? "—")}</td>
      <td><span class="chip instrument">${escHtml(s.instrument ?? "—")}</span></td>
      <td class="editable" data-field="genre">${escHtml(s.genre ?? "")}</td>
      <td class="editable" data-field="energy">${escHtml(s.energy ?? "")}</td>
      <td class="editable" data-field="mood">${escHtml(s.mood ?? "")}</td>
      <td><button class="play-btn" data-id="${s.id}">▶</button></td>
      <td><button class="tag-btn">🏷️</button></td>
    </tr>
  `).join("");
}

// Escape HTML to prevent XSS — never inject raw user data into innerHTML
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}


// ── Audio playback ───────────────────────────────────────────────────────────

// Event delegation: one listener on tbody catches clicks from all ▶ buttons,
// even ones added dynamically by renderTable(). This is more efficient than
// attaching a listener to every single button.
tbody.addEventListener("click", e => {
  const btn = e.target.closest(".play-btn");
  if (!btn) return;

  const id       = btn.dataset.id;
  const filename = btn.closest("tr").querySelector(".filename").textContent;

  // Toggle off if clicking the same button again
  if (currentPlayBtn === btn && !audioPlayer.paused) {
    audioPlayer.pause();
    btn.textContent = "▶";
    btn.classList.remove("playing");
    currentPlayBtn = null;
    return;
  }

  // Reset previous play button
  if (currentPlayBtn) {
    currentPlayBtn.textContent = "▶";
    currentPlayBtn.classList.remove("playing");
  }

  // Start new playback
  audioPlayer.src = `/audio/${id}`;
  audioPlayer.play();
  btn.textContent = "⏸";
  btn.classList.add("playing");
  currentPlayBtn = btn;

  playerBar.classList.remove("hidden");
  playerName.textContent = filename;
});

audioPlayer.addEventListener("ended", () => {
  if (currentPlayBtn) {
    currentPlayBtn.textContent = "▶";
    currentPlayBtn.classList.remove("playing");
    currentPlayBtn = null;
  }
});


// ── Tag modal ────────────────────────────────────────────────────────────────

let modalPath = null;

tbody.addEventListener("click", e => {
  const btn = e.target.closest(".tag-btn");
  if (!btn) return;

  const row      = btn.closest("tr");
  modalPath      = row.dataset.path;
  const filename = row.querySelector(".filename").textContent;

  // Pre-fill modal with current values
  document.getElementById("modal-filename").textContent = filename;
  document.getElementById("modal-genre").value  = row.querySelector('[data-field="genre"]').textContent;
  document.getElementById("modal-mood").value   = row.querySelector('[data-field="mood"]').textContent;
  document.getElementById("modal-energy").value = row.querySelector('[data-field="energy"]').textContent;
  document.getElementById("modal-tags").value   = "";

  modal.classList.remove("hidden");
});

document.getElementById("modal-cancel").addEventListener("click", () => {
  modal.classList.add("hidden");
});

document.getElementById("modal-save").addEventListener("click", async () => {
  const body = {
    path:   modalPath,
    genre:  document.getElementById("modal-genre").value  || null,
    mood:   document.getElementById("modal-mood").value   || null,
    energy: document.getElementById("modal-energy").value || null,
    tags:   document.getElementById("modal-tags").value   || null,
  };

  const res = await fetch("/api/tag", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(body),
  });

  if (res.ok) {
    modal.classList.add("hidden");
    fetchSamples();  // refresh the table to show updated tags
  } else {
    alert("Failed to save tags.");
  }
});

// Close modal on backdrop click
modal.addEventListener("click", e => {
  if (e.target === modal) modal.classList.add("hidden");
});


// ── Drag-and-drop import ──────────────────────────────────────────────────────
//
// Tauri gives us REAL filesystem paths when files are dragged onto the window.
// This is fundamentally different from browser drag-drop which gives sandboxed
// File objects — in Tauri, you can drop any file from anywhere on the system.
//
// Event flow:
//   tauri://drag-drop { type: 'enter' }  → show overlay
//   tauri://drag-drop { type: 'over'  }  → (ignore, just hover)
//   tauri://drag-drop { type: 'drop'  }  → handle the paths
//   tauri://drag-drop { type: 'leave' }  → hide overlay
//
// For each drop we:
//   1. Ask Rust is_directory(path) for the first path
//   2. If folder  → POST /api/import       { path }
//   3. If files   → POST /api/import-files { paths }

const dropOverlay = document.getElementById("drop-overlay");

async function handleDrop(paths) {
  if (!paths || paths.length === 0) return;

  dropOverlay.classList.add("hidden");
  dropOverlay.classList.remove("active");

  // Determine if we got a folder or individual files
  const firstIsDir = await invoke("is_directory", { path: paths[0] });

  if (firstIsDir) {
    // Folder drop — use the existing folder import endpoint
    showToast(`⏳ Importing from ${paths[0]}…`);
    try {
      const res  = await fetch("/api/import", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ folder: paths[0] }),
      });
      const data = await res.json();
      if (res.ok) {
        showToast(`✅ Imported ${data.imported} sample(s)`, "success", 4000);
        fetchSamples();
        updateLibraryCount();
      } else {
        showToast(`❌ ${data.error}`, "error", 5000);
      }
    } catch (err) {
      showToast(`❌ ${err}`, "error", 5000);
    }
  } else {
    // Individual file drop — filter to WAV files only
    const wavPaths = paths.filter(p => p.toLowerCase().endsWith(".wav"));

    if (wavPaths.length === 0) {
      showToast("⚠️ No WAV files in the dropped items", "error", 3000);
      return;
    }

    showToast(`⏳ Importing ${wavPaths.length} WAV file(s)…`);
    try {
      const res  = await fetch("/api/import-files", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ paths: wavPaths }),
      });
      const data = await res.json();
      if (res.ok) {
        const errs = data.errors?.length ? ` (${data.errors.length} failed)` : "";
        showToast(`✅ Imported ${data.imported} sample(s)${errs}`, "success", 4000);
        fetchSamples();
        updateLibraryCount();
      } else {
        showToast(`❌ ${data.error}`, "error", 5000);
      }
    } catch (err) {
      showToast(`❌ ${err}`, "error", 5000);
    }
  }
}

// Subscribe to Tauri's drag-drop event stream.
// listen() returns an unlisten function — call it to unsubscribe.
listen("tauri://drag-drop", event => {
  const { type, paths } = event.payload;

  switch (type) {
    case "enter":
      // Files are hovering over the window — show the overlay
      dropOverlay.classList.remove("hidden");
      dropOverlay.classList.add("active");
      break;

    case "leave":
      // Files left the window without dropping
      dropOverlay.classList.add("hidden");
      dropOverlay.classList.remove("active");
      break;

    case "drop":
      // Files were released — handle them
      handleDrop(paths);
      break;
  }
});
