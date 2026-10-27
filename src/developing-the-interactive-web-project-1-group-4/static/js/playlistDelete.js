// Library page: "Delete playlist" button inside the playlist pop-up.
(() => {
    "use strict";

    const dialog = document.getElementById("playlistDialog");
    const deleteBtn = document.getElementById("plDelete");
    const confirmBox = document.getElementById("plConfirm");
    const confirmNo = document.getElementById("plConfirmNo");
    const confirmYes = document.getElementById("plConfirmYes");
    const errorEl = document.getElementById("plError");
    if (!dialog || !deleteBtn) return;

    let currentCard = null;

    function say(message, kind) {
        if (window.tuneToast) window.tuneToast(message, kind);
    }

    function hideConfirm() {
        confirmBox.hidden = true;
        deleteBtn.hidden = false;
    }

    // remember which playlist card opened the pop-up
    document.querySelectorAll(".playlist-open").forEach((card) => {
        card.addEventListener("click", () => {
            currentCard = card;
            hideConfirm();
        });
    });

    deleteBtn.addEventListener("click", () => {
        deleteBtn.hidden = true;
        confirmBox.hidden = false;
        confirmNo.focus();
    });

    confirmNo.addEventListener("click", hideConfirm);
    dialog.addEventListener("close", hideConfirm);

    confirmYes.addEventListener("click", async () => {
        if (!currentCard || !currentCard.dataset.deleteUrl) return;
        confirmYes.disabled = true;
        try {
            const response = await fetch(currentCard.dataset.deleteUrl, { method: "POST" });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                hideConfirm();
                if (errorEl) { errorEl.textContent = data.error || "Could not delete the playlist."; errorEl.hidden = false; }
                return;
            }
            currentCard.remove();
            currentCard = null;
            hideConfirm();
            dialog.close();
            say(data.message || "Playlist deleted.");
        } catch (error) {
            hideConfirm();
            if (errorEl) { errorEl.textContent = "Could not delete the playlist."; errorEl.hidden = false; }
        } finally {
            confirmYes.disabled = false;
        }
    });
})();