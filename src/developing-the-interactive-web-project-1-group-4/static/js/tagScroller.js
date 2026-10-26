// Genre tag scroller (arrows + scroll), same behaviour as on the home page.
(function () {
    const tagScroller = document.querySelector(".tag-scroller");
    if (!tagScroller) return;

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

    // If a genre is selected, scroll it into view
    const active = track.querySelector(".tag.active");
    if (active) {
        track.scrollLeft = active.offsetLeft - track.offsetLeft - (track.clientWidth - active.offsetWidth) / 2;
    }

    updateArrows();
})();