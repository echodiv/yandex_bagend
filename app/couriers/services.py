import json
import re
from app import db
from flask import current_app
from json.decoder import JSONDecodeError
from pydantic import BaseModel, validator, ValidationError
from typing import List

from app.models import Courier, Region, WorkTime


class ValidCourier(BaseModel):
    """
    Класс описывающий валидную часть запроса содержащую
    одного курьера
    """
    courier_id: int
    courier_type: str
    regions: List[int]
    working_hours: List[str]

    @validator('working_hours')
    def working_hours_format(cls, v: List) -> None:
        pattern =  re.compile('\d\d:\d\d-\d\d:\d\d')
        if list(filter(lambda x: not pattern.match(x), v)):
            raise ValidationError
    
    @validator('regions')
    def regions_is_positive(cls, v: List) -> None:
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
        regions = [Region(courier_id = courier.fake_id, region_id = int(region)) 
            for region in raw_courier['regions']]

        working_hours = [WorkTime(
            courier_id=courier.fake_id, 
            start=int(x.split('-')[0].split(':')[0])*60 + int(x.split('-')[0].split(':')[1]), 
            end=int(x.split('-')[1].split(':')[0])*60 + int(x.split('-')[1].split(':')[1]))
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
        except ValidationError as e:
            current_app.logger.debug(f'Invalid request scehme in {courier=}')
            if not [True for x in error if courier['courier_id'] in x.values()]:
                error.append({"id": courier['courier_id']})

    if error:
        return False, json.dumps({'couriers': error})

    return True, None


def parse_patch_request(id, request):
    # Ничего не боимся. Слабоумие и отвага!
    current_app.logger.debug(f'PATCH request for courier with {id=}', request)
    result, error = validate_patch_request(request)
    if error:
        return result, error

    courier = Courier.query.filter_by(fake_id=id).first_or_404()
    
    # Перезаписываем. Про мёрж не было ни слова
    if 'regions' in request.keys():
        regions = Region.query.filter_by(courier_id=courier.id)
        if regions:
            regions.delete()
        regions = [Region(courier_id = courier.id, region_id = int(region)) 
            for region in request['regions']]
        db.session.add_all(regions)

    # Повторяем безумие
    if 'working_hours' in request.keys():
        hours = WorkTime.query.filter_by(courier_id=courier.id)
        if hours:
            hours.delete()
            working_hours = [WorkTime(
                courier_id=courier.id, 
                start=int(x.split('-')[0].split(':')[0])*60 + int(x.split('-')[0].split(':')[1]), 
                end=int(x.split('-')[1].split(':')[0])*60 + int(x.split('-')[1].split(':')[1]))
                    for x in request['working_hours']]
        db.session.add_all(working_hours)
    
    if 'courier_type' in request.keys():
        courier.type = request['courier_type']
    
    # Коммитим всё за раз. (=
    db.session.commit()

    return ('', 200), False


def validate_patch_request(request):
    """
    Валидация patch запроса на обновление пользователя
    Валидируем всё руками
    """
    if 'working_hours' not in request.keys() and \
       'courier_type' not in request.keys() and \
       'regions' not in request.keys():
        return ('{"error": "request not contain valid keys"}', 400), True
    
    if [True for x in request.keys() if x not in ['working_hours','courier_type','regions']]:
        return ('{"error": "invalid key in request"}', 400), True
    
    if 'courier_type' in request.keys():
        if type(request['courier_type']) is not str:
            return ('{"error": "invalid courier_type type"}', 400), True

        if request['courier_type'] not in ['foot', 'bike', 'car']:
            return ('{"error": "invalid courier_type value"}', 400), True

    if 'working_hours' in request.keys():
        if type(request['working_hours']) is not list:
            return ('{"error": "invalid working_hours type"}', 400), True
        pattern =  re.compile('\d\d:\d\d-\d\d:\d\d')
        for i in request['working_hours']:
            if not pattern.match(str(i)):
                return ('{"error": "invalid working_hours type"}', 400), True

    if 'regions' in request.keys():
        if type(request['regions']) is not list:
            return ('{"error": "invalid regions type"}', 400), True
        for i in request['regions']:
            try:
                int(i)
            except ValueError:
                return ('{"error": "invalid region type"}', 400), True

    return ('', 200), False


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
    cura = Courier.query.filter_by(fake_id=id).first_or_404()

    response = {'courier_id': cura.id,
                'courier_type': str(cura.type).split('.')[-1]}
    
    # как я понял можно и обнулить всё и получить курьера без
    # рабочего времени\региона. Можно даже понять зачем
    working = WorkTime.query.filter_by(courier_id=id).all()
    if working:
        for time in working:
            h_start = str(time.start//60).zfill(2)
            m_start = str(time.start%60).zfill(2)
            h_end = str(time.end//60).zfill(2)
            m_end = str(time.end%60).zfill(2)
            if 'working_hours' not in response.keys():
                response['working_hours'] = [f'{h_start}:{m_start}-{h_end}:{m_end}']
            else:
                response['working_hours'].append(f'{h_start}:{m_start}-{h_end}:{m_end}')

    regs = Region.query.filter_by(courier_id=id).all()
    if regs:
        response['regions'] = [reg.region_id for reg in regs]

    current_app.logger.debug(f'GET request :: {response=}')

    return (response, 200), None
