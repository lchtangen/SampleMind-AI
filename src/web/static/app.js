/**
 * app.js — SampleMind AI frontend
 *
 * Three things this file does:
 * 1. Live search — calls /api/samples as you type, re-renders the table
 *    without reloading the page (this is called an AJAX request, using fetch())
 * 2. Tag modal — clicking 🏷️ opens a form to edit a sample's metadata,
 *    then POSTs to /api/tag to save it
 * 3. Audio playback — clicking ▶ streams the WAV from /audio/<id> into
 *    the <audio> element in the player bar at the bottom
 */

// ── Grab elements we'll reuse ───────────────────────────────────────────────
const searchInput      = document.getElementById("search-input");
const genreFilter      = document.getElementById("genre-filter");
const energyFilter     = document.getElementById("energy-filter");
const instrumentFilter = document.getElementById("instrument-filter");
const bpmMin           = document.getElementById("bpm-min");
const bpmMax           = document.getElementById("bpm-max");
const tbody        = document.getElementById("sample-tbody");
const modal        = document.getElementById("tag-modal");
const playerBar    = document.getElementById("player-bar");
const audioPlayer  = document.getElementById("audio-player");
const playerName   = document.getElementById("player-filename");

let currentPlayBtn = null;  // track which ▶ button is "playing" state


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
