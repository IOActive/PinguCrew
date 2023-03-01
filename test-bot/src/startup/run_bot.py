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
"""Bot startup script."""

# Before any other imports, we must fix the path. Some libraries might expect
# to be able to import dependencies directly, but we must store these in
# subdirectories of common so that they are shared with App Engine.
import multiprocessing
import os
import sys
import time
import traceback

from src.bot.datastore import data_handler
from src.bot.datastore.data_handler import register_bot
from src.bot.metrics import logs, monitoring_metrics
from src.bot.system import environment, errors, tasks
from src.bot.tasks import update_task
from src.bot.utils import dates, utils
from src.bot.fuzzers import init as fuzzers_init


class _Monitor(object):
    """Monitor one task."""

    def __init__(self, task, time_module=time):
        self.task = task
        self.time_module = time_module
        self.start_time = None

    def __enter__(self):
        monitoring_metrics.TASK_COUNT.increment({
            'task': self.task.command or '',
            'job': self.task.job or '',
        })
        self.start_time = self.time_module.time()

    def __exit__(self, exc_type, value, trackback):
        pass


def task_loop():
    """Executes tasks indefinitely."""
    # Defer heavy task imports to prevent issues with multiprocessing.Process
    from src.bot.tasks import commands
    # Register Bot
    register_bot()
    clean_exit = False
    while True:
        stacktrace = ''
        exception_occurred = False
        task = None
        # This caches the current environment on first run. Don't move this.
        environment.reset_environment()
        try:
            # Run regular updates.
            update_task.run()

            task = tasks.get_task()
            if not task:
                wait_next_loop()
                continue

            with _Monitor(task):
                with task.lease():
                    # Execute the command and delete the task.
                    commands.process_command(task)
        except SystemExit as e:
            exception_occurred = True
            clean_exit = (e.code == 0)
            if not clean_exit:
                logs.log_error('SystemExit occurred while working on task.')

            stacktrace = traceback.format_exc()
        except commands.AlreadyRunningError:
            exception_occurred = False
        except Exception as e:
            logs.log_error('Error occurred while working on task: %s' % e)
            exception_occurred = True
            stacktrace = traceback.format_exc()

        if exception_occurred:
            wait_next_loop()
            break

    task_payload = task.payload() if task else None
    return stacktrace, clean_exit, task_payload


def wait_next_loop():
    # Prevent looping too quickly. See: crbug.com/644830
    failure_wait_interval = environment.get_value('FAIL_WAIT')
    time.sleep(utils.random_number(1, failure_wait_interval))


def main():
    """Prepare the configuration options and start requesting tasks."""
    logs.configure('run_bot')

    dates.initialize_timezone_from_environment()
    # monitor.initialize()
    fuzzers_init.run()

    while True:
        # task_loop should be an infinite loop,
        # unless we run into an exception.
        error_stacktrace, clean_exit, task_payload = task_loop()

        # Print the error trace to the console.
        if not clean_exit:
            print('Exception occurred while running "%s".' % task_payload)
            print('-' * 80)
            print(error_stacktrace)
            print('-' * 80)

        should_terminate = (
                clean_exit or errors.error_in_list(error_stacktrace,
                                                   errors.BOT_ERROR_TERMINATION_LIST))
        if should_terminate:
            return

        logs.log_error(
            'Task exited with exception (payload="%s").' % task_payload,
            error_stacktrace=error_stacktrace)

        should_hang = errors.error_in_list(error_stacktrace,
                                           errors.BOT_ERROR_HANG_LIST)
        if should_hang:
            logs.log('Start hanging forever.')
            while True:
                # Sleep to avoid consuming 100% of CPU.
                time.sleep(60)

        # See if our run timed out, if yes bail out.
        if data_handler.bot_run_timed_out():
            return


if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')

    try:
        main()
        exit_code = 0
    except Exception as e:
        traceback.print_exc()
        exit_code = 1

    # TODO monitor.stop()

    # Prevent python GIL deadlocks on shutdown. See https://crbug.com/744680.
    # os._exit(exit_code)  # pylint: disable=protected-access
