(function () {
    const dialog = document.getElementById("playlistDialog");
    if (!dialog) return;

    const titleEl = document.getElementById("plTitle");
    const metaEl = document.getElementById("plMeta");
    const listEl = document.getElementById("plList");
    const emptyEl = document.getElementById("plEmpty");
    const errorEl = document.getElementById("plError");
    const btnPlay = document.getElementById("plPlay");
    const btnClose = document.getElementById("plClose");

    let playUrl = "";
    let currentCard = null;
    let playlistTracks = [];

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
        const template = card.querySelector("template.playlist-videos");
        if (!template) return [];

        return Array.from(template.content.querySelectorAll("li")).map(li => {
            const seconds = parseInt(li.dataset.seconds, 10) || 0;

            return {
                id: Number(li.dataset.videoId),
                title: li.dataset.title || "Untitled",
                artist: li.dataset.artist || "",
                duration: li.dataset.durationText || (seconds ? fmt(seconds) : ""),
                seconds,
                thumb: li.dataset.thumb || "",
                playUrl: li.dataset.playUrl || "",
                removeUrl: li.dataset.removeUrl || ""
            };
        });
    }

    function renderList(tracks) {
        listEl.textContent = "";

        tracks.forEach((track, index) => {
            const item = document.createElement("li");
            item.dataset.playUrl = track.playUrl;
            item.dataset.videoId = String(track.id);
            item.tabIndex = 0;
            item.setAttribute("role", "link");
            item.setAttribute("aria-label", `Play ${track.title}`);

            const row = document.createElement("div");
            row.className = "pl-row";

            const num = document.createElement("span");
            num.className = "pl-num";
            num.textContent = index + 1;

            const thumb = document.createElement("img");
            thumb.className = "pl-thumb";
            thumb.alt = "";

            if (track.thumb) {
                thumb.src = track.thumb;
                thumb.onerror = () => thumb.removeAttribute("src");
            }

            const text = document.createElement("span");
            text.className = "pl-row-text";

            const title = document.createElement("span");
            title.className = "pl-row-title";
            title.textContent = track.title;

            const artist = document.createElement("span");
            artist.className = "pl-row-artist";
            artist.textContent = track.artist;

            text.append(title, artist);

            const time = document.createElement("span");
            time.className = "pl-row-time";
            time.textContent = track.duration;

            const dots = document.createElement("button");
            dots.type = "button";
            dots.className = "mv-dots pl-dots";
            dots.setAttribute("aria-haspopup", "menu");
            dots.setAttribute("aria-expanded", "false");
            dots.setAttribute("aria-label", `Options for ${track.title}`);
            dots.innerHTML = "<span></span><span></span><span></span>";

            const menu = document.createElement("div");
            menu.className = "mv-menu pl-menu";
            menu.setAttribute("role", "menu");
            menu.hidden = true;

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "mv-menu-danger";
            removeButton.dataset.action = "remove";
            removeButton.setAttribute("role", "menuitem");
            removeButton.textContent = "Remove video";
            menu.appendChild(removeButton);

            row.append(num, thumb, text, time, dots);
            item.append(row, menu);
            listEl.appendChild(item);
        });
    }

    function openTrack(event) {
        if (event.target.closest("button, [role='menu']")) return;

        const item = event.target.closest("#plList li[data-play-url]");
        if (!item || !item.dataset.playUrl) return;

        if (event.type === "keydown") {
            if (event.key !== "Enter" && event.key !== " ") return;
            event.preventDefault();
        }

        window.location.assign(item.dataset.playUrl);
    }

    function closeMenus() {
        listEl.querySelectorAll(".pl-menu").forEach(menu => {
            menu.hidden = true;
            menu.parentElement.classList.remove("menu-open");
        });
        listEl.querySelectorAll(".pl-dots[aria-expanded='true']").forEach(dots => {
            dots.setAttribute("aria-expanded", "false");
        });
    }

    function updatePlaylist(tracks) {
        playlistTracks = tracks;
        renderList(tracks);
        emptyEl.hidden = tracks.length > 0;
        listEl.hidden = tracks.length === 0;
        btnPlay.disabled = tracks.length === 0;

        const totalSeconds = tracks.reduce(
            (sum, track) => sum + track.seconds,
            0
        );
        const count = tracks.length +
            (tracks.length === 1 ? " video" : " videos");
        metaEl.textContent = totalSeconds
            ? count + " · " + Math.max(1, Math.round(totalSeconds / 60)) + " min"
            : count;

        if (currentCard) {
            const countEl = currentCard.querySelector(".playlist-count span");
            if (countEl) countEl.textContent = count;
        }
    }

    listEl.addEventListener("click", async event => {
        const dots = event.target.closest(".pl-dots");
        if (dots) {
            const item = dots.closest("li");
            const menu = item.querySelector(".pl-menu");
            const wasOpen = !menu.hidden;
            closeMenus();
            menu.hidden = wasOpen;
            item.classList.toggle("menu-open", !wasOpen);
            dots.setAttribute("aria-expanded", String(!wasOpen));
            event.stopPropagation();
            return;
        }

        const removeButton = event.target.closest(".pl-menu [data-action='remove']");
        if (removeButton) {
            event.stopPropagation();
            const item = removeButton.closest("li");
            const trackId = Number(item.dataset.videoId);
            const track = playlistTracks.find(current => current.id === trackId);

            if (!track || !track.removeUrl) {
                showError("Could not remove the video from this playlist.");
                return;
            }

            removeButton.disabled = true;
            showError("");
            try {
                const response = await fetch(track.removeUrl, { method: "DELETE" });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    showError(data.error || "Could not remove the video.");
                    return;
                }

                const template = currentCard?.querySelector("template.playlist-videos");
                const sourceTrack = template && Array.from(
                    template.content.querySelectorAll("li")
                ).find(source => Number(source.dataset.videoId) === track.id);
                sourceTrack?.remove();

                closeMenus();
                updatePlaylist(playlistTracks.filter(current => current.id !== track.id));
            } catch {
                showError("Could not remove the video. Please try again.");
            } finally {
                removeButton.disabled = false;
            }
            return;
        }

        if (!event.target.closest(".pl-menu")) closeMenus();
        openTrack(event);
    });
    listEl.addEventListener("keydown", openTrack);

    document.querySelectorAll(".playlist-open").forEach(card => {
        card.addEventListener("click", () => {
            currentCard = card;
            const tracks = readTracks(card);
            playUrl = card.dataset.playUrl || "";

            titleEl.textContent = card.dataset.playlistTitle || "Playlist";
            updatePlaylist(tracks);
            showError("");
            dialog.showModal();
        });
    });

    btnPlay.addEventListener("click", () => {
        if (!playUrl) {
            showError("Playlist play URL is missing.");
            return;
        }

        window.location.href = playUrl;
    });

    btnClose?.addEventListener("click", () => dialog.close());

    dialog.addEventListener("click", event => {
        if (event.target === dialog) dialog.close();
    });
})();