import base64
import datetime

import flask
from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist, ValidationError

from database.models.Crash import Crash
from frontend.api.utils import validate_body, fix_json

crash_api = flask.Blueprint('crash_api', __name__)


@crash_api.route('/api/crash', methods=['PUT'])
@auth_token_required
def add_crash():
    body = flask.request.get_json()
    validation_list = (
        "crash_signal", "exploitability", "crash_hash", "verified", "additional", "iteration", "crash_type",
        "crash_address", "crash_state", "crash_stacktrace", "regression",
        "security_severity", "absolute_path", "security_flag", "reproducible_flag", "return_code", "gestures",
        "resource_list", "fuzzing_strategy", "should_be_ignored",
        "application_command_line", "unsymbolized_crash_stacktrace", "crash_frame", "crash_info", "testcase_id")
    validation = validate_body(body, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 400
        return response
    else:
        try:
            unsymbolized_crash_stacktrace = base64.b64decode(body.get("unsymbolized_crash_stacktrace"))
            #crash_frame = base64.b64decode(body.get("crash_frame"))
            crash_stacktrace = base64.b64decode(body.get("crash_stacktrace"))
            crash = Crash(
                crash_signal=body.get("crash_signal"),
                exploitability=body.get("exploitability"),
                crash_time=datetime.datetime.now().strftime('%Y-%m-%d'),
                crash_hash=body.get("crash_hash"),
                verified=body.get("verified"),
                additional=body.get("additional"),
                iteration=body.get("iteration"),
                crash_type=body.get("crash_type"),
                crash_address=body.get("crash_address"),
                crash_state=body.get("crash_state"),
                crash_stacktrace=crash_stacktrace,
                regression=body.get("regression"),
                security_severity=body.get("security_severity"),
                absolute_path=body.get("absolute_path"),
                security_flag=body.get("security_flag"),
                reproducible_flag=body.get("reproducible_flag"),
                return_code=body.get("return_code"),
                gestures=body.get("gestures"),
                resource_list=body.get("resource_list"),
                fuzzing_strategy=body.get("fuzzing_strategy"),
                should_be_ignored=body.get("should_be_ignored"),
                application_command_line=body.get("application_command_line"),
                unsymbolized_crash_stacktrace=unsymbolized_crash_stacktrace,
                crash_frame=body.get("crash_frame"),
                crash_info=body.get("crash_info"),
                testcase_id=body.get("testcase_id")
            )
            crash.save()
            response = jsonify({'success': True})
            response.status_code = 200  # or 400 or whatever
            return response
        except ValidationError or Exception as e:
            response = jsonify({'success': False, 'msg': e})
            response.status_code = 400
            return response


@crash_api.route('/api/crash', methods=['GET'])
@auth_token_required
def get_crash():
    data = request.args
    if 'id' in data:
        crash_id = data['id']
        try:
            crash = Crash.objects.get(id=crash_id)
            fixed_json = fix_json(crash.to_json())
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'crash  %s not found' % crash_id})
            response.status_code = 404  # or 400 or whatever
            return response
    elif 'testcase_id' in data:
        testcase_id = data['testcase_id']
        try:
            crashes = Crash.objects(testcase_id=testcase_id)
            fixed_json = [fix_json(crash.to_json()) for crash in crashes]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'testcase %s crashes not found' % testcase_id})
            response.status_code = 404  # or 400 or whatever
            return response
    else:
        response = jsonify({'success': False, 'msg': 'testcase id not provided'})
        response.status_code = 400
        return response


@crash_api.route('/api/crash', methods=['DELETE'])
@auth_token_required
def delete_BuildMetadata():
    data = request.args
    if 'id' not in data:
        response = jsonify({'success': False, 'msg': "No Crash ID specified"})
        response.status_code = 400
        return response
    else:
        try:
            crash = Crash.objects.get(id=data['id'])
            crash.delete()
            response = jsonify({'success': True})
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Crash not found'})
            response.status_code = 404  # or 400 or whatever
            return response
