from flask import Blueprint

homePage_bp = Blueprint("homePage", __name__)
profileInput_bp = Blueprint("profileInput", __name__)

from . import homePage, profileInput

