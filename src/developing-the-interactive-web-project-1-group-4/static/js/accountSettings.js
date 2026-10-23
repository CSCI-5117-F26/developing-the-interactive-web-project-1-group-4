const statusBox = document.getElementById("settingsStatus");
const settingsAvatar = document.getElementById("settingsAvatar");
const picturePreview = document.getElementById("picturePreview");
const pictureInput = document.getElementById("profilePicture");
const bioInput = document.getElementById("userBio");
const bioCount = document.getElementById("bioCount");

// ---------- Small helpers ----------
function showStatus(message) {
    statusBox.textContent = message;
    statusBox.hidden = false;
    clearTimeout(showStatus.timer);
    showStatus.timer = setTimeout(() => { statusBox.hidden = true; }, 4000);
}

function clearErrors(form) {
    form.querySelectorAll("[data-error]").forEach((p) => { p.textContent = ""; });
}

function showErrors(form, data) {
    const fieldErrors = data.errors || {};
    for (const [field, message] of Object.entries(fieldErrors)) {
        const box = form.querySelector(`[data-error="${field}"]`);
        if (box) box.textContent = message;
    }
    if (data.error || !Object.keys(fieldErrors).length) {
        form.querySelector('[data-error="form"]').textContent = data.error || "Something went wrong. Please try again.";
    }
}

function updateBioCount() {
    bioCount.textContent = `${bioInput.value.length} / ${bioInput.maxLength}`;
}

// After saving, make the saved values the new "starting" values,
// so Cancel or reopening the pop-up shows what's actually in the database.
function rememberValues(form) {
    form.querySelectorAll("input:not([type=file]), textarea").forEach((field) => {
        field.defaultValue = field.value;
    });
}

// ---------- What to do after each pop-up saves successfully ----------
const onSuccess = {
    pictureForm(data) {
        settingsAvatar.src = data.profilePictureURL;
        picturePreview.src = data.profilePictureURL;
        showStatus("Profile picture updated.");
    },
    infoForm(data, form) {
        rememberValues(form);
        showStatus("Account info updated.");
    },
    bioForm(data, form) {
        rememberValues(form);
        showStatus("Bio updated.");
    },
    deleteForm(data) {
        window.location.href = data.redirectURL;
    },
};

// ---------- Open and close the pop-ups ----------
document.querySelectorAll("[data-open]").forEach((button) => {
    button.addEventListener("click", () => {
        document.getElementById(button.dataset.open).showModal();
    });
});

document.querySelectorAll(".settings-dialog").forEach((dialog) => {
    const form = dialog.querySelector("form");

    dialog.querySelector("[data-close]").addEventListener("click", () => dialog.close());

    // Runs for Cancel, Esc, and after a successful save: put everything back to the saved values
    dialog.addEventListener("close", () => {
        form.reset();
        clearErrors(form);
        if (form.id === "pictureForm") picturePreview.src = settingsAvatar.src;
        if (form.id === "bioForm") updateBioCount();
    });

    // ---------- Submit: send to the backend without reloading the page ----------
    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearErrors(form);

        const saveButton = form.querySelector('[type="submit"]');
        saveButton.disabled = true;

        try {
            const response = await fetch(form.dataset.url, {
                method: form.dataset.method,
                body: new FormData(form),
                headers: { "X-Requested-With": "fetch" },
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                showErrors(form, data);
                return;
            }
            onSuccess[form.id](data, form);
            if (form.id !== "deleteForm") dialog.close();
        } catch {
            showErrors(form, { error: "Network error. Please check your connection and try again." });
        } finally {
            saveButton.disabled = false;
        }
    });
});

// ---------- Live extras ----------
pictureInput.addEventListener("change", () => {
    const file = pictureInput.files[0];
    if (file) picturePreview.src = URL.createObjectURL(file);
});

bioInput.addEventListener("input", updateBioCount);
updateBioCount();