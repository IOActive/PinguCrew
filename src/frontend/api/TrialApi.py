import flask

from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist, InvalidQueryError

from database.models.TestCaseVariant import TestCaseVariant
from database.models.Trial import Trial
from src.database.models.Job import Job
from src.database.models.TestCase import TestCase
from src.frontend.api.utils import validate_body, fix_json

trial_api = flask.Blueprint('trial_api', __name__)


@trial_api.route('/api/trial', methods=['GET'])
@auth_token_required
def api_get_testcase():
    data = request.args
    if 'id' not in data and 'app_name' not in data:
        response = jsonify({'success': False, 'msg': 'Trial ID or App_name  provided'})
        response.status_code = 400  # or 400 or whatever
        return response
    try:
        if 'id' in data:
            trial_id = data['id']
            trial = TestCaseVariant.objects.get(id=trial_id)
            fixed_json = [fix_json(trial.to_json())]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        elif 'app_name' in data:
            app_name = data['app_name']
            trials = TestCaseVariant.objects.get(app_name=app_name)
            fixed_json = [fix_json(trial.to_json()) for trial in trials]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
    except DoesNotExist:
        response = jsonify({'success': False, 'msg': 'Testcase not found'})
        response.status_code = 404
        return response


@trial_api.route('/api/trial/<trial_id>', methods=['POST'])
@auth_token_required
def update_testcase_variant(trial_id=None):
    if trial_id is None:
        response = jsonify({'success': False, 'msg': 'testcase variant not found'})
        response.status_code = 400
        return response
    else:
        data = flask.request.get_json()
        try:
            if data:
                trial = Trial.objects.get(id=trial_id)
                trial.update(**data)
                response = jsonify({'success': True, 'msg': "Updated"})
                response.status_code = 200  # or 400 or whatever
                return response
            else:
                return jsonify({'success': False, 'msg': 'no json document provided'})
        except InvalidQueryError as e:
            response = jsonify({'success': False, 'msg': str(e)})
            response.status_code = 404
            return response


@trial_api.route('/api/trial', methods=['PUT'])
@auth_token_required
def create_testcase_variant():
    data = flask.request.get_json()
    validation_list = ["app_name"]
    validation = validate_body(data, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 400
        return response
    else:
        new_trial = Trial(
            app_name=data['app_name'],
            probability=data["probability"] if "probability" in data else None,
            app_args=data["app_args"] if "app_args" in data else None
        )
        new_trial.save()
        response = jsonify({'success': True, 'id': str(new_trial.id)})
        response.status_code = 201
        return response
