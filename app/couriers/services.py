import json
import re
from app import db
from flask import current_app
from json.decoder import JSONDecodeError
from pydantic import BaseModel, validator, ValidationError

from app.models import Courier, Region, WorkTime


class ValidCourier(BaseModel):
    courier_id: int
    courier_type: str
    regions: list[int]
    working_hours: list[str]

    @validator('working_hours')
    def working_hours_format(cls, v: str):
        pattern =  re.compile('\d\d:\d\d-\d\d:\d\d')
        for time in v:
            if not pattern.match(time):
                raise ValidationError
    

def parse_post_request(request):
    # current_app.logger.debug('POST request for couriesrs {}'.format(request))
    
    result, error = validate_request(request)
    if not result:
        return False, error
    
    json_data = json.loads(request)

    for raw_courier in json_data['data']:
        courier = Courier(
                type = raw_courier['courier_type']
            )
        db.session.add(courier)
        db.session.commit()
        regions = [Region(courier_id = courier.id, region_id = int(region)) 
            for region in raw_courier['regions']]

        working_hours = [WorkTime(courier_id=courier.id, start=x.split('-')[0], end=x.split('-')[1])
            for x in raw_courier['working_hours']]
        
        db.session.add_all(regions + working_hours)
        db.session.commit()

    return 'bb', None

def validate_request(data):
    try:
        json_data = json.loads(data)
    except JSONDecodeError as e:
        return False, '{"couriers": {"error": "invalid request"}}'
    error = [{"id": x['courier_id']} for x in json_data['data']
        if sorted(['courier_id', 'courier_type', 'regions', 'working_hours']) != \
            sorted(x.keys())]
    for courier in json_data['data']:
        try:
            res = ValidCourier.parse_obj(courier)
        except ValidationError:
            if not [True for x in error if courier['courier_id'] in x.values()]:
                error.append({"id": courier['courier_id']})

    if error:
        return False, json.dumps({'couriers': error})
        

    return True, None

def parse_patch_request(id, request):
    current_app.logger.debug(f'PATCH request for courier with {id=}', request)
    return 'aa', None

def make_get_respose(id):
    current_app.logger.debug(f'GET request for courier with {id=}')
    return 'cc', None