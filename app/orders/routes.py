from app import db
from app.couriers import bp
from flask import jsonify, request

from app.orders import services


@bp.route('/orders', methods=['POST'])
@bp.route('/orders/<int:id>', methods=['GET','PATCH'])
def orders(id=None):
    if id is None:
        result, error = services.post_orders(request.json)
    else:
        if request.method == 'GET':
            result, error = services.get_orders(id)
        elif request.method == 'PATCH':
            result, error = reservices.patch_orders(id, request.json)
    
    return result