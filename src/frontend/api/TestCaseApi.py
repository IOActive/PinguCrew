import base64
from datetime import datetime

import flask
from bson import ObjectId
from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist, InvalidQueryError

from database.models.Crash import Crash
from database.models.Fuzzer import Fuzzer
from src.database.models.Job import Job
from src.database.models.TestCase import TestCase
from src.frontend.api.utils import validate_body, fix_json

testcases_api = flask.Blueprint('testcase_api', __name__)


@testcases_api.route('/api/testcase/<testcase_id>', methods=['GET'])
@auth_token_required
def api_get_testcase(testcase_id=None):
    try:
        testcase = TestCase.objects.get(id=testcase_id)
        fixed_json = fix_json(testcase.to_json())
        response = jsonify(fixed_json)
        response.status_code = 200
        return response
    except DoesNotExist:
        response = jsonify({'success': False, 'msg': 'Testcase not found'})
        response.status_code = 404
        return response


@testcases_api.route('/api/<job_id>/testcases', methods=['GET'])
@auth_token_required
def api_get_testcases(job_id=None):
    if job_id is None:
        response = jsonify({'success': False, 'msg': 'job name not provided'})
        response.status_code = 400
        return response

    job = Job.objects.get(id=job_id)
    if job:
        try:
            testcases = TestCase.objects(job_id=job.id)
            fixed_json = [fix_json(testcase.to_json()) for testcase in testcases]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'This job has not testcases'})
            response.status_code = 404  # or 400 or whatever
            return response

    else:
        response = jsonify({'success': False, 'msg': 'job not found'})
        response.status_code = 404
        return response


@testcases_api.route('/api/testcase', methods=['GET'])
@auth_token_required
def api_find_testcase():
    data = request.args
    validation_list = ("project_name", "crash_type", "crash_state", "security_flag")
    validation = validate_body(data, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 400
        return response
    else:
        try:
            job = Job.objects.get(name=data.get("project_name"))
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'job not found'})
            response.status_code = 404
            return response
        if job:
            try:
                security_flag = bool(data.get("security_flag"))
                crashes = Crash.objects(crash_type=data.get("crash_type"), crash_state=data.get("crash_state"),
                                          security_flag=security_flag)
            except DoesNotExist:
                response = jsonify({'success': False, 'msg': 'crash not found'})
                response.status_code = 404
                return response
            if crashes:
                try:
                    fixed_json = []
                    for crash in crashes:
                        testcase = TestCase.objects.get(job_id=job.id, id=crash.testcase_id.id)
                        if testcase not in fixed_json:
                            fixed_json.append(fix_json(testcase.to_json()))
                    response = jsonify(fixed_json[0])
                    response.status_code = 200
                    return response
                except DoesNotExist:
                    response = jsonify({'success': False, 'msg': 'Testcase not found'})
                    response.status_code = 404
                    return response
            else:
                response = jsonify({'success': False, 'msg': 'Testcase not found'})
                response.status_code = 404
                return response


@testcases_api.route('/api/testcase/<testcase_id>', methods=['POST'])
@auth_token_required
def update_testcase(testcase_id=None):
    if testcase_id is None:
        response = jsonify({'success': False, 'msg': 'testcase not found'})
        response.status_code = 400
        return response
    else:
        data = flask.request.get_json()
        try:
            if data:
                testcase = TestCase.objects.get(id=testcase_id)
                data.pop('job_id')
                data.pop("test_case")
                data.pop("fuzzer_id")
                testcase.update(**data)
                response = jsonify({'success': True, 'msg': "Updated"})
                response.status_code = 200  # or 400 or whatever
                return response
            else:
                return jsonify({'success': False, 'msg': 'no json document provided'})
        except InvalidQueryError as e:
            response = jsonify({'success': False, 'msg': str(e)})
            response.status_code = 404
            return response


@testcases_api.route('/api/testcase', methods=['PUT'])
@auth_token_required
def create_testcase():
    data = flask.request.get_json()
    validation_list = ("job_id", "test_case", "fuzzer_id")
    validation = validate_body(data, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 400
        return response
    else:
        try:
            job_id = data['job_id']
            job = Job.objects.get(id=job_id)
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'job id not found'})
            response.status_code = 404
            return response
        try:
            fuzzer_id = data['fuzzer_id']
            fuzzer = Fuzzer.objects.get(id=fuzzer_id)
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzzer id not found'})
            response.status_code = 404
            return response
        validation_list = ("absolute_path", "queue")
        validation = validate_body(data, validation_list)
        if not validation[0]:
            response = jsonify(validation[1])
            response.status_code = 400
            return response
        else:
            testCaseFile = base64.b64decode(data.get("test_case"))
            new_testcase = TestCase(**data)
            new_testcase.test_case = testCaseFile
            new_testcase.fuzzer_id = fuzzer.id
            new_testcase.job_id = job.id
            new_testcase.timestamp = datetime.now().strftime('%Y-%m-%d')
            new_testcase.save()
            response = jsonify({'success': True, 'id': str(new_testcase.id)})
            response.status_code = 200
            return response
