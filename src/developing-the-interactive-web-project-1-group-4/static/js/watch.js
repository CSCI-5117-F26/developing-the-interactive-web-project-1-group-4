const page = document.getElementById("watchPage");
const loggedIn = page.dataset.loggedIn === "true";

// ---------- Helpers ----------
function formatCount(n) {
    if (n < 1000) return String(n);
    if (n < 1000000) return (n / 1000).toFixed(1).replace(/\.0$/, "") + "K";
    return (n / 1000000).toFixed(1).replace(/\.0$/, "") + "M";
}

function goToLogin() {
    window.location.href = page.dataset.loginUrl;
}

// ================= Likes =================
const likeButton = document.getElementById("likeButton");
const likeText = document.querySelector(".video-title .video-stat-likes .video-stat-text");

function showLiked(liked, count) {
    likeButton.classList.toggle("liked", liked);
    likeButton.setAttribute("aria-pressed", String(liked));
    likeButton.setAttribute("aria-label", `${liked ? "Unlike" : "Like"} this video`);
    likeButton.textContent = liked ? "♥" : "♡";
    if (likeText) likeText.textContent = `${formatCount(count)} like${count === 1 ? "" : "s"}`;
}

likeButton.addEventListener("click", async () => {
    if (!loggedIn) return goToLogin();

    const liked = likeButton.getAttribute("aria-pressed") === "true";
    likeButton.disabled = true;
    try {
        const response = await fetch(page.dataset.likesUrl, {
            method: liked ? "DELETE" : "POST",          // POST = like, DELETE = unlike
            headers: { "Content-Type": "application/json" },
        });
        if (response.status === 401) return goToLogin();
        if (!response.ok) throw new Error();
        const data = await response.json();
        showLiked(data.likedByMe, data.likeCount);
    } catch {
        alert("Couldn't update your like. Please try again.");
    } finally {
        likeButton.disabled = false;
    }
});

// ================= Comments =================
const commentList = document.getElementById("commentList");
const commentCount = document.getElementById("commentCount");
const noComments = document.getElementById("noComments");

// Build a comment with textContent (never innerHTML), so typed HTML can't run as code
function commentElement(c) {
    const card = document.createElement("article");
    card.className = "comment-card";

    const header = document.createElement("div");
    header.className = "comment-header";
    const author = document.createElement("strong");
    author.className = "comment-author";
    author.textContent = c.username;
    const time = document.createElement("span");
    time.className = "commented-time";
    time.textContent = c.timeAgo;
    time.title = c.createdAt;
    header.append(author, time);

    const text = document.createElement("p");
    text.className = "comment-text";
    text.textContent = c.comment;

    card.append(header, text);
    return card;
}

const commentForm = document.getElementById("commentForm");
if (commentForm) {
    const input = document.getElementById("commentInput");
    const error = document.getElementById("commentError");
    const submit = commentForm.querySelector(".comment-submit");

    commentForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        error.hidden = true;
        submit.disabled = true;
        try {
            const response = await fetch(page.dataset.commentsUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ comment: text }),
            });
            if (response.status === 401) return goToLogin();
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(data.error || "Couldn't post your comment.");

            commentList.prepend(commentElement(data));          // newest on top, shows "just now"
            commentCount.textContent = Number(commentCount.textContent) + 1;
            noComments.hidden = true;
            input.value = "";
        } catch (e) {
            error.textContent = e.message || "Couldn't post your comment. Please try again.";
            error.hidden = false;
        } finally {
            submit.disabled = false;
        }
    });
}

// ----- "Show more comments" -----
const loadMore = document.getElementById("loadMoreComments");
if (loadMore) {
    loadMore.addEventListener("click", async () => {
        loadMore.disabled = true;
        try {
            const url = `${loadMore.dataset.url}?offset=${loadMore.dataset.offset}`;
            const data = await (await fetch(url)).json();
            data.comments.forEach((c) => commentList.append(commentElement(c)));
            loadMore.dataset.offset = Number(loadMore.dataset.offset) + data.comments.length;
            if (!data.hasMore) loadMore.remove();
        } finally {
            loadMore.disabled = false;
        }
    });
}

// ================= Description: Show more / Show less =================
const description = document.getElementById("videoDescription");
const descriptionToggle = document.getElementById("descriptionToggle");

if (description && descriptionToggle) {
    description.classList.add("collapsed");

    // Only show the button if the text is actually longer than 3 lines
    if (description.scrollHeight > description.clientHeight + 1) {
        descriptionToggle.hidden = false;
    } else {
        description.classList.remove("collapsed");
    }

    descriptionToggle.addEventListener("click", () => {
        const collapsed = description.classList.toggle("collapsed");
        descriptionToggle.textContent = collapsed ? "Show more" : "Show less";
    });
}