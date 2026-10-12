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

// Find every card that has a video link, and make clicking it play the video
document.querySelectorAll(".container[data-video-url]").forEach((card) => {
    const play = () => playFullscreen(card.dataset.videoUrl);
    card.addEventListener("click", play);
    card.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            play();
        }
    });
});