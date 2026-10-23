const form = document.getElementById("editForm");
const titleInput = document.getElementById("titleInput");
const descInput = document.getElementById("descInput");
const thumbFile = document.getElementById("thumbFile");
const thumbPreview = document.getElementById("thumbPreview");
const submitBtn = document.getElementById("submitBtn");
const deleteBtn = document.getElementById("deleteBtn");
const dialog = document.getElementById("deleteDialog");
const deleteYes = document.getElementById("deleteYes");

function setText(id, message) {
    document.getElementById(id).textContent = message || "";
}

async function readJson(response) {
    return response.json().catch(() => ({}));
}

// Pencil buttons jump to their field
document.querySelectorAll("[data-focus]").forEach((button) => {
    button.addEventListener("click", () => {
        const field = document.getElementById(button.dataset.focus);
        field.focus();
        field.setSelectionRange(field.value.length, field.value.length);
    });
});

// Show a preview of the new thumbnail
thumbFile.addEventListener("change", () => {
    const file = thumbFile.files[0];
    if (file) {
        thumbPreview.src = URL.createObjectURL(file);
        thumbPreview.hidden = false;
    }
});

// Submit: upload thumbnail (if any), then save title/description
form.addEventListener("submit", async (event) => {
    event.preventDefault();
    setText("titleError", "");
    setText("thumbError", "");
    setText("formError", "");

    const title = titleInput.value.trim();
    if (!title) {
        setText("titleError", "Title is required.");
        return;
    }

    submitBtn.disabled = true;
    try {
        const payload = { title, description: descInput.value.trim() };

        const file = thumbFile.files[0];
        if (file) {
            const formData = new FormData();
            formData.append("thumbnail_file", file);
            const upload = await fetch(form.dataset.uploadUrl, { method: "POST", body: formData });
            const uploadData = await readJson(upload);
            if (!upload.ok) {
                setText("thumbError", uploadData.error || "Thumbnail upload failed.");
                return;
            }
            payload.thumbnail_key = uploadData.thumbnail_key;
        }

        const response = await fetch(form.dataset.saveUrl, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await readJson(response);
        if (!response.ok) {
            setText("formError", data.error || "Could not save changes.");
            return;
        }
        window.location.href = form.dataset.backUrl;
    } catch {
        setText("formError", "Network error. Please try again.");
    } finally {
        submitBtn.disabled = false;
    }
});

// Delete: confirmation first
deleteBtn.addEventListener("click", () => {
    setText("deleteError", "");
    dialog.showModal();
});
dialog.querySelectorAll("[data-close]").forEach((button) => {
    button.addEventListener("click", () => dialog.close());
});

deleteYes.addEventListener("click", async () => {
    deleteYes.disabled = true;
    try {
        const response = await fetch(form.dataset.deleteUrl, { method: "POST" });
        const data = await readJson(response);
        if (!response.ok) {
            setText("deleteError", data.error || "Could not delete video.");
            return;
        }
        window.location.href = form.dataset.backUrl;
    } catch {
        setText("deleteError", "Network error. Please try again.");
    } finally {
        deleteYes.disabled = false;
    }
});