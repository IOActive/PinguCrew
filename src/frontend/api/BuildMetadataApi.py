import datetime

import flask
from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist

from src.database.models.BuildMetadata import BuildMetadata
from src.database.models.Job import Job
from src.frontend.api.utils import validate_body, fix_json

BuildMetadata_api = flask.Blueprint('BuildMetadata_api', __name__)


@BuildMetadata_api.route('/api/buildMetada', methods=['PUT'])
@auth_token_required
def add_BuildMetadata():
    body = flask.request.get_json()
    validation_list = ("revision", "job", "bad_build", "console_output", "bot_name", "symbols")
    validation = validate_body(body, validation_list)
    if not validation[0]:
        response = jsonify(validation[1])
        response.status_code = 500
        return response
    else:
        try:
            job = Job.objects.get(id=body.get("job"))
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'job id not found'})
            response.status_code = 404
            return response

        buildMetada = BuildMetadata(
            job=job.id,
            revision=body.get("revision"),
            bad_build=body.get("bad_build"),
            console_output=body.get("console_output"),
            bot_name=body.get("bot_name"),
            symbols=body.get("symbols"),
            timestamp=datetime.datetime.now().strftime('%Y-%m-%d')
        )
        buildMetada.save()
        response = jsonify({'success': True})
        response.status_code = 200  # or 400 or whatever
        return response


@BuildMetadata_api.route('/api/buildMetada', methods=['GET'])
@auth_token_required
def get_BuildMetadata():
    data = request.args
    if 'job_id' in data and 'revision' not in data:
        job_id = data['job_id']
        try:
            buildMetadatas = BuildMetadata.objects(job=job_id)
            fixed_json = [fix_json(buildMetadata.to_json()) for buildMetadata in buildMetadatas]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'buildMetadata for job %s not found' % job_id})
            response.status_code = 404  # or 400 or whatever
    elif 'job_id' in data and 'revision' in data:
        job_id = data['job_id']
        revision = data['revision']
        try:
            buildMetadatas = BuildMetadata.objects(job=job_id, revision=revision)
            fixed_json = [fix_json(buildMetadata.to_json()) for buildMetadata in buildMetadatas]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'buildMetadata for job %s not found' % job_id})
            response.status_code = 404  # or 400 or whatever
    else:
        response = jsonify({'success': False, 'msg': 'job id or revision not provided'})
        response.status_code = 400
        return response
