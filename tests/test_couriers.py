import json
import unittest

from app import create_app, db
from unittest.mock import Mock, patch
from app.couriers import services

from app.models import Courier, Region, WorkTime


# class CouriersBusines(unittest.TestCase):
    # def setUp(self):
        # my_app.app.config['TESTING'] = True
        # self.app = my_app.app.test_client()
# 
    # def test_dummy(self):
        # response = self.app.get("/dummy")
        # data = json.loads(response.get_data(as_text=True))
# 
        # self.assertEqual(data['dummy'], "dummy-value")


class CouriersServicesValidate(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        self.app_context.pop()

    def test_validate_post(self):
        data = json.loads("""{\"data\":
        [{\"courier_id\": 1,
        \"courier_type\": \"foot\",
        \"regions\": [1, 12, 22], 
        \"working_hours\": [\"11:35-14:05\", \"09:00-11:00\"]
        }]}""")
        result, error = services.validate_request(data)
        self.assertEqual(result, True)
        self.assertEqual(error, None)

  
    def test_not_contain_mondatory_param(self):
        data = json.loads("""{\"data\":[{\"courier_type\": \"foot\",\"courier_id\": 1,
        \"working_hours\": [\"11:35-14:05\", \"09:00-11:00\"]
        },{\"courier_id\": 2,\"courier_type\": \"bike\",
        \"regions\": [22],\"working_hours\": [\"09:00-18:00\"]}]}""")
        result, error = services.validate_request(data)
        exp_error = """{\"couriers\": [{\"id\": 1}]}"""
        self.assertEqual(result, False)
        self.assertEqual(error, exp_error)

    def test_not_contain_mondatory_param_in_two_requests(self):
        data = json.loads("""{\"data\":[{\"courier_type\": \"foot\",\"courier_id\": 1,
        \"working_hours\": [\"11:35-14:05\", \"09:00-11:00\"]
        },{\"courier_id\": 2,\"courier_type\": \"bike\",\"regions\": [22]}]}""")
        result, error = services.validate_request(data)
        exp_error = """{\"couriers\": [{\"id\": 1}, {\"id\": 2}]}"""
        self.assertEqual(result, False)
        self.assertEqual(error, exp_error)

    def test_valid_request_with_enother_params(self):
        data = json.loads("""{\"data\":[{\"courier_id\": 1,\"courier_type\": \"foot\",
        \"regions\": [1, 12, 22], \"working_hours\": [\"11:35-14:05\", \"09:00-11:00\"]
        },{\"courier_id\": 2,\"courier_type\": \"bike\",
        \"regions\": [22],\"other\":1,\"working_hours\": [\"09:00-18:00\"]}]}""")
        result, error = services.validate_request(data)
        exp_error = """{\"couriers\": [{\"id\": 2}]}"""
        self.assertEqual(result, False)
        self.assertEqual(error, exp_error)
    
    def test_invalid_region_is_string(self):
        data = json.loads("""{\"data\":
        [{\"courier_id\": 1,
        \"courier_type\": \"foot\",
        \"regions\": ["a", 12, 22], 
        \"working_hours\": [\"11:35-14:05\", \"09:00-11:00\"]
        }]}""")
        result, error = services.validate_request(data)
        exp_error = """{\"couriers\": [{\"id\": 1}]}"""
        self.assertEqual(result, False)
        self.assertEqual(error, exp_error)
    
    def test_invalid_region_is_negative(self):
        data = json.loads("""{\"data\":
        [{\"courier_id\": 1,
        \"courier_type\": \"foot\",
        \"regions\": [-1, 12, 22], 
        \"working_hours\": [\"11:35-14:05\", \"09:00-11:00\"]
        }]}""")
        result, error = services.validate_request(data)
        exp_error = """{\"couriers\": [{\"id\": 1}]}"""
        self.assertEqual(result, False)
        self.assertEqual(error, exp_error)

    def test_invalid_region_is_zero(self):
        data = json.loads("""{\"data\":
        [{\"courier_id\": 1,
        \"courier_type\": \"foot\",
        \"regions\": [0, 12, 22], 
        \"working_hours\": [\"11:35-14:05\", \"09:00-11:00\"]
        }]}""")
        result, error = services.validate_request(data)
        exp_error = """{\"couriers\": [{\"id\": 1}]}"""
        self.assertEqual(result, False)
        self.assertEqual(error, exp_error)

    def test_invalid_hours(self):
        data = json.loads("""{\"data\":
        [{\"courier_id\": 1,
        \"courier_type\": \"foot\",
        \"regions\": [12, 22], 
        \"working_hours\": [\"11:35-1:05\", \"s00-11:00\"]
        }]}""")
        result, error = services.validate_request(data)
        exp_error = """{\"couriers\": [{\"id\": 1}]}"""
        self.assertEqual(result, False)
        self.assertEqual(error, exp_error)


class AddCouriersToDatabase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        db.session.query(Courier).delete()
        db.session.query(Region).delete()
        db.session.query(WorkTime).delete()
        db.session.remove()
        self.app_context.pop()

    @patch('app.couriers.services.validate_request')
    def test_add_one_courier(self, validate_mock):
        validate_mock.return_value = (True, None)
        data = json.loads("""{\"data\":[{\"courier_id\": 1,\"courier_type\": \"foot\",
        \"regions\": [1, 12, 22], \"working_hours\": [\"11:35-14:05\", \"09:00-11:00\"]}]}""")
        result, error = services.parse_post_request(data)
        self.assertEqual(error, None)


class PatchRequest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        db.session.query(Courier).delete()
        db.session.query(Region).delete()
        db.session.query(WorkTime).delete()
        db.session.remove()
        self.app_context.pop()
    
    def test_empmty_patch(self):
        request = {"regions": [11, 33, 2]}
        result, error = services.validate_patch_request(request)
        self.assertEqual(result, ('', 200))
        self.assertFalse(error)
    
    def test_invalid_courier_type(self):
        request = {"courier_type": [11, 33, 2]}
        result, error = services.validate_patch_request(request)
        self.assertEqual(result, ('{"error": "invalid courier_type type"}', 400))
        self.assertTrue(error)
 
    def test_invalid_region_type(self):
        request = {"regions": ["a"]}
        result, error = services.validate_patch_request(request)
        self.assertEqual(result, ('{"error": "invalid region type"}', 400))
        self.assertTrue(error)

    def test_invalid_wh_type(self):
        request = {"working_hours": [11, 33, 2]}
        result, error = services.validate_patch_request(request)
        self.assertEqual(result, ('{"error": "invalid working_hours type"}', 400))
        self.assertTrue(error)

    def test_invalid_one_wh_type(self):
        request = {"working_hours": ['lool']}
        result, error = services.validate_patch_request(request)
        self.assertEqual(result, ('{"error": "invalid working_hours type"}', 400))
        self.assertTrue(error)