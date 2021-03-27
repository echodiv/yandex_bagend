from app import db
from app.couriers import bp
from flask import jsonify, request

from app.couriers import services


@bp.route('/couriers', methods=['POST'])
@bp.route('/couriers/<int:id>', methods=['GET','PATCH'])
def couriers(id=None):
    if id is None:
        result, error = services.parse_post_request(request.json)
    else:
        if request.method == 'GET':
            result, error = services.make_get_respose(id)
        elif request.method == 'PATCH':
            result, error = services.parse_patch_request(id, request.json)
            return result
    
    if error is None or error is False:
        return result
    return error, 400
