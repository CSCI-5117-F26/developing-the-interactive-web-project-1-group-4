const player = document.getElementById("fullscreen-player");

function playFullscreen(url) {
    player.src = url;
    player.hidden = false;

    const goFullscreen =
        player.requestFullscreen ||
        player.webkitRequestFullscreen ||
        player.webkitEnterFullscreen;

    try {
        const result = goFullscreen ? goFullscreen.call(player) : null;
        if (result && result.catch) result.catch(() => {});
    } catch (e) {}

    player.play().catch(() => {});
}

function stopPlayer() {
    player.pause();
    player.removeAttribute("src");
    player.load();
    player.hidden = true;
}

document.addEventListener("fullscreenchange", () => {
    if (!document.fullscreenElement) stopPlayer();
});
document.addEventListener("webkitfullscreenchange", () => {
    if (!document.webkitFullscreenElement) stopPlayer();
});
player.addEventListener("webkitendfullscreen", stopPlayer);

player.addEventListener("ended", () => {
    if (document.fullscreenElement) document.exitFullscreen();
    else stopPlayer();
});

// Clicking (or pressing Enter on) a video card opens the media player page
function openCard(card) {
    window.location.href = card.dataset.watchUrl;
}

document.addEventListener("click", (e) => {
    const card = e.target.closest("[data-watch-url]");
    if (!card) return;
    e.preventDefault();
    openCard(card);
});

document.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const card = e.target.closest("[data-watch-url]");
    if (!card) return;
    e.preventDefault();
    openCard(card);
});

// Keyboard support for the vinyl cards (Enter or Space)
document.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const card = e.target.closest(".container[data-video-url]");
    if (!card) return;
    e.preventDefault();
    playFullscreen(card.dataset.videoUrl);
});

// ----- Genre tag scroller -----
const tagScroller = document.querySelector(".tag-scroller");

if (tagScroller) {
    const track = tagScroller.querySelector(".tag-container");
    const leftArrow = tagScroller.querySelector(".tag-arrow-left");
    const rightArrow = tagScroller.querySelector(".tag-arrow-right");

    // Grey out an arrow when there's nothing more to scroll in that direction
    function updateArrows() {
        const maxScroll = track.scrollWidth - track.clientWidth;
        leftArrow.disabled = track.scrollLeft <= 1;
        rightArrow.disabled = track.scrollLeft >= maxScroll - 1;
    }

    // Each click scrolls by most of the visible width
    const step = () => track.clientWidth * 0.8;
    leftArrow.addEventListener("click", () => track.scrollBy({ left: -step(), behavior: "smooth" }));
    rightArrow.addEventListener("click", () => track.scrollBy({ left: step(), behavior: "smooth" }));

    track.addEventListener("scroll", updateArrows, { passive: true });
    window.addEventListener("resize", updateArrows);

    // If a genre is selected, scroll it into view so the user can see it
    const active = track.querySelector(".tag.active");
    if (active) {
        track.scrollLeft = active.offsetLeft - track.offsetLeft - (track.clientWidth - active.offsetWidth) / 2;
    }

    updateArrows();
}

(() => {
    const grid = document.getElementById("mvGrid");

    function closeMenus() {
        grid.querySelectorAll(".mv-menu").forEach(menu => {
            menu.hidden = true;
        });

        grid.querySelectorAll(".mv-dots").forEach(button => {
            button.setAttribute("aria-expanded", "false");
        });
    }

    grid.addEventListener("click", event => {
        const toggle = event.target.closest(".mv-dots");

        if (toggle) {
            event.preventDefault();
            event.stopPropagation();

            const card = toggle.closest(".mv-card");
            const menu = card.querySelector(".mv-menu");
            const shouldOpen = menu.hidden;

            closeMenus();

            menu.hidden = !shouldOpen;
            toggle.setAttribute("aria-expanded", String(shouldOpen));

            if (shouldOpen) {
                menu.querySelector('[role="menuitem"]').focus();
            }

            return;
        }

        const item = event.target.closest(".mv-menu [data-action]");

        if (item) {
            event.preventDefault();
            event.stopPropagation();

            const card = item.closest(".mv-card");
            const videoId = Number(card.dataset.videoId);
            const action = item.dataset.action;

            closeMenus();
            card.querySelector(".mv-dots").focus();

            // Connect your API requests or playlist picker here.
            grid.dispatchEvent(new CustomEvent("video-menu-action", {
                bubbles: true,
                detail: { videoId, action }
            }));
        }
    });

    document.addEventListener("click", event => {
        if (!event.target.closest("#mvGrid .mv-menu, #mvGrid .mv-dots")) {
            closeMenus();
        }
    });

    document.addEventListener("keydown", event => {
        if (event.key !== "Escape") return;

        const openToggle = grid.querySelector(
            '.mv-dots[aria-expanded="true"]'
        );

        closeMenus();
        openToggle?.focus();
    });

    grid.addEventListener("keydown", event => {
        const item = event.target.closest('.mv-menu [role="menuitem"]');
        if (!item) return;

        const items = [...item.closest(".mv-menu").querySelectorAll(
            '[role="menuitem"]'
        )];
        const index = items.indexOf(item);

        if (event.key === "ArrowDown") {
            event.preventDefault();
            items[(index + 1) % items.length].focus();
        } else if (event.key === "ArrowUp") {
            event.preventDefault();
            items[(index - 1 + items.length) % items.length].focus();
        }
    });
})();
(() => {
    const grid = document.getElementById("mvGrid");
    const dialog = document.getElementById("playlistDialog");
    const choices = document.getElementById("playlistChoices");
    const message = document.getElementById("playlistMessage");
    const status = document.getElementById("videoMenuStatus");

    let selectedVideoId = null;
    let busy = false;

    function showStatus(text) {
        status.textContent = text;
        status.hidden = false;
    }

    async function addVideo(url, videoId) {
        const response = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ video_id: videoId })
        });

        if (response.redirected) {
            throw new Error("Please log in to save videos.");
        }

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            throw new Error(data.error || "Could not add the video.");
        }

        return data;
    }

    grid.addEventListener("video-menu-action", async event => {
        if (busy) return;

        const { videoId, action } = event.detail;

        if (action === "playlist") {
            selectedVideoId = videoId;
            message.textContent = choices.querySelector("button")
                ? ""
                : "No playlists available. Create a playlist first.";
            dialog.showModal();
            return;
        }

        const card = [...grid.querySelectorAll(".mv-card")].find(
            card => Number(card.dataset.videoId) === videoId
        );
        const button = card?.querySelector(
            `[data-action="${action}"]`
        );

        if (!button?.dataset.url) return;

        busy = true;
        button.disabled = true;

        try {
            const data = await addVideo(button.dataset.url, videoId);
            showStatus(data.message || "Video added.");
        } catch (error) {
            showStatus(error.message);
        } finally {
            busy = false;
            button.disabled = false;
        }
    });

    choices.addEventListener("click", async event => {
        const button = event.target.closest("button[data-url]");
        if (!button || busy || selectedVideoId === null) return;

        busy = true;
        choices.querySelectorAll("button").forEach(item => {
            item.disabled = true;
        });
        message.textContent = "Adding video…";

        try {
            const data = await addVideo(
                button.dataset.url,
                selectedVideoId
            );

            dialog.close();
            showStatus(data.message || "Video added to playlist.");
        } catch (error) {
            message.textContent = error.message;
        } finally {
            busy = false;
            choices.querySelectorAll("button").forEach(item => {
                item.disabled = false;
            });
        }
    });

    document.getElementById("closePlaylistDialog")
        .addEventListener("click", () => dialog.close());
})();
