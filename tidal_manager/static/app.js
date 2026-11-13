/**
 * TIDAL Playlist Manager - Frontend Application v1.1
 */

const state = {
  auth: { loggedIn: false, user: null },
  spotify: {
    configured: false,
    authenticated: false,
    user: null,
    pendingPaneSwitch: null,
  },
  playlists: [],
  paneA: {
    platform: "tidal",
    playlistId: null,
    details: null,
    tracks: [],
    filteredTracks: [],
    selectedIndices: new Set(),
    filterQuery: "",
    sortBy: "original",
    sortAscending: true,
    duplicateIndices: new Set(),
  },
  paneB: {
    platform: "tidal",
    playlistId: null,
    details: null,
    tracks: [],
    filteredTracks: [],
    selectedIndices: new Set(),
    filterQuery: "",
    sortBy: "original",
    sortAscending: true,
    duplicateIndices: new Set(),
  },
  audioPlayer: {
    activeTrackId: null,
    isPlaying: false,
  },
  pollInterval: null,
  countdownInterval: null,
  searchDebounce: null,
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

  // Spotify Elements
  spotifyBadge: document.getElementById("spotify-badge"),
  spotifyUserName: document.getElementById("spotify-user-name"),
  btnSpotifyLogout: document.getElementById("btn-spotify-logout"),
  btnSpotifyConnect: document.getElementById("btn-spotify-connect"),
  modalSpotifyConfig: document.getElementById("modal-spotify-config"),
  spotifyClientId: document.getElementById("spotify-client-id"),
  spotifyClientSecret: document.getElementById("spotify-client-secret"),
  spotifyRedirectUriDisplay: document.getElementById("spotify-redirect-uri-display"),
  btnSaveSpotifyConfig: document.getElementById("btn-save-spotify-config"),

  // Transfer Report
  modalTransferReport: document.getElementById("modal-transfer-report"),
  reportTitle: document.getElementById("report-title"),
  reportBadge: document.getElementById("report-badge"),
  reportSummary: document.getElementById("report-summary"),
  reportUnmatchedBox: document.getElementById("report-unmatched-box"),
  reportUnmatchedList: document.getElementById("report-unmatched-list"),

  // Global Header Actions
  btnOpenSearch: document.getElementById("btn-open-search"),
  btnMergePlaylists: document.getElementById("btn-merge-playlists"),
  btnImportPlaylist: document.getElementById("btn-import-playlist"),
  btnNewPlaylist: document.getElementById("btn-new-playlist"),
  btnRefreshAll: document.getElementById("btn-refresh-all"),
  btnOpenHelp: document.getElementById("btn-open-help"),

  // Transfer Dock
  btnCopyAToB: document.getElementById("btn-copy-a-to-b"),
  btnMoveAToB: document.getElementById("btn-move-a-to-b"),
  btnCopyBToA: document.getElementById("btn-copy-b-to-a"),
  btnMoveBToA: document.getElementById("btn-move-b-to-a"),
  btnDeleteSelected: document.getElementById("btn-delete-selected"),

  // Pane A
  paneAEl: document.getElementById("pane-a"),
  selectA: document.getElementById("select-playlist-a"),
  infoA: document.getElementById("info-a"),
  imgA: document.getElementById("img-a"),
  titleA: document.getElementById("title-a"),
  descA: document.getElementById("desc-a"),
  badgeTracksA: document.getElementById("badge-tracks-a"),
  badgeDurationA: document.getElementById("badge-duration-a"),
  badgeDupA: document.getElementById("badge-dup-a"),
  btnSplitA: document.getElementById("btn-split-a"),
  btnDupA: document.getElementById("btn-dup-a"),
  btnRemoveLocalA: document.getElementById("btn-remove-local-a"),
  btnShuffleA: document.getElementById("btn-shuffle-a"),
  btnExportA: document.getElementById("btn-export-a"),
  btnRenameA: document.getElementById("btn-rename-a"),
  btnDeleteA: document.getElementById("btn-delete-a"),
  filterA: document.getElementById("filter-a"),
  sortA: document.getElementById("sort-a"),
  btnSortDirA: document.getElementById("btn-sort-dir-a"),
  btnSaveSortA: document.getElementById("btn-save-sort-a"),
  selectAllA: document.getElementById("select-all-a"),
  selectedCountA: document.getElementById("selected-count-a"),
  btnDeleteSelectedA: document.getElementById("btn-delete-selected-a"),
  emptyA: document.getElementById("empty-a"),
  listA: document.getElementById("list-a"),

  // Pane B
  paneBEl: document.getElementById("pane-b"),
  selectB: document.getElementById("select-playlist-b"),
  infoB: document.getElementById("info-b"),
  imgB: document.getElementById("img-b"),
  titleB: document.getElementById("title-b"),
  descB: document.getElementById("desc-b"),
  badgeTracksB: document.getElementById("badge-tracks-b"),
  badgeDurationB: document.getElementById("badge-duration-b"),
  badgeDupB: document.getElementById("badge-dup-b"),
  btnSplitB: document.getElementById("btn-split-b"),
  btnDupB: document.getElementById("btn-dup-b"),
  btnRemoveLocalB: document.getElementById("btn-remove-local-b"),
  btnShuffleB: document.getElementById("btn-shuffle-b"),
  btnExportB: document.getElementById("btn-export-b"),
  btnRenameB: document.getElementById("btn-rename-b"),
  btnDeleteB: document.getElementById("btn-delete-b"),
  filterB: document.getElementById("filter-b"),
  sortB: document.getElementById("sort-b"),
  btnSortDirB: document.getElementById("btn-sort-dir-b"),
  btnSaveSortB: document.getElementById("btn-save-sort-b"),
  selectAllB: document.getElementById("select-all-b"),
  selectedCountB: document.getElementById("selected-count-b"),
  btnDeleteSelectedB: document.getElementById("btn-delete-selected-b"),
  emptyB: document.getElementById("empty-b"),
  listB: document.getElementById("list-b"),

  // Audio Player Bar
  audioPreviewBar: document.getElementById("audio-preview-bar"),
  audioThumb: document.getElementById("audio-thumb"),
  audioTrackName: document.getElementById("audio-track-name"),
  audioArtistName: document.getElementById("audio-artist-name"),
  btnAudioPlay: document.getElementById("btn-audio-play"),
  iconPlay: document.getElementById("icon-play"),
  iconPause: document.getElementById("icon-pause"),
  audioCurrentTime: document.getElementById("audio-current-time"),
  audioDurationTime: document.getElementById("audio-duration-time"),
  audioSeekBar: document.getElementById("audio-seek-bar"),
  audioProgressFill: document.getElementById("audio-progress-fill"),
  nativeAudio: document.getElementById("native-audio"),
  audioOpenTidal: document.getElementById("audio-open-tidal"),
  btnAudioClose: document.getElementById("btn-audio-close"),

  // Modals
  modalSearch: document.getElementById("modal-search"),
  catalogSearchInput: document.getElementById("catalog-search-input"),
  searchLoading: document.getElementById("search-loading"),
  searchEmpty: document.getElementById("search-empty"),
  searchResultsList: document.getElementById("search-results-list"),

  modalDuplicates: document.getElementById("modal-duplicates"),
  dupPlId: document.getElementById("dup-pl-id"),
  dupTargetName: document.getElementById("dup-target-name"),
  dupBadgeCount: document.getElementById("dup-badge-count"),
  duplicatesList: document.getElementById("duplicates-list"),
  btnSubmitCleanDups: document.getElementById("btn-submit-clean-dups"),

  modalRemoveLocal: document.getElementById("modal-remove-local"),
  removeLocalPlId: document.getElementById("remove-local-pl-id"),
  removeLocalPlatform: document.getElementById("remove-local-platform"),
  removeLocalTargetName: document.getElementById("remove-local-target-name"),
  removeLocalBadgeCount: document.getElementById("remove-local-badge-count"),
  localFolderPath: document.getElementById("local-folder-path"),
  btnScanLocalDir: document.getElementById("btn-scan-local-dir"),
  localScanStatus: document.getElementById("local-scan-status"),
  localScanStatusText: document.getElementById("local-scan-status-text"),
  localMatchesResults: document.getElementById("local-matches-results"),
  localMatchesSummaryText: document.getElementById("local-matches-summary-text"),
  btnLocalSelectAll: document.getElementById("btn-local-select-all"),
  btnLocalDeselectAll: document.getElementById("btn-local-deselect-all"),
  localMatchesList: document.getElementById("local-matches-list"),
  btnSubmitRemoveLocal: document.getElementById("btn-submit-remove-local"),


  modalExport: document.getElementById("modal-export"),
  exportPlId: document.getElementById("export-pl-id"),
  exportPlName: document.getElementById("export-pl-name"),
  btnSubmitExport: document.getElementById("btn-submit-export"),

  modalImport: document.getElementById("modal-import"),
  importDestination: document.getElementById("import-destination"),
  optImportPaneA: document.getElementById("opt-import-pane-a"),
  optImportPaneB: document.getElementById("opt-import-pane-b"),
  importTitleGroup: document.getElementById("import-title-group"),
  importTitle: document.getElementById("import-title"),
  importFile: document.getElementById("import-file"),
  importText: document.getElementById("import-text"),
  btnSubmitImport: document.getElementById("btn-submit-import"),

  modalMerge: document.getElementById("modal-merge"),
  mergePlaylistChecklist: document.getElementById("merge-playlist-checklist"),
  mergeTargetTitle: document.getElementById("merge-target-title"),
  mergeDedupe: document.getElementById("merge-dedupe"),
  btnSubmitMerge: document.getElementById("btn-submit-merge"),

  modalCreate: document.getElementById("modal-create"),
  newPlPlatform: document.getElementById("new-pl-platform"),
  newPlTitle: document.getElementById("new-pl-title"),
  newPlDesc: document.getElementById("new-pl-desc"),
  btnSubmitCreate: document.getElementById("btn-submit-create"),

  modalRename: document.getElementById("modal-rename"),
  renameModalTitle: document.getElementById("rename-modal-title"),
  renamePlId: document.getElementById("rename-pl-id"),
  renamePlPane: document.getElementById("rename-pl-pane"),
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

  modalHelp: document.getElementById("modal-help"),

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
    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = { detail: text || `Request failed with status ${res.status}` };
    }
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
  el.btnOpenSearch.classList.remove("hidden");
  el.btnMergePlaylists.classList.remove("hidden");
  el.btnImportPlaylist.classList.remove("hidden");
  el.btnNewPlaylist.classList.remove("hidden");
  el.btnRefreshAll.classList.remove("hidden");

  const uname = user.username || "TIDAL User";
  el.userName.textContent = uname;
  el.userName.title = uname;
  el.userCountry.textContent = user.country_code || "US";

  checkSpotifyStatus();

  clearInterval(state.pollInterval);
  clearInterval(state.countdownInterval);
}

function setUnauthenticated() {
  state.auth.loggedIn = false;
  state.auth.user = null;

  el.authSection.classList.remove("hidden");
  el.dashboardSection.classList.add("hidden");
  el.userBadge.classList.add("hidden");
  el.spotifyBadge.classList.add("hidden");
  el.btnSpotifyConnect.classList.add("hidden");
  el.btnOpenSearch.classList.add("hidden");
  el.btnMergePlaylists.classList.add("hidden");
  el.btnImportPlaylist.classList.add("hidden");
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
// Spotify Integration & Auth
// ============================================================================

async function checkSpotifyStatus() {
  try {
    const res = await api("/api/spotify/status");
    state.spotify.configured = res.configured;
    state.spotify.authenticated = res.authenticated;
    state.spotify.user = res.user;

    if (el.spotifyRedirectUriDisplay && res.redirect_uri) {
      el.spotifyRedirectUriDisplay.textContent = res.redirect_uri;
    }
    if (el.spotifyClientId && res.client_id) {
      el.spotifyClientId.value = res.client_id;
    }

    if (res.authenticated && res.user) {
      el.spotifyBadge.classList.remove("hidden");
      const spName = res.user.username || "Spotify User";
      el.spotifyUserName.textContent = spName;
      el.spotifyUserName.title = spName;
      el.btnSpotifyConnect.classList.add("hidden");
    } else {
      el.spotifyBadge.classList.add("hidden");
      el.btnSpotifyConnect.classList.remove("hidden");
      if (res.error) {
        showToast(`Spotify: ${res.error}`, "error", 9000);
      }
    }
    return res;
  } catch (err) {
    console.error("Failed to check Spotify status:", err);
    return null;
  }
}

function openSpotifyConfigModal(forPane = null) {
  if (forPane) {
    state.spotify.pendingPaneSwitch = forPane;
  }
  el.modalSpotifyConfig.classList.remove("hidden");
}

async function submitSpotifyConfig() {
  const clientId = el.spotifyClientId.value.trim();
  const clientSecret = el.spotifyClientSecret.value.trim();

  if (!clientId || !clientSecret) {
    showToast("Please enter both Client ID and Client Secret", "error");
    return;
  }

  try {
    await api("/api/spotify/config", {
      method: "POST",
      body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
    });

    const authRes = await api("/api/spotify/auth-url");
    if (authRes.auth_url) {
      const width = 500;
      const height = 700;
      const left = window.screen.width / 2 - width / 2;
      const top = window.screen.height / 2 - height / 2;
      window.open(
        authRes.auth_url,
        "SpotifyAuthorization",
        `width=${width},height=${height},top=${top},left=${left}`
      );
      showToast("Approve the Spotify connection in the popup window...", "info");
      closeModal(el.modalSpotifyConfig);
    }
  } catch (err) {
    showToast(`Spotify configuration failed: ${err.message}`, "error");
  }
}

async function logoutSpotify() {
  try {
    await api("/api/spotify/logout", { method: "POST" });
    showToast("Disconnected from Spotify", "info");
    await checkSpotifyStatus();

    // Revert any pane currently set to Spotify back to TIDAL
    if (state.paneA.platform === "spotify") {
      await handlePlatformSwitch("paneA", "tidal");
    }
    if (state.paneB.platform === "spotify") {
      await handlePlatformSwitch("paneB", "tidal");
    }
  } catch (err) {
    showToast(`Spotify logout failed: ${err.message}`, "error");
  }
}

async function handlePlatformSwitch(paneKey, newPlatform) {
  const pState = state[paneKey];
  if (pState.platform === newPlatform) return;

  if (newPlatform === "spotify") {
    const status = await checkSpotifyStatus();
    if (!status || !status.authenticated) {
      openSpotifyConfigModal(paneKey);
      return;
    }
  }

  pState.platform = newPlatform;
  pState.playlistId = null;
  pState.selectedIndices.clear();

  // Update tabs UI
  document.querySelectorAll(`.platform-tabs[data-pane="${paneKey}"] .platform-tab`).forEach((tab) => {
    tab.classList.toggle("active", tab.dataset.platform === newPlatform);
  });

  // Load playlists for newly selected platform
  await loadPanePlaylists(paneKey);
  showToast(`Switched ${paneKey === "paneA" ? "Panel A" : "Panel B"} to ${newPlatform.toUpperCase()}`, "info", 1500);
}

// ============================================================================
// Playlists Management
// ============================================================================

async function loadPlaylists() {
  await Promise.all([
    loadPanePlaylists("paneA"),
    loadPanePlaylists("paneB"),
  ]);
}

async function loadPanePlaylists(paneKey) {
  const isA = paneKey === "paneA";
  const pState = state[paneKey];
  const selectEl = isA ? el.selectA : el.selectB;

  try {
    const playlists = await api(`/api/${pState.platform}/playlists`);
    pState.playlists = playlists;
    populateDropdown(selectEl, playlists, pState.playlistId);

    if (pState.playlistId) {
      await loadPlaylistDetails(paneKey, pState.playlistId);
    } else {
      await loadPlaylistDetails(paneKey, null);
    }
  } catch (err) {
    showToast(`Error loading ${pState.platform.toUpperCase()} playlists: ${err.message}`, "error");
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
    pState.duplicateIndices.clear();
    infoEl.classList.add("hidden");
    listEl.classList.add("hidden");
    emptyEl.classList.remove("hidden");
    emptyEl.textContent = "No playlist selected";
    updateSelectionCounter(paneKey);
    return;
  }

  pState.playlistId = playlistId;
  pState.selectedIndices.clear();
  pState.duplicateIndices.clear();
  emptyEl.classList.remove("hidden");
  emptyEl.innerHTML = '<div class="spinner"></div> Loading tracks...';
  listEl.classList.add("hidden");

  try {
    const data = await api(`/api/${pState.platform}/playlists/${playlistId}`);
    pState.details = data;
    pState.tracks = data.tracks || [];

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

    if (data.num_tracks > 99) {
      btnSplit.classList.add("split-pill");
      btnSplit.textContent = `⚡ Split (${data.num_tracks} tracks)`;
      btnSplit.title = `This playlist has ${data.num_tracks} tracks (> 99). Click to auto-split!`;
    } else {
      btnSplit.textContent = "⚡ Split (>99)";
      btnSplit.title = `Auto-Split (Currently ${data.num_tracks} tracks)`;
    }

    // Check duplicates in background
    checkDuplicatesBackground(paneKey, playlistId);

    applySortingAndFilter(paneKey);
  } catch (err) {
    emptyEl.textContent = `Failed to load playlist: ${err.message}`;
    showToast(err.message, "error");
  }
}

async function checkDuplicatesBackground(paneKey, playlistId) {
  try {
    const res = await api(`/api/playlists/${playlistId}/duplicates`);
    const isA = paneKey === "paneA";
    const badgeDup = isA ? el.badgeDupA : el.badgeDupB;
    const pState = state[paneKey];

    pState.duplicateIndices = new Set(res.duplicate_indices || []);

    if (res.duplicate_count > 0) {
      badgeDup.textContent = `${res.duplicate_count} dups`;
      badgeDup.classList.remove("hidden");
    } else {
      badgeDup.classList.add("hidden");
    }

    // Refresh row highlighting if tracks are visible
    const listEl = isA ? el.listA : el.listB;
    listEl.querySelectorAll(".track-row").forEach((row) => {
      const idx = parseInt(row.dataset.index, 10);
      row.classList.toggle("is-duplicate", pState.duplicateIndices.has(idx));
    });
  } catch (e) {
    // Non-critical background check
  }
}

// ============================================================================
// Sorting & Filtering
// ============================================================================

function applySortingAndFilter(paneKey) {
  const pState = state[paneKey];
  let list = [...pState.tracks];

  // 1. Filter
  if (pState.filterQuery) {
    const q = pState.filterQuery;
    list = list.filter((t) =>
      t.name.toLowerCase().includes(q) ||
      t.artist.toLowerCase().includes(q) ||
      t.album.toLowerCase().includes(q)
    );
  }

  // 2. Sort
  if (pState.sortBy !== "original") {
    let key = pState.sortBy;
    if (key === "title") key = "name";
    const asc = pState.sortAscending;

    list.sort((a, b) => {
      let valA = a[key] !== undefined ? a[key] : (a.name || "");
      let valB = b[key] !== undefined ? b[key] : (b.name || "");

      if (typeof valA === "number" && typeof valB === "number") {
        return asc ? valA - valB : valB - valA;
      }

      valA = String(valA || "").trim();
      valB = String(valB || "").trim();
      const cmp = valA.localeCompare(valB, undefined, { sensitivity: "base", numeric: true });
      return asc ? cmp : -cmp;
    });
  }

  pState.filteredTracks = list;

  // Show "Save Order" button if non-original sort is active
  const isA = paneKey === "paneA";
  const btnSaveSort = isA ? el.btnSaveSortA : el.btnSaveSortB;
  if (pState.sortBy !== "original") {
    btnSaveSort.classList.remove("hidden");
  } else {
    btnSaveSort.classList.add("hidden");
  }

  renderTracksList(paneKey);
}

function handleSortChange(paneKey, newSort) {
  state[paneKey].sortBy = newSort;
  applySortingAndFilter(paneKey);
}

function handleSortDirToggle(paneKey) {
  const pState = state[paneKey];
  pState.sortAscending = !pState.sortAscending;
  const isA = paneKey === "paneA";
  const btnDir = isA ? el.btnSortDirA : el.btnSortDirB;
  btnDir.querySelector(".sort-dir-arrow").textContent = pState.sortAscending ? "↑" : "↓";
  applySortingAndFilter(paneKey);
}

async function handleSaveSortToTidal(paneKey) {
  const pState = state[paneKey];
  if (!pState.playlistId || pState.sortBy === "original") return;

  openConfirmModal(
    "Save Order to TIDAL",
    `Save this sorted order (${pState.sortBy.toUpperCase()}, ${pState.sortAscending ? 'A-Z' : 'Z-A'}) permanently to TIDAL?`,
    async () => {
      try {
        showToast("Saving sorted playlist order to TIDAL...", "info");
        await api(`/api/playlists/${pState.playlistId}/sort`, {
          method: "POST",
          body: JSON.stringify({
            sort_by: pState.sortBy,
            ascending: pState.sortAscending,
          }),
        });
        showToast("Playlist order saved permanently to TIDAL!", "success");
        // Reset sort to original and reload
        pState.sortBy = "original";
        const isA = paneKey === "paneA";
        const selectSort = isA ? el.sortA : el.sortB;
        selectSort.value = "original";
        await loadPlaylistDetails(paneKey, pState.playlistId);
      } catch (err) {
        showToast(err.message, "error");
      }
    }
  );
}

function filterTracks(paneKey, query) {
  state[paneKey].filterQuery = query.toLowerCase().trim();
  applySortingAndFilter(paneKey);
}

// ============================================================================
// Track Rendering & Drag and Drop
// ============================================================================

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

  pState.filteredTracks.forEach((t, displayIdx) => {
    const isSelected = pState.selectedIndices.has(t.index);
    const isDup = pState.duplicateIndices.has(t.index);
    const isPlaying = state.audioPlayer.activeTrackId === String(t.id) && state.audioPlayer.isPlaying;
    const rowNum = pState.sortBy === "original" ? (t.index + 1) : (displayIdx + 1);

    const row = document.createElement("div");
    row.className = `track-row ${isSelected ? "selected" : ""} ${isDup ? "is-duplicate" : ""}`;
    row.dataset.index = t.index;
    row.dataset.id = t.id;
    row.draggable = true;

    row.innerHTML = `
      <span class="drag-grip" title="Drag to reorder or transfer">⋮⋮</span>
      <input type="checkbox" ${isSelected ? "checked" : ""} class="track-checkbox">
      <span class="track-idx">${rowNum}</span>
      <div class="thumb-wrap ${isPlaying ? "playing" : ""}" data-track-id="${t.id}" title="Play preview">
        <img src="${t.album_image || ''}" class="track-thumb" onerror="this.style.display='none'">
        <div class="play-overlay">
          ${isPlaying ? '⏸' : '▶'}
        </div>
      </div>
      <div class="track-info">
        <div class="track-name-row">
          <span class="track-name" title="${escapeHtml(t.name)}">${escapeHtml(t.name)}</span>
          ${t.explicit ? '<span class="badge-explicit">E</span>' : ""}
        </div>
        <span class="track-meta" title="${escapeHtml(t.artist)} • ${escapeHtml(t.album)}">${escapeHtml(t.artist)} • ${escapeHtml(t.album)}</span>
      </div>
      <div class="track-right">
        <span class="track-dur">${t.duration_formatted}</span>
        <button type="button" class="btn-delete-track" title="Remove track from playlist" data-index="${t.index}">🗑</button>
      </div>
    `;

    // Row click selection
    row.addEventListener("click", (evt) => {
      if (
        evt.target.closest(".thumb-wrap") ||
        evt.target.type === "checkbox" ||
        evt.target.closest(".btn-delete-track")
      ) return;
      const chk = row.querySelector(".track-checkbox");
      chk.checked = !chk.checked;
      toggleTrackSelection(paneKey, t.index);
    });

    // Checkbox click
    const chk = row.querySelector(".track-checkbox");
    chk.addEventListener("click", (evt) => {
      evt.stopPropagation();
      toggleTrackSelection(paneKey, t.index);
    });

    // Delete track button click
    const btnTrackDelete = row.querySelector(".btn-delete-track");
    if (btnTrackDelete) {
      btnTrackDelete.addEventListener("click", (evt) => {
        evt.stopPropagation();
        handleRemoveSingleTrack(paneKey, t.index, t.name);
      });
    }

    // Play button on thumbnail
    const thumbWrap = row.querySelector(".thumb-wrap");
    thumbWrap.addEventListener("click", (evt) => {
      evt.stopPropagation();
      playTrackPreview(t.id);
    });

    // Drag events
    row.addEventListener("dragstart", (evt) => {
      if (!pState.selectedIndices.has(t.index)) {
        pState.selectedIndices.clear();
        pState.selectedIndices.add(t.index);
        updateSelectionCounter(paneKey);
      }

      row.classList.add("dragging");
      const transferData = {
        fromPane: paneKey,
        fromIndex: t.index,
        indices: Array.from(pState.selectedIndices),
        trackIds: Array.from(pState.selectedIndices).map((i) => pState.tracks[i]?.id),
      };
      evt.dataTransfer.setData("application/json", JSON.stringify(transferData));
      evt.dataTransfer.effectAllowed = "copyMove";
    });

    row.addEventListener("dragover", (evt) => {
      evt.preventDefault();
      evt.stopPropagation();
      const rect = row.getBoundingClientRect();
      const isUpper = (evt.clientY - rect.top) < (rect.height / 2);
      row.classList.toggle("drop-before", isUpper);
      row.classList.toggle("drop-after", !isUpper);
    });

    row.addEventListener("dragleave", () => {
      row.classList.remove("drop-before", "drop-after");
    });

    row.addEventListener("drop", async (evt) => {
      row.classList.remove("drop-before", "drop-after");
      const raw = evt.dataTransfer.getData("application/json");
      if (!raw) return;

      try {
        const data = JSON.parse(raw);
        if (data.fromPane === paneKey) {
          // Reorder within the same playlist
          evt.preventDefault();
          evt.stopPropagation();

          const fromIndex = data.fromIndex !== undefined ? data.fromIndex : data.indices[0];
          const rect = row.getBoundingClientRect();
          const isUpper = (evt.clientY - rect.top) < (rect.height / 2);
          let toIndex = parseInt(row.dataset.index, 10);
          if (!isUpper && fromIndex < toIndex) {
            // dropping below a lower item
            toIndex = toIndex;
          }

          if (fromIndex !== undefined && toIndex !== undefined && fromIndex !== toIndex) {
            await handleInPlaylistReorder(paneKey, fromIndex, toIndex);
          }
        }
      } catch (e) {
        console.error("Reorder drop error:", e);
      }
    });

    row.addEventListener("dragend", () => {
      row.classList.remove("dragging");
      document.querySelectorAll(".playlist-pane").forEach((p) => p.classList.remove("drag-over"));
      document.querySelectorAll(".track-row").forEach((r) => r.classList.remove("drop-before", "drop-after"));
    });

    listEl.appendChild(row);
  });

  updateSelectionCounter(paneKey);
}

async function handleInPlaylistReorder(paneKey, fromIndex, toIndex) {
  const pState = state[paneKey];
  if (!pState.playlistId || fromIndex === toIndex) return;

  // Optimistic UI update: move track locally in array
  const [movedItem] = pState.tracks.splice(fromIndex, 1);
  pState.tracks.splice(toIndex, 0, movedItem);
  pState.tracks.forEach((t, i) => t.index = i);
  pState.selectedIndices.clear();
  pState.selectedIndices.add(toIndex);

  applySortingAndFilter(paneKey);

  try {
    await api(`/api/${pState.platform}/playlists/${pState.playlistId}/reorder`, {
      method: "POST",
      body: JSON.stringify({ from_index: fromIndex, to_index: toIndex }),
    });
    showToast(`Reordered track to position #${toIndex + 1}`, "info", 1500);
  } catch (err) {
    showToast(`Failed to save reorder: ${err.message}`, "error");
    await loadPlaylistDetails(paneKey, pState.playlistId);
  }
}

function toggleTrackSelection(paneKey, trackIndex) {
  const pState = state[paneKey];
  if (pState.selectedIndices.has(trackIndex)) {
    pState.selectedIndices.delete(trackIndex);
  } else {
    pState.selectedIndices.add(trackIndex);
  }

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
  const btnDeleteSelected = isA ? el.btnDeleteSelectedA : el.btnDeleteSelectedB;

  const count = pState.selectedIndices.size;
  countEl.textContent = `${count} selected`;

  const totalVisible = pState.filteredTracks.length;
  selectAllChk.checked = totalVisible > 0 && count === totalVisible;
  selectAllChk.indeterminate = count > 0 && count < totalVisible;

  if (btnDeleteSelected) {
    if (count > 0) {
      btnDeleteSelected.textContent = `🗑 Remove (${count})`;
      btnDeleteSelected.classList.remove("hidden");
    } else {
      btnDeleteSelected.classList.add("hidden");
    }
  }
}

// Drag & Drop Pane Listeners
function setupDragAndDrop() {
  [el.paneAEl, el.paneBEl].forEach((pane) => {
    const targetPaneKey = pane.dataset.pane;

    pane.addEventListener("dragover", (evt) => {
      evt.preventDefault();
      pane.classList.add("drag-over");
      evt.dataTransfer.dropEffect = evt.altKey || evt.shiftKey ? "move" : "copy";
    });

    pane.addEventListener("dragleave", (evt) => {
      if (!pane.contains(evt.relatedTarget)) {
        pane.classList.remove("drag-over");
      }
    });

    pane.addEventListener("drop", async (evt) => {
      evt.preventDefault();
      pane.classList.remove("drag-over");

      const raw = evt.dataTransfer.getData("application/json");
      if (!raw) return;

      try {
        const data = JSON.parse(raw);
        const sourcePane = data.fromPane;
        if (sourcePane === targetPaneKey) return; // Dropped on self

        const isMove = evt.altKey || evt.shiftKey;
        await transferTracks(sourcePane, targetPaneKey, isMove);
      } catch (err) {
        console.error("Drop transfer error:", err);
      }
    });
  });
}

// ============================================================================
// Transfer Actions (Copy, Move, Remove)
// ============================================================================

async function transferTracks(fromPaneKey, toPaneKey, isMove = false) {
  const src = state[fromPaneKey];
  const dst = state[toPaneKey];

  if (!src.playlistId) {
    showToast(`Select a source playlist in ${fromPaneKey === 'paneA' ? 'Panel A' : 'Panel B'}`, "error");
    return;
  }
  if (!dst.playlistId) {
    showToast(`Select a destination playlist in ${toPaneKey === 'paneA' ? 'Panel A' : 'Panel B'}`, "error");
    return;
  }
  if (src.platform === dst.platform && src.playlistId === dst.playlistId) {
    showToast("Source and target playlists cannot be the same!", "error");
    return;
  }
  if (src.selectedIndices.size === 0) {
    showToast("Select at least one track to transfer", "info");
    return;
  }

  const indices = Array.from(src.selectedIndices);
  const actionName = isMove ? "Moving" : "Copying";
  const crossDesc = (src.platform !== dst.platform)
    ? ` (${src.platform.toUpperCase()} → ${dst.platform.toUpperCase()})`
    : "";

  showToast(`${actionName} ${indices.length} tracks to '${dst.details?.name || 'playlist'}'${crossDesc}...`, "info");

  try {
    const payload = {
      from_platform: src.platform,
      to_platform: dst.platform,
      from_playlist_id: src.playlistId,
      to_playlist_id: dst.playlistId,
      indices: indices,
      is_move: isMove,
    };

    const res = await api("/api/transfer/universal", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    if (res.unmatched_count > 0) {
      showTransferReport(res);
    } else {
      showToast(res.message, "success");
    }

    await loadPlaylistDetails(toPaneKey, dst.playlistId);
    if (isMove) {
      await loadPlaylistDetails(fromPaneKey, src.playlistId);
    }
    await refreshDropdownCounts();
  } catch (err) {
    showToast(`Transfer failed: ${err.message}`, "error");
  }
}

function showTransferReport(res) {
  el.reportTitle.textContent = res.success ? "Transfer Finished with Warnings" : "Transfer Incomplete";
  el.reportBadge.textContent = `${res.transferred_count} Transferred`;
  el.reportBadge.className = res.transferred_count > 0 ? "badge badge-cyan" : "badge badge-dup";
  el.reportSummary.textContent = res.message;

  if (res.unmatched_tracks && res.unmatched_tracks.length > 0) {
    el.reportUnmatchedBox.classList.remove("hidden");
    el.reportUnmatchedList.innerHTML = res.unmatched_tracks
      .map((t) => `<li>${escapeHtml(t)}</li>`)
      .join("");
  } else {
    el.reportUnmatchedBox.classList.add("hidden");
  }

  el.modalTransferReport.classList.remove("hidden");
}

async function removeSelectedTracksFromPane(paneKey) {
  const pState = state[paneKey];
  if (!pState.details || pState.selectedIndices.size === 0) {
    showToast("No tracks selected to remove", "info");
    return;
  }

  const indices = Array.from(pState.selectedIndices);
  const plName = pState.details?.name || "this playlist";

  openConfirmModal(
    "Remove Selected Tracks",
    `Are you sure you want to remove ${indices.length} track(s) from '${plName}'?`,
    async () => {
      try {
        await api(`/api/${pState.platform}/playlists/${pState.playlistId}/tracks`, {
          method: "DELETE",
          body: JSON.stringify({ indices: indices }),
        });
        showToast(`Removed ${indices.length} tracks from '${plName}'`, "success");
        pState.selectedIndices.clear();
        await loadPlaylistDetails(paneKey, pState.playlistId);
        await refreshDropdownCounts();
      } catch (err) {
        showToast(err.message, "error");
      }
    }
  );
}

async function removeSelectedTracks() {
  if (state.paneA.selectedIndices.size > 0) {
    await removeSelectedTracksFromPane("paneA");
  } else if (state.paneB.selectedIndices.size > 0) {
    await removeSelectedTracksFromPane("paneB");
  } else {
    showToast("Select tracks in Panel A or Panel B to remove", "info");
  }
}

async function handleRemoveSingleTrack(paneKey, trackIndex, trackTitle) {
  const pState = state[paneKey];
  if (!pState.details) return;

  const plName = pState.details?.name || "this playlist";
  const displayTitle = trackTitle ? `'${trackTitle}'` : "this track";

  openConfirmModal(
    "Remove Track from Playlist",
    `Are you sure you want to remove ${displayTitle} from '${plName}'?`,
    async () => {
      try {
        await api(`/api/${pState.platform}/playlists/${pState.playlistId}/tracks`, {
          method: "DELETE",
          body: JSON.stringify({ indices: [trackIndex] }),
        });
        showToast(`Removed ${displayTitle} from '${plName}'`, "success");
        pState.selectedIndices.delete(trackIndex);
        await loadPlaylistDetails(paneKey, pState.playlistId);
        await refreshDropdownCounts();
      } catch (err) {
        showToast(err.message, "error");
      }
    }
  );
}


async function refreshDropdownCounts() {
  await Promise.all([
    loadPanePlaylists("paneA"),
    loadPanePlaylists("paneB"),
  ]);
}

// ============================================================================
// 1. Duplicates Finder & Cleaner
// ============================================================================

async function openDuplicatesModal(paneKey) {
  const pState = state[paneKey];
  if (!pState.details) {
    showToast("Select a playlist first", "error");
    return;
  }

  try {
    showToast("Checking playlist for duplicate tracks...", "info");
    const data = await api(`/api/playlists/${pState.playlistId}/duplicates`);

    el.dupPlId.value = pState.playlistId;
    el.dupTargetName.textContent = `'${pState.details.name}'`;
    el.dupBadgeCount.textContent = `${data.duplicate_count} Duplicates`;

    el.duplicatesList.innerHTML = "";

    if (data.duplicate_count === 0) {
      el.duplicatesList.innerHTML = '<div class="tracks-empty" style="padding: 24px;">✨ No duplicate tracks found in this playlist!</div>';
      el.btnSubmitCleanDups.disabled = true;
    } else {
      el.btnSubmitCleanDups.disabled = false;
      data.groups.forEach((grp) => {
        const card = document.createElement("div");
        card.className = "dup-group-card";
        let tracksHtml = "";
        grp.tracks.forEach((t) => {
          tracksHtml += `<div class="dup-item"><span>#${t.index + 1} - ${escapeHtml(t.name)}</span> <span>${t.duration_formatted}</span></div>`;
        });
        card.innerHTML = `<div class="dup-group-title">${escapeHtml(grp.key)} (${grp.count} copies)</div>${tracksHtml}`;
        el.duplicatesList.appendChild(card);
      });
    }

    el.modalDuplicates.classList.remove("hidden");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function submitCleanDuplicates() {
  const playlistId = el.dupPlId.value;
  try {
    const res = await api(`/api/playlists/${playlistId}/duplicates/clean`, { method: "POST" });
    showToast(res.message, "success");
    closeModal(el.modalDuplicates);
    if (state.paneA.playlistId === playlistId) await loadPlaylistDetails("paneA", playlistId);
    if (state.paneB.playlistId === playlistId) await loadPlaylistDetails("paneB", playlistId);
    await refreshDropdownCounts();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ============================================================================
// Remove Locally Available Tracks
// ============================================================================

function openRemoveLocalModal(paneKey) {
  const pState = state[paneKey];
  if (!pState.details) {
    showToast("Select a playlist first", "error");
    return;
  }

  el.removeLocalPlId.value = pState.playlistId;
  el.removeLocalPlatform.value = pState.platform || "tidal";
  el.removeLocalTargetName.textContent = `'${pState.details.name}'`;
  el.removeLocalBadgeCount.classList.add("hidden");
  el.localScanStatus.classList.add("hidden");
  el.localMatchesResults.classList.add("hidden");
  el.localMatchesList.innerHTML = "";
  el.btnSubmitRemoveLocal.disabled = true;
  el.btnSubmitRemoveLocal.textContent = "Remove Selected from Playlist";

  el.modalRemoveLocal.classList.remove("hidden");
}

function updateLocalMatchesSubmitButton() {
  const checkedBoxes = el.localMatchesList.querySelectorAll(".local-match-checkbox:checked");
  const count = checkedBoxes.length;
  if (count === 0) {
    el.btnSubmitRemoveLocal.disabled = true;
    el.btnSubmitRemoveLocal.textContent = "Remove Selected from Playlist";
  } else {
    el.btnSubmitRemoveLocal.disabled = false;
    el.btnSubmitRemoveLocal.textContent = `Remove ${count} Selected from Playlist`;
  }
}

async function startLocalDirectoryScan() {
  const dirPath = el.localFolderPath.value.trim();
  if (!dirPath) {
    showToast("Please enter a local directory path", "warning");
    return;
  }

  const platform = el.removeLocalPlatform.value || "tidal";
  const playlistId = el.removeLocalPlId.value;

  try {
    el.btnScanLocalDir.disabled = true;
    el.localScanStatus.classList.remove("hidden");
    el.localMatchesResults.classList.add("hidden");
    el.localMatchesList.innerHTML = "";

    const res = await api(`/api/${platform}/playlists/${playlistId}/match-local`, {
      method: "POST",
      body: JSON.stringify({ directory_path: dirPath }),
    });

    el.localScanStatus.classList.add("hidden");
    el.btnScanLocalDir.disabled = false;

    if (res.matched_count === 0) {
      el.removeLocalBadgeCount.classList.add("hidden");
      el.localMatchesSummaryText.textContent = `Scanned ${res.scanned_files_count} local audio files. No matches found in this playlist!`;
      el.localMatchesList.innerHTML = '<div class="tracks-empty" style="padding: 24px;">✨ All tracks in this playlist are unique (not found in your local folder).</div>';
      el.btnSubmitRemoveLocal.disabled = true;
      el.btnSubmitRemoveLocal.textContent = "Remove Selected from Playlist";
    } else {
      el.removeLocalBadgeCount.textContent = `${res.matched_count} Matches`;
      el.removeLocalBadgeCount.classList.remove("hidden");
      el.localMatchesSummaryText.textContent = `Scanned ${res.scanned_files_count} local files. Found ${res.matched_count} matching tracks:`;

      res.matches.forEach((m) => {
        const row = document.createElement("div");
        row.className = "local-match-row";
        row.innerHTML = `
          <input type="checkbox" class="local-match-checkbox" data-index="${m.index}" checked>
          <div class="local-match-info">
            <div class="local-match-header">
              <span class="local-match-track">#${m.index + 1} - ${escapeHtml(m.track_name)} &bull; ${escapeHtml(m.artist_name)}</span>
              <span class="local-match-type-tag">${escapeHtml(m.match_type.toUpperCase())}</span>
            </div>
            <div class="local-match-file" title="${escapeHtml(m.local_file_path)}">📁 ${escapeHtml(m.local_filename)}</div>
          </div>
        `;

        const cb = row.querySelector(".local-match-checkbox");
        cb.addEventListener("change", updateLocalMatchesSubmitButton);
        el.localMatchesList.appendChild(row);
      });

      updateLocalMatchesSubmitButton();
    }

    el.localMatchesResults.classList.remove("hidden");
  } catch (err) {
    el.localScanStatus.classList.add("hidden");
    el.btnScanLocalDir.disabled = false;
    showToast(err.message, "error");
  }
}

async function submitRemoveLocalTracks() {
  const checkboxes = el.localMatchesList.querySelectorAll(".local-match-checkbox:checked");
  const indices = Array.from(checkboxes).map((cb) => parseInt(cb.dataset.index, 10));
  if (indices.length === 0) {
    showToast("No tracks selected for removal", "warning");
    return;
  }

  const platform = el.removeLocalPlatform.value || "tidal";
  const playlistId = el.removeLocalPlId.value;
  const targetName = el.removeLocalTargetName.textContent;

  openConfirmModal(
    "Confirm Removal",
    `Are you sure you want to remove ${indices.length} locally available track(s) from ${targetName} on ${platform.toUpperCase()}?`,
    async () => {
      try {
        const res = await api(`/api/${platform}/playlists/${playlistId}/remove-local`, {
          method: "POST",
          body: JSON.stringify({ indices }),
        });
        showToast(`Successfully removed ${res.removed_count} tracks from ${targetName}!`, "success");
        closeModal(el.modalRemoveLocal);
        if (state.paneA.playlistId === playlistId) await loadPlaylistDetails("paneA", playlistId);
        if (state.paneB.playlistId === playlistId) await loadPlaylistDetails("paneB", playlistId);
        await refreshDropdownCounts();
      } catch (err) {
        showToast(err.message, "error");
      }
    }
  );
}



// ============================================================================
// 2. Backup & Export / Import
// ============================================================================

function openExportModal(paneKey) {
  const pState = state[paneKey];
  if (!pState.details) {
    showToast("Select a playlist to export", "error");
    return;
  }
  el.exportPlId.value = pState.playlistId;
  el.exportPlName.textContent = `'${pState.details.name}'`;
  el.modalExport.classList.remove("hidden");
}

function submitExportPlaylist() {
  const playlistId = el.exportPlId.value;
  const fmt = document.querySelector('input[name="export-fmt"]:checked')?.value || "json";
  const url = `/api/playlists/${playlistId}/export?format=${fmt}`;
  window.open(url, "_blank");
  closeModal(el.modalExport);
  showToast(`Downloading ${fmt.toUpperCase()} backup...`, "info");
}

function openImportModal() {
  el.importTitle.value = "";
  el.importFile.value = "";
  el.importText.value = "";
  el.importDestination.value = "new";
  el.importTitleGroup.classList.remove("hidden");

  // Configure Panel A option
  if (state.paneA.playlistId && state.paneA.details) {
    el.optImportPaneA.textContent = `📥 Append to Panel A: ${state.paneA.details.name}`;
    el.optImportPaneA.disabled = false;
  } else {
    el.optImportPaneA.textContent = "📥 Append to Panel A (No playlist selected)";
    el.optImportPaneA.disabled = true;
  }

  // Configure Panel B option
  if (state.paneB.playlistId && state.paneB.details) {
    el.optImportPaneB.textContent = `📥 Append to Panel B: ${state.paneB.details.name}`;
    el.optImportPaneB.disabled = false;
  } else {
    el.optImportPaneB.textContent = "📥 Append to Panel B (No playlist selected)";
    el.optImportPaneB.disabled = true;
  }

  el.modalImport.classList.remove("hidden");
}

async function submitImportPlaylist() {
  const dest = el.importDestination.value;
  const title = el.importTitle.value.trim();
  let content = el.importText.value.trim();
  const file = el.importFile.files[0];

  if (!content && file) {
    content = await file.text();
  }

  if (!content) {
    showToast("Please select a file or paste content to import", "error");
    return;
  }

  let targetId = null;
  if (dest === "paneA") {
    targetId = state.paneA.playlistId;
  } else if (dest === "paneB") {
    targetId = state.paneB.playlistId;
  }

  try {
    showToast(targetId ? "Appending imported tracks..." : "Creating new imported playlist on TIDAL...", "info");
    const res = await api("/api/playlists/import", {
      method: "POST",
      body: JSON.stringify({
        title: title || (file ? file.name.replace(/\.[^/.]+$/, "") : "Imported Playlist"),
        content: content,
        format_type: "auto",
        target_playlist_id: targetId,
      }),
    });

    if (res.mode === "appended") {
      showToast(`Successfully added ${res.imported_tracks_count} tracks to '${res.title}'!`, "success");
      closeModal(el.modalImport);
      if (dest === "paneA") {
        await loadPlaylistDetails("paneA", targetId);
      } else {
        await loadPlaylistDetails("paneB", targetId);
      }
      await refreshDropdownCounts();
    } else {
      showToast(`Successfully created playlist '${res.title}' with ${res.imported_tracks_count} tracks!`, "success");
      closeModal(el.modalImport);
      await loadPlaylists();

      if (!state.paneA.playlistId) {
        el.selectA.value = res.playlist_id;
        await loadPlaylistDetails("paneA", res.playlist_id);
      } else {
        el.selectB.value = res.playlist_id;
        await loadPlaylistDetails("paneB", res.playlist_id);
      }
    }
  } catch (err) {
    showToast(`Import failed: ${err.message}`, "error");
  }
}

// ============================================================================
// 3. Merge & Shuffle
// ============================================================================

function openMergeModal() {
  if (state.playlists.length < 2) {
    showToast("You need at least 2 playlists to merge", "info");
    return;
  }

  el.mergeTargetTitle.value = "Merged Playlist";
  el.mergePlaylistChecklist.innerHTML = "";

  state.playlists.forEach((pl) => {
    const item = document.createElement("label");
    item.className = "checklist-item";
    item.innerHTML = `
      <input type="checkbox" value="${pl.id}" class="merge-chk">
      <span><strong>${escapeHtml(pl.name)}</strong> (${pl.num_tracks} tracks)</span>
    `;
    el.mergePlaylistChecklist.appendChild(item);
  });

  el.modalMerge.classList.remove("hidden");
}

async function submitMergePlaylists() {
  const checked = Array.from(document.querySelectorAll(".merge-chk:checked")).map((c) => c.value);
  const targetTitle = el.mergeTargetTitle.value.trim();
  const dedupe = el.mergeDedupe.checked;

  if (checked.length < 2) {
    showToast("Please check at least 2 playlists to merge", "error");
    return;
  }
  if (!targetTitle) {
    showToast("Please provide a title for the merged playlist", "error");
    return;
  }

  try {
    showToast("Merging playlists...", "info");
    const res = await api("/api/playlists/merge", {
      method: "POST",
      body: JSON.stringify({
        source_ids: checked,
        target_title: targetTitle,
        deduplicate: dedupe,
      }),
    });

    showToast(`Created merged playlist '${res.title}' with ${res.total_tracks} tracks!`, "success");
    closeModal(el.modalMerge);
    await loadPlaylists();
    el.selectB.value = res.merged_playlist_id;
    await loadPlaylistDetails("paneB", res.merged_playlist_id);
  } catch (err) {
    showToast(`Merge failed: ${err.message}`, "error");
  }
}

async function handleShufflePlaylist(paneKey) {
  const pState = state[paneKey];
  if (!pState.details) {
    showToast("Select a playlist to shuffle", "error");
    return;
  }

  openConfirmModal(
    "Shuffle Playlist",
    `Randomly shuffle the track order of '${pState.details.name}' in TIDAL?`,
    async () => {
      try {
        showToast("Shuffling playlist on TIDAL...", "info");
        const res = await api(`/api/playlists/${pState.playlistId}/shuffle`, { method: "POST" });
        showToast(res.message, "success");
        await loadPlaylistDetails(paneKey, pState.playlistId);
      } catch (err) {
        showToast(err.message, "error");
      }
    }
  );
}

// ============================================================================
// 5. Audio Preview Player
// ============================================================================

async function playTrackPreview(trackId) {
  // If already playing this track, toggle pause/play
  if (state.audioPlayer.activeTrackId === String(trackId)) {
    if (state.audioPlayer.isPlaying) {
      el.nativeAudio.pause();
      state.audioPlayer.isPlaying = false;
      updateAudioPlayerUI();
      renderActiveTrackPlayingState();
    } else {
      el.nativeAudio.play();
      state.audioPlayer.isPlaying = true;
      updateAudioPlayerUI();
      renderActiveTrackPlayingState();
    }
    return;
  }

  try {
    showToast("Loading audio preview...", "info", 1500);
    const data = await api(`/api/tracks/${trackId}/preview`);

    state.audioPlayer.activeTrackId = String(trackId);
    el.audioTrackName.textContent = data.name || "Track";
    el.audioArtistName.textContent = data.artist || "";
    el.audioThumb.src = data.album_image || "";
    el.audioOpenTidal.href = data.web_url;
    el.audioPreviewBar.classList.remove("hidden");

    if (data.preview_url) {
      el.nativeAudio.src = data.preview_url;
      el.nativeAudio.play().then(() => {
        state.audioPlayer.isPlaying = true;
        updateAudioPlayerUI();
        renderActiveTrackPlayingState();
      }).catch((e) => {
        console.warn("Autoplay prevented:", e);
        state.audioPlayer.isPlaying = false;
        updateAudioPlayerUI();
      });
    } else {
      // Stream URL not directly available via API token; open TIDAL web player
      showToast("Direct audio preview restricted for this track. Use 'Open in TIDAL' to listen.", "info");
      state.audioPlayer.isPlaying = false;
      updateAudioPlayerUI();
    }
  } catch (err) {
    showToast(`Could not load preview: ${err.message}`, "error");
  }
}

function updateAudioPlayerUI() {
  if (state.audioPlayer.isPlaying) {
    el.iconPlay.classList.add("hidden");
    el.iconPause.classList.remove("hidden");
  } else {
    el.iconPlay.classList.remove("hidden");
    el.iconPause.classList.add("hidden");
  }
}

function renderActiveTrackPlayingState() {
  document.querySelectorAll(".thumb-wrap").forEach((w) => {
    const tid = w.dataset.trackId;
    const isPlaying = tid === state.audioPlayer.activeTrackId && state.audioPlayer.isPlaying;
    w.classList.toggle("playing", isPlaying);
    const overlay = w.querySelector(".play-overlay");
    if (overlay) overlay.textContent = isPlaying ? "⏸" : "▶";
  });
}

function setupAudioPlayerEvents() {
  el.btnAudioPlay.addEventListener("click", () => {
    if (state.audioPlayer.isPlaying) {
      el.nativeAudio.pause();
    } else {
      el.nativeAudio.play();
    }
  });

  el.nativeAudio.addEventListener("play", () => {
    state.audioPlayer.isPlaying = true;
    updateAudioPlayerUI();
    renderActiveTrackPlayingState();
  });

  el.nativeAudio.addEventListener("pause", () => {
    state.audioPlayer.isPlaying = false;
    updateAudioPlayerUI();
    renderActiveTrackPlayingState();
  });

  el.nativeAudio.addEventListener("timeupdate", () => {
    const cur = el.nativeAudio.currentTime;
    const dur = el.nativeAudio.duration || 30;
    const pct = (cur / dur) * 100;
    el.audioProgressFill.style.width = `${pct}%`;

    const m = Math.floor(cur / 60);
    const s = Math.floor(cur % 60);
    el.audioCurrentTime.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
  });

  el.nativeAudio.addEventListener("loadedmetadata", () => {
    const dur = el.nativeAudio.duration;
    if (dur && !isNaN(dur)) {
      const m = Math.floor(dur / 60);
      const s = Math.floor(dur % 60);
      el.audioDurationTime.textContent = `${m}:${s < 10 ? '0' : ''}${s}`;
    }
  });

  el.audioSeekBar.addEventListener("click", (evt) => {
    const rect = el.audioSeekBar.getBoundingClientRect();
    const pos = (evt.clientX - rect.left) / rect.width;
    const dur = el.nativeAudio.duration;
    if (dur) {
      el.nativeAudio.currentTime = pos * dur;
    }
  });

  el.btnAudioClose.addEventListener("click", () => {
    el.nativeAudio.pause();
    el.nativeAudio.src = "";
    state.audioPlayer.activeTrackId = null;
    state.audioPlayer.isPlaying = false;
    el.audioPreviewBar.classList.add("hidden");
    renderActiveTrackPlayingState();
  });
}

// ============================================================================
// 7. TIDAL Catalog Search
// ============================================================================

function openSearchModal() {
  el.catalogSearchInput.value = "";
  el.searchResultsList.innerHTML = "";
  el.searchResultsList.classList.add("hidden");
  el.searchEmpty.classList.remove("hidden");
  el.searchLoading.classList.add("hidden");
  el.modalSearch.classList.remove("hidden");
  setTimeout(() => el.catalogSearchInput.focus(), 50);
}

function handleSearchInput(query) {
  clearTimeout(state.searchDebounce);
  const q = query.trim();

  if (!q) {
    el.searchResultsList.classList.add("hidden");
    el.searchEmpty.classList.remove("hidden");
    el.searchLoading.classList.add("hidden");
    return;
  }

  el.searchEmpty.classList.add("hidden");
  el.searchLoading.classList.remove("hidden");
  el.searchResultsList.classList.add("hidden");

  state.searchDebounce = setTimeout(async () => {
    try {
      const results = await api(`/api/search?q=${encodeURIComponent(q)}&limit=25`);
      renderSearchResults(results);
    } catch (err) {
      el.searchLoading.classList.add("hidden");
      el.searchEmpty.textContent = `Search error: ${err.message}`;
      el.searchEmpty.classList.remove("hidden");
    }
  }, 350);
}

function renderSearchResults(tracks) {
  el.searchLoading.classList.add("hidden");
  el.searchResultsList.innerHTML = "";

  if (!tracks || tracks.length === 0) {
    el.searchEmpty.textContent = "No tracks found on TIDAL.";
    el.searchEmpty.classList.remove("hidden");
    el.searchResultsList.classList.add("hidden");
    return;
  }

  el.searchEmpty.classList.add("hidden");
  el.searchResultsList.classList.remove("hidden");

  tracks.forEach((t) => {
    const row = document.createElement("div");
    row.className = "search-track-row";

    row.innerHTML = `
      <div class="search-track-info">
        <div class="thumb-wrap" data-track-id="${t.id}" title="Preview audio">
          <img src="${t.album_image || ''}" class="track-thumb" onerror="this.style.display='none'">
          <div class="play-overlay">▶</div>
        </div>
        <div class="track-info">
          <div class="track-name-row">
            <span class="track-name">${escapeHtml(t.name)}</span>
            ${t.explicit ? '<span class="badge-explicit">E</span>' : ""}
          </div>
          <span class="track-meta">${escapeHtml(t.artist)} • ${escapeHtml(t.album)}</span>
        </div>
        <span class="track-dur">${t.duration_formatted}</span>
      </div>
      <div class="search-track-btns">
        <button class="btn btn-action-pill btn-add-pane-a" title="Add to Panel A">+ Panel A</button>
        <button class="btn btn-action-pill btn-add-pane-b" title="Add to Panel B">+ Panel B</button>
      </div>
    `;

    // Preview
    row.querySelector(".thumb-wrap").addEventListener("click", () => playTrackPreview(t.id));

    // Add to Pane A
    row.querySelector(".btn-add-pane-a").addEventListener("click", async () => {
      if (!state.paneA.playlistId) {
        showToast("Select a playlist in Panel A first", "error");
        return;
      }
      await addSingleTrackToPlaylist("paneA", state.paneA.playlistId, t.id, t.name);
    });

    // Add to Pane B
    row.querySelector(".btn-add-pane-b").addEventListener("click", async () => {
      if (!state.paneB.playlistId) {
        showToast("Select a playlist in Panel B first", "error");
        return;
      }
      await addSingleTrackToPlaylist("paneB", state.paneB.playlistId, t.id, t.name);
    });

    el.searchResultsList.appendChild(row);
  });
}

async function addSingleTrackToPlaylist(paneKey, playlistId, trackId, trackName) {
  try {
    await api(`/api/playlists/copy`, {
      method: "POST",
      body: JSON.stringify({
        from_id: playlistId,
        to_id: playlistId,
        track_ids: [String(trackId)],
      }),
    });
    showToast(`Added '${trackName}' to playlist!`, "success");
    await loadPlaylistDetails(paneKey, playlistId);
    await refreshDropdownCounts();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ============================================================================
// Modals & Splits
// ============================================================================

function openCreateModal() {
  el.newPlTitle.value = "";
  el.newPlDesc.value = "";
  if (el.newPlPlatform) {
    el.newPlPlatform.value = state.paneA.platform || "tidal";
  }
  el.modalCreate.classList.remove("hidden");
  el.newPlTitle.focus();
}

async function submitCreatePlaylist() {
  const title = el.newPlTitle.value.trim();
  const desc = el.newPlDesc.value.trim();
  const platform = el.newPlPlatform ? el.newPlPlatform.value : "tidal";
  if (!title) {
    showToast("Please enter a playlist title", "error");
    return;
  }

  if (platform === "spotify" && !state.spotify.authenticated) {
    showToast("Please connect Spotify first before creating a Spotify playlist", "error");
    openSpotifyConfigModal();
    return;
  }

  try {
    const res = await api(`/api/${platform}/playlists`, {
      method: "POST",
      body: JSON.stringify({ name: title, description: desc }),
    });

    showToast(`Playlist '${res.name}' created on ${platform.toUpperCase()}!`, "success");
    closeModal(el.modalCreate);
    await loadPlaylists();

    if (state.paneA.platform === platform && !state.paneA.playlistId) {
      el.selectA.value = res.id;
      await loadPlaylistDetails("paneA", res.id);
    } else if (state.paneB.platform === platform) {
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
  if (el.renamePlPane) el.renamePlPane.value = paneKey;
  if (el.renameModalTitle) {
    el.renameModalTitle.textContent = `Rename ${pState.platform.toUpperCase()} Playlist`;
  }
  el.renamePlTitle.value = pState.details.name || "";
  el.renamePlDesc.value = pState.details.description || "";
  el.modalRename.classList.remove("hidden");
  el.renamePlTitle.focus();
}

async function submitRenamePlaylist() {
  const playlistId = el.renamePlId.value;
  const paneKey = el.renamePlPane?.value || "paneA";
  const platform = state[paneKey]?.platform || "tidal";
  const title = el.renamePlTitle.value.trim();
  const desc = el.renamePlDesc.value.trim();

  if (!title) {
    showToast("Title cannot be empty", "error");
    return;
  }

  try {
    const res = await api(`/api/${platform}/playlists/${playlistId}`, {
      method: "PUT",
      body: JSON.stringify({ name: title, description: desc }),
    });

    showToast(`Renamed playlist to '${res.name}'`, "success");
    closeModal(el.modalRename);
    await loadPanePlaylists(paneKey);
    if (state[paneKey].playlistId === playlistId) {
      await loadPlaylistDetails(paneKey, playlistId);
    }
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
  const platform = pState.platform || "tidal";
  openConfirmModal(
    `Delete ${platform.toUpperCase()} Playlist`,
    `Are you sure you want to permanently delete playlist '${plName}' on ${platform.toUpperCase()}? This action cannot be undone.`,
    async () => {
      try {
        await api(`/api/${platform}/playlists/${pState.playlistId}`, { method: "DELETE" });
        showToast(`Playlist '${plName}' deleted from ${platform.toUpperCase()}`, "info");
        await loadPanePlaylists(paneKey);
        await loadPlaylistDetails(paneKey, null);
      } catch (err) {
        showToast(err.message, "error");
      }
    }
  );
}

function openSplitModal(paneKey) {
  const pState = state[paneKey];
  if (!pState.details) {
    showToast("Select a playlist to split", "error");
    return;
  }

  const pl = pState.details;
  const count = pl.num_tracks;

  el.splitPlId.value = pl.id;
  el.splitTargetName.textContent = `'${pl.name}'`;
  el.splitCurrentCount.textContent = count;

  const match = pl.name.match(/^(.*?)(?:\s*[-_]?\s*(\d+))?$/);
  const baseName = (match && match[2]) ? match[1].trim() : pl.name.trim();

  const maxTracks = 99;
  const numParts = Math.max(1, Math.ceil(count / maxTracks));
  el.splitProjectedParts.textContent = numParts;

  el.splitPreviewOrig.textContent = `${baseName} 1`;
  el.splitPreviewNext.textContent = numParts > 1 ? `${baseName} 2, ${baseName} 3...` : "(no extra parts needed)";

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
  el.btnMergePlaylists.addEventListener("click", openMergeModal);
  el.btnImportPlaylist.addEventListener("click", openImportModal);
  el.btnOpenSearch.addEventListener("click", openSearchModal);
  if (el.btnOpenHelp && el.modalHelp) {
    el.btnOpenHelp.addEventListener("click", () => {
      el.modalHelp.classList.remove("hidden");
    });
  }

  // Pane A Listeners
  el.selectA.addEventListener("change", (e) => loadPlaylistDetails("paneA", e.target.value));
  el.filterA.addEventListener("input", (e) => filterTracks("paneA", e.target.value));
  el.selectAllA.addEventListener("change", (e) => setSelectAll("paneA", e.target.checked));
  el.sortA.addEventListener("change", (e) => handleSortChange("paneA", e.target.value));
  el.btnSortDirA.addEventListener("click", () => handleSortDirToggle("paneA"));
  el.btnSaveSortA.addEventListener("click", () => handleSaveSortToTidal("paneA"));
  el.btnSplitA.addEventListener("click", () => openSplitModal("paneA"));
  el.btnDupA.addEventListener("click", () => openDuplicatesModal("paneA"));
  el.btnRemoveLocalA.addEventListener("click", () => openRemoveLocalModal("paneA"));
  el.btnShuffleA.addEventListener("click", () => handleShufflePlaylist("paneA"));
  el.btnExportA.addEventListener("click", () => openExportModal("paneA"));
  el.btnRenameA.addEventListener("click", () => openRenameModal("paneA"));
  el.btnDeleteA.addEventListener("click", () => openDeletePlaylistModal("paneA"));

  // Pane B Listeners
  el.selectB.addEventListener("change", (e) => loadPlaylistDetails("paneB", e.target.value));
  el.filterB.addEventListener("input", (e) => filterTracks("paneB", e.target.value));
  el.selectAllB.addEventListener("change", (e) => setSelectAll("paneB", e.target.checked));
  el.sortB.addEventListener("change", (e) => handleSortChange("paneB", e.target.value));
  el.btnSortDirB.addEventListener("click", () => handleSortDirToggle("paneB"));
  el.btnSaveSortB.addEventListener("click", () => handleSaveSortToTidal("paneB"));
  el.btnSplitB.addEventListener("click", () => openSplitModal("paneB"));
  el.btnDupB.addEventListener("click", () => openDuplicatesModal("paneB"));
  el.btnRemoveLocalB.addEventListener("click", () => openRemoveLocalModal("paneB"));
  el.btnShuffleB.addEventListener("click", () => handleShufflePlaylist("paneB"));
  el.btnExportB.addEventListener("click", () => openExportModal("paneB"));
  el.btnRenameB.addEventListener("click", () => openRenameModal("paneB"));
  el.btnDeleteB.addEventListener("click", () => openDeletePlaylistModal("paneB"));

  // Transfer Buttons
  el.btnCopyAToB.addEventListener("click", () => transferTracks("paneA", "paneB", false));
  el.btnMoveAToB.addEventListener("click", () => transferTracks("paneA", "paneB", true));
  el.btnCopyBToA.addEventListener("click", () => transferTracks("paneB", "paneA", false));
  el.btnMoveBToA.addEventListener("click", () => transferTracks("paneB", "paneA", true));
  el.btnDeleteSelected.addEventListener("click", removeSelectedTracks);
  if (el.btnDeleteSelectedA) {
    el.btnDeleteSelectedA.addEventListener("click", () => removeSelectedTracksFromPane("paneA"));
  }
  if (el.btnDeleteSelectedB) {
    el.btnDeleteSelectedB.addEventListener("click", () => removeSelectedTracksFromPane("paneB"));
  }

  // Catalog Search Input
  el.catalogSearchInput.addEventListener("input", (e) => handleSearchInput(e.target.value));

  // Modal Submissions
  el.importDestination.addEventListener("change", (e) => {
    if (e.target.value === "new") {
      el.importTitleGroup.classList.remove("hidden");
    } else {
      el.importTitleGroup.classList.add("hidden");
    }
  });
  el.btnSubmitCreate.addEventListener("click", submitCreatePlaylist);
  el.btnSubmitRename.addEventListener("click", submitRenamePlaylist);
  el.btnSubmitSplit.addEventListener("click", submitAutoSplit);
  el.btnSubmitCleanDups.addEventListener("click", submitCleanDuplicates);
  el.btnSubmitExport.addEventListener("click", submitExportPlaylist);
  el.btnSubmitImport.addEventListener("click", submitImportPlaylist);
  el.btnSubmitMerge.addEventListener("click", submitMergePlaylists);

  // Remove Local Listeners
  if (el.btnScanLocalDir) {
    el.btnScanLocalDir.addEventListener("click", startLocalDirectoryScan);
  }
  if (el.localFolderPath) {
    el.localFolderPath.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        startLocalDirectoryScan();
      }
    });
  }
  if (el.btnLocalSelectAll) {
    el.btnLocalSelectAll.addEventListener("click", () => {
      el.localMatchesList.querySelectorAll(".local-match-checkbox").forEach((cb) => {
        cb.checked = true;
      });
      updateLocalMatchesSubmitButton();
    });
  }
  if (el.btnLocalDeselectAll) {
    el.btnLocalDeselectAll.addEventListener("click", () => {
      el.localMatchesList.querySelectorAll(".local-match-checkbox").forEach((cb) => {
        cb.checked = false;
      });
      updateLocalMatchesSubmitButton();
    });
  }
  document.querySelectorAll(".btn-path-suggestion").forEach((btn) => {
    btn.addEventListener("click", () => {
      const p = btn.getAttribute("data-path");
      if (p && el.localFolderPath) el.localFolderPath.value = p;
    });
  });
  if (el.btnSubmitRemoveLocal) {
    el.btnSubmitRemoveLocal.addEventListener("click", submitRemoveLocalTracks);
  }
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

  // Spotify Auth & Connect Listeners
  if (el.btnSpotifyConnect) {
    el.btnSpotifyConnect.addEventListener("click", () => openSpotifyConfigModal());
  }
  if (el.btnSpotifyLogout) {
    el.btnSpotifyLogout.addEventListener("click", logoutSpotify);
  }
  if (el.btnSaveSpotifyConfig) {
    el.btnSaveSpotifyConfig.addEventListener("click", submitSpotifyConfig);
  }

  // Platform Tabs Switcher (TIDAL <-> Spotify)
  document.querySelectorAll(".platform-tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const pane = tab.dataset.pane;
      const platform = tab.dataset.platform;
      if (pane && platform) {
        handlePlatformSwitch(pane, platform);
      }
    });
  });

  // OAuth Popup Message Listener
  window.addEventListener("message", async (event) => {
    if (event.data && event.data.type === "SPOTIFY_AUTH_SUCCESS") {
      showToast("Spotify connected successfully!", "success");
      await checkSpotifyStatus();
      if (state.spotify.pendingPaneSwitch) {
        const targetPane = state.spotify.pendingPaneSwitch;
        state.spotify.pendingPaneSwitch = null;
        await handlePlatformSwitch(targetPane, "spotify");
      }
    }
  });

  // Close modals when clicking backdrop overlay
  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) {
        closeModal(overlay);
      }
    });
  });

  // Keyboard Shortcuts: Cmd+K for search, Escape for modals
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      openSearchModal();
    } else if (e.key === "Escape") {
      document.querySelectorAll(".modal-overlay:not(.hidden)").forEach(closeModal);
    }
  });

  setupDragAndDrop();
  setupAudioPlayerEvents();
}

// Initial Boot
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await checkAuthStatus();

  // Check if returned from full-page Spotify OAuth redirect
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get("spotify_connected") === "1") {
    showToast("Spotify connected successfully!", "success");
    await checkSpotifyStatus();
    window.history.replaceState({}, document.title, window.location.pathname);
  }
});
