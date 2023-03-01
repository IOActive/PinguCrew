import flask

from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist, InvalidQueryError

from database.models.TestCaseVariant import TestCaseVariant
from src.database.models.Job import Job
from src.database.models.TestCase import TestCase
from src.frontend.api.utils import validate_body, fix_json

testcase_variants_api = flask.Blueprint('testcase_variants_api', __name__)


@testcase_variants_api.route('/api/testcase_variant', methods=['GET'])
@auth_token_required
def api_get_testcase():
    data = request.args
    if 'job_id' not in data or 'testcase_id' not in data:
        response = jsonify({'success': False, 'msg': 'Job ID and Testcase ID provided'})
        response.status_code = 400  # or 400 or whatever
        return response
    try:
        testcase_id = data['testcase_id']
        job_id = data['job_id']
        testcase_variant = TestCaseVariant.objects.get(testcase_id=testcase_id, job_id=job_id)
        fixed_json = fix_json(testcase_variant.to_json())
        response = jsonify(fixed_json)
        response.status_code = 200
        return response
    except DoesNotExist:
        response = jsonify({'success': False, 'msg': 'Testcase not found'})
        response.status_code = 404
        return response


@testcase_variants_api.route('/api/testcase_variant/<testcase_variant_id>', methods=['POST'])
@auth_token_required
def update_testcase_variant(testcase_variant_id=None):
    if testcase_variant_id is None:
        response = jsonify({'success': False, 'msg': 'testcase variant not found'})
        response.status_code = 400
        return response
    else:
        data = flask.request.get_json()
        try:
            if data:
                testcase_variant = TestCaseVariant.objects.get(id=testcase_variant_id)
                if 'job_id' in data:
                    data.pop('job_id')
                if 'testcase_id' in data:
                    data.pop("testcase_id")
                testcase_variant.update(**data)
                response = jsonify({'success': True, 'msg': "Updated"})
                response.status_code = 200  # or 400 or whatever
                return response
            else:
                return jsonify({'success': False, 'msg': 'no json document provided'})
        except InvalidQueryError as e:
            response = jsonify({'success': False, 'msg': str(e)})
            response.status_code = 404
            return response


@testcase_variants_api.route('/api/testcase_variant', methods=['PUT'])
@auth_token_required
def create_testcase_variant():
    data = flask.request.get_json()
    validation_list = ("job_id", "testcase_id")
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
            testcase_id = data['testcase_id']
            testcase = TestCase.objects.get(id=testcase_id)
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'TestCase id not found'})
            response.status_code = 404
            return response
        new_testcasevariant = TestCaseVariant(
            job_id=job.id,
            testcase_id=testcase.id
        )
        new_testcasevariant.save()
        response = jsonify({'success': True, 'id': str(new_testcasevariant.id)})
        response.status_code = 201
        return response
