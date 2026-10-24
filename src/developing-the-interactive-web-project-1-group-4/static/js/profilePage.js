// Subscribe / Unsubscribe button (only exists when viewing someone else's profile)
const subscribeBtn = document.getElementById("subscribeBtn");

if (subscribeBtn) {
    const countBox = document.getElementById("statSubscribers");
    const errorBox = document.getElementById("pfError");

    function showState(subscribed) {
        subscribeBtn.dataset.subscribed = String(subscribed);
        subscribeBtn.textContent = subscribed ? "Subscribed" : "Subscribe";
        subscribeBtn.classList.toggle("pf-btn-light", subscribed);
        subscribeBtn.classList.toggle("pf-btn-primary", !subscribed);
    }

    function changeCount(delta) {
        const current = parseInt(countBox.textContent, 10) || 0;
        countBox.textContent = String(Math.max(0, current + delta));
    }

    subscribeBtn.addEventListener("click", async () => {
        const wasSubscribed = subscribeBtn.dataset.subscribed === "true";
        const url = wasSubscribed
            ? subscribeBtn.dataset.unsubscribeUrl
            : subscribeBtn.dataset.subscribeUrl;

        subscribeBtn.disabled = true;
        errorBox.textContent = "";

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ channel_id: Number(subscribeBtn.dataset.channelId) }),
            });
            const data = await response.json().catch(() => ({}));

            if (response.ok) {
                showState(!wasSubscribed);
                changeCount(wasSubscribed ? -1 : 1);
            } else if (response.status === 409) {
                // The server was already in the state we asked for: just sync the button.
                showState(!wasSubscribed);
            } else {
                errorBox.textContent = data.error || "Something went wrong. Please try again.";
            }
        } catch {
            errorBox.textContent = "Network error. Please try again.";
        } finally {
            subscribeBtn.disabled = false;
        }
    });
}