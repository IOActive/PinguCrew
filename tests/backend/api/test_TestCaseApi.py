import base64
from datetime import datetime
from random import random
from unittest import TestCase as TC

from database.models.Fuzzer import Fuzzer
from src.database.models.Job import Job
from src.database.models.TestCase import TestCase
from src.frontend.app import app


class Test(TC):
    def test_api_get_testcases(self):
        pipeline = [{"$sample": {"size": 1}}]
        jobs = Job.objects().aggregate(pipeline)
        for job1 in jobs:
            job_id = str(job1['_id'])
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/' + job_id + '/testcases', headers=headers)
            json_data = rv.get_json()
            assert 'job not found' not in json_data
            assert 'job name not provided' not in json_data

    def test_api_get_testcase(self):
        pipeline = [{"$sample": {"size": 1}}]

        testcases = TestCase.objects().aggregate(pipeline)

        for testcases1 in testcases:
            testcase_id = str(testcases1['_id'])

        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get(f'/api/testcase/{testcase_id}', headers=headers)
            json_data = rv.get_json()
            assert 'job not found' not in json_data
            assert 'job name not provided' not in json_data

    def test_update_testcase(self):
        pipeline = [{"$sample": {"size": 1}}]
        testcases = TestCase.objects().aggregate(pipeline)
        for testcases1 in testcases:
            testcase_id = str(testcases1['_id'])

        testcase_test = {
            "bug_information": "",
            "fixed": "",
            "test_case": base64.b64encode(b"").decode(),
            "one_time_crasher_flag": False,
            "comments": "",
            "absolute_path": "",
            "queue": "",
            "archived": False,
            "timestamp": datetime.now().strftime('%Y-%m-%d'),
            "status": "done",
            "triaged": False,
            "has_bug_flag": False,
            "open": False,
            "testcase_keys": "",
            "minimized_keys": "",
            "minidump_path": "",
            "additional_metadata": "",
            "job_id": ""
        }
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.post(f'/api/testcase/{testcase_id}', headers=headers, json=testcase_test)
            json_data = rv.get_json()
            assert 'job not found' not in json_data['msg']
            assert 'job name not provided' not in json_data['msg']
            assert 'no json document provided' not in json_data['msg']
            assert 'Cannot resolve field' not in json_data['msg']

    def test_create_testcase(self):
        pipeline = [{"$sample": {"size": 1}}]
        jobs = Job.objects().aggregate(pipeline)
        for job1 in jobs:
            job_id = str(job1['_id'])
        fuzzers = Fuzzer.objects().aggregate(pipeline)
        for fuzzer1 in fuzzers:
            fuzzer_id = str(fuzzer1['_id'])
        testcase_test = {
            "bug_information": "",
            "test_case": base64.b64encode(b"").decode(),
            "fixed": "",
            "one_time_crasher_flag": False,
            "comments": "",
            "absolute_path": "",
            "queue": "",
            "archived": False,
            "timestamp": datetime.now().strftime('%Y-%m-%d'),
            "status": "done",
            "triaged": False,
            "has_bug_flag": False,
            "open": False,
            "testcase_path": "",
            "minimized_keys": "",
            "minidump_keys": "",
            "additional_metadata": "",
            "job_id": job_id,
            "fuzzer_id": fuzzer_id
        }
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.put('/api/testcase', headers=headers, json=testcase_test)
            json_data = rv.get_json()
            assert 'job not found' not in json_data
            assert 'job name not provided' not in json_data
