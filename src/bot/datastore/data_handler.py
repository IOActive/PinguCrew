import base64
import collections
import hashlib
import os
import re
import shlex
import time
from datetime import datetime
import json
from pipes import quote
from typing import List

import requests
import six
from pydantic import ValidationError

from bot.crash_analysis import severity_analyzer
from bot.datastore import blobs_manager
from bot.datastore.data_types import Trial
from bot.fuzzing import leak_blacklist
from bot.system import memoize, errors
from src.bot.datastore import data_types
from src.bot.datastore.data_types import Job, JobTemplate, Fuzzer, FuzzTargetJob, FuzzTarget, BuildMetadata, \
    DataBundle, Testcase, Crash, TestcaseVariant, Trial
from src.bot.metrics import logs
from src.bot.system import persistent_cache, environment, tasks, shell
from src.bot.system.tasks import Task
from src.bot.utils import dates, utils
from src.bot.config import db_config

DATA_BUNDLE_DEFAULT_BUCKET_IAM_ROLE = 'roles/storage.objectAdmin'
DEFAULT_FAIL_RETRIES = 3
DEFAULT_FAIL_WAIT = 1.5
GOMA_DIR_LINE_REGEX = re.compile(r'^\s*goma_dir\s*=')
HEARTBEAT_LAST_UPDATE_KEY = 'heartbeat_update'
INPUT_DIR = 'inputs'
MEMCACHE_TTL_IN_SECONDS = 30 * 60

NUM_TESTCASE_QUALITY_BITS = 3
MAX_TESTCASE_QUALITY = 2 ** NUM_TESTCASE_QUALITY_BITS - 1

# Value and dimension map for some crash types (timeout, ooms).
CRASH_TYPE_VALUE_REGEX_MAP = {
    'Timeout': r'.*-timeout=(\d+)',
    'Out-of-memory': r'.*-rss_limit_mb=(\d+)',
}
CRASH_TYPE_DIMENSION_MAP = {
    'Timeout': 'secs',
    'Out-of-memory': 'MB',
}

TESTCASE_REPORT_URL = 'https://{domain}/testcase?key={testcase_id}'
TESTCASE_DOWNLOAD_URL = 'https://{domain}/download?testcase_id={testcase_id}'
TESTCASE_REVISION_RANGE_URL = (
    'https://{domain}/revisions?job={job_type}&range={revision_range}')
TESTCASE_REVISION_URL = (
    'https://{domain}/revisions?job={job_type}&revision={revision}')

FILE_UNREPRODUCIBLE_TESTCASE_TEXT = (
        '************************* UNREPRODUCIBLE *************************\n'
        'Note: This crash might not be reproducible with the provided testcase. '
        'That said, for the past %d days, we\'ve been seeing this crash '
        'frequently.\n\n'
        'It may be possible to reproduce by trying the following options:\n'
        '- Run testcase multiple times for a longer duration.\n'
        '- Run fuzzing without testcase argument to hit the same crash signature.\n'
        '\nIf it still does not reproduce, try a speculative fix based on the '
        'crash stacktrace and verify if it works by looking at the crash '
        'statistics in the report. We will auto-close the bug if the crash is not '
        'seen for %d days.\n'
        '******************************************************************' %
        (data_types.FILE_CONSISTENT_UNREPRODUCIBLE_TESTCASE_DEADLINE,
         data_types.UNREPRODUCIBLE_TESTCASE_WITH_BUG_DEADLINE))

FuzzerDisplay = collections.namedtuple(
    'FuzzerDisplay', ['engine', 'target', 'name', 'fully_qualified_name'])


def bot_run_timed_out():
    """Return true if our run timed out."""
    run_timeout = environment.get_value('RUN_TIMEOUT')
    if not run_timeout:
        return False

    start_time = float(environment.get_value('START_TIME'))
    if not start_time:
        return False

    run_timeout = float(run_timeout)
    start_time = datetime.utcfromtimestamp(start_time)

    # Actual run timeout takes off the duration for one task.
    average_task_duration = environment.get_value('AVERAGE_TASK_DURATION', 0)
    actual_run_timeout = run_timeout - average_task_duration

    return dates.time_has_expired(start_time, seconds=actual_run_timeout)


# ------------------------------------------------------------------------------
# Backend API  Functions
# ------------------------------------------------------------------------------

def api_headers():
    api_host = os.environ.get('API_HOST')
    headers = {'Authorization': os.environ.get('API_KEY'),
               'content-type': 'application/json'}
    return api_host, headers


# ------------------------------------------------------------------------------
# Bot API  Functions
# ---
def register_bot():
    api_host, headers = api_headers()
    payload = {'bot_name': environment.get_value('BOT_NAME'),
               'current_time': datetime.now().strftime('%Y-%m-%d'),
               'task_payload': "",
               'task_end_time': None,
               'last_beat_time': datetime.now().strftime('%Y-%m-%d'),
               'platform': environment.get_platform()}

    response = requests.put('http://%s/api/bot/register' % api_host, json=payload, headers=headers)
    if response.status_code == 200:
        logs.log("Bot Registered")
    elif response.status_code == 500:
        logs.log("Bot already Registered")


def get_bot(bot_name):
    """Return the Bot object with the given name."""
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/bot/%s' % (api_host, bot_name), headers=headers)
    json_bot = json.loads(response.content.decode('utf-8'))
    return json_bot


def send_heartbeat(heartbeat, log_info=None):
    api_host = os.environ.get('API_HOST')
    payload = heartbeat
    headers = {'Authorization': os.environ.get('API_KEY'),
               'content-type': 'application/json'}
    response = requests.post('http://%s/api/bot/heartbeat' % api_host, json=payload, headers=headers)
    if response.status_code == 200:
        json_heratbeat = json.loads(response.content.decode('utf-8'))


def update_heartbeat(force_update=False, task_status='NA'):
    """Updates heartbeat with current timestamp and log data."""
    # Check if the heartbeat was recently updated. If yes, bail out.
    last_modified_time = persistent_cache.get_value(
        HEARTBEAT_LAST_UPDATE_KEY, constructor=datetime.utcfromtimestamp)
    if (not force_update and last_modified_time and not dates.time_has_expired(
            last_modified_time, seconds=data_types.HEARTBEAT_WAIT_INTERVAL)):
        return 0

    bot_name = environment.get_value('BOT_NAME')
    current_time = datetime.utcnow().strftime('%Y-%m-%d')
    task_payload = tasks.get_task_payload()
    task_end_time = tasks.get_task_end_time()
    if task_end_time is not None:
        task_end_time = task_end_time.strftime('%Y-%m-%d')
    else:
        task_end_time = current_time
    last_beat_time = current_time
    platform = environment.get_platform()

    heartbeat = {'bot_name': bot_name,
                 'current_time': current_time,
                 'task_status': task_status,
                 'task_payload': task_payload,
                 'task_end_time': task_end_time,
                 'last_beat_time': last_beat_time,
                 'platform': platform}

    send_heartbeat(heartbeat)

    persistent_cache.set_value(
        HEARTBEAT_LAST_UPDATE_KEY, time.time(), persist_across_reboots=True)


def get_task_status(bot_name, task_name):
    """Return the status with the given name."""
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/bot/%s' % (api_host, bot_name), headers=headers)
    json_bot = json.loads(response.content.decode('utf-8'))
    return json_bot['task_status'], json_bot['last_beat_time']


def get_task(platform) -> Task:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/task?platform=%s' % (api_host, platform), headers=headers)
    if response.status_code == 200:
        json_task = json.loads(response.content.decode('utf-8'))
        task = Task(command=json_task['command'], argument=json_task['argument'], job_id=json_task['job_id'])
        return task
    else:
        return None


def add_task(task: Task, queue):
    api_host, headers = api_headers()
    platform = queue.split("-")[1].title()
    payload = {'job_id': task.job,
               'platform': platform,
               'command': task.command,
               'argument': task.argument,
               }
    response = requests.put('http://%s//api/task' % api_host, json=payload, headers=headers)
    if response.status_code == 200:
        logs.log(f"{response.text}")
    else:
        logs.log(f"{response.text}")


def update_task_status(task_name, status, expiry_interval=None):
    """Updates status for a task. Used to ensure that a single instance of a task
  is running at any given time."""
    bot_name = environment.get_value('BOT_NAME')
    failure_wait_interval = environment.get_value('FAIL_WAIT')

    # If we didn't get an expiry interval, default to our task lease interval.
    if expiry_interval is None:
        expiry_interval = environment.get_value('TASK_LEASE_SECONDS')
        if expiry_interval is None:
            logs.log_error('expiry_interval is None and TASK_LEASE_SECONDS not set.')

    def _try_update_status():
        """Try update metadata."""
        task_status, task_status_time = get_task_status(bot_name, task_name)

        # If another bot is already working on this task, bail out with error.
        if (status == data_types.TaskState.STARTED and
                task_status == data_types.TaskState.STARTED and
                not dates.time_has_expired(
                    task_status_time, seconds=expiry_interval - 1)):
            return False

        update_heartbeat(force_update=True, task_status=status)
        return True

    # It is important that we do not continue until the metadata is updated.
    # This can lead to task loss, or can cause issues with multiple bots
    # attempting to run the task at the same time.
    while True:
        try:
            return _try_update_status()
        except Exception as e:
            # We need to update the status under all circumstances.
            # Failing to update 'completed' status causes another bot
            # that picked up this job to bail out.
            logs.log_error('Unable to update %s task metadata. Retrying.' % task_name)
            time.sleep(utils.random_number(1, failure_wait_interval))


# ------------------------------------------------------------------------------
# Job API  Functions
# ------------------------------------------------------------------------------

@memoize.wrap(memoize.Memcache(MEMCACHE_TTL_IN_SECONDS))
def get_all_project_names():
    """Return all project names."""
    query = get_jobs()
    return sorted([job.project for job in query])


def get_job(job_id) -> Job:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/job/%s' % (api_host, job_id), headers=headers)
    if response.status_code == 200:
        json_job = json.loads(response.content.decode('utf-8'))
        try:
            return Job(**json_job)
        except ValidationError as e:
            logs.log_error(e)
    else:
        return None


def get_jobs() -> list[Job]:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/jobs' % api_host, headers=headers)
    jobs = []
    if response.status_code == 200:
        json_jobs = json.loads(response.content.decode('utf-8'))
        try:
            for json_job in json_jobs:
                jobs.append(Job(**json_job))
            return jobs
        except ValidationError as e:
            logs.log_error(e)
    else:
        return []


def get_template(template_name) -> JobTemplate:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/template?name=%s' % (api_host, template_name), headers=headers)
    json_template = json.loads(response.content.decode('utf-8'))
    try:
        return JobTemplate(**json_template)
    except ValidationError as e:
        logs.log_error(e)


def get_value_from_job_definition(job_type, variable_pattern, default=None):
    """Get a specific environment variable's value from a job definition."""
    if not job_type:
        return default

    job = get_job(job_type)
    if not job:
        return default

    return job.name


def get_project_name(job_type):
    """Return project name for a job type."""
    default_project_name = utils.default_project_name()
    return get_value_from_job_definition(job_type, 'PROJECT_NAME',
                                         default_project_name)


# ------------------------------------------------------------------------------
# Fuzzer API  Functions
# ------------------------------------------------------------------------------

def get_fuzzer(fuzzer_name) -> Fuzzer:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/fuzzer?name=%s' % (api_host, fuzzer_name), headers=headers)
    json_fuzzer = json.loads(response.content.decode('utf-8'))
    try:
        if response.status_code == 200:
            return Fuzzer(**json_fuzzer)
    except ValidationError as e:
        logs.log_error(e)


def get_fuzzer_by_id(fuzzer_id) -> Fuzzer:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/fuzzer?id=%s' % (api_host, fuzzer_id), headers=headers)
    json_fuzzer = json.loads(response.content.decode('utf-8'))
    try:
        return Fuzzer(**json_fuzzer)
    except ValidationError as e:
        logs.log_error(e)


# ------------------------------------------------------------------------------
# Fuzzer Target Job API  Functions
# ------------------------------------------------------------------------------

def get_fuzz_target_job_by_job(job_id) -> list[FuzzTargetJob]:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/fuzzTargetJob?job_id=%s' % (api_host, job_id), headers=headers)
    json_fuzzTargetJobs = json.loads(response.content.decode('utf-8'))

    try:
        fuzzTargetJobs = [FuzzTargetJob(**json_fuzzTargetJob) for json_fuzzTargetJob in json_fuzzTargetJobs]
        return fuzzTargetJobs
    except ValidationError as e:
        logs.log_error(e)


def get_fuzz_target_job_by_job_fuzztarget(job_id, fuzzTarget_id) -> list[FuzzTargetJob]:
    api_host, headers = api_headers()
    response = requests.get(
        'http://%s/api/fuzzTargetJob?job_id=%s&fuzzing_target_id=%s' % (api_host, job_id, fuzzTarget_id),
        headers=headers)
    json_fuzzTargetJobs = json.loads(response.content.decode('utf-8'))

    try:
        fuzzTargetJobs = [FuzzTargetJob(**json_fuzzTargetJob) for json_fuzzTargetJob in json_fuzzTargetJobs]
        return fuzzTargetJobs
    except ValidationError as e:
        logs.log_error(e)


def get_fuzz_target_job_by_engine(engine) -> list[FuzzTargetJob]:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/fuzzTargetJob?engine=%s' % (api_host, engine), headers=headers)
    json_fuzzTargetJobs = json.loads(response.content.decode('utf-8'))

    try:
        fuzzTargetJobs = [FuzzTargetJob(**json_fuzzTargetJob) for json_fuzzTargetJob in json_fuzzTargetJobs]
        return fuzzTargetJobs
    except ValidationError as e:
        logs.log_error(e)


def add_fuzz_target_job(fuzz_target_job):
    api_host, headers = api_headers()
    payload = json.loads(fuzz_target_job.json())
    response = requests.put(f'http://{api_host}/api/fuzzTargetJob', json=payload, headers=headers)
    if response.status_code == 200:
        logs.log("Fuzz Target JOb Registered")
    elif response.status_code == 500:
        logs.log("Fuzz Target Job already Registered")


# ------------------------------------------------------------------------------
# Trial API  Functions
# ------------------------------------------------------------------------------

def get_trial_by_id(trial_id) -> Trial:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/trial?id=%s' % (api_host, trial_id), headers=headers)
    json_trial = json.loads(response.content.decode('utf-8'))
    try:
        if response.status_code == 200:
            return Trial(**json_trial)
    except ValidationError as e:
        logs.log_error(e)


def get_trial_by_appname(app_name) -> list[Trial]:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/trial?app_name=%s' % (api_host, app_name), headers=headers)
    json_trial = json.loads(response.content.decode('utf-8'))
    try:
        if response.status_code == 200:
            trials = []
            for trial in json_trial:
                trials.append(Trial(**trial))
            return trials
    except ValidationError as e:
        logs.log_error(e)


def add_trial(app_name, probability=1.0, app_args=""):
    payload = {
        "app_name": app_name,
        "probability": probability,
        "app_args": app_args
    }
    api_host, headers = api_headers()
    response = requests.put('http://%s/api/trial', headers=headers, json=payload)
    json_trial = json.loads(response.content.decode('utf-8'))
    try:
        if response.status_code == 201:
            logs.log("Trial Registered")
    except ValidationError as e:
        logs.log_error(e)


# ------------------------------------------------------------------------------
# Fuzz Target API  Functions
# ------------------------------------------------------------------------------

def get_fuzz_target_by_id(fuzz_target_id) -> FuzzTarget:
    api_host, headers = api_headers()
    response = requests.get('http://%s/api/fuzztarget?id=%s' % (api_host, fuzz_target_id), headers=headers)
    json_fuzzTarget = json.loads(response.content.decode('utf-8'))
    try:
        return FuzzTarget(**json_fuzzTarget)
    except ValidationError as e:
        logs.log_error(e)


def get_fuzz_target_by_keyName(keyname) -> FuzzTarget:
    api_host = os.environ.get('API_HOST')
    split = keyname.split('_')
    fuzzer_engine = split[0]
    binary = split[2]
    headers = {'Authorization': os.environ.get('API_KEY'),
               'content-type': 'application/json'}
    response = requests.get(f'http://{api_host}/api/fuzztarget?fuzzer_engine={fuzzer_engine}&binary={binary}',
                            headers=headers)
    try:
        json_fuzzTarget = json.loads(response.content.decode('utf-8'))
        return FuzzTarget(**json_fuzzTarget)
    except ValidationError as e:
        logs.log_error(e)


def add_fuzz_target(fuzz_target):
    api_host, headers = api_headers()
    payload = json.loads(fuzz_target.json())
    response = requests.put(f'http://{api_host}/api/fuzztarget', json=payload, headers=headers)
    if response.status_code == 200:
        logs.log("Fuzz Target Registered")
    elif response.status_code == 500:
        logs.log("Fuzz Target already Registered")


def record_fuzz_target(engine_name, binary_name, job_type) -> FuzzTarget:
    """Record existence of fuzz target."""
    if not binary_name:
        logs.log_error('Expected binary_name.')
        return None

    project = get_project_name(job_type)
    key_name = data_types.fuzz_target_fully_qualified_name(
        engine_name, project, binary_name)

    fuzz_target = get_fuzz_target_by_keyName(key_name)  # ndb.Key(data_types.FuzzTarget, key_name).get()
    if not fuzz_target:
        fuzz_target = data_types.FuzzTarget(
            fuzzer_engine=engine_name, project=project, binary=binary_name)
        add_fuzz_target(fuzz_target)
    fuzz_target = get_fuzz_target_by_keyName(key_name)

    # job_mapping_key = data_types.fuzz_target_job_key(key_name, job_type)
    job_mapping = get_fuzz_target_job_by_job_fuzztarget(job_type, fuzz_target.id)
    if job_mapping:
        for job in job_mapping:
            job.last_run = utils.utcnow()
    else:
        job_mapping = data_types.FuzzTargetJob(
            fuzzing_target=fuzz_target.id,
            job=job_type,
            engine=engine_name,
            last_run=utils.utcnow())
        add_fuzz_target_job(job_mapping)

    logs.log(
        'Recorded use of fuzz target %s.' % key_name,
        project=project,
        engine=engine_name,
        binary_name=binary_name,
        job_type=job_type)
    return fuzz_target


# ------------------------------------------------------------------------------
# Testcase, TestcaseUploadMetadata database related functions
# ------------------------------------------------------------------------------

def find_testcase(project_name, crash_type, crash_state, security_flag) -> Testcase:
    api_host, headers = api_headers()
    response = requests.get(
        f'http://{api_host}/api/testcase?project_name={project_name}&crash_type={crash_type}&crash_state={crash_state}&security_flag={security_flag}',
        headers=headers)
    try:
        json_testcase = json.loads(response.content.decode('utf-8'))
        if response.status_code == 200:
            logs.log("Main Testcase Identified")
            return Testcase(**json_testcase)
        else:
            logs.log("Testcase Not Found")
            return None
    except ValidationError as e:
        logs.log_error(e)


def get_testcase_by_id(testcase_id) -> Testcase:
    """Return the testcase with the given id, or None if it does not exist."""
    if not testcase_id:
        raise errors.InvalidTestcaseError

    api_host, headers = api_headers()
    response = requests.get(
        f'http://{api_host}/api/testcase/{testcase_id}', headers=headers)
    try:
        json_testcase = json.loads(response.content.decode('utf-8'))
        logs.log("Main Testcase Identified")
        return Testcase(**json_testcase)
    except ValidationError as e:
        logs.log_error(errors.InvalidTestcaseError)


def store_testcase(crash, fuzzed_keys, minimized_keys, regression, fixed,
                   one_time_crasher_flag, comment,
                   absolute_path, fuzzer_name,
                   job_type, archived,
                   gestures, redzone, disable_ubsan, minidump_keys,
                   window_argument, timeout_multiplier, minimized_arguments, archive_filename):
    """Create a testcase and store it in the datastore using remote api."""
    # Initialize variable to prevent invalid values.
    if archived:
        archive_state = data_types.ArchiveStatus.FUZZED
    else:
        archive_state = 0
    if not gestures:
        gestures = []
    if not redzone:
        redzone = 128

    # Create the testcase.

    with open(absolute_path, 'rb') as f:
        test_case = f.read()

    fuzzer = get_fuzzer(fuzzer_name)
    testcase = data_types.Testcase(test_case=test_case, fixed=fixed, one_time_crasher_flag=one_time_crasher_flag,
                                   comments=comment, fuzzed_keys=fuzzed_keys,
                                   absolute_path=absolute_path,
                                   queue=job_type, archived=False,
                                   timestamp=datetime.utcnow(),
                                   triaged=False, has_bug_flag=False, open=True,
                                   testcase_path=absolute_path, minimized_keys=minimized_keys,
                                   minidump_keys=minidump_keys,
                                   additional_metadata='', job_id=job_type, fuzzer_id=fuzzer.id,
                                   regression=regression, disable_ubsan=disable_ubsan,
                                   minimized_arguments=minimized_arguments, timeout_multiplier=timeout_multiplier
                                   )
    testcase.bug_information = crash.crash_info

    # Set metadata fields (e.g. build url, build key, platform string, etc).
    set_initial_testcase_metadata(testcase)

    # Update the comment and save testcase.
    update_testcase_comment(testcase, data_types.TaskState.NA, comment)

    return add_testcase(testcase, crash)


def add_testcase(testcase: Testcase, crash: Crash):
    api_host, headers = api_headers()
    payload = json.loads(testcase.json())
    response = requests.put(f'http://{api_host}/api/testcase', json=payload, headers=headers)
    if response.status_code == 200:
        logs.log("Testcase Registered")
        # Get testcase id from newly created testcase.
        json_testcase = json.loads(response.content.decode('utf-8'))
        testcase_id = json_testcase['id']
        logs.log(
            ('Created new testcase %s (reproducible:%s, security:%s).\n'
             'crash_type: %s\ncrash_state:\n%s\n') %
            (testcase_id, not testcase.one_time_crasher_flag, crash.security_flag,
             crash.crash_type, crash.crash_state))

        # Update global blacklist to avoid finding this leak again (if needed).
        is_lsan_enabled = environment.get_value('LSAN')
        if is_lsan_enabled:
            leak_blacklist.add_crash_to_global_blacklist_if_needed(testcase)
        return testcase_id
    elif response.status_code == 500:
        logs.log("Testcase already Registered")
        return None

def update_testcase(testcase):
    api_host, headers = api_headers()
    payload = json.loads(testcase.json())
    response = requests.post(f'http://{api_host}/api/testcase/{testcase.id}', json=payload,
                             headers=headers)
    try:
        if response.status_code == 200:
            return True
    except ValidationError as e:
        logs.log_error(errors.InvalidTestcaseError)


def set_initial_testcase_metadata(testcase):
    """Set various testcase metadata fields during testcase initialization."""
    build_key = environment.get_value('BUILD_KEY')
    if build_key:
        testcase.set_metadata('build_key', build_key, update_testcase=False)

    build_url = environment.get_value('BUILD_URL')
    if build_url:
        testcase.set_metadata('build_url', build_url, update_testcase=False)

    gn_args_path = environment.get_value('GN_ARGS_PATH', '')
    if gn_args_path and os.path.exists(gn_args_path):
        gn_args = utils.read_data_from_file(
            gn_args_path, eval_data=False, default='').decode('utf-8')

        # Remove goma_dir from gn args since it is only relevant to the machine that
        # did the build.
        filtered_gn_args_lines = [
            line for line in gn_args.splitlines()
            if not GOMA_DIR_LINE_REGEX.match(line)
        ]
        filtered_gn_args = '\n'.join(filtered_gn_args_lines)
        testcase.set_metadata('gn_args', filtered_gn_args, update_testcase=False)

    # testcase.platform = environment.platform().lower()
    # estcase.platform_id = environment.get_platform_id()


def update_testcase_comment(testcase, task_state, message=None):
    """Add task status and message to the test case's comment field."""
    bot_name = environment.get_value('BOT_NAME', 'Unknown')
    task_name = environment.get_value('TASK_NAME', 'Unknown')
    task_string = '%s task' % task_name.capitalize()
    timestamp = utils.current_date_time()

    # For some tasks like blame, progression and impact, we need to delete lines
    # from old task executions to avoid clutter.
    if (task_name in ['blame', 'progression', 'impact'] and
            task_state == data_types.TaskState.STARTED):
        pattern = r'.*?: %s.*\n' % task_string
        testcase.comments = re.sub(pattern, '', testcase.comments)

    testcase.comments += '[%s] %s: %s %s' % (timestamp, bot_name, task_string,
                                             task_state)
    if message:
        testcase.comments += ': %s' % message.rstrip('.')
    testcase.comments += '.\n'

    # Truncate if too long.
    if len(testcase.comments) > data_types.TESTCASE_COMMENTS_LENGTH_LIMIT:
        logs.log_error(
            'Testcase comments truncated (testcase {testcase_id}, job {job_type}).'.
                format(testcase_id=testcase.id, job_type=testcase.job_id))
        testcase.comments = testcase.comments[
                            -data_types.TESTCASE_COMMENTS_LENGTH_LIMIT:]

    # Log the message in stackdriver after the testcase.put() call as otherwise
    # the testcase key might not available yet (i.e. for new testcase).
    if message:
        log_func = (
            logs.log_error
            if task_state == data_types.TaskState.ERROR else logs.log)
        log_func('{message} (testcase {testcase_id}, job {job_type}).'.format(
            message=message,
            testcase_id=testcase.id,
            job_type=testcase.job_id))


# ------------------------------------------------------------------------------
# TestCaseVariants API Functions
# ------------------------------------------------------------------------------

def get_testcase_variant(testcase_id, job_type):
    """Get a testcase variant entity, and create if needed."""
    api_host, headers = api_headers()
    response = requests.get(
        f'http://{api_host}/api/testcase_variant?testcase_id={testcase_id}&job_id={job_type}',
        headers=headers)
    try:
        json_testcase_variant = json.loads(response.content.decode('utf-8'))
        if response.status_code == 200:
            return TestcaseVariant(**json_testcase_variant)
        else:
            logs.log("Testcase Variant Not Found, Creating a new one")
            add_testcase_variant(testcase_id, job_type)
    except ValidationError as e:
        logs.log_error(e)


def add_testcase_variant(testcase_id, job_type):
    api_host, headers = api_headers()
    variant = TestcaseVariant(testcase_id=testcase_id, job_id=job_type)
    payload = json.loads(variant.json())
    response = requests.put(f'http://{api_host}/api/testcase_variant', json=payload, headers=headers)
    if response.status_code == 201:
        logs.log("TestCase Variant Registered")
    elif response.status_code == 500:
        logs.log("TestCase Variant already Registered")


def update_testcase_variant(testcase_variant):
    api_host, headers = api_headers()
    payload = json.loads(testcase_variant.json())
    response = requests.post(f'http://{api_host}/api/testcase_variant/{testcase_variant.id}', json=payload,
                             headers=headers)
    try:
        if response.status_code == 200:
            return True
    except ValidationError as e:
        logs.log_error(errors.InvalidTestcaseError)


# ------------------------------------------------------------------------------
# Crash Target API  Functions
# ------------------------------------------------------------------------------
def get_crash_by_testcase(testcase_id) -> Crash:
    api_host, headers = api_headers()
    response = requests.get(f'http://{api_host}/api/crash?testcase_id={testcase_id}', headers=headers)
    try:
        json_crash = json.loads(response.content.decode('utf-8'))
        if response.status_code == 200:
            if len(json_crash) > 0:
                return Crash(**json_crash)
    except ValidationError as e:
        logs.log_error(e)


def get_crash_type_string(testcase: Testcase):
    """Return a crash type string for a testcase."""
    crash = get_crash_by_testcase(str(testcase.id))
    crash_type = ' '.join(crash.crash_type.splitlines())
    if crash_type not in list(CRASH_TYPE_VALUE_REGEX_MAP.keys()):
        return crash_type

    crash_stacktrace = get_stacktrace(crash)
    match = re.match(CRASH_TYPE_VALUE_REGEX_MAP[crash_type], crash_stacktrace,
                     re.DOTALL)
    if not match:
        return crash_type

    return '%s (exceeds %s %s)' % (crash_type, match.group(1),
                                   CRASH_TYPE_DIMENSION_MAP[crash_type])


def get_reproduction_help_url(testcase, config):
    """Return url to reproduce the bug."""
    return get_value_from_job_definition_or_environment(
        testcase.job_type, 'HELP_URL', default=config.reproduction_help_url)


def store_crash(crash_obj, job_type, testcase_id, one_time_crasher_flag, crash_revision, regression, reproducible_flag,
                iteration):
    crash_hash = hashlib.sha256(crash_obj.crash_stacktrace.encode()).hexdigest()
    crash_stacktrace = base64.b64encode(filter_stacktrace(crash_obj.crash_stacktrace).encode()).decode()
    unsymbolized_crash_stacktrace = base64.b64encode(crash_obj.unsymbolized_crash_stacktrace.encode()).decode()
    crash = Crash(exploitability='', verified=False, additional="", crash_signal=crash_obj.return_code,
                  crash_time=crash_obj.crash_time, crash_hash=crash_hash, iteration=iteration,
                  crash_type=crash_obj.crash_type, crash_address=crash_obj.crash_address,
                  crash_state=utils.decode_to_unicode(crash_obj.crash_state), crash_stacktrace=crash_stacktrace,
                  regression=regression,
                  security_severity=_get_security_severity(crash_obj, job_type, crash_obj.gestures),
                  absolute_path=crash_obj.file_path, security_flag=crash_obj.security_flag,
                  reproducible_flag=not reproducible_flag, return_code=crash_obj.return_code,
                  fuzzing_strategy=crash_obj.fuzzing_strategies,
                  should_be_ignored=crash_obj.should_be_ignored,
                  application_command_line=crash_obj.application_command_line,
                  unsymbolized_crash_stacktrace=unsymbolized_crash_stacktrace,
                  crash_info=crash_obj.crash_info)

    crash.testcase_id = testcase_id

    api_host, headers = api_headers()
    payload = json.loads(crash.json())
    response = requests.put(f'http://{api_host}/api/crash', json=payload, headers=headers)
    if response.status_code == 200:
        logs.log("Crash Registered")
    elif response.status_code == 500:
        logs.log("Crash already Registered")


# ------------------------------------------------------------------------------
# Extra Functions
# ------------------------------------------------------------------------------

def get_fuzzer_display(testcase):
    """Return FuzzerDisplay tuple."""
    if (testcase.overridden_fuzzer_name == testcase.fuzzer_name or
            not testcase.overridden_fuzzer_name):
        return FuzzerDisplay(
            engine=None,
            target=None,
            name=testcase.fuzzer_name,
            fully_qualified_name=testcase.fuzzer_name)

    fuzz_target = get_fuzz_target_by_keyName(testcase.overridden_fuzzer_name)
    if not fuzz_target:
        # Legacy testcases.
        return FuzzerDisplay(
            engine=testcase.fuzzer_name,
            target=testcase.get_metadata('fuzzer_binary_name'),
            name=testcase.fuzzer_name,
            fully_qualified_name=testcase.overridden_fuzzer_name)

    return FuzzerDisplay(
        engine=fuzz_target.engine,
        target=fuzz_target.binary,
        name=fuzz_target.engine,
        fully_qualified_name=fuzz_target.fully_qualified_name())


def filter_arguments(arguments, fuzz_target_name=None):
    """Filter arguments, removing testcase argument and fuzz target binary
  names."""
    # Filter out %TESTCASE*% argument.
    arguments = re.sub(r'[^\s]*%TESTCASE(|_FILE_URL|_HTTP_URL)%', '', arguments)
    if fuzz_target_name:
        arguments = arguments.replace(fuzz_target_name, '')

    return arguments.strip()


def get_arguments(testcase):
    """Return minimized arguments, without testcase argument and fuzz target
  binary itself (for engine fuzzers)."""
    arguments = (
            testcase.minimized_arguments or
            get_value_from_job_definition(testcase.job_type, 'APP_ARGS', default=''))

    # Filter out fuzz target argument. We shouldn't have any case for this other
    # than what is needed by launcher.py for engine based fuzzers.
    fuzzer_display = get_fuzzer_display(testcase)
    fuzz_target = fuzzer_display.target
    return filter_arguments(arguments, fuzz_target)


def _get_memory_tool_options(testcase):
    """Return memory tool options as a string to pass on command line."""
    env = testcase.get_metadata('env')
    if not env:
        return []

    result = []
    for options_name, options_value in sorted(six.iteritems(env)):
        # Strip symbolize flag, use default symbolize=1.
        options_value.pop('symbolize', None)
        if not options_value:
            continue

        options_string = environment.join_memory_tool_options(options_value)
        result.append('{options_name}="{options_string}"'.format(
            options_name=options_name, options_string=quote(options_string)))

    return result


def _get_bazel_test_args(arguments, sanitizer_options):
    """Return arguments to pass to a bazel test."""
    result = []
    for sanitizer_option in sanitizer_options:
        result.append('--test_env=%s' % sanitizer_option)

    for argument in shlex.split(arguments):
        result.append('--test_arg=%s' % quote(argument))

    return ' '.join(result)


def format_issue_information(testcase, format_string):
    """Format a string with information from the testcase."""
    arguments = get_arguments(testcase)
    fuzzer_display = get_fuzzer_display(testcase)
    fuzzer_name = fuzzer_display.name or 'NA'
    fuzz_target = fuzzer_display.target or 'NA'
    engine = fuzzer_display.engine or 'NA'
    last_tested_crash_revision = str(
        testcase.get_metadata('last_tested_crash_revision') or
        testcase.crash_revision)
    project_name = get_project_name(testcase.job_type)
    testcase_id = str(testcase.key.id())
    sanitizer = environment.get_memory_tool_name(testcase.job_type)
    sanitizer_options = _get_memory_tool_options(testcase)
    sanitizer_options_string = ' '.join(sanitizer_options)
    bazel_test_args = _get_bazel_test_args(arguments, sanitizer_options)

    # Multi-target binaries.
    fuzz_target_parts = fuzz_target.split('@')
    base_fuzz_target = fuzz_target_parts[0]
    if len(fuzz_target_parts) == 2:
        fuzz_test_name = fuzz_target_parts[1]
    else:
        fuzz_test_name = ''

    result = format_string.replace('%TESTCASE%', testcase_id)
    result = result.replace('%PROJECT%', project_name)
    result = result.replace('%REVISION%', last_tested_crash_revision)
    result = result.replace('%FUZZER_NAME%', fuzzer_name)
    result = result.replace('%FUZZ_TARGET%', fuzz_target)
    result = result.replace('%BASE_FUZZ_TARGET%', base_fuzz_target)
    result = result.replace('%FUZZ_TEST_NAME%', fuzz_test_name)
    result = result.replace('%ENGINE%', engine)
    result = result.replace('%SANITIZER%', sanitizer)
    result = result.replace('%SANITIZER_OPTIONS%', sanitizer_options_string)
    result = result.replace('%ARGS%', arguments)
    result = result.replace('%BAZEL_TEST_ARGS%', bazel_test_args)
    return result


def get_formatted_reproduction_help(testcase):
    """Return url to reproduce the bug."""
    help_format = get_value_from_job_definition_or_environment(
        testcase.job_type, 'HELP_FORMAT')
    if not help_format:
        return None

    # Since this value may be in a job definition, it's non-trivial for it to
    # include newlines. Instead, it will contain backslash-escaped characters
    # that must be converted here (e.g. \n).
    help_format = help_format.encode().decode('unicode-escape')
    return format_issue_information(testcase, help_format)


def get_plaintext_help_text(testcase, config):
    """Get the help text for this testcase for display in issue descriptions."""
    # Prioritize a HELP_FORMAT message if available.
    formatted_help = get_formatted_reproduction_help(testcase)
    if formatted_help:
        return formatted_help

    # Show a default message and HELP_URL if only it has been supplied.
    help_url = get_reproduction_help_url(testcase, config)
    if help_url:
        return 'See %s for instructions to reproduce this bug locally.' % help_url

    return ''


def handle_duplicate_entry(testcase):
    """Handles duplicates and deletes unreproducible one."""
    # Caller ensures that our testcase object is up-to-date. If someone else
    # already marked us as a duplicate, no more work to do.
    if testcase.duplicate_of:
        return

    existing_testcase = find_testcase(
        testcase.project_name,
        testcase.crash_type,
        testcase.crash_state,
        testcase.security_flag,
        testcase_to_exclude=testcase)
    if not existing_testcase:
        return

    # If the existing testcase's minimization has not completed yet, we shouldn't
    # be doing the next step. The testcase might turn out to be a non reproducible
    # bug and we don't want to delete the other testcase which could be a fully
    # minimized and reproducible bug.
    if not existing_testcase.minimized_keys:
        return

    testcase_id = testcase.key.id()
    existing_testcase_id = existing_testcase.key.id()
    if (not testcase.bug_information and
            not existing_testcase.one_time_crasher_flag):
        metadata = data_types.TestcaseUploadMetadata.query(
            data_types.TestcaseUploadMetadata.testcase_id == testcase_id).get()
        if metadata:
            metadata.status = 'Duplicate'
            metadata.duplicate_of = existing_testcase_id
            metadata.security_flag = existing_testcase.security_flag
            metadata.put()

        testcase.status = 'Duplicate'
        testcase.duplicate_of = existing_testcase_id
        testcase.put()
        logs.log('Marking testcase %d as duplicate of testcase %d.' %
                 (testcase_id, existing_testcase_id))

    elif (not existing_testcase.bug_information and
          not testcase.one_time_crasher_flag):
        metadata = data_types.TestcaseUploadMetadata.query(
            data_types.TestcaseUploadMetadata.testcase_id == testcase_id).get()
        if metadata:
            metadata.status = 'Duplicate'
            metadata.duplicate_of = testcase_id
            metadata.security_flag = testcase.security_flag
            metadata.put()

        existing_testcase.status = 'Duplicate'
        existing_testcase.duplicate_of = testcase_id
        existing_testcase.put()
        logs.log('Marking testcase %d as duplicate of testcase %d.' %
                 (existing_testcase_id, testcase_id))


def is_first_retry_for_task(testcase, reset_after_retry=False):
    """Returns true if this task is tried atleast once. Only applicable for
  analyze and progression tasks."""
    task_name = environment.get_value('TASK_NAME')
    retry_key = '%s_retry' % task_name
    retry_flag = testcase.get_metadata(retry_key)
    if not retry_flag:
        # Update the metadata key since now we have tried it once.
        retry_value = True
        testcase.set_metadata(retry_key, retry_value)
        return True

    # Reset the metadata key so that tasks like progression task can be retried.
    if reset_after_retry:
        retry_value = False
        testcase.set_metadata(retry_key, retry_value)

    return False


@memoize.wrap(memoize.Memcache(MEMCACHE_TTL_IN_SECONDS))
def get_issue_tracker_name(job_type=None):
    """Return issue tracker name for a job type."""
    return get_value_from_job_definition_or_environment(job_type, 'ISSUE_TRACKER')


@memoize.wrap(memoize.Memcache(MEMCACHE_TTL_IN_SECONDS))
def get_project_name(job_type):
    """Return project name for a job type."""
    default_project_name = utils.default_project_name()
    return get_value_from_job_definition(job_type, 'PROJECT_NAME',
                                         default_project_name)


@memoize.wrap(memoize.Memcache(MEMCACHE_TTL_IN_SECONDS))
def get_main_repo(job_type):
    """Return project name for a job type."""
    return get_value_from_job_definition(job_type, 'MAIN_REPO')


def _get_security_severity(crash, job_type, gestures):
    """Get security severity."""
    if crash.security_flag:
        return severity_analyzer.get_security_severity(
            crash.crash_type, crash.crash_stacktrace, job_type, bool(gestures))

    return 0


def get_component_name(job_type):
    """Gets component name for a job type."""
    job = get_job(job_type)
    if not job:
        return ''

    match = re.match(r'.*BUCKET_PATH[^\r\n]*-([a-zA-Z0-9]+)-component',
                     job.get_environment_string(), re.DOTALL)
    if not match:
        return ''

    component_name = match.group(1)
    return component_name


def get_repository_for_component(component):
    """Get the repository based on component."""
    default_repository = ''
    repository = ''
    repository_mappings = db_config.get_value('component_repository_mappings')

    for line in repository_mappings.splitlines():
        current_component, value = line.split(';', 1)

        if current_component == 'default':
            default_repository = value
        elif current_component == component:
            repository = value

    return repository or default_repository


# Utils
def filter_arguments(arguments, fuzz_target_name=None):
    """Filter arguments, removing testcase argument and fuzz target binary
  names."""
    # Filter out %TESTCASE*% argument.
    arguments = re.sub(r'[^\s]*%TESTCASE(|_FILE_URL|_HTTP_URL)%', '', arguments)
    if fuzz_target_name:
        arguments = arguments.replace(fuzz_target_name, '')

    return arguments.strip()


def get_value_from_job_definition_or_environment(job_type,
                                                 variable_pattern,
                                                 default=None):
    """Gets a specific environment variable's value from a job definition. If
  not found, it returns the value from current environment."""
    return get_value_from_job_definition(
        job_type,
        variable_pattern,
        default=environment.get_value(variable_pattern, default))


# ------------------------------------------------------------------------------
# Tasks related functions
# ------------------------------------------------------------------------------
def critical_tasks_completed(testcase):
    """Check to see if all critical tasks have finished running on a test case."""
    if testcase.status == 'Unreproducible':
        # These tasks don't apply to unreproducible testcases.
        return True

    if testcase.one_time_crasher_flag:
        # These tasks don't apply to flaky testcases.
        return True

    # For non-chromium projects, impact and blame tasks are not applicable.
    if not utils.is_chromium():
        return testcase.minimized_keys and testcase.regression

    return bool(testcase.minimized_keys and testcase.regression and
                testcase.is_impact_set_flag)


# ------------------------------------------------------------------------------
# Heartbeat database related functions
# ------------------------------------------------------------------------------
HEARTBEAT_LAST_UPDATE_KEY = 'heartbeat_update'


# ------------------------------------------------------------------------------
# BuildMetadata database related functions
# ------------------------------------------------------------------------------


def get_build_state(job_id, crash_revision):
    """Return whether a build is unmarked, good or bad."""
    api_host, headers = api_headers()

    response = requests.get(f'http://{api_host}/api/buildMetada?job_id={job_id}&revision={crash_revision}',
                            headers=headers)
    try:
        json_BuildMetadatas = json.loads(response.content.decode('utf-8'))
        builds = [BuildMetadata(**json_BuildMetadata) for json_BuildMetadata in json_BuildMetadatas]

        for build in builds:
            if not build:
                return data_types.BuildState.UNMARKED

            if build.bad_build:
                return data_types.BuildState.BAD

            return data_types.BuildState.GOOD
    except ValidationError as e:
        logs.log_error(e)


def add_build_metadata(job,
                       crash_revision,
                       is_bad_build,
                       console_output=None):
    """Add build metadata."""
    build = data_types.BuildMetadata()
    build.bad_build = is_bad_build
    build.bot_name = environment.get_value('BOT_NAME')
    build.console_output = filter_stacktrace(console_output)
    build.job_type = job
    build.revision = crash_revision
    build.timestamp = datetime.utcnow()

    json_build = build.json()

    api_host, headers = api_headers()

    response = requests.put(f'http://{api_host}/api/buildMetada',
                            headers=headers, json=json_build)

    if is_bad_build:
        logs.log_error(
            'Bad build %s.' % job,
            revision=crash_revision,
            job_type=job,
            output=console_output)
    else:
        logs.log(
            'Good build %s.' % job, revision=crash_revision, job_type=job)
    return build


# ------------------------------------------------------------------------------
# Data bundlers database related functions
# ------------------------------------------------------------------------------

def get_data_bundle(bundle_name):
    """Return data bundle object"""
    api_host, headers = api_headers()

    response = requests.get(f'http://{api_host}/api/dataBundle?name={bundle_name}',
                            headers=headers)
    try:
        json_data_bundle = json.loads(response.content.decode('utf-8'))
        data_bundle = DataBundle(**json_data_bundle)
        return data_bundle
    except ValidationError as e:
        logs.log_error(e)


# ------------------------------------------------------------------------------
# Stacktraces related functions
# -----------------

def get_stacktrace(crash, stack_attribute='crash_stacktrace'):
    """Returns the stacktrace for a test case.

  This may require a blobstore read.
  """
    result = getattr(crash, stack_attribute)
    if not result or not result.startswith(data_types.BLOBSTORE_STACK_PREFIX):
        return result

    # For App Engine, we can't write to local file, so use blobs.read_key instead.
    if environment.is_running_on_app_engine():
        key = result[len(data_types.BLOBSTORE_STACK_PREFIX):]
        return str(blobs_manager.read_key(key), 'utf-8', errors='replace')

    key = result[len(data_types.BLOBSTORE_STACK_PREFIX):]
    tmpdir = environment.get_value('BOT_TMPDIR')
    tmp_stacktrace_file = os.path.join(tmpdir, 'stacktrace.tmp')
    blobs_manager.read_blob_to_disk(key, tmp_stacktrace_file)

    try:
        with open(tmp_stacktrace_file) as handle:
            result = handle.read()
    except:
        logs.log_error(
            'Unable to read stacktrace for testcase %d.' % crash.key.id())
        result = ''

    shell.remove_file(tmp_stacktrace_file)
    return result


def filter_stacktrace(stacktrace):
    """Filters stacktrace and returns content appropriate for storage as an
  appengine entity."""
    unicode_stacktrace = utils.decode_to_unicode(stacktrace)
    if len(unicode_stacktrace) <= data_types.STACKTRACE_LENGTH_LIMIT:
        return unicode_stacktrace

    tmpdir = environment.get_value('BOT_TMPDIR')
    tmp_stacktrace_file = os.path.join(tmpdir, 'stacktrace.tmp')

    try:
        with open(tmp_stacktrace_file, 'wb') as handle:
            handle.write(unicode_stacktrace.encode('utf-8'))
        with open(tmp_stacktrace_file, 'rb') as handle:
            size = os.stat(tmp_stacktrace_file).st_size
            key = blobs_manager.write_blob(handle, file_size=size)
    except Exception:
        logs.log_error('Unable to write crash stacktrace to temporary file.')
        shell.remove_file(tmp_stacktrace_file)
        return unicode_stacktrace[(-1 * data_types.STACKTRACE_LENGTH_LIMIT):]

    shell.remove_file(tmp_stacktrace_file)
    return '%s%s' % (data_types.BLOBSTORE_STACK_PREFIX, key)
