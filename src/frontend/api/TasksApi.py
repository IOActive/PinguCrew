import json

import flask
from flask import jsonify, request
from flask_security import auth_token_required

from src.database.models.Job import Job
from src.frontend.utils.workQueue import get_queue_element, queue_exists, create_queue, publish
from flask import current_app

tasks_api = flask.Blueprint('task_api', __name__)


@tasks_api.route('/api/task', methods=['GET'])
@auth_token_required
def get_task(platform=None):
    data = request.args
    if 'platform' in data:
        platform = data['platform']

    if platform is None:
        response = jsonify({'success': False, 'msg': 'platform and fuzzer must be specified'})
        response.status_code = 400
        return response
    else:
        queue = 'tasks-%s' % platform
        if queue_exists(queue):
            empty, task = get_queue_element(queue)
            if not empty:
                response = jsonify(task)
                response.status_code = 200
                return response
            else:
                response = jsonify({'success': False, 'msg': 'empty queue'})
                response.status_code = 404
                return response
        else:
            response = jsonify({'success': False, 'msg': 'queue does not exist'})
            response.status_code = 404
            return response


@tasks_api.route('/api/task', methods=['PUT'])
@auth_token_required
def add_task():
    body = flask.request.get_json()
    command = body.get('command')
    argument = body.get('argument')
    platform = body.get('platform')
    job_id = body.get('job_id')

    if job_id is None:
        response = jsonify({'success': False, 'msg': 'Job ID not specified'})
        response.status_code = 400
        return response

    job = Job.objects.get(id=job_id)

    if (command is None) or (argument is None):
        response = jsonify({'success': False, 'msg': 'missing command or argument parameters'})
        response.status_code = 400
        return response

    if job.platform != platform:
        response = jsonify({'success': False, 'msg': 'Tasks platform does not math the Job platform'})
        response.status_code = 406
        return response

    queue = 'tasks-%s' % job.platform
    if not queue_exists(queue):
        create_queue(current_app.config['queue_host'], queue)

    task = {'job_id': str(job.id),
            'platform': platform,
            'command': command,
            'argument': argument,
            }
    publish(current_app.config['queue_host'], queue, json.dumps(task))
    response = jsonify({'success': True, 'msg': 'Tasks Published'})
    response.status_code = 200
    return response
