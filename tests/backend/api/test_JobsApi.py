import json
from datetime import datetime
from unittest import TestCase

from src.frontend.app import app


class Test(TestCase):
    def test_api_delete_job(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.delete('/api/job/62277a5279f4d20c59a37078', headers=headers)
            json_data = rv.get_json()
            assert json_data['success'] is True

    def test_api_get_job(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()
            assert 'unknown job' not in json_data

    def test_api_create_job(self):
        job_test = {'name': 'TestJob',
                    'description': 'Test',
                    'archived': False,
                    'enabled': True,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'fuzzer_engine': 'Libfuzzer',
                    'platform': 'Linux',
                    'environment_string': ""}
        headers = {'Authorization': app.config.get('default_user_api_key'),
                   'content-type': 'application/json'}
        with app.test_client() as c:
            rv = c.put('/api/job', json=job_test, headers=headers)
            json_data = rv.get_json()
            assert 'success' in json_data
