import json
import unittest


class MyAppCase(unittest.TestCase):
    def setUp(self):
        my_app.app.config['TESTING'] = True
        self.app = my_app.app.test_client()

    def test_dummy(self):
        response = self.app.get("/dummy")
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(data['dummy'], "dummy-value")