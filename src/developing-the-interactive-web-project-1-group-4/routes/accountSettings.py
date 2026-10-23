import re

from flask import render_template, request, jsonify, session, redirect, url_for, current_app
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from . import accountSettings_bp
from ..database import db
from ..models import Ti_user
from ..services import get_current_user, mediaURL, deleteAccountData
from .profileInput import savePicture, userNameRE, userPhoneRE

emailRE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
bioMaxLength = 200

# form field name -> (Ti_user column, max length, required?)
infoFields = {
    "firstName":       ("first_name", 50, True),
    "lastName":        ("last_name", 50, True),
    "userName":        ("username", 50, True),
    "userEmail":       ("email", 100, True),
    "userPhoneNumber": ("Phone_number", 20, False),
}


# ---------------- Helpers ----------------

def accountData(user):
    """Everything the page and pop-ups need about the user."""
    return {
        "firstName": user.first_name,
        "lastName": user.last_name,
        "userName": user.username,
        "userEmail": user.email,
        "userPhoneNumber": user.Phone_number or "",
        "userBio": user.Bio or "",
        "profilePictureURL": mediaURL(user.Profile_picture_key) or "",
    }


def apiUser():
    """Returns (user, None) if allowed, or (None, errorResponse)."""
    if session.get("user") is None:
        return None, (jsonify(error="Please log in first."), 401)
    # Changes must come from our own JavaScript. Other websites can't add this header,
    # so they can't trick a logged-in user's browser into changing their account (CSRF).
    if request.method != "GET" and request.headers.get("X-Requested-With") != "fetch":
        return None, (jsonify(error="Invalid request."), 400)
    user = get_current_user()
    if user is None:
        return None, (jsonify(error="Please create your profile first."), 403)
    return user, None


def isTaken(column, value, user):
    """True if another user already has this username/email (case-insensitive)."""
    otherId = db.session.scalar(
        select(Ti_user.ti_user_id).where(
            func.lower(column) == value.lower(),
            Ti_user.ti_user_id != user.ti_user_id,
        )
    )
    return otherId is not None


def deleteCloudFile(key):
    """Remove an old file from R2. A failure here shouldn't break the request."""
    if not key:
        return
    try:
        from ..storage import r2, bucket_name
        r2.delete_object(Bucket=bucket_name, Key=key)
    except Exception:
        current_app.logger.exception("Could not delete %s from R2", key)


# ---------------- Page ----------------

@accountSettings_bp.get("/account-settings")
def accountSettings():
    if session.get("user") is None:
        return redirect(url_for("login"))
    user = get_current_user()
    if user is None:
        return redirect(url_for("profileInput.createProfile"))
    return render_template("accountSettings.html", account=accountData(user))


@accountSettings_bp.get("/api/account")
def getAccount():
    user, error = apiUser()
    if error:
        return error
    return jsonify(accountData(user))


# ---------------- Profile picture ----------------

@accountSettings_bp.post("/api/account/picture")
def updatePicture():
    user, error = apiUser()
    if error:
        return error

    picture = request.files.get("profilePicture")
    if picture is None or not picture.filename:
        return jsonify(errors={"profilePicture": "Please choose a picture."}), 400

    newKey, uploadError = savePicture(picture)        # same checks + R2 upload as createProfile
    if uploadError:
        return jsonify(errors={"profilePicture": uploadError}), 400

    oldKey = user.Profile_picture_key
    user.Profile_picture_key = newKey
    db.session.commit()
    deleteCloudFile(oldKey)                           # only after the new one is saved

    return jsonify(accountData(user))


# ---------------- Account info ----------------

@accountSettings_bp.patch("/api/account/info")
def updateInfo():
    user, error = apiUser()
    if error:
        return error

    data = {name: request.form.get(name, "").strip() for name in infoFields}
    errors = {}

    for name, (column, maxLength, required) in infoFields.items():
        if required and not data[name]:
            errors[name] = "This field is required."
        elif len(data[name]) > maxLength:
            errors[name] = f"Must be {maxLength} characters or fewer."

    if "userName" not in errors and not userNameRE.match(data["userName"]):
        errors["userName"] = "3-50 characters: letters, numbers, _ or . only."
    if "userEmail" not in errors and not emailRE.match(data["userEmail"]):
        errors["userEmail"] = "Enter a valid email address."
    if data["userPhoneNumber"] and "userPhoneNumber" not in errors and not userPhoneRE.match(data["userPhoneNumber"]):
        errors["userPhoneNumber"] = "Enter a valid phone number."

    if "userName" not in errors and isTaken(Ti_user.username, data["userName"], user):
        errors["userName"] = "That username is already taken."
    if "userEmail" not in errors and isTaken(Ti_user.email, data["userEmail"], user):
        errors["userEmail"] = "That email is already in use."

    if errors:
        return jsonify(errors=errors), 400

    for name, (column, _, _) in infoFields.items():
        setattr(user, column, data[name] or None)

    try:
        db.session.commit()
    except IntegrityError:          # two people grabbed the same username at the same moment
        db.session.rollback()
        return jsonify(error="That username or email was just taken. Please try another."), 409

    return jsonify(accountData(user))


# ---------------- Bio ----------------

@accountSettings_bp.patch("/api/account/bio")
def updateBio():
    user, error = apiUser()
    if error:
        return error

    bio = request.form.get("userBio", "").strip()
    if len(bio) > bioMaxLength:
        return jsonify(errors={"userBio": f"Bio must be {bioMaxLength} characters or fewer."}), 400

    user.Bio = bio or None
    db.session.commit()
    return jsonify(accountData(user))


# ---------------- Delete account ----------------

@accountSettings_bp.delete("/api/account")
def deleteAccount():
    user, error = apiUser()
    if error:
        return error

    if request.form.get("confirmUsername", "").strip() != user.username:
        return jsonify(errors={"confirmUsername": "Type your username exactly to confirm."}), 400

    try:
        deleteAccountData(user)
    except Exception:
        current_app.logger.exception("Account deletion failed")
        return jsonify(error="Your account couldn't be deleted. Please try again."), 500

    session.clear()
    # Go through logout so the Auth0 login session ends too
    return jsonify(redirectURL=url_for("logout"))