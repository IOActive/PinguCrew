import base64
from unittest import TestCase

from src.frontend.app import app


class Test(TestCase):
    def test_remove_fuzz_target(self):
        self.fail()

    def test_add_FuzzTarget(self):
        fuzzTarget = {
            "fuzzer_engine": "libFuzzer",
            #"fuzzing_target": base64.b64encode(b"XZaaaa").decode(),
            "binary": 'TestFuzz',
            "project": 'testproject'
        }

        fuzz2 = {"id": "62d6f0c724a7cad9fbc9cd78", "fuzzer_engine": "libFuzzer", "project": "test-project", "binary": "fuzzer"}
        headers = {'Authorization': app.config.get('default_user_api_key'),
                   'content-type': 'application/json'}
        with app.test_client() as c:
            rv = c.put('/api/fuzztarget', json=fuzz2, headers=headers)
            json_data = rv.get_json()
            assert 'success' in json_data

    def test_get_fuzzTargets(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzztargets', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

    def test_get_fuzzTarget(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzztargets', headers=headers)
            json_data = rv.get_json()

            fuzzer_engine = json_data[0]["fuzzer_engine"]
            binary = json_data[0]["binary"]
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzztarget?fuzzer_engine=%s&binary=%s' % ("libFuzzer", binary), headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

    def test_remove_fuzzTarget(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzztarget', headers=headers)
            json_data = rv.get_json()

            fuzzTargetId = json_data[0]["_id"]
            rv = c.delete('/api/fuzztarget/%s' %  fuzzTargetId, headers=headers)
            json_data = rv.get_json()
            assert 'success' in json_data



