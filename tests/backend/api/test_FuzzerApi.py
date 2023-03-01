from datetime import datetime
from unittest import TestCase

from src.frontend.app import app


class Test(TestCase):
    def test_add_fuzzer(self):
        fuzzer_test = {
            "timestamp": datetime.now(),
            "name": "libFuzzer",
            "filename": "TestFuzzer.zip",
            "blobstore_path": "~/mount_point/nfs/fuzzers/TestFuzzer",
            "file_size": "1MB",
            "executable_path": "~/mount_point/nfs/fuzzers/TestFuzzer/TestFuzzer",
            "timeout": 10000,
            "supported_platforms": "linux",
            "launcher_script": "~/mount_point/nfs/fuzzers/TestFuzzer/TestFuzzer.sh",
            "max_testcases": 100,
            "untrusted_content": False,
            "additional_environment_string": "",
            "stats_columns": "",
            "stats_column_descriptions": "",
            "builtin": True,
            "differential": False,
            "has_large_testcases": False
        }

        headers = {'Authorization': app.config.get('default_user_api_key'),
                   'content-type': 'application/json'}
        with app.test_client() as c:
            rv = c.put('/api/fuzzer', json=fuzzer_test, headers=headers)
            json_data = rv.get_json()
            assert {'success': True} == json_data

    def test_get_fuzzers(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzzers', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

    def test_get_fuzzer(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzzer?name=libFuzzer', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0
            fuzzer_test_id = json_data["_id"]

        with app.test_client() as c2:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv2 = c2.get('/api/fuzzer?id=%s' % fuzzer_test_id, headers=headers)
            json_data2 = rv2.get_json()
            assert len(json_data2) > 0

    def test_delete_fuzzer(self):
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/fuzzers', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0
            fuzzer_test_name = json_data[0]["name"]

        with app.test_client() as c2:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv2 = c2.delete('/api/fuzzer/%s' % fuzzer_test_name, headers=headers)
            json_data2 = rv2.get_json()
            assert {'success': True} == json_data2
