// Library page: the three dots on Saved Videos / Watch Later cards open a small
// menu with "Remove video". Choosing it removes the video from that list.
(() => {
    "use strict";

    const removeUrl = document.currentScript && document.currentScript.dataset.removeUrl;

    function closeMenus() {
        document.querySelectorAll(".lib-remove-menu").forEach((menu) => { menu.hidden = true; });
        document.querySelectorAll('.saved-vid-card .mv-dots[aria-expanded="true"]')
            .forEach((dots) => dots.setAttribute("aria-expanded", "false"));
    }

    function getMenu(card) {
        let menu = card.querySelector(".lib-remove-menu");
        if (!menu) {
            menu = document.createElement("div");
            menu.className = "mv-menu lib-remove-menu";
            menu.setAttribute("role", "menu");
            menu.hidden = true;
            menu.innerHTML =
                '<button type="button" role="menuitem" class="mv-menu-danger" data-action="remove">Remove video</button>';
            card.querySelector(".mv-dots").after(menu);
        }
        return menu;
    }

    function say(message, kind) {
        if (window.tuneToast) window.tuneToast(message, kind);
    }

    async function removeVideo(card) {
        const track = card.closest("[data-list]");
        const videoId = Number(card.dataset.videoId);
        if (!track || !videoId || !removeUrl) return;

        try {
            const response = await fetch(removeUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ video_id: videoId, list: track.dataset.list }),
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                say(data.error || "Could not remove the video.", "error");
                return;
            }
            card.remove();
            say(data.message || "Video removed.");
        } catch (error) {
            say("Could not remove the video.", "error");
        }
    }

    document.addEventListener("click", (event) => {
        const dots = event.target.closest(".saved-vid-card .mv-dots");
        const item = event.target.closest(".lib-remove-menu [data-action='remove']");

        if (dots) {
            const card = dots.closest(".saved-vid-card");
            if (!card.closest("[data-list]")) return;
            const menu = getMenu(card);
            const wasOpen = !menu.hidden;
            closeMenus();
            menu.hidden = wasOpen;
            dots.setAttribute("aria-expanded", String(!wasOpen));
            event.stopPropagation();
        } else if (item) {
            const card = item.closest(".saved-vid-card");
            closeMenus();
            removeVideo(card);
        } else if (!event.target.closest(".lib-remove-menu")) {
            closeMenus();
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeMenus();
    });
})();