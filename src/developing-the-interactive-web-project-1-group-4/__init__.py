from urllib.parse import urlencode

from sqlalchemy import inspect
from . import models
from flask import Flask, render_template, request,jsonify, current_app , session, redirect , url_for
from .database import db
from .services import get_thumbnails_url, mediaURL , get_current_user, create_default_playlists_for_all_users
from botocore.exceptions import BotoCoreError, ClientError
from .models import Ti_user
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from .routes import homePage_bp, profileInput_bp, uploadVideo_bp, profilePage_bp, manageVideos_bp , subscription_bp, mediaPlayer_bp, accountSettings_bp, trending_bp, library_bp,activity_bp
load_dotenv()
from authlib.integrations.flask_client import OAuth
app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET"]
oauth = OAuth(app)


domain = os.environ["AUTH_0_DOMAIN"]
client_id = os.environ["AUTH_0_CLIENT_ID"]
client_secret = os.environ["AUTH_0_CLIENT_SECRET"]

oauth.register(
    "auth0",
    client_id=client_id,
    client_secret=client_secret,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{domain}/.well-known/openid-configuration",
)
app.register_blueprint(homePage_bp)
app.register_blueprint(profileInput_bp)
app.register_blueprint(uploadVideo_bp)
app.register_blueprint(profilePage_bp)
app.register_blueprint(manageVideos_bp)
app.register_blueprint(subscription_bp)
app.register_blueprint(mediaPlayer_bp)
app.register_blueprint(accountSettings_bp)
app.register_blueprint(trending_bp)
app.register_blueprint(library_bp)
app.register_blueprint(activity_bp)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["Database_url"]
db.init_app(app)
@app.context_processor
def inject_nav_user():
    # Gives every template `nav_user` for the top-right avatar (None when logged out).
    try:
        user = get_current_user()
        if user is None:
            return {"nav_user": None}
        name = user.username or ""
        return {"nav_user": {
            "username": name,
            "initial": name[:1].upper() or "?",
            "picture": mediaURL(user.Profile_picture_key),
        }}
    except Exception:
        return {"nav_user": None}

with app.app_context():
    db.create_all()
    
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    print("Tables in the database:", inspector.get_table_names())
with app.app_context():
    count = create_default_playlists_for_all_users()
    print(f"Default playlists checked for {count} users.")

@app.cli.command("reset-db")
def reset_db(): 

    db.drop_all()
    db.create_all()

    print("Database tables recreated.")

@app.route("/callback", methods=["GET", "POST"])
def callback():
    """
    Callback redirect from Auth0
    """
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    auth0_id = session["user"]["userinfo"]["sub"]

    user = db.session.execute(
    db.select(Ti_user).where(Ti_user.auth0_id == auth0_id)
    ).scalar_one_or_none()
    return redirect(url_for("profileInput.createProfile")) if user is None else redirect(url_for("homePage.home"))

@app.route("/userinfor",methods=["GET"])
def userinfor():
    user = session.get("user")
    if user:
        return jsonify(user)
    else:
        return jsonify({"error": "User not logged in"}), 401
@app.route("/login")
def login():
    """
    Redirects the user to the Auth0 Universal Login (https://auth0.com/docs/authenticate/login/auth0-universal-login)
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        prompt="login"
    )


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for("homePage.home"))
@app.route("/signup")
def signup():
    """
    Redirects the user to the Auth0 Universal Login (https://auth0.com/docs/authenticate/login/auth0-universal-login)
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True),
        prompt="signup"
    )

@app.route("/api/thumbnails", methods=["GET"])
def get_thumbnails():
    thumbnails = get_thumbnails_url()
    return jsonify(thumbnails)

@app.route("/play-video")
def playvid():
    url = mediaURL("videos/00f523e3-5701-4db3-abf6-4bc1ffb3ea95.mp4")
    return render_template('watch.html', url=url, recommendations = recommendations)

if __name__ == "__main__":
    app.run(debug=True)
