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
"""Run command based on the current task."""

import sys

import six

from src.bot.datastore import data_handler
from src.bot.datastore import data_types
from src.bot.datastore.data_handler import get_job
from src.bot.metrics import logs
from src.bot.system import environment, tasks, errors
from src.bot.system import process_handler
from src.bot.system import shell
from src.bot.tasks import analyze_task
from src.bot.tasks import corpus_pruning_task
from src.bot.tasks import fuzz_task
from src.bot.tasks import minimize_task
from src.bot.tasks import progression_task
from src.bot.tasks import regression_task
from src.bot.tasks import symbolize_task
from src.bot.tasks import train_rnn_generator_task
from src.bot.tasks import unpack_task
from src.bot.tasks import upload_reports_task
from src.bot.utils import utils

COMMAND_MAP = {
    'analyze': analyze_task,
    'corpus_pruning': corpus_pruning_task,
    'fuzz': fuzz_task,
    'minimize': minimize_task,
    'train_rnn_generator': train_rnn_generator_task,
    'progression': progression_task,
    'regression': regression_task,
    'symbolize': symbolize_task,
    'unpack': unpack_task,
    'upload_reports': upload_reports_task,
}

TASK_RETRY_WAIT_LIMIT = 5 * 60  # 5 minutes.


class Error(Exception):
    """Base commands exceptions."""


class AlreadyRunningError(Error):
    """Exception raised for a task that is already running on another bot."""


def cleanup_task_state():
    """Cleans state before and after a task is executed."""
    # Cleanup stale processes.
    process_handler.cleanup_stale_processes()

    # Clear build urls, temp and testcase directories.
    shell.clear_build_urls_directory()
    shell.clear_crash_stacktraces_directory()
    shell.clear_testcase_directories()
    shell.clear_temp_directory()
    shell.clear_system_temp_directory()
    shell.clear_device_temp_directories()

    # Reset memory tool environment variables.
    environment.reset_current_memory_tool_options()

    # Call python's garbage collector.
    utils.python_gc()


def is_supported_cpu_arch_for_job():
    """Return true if the current cpu architecture can run this job."""
    cpu_arch = environment.get_cpu_arch()
    if not cpu_arch:
        # No cpu architecture check is defined for this platform, bail out.
        return True

    supported_cpu_arch = environment.get_value('CPU_ARCH')
    if not supported_cpu_arch:
        # No specific cpu architecture requirement specified in job, bail out.
        return True

    # Convert to list just in case anyone specifies value as a single string.
    supported_cpu_arch_list = list(supported_cpu_arch)

    return cpu_arch in supported_cpu_arch_list


def update_environment_for_job(environment_string):
    """Process the environment variable string included with a job."""
    # Now parse the job's environment definition.
    environment_values = (
        environment.parse_environment_definition(environment_string))

    for key, value in six.iteritems(environment_values):
        environment.set_value(key, value)

    # If we share the build with another job type, force us to be a custom binary
    # job type.
    if environment.get_value('SHARE_BUILD_WITH_JOB_TYPE'):
        environment.set_value('CUSTOM_BINARY', True)

    # Allow the default FUZZ_TEST_TIMEOUT and MAX_TESTCASES to be overridden on
    # machines that are preempted more often.
    fuzz_test_timeout_override = environment.get_value(
        'FUZZ_TEST_TIMEOUT_OVERRIDE')
    if fuzz_test_timeout_override:
        environment.set_value('FUZZ_TEST_TIMEOUT', fuzz_test_timeout_override)

    max_testcases_override = environment.get_value('MAX_TESTCASES_OVERRIDE')
    if max_testcases_override:
        environment.set_value('MAX_TESTCASES', max_testcases_override)


def set_task_payload(func):
    """Set TASK_PAYLOAD and unset TASK_PAYLOAD."""

    def wrapper(task):
        """Wrapper."""
        environment.set_value('TASK_PAYLOAD', task.payload())
        try:
            return func(task)
        except:  # Truly catch *all* exceptions.
            e = sys.exc_info()[1]
            e.extras = {'task_payload': environment.get_value('TASK_PAYLOAD')}
            raise
        finally:
            environment.remove_key('TASK_PAYLOAD')

    return wrapper


def should_update_task_status(task_name):
    """Whether the task status should be automatically handled."""
    return task_name not in [
        # Multiple fuzz tasks are expected to run in parallel.
        'fuzz',

        # The task payload can't be used as-is for de-duplication purposes as it
        # includes revision. corpus_pruning_task calls update_task_status itself
        # to handle this.
        # TODO(ochang): This will be cleaned up as part of migration to Pub/Sub.
        'corpus_pruning',
    ]


def run_command(task_name, task_argument, job_name):
    """Run the command."""
    if task_name not in COMMAND_MAP:
        logs.log_error("Unknown command '%s'" % task_name)
        return

    task_module = COMMAND_MAP[task_name]

    # If applicable, ensure this is the only instance of the task running.
    task_state_name = ' '.join([task_name, task_argument, job_name])
    if should_update_task_status(task_name):
        if not data_handler.update_task_status(environment.get_value('BOT_NAME'),
                                               data_types.TaskState.STARTED):
            logs.log('Another instance of "{}" already '
                     'running, exiting.'.format(task_state_name))
            raise AlreadyRunningError

    try:
        task_module.execute_task(task_argument, job_name)
    except errors.InvalidTestcaseError:
        # It is difficult to try to handle the case where a test case is deleted
        # during processing. Rather than trying to catch by checking every point
        # where a test case is reloaded from the datastore, just abort the task.
        logs.log_warn('Test case %s no longer exists.' % task_argument)
    except BaseException as e:
        # On any other exceptions, update state to reflect error and re-raise.
        if should_update_task_status(task_name):
            data_handler.update_task_status(task_state_name,
                                            data_types.TaskState.ERROR)

        raise

    # Task completed successfully.
    if should_update_task_status(task_name):
        data_handler.update_task_status(task_state_name,
                                        data_types.TaskState.FINISHED)


# pylint: disable=too-many-nested-blocks
@set_task_payload
def process_command(task):
    """Figures out what to do with the given task and executes the command."""
    logs.log("Executing command '%s'" % task.payload())
    if not task.payload().strip():
        logs.log_error('Empty task received.')
        return

    # Parse task payload.
    task_name = task.command
    task_argument = task.argument
    job = get_job(task.job)
    if not job:
        logs.log_error("Job not found.")
        return
    job_name = str(job.id)

    environment.set_value('TASK_NAME', task_name)
    environment.set_value('TASK_ARGUMENT', task_argument)
    environment.set_value('JOB_NAME', job_name)

    if not job.platform:
        error_string = "No platform set for job '%s'" % job_name
        logs.log_error(error_string)
        raise errors.BadStateError(error_string)

    fuzzer_name = None
    if task_name == 'fuzz':
        fuzzer_name = task_argument
        environment.set_value("FUZZER_NAME", fuzzer_name)

    # Get job's environment string.
    environment_string = job.get_environment_string()

    if task_name == 'minimize':
        # Let jobs specify a different job and fuzzer to minimize with.
        job_environment = job.get_environment()
        minimize_job_override = job_environment.get('MINIMIZE_JOB_OVERRIDE')
        if minimize_job_override:
            minimize_job = job
            if minimize_job:
                environment.set_value('JOB_NAME', minimize_job_override)
                environment_string = minimize_job.get_environment_string()
                environment_string += '\nORIGINAL_JOB_NAME = %s\n' % job_name
                job_name = minimize_job_override
            else:
                logs.log_error(
                    'Job for minimization not found: %s.' % minimize_job_override)
                # Fallback to using own job for minimization.

        minimize_fuzzer_override = job_environment.get('MINIMIZE_FUZZER_OVERRIDE')
        fuzzer_name = minimize_fuzzer_override or fuzzer_name

    if fuzzer_name and not environment.is_engine_fuzzer_job(fuzzer_name):
        fuzzer = data_handler.get_fuzzer(fuzzer_name)
        additional_default_variables = ''
        additional_variables_for_job = ''
        if (fuzzer and hasattr(fuzzer, 'additional_environment_string') and
                fuzzer.additional_environment_string):
            for line in fuzzer.additional_environment_string.splitlines():
                # Job specific values may be defined in fuzzer additional
                # environment variable name strings in the form
                # job_name:VAR_NAME = VALUE.
                if '=' in line and ':' in line.split('=', 1)[0]:
                    fuzzer_job_name, environment_definition = line.split(':', 1)
                    if fuzzer_job_name == job_name:
                        additional_variables_for_job += '\n%s' % environment_definition
                    continue

                additional_default_variables += '\n%s' % line

        environment_string += additional_default_variables
        environment_string += additional_variables_for_job

    # Update environment for the job.
    update_environment_for_job(environment_string)

    # Match the cpu architecture with the ones required in the job definition.
    # If they don't match, then bail out and recreate task.
    if not is_supported_cpu_arch_for_job():
        logs.log(
            'Unsupported cpu architecture specified in job definition, exiting.')
        tasks.add_task(
            task_name,
            task_argument,
            job_name,
            wait_time=utils.random_number(1, TASK_RETRY_WAIT_LIMIT))
        return

    run_command(task_name, task_argument, job_name)
