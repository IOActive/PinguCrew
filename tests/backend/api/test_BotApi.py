from datetime import datetime
from unittest import TestCase
from src.frontend.app import app


class Test(TestCase):
    def test_get_bot(self):
        with app.test_client() as c:
            headers = {'Authorization:': app.config.get('default_user_api_key'),
                       'content-type': 'application/json'}
            rv = c.get('/api/bot/test_bot', headers=headers)
            json_data = rv.get_json()
            assert 'bot has not been registered yet' not in json_data

    def test_register(self):
        bot = {'bot_name': "test_bot",
               'current_time': datetime.now().strftime('%Y-%m-%d'),
               'task_payload': "task_payload",
               'task_end_time': "2022-05-21",
               'last_beat_time': datetime.now().strftime('%Y-%m-%d'),
               'platform': "Linux"}

        headers = {'Authorization': app.config.get('default_user_api_key'),
                   'content-type': 'application/json'}
        with app.test_client() as c:
            rv = c.put('/api/bot/register', json=bot, headers=headers)
            json_data = rv.get_json()
            assert 'success' in json_data

    def test_heartbeat(self):
        heartbeat = {
            'bot_name': 'test_bot',
            'last_beat_time': datetime.now().strftime('%Y-%m-%d'),
            'task_status': 'started'
        }
        headers = {'Authorization': app.config.get('default_user_api_key'),
                   'content-type': 'application/json'}
        with app.test_client() as c:
            rv = c.post('/api/bot/heartbeat', json=heartbeat, headers=headers)
            json_data = rv.get_json()
            assert 'success' in json_data
