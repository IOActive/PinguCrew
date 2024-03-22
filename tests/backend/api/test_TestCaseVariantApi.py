from unittest import TestCase as TC

from database.models.TestCaseVariant import TestCaseVariant
from src.database.models.TestCase import TestCase
from src.frontend.app import app


class Test(TC):
    def test_api_get_testcase_variant(self):
        pipeline = [{"$sample": {"size": 1}}]

        testcases = TestCase.objects().aggregate(pipeline)

        for testcases1 in testcases:
            testcase_id = str(testcases1['_id'])
            job_id = str(testcases1['job_id'])

        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get(f'/api/testcase_variant?testcase_id={testcase_id}&job_id={job_id}', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

    def test_update_testcase_variant(self):
        pipeline = [{"$sample": {"size": 1}}]
        testcasevariants = TestCaseVariant.objects().aggregate(pipeline)
        for testcasesvariant1 in testcasevariants:
            testcase_variant_id = str(testcasesvariant1['_id'])

        testcase_test = {
            "is_similar": True
        }
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.post(f'/api/testcase_variant/{testcase_variant_id}', headers=headers, json=testcase_test)
            json_data = rv.get_json()
            assert 'Updated' not in json_data['msg']

    def test_create_testcase_variant(self):
        pipeline = [{"$sample": {"size": 1}}]
        testcases = TestCase.objects().aggregate(pipeline)

        for testcases1 in testcases:
            testcase_id = str(testcases1['_id'])
            job_id = str(testcases1['job_id'])

        testcase_variant_test = {
            "job_id": job_id,
            "testcase_id": testcase_id
        }
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.put('/api/testcase_variant', headers=headers, json=testcase_variant_test)
            assert rv.status_code == 201
