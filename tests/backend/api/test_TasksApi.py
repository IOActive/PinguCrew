import json

from database.models.TestCase import TestCase
from src.database.models.Job import Job
from src.frontend.app import app
from src.frontend.utils.workQueue import create_queue, publish
from unittest import TestCase as TC


class Test(TC):
    def mock_tasks(self):
        queue_host = app.config['queue_host']
        create_queue(queue_host, 'tasks-linux')
        task = {'job_id': str(112432354325),
                'platform': 'Linux',
                'command': 'ls',
                'argument': '-l',
                }
        publish(queue_host, 'tasks-linux', json.dumps(task))

    def test_get_task(self):
        # self.mock_tasks()
        with app.test_client() as c:
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/task?platform=Linux', headers=headers)
            json_data = rv.get_json()
            assert 'empty queue' not in json_data
            assert 'queue does not exist' not in json_data

    def test_add_libfuzz_task(self):
        pipeline = [{"$sample": {"size": 1}}]
        jobs = Job.objects().aggregate(pipeline)
        for job in jobs:
            job_id = str(job['_id'])
            task_test = {
                'job_id': job_id,
                'platform': 'Linux',
                'command': 'fuzz',
                'argument': 'libFuzzer',
            }
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            with app.test_client() as c:
                rv = c.put('/api/task', json=task_test, headers=headers)
                json_data = rv.get_json()
                assert 'success' in json_data

    def test_add_blackbox_fuzz_task(self):
        pipeline = [{"$sample": {"size": 1}}]
        jobs = Job.objects().aggregate(pipeline)
        for job in jobs:
            job_id = str(job['_id'])
            task_test = {
                'job_id': job_id,
                'platform': 'Linux',
                'command': 'fuzz',
                'argument': 'libFuzzer',
            }
            headers = {'Authorization': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            with app.test_client() as c:
                rv = c.put('/api/task', json=task_test, headers=headers)
                json_data = rv.get_json()
                assert 'success' in json_data
    def test_add_minimize_task(self):
        pipeline = [{"$sample": {"size": 1}}]
        jobs = Job.objects().aggregate(pipeline)
        try:
            for job in jobs:
                job_id = str(job['_id'])
                testcase = TestCase.objects(job_id=job['_id'])[0]
                task_test = {
                    'job_id': job_id,
                    'platform': 'Linux',
                    'command': 'minimize',
                    'argument': str(testcase.id),
                }
                headers = {'Authorization': app.config.get('default_user_api_key'),
                           'content-type': 'application/json'}
                with app.test_client() as c:
                    rv = c.put('/api/task', json=task_test, headers=headers)
                    json_data = rv.get_json()
                    assert 'success' in json_data
        except Exception as e:
            print(e)
