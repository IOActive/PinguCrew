import json

import flask
from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist, NotUniqueError
from pymongo.errors import DuplicateKeyError

from src.database.models.Fuzzer import Fuzzer
from src.frontend.api.utils import validate_body, fix_json
from src.frontend.utils.workQueue import get_queue_element, queue_exists, create_queue, publish

fuzzers_api = flask.Blueprint('fuzzers_api', __name__)


@fuzzers_api.route('/api/fuzzers', methods=['GET'])
@auth_token_required
def get_fuzzers():
    res = Fuzzer.objects
    fixed_json = [fix_json(fuzzer.to_json()) for fuzzer in res]
    response = jsonify(fixed_json)
    response.status_code = 200
    return response


@fuzzers_api.route('/api/fuzzer', methods=['GET'])
@auth_token_required
def get_fuzzer():
    data = request.args
    if 'name' not in data and 'id' not in data:
        response = jsonify({'success': False, 'msg': "No fuzzer name or id specified"})
        response.status_code = 400
        return response
    else:
        try:
            if 'name' in data:
                fuzzer = Fuzzer.objects.get(name=data['name'])
            elif 'id' in data:
                fuzzer = Fuzzer.objects.get(id=data['id'])
            fixed_json = fix_json(fuzzer.to_json())
            response = jsonify(fixed_json)
            response.status_code = 200
            return response

        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzzer not found'})
            response.status_code = 404  # or 400 or whatever
            return response


@fuzzers_api.route('/api/fuzzer', methods=['PUT'])
@auth_token_required
def add_fuzzer():
    data = flask.request.get_json()
    if data:
        validation_list = ("name", "filename", "blobstore_path", "file_size", "executable_path", "supported_platforms",
                           "additional_environment_string", "untrusted_content", "stats_columns",
                           "stats_column_descriptions", "builtin", "differential")
        validation = validate_body(data, validation_list)

        if not validation[0]:
            response = jsonify(validation[1])
            response.status_code = 500
            return response
        else:
            new_fuzzer = Fuzzer(timestamp=data.get("timestamp"),
                                name=data.get("name"),
                                filename=data.get("filename"),
                                blobstore_path=data.get("blobstore_path"),
                                file_size=data.get("file_size"),
                                executable_path=data.get("executable_path"),
                                timeout=data.get("timeout"),
                                supported_platforms=data.get("supported_platforms"),
                                launcher_script=data.get("launcher_script"),
                                max_testcases=data.get("max_testcases"),
                                untrusted_content=data.get("untrusted_content"),
                                additional_environment_string=data.get("additional_environment_string"),
                                builtin=data.get("builtin"),
                                differential=data.get("differential"),
                                has_large_testcases=data.get("has_large_testcases")
                                )
            try:
                new_fuzzer.save()
                response = jsonify({'success': True})
                response.status_code = 200  # or 400 or whatever
                return response
            except DuplicateKeyError as e:
                response = jsonify({'success': False, 'msg': 'Fuzzer already created'})
                response.status_code = 404  # or 400 or whatever
                return response
            except NotUniqueError as e:
                response = jsonify({'success': False, 'msg': 'Fuzzer already created'})
                response.status_code = 404  # or 400 or whatever
                return response



@fuzzers_api.route('/api/fuzzer/<fuzzer_name>', methods=['DELETE'])
@auth_token_required
def delete_fuzzer(fuzzer_name=None):
    if fuzzer_name is None:
        response = jsonify({'success': False, 'msg': "No fuzzer name specified"})
        response.status_code = 400
        return response
    else:
        try:
            fuzzer = Fuzzer.objects.get(name=fuzzer_name)
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzzer not found'})
            response.status_code = 404  # or 400 or whatever
            return response
        if fuzzer:
            fuzzer.delete()
            response = jsonify({'success': True})
            response.status_code = 200
            return response
        else:
            response = jsonify({'success': False, 'msg': 'Fuzzer not found'})
            response.status_code = 404
            return response

