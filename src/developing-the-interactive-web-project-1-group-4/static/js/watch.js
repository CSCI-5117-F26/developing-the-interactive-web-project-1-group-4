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
const commentSection = document.querySelector(".comment-section");
const commentList = document.getElementById("commentList");          // other people's
const myCommentList = document.getElementById("myCommentList");      // yours
const myCommentsSection = document.getElementById("myCommentsSection");
const otherCommentsTitle = document.getElementById("otherCommentsTitle");
const commentCount = document.getElementById("commentCount");
const noComments = document.getElementById("noComments");
const commentDeleteDialog = document.getElementById("commentDeleteDialog");
const commentDeleteQuestion = document.getElementById("commentDeleteQuestion");
const commentDeleteText = document.getElementById("commentDeleteText");
const commentDeleteError = document.getElementById("commentDeleteError");
const commentDeleteYes = document.getElementById("commentDeleteYes");
let commentToDelete = null;

// Show/hide the comment groups and global empty state to match what's on the page
function refreshCommentSections() {
    const hasMine = myCommentList.children.length > 0;
    myCommentsSection.hidden = !hasMine;
    if (otherCommentsTitle) otherCommentsTitle.hidden = !hasMine;
    noComments.hidden = Number(commentCount.textContent) > 0;
}

function changeCommentCount(by) {
    commentCount.textContent = Math.max(0, Number(commentCount.textContent) + by);
    refreshCommentSections();
}

// ---------- Which comments THIS browser liked (the server only keeps counts) ----------
const likedStorageKey = "likedComments";

function loadLikedComments() {
    try {
        return new Set(JSON.parse(localStorage.getItem(likedStorageKey) || "[]"));
    } catch {
        return new Set();
    }
}

const likedComments = loadLikedComments();

function saveLikedComments() {
    try {
        localStorage.setItem(likedStorageKey, JSON.stringify([...likedComments]));
    } catch {
        /* storage unavailable (private mode): likes still save to the server */
    }
}

function showCommentLike(button, liked, count) {
    button.classList.toggle("liked", liked);
    button.setAttribute("aria-pressed", String(liked));
    button.setAttribute("aria-label", `${liked ? "Unlike" : "Like"} this comment`);
    button.querySelector(".comment-like-icon").textContent = liked ? "♥" : "♡";
    if (count !== undefined) button.querySelector(".comment-like-count").textContent = count;
}

function markLikedComments(root) {
    root.querySelectorAll("[data-comment-id]").forEach((card) => {
        if (likedComments.has(card.dataset.commentId)) {
            showCommentLike(card.querySelector(":scope > .comment-body .comment-like"), true);
        }
    });
}

// ---------- Build a comment (same markup as commentMacros.html) ----------
// textContent everywhere, never innerHTML, so typed HTML can't run as code
function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
}

function menuElement() {
    const wrap = el("div", "comment-menu-wrap");
    const dots = el("button", "comment-dots");
    dots.type = "button";
    dots.setAttribute("aria-haspopup", "menu");
    dots.setAttribute("aria-expanded", "false");
    dots.setAttribute("aria-label", "Comment options");
    dots.append(el("span"), el("span"), el("span"));

    const menu = el("div", "comment-menu");
    menu.setAttribute("role", "menu");
    menu.hidden = true;
    const edit = el("button", "comment-edit", "Edit");
    const del = el("button", "comment-delete", "Delete");
    [edit, del].forEach((b) => { b.type = "button"; b.setAttribute("role", "menuitem"); });
    menu.append(edit, del);

    wrap.append(dots, menu);
    return wrap;
}

function commentElement(c) {
    const card = el("article", "comment-card" + (c.isReply ? " comment-reply" : ""));
    card.dataset.commentId = c.id;
    if (c.isMine) card.dataset.manageUrl = c.manageURL;

    const avatarLink = el("a", "comment-avatar");
    avatarLink.href = c.profileURL;
    avatarLink.title = c.username;
    const avatar = el("img");
    avatar.src = c.userPicture;
    avatar.alt = "";
    avatar.onerror = () => { avatar.onerror = null; avatar.src = c.fallbackPicture; };
    avatarLink.append(avatar);

    const body = el("div", "comment-body");

    const header = el("div", "comment-header");
    const author = el("a", "comment-author", c.username);
    author.href = c.profileURL;
    const time = el("span", "commented-time", c.timeAgo);
    time.title = c.createdAt;
    header.append(author, time);
    if (c.isMine) header.append(menuElement());

    const text = el("p", "comment-text", c.comment);

    const actions = el("div", "comment-actions");
    const like = el("button", "comment-like");
    like.type = "button";
    like.dataset.likeUrl = c.likeURL;
    like.setAttribute("aria-pressed", "false");
    like.setAttribute("aria-label", "Like this comment");
    like.append(el("span", "comment-like-icon", "♡"), " ", el("span", "comment-like-count", String(c.likes)));
    actions.append(like);

    body.append(header, text, actions);

    if (!c.isReply) {
        const reply = el("button", "comment-reply-button", "Reply");
        reply.type = "button";
        actions.append(reply);

        const replies = el("div", "comment-replies");
        (c.replies || []).forEach((r) => replies.append(commentElement(r)));
        body.append(replies);
    }

    card.append(avatarLink, body);
    if (likedComments.has(String(c.id))) showCommentLike(like, true);
    return card;
}

// ---------- Talk to the server ----------
async function sendJson(url, method, body) {
    const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
    });
    if (response.status === 401) {
        goToLogin();
        return null;
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
    return data;
}

// ---------- New top-level comment: goes to the top of "Your comments" ----------
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
            const data = await sendJson(page.dataset.commentsUrl, "POST", { comment: text });
            if (!data) return;
            myCommentList.prepend(commentElement(data));
            changeCommentCount(1);
            input.value = "";
        } catch (e) {
            error.textContent = e.message;
            error.hidden = false;
        } finally {
            submit.disabled = false;
        }
    });
}

// ---------- Small inline form (used for replying and editing) ----------
function inlineForm({ className, initialText, placeholder, submitLabel, onSubmit, onCancel }) {
    const form = el("form", `${className} comment-form`);
    const input = el("textarea");
    input.rows = 3;
    input.maxLength = 2000;
    input.required = true;
    input.value = initialText || "";
    if (placeholder) input.placeholder = placeholder;
    const error = el("p", "comment-error");
    error.hidden = true;
    const buttons = el("div", "comment-form-actions");
    const cancel = el("button", "comment-cancel", "Cancel");
    cancel.type = "button";
    const submit = el("button", "comment-submit", submitLabel);
    submit.type = "submit";
    buttons.append(cancel, submit);
    form.append(input, error, buttons);

    cancel.addEventListener("click", () => { form.remove(); onCancel?.(); });

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        error.hidden = true;
        submit.disabled = true;
        try {
            await onSubmit(text);
            form.remove();
        } catch (e) {
            error.textContent = e.message;
            error.hidden = false;
        } finally {
            submit.disabled = false;
        }
    });

    return { form, input };
}

// ---------- Reply ----------
function openReplyForm(card) {
    const body = card.querySelector(":scope > .comment-body");
    const existing = body.querySelector(":scope > .reply-form");
    if (existing) return existing.querySelector("textarea").focus();

    const { form, input } = inlineForm({
        className: "reply-form",
        placeholder: `Reply to ${card.querySelector(".comment-author").textContent}...`,
        submitLabel: "Reply",
        onSubmit: async (text) => {
            const data = await sendJson(page.dataset.commentsUrl, "POST",
                                        { comment: text, parentId: Number(card.dataset.commentId) });
            if (!data) return;
            body.querySelector(":scope > .comment-replies").append(commentElement(data));
            changeCommentCount(1);
        },
    });
    body.insertBefore(form, body.querySelector(":scope > .comment-replies"));
    input.focus();
}

// ---------- Edit (only your own comments have the menu) ----------
function startEdit(card) {
    const body = card.querySelector(":scope > .comment-body");
    if (body.querySelector(":scope > .edit-form")) return;
    const textBox = body.querySelector(":scope > .comment-text");

    const { form, input } = inlineForm({
        className: "edit-form",
        initialText: textBox.textContent,
        submitLabel: "Save",
        onSubmit: async (text) => {
            const data = await sendJson(card.dataset.manageUrl, "PATCH", { comment: text });
            if (!data) return;
            textBox.textContent = data.comment;
            textBox.hidden = false;
        },
        onCancel: () => { textBox.hidden = false; },
    });
    textBox.hidden = true;
    textBox.after(form);
    input.focus();
}

// ---------- Delete ----------
function confirmRemoveComment(card) {
    const isReply = card.classList.contains("comment-reply");
    commentDeleteQuestion.textContent = isReply
        ? "Delete this reply?"
        : "Delete this comment? Any replies to it will be deleted too.";
    commentDeleteText.textContent = card.querySelector(":scope > .comment-body > .comment-text").textContent;
    commentDeleteError.textContent = "";
    commentToDelete = card;
    commentDeleteDialog.showModal();
}

commentDeleteDialog.querySelectorAll("[data-close]").forEach((button) => {
    button.addEventListener("click", () => commentDeleteDialog.close());
});

commentDeleteDialog.addEventListener("close", () => {
    commentToDelete = null;
});

commentDeleteYes.addEventListener("click", async () => {
    if (!commentToDelete) return;
    const card = commentToDelete;
    commentDeleteYes.disabled = true;
    commentDeleteError.textContent = "";
    try {
        const data = await sendJson(card.dataset.manageUrl, "DELETE");
        if (!data) return;
        card.remove();
        changeCommentCount(-data.deleted);
        commentDeleteDialog.close();
    } catch (e) {
        commentDeleteError.textContent = e.message;
    } finally {
        commentDeleteYes.disabled = false;
    }
});

// ---------- Like a comment ----------
async function toggleCommentLike(button) {
    if (!loggedIn) return goToLogin();

    const id = button.closest("[data-comment-id]").dataset.commentId;
    const liked = likedComments.has(id);
    button.disabled = true;
    try {
        const data = await sendJson(button.dataset.likeUrl, liked ? "DELETE" : "POST");
        if (!data) return;
        if (liked) likedComments.delete(id);
        else likedComments.add(id);
        saveLikedComments();
        showCommentLike(button, !liked, data.likes);
    } catch {
        alert("Couldn't update the like. Please try again.");
    } finally {
        button.disabled = false;
    }
}

// ---------- ⋮ menus ----------
function closeCommentMenus(except) {
    commentSection.querySelectorAll(".comment-menu").forEach((menu) => {
        if (menu === except) return;
        menu.hidden = true;
        menu.previousElementSibling.setAttribute("aria-expanded", "false");
    });
}

// ---------- One click listener for BOTH sections (and anything added later) ----------
commentSection.addEventListener("click", (event) => {
    const target = event.target;

    const dots = target.closest(".comment-dots");
    if (dots) {
        const menu = dots.nextElementSibling;
        closeCommentMenus(menu);
        menu.hidden = !menu.hidden;
        dots.setAttribute("aria-expanded", String(!menu.hidden));
        return;
    }

    const editButton = target.closest(".comment-edit");
    if (editButton) {
        closeCommentMenus();
        return startEdit(editButton.closest(".comment-card"));
    }

    const deleteButton = target.closest(".comment-delete");
    if (deleteButton) {
        closeCommentMenus();
        return confirmRemoveComment(deleteButton.closest(".comment-card"));
    }

    const likeButton = target.closest(".comment-like");
    if (likeButton) return toggleCommentLike(likeButton);

    const replyButton = target.closest(".comment-reply-button");
    if (replyButton) {
        if (!loggedIn) return goToLogin();
        openReplyForm(replyButton.closest(".comment-card"));
    }
});

// Close any open ⋮ menu when clicking elsewhere or pressing Esc
document.addEventListener("click", (event) => {
    if (!event.target.closest(".comment-menu-wrap")) closeCommentMenus();
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeCommentMenus();
});

markLikedComments(commentSection);

// ----- "Show more comments" (other people's comments) -----
const loadMore = document.getElementById("loadMoreComments");
if (loadMore) {
    loadMore.addEventListener("click", async () => {
        loadMore.disabled = true;
        try {
            const url = `${loadMore.dataset.url}?offset=${loadMore.dataset.offset}`;
            const data = await (await fetch(url)).json();
            data.comments.forEach((c) => commentList.append(commentElement(c)));
            loadMore.dataset.offset = Number(loadMore.dataset.offset) + data.comments.length;
            refreshCommentSections();
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