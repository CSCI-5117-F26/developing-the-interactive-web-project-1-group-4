from urllib.parse import urlencode

from sqlalchemy import inspect
from . import models
from flask import Flask, render_template, request,jsonify, current_app , session, redirect , url_for
from .database import db
from .services import create_dummy_user, create_dummy_video, get_thumbnails_url, upload_video_to_cloud, upload_thumbnail_to_cloud, get_upload_form_data, create_video_helper, create_draft_helper
from botocore.exceptions import BotoCoreError, ClientError
from .models import Ti_user
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from .routes import homePage_bp, profileInput_bp, uploadVideo_bp, profilePage_bp
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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["Database_url"]
db.init_app(app)
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    print("Tables in the database:", inspector.get_table_names())

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

@app.route('/create-profile', methods=['POST'])
def create_profile():
    username = request.args.get('username')
    email = request.args.get('email')
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    create_dummy_user(username, email, first_name, last_name)
    return "successfull"
@app.route('/create-video', methods=['POST'])
def create_video():
    ti_user = request.args.get('ti_user',type=int)
    thumbnail_key = request.args.get('thumbnail_key')
    duration = request.args.get('duration',type=int)
    title = request.args.get('title')
    video_key = request.args.get('video_key')
    language = request.args.get('language')
    original = request.args.get("original", "false").lower() == "true"
    create_dummy_video(ti_user, thumbnail_key, duration, title, video_key, language, original)
    return "successfull"



@app.route("/api/thumbnails", methods=["GET"])
def get_thumbnails():
    thumbnails = get_thumbnails_url()
    return jsonify(thumbnails)

if __name__ == "__main__":
    app.run(debug=True)

