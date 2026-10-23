const grid = document.getElementById("mvGrid");
const emptyBox = document.getElementById("mvEmpty");
const countPill = document.getElementById("mvCount");
const toast = document.getElementById("mvToast");
const dialog = document.getElementById("deleteDialog");
const deleteName = document.getElementById("deleteName");
const deleteError = document.getElementById("deleteError");
const deleteYes = document.getElementById("deleteYes");

let cardToDelete = null;

function showToast(message) {
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(showToast.timer);
    showToast.timer = setTimeout(() => { toast.hidden = true; }, 4000);
}

function closeMenus() {
    grid.querySelectorAll(".mv-menu").forEach((menu) => { menu.hidden = true; });
    grid.querySelectorAll(".mv-dots").forEach((dots) => dots.setAttribute("aria-expanded", "false"));
}

function updateCount() {
    const n = grid.querySelectorAll(".mv-card").length;
    countPill.textContent = `${n} video${n === 1 ? "" : "s"}`;
    emptyBox.hidden = n > 0;
}

// Three dots: open / close the Edit-Delete menu on that card
grid.addEventListener("click", (event) => {
    const dots = event.target.closest(".mv-dots");
    const deleteButton = event.target.closest('[data-action="delete"]');

    if (dots) {
        const menu = dots.parentElement.querySelector(".mv-menu");
        const wasOpen = !menu.hidden;
        closeMenus();
        menu.hidden = wasOpen;
        dots.setAttribute("aria-expanded", String(!wasOpen));
        event.stopPropagation();
    } else if (deleteButton) {
        cardToDelete = deleteButton.closest(".mv-card");
        closeMenus();
        deleteName.textContent = cardToDelete.dataset.title;
        deleteError.textContent = "";
        dialog.showModal();
    }
});

// Click anywhere else, or press Esc, to close menus
document.addEventListener("click", (event) => {
    if (!event.target.closest(".mv-menu")) closeMenus();
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeMenus();
});

// Confirmation dialog: X and No close it
dialog.querySelectorAll("[data-close]").forEach((button) => {
    button.addEventListener("click", () => dialog.close());
});

// Yes: delete on the server, then remove the card
deleteYes.addEventListener("click", async () => {
    if (!cardToDelete) return;
    deleteYes.disabled = true;
    deleteError.textContent = "";

    try {
        const response = await fetch(cardToDelete.dataset.deleteUrl, { method: "POST" });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            deleteError.textContent = data.error || "Could not delete video.";
            return;
        }
        cardToDelete.remove();
        cardToDelete = null;
        updateCount();
        dialog.close();
        showToast(data.cleanup_required
            ? "Video deleted, but some cloud files could not be removed."
            : "Video deleted.");
    } catch {
        deleteError.textContent = "Network error. Please try again.";
    } finally {
        deleteYes.disabled = false;
    }
});