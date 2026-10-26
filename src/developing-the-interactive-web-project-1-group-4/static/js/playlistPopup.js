// Playlist popup on the Library page: click a playlist, see its videos,
// and use Play / Pause / Resume / Previous / Next.
(function () {
    const dialog = document.getElementById("playlistDialog");
    if (!dialog) return;

    const titleEl = document.getElementById("plTitle");
    const metaEl = document.getElementById("plMeta");
    const nowBox = document.getElementById("plNow");
    const video = document.getElementById("plVideo");
    const nowTitle = document.getElementById("plNowTitle");
    const nowArtist = document.getElementById("plNowArtist");
    const nowLabel = document.getElementById("plNowLabel");
    const bar = document.getElementById("plBar");
    const timeEl = document.getElementById("plTime");
    const listEl = document.getElementById("plList");
    const emptyEl = document.getElementById("plEmpty");
    const errorEl = document.getElementById("plError");

    const btnPrev = document.getElementById("plPrev");
    const btnPlay = document.getElementById("plPlay");
    const btnPause = document.getElementById("plPause");
    const btnResume = document.getElementById("plResume");
    const btnNext = document.getElementById("plNext");

    let tracks = [];
    let current = -1;      // index of the video loaded in the player
    let started = false;   // has anything been played since the popup opened

    function fmt(seconds) {
        seconds = Math.max(0, Math.floor(seconds || 0));
        const m = Math.floor(seconds / 60);
        const s = String(seconds % 60).padStart(2, "0");
        return m + ":" + s;
    }

    function showError(message) {
        errorEl.textContent = message || "";
        errorEl.hidden = !message;
    }

    function readTracks(card) {
        const tpl = card.querySelector("template.playlist-videos");
        if (!tpl) return [];
        return Array.from(tpl.content.querySelectorAll("li")).map((li) => {
            const seconds = parseInt(li.dataset.seconds, 10) || 0;
            return {
                title: li.dataset.title || "Untitled",
                artist: li.dataset.artist || "",
                duration: li.dataset.durationText || (seconds ? fmt(seconds) : ""),
                seconds: seconds,
                thumb: li.dataset.thumb || "",
                src: li.dataset.src || "",
            };
        });
    }

    function renderList() {
        listEl.textContent = "";
        tracks.forEach((track, i) => {
            const item = document.createElement("li");
            const row = document.createElement("button");
            row.type = "button";
            row.className = "pl-row" + (track.src ? "" : " is-unavailable");
            row.dataset.index = i;

            const num = document.createElement("span");
            num.className = "pl-num";
            num.textContent = i + 1;

            const thumb = document.createElement("img");
            thumb.className = "pl-thumb";
            thumb.alt = "";
            if (track.thumb) {
                thumb.src = track.thumb;
                thumb.onerror = () => { thumb.removeAttribute("src"); };
            }

            const text = document.createElement("span");
            text.className = "pl-row-text";
            const t = document.createElement("span");
            t.className = "pl-row-title";
            t.textContent = track.title;
            const a = document.createElement("span");
            a.className = "pl-row-artist";
            a.textContent = track.artist;
            text.append(t, a);

            const time = document.createElement("span");
            time.className = "pl-row-time";
            time.textContent = track.duration;

            row.append(num, thumb, text, time);
            item.appendChild(row);
            listEl.appendChild(item);
        });
    }

    function highlight() {
        listEl.querySelectorAll(".pl-row").forEach((row) => {
            row.classList.toggle("is-current", Number(row.dataset.index) === current);
        });
    }

    function updateButtons() {
        const hasVideos = tracks.length > 0;
        const playing = started && !video.paused && !video.ended;
        const paused = started && video.paused && !video.ended;
        btnPlay.disabled = !hasVideos;
        btnPause.disabled = !playing;
        btnResume.disabled = !paused;
        btnPrev.disabled = !started || nextPlayable(current - 1, -1) === -1;
        btnNext.disabled = !started || nextPlayable(current + 1, 1) === -1;
    }

    function loadTrack(index) {
        const track = tracks[index];
        if (!track) return false;
        if (!track.src) {
            showError("\"" + track.title + "\" can't be played right now.");
            return false;
        }
        showError("");
        current = index;
        video.src = track.src;
        video.poster = track.thumb || "";
        nowBox.hidden = false;
        nowTitle.textContent = track.title;
        nowArtist.textContent = track.artist;
        bar.style.width = "0%";
        timeEl.textContent = "0:00 / " + (track.duration || "0:00");
        highlight();
        return true;
    }

    function playTrack(index) {
        if (!loadTrack(index)) { updateButtons(); return; }
        started = true;
        nowLabel.textContent = "NOW PLAYING";
        video.play().catch(() => {
            showError("Your browser blocked playback. Press Resume to start.");
        });
        updateButtons();
    }

    // First playable video at or after `from`
    function nextPlayable(from, step) {
        for (let i = from; i >= 0 && i < tracks.length; i += step) {
            if (tracks[i].src) return i;
        }
        return -1;
    }

    // ----- Buttons -----
    btnPlay.addEventListener("click", () => {
        const first = nextPlayable(0, 1);
        if (first === -1) { showError("None of the videos in this playlist can be played right now."); return; }
        playTrack(first);
    });

    btnPause.addEventListener("click", () => {
        video.pause();
        nowLabel.textContent = "PAUSED";
        updateButtons();
    });

    btnResume.addEventListener("click", () => {
        nowLabel.textContent = "NOW PLAYING";
        video.play().catch(() => {});
        updateButtons();
    });

    btnNext.addEventListener("click", () => {
        const next = nextPlayable(current + 1, 1);
        if (next !== -1) playTrack(next);
    });

    btnPrev.addEventListener("click", () => {
        const prev = nextPlayable(current - 1, -1);
        if (prev !== -1) playTrack(prev);
    });

    listEl.addEventListener("click", (event) => {
        const row = event.target.closest(".pl-row");
        if (!row) return;
        playTrack(Number(row.dataset.index));
    });

    // ----- Player events -----
    video.addEventListener("play", updateButtons);
    video.addEventListener("pause", updateButtons);
    video.addEventListener("timeupdate", () => {
        const total = video.duration || tracks[current]?.seconds || 0;
        bar.style.width = total ? Math.min(100, (video.currentTime / total) * 100) + "%" : "0%";
        timeEl.textContent = fmt(video.currentTime) + " / " + (total ? fmt(total) : "0:00");
    });
    video.addEventListener("ended", () => {
        const next = nextPlayable(current + 1, 1);
        if (next !== -1) {
            playTrack(next);
        } else {
            nowLabel.textContent = "FINISHED";
            updateButtons();
        }
    });
    video.addEventListener("error", () => {
        if (video.getAttribute("src")) showError("This video couldn't be loaded.");
    });

    // ----- Open / close -----
    function stopAndReset() {
        video.pause();
        video.removeAttribute("src");
        video.removeAttribute("poster");
        video.load();
        started = false;
        current = -1;
        nowBox.hidden = true;
        showError("");
    }

    document.querySelectorAll(".playlist-open").forEach((card) => {
        card.addEventListener("click", () => {
            tracks = readTracks(card);
            stopAndReset();
            titleEl.textContent = card.dataset.playlistTitle || "Playlist";

            const totalSeconds = tracks.reduce((sum, t) => sum + t.seconds, 0);
            const count = tracks.length + (tracks.length === 1 ? " video" : " videos");
            metaEl.textContent = totalSeconds ? count + " · " + Math.max(1, Math.round(totalSeconds / 60)) + " min" : count;

            renderList();
            emptyEl.hidden = tracks.length > 0;
            listEl.hidden = tracks.length === 0;
            updateButtons();
            dialog.showModal();
        });
    });

    document.getElementById("plClose").addEventListener("click", () => dialog.close());

    // Click on the dimmed backdrop closes the popup
    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) dialog.close();
    });

    // Closing (X, Esc or backdrop) stops the video
    dialog.addEventListener("close", stopAndReset);
})();