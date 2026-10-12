# from flask import Blueprint
# from . import homePage


# homePage_bp = Blueprint("homePage", __name__)

from flask import Blueprint

homePage_bp = Blueprint("homePage", __name__)

from . import homePage

