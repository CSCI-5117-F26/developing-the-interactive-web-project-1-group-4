// Create a playlist right inside the "Add to playlist" pop-up, then add the video to it.
(() => {
    const form = document.getElementById("quickPlaylistForm");
    const grid = document.getElementById("mvGrid");
    const dialog = document.getElementById("playlistDialog");
    const choices = document.getElementById("playlistChoices");
    const message = document.getElementById("playlistMessage");
    if (!form || !grid || !dialog || !choices || !message) return;

    const input = document.getElementById("quickPlaylistTitle");
    const submit = form.querySelector("button[type='submit']");
    let videoId = null;
    let busy = false;

    // Remember which video the pop-up was opened for (home.js fires this event first).
    grid.addEventListener("video-menu-action", event => {
        if (event.detail.action !== "playlist") return;
        videoId = event.detail.videoId;
        input.value = "";
        message.textContent = choices.querySelector("button")
            ? ""
            : "You have no playlists yet. Create your first one below.";
    });

    async function readJson(response) {
        return response.json().catch(() => ({}));
    }

    form.addEventListener("submit", async event => {
        event.preventDefault();
        const title = input.value.trim();
        if (busy || videoId === null) return;
        if (!title) {
            message.textContent = "Please type a playlist name.";
            return;
        }

        busy = true;
        submit.disabled = true;
        message.textContent = "Creating playlist…";

        try {
            const body = new FormData();
            body.append("title", title);
            const created = await fetch(form.dataset.createUrl, {
                method: "POST",
                body,
                headers: { "X-Requested-With": "fetch" }
            });
            if (created.redirected) throw new Error("Please log in to create playlists.");
            const playlist = await readJson(created);
            if (!created.ok || !playlist.id) {
                throw new Error(playlist.error || "Could not create the playlist.");
            }

            const addUrl = form.dataset.addTemplate.replace("/0/", "/" + playlist.id + "/");
            const added = await fetch(addUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ video_id: videoId })
            });
            const data = await readJson(added);
            if (!added.ok) throw new Error(data.error || "Playlist created, but the video could not be added.");

            // Show the new playlist in the list for next time, without a page reload.
            const item = document.createElement("button");
            item.type = "button";
            item.className = "pure-button";
            item.dataset.url = addUrl;
            item.textContent = playlist.title;
            choices.appendChild(item);

            dialog.close();
            const text = "Playlist \u201C" + playlist.title + "\u201D created and video added.";
            if (window.tuneToast) window.tuneToast(text, "success");
        } catch (error) {
            message.textContent = error.message;
        } finally {
            busy = false;
            submit.disabled = false;
        }
    });
})();


 // ===== Watch page: plus menu + recommended-card actions =====
(() => {
    const watchPage = document.getElementById("watchPage");
    if (!watchPage) return;

    const dialog = document.getElementById("playlistDialog");
    const choices = document.getElementById("playlistChoices");
    const message = document.getElementById("playlistMessage");
    const closeDialogButton = document.getElementById("closePlaylistDialog");
    const form = document.getElementById("quickPlaylistForm");

    if (!dialog || !choices || !message) {
        console.error("Playlist dialog elements are missing.");
        return;
    }

    // The ID changes depending on which menu action was selected.
    let selectedVideoId = null;
    let busy = false;

    // Create a status element if watch.html does not already have one.
    let status = document.getElementById("videoMenuStatus");

    if (!status) {
        status = document.createElement("p");
        status.id = "videoMenuStatus";
        status.setAttribute("role", "status");
        status.hidden = true;
        watchPage.insertAdjacentElement("afterend", status);
    }

    function showStatus(text) {
        status.textContent = text;
        status.hidden = false;
    }

    function closeMenus() {
        watchPage.querySelectorAll(
            ".record-player-controls .mv-menu, " +
            ".recommended-section .mv-menu"
        ).forEach(menu => {
            menu.hidden = true;
        });

        watchPage.querySelectorAll(
            ".record-player-controls button[aria-haspopup='menu'], " +
            ".recommended-section .mv-dots"
        ).forEach(button => {
            button.setAttribute("aria-expanded", "false");
        });
    }

    function openPlaylistDialog(videoId) {
        selectedVideoId = videoId;
        message.textContent = "";

        if (!choices.querySelector("button[data-url]")) {
            message.textContent =
                "You have no playlists yet. Create your first one below.";
        }

        dialog.showModal();
    }

    async function readJson(response) {
        return response.json().catch(() => ({}));
    }

    async function addVideo(url, videoId) {
        if (!url || !Number.isFinite(videoId)) {
            throw new Error("The video or destination URL is missing.");
        }

        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_id: videoId })
        });

        if (response.redirected) {
            throw new Error("Please log in to save videos.");
        }

        const data = await readJson(response);

        if (!response.ok) {
            throw new Error(data.error || "Could not save the video.");
        }

        return data;
    }

    // Handle both the plus-button menu and recommendation-card menus.
    watchPage.addEventListener("click", async event => {
        const toggle = event.target.closest(
            ".record-player-controls button[aria-haspopup='menu'], " +
            ".recommended-section .mv-dots"
        );

        if (toggle) {
            event.preventDefault();
            event.stopPropagation();

            const card = toggle.closest(".mv-card");
            const menu = card
                ? card.querySelector(".mv-menu")
                : toggle.closest(".knob-controls")?.querySelector(".mv-menu");

            if (!menu) return;

            const shouldOpen = menu.hidden;
            closeMenus();

            menu.hidden = !shouldOpen;
            toggle.setAttribute("aria-expanded", String(shouldOpen));
            return;
        }

        const item = event.target.closest(".mv-menu [data-action]");

        if (!item || !watchPage.contains(item)) return;

        event.preventDefault();
        event.stopPropagation();

        if (busy) return;

        const card = item.closest(".mv-card");

        selectedVideoId = card
            ? Number(card.dataset.videoId)
            : Number(watchPage.dataset.videoId);

        const action = item.dataset.action;
        const url = item.dataset.url;

        closeMenus();

        if (!Number.isFinite(selectedVideoId) || selectedVideoId <= 0) {
            showStatus("Could not identify the selected video.");
            return;
        }

        if (action === "playlist") {
            openPlaylistDialog(selectedVideoId);
            return;
        }

        if (action !== "watch-later" && action !== "save") return;

        busy = true;
        item.disabled = true;

        try {
            const data = await addVideo(url, selectedVideoId);
            showStatus(
                data.message ||
                (action === "watch-later"
                    ? "Video added to Watch Later."
                    : "Video saved successfully.")
            );
        } catch (error) {
            showStatus(error.message);
        } finally {
            busy = false;
            item.disabled = false;
        }
    });

    // Close menus when clicking outside them.
    document.addEventListener("click", event => {
        if (!watchPage.contains(event.target)) {
            closeMenus();
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key === "Escape") closeMenus();
    });

    // Add the selected video to an existing playlist.
    choices.addEventListener("click", async event => {
        const button = event.target.closest("button[data-url]");

        if (!button || busy || selectedVideoId === null) return;

        busy = true;
        button.disabled = true;
        message.textContent = "Adding video…";

        try {
            const data = await addVideo(button.dataset.url, selectedVideoId);
            dialog.close();
            showStatus(data.message || "Video added to playlist.");
        } catch (error) {
            message.textContent = error.message;
        } finally {
            busy = false;
            button.disabled = false;
        }
    });

    closeDialogButton?.addEventListener("click", () => {
        dialog.close();
    });

    // Create a playlist, then add the currently selected video to it.
    form?.addEventListener("submit", async event => {
        event.preventDefault();

        if (busy || selectedVideoId === null) return;

        const input = document.getElementById("quickPlaylistTitle");
        const submit = form.querySelector("button[type='submit']");
        const title = input?.value.trim();

        if (!title) {
            message.textContent = "Please type a playlist name.";
            return;
        }

        busy = true;
        if (submit) submit.disabled = true;
        message.textContent = "Creating playlist…";

        try {
            const body = new FormData();
            body.append("title", title);

            const created = await fetch(form.dataset.createUrl, {
                method: "POST",
                body,
                headers: { "X-Requested-With": "fetch" }
            });

            if (created.redirected) {
                throw new Error("Please log in to create playlists.");
            }

            const playlist = await readJson(created);

            if (!created.ok || !playlist.id) {
                throw new Error(
                    playlist.error || "Could not create the playlist."
                );
            }

            const addUrl = form.dataset.addTemplate.replace(
                "/0/",
                `/${playlist.id}/`
            );

            await addVideo(addUrl, selectedVideoId);

            const newChoice = document.createElement("button");
            newChoice.type = "button";
            newChoice.dataset.url = addUrl;
            newChoice.textContent = playlist.title;
            choices.appendChild(newChoice);

            dialog.close();
            form.reset();

            showStatus(
                `Playlist "${playlist.title}" created and video added.`
            );
        } catch (error) {
            message.textContent = error.message;
        } finally {
            busy = false;
            if (submit) submit.disabled = false;
        }
    });
})();
