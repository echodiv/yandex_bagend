import json
import re
from datetime import datetime
from flask import current_app
from pydantic import BaseModel, validator, ValidationError
from typing import List

from app import db
from app.models import Courier, Order, DeliveryTime


class ValidComplete(BaseModel):
    courier_id: int
    order_id: int
    complete_time: str

    @validator('complete_time')
    def valid_time(cls, time):
        pattern =  re.compile('\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{2}Z')
        if not pattern.match(time):
            raise ValidationError
        
class ValidOrder(BaseModel):
    """
    Класс описывающий валидную часть запроса содержащую
    одного курьера
    """
    order_id: int
    weight: float
    region: int
    delivery_hours: List[str]

    @validator('delivery_hours')
    def delivery_hours_format(cls, v: List) -> None:
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
    """
    Добавить заказы в базу данных
    """
    if 'data' not in request.keys():
        return ('invalid request', 400), True

    result, error = validate_post_request(request['data'])
    if error:
        return result, error
    
    # Проходим по каждому заказу в группе и добавляем
    # Ничего не боимся. Слабоумие и отвага!
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
                delivery_from = int(time.split('-')[0].split(':')[0])*60 + int(time.split('-')[0].split(':')[1]),
                delivery_to = int(time.split('-')[1].split(':')[0])*60 + int(time.split('-')[1].split(':')[1]))
            db.session.add(db_times)
        db.session.commit()
    
    # Собираем ответ прямиком из запроса. 300iq
    response = {"orders": [{"id": i['order_id']} for i in request['data']]}
    return (json.dumps(response), 201), False


def validate_post_request(request):
    """
    Проверка валидности тела POST запроса
    """
    error = [{"id": x['order_id']} for x in request
        if sorted(['order_id', 'weight', 'region', 'delivery_hours']) != \
            sorted(x.keys())]
    if error:
        current_app.logger.debug(f'Arguments in request is not valid, {error=}')

    for order in request:
        try:
            res = ValidOrder.parse_obj(order)
        except ValidationError as e:
            current_app.logger.debug(f'Invalid request scehme in {order=}' + str(e.json()))
            if not [True for x in error if order['order_id'] in x.values()]:
                error.append({"id": order['order_id'], "error": e.json()})

    if error:
        return (json.dumps({'couriers': error}), 400), True

    return ('', 200), False


def search_aviable_orders(id):
    """
    Поиск заказов доступных для курьера
    """
    courier = Courier.query.filter_by(fake_id=id).first_or_404()
    max_weight = {"foot": 10, "bike": 15, "car": 50}
    cases_request = f"""SELECT distinct ord.fake_id FROM 'DeliveryTime' d 
        join 'Order' ord on ord.fake_id = d.'order'
        join WorkTime w on w.start < d.delivery_to and 
                    w.end > d.delivery_from 
        join Courier c on c.fake_id = w.courier_id
        where ord.weight < {max_weight[str(courier.type).split('.')[-1]]} AND c.fake_id = {id}
            AND ord.region in (select region_id from 'region' where courier_id = {id})
            AND ord.executor is null"""
    current_app.logger.debug(cases_request)
    cases = db.engine.execute(cases_request)
    
    if not cases:
        return []
    return [int(row[0]) for row in cases]


def assign(orders, id):
    """
    Назначение заказов курьеру
    """
    for order in orders:
        db_order = Order.query.filter_by(fake_id=order).first_or_404()
        db_order.executor = id
        db_order.assign_time = datetime.utcnow()
        db.session.commit()
    return True


def get_active_orders(id):
    """
    Получение заказов активных для курьера
    """
    orders = Order.query.filter_by(
        executor=id,
        complete_time=None
    )
    if not orders:
        return ('', 404), True
    res_orders ={'orders': [{'id': order.fake_id} for order in orders], \
                 'assign_time': orders[0].assign_time}
    
    return (res_orders, 200), False


def validate_assign(request):
    """
    Валидация запроса на установку заказов курьеру
    Возращает номер id курьера
    """
    if "courier_id" not in request.keys() or len(request.keys()) != 1:
        return ('{"error":"courier_id not found"}', 400), True
    try:
        id = int(request["courier_id"])
    except ValueError:
        return ('{"error": "invalid courier_irequest["courier_id"]d type"}', 400), True
    
    courier = Courier.query.filter_by(fake_id=id).all()
    if not courier:
        return ('', 404), True
    
    return int(request["courier_id"]), False


def in_work(id):
    """
    Проверка находится ли курьер в работе
    """
    orders = Order.query.filter_by(executor=id).all()
    current_app.logger.debug(str(orders))
    if orders:
        return True
    return False


def validate_complete(request):
    if [True for x in request.keys() \
        if x not in ['courier_id', 'order_id', 'complete_time']]:
        return '{"error": "invalid params"}', 400
    
    try:
        ValidComplete.parse_obj(request)
    except ValidationError as e:
        current_app.logger.debug(f'Invalid request scehme in {request=}')
        return ('{"error":"invalid request", "details":' + e.json() +'}', 400), True
    
    return ('', 200), False


def complete(request):
    order = Order.query.filter_by(fake_id = request['order_id'],
                  executor = request['courier_id'],
                  complete_time = None).first()
    if not order:
        return ('{"error": "order not found"}', 400), True
    time = datetime.strptime(request['complete_time'][:-4], '%Y-%m-%dT%H:%M:%S')
    order.complete_time = time
    db.session.commit()

    return ('{"order_id":'+ str(request['order_id']) + '}', 200), True