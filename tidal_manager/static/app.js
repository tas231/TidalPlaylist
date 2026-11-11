/**
 * TIDAL Playlist Manager - Frontend Application
 */

const state = {
  auth: { loggedIn: false, user: null },
  playlists: [],
  paneA: {
    playlistId: null,
    details: null,
    tracks: [],
    filteredTracks: [],
    selectedIndices: new Set(),
    filterQuery: "",
  },
  paneB: {
    playlistId: null,
    details: null,
    tracks: [],
    filteredTracks: [],
    selectedIndices: new Set(),
    filterQuery: "",
  },
  pollInterval: null,
  countdownInterval: null,
  activeSplitPl: null,
};

// ============================================================================
// DOM Elements
// ============================================================================

const el = {
  // Auth
  authSection: document.getElementById("auth-section"),
  dashboardSection: document.getElementById("dashboard-section"),
  loginInitialState: document.getElementById("login-initial-state"),
  loginPendingState: document.getElementById("login-pending-state"),
  btnStartLogin: document.getElementById("btn-start-login"),
  btnOpenTidal: document.getElementById("btn-open-tidal"),
  deviceCode: document.getElementById("device-code"),
  btnCopyCode: document.getElementById("btn-copy-code"),
  loginCountdown: document.getElementById("login-countdown"),
  userBadge: document.getElementById("user-badge"),
  userName: document.getElementById("user-name"),
  userCountry: document.getElementById("user-country"),
  btnLogout: document.getElementById("btn-logout"),

  // Global Actions
  btnNewPlaylist: document.getElementById("btn-new-playlist"),
  btnRefreshAll: document.getElementById("btn-refresh-all"),

  // Transfer Dock
  btnCopyAToB: document.getElementById("btn-copy-a-to-b"),
  btnMoveAToB: document.getElementById("btn-move-a-to-b"),
  btnCopyBToA: document.getElementById("btn-copy-b-to-a"),
  btnMoveBToA: document.getElementById("btn-move-b-to-a"),
  btnDeleteSelected: document.getElementById("btn-delete-selected"),

  // Pane A
  selectA: document.getElementById("select-playlist-a"),
  infoA: document.getElementById("info-a"),
  imgA: document.getElementById("img-a"),
  titleA: document.getElementById("title-a"),
  descA: document.getElementById("desc-a"),
  badgeTracksA: document.getElementById("badge-tracks-a"),
  badgeDurationA: document.getElementById("badge-duration-a"),
  btnSplitA: document.getElementById("btn-split-a"),
  btnRenameA: document.getElementById("btn-rename-a"),
  btnDeleteA: document.getElementById("btn-delete-a"),
  filterA: document.getElementById("filter-a"),
  selectAllA: document.getElementById("select-all-a"),
  selectedCountA: document.getElementById("selected-count-a"),
  emptyA: document.getElementById("empty-a"),
  listA: document.getElementById("list-a"),

  // Pane B
  selectB: document.getElementById("select-playlist-b"),
  infoB: document.getElementById("info-b"),
  imgB: document.getElementById("img-b"),
  titleB: document.getElementById("title-b"),
  descB: document.getElementById("desc-b"),
  badgeTracksB: document.getElementById("badge-tracks-b"),
  badgeDurationB: document.getElementById("badge-duration-b"),
  btnSplitB: document.getElementById("btn-split-b"),
  btnRenameB: document.getElementById("btn-rename-b"),
  btnDeleteB: document.getElementById("btn-delete-b"),
  filterB: document.getElementById("filter-b"),
  selectAllB: document.getElementById("select-all-b"),
  selectedCountB: document.getElementById("selected-count-b"),
  emptyB: document.getElementById("empty-b"),
  listB: document.getElementById("list-b"),

  // Modals
  modalCreate: document.getElementById("modal-create"),
  newPlTitle: document.getElementById("new-pl-title"),
  newPlDesc: document.getElementById("new-pl-desc"),
  btnSubmitCreate: document.getElementById("btn-submit-create"),

  modalRename: document.getElementById("modal-rename"),
  renamePlId: document.getElementById("rename-pl-id"),
  renamePlTitle: document.getElementById("rename-pl-title"),
  renamePlDesc: document.getElementById("rename-pl-desc"),
  btnSubmitRename: document.getElementById("btn-submit-rename"),

  modalSplit: document.getElementById("modal-split"),
  splitPlId: document.getElementById("split-pl-id"),
  splitTargetName: document.getElementById("split-target-name"),
  splitCurrentCount: document.getElementById("split-current-count"),
  splitProjectedParts: document.getElementById("split-projected-parts"),
  splitRenameOrig: document.getElementById("split-rename-orig"),
  splitPreviewOrig: document.getElementById("split-preview-orig"),
  splitPreviewNext: document.getElementById("split-preview-next"),
  splitPreviewList: document.getElementById("split-preview-list"),
  splitInProgress: document.getElementById("split-in-progress"),
  btnSubmitSplit: document.getElementById("btn-submit-split"),

  modalConfirm: document.getElementById("modal-confirm"),
  confirmTitle: document.getElementById("confirm-title"),
  confirmMessage: document.getElementById("confirm-message"),
  btnConfirmOk: document.getElementById("btn-confirm-ok"),

  toastContainer: document.getElementById("toast-container"),
};

// ============================================================================
// Notification / Toasts
// ============================================================================

function showToast(message, type = "info", duration = 4000) {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;

  let icon = "ℹ️";
  if (type === "success") icon = "✅";
  if (type === "error") icon = "⚠️";

  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  el.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// ============================================================================
// API Calls Helper
// ============================================================================

async function api(path, options = {}) {
  try {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.message || `Request failed with status ${res.status}`);
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${path}:`, err);
    throw err;
  }
}

// ============================================================================
// Authentication Flow
// ============================================================================

async function checkAuthStatus() {
  try {
    const data = await api("/api/auth/status");
    if (data.logged_in) {
      setAuthenticated(data.user);
      await loadPlaylists();
    } else {
      setUnauthenticated();
    }
  } catch (err) {
    setUnauthenticated();
  }
}

function setAuthenticated(user) {
  state.auth.loggedIn = true;
  state.auth.user = user;

  el.authSection.classList.add("hidden");
  el.dashboardSection.classList.remove("hidden");
  el.userBadge.classList.remove("hidden");
  el.btnNewPlaylist.classList.remove("hidden");
  el.btnRefreshAll.classList.remove("hidden");

  el.userName.textContent = user.username || "TIDAL User";
  el.userCountry.textContent = user.country_code || "US";

  clearInterval(state.pollInterval);
  clearInterval(state.countdownInterval);
}

function setUnauthenticated() {
  state.auth.loggedIn = false;
  state.auth.user = null;

  el.authSection.classList.remove("hidden");
  el.dashboardSection.classList.add("hidden");
  el.userBadge.classList.add("hidden");
  el.btnNewPlaylist.classList.add("hidden");
  el.btnRefreshAll.classList.add("hidden");

  el.loginInitialState.classList.remove("hidden");
  el.loginPendingState.classList.add("hidden");

  clearInterval(state.pollInterval);
  clearInterval(state.countdownInterval);
}

async function startDeviceLogin() {
  try {
    el.btnStartLogin.disabled = true;
    el.btnStartLogin.textContent = "Connecting...";

    const res = await api("/api/auth/start", { method: "POST" });
    el.deviceCode.textContent = res.user_code;
    el.btnOpenTidal.href = res.verification_url;

    el.loginInitialState.classList.add("hidden");
    el.loginPendingState.classList.remove("hidden");

    let secondsLeft = res.expires_in;
    el.loginCountdown.textContent = secondsLeft;

    clearInterval(state.countdownInterval);
    state.countdownInterval = setInterval(() => {
      secondsLeft--;
      el.loginCountdown.textContent = Math.max(0, secondsLeft);
      if (secondsLeft <= 0) {
        clearInterval(state.countdownInterval);
        clearInterval(state.pollInterval);
        showToast("Device login code expired. Please try again.", "error");
        setUnauthenticated();
      }
    }, 1000);

    // Poll status every 2.5 seconds
    clearInterval(state.pollInterval);
    state.pollInterval = setInterval(async () => {
      try {
        const poll = await api("/api/auth/poll");
        if (poll.logged_in) {
          clearInterval(state.pollInterval);
          clearInterval(state.countdownInterval);
          showToast("TIDAL account connected successfully!", "success");
          setAuthenticated(poll.user);
          await loadPlaylists();
        } else if (poll.status === "expired") {
          clearInterval(state.pollInterval);
          clearInterval(state.countdownInterval);
          showToast("Login code expired.", "error");
          setUnauthenticated();
        }
      } catch (e) {
        // Continue polling
      }
    }, 2500);

  } catch (err) {
    showToast(err.message, "error");
  } finally {
    el.btnStartLogin.disabled = false;
    el.btnStartLogin.textContent = "Connect with TIDAL";
  }
}

async function handleLogout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
    showToast("Logged out from TIDAL", "info");
    setUnauthenticated();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ============================================================================
// Playlists Management
// ============================================================================

async function loadPlaylists() {
  try {
    const playlists = await api("/api/playlists");
    state.playlists = playlists;

    populateDropdown(el.selectA, playlists, state.paneA.playlistId);
    populateDropdown(el.selectB, playlists, state.paneB.playlistId);

    // If active playlist is still available, refresh it
    if (state.paneA.playlistId) {
      await loadPlaylistDetails("paneA", state.paneA.playlistId);
    }
    if (state.paneB.playlistId) {
      await loadPlaylistDetails("paneB", state.paneB.playlistId);
    }
  } catch (err) {
    showToast(`Error loading playlists: ${err.message}`, "error");
  }
}

function populateDropdown(selectEl, playlists, currentSelectedId) {
  const prevVal = currentSelectedId || selectEl.value;
  selectEl.innerHTML = '<option value="">-- Choose a Playlist --</option>';

  playlists.forEach((pl) => {
    const opt = document.createElement("option");
    opt.value = pl.id;
    opt.textContent = `${pl.name} (${pl.num_tracks} tracks)`;
    if (pl.id === prevVal) {
      opt.selected = true;
    }
    selectEl.appendChild(opt);
  });
}

async function loadPlaylistDetails(paneKey, playlistId) {
  const isA = paneKey === "paneA";
  const pState = state[paneKey];
  const listEl = isA ? el.listA : el.listB;
  const emptyEl = isA ? el.emptyA : el.emptyB;
  const infoEl = isA ? el.infoA : el.infoB;

  if (!playlistId) {
    pState.playlistId = null;
    pState.details = null;
    pState.tracks = [];
    pState.filteredTracks = [];
    pState.selectedIndices.clear();
    infoEl.classList.add("hidden");
    listEl.classList.add("hidden");
    emptyEl.classList.remove("hidden");
    emptyEl.textContent = "No playlist selected";
    updateSelectionCounter(paneKey);
    return;
  }

  pState.playlistId = playlistId;
  pState.selectedIndices.clear();
  emptyEl.classList.remove("hidden");
  emptyEl.innerHTML = '<div class="spinner"></div> Loading tracks...';
  listEl.classList.add("hidden");

  try {
    const data = await api(`/api/playlists/${playlistId}`);
    pState.details = data;
    pState.tracks = data.tracks || [];
    pState.filteredTracks = [...pState.tracks];

    // Render meta info
    infoEl.classList.remove("hidden");
    emptyEl.classList.add("hidden");

    const imgEl = isA ? el.imgA : el.imgB;
    const titleEl = isA ? el.titleA : el.titleB;
    const descEl = isA ? el.descA : el.descB;
    const badgeTracks = isA ? el.badgeTracksA : el.badgeTracksB;
    const badgeDur = isA ? el.badgeDurationA : el.badgeDurationB;
    const btnSplit = isA ? el.btnSplitA : el.btnSplitB;

    imgEl.src = data.image || "https://resources.tidal.com/images/default.jpg";
    imgEl.onerror = () => { imgEl.src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='80' height='80' fill='%23262a36'><rect width='80' height='80'/></svg>"; };
    titleEl.textContent = data.name;
    descEl.textContent = data.description || "No description";
    badgeTracks.textContent = `${data.num_tracks} tracks`;
    badgeDur.textContent = data.duration_formatted;

    // Highlight split button if > 99 tracks
    if (data.num_tracks > 99) {
      btnSplit.classList.add("split-pill");
      btnSplit.textContent = `⚡ Split (${data.num_tracks} tracks)`;
      btnSplit.title = `This playlist has ${data.num_tracks} tracks (> 99). Click to auto-split!`;
    } else {
      btnSplit.textContent = "⚡ Split (>99)";
      btnSplit.title = `Auto-Split (Currently ${data.num_tracks} tracks)`;
    }

    renderTracksList(paneKey);
  } catch (err) {
    emptyEl.textContent = `Failed to load playlist: ${err.message}`;
    showToast(err.message, "error");
  }
}

function renderTracksList(paneKey) {
  const isA = paneKey === "paneA";
  const pState = state[paneKey];
  const listEl = isA ? el.listA : el.listB;
  const emptyEl = isA ? el.emptyA : el.emptyB;

  listEl.innerHTML = "";

  if (pState.filteredTracks.length === 0) {
    listEl.classList.add("hidden");
    emptyEl.classList.remove("hidden");
    emptyEl.textContent = pState.tracks.length === 0 ? "This playlist is empty." : "No tracks match your filter.";
    updateSelectionCounter(paneKey);
    return;
  }

  emptyEl.classList.add("hidden");
  listEl.classList.remove("hidden");

  pState.filteredTracks.forEach((t) => {
    const isSelected = pState.selectedIndices.has(t.index);
    const row = document.createElement("div");
    row.className = `track-row ${isSelected ? "selected" : ""}`;
    row.dataset.index = t.index;

    row.innerHTML = `
      <input type="checkbox" ${isSelected ? "checked" : ""} class="track-checkbox">
      <span class="track-idx">${t.index + 1}</span>
      <img src="${t.album_image || ''}" class="track-thumb" onerror="this.style.display='none'">
      <div class="track-info">
        <div class="track-name-row">
          <span class="track-name" title="${escapeHtml(t.name)}">${escapeHtml(t.name)}</span>
          ${t.explicit ? '<span class="badge-explicit">E</span>' : ""}
        </div>
        <span class="track-meta" title="${escapeHtml(t.artist)} • ${escapeHtml(t.album)}">${escapeHtml(t.artist)} • ${escapeHtml(t.album)}</span>
      </div>
      <span class="track-dur">${t.duration_formatted}</span>
    `;

    // Click on row to toggle selection
    row.addEventListener("click", (evt) => {
      // Don't trigger twice if clicked directly on checkbox
      if (evt.target.type !== "checkbox") {
        const chk = row.querySelector(".track-checkbox");
        chk.checked = !chk.checked;
      }
      toggleTrackSelection(paneKey, t.index);
    });

    listEl.appendChild(row);
  });

  updateSelectionCounter(paneKey);
}

function toggleTrackSelection(paneKey, trackIndex) {
  const pState = state[paneKey];
  if (pState.selectedIndices.has(trackIndex)) {
    pState.selectedIndices.delete(trackIndex);
  } else {
    pState.selectedIndices.add(trackIndex);
  }

  // Update visual state of that row
  const listEl = paneKey === "paneA" ? el.listA : el.listB;
  const row = listEl.querySelector(`.track-row[data-index="${trackIndex}"]`);
  if (row) {
    const isSelected = pState.selectedIndices.has(trackIndex);
    row.classList.toggle("selected", isSelected);
    const chk = row.querySelector(".track-checkbox");
    if (chk) chk.checked = isSelected;
  }

  updateSelectionCounter(paneKey);
}

function setSelectAll(paneKey, selectAll) {
  const pState = state[paneKey];
  if (selectAll) {
    pState.filteredTracks.forEach((t) => pState.selectedIndices.add(t.index));
  } else {
    pState.selectedIndices.clear();
  }

  const listEl = paneKey === "paneA" ? el.listA : el.listB;
  listEl.querySelectorAll(".track-row").forEach((row) => {
    const idx = parseInt(row.dataset.index, 10);
    const isSelected = pState.selectedIndices.has(idx);
    row.classList.toggle("selected", isSelected);
    const chk = row.querySelector(".track-checkbox");
    if (chk) chk.checked = isSelected;
  });

  updateSelectionCounter(paneKey);
}

function updateSelectionCounter(paneKey) {
  const isA = paneKey === "paneA";
  const pState = state[paneKey];
  const countEl = isA ? el.selectedCountA : el.selectedCountB;
  const selectAllChk = isA ? el.selectAllA : el.selectAllB;

  const count = pState.selectedIndices.size;
  countEl.textContent = `${count} selected`;

  const totalVisible = pState.filteredTracks.length;
  selectAllChk.checked = totalVisible > 0 && count === totalVisible;
  selectAllChk.indeterminate = count > 0 && count < totalVisible;
}

function filterTracks(paneKey, query) {
  const pState = state[paneKey];
  pState.filterQuery = query.toLowerCase().trim();

  if (!pState.filterQuery) {
    pState.filteredTracks = [...pState.tracks];
  } else {
    pState.filteredTracks = pState.tracks.filter((t) => {
      const q = pState.filterQuery;
      return (
        t.name.toLowerCase().includes(q) ||
        t.artist.toLowerCase().includes(q) ||
        t.album.toLowerCase().includes(q)
      );
    });
  }

  renderTracksList(paneKey);
}

// ============================================================================
// Transfer Actions (Copy, Move, Remove)
// ============================================================================

async function transferTracks(fromPaneKey, toPaneKey, isMove = false) {
  const src = state[fromPaneKey];
  const dst = state[toPaneKey];

  if (!src.playlistId) {
    showToast(`Please select a source playlist in ${fromPaneKey === 'paneA' ? 'Panel A' : 'Panel B'}`, "error");
    return;
  }
  if (!dst.playlistId) {
    showToast(`Please select a destination playlist in ${toPaneKey === 'paneA' ? 'Panel A' : 'Panel B'}`, "error");
    return;
  }
  if (src.playlistId === dst.playlistId) {
    showToast("Source and target playlists cannot be the same!", "error");
    return;
  }
  if (src.selectedIndices.size === 0) {
    showToast("Please select at least one track to transfer", "info");
    return;
  }

  const indices = Array.from(src.selectedIndices);
  const actionName = isMove ? "Moving" : "Copying";
  const endpoint = isMove ? "/api/playlists/move" : "/api/playlists/copy";

  showToast(`${actionName} ${indices.length} tracks to '${dst.details?.name || 'playlist'}'...`, "info");

  try {
    const payload = {
      from_id: src.playlistId,
      to_id: dst.playlistId,
      indices: indices,
      allow_duplicates: true,
    };

    const res = await api(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    const count = res.copied_count || res.moved_count || indices.length;
    showToast(`Successfully ${isMove ? 'moved' : 'copied'} ${count} tracks to '${res.to_playlist}'!`, "success");

    // Refresh playlists
    await loadPlaylistDetails(toPaneKey, dst.playlistId);
    if (isMove) {
      await loadPlaylistDetails(fromPaneKey, src.playlistId);
    }

    // Refresh playlist dropdown counts
    await refreshDropdownCounts();
  } catch (err) {
    showToast(`Transfer failed: ${err.message}`, "error");
  }
}

async function removeSelectedTracks() {
  // Determine which pane has selection
  let paneKey = null;
  if (state.paneA.selectedIndices.size > 0) paneKey = "paneA";
  else if (state.paneB.selectedIndices.size > 0) paneKey = "paneB";

  if (!paneKey) {
    showToast("Select tracks in Panel A or Panel B to remove", "info");
    return;
  }

  const pState = state[paneKey];
  const indices = Array.from(pState.selectedIndices);
  const plName = pState.details?.name || "this playlist";

  openConfirmModal(
    "Remove Selected Tracks",
    `Are you sure you want to remove ${indices.length} track(s) from '${plName}'?`,
    async () => {
      try {
        await api(`/api/playlists/${pState.playlistId}/tracks`, {
          method: "DELETE",
          body: JSON.stringify({ indices: indices }),
        });
        showToast(`Removed ${indices.length} tracks from '${plName}'`, "success");
        await loadPlaylistDetails(paneKey, pState.playlistId);
        await refreshDropdownCounts();
      } catch (err) {
        showToast(err.message, "error");
      }
    }
  );
}

async function refreshDropdownCounts() {
  const playlists = await api("/api/playlists");
  state.playlists = playlists;
  populateDropdown(el.selectA, playlists, state.paneA.playlistId);
  populateDropdown(el.selectB, playlists, state.paneB.playlistId);
}

// ============================================================================
// Playlist Modals (Create, Rename, Delete)
// ============================================================================

function openCreateModal() {
  el.newPlTitle.value = "";
  el.newPlDesc.value = "";
  el.modalCreate.classList.remove("hidden");
  el.newPlTitle.focus();
}

async function submitCreatePlaylist() {
  const title = el.newPlTitle.value.trim();
  const desc = el.newPlDesc.value.trim();
  if (!title) {
    showToast("Please enter a playlist title", "error");
    return;
  }

  try {
    const res = await api("/api/playlists", {
      method: "POST",
      body: JSON.stringify({ name: title, description: desc }),
    });

    showToast(`Playlist '${res.name}' created!`, "success");
    closeModal(el.modalCreate);
    await loadPlaylists();

    // Select new playlist in Panel A if none selected, or Panel B
    if (!state.paneA.playlistId) {
      el.selectA.value = res.id;
      await loadPlaylistDetails("paneA", res.id);
    } else {
      el.selectB.value = res.id;
      await loadPlaylistDetails("paneB", res.id);
    }
  } catch (err) {
    showToast(err.message, "error");
  }
}

function openRenameModal(paneKey) {
  const pState = state[paneKey];
  if (!pState.details) {
    showToast("Select a playlist first", "error");
    return;
  }

  el.renamePlId.value = pState.playlistId;
  el.renamePlTitle.value = pState.details.name || "";
  el.renamePlDesc.value = pState.details.description || "";
  el.modalRename.classList.remove("hidden");
  el.renamePlTitle.focus();
}

async function submitRenamePlaylist() {
  const playlistId = el.renamePlId.value;
  const title = el.renamePlTitle.value.trim();
  const desc = el.renamePlDesc.value.trim();

  if (!title) {
    showToast("Title cannot be empty", "error");
    return;
  }

  try {
    const res = await api(`/api/playlists/${playlistId}`, {
      method: "PUT",
      body: JSON.stringify({ name: title, description: desc }),
    });

    showToast(`Renamed playlist to '${res.name}'`, "success");
    closeModal(el.modalRename);
    await loadPlaylists();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function openDeletePlaylistModal(paneKey) {
  const pState = state[paneKey];
  if (!pState.details) {
    showToast("Select a playlist first", "error");
    return;
  }

  const plName = pState.details.name;
  openConfirmModal(
    "Delete Playlist",
    `Are you sure you want to permanently delete playlist '${plName}'? This action cannot be undone.`,
    async () => {
      try {
        await api(`/api/playlists/${pState.playlistId}`, { method: "DELETE" });
        showToast(`Playlist '${plName}' deleted`, "info");
        await loadPlaylists();
        if (state.paneA.playlistId === pState.playlistId) {
          await loadPlaylistDetails("paneA", null);
        }
        if (state.paneB.playlistId === pState.playlistId) {
          await loadPlaylistDetails("paneB", null);
        }
      } catch (err) {
        showToast(err.message, "error");
      }
    }
  );
}

// ============================================================================
// Auto-Split Feature (> 99 Tracks)
// ============================================================================

function openSplitModal(paneKey) {
  const pState = state[paneKey];
  if (!pState.details) {
    showToast("Select a playlist to split", "error");
    return;
  }

  const pl = pState.details;
  state.activeSplitPl = pl;
  const count = pl.num_tracks;

  el.splitPlId.value = pl.id;
  el.splitTargetName.textContent = `'${pl.name}'`;
  el.splitCurrentCount.textContent = count;

  // Calculate base name
  const match = pl.name.match(/^(.*?)(?:\s*[-_]?\s*(\d+))?$/);
  const baseName = (match && match[2]) ? match[1].trim() : pl.name.trim();

  const maxTracks = 99;
  const numParts = Math.max(1, Math.ceil(count / maxTracks));
  el.splitProjectedParts.textContent = numParts;

  el.splitPreviewOrig.textContent = `${baseName} 1`;
  el.splitPreviewNext.textContent = numParts > 1 ? `${baseName} 2, ${baseName} 3...` : "(no extra parts needed)";

  // Build preview cards
  el.splitPreviewList.innerHTML = "";
  for (let p = 1; p <= numParts; p++) {
    const card = document.createElement("div");
    card.className = "split-card-item";

    const startIdx = (p - 1) * maxTracks + 1;
    const endIdx = Math.min(p * maxTracks, count);
    const chunkTracks = count > 0 ? (endIdx - startIdx + 1) : 0;
    const partName = `${baseName} ${p}`;

    card.innerHTML = `
      <span class="split-part-badge">Part ${p}</span>
      <span class="split-part-name">${escapeHtml(partName)}</span>
      <span class="split-part-count">${chunkTracks} tracks (${startIdx} - ${endIdx})</span>
    `;
    el.splitPreviewList.appendChild(card);
  }

  el.splitInProgress.classList.add("hidden");
  el.btnSubmitSplit.disabled = false;
  el.modalSplit.classList.remove("hidden");
}

async function submitAutoSplit() {
  const playlistId = el.splitPlId.value;
  const renameOrig = el.splitRenameOrig.checked;

  try {
    el.splitInProgress.classList.remove("hidden");
    el.btnSubmitSplit.disabled = true;

    const res = await api(`/api/playlists/${playlistId}/split`, {
      method: "POST",
      body: JSON.stringify({
        max_tracks: 99,
        rename_original: renameOrig,
      }),
    });

    closeModal(el.modalSplit);

    if (res.needed_split) {
      showToast(res.message, "success", 6000);
      await loadPlaylists();

      // Automatically display Part 1 in Panel A and Part 2 in Panel B!
      if (res.playlists && res.playlists.length >= 2) {
        el.selectA.value = res.playlists[0].id;
        el.selectB.value = res.playlists[1].id;
        await loadPlaylistDetails("paneA", res.playlists[0].id);
        await loadPlaylistDetails("paneB", res.playlists[1].id);
      } else {
        await loadPlaylistDetails("paneA", playlistId);
      }
    } else {
      showToast(res.message, "info");
    }
  } catch (err) {
    showToast(`Split failed: ${err.message}`, "error");
  } finally {
    el.splitInProgress.classList.add("hidden");
    el.btnSubmitSplit.disabled = false;
  }
}

// ============================================================================
// Confirmation Dialog Helper
// ============================================================================

let onConfirmCallback = null;

function openConfirmModal(title, message, callback) {
  el.confirmTitle.textContent = title;
  el.confirmMessage.textContent = message;
  onConfirmCallback = callback;
  el.modalConfirm.classList.remove("hidden");
}

function closeModal(modalEl) {
  modalEl.classList.add("hidden");
}

// ============================================================================
// Event Listeners Registration
// ============================================================================

function setupEventListeners() {
  // Auth
  el.btnStartLogin.addEventListener("click", startDeviceLogin);
  el.btnLogout.addEventListener("click", handleLogout);
  el.btnCopyCode.addEventListener("click", () => {
    navigator.clipboard.writeText(el.deviceCode.textContent);
    showToast("Device code copied to clipboard!", "success", 2000);
  });

  // Global Actions
  el.btnRefreshAll.addEventListener("click", async () => {
    showToast("Refreshing playlists...", "info");
    await loadPlaylists();
    showToast("Playlists refreshed", "success");
  });
  el.btnNewPlaylist.addEventListener("click", openCreateModal);

  // Pane A Listeners
  el.selectA.addEventListener("change", (e) => loadPlaylistDetails("paneA", e.target.value));
  el.filterA.addEventListener("input", (e) => filterTracks("paneA", e.target.value));
  el.selectAllA.addEventListener("change", (e) => setSelectAll("paneA", e.target.checked));
  el.btnSplitA.addEventListener("click", () => openSplitModal("paneA"));
  el.btnRenameA.addEventListener("click", () => openRenameModal("paneA"));
  el.btnDeleteA.addEventListener("click", () => openDeletePlaylistModal("paneA"));

  // Pane B Listeners
  el.selectB.addEventListener("change", (e) => loadPlaylistDetails("paneB", e.target.value));
  el.filterB.addEventListener("input", (e) => filterTracks("paneB", e.target.value));
  el.selectAllB.addEventListener("change", (e) => setSelectAll("paneB", e.target.checked));
  el.btnSplitB.addEventListener("click", () => openSplitModal("paneB"));
  el.btnRenameB.addEventListener("click", () => openRenameModal("paneB"));
  el.btnDeleteB.addEventListener("click", () => openDeletePlaylistModal("paneB"));

  // Transfer Buttons
  el.btnCopyAToB.addEventListener("click", () => transferTracks("paneA", "paneB", false));
  el.btnMoveAToB.addEventListener("click", () => transferTracks("paneA", "paneB", true));
  el.btnCopyBToA.addEventListener("click", () => transferTracks("paneB", "paneA", false));
  el.btnMoveBToA.addEventListener("click", () => transferTracks("paneB", "paneA", true));
  el.btnDeleteSelected.addEventListener("click", removeSelectedTracks);

  // Modal Submissions
  el.btnSubmitCreate.addEventListener("click", submitCreatePlaylist);
  el.btnSubmitRename.addEventListener("click", submitRenamePlaylist);
  el.btnSubmitSplit.addEventListener("click", submitAutoSplit);
  el.btnConfirmOk.addEventListener("click", async () => {
    closeModal(el.modalConfirm);
    if (onConfirmCallback) {
      await onConfirmCallback();
      onConfirmCallback = null;
    }
  });

  // Modal Closes
  document.querySelectorAll("[data-close]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-close");
      const targetEl = document.getElementById(targetId);
      if (targetEl) closeModal(targetEl);
    });
  });

  // Close modals on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay:not(.hidden)").forEach(closeModal);
    }
  });
}

// Initial Boot
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  checkAuthStatus();
});
