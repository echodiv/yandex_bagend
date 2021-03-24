import json
import re
from app import db
from flask import current_app
from pydantic import BaseModel, validator, ValidationError

from app.models import Courier, Order, DeliveryTime


class ValidOrder(BaseModel):
    """
    Класс описывающий валидную часть запроса содержащую
    одного курьера
    """
    order_id: int
    weight: float
    region: int
    delivery_hours: list[str]

    @validator('delivery_hours')
    def delivery_hours_format(cls, v: list) -> None:
        pattern =  re.compile('\d\d:\d\d-\d\d:\d\d')
        if list(filter(lambda x: not pattern.match(x), v)):
            raise ValidationError
    
    @validator('region')
    def region_is_positive(cls, v: int) -> None:
        if v <= 0:
            raise ValidationError
    
    @validator('weight')
    def weight_in_params(cls, v: float) -> None:
        if v < 0.01 or v > 50:
            raise ValidationError
    

def post_orders(request):
    result, error = validate_post_request(request['data'])
    if error:
        return result, error

    for order in request['data']:
        db_order = Order(
            fake_id = order['order_id'],
            weight = order['weight'],
            region = order['region'])
        db.session.add(db_order)
        db.session.commit()
        for time in order['delivery_hours']:
            db_times = DeliveryTime(
                order = db_order.fake_id,
                delivery_from = time.split('-')[0],
                delivery_to = time.split('-')[-1])
            db.session.add(db_times)
        db.session.commit()

    response = {"orders": [{"id": i['order_id']} for i in request['data']]}
    return (response, 201), False


def validate_post_request(request):
    error = [{"id": x['order_id']} for x in request
        if sorted(['order_id', 'weight', 'region', 'delivery_hours']) != \
            sorted(x.keys())]
    if error:
        current_app.logger.debug(f'Arguments in request is not valid, {error=}')

    for order in request:
        try:
            res = ValidOrder.parse_obj(order)
        except ValidationError:
            current_app.logger.debug(f'Invalid request scehme in {order=}')
            if not [True for x in error if order['order_id'] in x.values()]:
                error.append({"id": order['order_id']})

    if error:
        return (json.dumps({'couriers': error}), 400), True

    return ('', 200), False