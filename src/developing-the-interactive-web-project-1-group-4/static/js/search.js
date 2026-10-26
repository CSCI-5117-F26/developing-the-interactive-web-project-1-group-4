const searchForm = document.getElementById("search-form");
const searchInput = document.getElementById("fl-search");
const dropdown = document.getElementById("search-dropdown");

let typingTimer = null;
let currentRequest = null;

// Small helper: create an element with a class and (safe) text
function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    return node;
}

function hideDropdown() {
    dropdown.hidden = true;
    dropdown.replaceChildren();
    searchInput.setAttribute("aria-expanded", "false");
}

function showDropdown() {
    dropdown.hidden = false;
    searchInput.setAttribute("aria-expanded", "true");
}

function buildGroup(title, items, buildItem) {
    if (!items.length) return null;
    const group = el("div", "search-group");
    group.append(el("p", "search-group-title", title));
    items.forEach((item) => group.append(buildItem(item)));
    return group;
}

function videoItem(video) {
    const link = el("a", "search-item");
    link.href = video.watchURL;

    const img = el("img");
    img.src = video.cover || "";
    img.alt = "";
    const text = el("div");
    text.append(el("strong", null, video.title));
    text.append(el("small", null, [video.artist, video.durationText].filter(Boolean).join(" · ")));
    link.append(img, text);
    return link;
}

function artistItem(artist) {
    const link = el("a", "search-item");
    link.href = artist.url;
    const text = el("div");
    text.append(el("strong", null, artist.displayName || artist.username));
    text.append(el("small", null, `@${artist.username} · ${artist.videoCount} videos`));
    link.append(text);
    return link;
}

function genreItem(genre) {
    const link = el("a", "search-item");
    link.href = genre.url;
    const text = el("div");
    text.append(el("strong", null, genre.name));
    text.append(el("small", null, `${genre.videoCount} videos`));
    link.append(text);
    return link;
}

function renderResults(data) {
    const groups = [
        buildGroup("Videos", data.videos, videoItem),
        buildGroup("Artists", data.artists, artistItem),
        buildGroup("Genres", data.genres, genreItem),
    ].filter(Boolean);

    dropdown.replaceChildren();

    if (!groups.length) {
        dropdown.append(el("p", "search-empty", "No matches found."));
    } else {
        dropdown.append(...groups);
        const more = el("a", "search-view-more", `View all results for "${searchInput.value.trim()}"`);
        more.href = data.viewMoreURL;      // same tab, URL changes
        dropdown.append(more);
    }
    showDropdown();
}

async function runSearch(q) {
    if (currentRequest) currentRequest.abort();     // cancel the previous, slower request
    currentRequest = new AbortController();

    try {
        const url = `${searchForm.dataset.api}?q=${encodeURIComponent(q)}`;
        const response = await fetch(url, { signal: currentRequest.signal });
        if (!response.ok) return hideDropdown();
        renderResults(await response.json());
    } catch (error) {
        if (error.name !== "AbortError") hideDropdown();
    }
}

// Wait until the user pauses typing (250 ms) before searching
searchInput.addEventListener("input", () => {
    clearTimeout(typingTimer);
    const q = searchInput.value.trim();
    if (!q) return hideDropdown();
    typingTimer = setTimeout(() => runSearch(q), 250);
});

// Close the dropdown with Esc or by clicking elsewhere
searchInput.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideDropdown();
});
document.addEventListener("click", (e) => {
    if (!searchForm.contains(e.target)) hideDropdown();
});