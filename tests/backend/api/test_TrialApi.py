from unittest import TestCase as TC

from database.models.Trial import Trial
from src.frontend.app import app


class Test(TC):
    def test_api_get_trial(self):
        pipeline = [{"$sample": {"size": 1}}]

        trials = Trial.objects().aggregate(pipeline)

        for trial in trials:
            trial_id = str(trial['_id'])

        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get(f'/api/trial?id={trial_id}', headers=headers)
            json_data = rv.get_json()
            assert len(json_data) > 0

    def test_update_testcase_variant(self):
        pipeline = [{"$sample": {"size": 1}}]
        trials = Trial.objects().aggregate(pipeline)
        for trial in trials:
            trial_id = str(trial['_id'])

        trial_test = {
            "app_name": "test_app",
            "probability": 1.0,
            "app_args": "-g"
        }
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.post(f'/api/trial/{trial_id}', headers=headers, json=trial_test)
            json_data = rv.get_json()
            assert 'Updated' in json_data['msg']

    def test_create_testcase_variant(self):
        trial_test = {
            "app_name": "test_app",
            "probability": 1.0,
            #"app_args": "-f"
        }
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.put('/api/trial', headers=headers, json=trial_test)
            assert rv.status_code == 201
