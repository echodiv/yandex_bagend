from flask import Blueprint

bp = Blueprint('couriers', __name__)

from app.couriers import routes