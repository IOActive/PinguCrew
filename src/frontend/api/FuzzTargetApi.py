import base64
import json

import flask
from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist

from database.models.Fuzzer import Fuzzer
from src.database.models.FuzzTarget import FuzzTarget
from src.frontend.api.utils import fix_json, validate_body

fuzztargets_api = flask.Blueprint('fuzztargets_api', __name__)


@fuzztargets_api.route('/api/fuzztargets', methods=['GET'])
@auth_token_required
def get_fuzzTargets():
    res = FuzzTarget.objects
    if res:
        fixed_json = []
        for fuzzTarget in res:
            fuzzTargetJson = json.loads(fuzzTarget.to_json())
            #filedata = fuzzTarget.fuzzing_target.read()
            #fuzzTargetJson['fuzzTarget'] = base64.b64encode(filedata).decode()
            fixed_json.append(fix_json(json.dumps(fuzzTargetJson)))

        response = jsonify(fixed_json)
        response.status_code = 200
        return response
    else:
        response = jsonify({'success': False, 'msg': 'Not Fuzz Targets found'})
        response.status_code = 404  # or 400 or whatever
        return response


@fuzztargets_api.route('/api/fuzztarget', methods=['GET'])
@auth_token_required
def get_fuzzTarget():
    data = request.args
    if ('fuzzer_engine' not in data or 'binary' not in data) and 'id' not in data:
        response = jsonify({'success': False, 'msg': 'no Fuzz Target Engine or Binary Name provided'})
        response.status_code = 400  # or 400 or whatever
        return response
    else:
        if 'fuzzer_engine' in data and 'binary' in data:
            try:
                fuzzer = Fuzzer.objects.get(name=data.get('fuzzer_engine'))
                fuzzTarget = FuzzTarget.objects.get(fuzzer_engine=fuzzer.id, binary=data.get('binary'))
                fuzzTargetJson = json.loads(fuzzTarget.to_json())
                #filedata = fuzzTarget.fuzzing_target.read()
                #fuzzTargetJson['fuzzing_target'] = base64.b64encode(filedata).decode()
                fixed_json = fix_json(json.dumps(fuzzTargetJson))
                response = jsonify(fixed_json)
                return response
            except DoesNotExist:
                response = jsonify({'success': False, 'msg': 'Fuzz Target not found'})
                response.status_code = 404  # or 400 or whatever
                return response
        elif 'id' in data:
            try:
                fuzzTarget = FuzzTarget.objects.get(id=data.get('id'))
                fuzzTargetJson = json.loads(fuzzTarget.to_json())
                #filedata = fuzzTarget.fuzzing_target.read()
                #fuzzTargetJson['fuzzing_target'] = base64.b64encode(filedata).decode()
                fixed_json = fix_json(json.dumps(fuzzTargetJson))
                response = jsonify(fixed_json)
                return response
            except DoesNotExist:
                response = jsonify({'success': False, 'msg': 'Fuzz Target not found'})
                response.status_code = 404  # or 400 or whatever
                return response



@fuzztargets_api.route('/api/fuzztarget', methods=['PUT'])
@auth_token_required
def add_FuzzTarget():
    body = flask.request.get_json()
    validation_list = ("fuzzer_engine", 'binary', 'project')
    validation = validate_body(body, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 400
        return response
    else:
        #fuzzTargetFile = base64.b64decode(body.get("fuzzing_target"))
        fuzzer = Fuzzer.objects.get(name=body.get('fuzzer_engine'))
        fuzzTarget = FuzzTarget(
            fuzzer_engine=fuzzer.id,
            project=body.get("project"),
            binary=body.get("binary")
        )
        #fuzzTarget.fuzzing_target.put(fuzzTargetFile)
        fuzzTarget.save()
        response = jsonify({'success': True})
        response.status_code = 201  # or 400 or whatever
        return response


@fuzztargets_api.route('/api/fuzztarget/<fuzzTargetId>', methods=['DELETE'])
@auth_token_required
def remove_fuzzTarget(fuzzTargetId=None):
    if fuzzTargetId is None:
        response = jsonify({'success': False, 'msg': 'no Fuzz Target ID provided'})
        response.status_code = 500  # or 400 or whatever
        return response
    else:
        try:
            fuzzTarget = FuzzTarget.objects.get(id=fuzzTargetId)
            fuzzTarget.delete()
            response = jsonify({'success': True})
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzz Target not found'})
            response.status_code = 404  # or 400 or whatever
            return response
