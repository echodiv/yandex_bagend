from app import db
from app.orders import bp
from flask import jsonify, request, current_app
from json import dumps

from app.orders import services


@bp.route('/orders', methods=['POST'])
def orders():
    result, error = services.post_orders(request.json)
    return result


@bp.route('/orders/assign', methods=['POST'])
def assign():
    id, error = services.validate_assign(request.json)
    current_app.logger.debug(f'Request for assing orders')
    if error: 
        current_app.logger.debug(f'Invalid assign request: {id}')
        return id

    if services.in_work(id):
        # Возможно неправильно понял. По факту получается сервис одного дня
        # Вероятно нужно проверять что задачи взяты сегодня
        # И обнулять
        current_app.logger.debug(f'Courier with {id} already in work')
        result, error = services.get_active_orders(id)
        return result

    aviable_orders = services.search_aviable_orders(id)
    if not aviable_orders:
        current_app.logger.debug(f'Aviable orders for courier with {id=} not found')
        return dumps({'orders': []}), 200

    asiign_status = services.assign(aviable_orders, id)
    result, error = services.get_active_orders(id)
    current_app.logger.debug(f'SUCESS: assigned orders for courier {id=} : {result=}')
    return result


@bp.route('/orders/complete', methods=['POST'])
def complete():
    result, error = services.validate_complete(request.json)
    current_app.logger.debug(f'NEW: complete request')
    if error:
        current_app.logger.debug(f'ERROR: invalid complete request {result=}')
        return result
    
    result, error = services.complete(request.json)
    return result
