import datetime

import flask
from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist

from src.database.models.BuildMetadata import BuildMetadata
from src.database.models.DataBundle import DataBundle
from src.database.models.Job import Job
from src.frontend.api.utils import validate_body, fix_json

DataBundle_api = flask.Blueprint('DataBundle_api', __name__)


@DataBundle_api.route('/api/dataBundle', methods=['PUT'])
@auth_token_required
def add_BuildMetadata():
    body = flask.request.get_json()
    validation_list = ("name", "bucket_name")
    validation = validate_body(body, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 400
        return response
    else:
        dataBundle = DataBundle(
            name=body.get("name"),
            bucket_name=body.get('bucket_name'),
            source=body.get('source') if 'source' in body else '',
            is_local=body.get('is_local') if 'source' in body else True,
            sync_to_worker=body.get('sync_to_worker') if 'source' in body else False,
            timestamp=datetime.datetime.now().strftime('%Y-%m-%d')
        )
        dataBundle.save()
        response = jsonify({'success': True})
        response.status_code = 200  # or 400 or whatever
        return response


@DataBundle_api.route('/api/dataBundle', methods=['GET'])
@auth_token_required
def get_DataBundle():
    data = request.args
    if 'name' in data:
        dataBundle_name = data['name']
        try:
            dataBundle = DataBundle.objects.get(name=dataBundle_name)
            fixed_json = fix_json(dataBundle.to_json())
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'dataBundle  %s not found' % dataBundle_name})
            response.status_code = 404  # or 400 or whatever
            return response
    else:
        response = jsonify({'success': False, 'msg': 'DataBundle name not provided'})
        response.status_code = 400
        return response


@DataBundle_api.route('/api/dataBundle', methods=['DELETE'])
@auth_token_required
def delete_BuildMetadata():
    data = request.args
    if 'name' not in data:
        response = jsonify({'success': False, 'msg': "No Data Bundle name specified"})
        response.status_code = 400
        return response
    else:
        try:
            dataBundle = DataBundle.objects.get(name=data['name'])
            dataBundle.delete()
            response = jsonify({'success': True})
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Data Bundle not found'})
            response.status_code = 404  # or 400 or whatever
            return response

