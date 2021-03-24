import json
import re
from app import db
from flask import current_app
from json.decoder import JSONDecodeError
from pydantic import BaseModel, validator, ValidationError

from app.models import Courier, Region, WorkTime


class ValidCourier(BaseModel):
    """
    Класс описывающий валидную часть запроса содержащую
    одного курьера
    """
    courier_id: int
    courier_type: str
    regions: list[int]
    working_hours: list[str]

    @validator('working_hours')
    def working_hours_format(cls, v: list) -> None:
        pattern =  re.compile('\d\d:\d\d-\d\d:\d\d')
        if list(filter(lambda x: not pattern.match(x), v)):
            raise ValidationError
    
    @validator('regions')
    def regions_is_positive(cls, v: list) -> None:
        if list(filter(lambda x: x <= 0, v)):
            raise ValidationError


def parse_post_request(json_data):
    """
    Функция добавления курьеров в базу данных
    """
    current_app.logger.debug('POST request for couriesrs {}'.format(json_data))
    
    result, error = validate_request(json_data)
    current_app.logger.debug('request is valid')
    if not result:
        return result, error

    for raw_courier in json_data['data']:
        courier = Courier(
                fake_id = raw_courier['courier_id'], # OMG!
                type = raw_courier['courier_type']
            )
        db.session.add(courier)
        current_app.logger.debug(f'Courier with id {raw_courier["courier_id"]} created')
        db.session.commit()
        regions = [Region(courier_id = courier.id, region_id = int(region)) 
            for region in raw_courier['regions']]

        working_hours = [WorkTime(courier_id=courier.id, start=x.split('-')[0], end=x.split('-')[1])
            for x in raw_courier['working_hours']]
        
        db.session.add_all(regions + working_hours)
        db.session.commit()

    response = {"couriers": [{"id": x['courier_id']} for x in json_data['data']]}
    current_app.logger.debug(f'response for couriers POST {response}')

    return (response, 201), None


def validate_request(json_data):
    """
    Валидация POST запроса на добавление курьеров
    На вход получает:
     - тело запроса
    Возвращает:
     - статус валидации
     - ошибки (если валидация провалилась)
    """
    error = [{"id": x['courier_id']} for x in json_data['data']
        if sorted(['courier_id', 'courier_type', 'regions', 'working_hours']) != \
            sorted(x.keys())]
    if error:
        current_app.logger.debug(f'Arguments in request is not valid, {error=}')

    for courier in json_data['data']:
        try:
            res = ValidCourier.parse_obj(courier)
        except ValidationError:
            current_app.logger.debug(f'Invalid request scehme in {courier=}')
            if not [True for x in error if courier['courier_id'] in x.values()]:
                error.append({"id": courier['courier_id']})

    if error:
        return False, json.dumps({'couriers': error})

    return True, None


def parse_patch_request(id, request):
    current_app.logger.debug(f'PATCH request for courier with {id=}', request)
    return 'aa', None


def make_get_respose(id):
    """
    Возвращает информацию о курьере и дополнительную
    статистику: рейтинг и заработок.
    Пример ответа:
    {
        "courier_id": 2,
        "courier_type": "foot",
        "regions": [11, 33, 2],
        "working_hours": ["09:00-18:00"],
        "rating": 4.93,
        "earnings": 10000
    }
    """
    current_app.logger.debug(f'GET request for courier with {id=}')
    cura = Courier.query.filter_by(id=id).first_or_404()

    response = {'courier_id': cura.id,
                'courier_type': str(cura.type).split('.')[-1]}
    
    working = WorkTime.query.filter_by(courier_id=id).all()
    if working:
        response['working_hours'] = [time.start + '-' + time.end for time in working]

    regs = Region.query.filter_by(courier_id=id).all()
    if regs:
        response['regions'] = [reg.region_id for reg in regs]

    current_app.logger.debug(f'GET request :: {response=}')

    return (response, 200), None
