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
                title: li.dataset.title || "Untitled",
                artist: li.dataset.artist || "",
                duration: li.dataset.durationText || (seconds ? fmt(seconds) : ""),
                seconds,
                thumb: li.dataset.thumb || ""
            };
        });
    }

    function renderList(tracks) {
        listEl.textContent = "";

        tracks.forEach((track, index) => {
            const item = document.createElement("li");

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

            row.append(num, thumb, text, time);
            item.appendChild(row);
            listEl.appendChild(item);
        });
    }

    document.querySelectorAll(".playlist-open").forEach(card => {
        card.addEventListener("click", () => {
            const tracks = readTracks(card);
            playUrl = card.dataset.playUrl || "";

            titleEl.textContent = card.dataset.playlistTitle || "Playlist";

            const totalSeconds = tracks.reduce(
                (sum, track) => sum + track.seconds,
                0
            );

            const count = tracks.length +
                (tracks.length === 1 ? " video" : " videos");

            metaEl.textContent = totalSeconds
                ? count + " · " + Math.max(1, Math.round(totalSeconds / 60)) + " min"
                : count;

            renderList(tracks);
            emptyEl.hidden = tracks.length > 0;
            listEl.hidden = tracks.length === 0;
            btnPlay.disabled = tracks.length === 0;

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