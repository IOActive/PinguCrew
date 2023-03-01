from datetime import datetime
from unittest import TestCase

from src.frontend.app import app


class Test(TestCase):
    def test_add_build_metadata(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()

            jobId = json_data[0]["_id"]

        with app.test_client() as c:
            buildMetada = {
                "job": jobId,
                "revision": "101",
                "bad_build": False,
                "console_output": "",
                "bot_name": "Pepe",
                'symbols': "",
                "timestamp": datetime.now().strftime('%Y-%m-%d'),
            }
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.put('/api/buildMetada', headers=headers, json=buildMetada)
            json_data = rv.get_json()
            assert 'success' in json_data

    def test_get_BuildMetadata(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}

            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()
            jobId = json_data[0]["_id"]

            rv = c.get('/api/fuzzTargetJob?job_id=%s&revisio=%s' % (jobId, 101), headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0
