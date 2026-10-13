const input = document.getElementById("profilePicture");
const preview = document.getElementById("profilePreview");
const empty = document.getElementById("profileEmpty");

input.addEventListener("change", () => {
    const file = input.files[0];
    if (!file) return;
    preview.src = URL.createObjectURL(file);
    preview.hidden = false;
    empty.hidden = true;
});