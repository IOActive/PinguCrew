from datetime import datetime

import flask
from flask import jsonify
from flask_security import auth_token_required
from mongoengine import DoesNotExist
from flasgger import Swagger
from src.database.models.Bot import Bot, TaskStatus
from src.frontend.api.utils import validate_body, fix_json

bots_api = flask.Blueprint('bot_api', __name__)


@bots_api.route('/api/bot/heartbeat', methods=['POST'])
@auth_token_required
def heartbeat():
    body = flask.request.get_json()
    validation_list = ("bot_name", "task_status", "last_beat_time")
    validation = validate_body(body, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 400
        return response
    else:
        bot_name = body.get("bot_name")
        last_beat_time = body.get("last_beat_time")

        try:
            bot = Bot.objects.get(bot_name=bot_name)
            bot_update = {
                "task_status": body.get("task_status"),
                'last_beat_time': last_beat_time
            }
            bot.update(**bot_update)
            response = jsonify({'success': True})
            response.status_code = 201  # or 400 or whatever
            return response

        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Bot not registered'})
            response.status_code = 404
            return response


@bots_api.route('/api/bot/register', methods=['PUT'])
@auth_token_required
def register():
    body = flask.request.get_json()
    validation_list = ("bot_name", "task_payload", "platform")
    validation = validate_body(body, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 400
        return response
    else:
        try:
            Bot.objects.get(bot_name=body.get("bot_name"))
            response = jsonify({'success': False, 'msg': 'Bot already Registered'})
            response.status_code = 409  # or 400 or whatever
            return response
        except DoesNotExist:
            bot = Bot(
                bot_name=body.get("bot_name"),
                task_status=TaskStatus.NA,
                task_payload=body.get("task_payload"),
                task_end_time=body.get("task_end_time"),
                last_beat_time=datetime.now().strftime('%Y-%m-%d'),
                platform=body.get("platform")
            )
            bot.save()
            response = jsonify({'success': True})
            response.status_code = 200  # or 400 or whatever
            return response


@bots_api.route('/api/bot/<bot_name>', methods=['GET'])
@auth_token_required
def get_bot(bot_name=None):
    if bot_name is None:
        response = jsonify({'success': False, 'msg': 'bot name not provided'})
        response.status_code = 400
        return response
    else:
        try:
            bot = Bot.objects.get(bot_name=bot_name)
            fixed_json = fix_json(bot.to_json())
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'bot has not been registered yet'})
            response.status_code = 404  # or 400 or whatever
            return response
