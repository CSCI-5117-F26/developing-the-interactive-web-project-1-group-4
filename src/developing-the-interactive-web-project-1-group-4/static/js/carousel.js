document.querySelectorAll(".carousel").forEach((carousel) => {
    const track = carousel.querySelector(".carousel-track");
    const leftArrow = carousel.querySelector(".carousel-arrow-left");
    const rightArrow = carousel.querySelector(".carousel-arrow-right");

    // Grey out an arrow when there's nothing more to scroll that way
    function updateArrows() {
        const maxScroll = track.scrollWidth - track.clientWidth;
        leftArrow.disabled = track.scrollLeft <= 1;
        rightArrow.disabled = track.scrollLeft >= maxScroll - 1;
    }

    // Each click moves most of one screen-width
    const step = () => track.clientWidth * 0.8;
    leftArrow.addEventListener("click", () => track.scrollBy({ left: -step(), behavior: "smooth" }));
    rightArrow.addEventListener("click", () => track.scrollBy({ left: step(), behavior: "smooth" }));

    track.addEventListener("scroll", updateArrows, { passive: true });
    window.addEventListener("resize", updateArrows);

    // Images change the track width as they load, so re-check then too
    track.querySelectorAll("img").forEach((img) => img.addEventListener("load", updateArrows));

    updateArrows();
});