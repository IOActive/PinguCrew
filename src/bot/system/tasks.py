# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Task queue functions."""

import contextlib
import datetime
import json
import random
import time

# Task queue prefixes for various job types.
from src.bot.datastore import data_types, data_handler
from src.bot.fuzzing import fuzzer_selection
from src.bot.system import environment, persistent_cache
from src.bot.utils import utils

JOBS_PREFIX = 'tasks'
HIGH_END_JOBS_PREFIX = 'high-end-jobs'

# Default task queue names for various job types. These will be different for
# different platforms with the platform name added as suffix later.
JOBS_TASKQUEUE = JOBS_PREFIX
HIGH_END_JOBS_TASKQUEUE = HIGH_END_JOBS_PREFIX

# ML job is currently supported on Linux only.
ML_JOBS_TASKQUEUE = 'ml-jobs-linux'

# Limits on number of tasks leased at once and in total.
MAX_LEASED_TASKS_LIMIT = 1000
MAX_TASKS_LIMIT = 100000

# Various variables for task leasing and completion times (in seconds).
TASK_COMPLETION_BUFFER = 90 * 60
TASK_CREATION_WAIT_INTERVAL = 2 * 60
TASK_EXCEPTION_WAIT_INTERVAL = 5 * 60
TASK_LEASE_SECONDS = 6 * 60 * 60  # Can be overridden via environment variable.
TASK_LEASE_SECONDS_BY_COMMAND = {
    'corpus_pruning': 24 * 60 * 60,
    'regression': 24 * 60 * 60,
}

TASK_QUEUE_DISPLAY_NAMES = {
    'LINUX': 'Linux',
    'LINUX_WITH_GPU': 'Linux (with GPU)',
    'LINUX_UNTRUSTED': 'Linux (untrusted)',
    'ANDROID': 'Android',
    'ANDROID_KERNEL': 'Android Kernel',
    'ANDROID_KERNEL_X86': 'Android Kernel (X86)',
    'ANDROID_AUTO': 'Android Auto',
    'ANDROID_X86': 'Android (x86)',
    'ANDROID_EMULATOR': 'Android (Emulated)',
    'CHROMEOS': 'Chrome OS',
    'FUCHSIA': 'Fuchsia OS',
    'MAC': 'Mac',
    'WINDOWS': 'Windows',
    'WINDOWS_WITH_GPU': 'Windows (with GPU)',
}

VALID_REDO_TASKS = ['minimize', 'regression', 'progression', 'impact', 'blame']

LEASE_FAIL_WAIT = 10
LEASE_RETRIES = 5

TASK_PAYLOAD_KEY = 'task_payload'
TASK_END_TIME_KEY = 'task_end_time'


class Error(Exception):
    """Base exception class."""


class InvalidRedoTask(Error):

    def __init__(self, task):
        super().__init__("The task '%s' is invalid." % task)


def queue_suffix_for_platform(platform):
    """Get the queue suffix for a platform."""
    return '-' + platform.lower().replace('_', '-')


def default_queue_suffix():
    """Get the queue suffix for the current platform."""
    queue_override = environment.get_value('QUEUE_OVERRIDE')
    if queue_override:
        return queue_suffix_for_platform(queue_override)

    return queue_suffix_for_platform(environment.platform())


def regular_queue(prefix=JOBS_PREFIX):
    """Get the regular jobs queue."""
    return prefix + default_queue_suffix()


def high_end_queue():
    """Get the high end jobs queue."""
    return regular_queue(prefix=HIGH_END_JOBS_PREFIX)


def default_queue():
    """Get the default jobs queue."""
    thread_multiplier = environment.get_value('THREAD_MULTIPLIER')
    if thread_multiplier and thread_multiplier > 1:
        return high_end_queue()

    return regular_queue()


def get_command_override():
    """Get command override task."""
    command_override = environment.get_value('COMMAND_OVERRIDE', '').strip()
    if not command_override:
        return None

    parts = command_override.split()
    if len(parts) != 3:
        raise ValueError('Command override should have 3 components.')

    return Task(*parts, is_command_override=True)


def get_fuzz_task():
    """Try to get a fuzz task."""
    argument, job = fuzzer_selection.get_fuzz_task_payload()
    if not argument:
        return None

    return Task('fuzz', argument, job)


def get_high_end_task():
    """Get a high end task."""
    task = get_regular_task(queue=high_end_queue())
    if not task:
        return None

    task.high_end = True
    return task


def _on_test_case(channel, method_frame, header_frame, body):
    test_case_info = json.loads(body.decode())
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)
    '''Tasks format
    {'payload': base64.b64encode(build_file).decode('utf-8'),
                  'filename': "build.zip",
                  'job_id': str(job.id),
                  'timeout': job.timeout}'''
    task = Task(command='fuzz', argument='', job_id=test_case_info)  # TODO backend multi-tasks
    return task


def get_regular_task(platform=None):
    """Get a regular task."""
    return data_handler.get_task(platform)


def get_task():
    """Get a task."""
    task = get_command_override()
    if task:
        return task

    task = get_regular_task(environment.get_value('PLATFORM'))
    if task:
        return task


class Task(object):
    """Represents a task."""

    def __init__(self,
                 command,  # task_name
                 argument,  # fuzzer_name
                 job_id,
                 eta=None,
                 is_command_override=False,
                 high_end=False):
        self.command = command
        self.argument = str(argument)
        self.job = str(job_id)
        self.eta = eta
        self.is_command_override = is_command_override
        self.high_end = high_end

    def attribute(self, _):
        return None

    def payload(self):
        """Get the payload."""
        return ' '.join([self.command, self.argument, self.job])

    @contextlib.contextmanager
    def lease(self):
        """Maintain a lease for the task. Track only start and end by default."""
        environment.set_value('TASK_LEASE_SECONDS', TASK_LEASE_SECONDS)
        track_task_start(self, TASK_LEASE_SECONDS)
        yield
        track_task_end()


def add_task(command, argument, job_type, queue=None, wait_time=None):
    """Add a new task to the job queue."""
    # Old testcases may pass in queue=None explicitly,
    # so we must check this here.
    if not queue:
        queue = default_queue()

    if wait_time is None:
        wait_time = random.randint(1, TASK_CREATION_WAIT_INTERVAL)

    if job_type != 'none':
        job = data_handler.get_job(job_type)
        if not job:
            raise Error(f'Job {job_type} not found.')

    # Add the task.
    eta = utils.utcnow() + datetime.timedelta(seconds=wait_time)
    task = Task(command, argument, job_type, eta=eta)
    data_handler.add_task(task=task, queue=queue)


def get_task_lease_timeout():
    """Return the task lease timeout."""
    return environment.get_value('TASK_LEASE_SECONDS', TASK_LEASE_SECONDS)


def get_task_completion_deadline():
    """Return task completion deadline. This gives an additional buffer over the
  task lease deadline."""
    start_time = time.time()
    task_lease_timeout = get_task_lease_timeout()
    return start_time + task_lease_timeout - TASK_COMPLETION_BUFFER


def queue_for_platform(platform, is_high_end=False):
    """Return the queue for the platform."""
    prefix = HIGH_END_JOBS_PREFIX if is_high_end else JOBS_PREFIX
    return prefix + queue_suffix_for_platform(platform)


def queue_for_testcase(testcase):
    """Return the right queue for the testcase."""
    is_high_end = (
            testcase.queue and testcase.queue.startswith(HIGH_END_JOBS_PREFIX))
    return queue_for_job(testcase.job_type, is_high_end=is_high_end)


def queue_for_job(job_name, is_high_end=False):
    """Queue for job."""
    job = data_types.Job.query(data_types.Job.name == job_name).get()
    if not job:
        raise Error('Job {} not found.'.format(job_name))

    return queue_for_platform(job.platform, is_high_end)


def redo_testcase(testcase, tasks, user_email):
    """Redo specific tasks for a testcase."""
    for task in tasks:
        if task not in VALID_REDO_TASKS:
            raise InvalidRedoTask(task)

    minimize = 'minimize' in tasks
    regression = 'regression' in tasks
    progression = 'progression' in tasks
    impact = 'impact' in tasks
    blame = 'blame' in tasks

    task_list = []
    testcase_id = testcase.key.id()

    # Metadata keys to clear based on which redo tasks were selected.
    metadata_keys_to_clear = ['potentially_flaky']

    if minimize:
        task_list.append('minimize')
        testcase.minimized_keys = ''
        testcase.set_metadata('redo_minimize', True, update_testcase=False)
        metadata_keys_to_clear += [
            'env', 'current_minimization_phase_attempts', 'minimization_phase'
        ]

        # If this testcase was archived during minimization, update the state.
        testcase.archive_state &= data_types.ArchiveStatus.MINIMIZED

    if regression:
        task_list.append('regression')
        testcase.regression = ''
        metadata_keys_to_clear += ['last_regression_min', 'last_regression_max']

    if progression:
        task_list.append('progression')
        testcase.fixed = ''
        testcase.open = True
        testcase.last_tested_crash_stacktrace = None
        testcase.triaged = False
        testcase.set_metadata('progression_pending', True, update_testcase=False)
        metadata_keys_to_clear += [
            'last_progression_min', 'last_progression_max', 'last_tested_revision'
        ]

    for key in metadata_keys_to_clear:
        testcase.delete_metadata(key, update_testcase=False)

    testcase.comments += '[%s] %s: Redo task(s): %s\n' % (
        utils.current_date_time(), user_email, ', '.join(sorted(task_list)))
    testcase.one_time_crasher_flag = False
    testcase.put()

    # # Allow new notifications to be sent for this testcase.
    # notifications = ndb_utils.get_all_from_query(
    #     data_types.Notification.query(
    #         data_types.Notification.testcase_id == testcase.key.id()),
    #     keys_only=True)
    # ndb_utils.delete_multi(notifications)

    # If we are re-doing minimization, other tasks will be done automatically
    # after minimization completes. So, don't add those tasks.
    if minimize:
        add_task('minimize', testcase_id, testcase.job_type,
                 queue_for_testcase(testcase))
    else:
        if regression:
            add_task('regression', testcase_id, testcase.job_type,
                     queue_for_testcase(testcase))

        if progression:
            add_task('progression', testcase_id, testcase.job_type,
                     queue_for_testcase(testcase))


def get_task_payload():
    """Return current task payload."""
    return persistent_cache.get_value(TASK_PAYLOAD_KEY)


def get_task_end_time():
    """Return current task end time."""
    return persistent_cache.get_value(
        TASK_END_TIME_KEY, constructor=datetime.datetime.utcfromtimestamp)


def track_task_start(task, task_duration):
    """Cache task information."""
    persistent_cache.set_value(TASK_PAYLOAD_KEY, task.payload())
    persistent_cache.set_value(TASK_END_TIME_KEY, time.time() + task_duration)

    # Don't wait on |run_heartbeat|, update task information as soon as it starts.

    from src.bot.datastore import data_handler
    data_handler.update_heartbeat(force_update=True)


def track_task_end():
    """Remove cached task information."""
    persistent_cache.delete_value(TASK_PAYLOAD_KEY)
    persistent_cache.delete_value(TASK_END_TIME_KEY)

    # Don't wait on |run_heartbeat|, remove task information as soon as it ends.

    from src.bot.datastore import data_handler
    data_handler.update_heartbeat(force_update=True)
