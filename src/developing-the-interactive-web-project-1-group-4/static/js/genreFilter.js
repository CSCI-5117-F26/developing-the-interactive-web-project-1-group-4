// Genre filter: show as many genres as fit inside the search bar's width,
// put the rest behind the "+N more" button.
(() => {
    document.querySelectorAll("[data-genre-filter]").forEach(root => {
        const bar = root.querySelector(".gf-bar");
        const more = root.querySelector(".gf-more");
        const count = root.querySelector(".gf-count");
        const panel = root.querySelector(".gf-panel");
        const chips = [...bar.querySelectorAll(".gf-chip:not(.gf-more)")];
        if (!more || !panel || !chips.length) return;

        const GAP = 8;

        function layout() {
            // Show everything first so the real widths can be measured.
            chips.forEach(chip => chip.classList.remove("gf-hide"));
            more.hidden = false;
            count.textContent = String(chips.length);
            const widths = chips.map(chip => chip.offsetWidth);
            const moreWidth = more.offsetWidth;
            const room = bar.clientWidth;
            const activeIndex = chips.findIndex(chip => chip.classList.contains("active"));

            const total = widths.reduce((sum, w) => sum + w, 0) + GAP * (chips.length - 1);
            if (total <= room) {                 // everything fits: no "more" button needed
                more.hidden = true;
                return;
            }

            // Largest number of chips that fits next to the "more" button.
            // If the selected genre would be hidden, it takes the last visible slot.
            let visible = [];
            for (let n = chips.length - 1; n >= 0; n--) {
                let indexes = Array.from({ length: n }, (_, i) => i);
                if (activeIndex >= n && activeIndex !== -1 && n > 0) {
                    indexes = indexes.slice(0, n - 1).concat(activeIndex);
                }
                const used = indexes.reduce((sum, i) => sum + widths[i], 0)
                    + moreWidth + GAP * indexes.length;
                if (used <= room) {
                    visible = indexes;
                    break;
                }
            }

            chips.forEach((chip, i) => chip.classList.toggle("gf-hide", !visible.includes(i)));
            count.textContent = String(chips.length - visible.length);
        }

        function setOpen(open) {
            panel.hidden = !open;
            more.setAttribute("aria-expanded", String(open));
        }

        more.addEventListener("click", () => setOpen(panel.hidden));
        document.addEventListener("click", event => {
            if (!root.contains(event.target)) setOpen(false);
        });
        document.addEventListener("keydown", event => {
            if (event.key === "Escape" && !panel.hidden) {
                setOpen(false);
                more.focus();
            }
        });

        window.addEventListener("resize", layout);
        if (document.fonts && document.fonts.ready) document.fonts.ready.then(layout);
        layout();
    });
})();