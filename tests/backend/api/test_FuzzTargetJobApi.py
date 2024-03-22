from datetime import datetime
from unittest import TestCase

from src.frontend.app import app


class Test(TestCase):
    def test_remove_fuzz_target(self):
        self.fail()

    def test_get_fuzzTargetJobs(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzzTargetJobs', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

    def test_get_fuzzTargetJob(self):
        with app.test_client() as c:

            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}

            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()
            jobId = json_data[0]["_id"]

            rv = c.get('/api/fuzztargets', headers=headers)
            json_data = rv.get_json()
            fuzztarget_id= json_data[0]["_id"]


            rv = c.get('/api/fuzzTargetJob?engine=%s' % 'libFuzzer', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

            rv = c.get('/api/fuzzTargetJob?job_id=%s' % jobId, headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

            rv = c.get('/api/fuzzTargetJob?job_id=%s&fuzzing_target_id=%s' % (jobId, fuzztarget_id), headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0


    def test_add_fuzzTargetJob(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzztargets', headers=headers)
            json_data = rv.get_json()

            fuzzTargetId = json_data[0]["_id"]
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()

            jobId = json_data[0]["_id"]

        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()

            jobId = json_data[0]["_id"]
        fuzzTargetJob = {
            "job": jobId,
            "engine": "libFuzzer",
            "fuzzing_target": fuzzTargetId,
            "weight": 1,
            "last_run": datetime.now().strftime('%Y-%m-%d'),
        }
        headers = {'Authorization': app.config.get('default_user_api_key'),
                   'content-type': 'application/json'}
        with app.test_client() as c:
            rv = c.put('/api/fuzzTargetJob', json=fuzzTargetJob, headers=headers)
            json_data = rv.get_json()
            assert 'success' in json_data
