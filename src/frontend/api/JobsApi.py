import base64
import json
import datetime
import flask
from flask import jsonify
from flask_security import auth_token_required
from mongoengine import DoesNotExist

from src.database.models.FuzzTarget import FuzzTarget
from src.database.models.Job import Job
from src.database.models.Crash import Crash
from src.database.models.TestCase import TestCase
from src.frontend.api.utils import validate_body, fix_json

jobs_api = flask.Blueprint('job_api', __name__)


def _api_get_job_information(job):
    fuzzTarget_info = FuzzTarget.objects.get(id=job.fuzzing_target.id)
    return {'name': job.name,
            'job_id': str(job.id),
            'description': job.description,
            'archived': job.archived,
            'enabled': job.enabled,
            'platform': job.platform,
            'fuzzTarget': {
                'fuzzer_engine': fuzzTarget_info.fuzzer_engine,
                'binary_flag': fuzzTarget_info.binary_flag
            }
            }


@jobs_api.route('/api/jobs', methods=['GET'])
@jobs_api.route('/api/job/<job_id>', methods=['GET'])
@auth_token_required
def api_get_job(job_id=None):
    if job_id is None:
        res = Job.objects
        fixed_json = [fix_json(job.to_json()) for job in res]
        response = jsonify(fixed_json)
        response.status_code = 200
        return response
    else:
        job = Job.objects.get(id=job_id)
        fixed_json = fix_json(job.to_json())
        response = jsonify(fixed_json)
        response.status_code = 200
        return response


@jobs_api.route('/api/job/<job_id>', methods=['DELETE'])
@auth_token_required
def api_delete_job(job_id=None):
    if job_id is None:
        response = jsonify({'success': False, 'msg': 'no job ID provided'})
        response.status_code = 404  # or 400 or whatever
        return response
    else:
        try:
            job = Job.objects.get(id=job_id)
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'job ID not found'})
            response.status_code = 404  # or 400 or whatever
            return response
        if job:
            job.delete()
            testcases = TestCase.objects(job_id=job_id)
            for testcase in testcases:
                crashes = Crash.objects(testcase=testcase.id)
                crashes.delete()
            fuzzTarget = FuzzTarget.objects.get(id=job.fuzzing_target.id)
            fuzzTarget.delete()
            response = jsonify({'success': True})
            response.status_code = 200
            return response
        else:
            response = jsonify({'success': False})
            response.status_code = 500
            return response


@jobs_api.route('/api/job', methods=['PUT'])
@auth_token_required
def api_create_job():
    # TODO check if a job with this name does already exist
    data = flask.request.get_json()
    if data:
        validation_list = ("name", "description", "platform")
        validation = validate_body(data, validation_list)
        if not validation[0]:
            response = jsonify(validation[1])
            response.status_code = 500
            return response
        else:
            new_job = Job(name=data.get('name'),
                          description=data.get('description'),
                          archived=False,
                          enabled=True,
                          date=datetime.datetime.now().strftime('%Y-%m-%d'),
                          owner=data.get("owner"),
                          environment_string=data.get('environment_string'),
                          template=data.get('template'),
                          platform=data.get('platform'))
            new_job.save()

            response = jsonify({'success': True})
            response.status_code = 200  # or 400 or whatever
            return response
    else:
        return jsonify({'success': False, 'msg': 'no json document provided'})
