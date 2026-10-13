import os, re, uuid
from datetime import datetime, timezone

from flask import render_template, request, current_app

from . import profileInput_bp
from ..services import saveProfile

fields = {
    # field name:        (max length, required?)
    "firstName":         (50, True),
    "lastName":          (50, True),
    "userName":          (50, True),
    "userEmail":         (100, True),
    "userPhoneNumber":   (20, False),
    "userBio":           (200, False),
}

userNameRE = re.compile(r"^[A-Za-z0-9_.]{3,50}$")
userEmailRE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
userPhoneRE = re.compile(r"^[0-9+()\-\s]{9,10}$")

imageTypes = {"png", "jpg", "jpeg", "webp"}
imageSize = 5 * 1024 * 1024   # 5 MB


def validate(form):
    data = {name: form.get(name, "").strip() for name in fields}
    errors = {}

    for name, (maxLen, required) in fields.items():
        if required and not data[name]:
            errors[name] = "This field is required."
        elif len(data[name]) > maxLen:
            errors[name] = f"Must be {maxLen} characters or fewer."

    if "userName" not in errors and not userNameRE.match(data["userName"]):
        errors["userName"] = "3-50 characters: letters, numbers, _ or . only."
    if "userEmail" not in errors and not userEmailRE.match(data["userEmail"]):
        errors["userEmail"] = "Enter a valid email address."
    if data["userPhoneNumber"] and "userPhoneNumber" not in errors and not userPhoneRE.match(data["userPhoneNumber"]):
        errors["userPhoneNumber"] = "Enter a valid phone number."

    return data, errors


def savePicture(file):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in imageTypes:
        return None, "Picture must be PNG, JPG, or WEBP."

    content = file.read()
    if len(content) > imageSize:
        return None, "Picture must be 5 MB or smaller."

    folder = os.path.join(current_app.instance_path, "profilePictures")
    os.makedirs(folder, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(folder, filename), "wb") as out:
        out.write(content)
    return filename, None


@profileInput_bp.route("/createProfile", methods=["GET", "POST"])
def createProfile():
    if request.method == "GET":
        return render_template("createProfile.html", form={}, errors={}, saved=None)

    data, errors = validate(request.form)

    picture = request.files.get("profilePicture")
    data["profilePicture"] = None
    if not errors and picture and picture.filename:
        filename, error = savePicture(picture)
        if error:
            errors["profilePicture"] = error
        else:
            data["profilePicture"] = filename

    if errors:
        return render_template("createProfile.html", form=data, errors=errors, saved=None), 400

    data["submittedAt"] = datetime.now(timezone.utc).isoformat()
    saveProfile(data)
    return render_template("createProfile.html", form={}, errors={}, saved=data)