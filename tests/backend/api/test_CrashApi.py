import base64
from datetime import datetime
from unittest import TestCase

from frontend.app import app


class Test(TestCase):
    def test_add_crash(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()

            jobID = json_data[0]["_id"]

        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get(f'/api/{jobID}/testcases', headers=headers)
            json_data = rv.get_json()

            testcaseID = json_data[0]["_id"]

        with app.test_client() as c:
            crash = {
                "testcase_id": testcaseID,
                "crash_signal": 1,
                "exploitability": "",
                "crash_hash": "",
                "verified": True,
                "additional": "",
                "iteration": 2,
                "crash_type": "",
                "crash_address": "",
                "crash_state": "",
                "crash_stacktrace": base64.b64encode(b"").decode(),
                "regression": "",
                "security_severity": 1,
                "absolute_path": "",
                "security_flag": True,
                "reproducible_flag": True,
                "return_code": "-1",
                "gestures": [],
                "resource_list": [],
                "fuzzing_strategy": "",
                "should_be_ignored": False,
                "application_command_line": "",
                "unsymbolized_crash_stacktrace": base64.b64encode(b"").decode(),
                "crash_frame": base64.b64encode(b"").decode(),
                "crash_info": "",
            }
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.put('/api/crash', headers=headers, json=crash)
            json_data = rv.get_json()
            assert 'success' in json_data

    def test_get_crash(self):
        headers = {'Authorization': app.config.get('default_user_api_key'),
                   'content-type': 'application/json'}

        with app.test_client() as c:
            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()
            jobID = json_data[0]["_id"]

        with app.test_client() as c:
            rv = c.get(f'/api/{jobID}/testcases', headers=headers)
            json_data = rv.get_json()

            testcaseID = json_data[0]["_id"]

        with app.test_client() as c:
            rv = c.get(f'/api/crash?testcase_id={testcaseID}', headers=headers)
            json_data = rv.get_json()
            crash_id = json_data[0]["_id"]

        with app.test_client() as c:
            rv = c.get(f'/api/crash?id={crash_id}', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

    def test_delete_crash(self):
        headers = {'Authorization': app.config.get('default_user_api_key'),
                   'content-type': 'application/json'}

        with app.test_client() as c:
            rv = c.get('/api/jobs', headers=headers)
            json_data = rv.get_json()
            jobID = json_data[0]["_id"]

        with app.test_client() as c:
            rv = c.get(f'/api/{jobID}/testcases', headers=headers)
            json_data = rv.get_json()

            testcaseID = json_data[0]["_id"]

        with app.test_client() as c:
            rv = c.get(f'/api/crash?testcase_id={testcaseID}', headers=headers)
            json_data = rv.get_json()
            crash_id = json_data[0]["_id"]

        with app.test_client() as c:
            rv = c.delete(f'/api/crash?id={crash_id}', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

