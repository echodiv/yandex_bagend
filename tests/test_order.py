import json
import unittest

from app import create_app, db
from unittest.mock import Mock, patch
from app.orders import services

from app.models import Courier, Region, WorkTime, Order


class CouriersServicesValidate(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        self.app_context.pop()

    def test_validate_post(self):
        data = json.loads("""[
        {
            \"order_id\": 1,
            \"weight\": 0.23,
            \"region\": 12,
            \"delivery_hours\": [\"09:00-18:00\"]
        }]""")
        result, error = services.validate_post_request(data)
        self.assertEqual(result, ('', 200))
        self.assertEqual(error, False)

    def test_small_weight(self):
        data = json.loads("""[
        {
            \"order_id\": 1,
            \"weight\": 0.005,
            \"region\": 12,
            \"delivery_hours\": [\"09:00-18:00\"]
        }]""")
        result, error = services.validate_post_request(data)
        self.assertEqual(result, (json.dumps({'couriers': [{'id': 1}]}), 400))
        self.assertEqual(error, True)

    def test_big_weight(self):
        data = json.loads("""[
        {
            \"order_id\": 1,
            \"weight\": 50.1,
            \"region\": 12,
            \"delivery_hours\": [\"09:00-18:00\"]
        }]""")
        result, error = services.validate_post_request(data)
        self.assertEqual(result, (json.dumps({'couriers': [{'id': 1}]}), 400))
        self.assertEqual(error, True)


class AddOrdersToDatabase(unittest.TestCase):
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

    @patch('app.orders.services.validate_post_request')
    def test_add_two_orders(self, validate_mock):
        validate_mock.return_value = (('', 200), False)
        data = json.loads("""
        {\"data\": [
        {
            \"order_id\": 1,
            \"weight\": 0.23,
            \"region\": 12,
            \"delivery_hours\": [\"09:00-18:00\"]
        },{
            \"order_id\": 2,
            \"weight\": 15,
            \"region\": 1,
            \"delivery_hours\": [\"09:00-18:00\"]
        }]}
        """)
        result, error = services.post_orders(data)
        self.assertFalse(error)
        self.assertEqual(result, (json.dumps({"orders": [{"id": 1}, {"id": 2}]}), 201))
