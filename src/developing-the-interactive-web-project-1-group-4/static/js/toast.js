// Tune In: pop-up confirmation messages ("toasts") used on every page.
//
// Other scripts can call:
//   tuneToast("Saved!")                  show a message now
//   tuneToast("Oops", "error")           show an error message now
//   tuneToastNext("Video published!")    show it on the NEXT page that loads
//                                        (use before a redirect / reload)
//
// It also listens for the places that already show a status line
// (#videoMenuStatus, #settingsStatus, #mvToast) and shows those as toasts,
// and it shows a success message after uploads, edits, drafts, new playlists
// and subscribe / unsubscribe, so those pages need no changes.
(function () {
    "use strict";

    var KEY = "tuneToastNext";
    var stack = null;

    function getStack() {
        if (stack && stack.isConnected) return stack;
        stack = document.createElement("div");
        stack.className = "tune-toast-stack";
        stack.setAttribute("aria-live", "polite");
        // "popover" puts the messages above open dialogs too.
        if ("popover" in HTMLElement.prototype) stack.setAttribute("popover", "manual");
        document.body.appendChild(stack);
        if (stack.showPopover) {
            try { stack.showPopover(); } catch (e) { /* older browsers: plain fixed box */ }
        }
        return stack;
    }

    function dismiss(el) {
        if (!el || el.dataset.leaving) return;
        el.dataset.leaving = "1";
        el.classList.add("is-leaving");
        setTimeout(function () { el.remove(); }, 250);
    }

    function toast(message, kind) {
        message = String(message || "").trim();
        if (!message) return;
        kind = kind === "error" ? "error" : "success";

        var el = document.createElement("div");
        el.className = "tune-toast is-" + kind;
        el.setAttribute("role", kind === "error" ? "alert" : "status");

        var icon = document.createElement("span");
        icon.className = "tune-toast-icon";
        icon.setAttribute("aria-hidden", "true");
        icon.textContent = kind === "error" ? "!" : "\u2713";

        var text = document.createElement("span");
        text.className = "tune-toast-text";
        text.textContent = message;

        var close = document.createElement("button");
        close.type = "button";
        close.className = "tune-toast-close";
        close.setAttribute("aria-label", "Dismiss message");
        close.textContent = "\u2715";
        close.addEventListener("click", function () { dismiss(el); });

        el.appendChild(icon);
        el.appendChild(text);
        el.appendChild(close);
        getStack().appendChild(el);

        setTimeout(function () { dismiss(el); }, kind === "error" ? 6000 : 4000);
    }

    function toastNext(message, kind) {
        try {
            sessionStorage.setItem(KEY, JSON.stringify({ m: message, k: kind || "success", t: Date.now() }));
        } catch (e) { /* storage blocked: the message is simply skipped */ }
    }

    window.tuneToast = toast;
    window.tuneToastNext = toastNext;

    // ---- 1. A message saved by the previous page ----
    try {
        var saved = sessionStorage.getItem(KEY);
        if (saved) {
            sessionStorage.removeItem(KEY);
            var data = JSON.parse(saved);
            // Ignore old leftovers (for example if the save failed and the page never changed)
            if (data && Date.now() - data.t < 10000) toast(data.m, data.k);
        }
    } catch (e) { /* ignore */ }

    // ---- 2. Existing status lines become toasts ----
    function looksLikeError(text) {
        return /could not|couldn't|error|failed|unable|please log in|no playlists|network|try again|not found/i.test(text);
    }

    ["videoMenuStatus", "settingsStatus", "mvToast"].forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        el.hidden = true;
        new MutationObserver(function () {
            var text = el.textContent.trim();
            if (el.hidden || !text) return;
            el.hidden = true;
            toast(text, looksLikeError(text) ? "error" : "success");
        }).observe(el, {
            childList: true,
            characterData: true,
            subtree: true,
            attributes: true,
            attributeFilter: ["hidden"]
        });
    });

    // ---- 3. Success messages after fetch() requests ----
    // when "next": the page reloads / redirects, so show it on the next page.
    // when "now": the page stays, so show it right away.
    var RULES = [
        { method: "PATCH", re: /\/edit-video\/\d+\/?$/, msg: "Video updated successfully.", when: "next" },
        { method: "POST", re: /\/update-draft\/?$/, msg: "Draft saved successfully.", when: "next" },
        { method: "POST", re: /\/publish-draft\/?$/, msg: "Video published successfully!", when: "next" },
        { method: "POST", re: /\/subscribe\/?$/, msg: "Subscribed successfully.", when: "now" },
        { method: "POST", re: /\/unsubscribe\/?$/, msg: "Unsubscribed.", when: "now" }
    ];

    var realFetch = window.fetch ? window.fetch.bind(window) : null;
    if (realFetch) {
        window.fetch = function (input, init) {
            var promise = realFetch(input, init);
            try {
                var url = typeof input === "string" ? input : (input && input.url) || "";
                var method = String((init && init.method) || (input && input.method) || "GET").toUpperCase();
                var path = new URL(url, window.location.href).pathname;
                var rule = RULES.find(function (r) { return r.method === method && r.re.test(path); });
                if (rule) {
                    promise.then(function (response) {
                        if (!response.ok) return;
                        if (rule.when === "next") toastNext(rule.msg);
                        else toast(rule.msg);
                    }).catch(function () { /* the caller handles the error */ });
                }
            } catch (e) { /* never break the real request */ }
            return promise;
        };
    }

    // ---- 4. Success messages after normal form posts ----
    // This listener runs after the page's own checks, so a form that was
    // stopped by validation (preventDefault) shows nothing.
    document.addEventListener("submit", function (event) {
        if (event.defaultPrevented) return;
        var form = event.target;
        var msg = null;
        if (form.id === "upload-video-form") {
            msg = event.submitter && event.submitter.value === "draft"
                ? "Draft saved successfully."
                : "Video published successfully!";
        } else if (form.closest && form.closest("#newPlaylistDialog")) {
            msg = "Playlist created successfully.";
        }
        if (msg) toastNext(msg);
    });
})();