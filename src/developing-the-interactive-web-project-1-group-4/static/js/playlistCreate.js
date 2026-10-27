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