import os, re, uuid
from datetime import datetime, timezone
from flask import render_template, request, current_app,jsonify, redirect, url_for, session
from botocore.exceptions import BotoCoreError, ClientError
from . import profileInput_bp
from ..services import saveProfile, upload_profile_picture_to_cloud , get_current_user, mediaURL, create_default_playlists


fields = {
    # field name:        (max length, required?)
    "firstName":         (50, True),
    "lastName":          (50, True),
    "userName":          (50, True),
    "userPhoneNumber":   (20, False),
    "userBio":           (200, False),
}

userNameRE = re.compile(r"^[A-Za-z0-9_.]{3,50}$")
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
    if data["userPhoneNumber"] and "userPhoneNumber" not in errors and not userPhoneRE.match(data["userPhoneNumber"]):
        errors["userPhoneNumber"] = "Enter a valid phone number."

    return data, errors


def savePicture(file):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    if ext not in imageTypes:
        return None, "Picture must be PNG, JPG, or WEBP."

    # Read at most one byte beyond the size limit
    content = file.read(imageSize + 1)

    if len(content) > imageSize:
        return None, "Picture must be 5 MB or smaller."

    # Reading moved the stream forward; rewind before uploading
    file.stream.seek(0)

    try:
        profile_picture_key = upload_profile_picture_to_cloud(file)
    except ValueError as error:
        return None, str(error)
    except (BotoCoreError, ClientError):
        current_app.logger.exception("Profile picture upload to R2 failed")
        return None, "Profile picture upload failed. Please try again."

    return profile_picture_key, None


@profileInput_bp.route("/createProfile", methods=["GET", "POST"])
def createProfile():
    if request.method == "GET":
        return render_template("createProfile.html",form={}, errors={}, saved=None)

    username = request.form.get("userName", "").strip()
    first_name = request.form.get("firstName", "").strip()
    last_name = request.form.get("lastName", "").strip()
    bio = request.form.get("userBio", "").strip()
    phone_number = request.form.get("userPhoneNumber", "").strip()
    picture = request.files.get("profilePicture")
    contact_me = request.form.get("userContact", "").strip()

    # Use the authenticated identity from the session
    userinfo = session["user"]["userinfo"]
    email = userinfo.get("email")
    auth0_id = userinfo["sub"]

    picture = request.files.get("profilePicture")
    picture_filename = None

    if picture and picture.filename:
        picture_filename, error = savePicture(picture)

        if error:
            return render_template(
                "createProfile.html",
                form=request.form.to_dict(),
                errors={"profilePicture": error},
                saved=None,
            ), 400
    

    saveProfile(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        auth0_id=auth0_id,
        bio=bio,
        phone_number=phone_number,
        profile_picture_key=picture_filename,
        contact_me=contact_me,
    )
    user = get_current_user()
    create_default_playlists(user.ti_user_id)

    return redirect(url_for("homePage.home"))