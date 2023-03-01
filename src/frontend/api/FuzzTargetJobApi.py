import flask
from flask import jsonify, request
from flask_security import auth_token_required
from mongoengine import DoesNotExist

from database.models.Fuzzer import Fuzzer
from src.database.models.FuzzTarget import FuzzTarget
from src.database.models.FuzzTargetJob import FuzzTargetJob
from src.database.models.Job import Job
from src.frontend.api.utils import fix_json, validate_body

fuzzTargetJobs_api = flask.Blueprint('fuzzTargetJobs_api', __name__)


@fuzzTargetJobs_api.route('/api/fuzzTargetJobs', methods=['GET'])
@auth_token_required
def get_fuzzTargetJobs():
    res = FuzzTargetJob.objects
    if res:
        fixed_json = [fix_json(fuzzTargetJob.to_json()) for fuzzTargetJob in res]
        response = jsonify(fixed_json)
        response.status_code = 200
        return response
    else:
        response = jsonify({'success': False, 'msg': 'Not Fuzz Targets found'})
        response.status_code = 404  # or 400 or whatever
        return response


@fuzzTargetJobs_api.route('/api/fuzzTargetJob', methods=['GET'])
@auth_token_required
def get_fuzzTargetJob():
    data = request.args
    if 'engine' in data:
        engine = data['engine']
        try:
            fuzzer = Fuzzer.objects.get(name=engine)
            fuzzTargetJobs = FuzzTargetJob.objects(engine=fuzzer.id)
            fixed_json = [fix_json(fuzzTargetJob.to_json()) for fuzzTargetJob in fuzzTargetJobs]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzz Target job not found'})
            response.status_code = 404  # or 400 or whatever
            return response
    elif 'job_id' in data and 'fuzzing_target_id' in data:
        job_id = data['job_id']
        fuzzing_target = data['fuzzing_target_id']
        try:
            fuzzTargetJobs = FuzzTargetJob.objects(job=job_id, fuzzing_target=fuzzing_target)
            fixed_json = [fix_json(fuzzTargetJob.to_json()) for fuzzTargetJob in fuzzTargetJobs]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzz Target job not found'})
            response.status_code = 404  # or 400 or whatever
            return response
    elif 'job_id' in data:
        job_id = data['job_id']
        try:
            fuzzTargetJobs = FuzzTargetJob.objects(job=job_id)
            fixed_json = [fix_json(fuzzTargetJob.to_json()) for fuzzTargetJob in fuzzTargetJobs]
            response = jsonify(fixed_json)
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzz Target job not found'})
            response.status_code = 404  # or 400 or whatever
            return response
    else:
        response = jsonify({'success': False, 'msg': 'job id or engine not provided'})
        response.status_code = 400
        return response


@fuzzTargetJobs_api.route('/api/fuzzTargetJob', methods=['PUT'])
@auth_token_required
def add_fuzzTargetJob():
    body = flask.request.get_json()
    validation_list = ("fuzzing_target", "job", "engine", "weight", "last_run")
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
        try:
            fuzzing_target = FuzzTarget.objects.get(id=body.get("fuzzing_target"))
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'FuzzTarget id not found'})
            response.status_code = 404
            return response

        try:
            fuzzer = Fuzzer.objects.get(name=body.get("engine"))
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzzer not found'})
            response.status_code = 404
            return response

        fuzzTargetJob = FuzzTargetJob(
            job=job.id,
            fuzzing_target=fuzzing_target.id,
            engine=fuzzer.id,
            weight=body.get("weight"),
            last_run=body.get("last_run")
        )
        fuzzTargetJob.save()
        response = jsonify({'success': True})
        response.status_code = 200  # or 400 or whatever
        return response


@fuzzTargetJobs_api.route('/api/fuzzTargetJob/<fuzzTargetjobId>', methods=['DELETE'])
@auth_token_required
def remove_fuzzTarget(fuzzTargetJobId=None):
    if fuzzTargetJobId is None:
        response = jsonify({'success': False, 'msg': 'no Fuzz Target Job ID provided'})
        response.status_code = 500  # or 400 or whatever
        return response
    else:
        try:
            fuzzTargetJob = FuzzTargetJob.objects.get(id=fuzzTargetJobId)
            fuzzTargetJob.delete()
            response = jsonify({'success': True})
            response.status_code = 200
            return response
        except DoesNotExist:
            response = jsonify({'success': False, 'msg': 'Fuzz Target Job not found'})
            response.status_code = 404  # or 400 or whatever
            return response
