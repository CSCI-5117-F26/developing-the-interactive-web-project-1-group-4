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

// One listener for the whole page: works for video cards AND dropdown results
document.addEventListener("click", (e) => {
    const target = e.target.closest("[data-video-url]");
    if (!target) return;
    e.preventDefault();
    playFullscreen(target.dataset.videoUrl);
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