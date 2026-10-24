from flask import Blueprint

homePage_bp = Blueprint("homePage", __name__)
profileInput_bp = Blueprint("profileInput", __name__)
uploadVideo_bp = Blueprint("uploadVideo", __name__)
profilePage_bp = Blueprint("profilePage", __name__)
manageVideos_bp = Blueprint("manageVideos", __name__)
subscription_bp = Blueprint("subscription", __name__)
mediaPlayer_bp = Blueprint("mediaPlayer", __name__)
accountSettings_bp = Blueprint("accountSettings", __name__)
trending_bp = Blueprint("trending", __name__)
from . import homePage, profileInput, uploadVideo, profilePage, manageVideos, subscription, mediaPlayer, accountSettings, trending

