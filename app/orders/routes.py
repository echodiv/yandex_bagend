from app import db
from app.orders import bp
from flask import jsonify


@bp.route('/')
def orders():
    return 'Responce(status=200)'