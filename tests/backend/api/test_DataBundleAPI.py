from datetime import datetime
from unittest import TestCase

from src.frontend.app import app


class Test(TestCase):
    def test_add_build_metadata(self):
        with app.test_client() as c:
            dataBundle = {
                "name": "test_budmle",
                "bucket_name" : "test",
                "source": '',
                "is_local":  True,
                "sync_to_worker": False,
                "timestamp": datetime.now().strftime('%Y-%m-%d'),
            }
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.put('/api/dataBundle', headers=headers, json=dataBundle)
            json_data = rv.get_json()
            assert 'success' in json_data

    def test_get_DataBundle(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}

            rv = c.get(f'/api/dataBundle?name={"test_budmle"}', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

    def test_delete_DataBundle(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}

            rv = c.delete(f'/api/dataBundle?name={"test_budmle"}', headers=headers)
            json_data = rv.get_json()
            assert 'success' in json_data