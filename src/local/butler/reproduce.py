# Copyright 2024 IOActive
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

"""reproduce.py reproduces test cases locally."""

import base64
from src.pingubot.src.bot.config import local_config
from src.pingubot.src.bot.system import modules

modules.fix_module_search_paths(submodule_root="pingubot")

import os
import shutil
import tempfile
import time
from urllib import parse

from src.pingubot.src.bot.utils import json_utils
from src.pingubot.src.bot.utils  import utils
from src.pingubot.src.bot import testcase_manager
from src.pingubot.src.bot.fuzzers import init
from src.pingubot.src.bot.tasks import commands
from src.pingubot.src.bot.tasks import setup
from src.pingubot.src.bot.build_management import build_manager
from src.pingubot.src.bot.datastore import data_types
from src.pingubot.src.bot.system import archive
from src.pingubot.src.bot.system import environment
from src.pingubot.src.bot.system import new_process
from src.pingubot.src.bot.system import shell
from src.pingubot.src.bot.datastore.data_handler import get_testcase_by_id, get_job, get_crash_by_testcase, get_fuzzer_by_id
from local.butler.reproduce_tool import android
from local.butler.reproduce_tool import config
from local.butler.reproduce_tool import errors
from local.butler.reproduce_tool import http_utils
from local.butler.reproduce_tool import prompts

CONFIG_DIRECTORY = os.path.join(
    os.path.expanduser('~'), '.config', 'bot')
DISPLAY = ':99'
PROCESS_START_WAIT_SECONDS = 2
SUPPORTED_PLATFORMS = ['android', 'fuchsia', 'linux', 'mac']

FILENAME_RESPONSE_HEADER = 'x-goog-meta-filename'


class SerializedTestcase(object):
  """Minimal representation of a test case."""

  def __init__(self, testcase_map):
    self._testcase_map = testcase_map

  def __getattr__(self, item):
    return self._testcase_map[item]

  def get_metadata(self, key=None, default=None):
    """Emulate Testcase's get_metadata function."""
    metadata = json_utils.loads(self.additional_metadata)
    if not key:
      return metadata

    try:
      return self.metadata[key]
    except KeyError:
      return default

  def actual_fuzzer_name(self):
    """Actual fuzzer name, uses one from overridden attribute if available."""
    return self.overridden_fuzzer_name or self.fuzzer_name

  def get_fuzz_target(self):
    """Return a fuzz target for this test case in the expected format."""
    if not self.serialized_fuzz_target:
      return None

    fuzz_target = data_types.FuzzTarget(
        engine=self.serialized_fuzz_target['engine'],
        project=self.serialized_fuzz_target['project'],
        binary=self.serialized_fuzz_target['binary'])
    return fuzz_target


def prepare_testcase(testcase):
  """Download the test case and return its path."""
  print('Downloading testcase...')

  content = base64.b64decode(testcase.test_case)

  # Store the test case in the config directory for debuggability.
  testcase_directory = os.path.join(CONFIG_DIRECTORY, 'current-testcase')
  shell.remove_directory(testcase_directory, recreate=True)
  environment.set_value('FUZZ_INPUTS', testcase_directory)
  testcase_path = f'{testcase_directory}/{testcase.id}'
                               
  utils.write_data_to_file(content, testcase_path)

  # Unpack the test case if it's archived.
  # TODO(mbarbella): Rewrite setup.unpack_testcase and share this code.
  if testcase.minimized_keys and testcase.minimized_keys != 'NA':
    mask = data_types.ArchiveStatus.MINIMIZED
  else:
    mask = data_types.ArchiveStatus.FUZZED

  if testcase.archive_state & mask:
    archive.unpack(testcase_path, testcase_directory)
    file_list = archive.get_file_list(testcase_path)

    testcase_path = None
    for file_name in file_list:
      if os.path.basename(file_name) == os.path.basename(
          testcase.absolute_path):
        testcase_path = os.path.join(testcase_directory, file_name)
        break

    if not testcase_path:
      raise errors.ReproduceToolUnrecoverableError(
          'Test case file was not found in archive.\n'
          'Original filename: {absolute_path}.\n'
          'Archive contents: {file_list}'.format(
              absolute_path=testcase.absolute_path, file_list=file_list))

  return testcase_path


def _setup_x(fuzzer_name):
  """Start Xvfb and blackbox before running the test application."""
  if environment.platform() != 'LINUX':
    return []

  if environment.is_engine_fuzzer_job(fuzzer_name):
    # For engine fuzzer jobs like AFL, libFuzzer, Xvfb is not needed as the
    # those fuzz targets do not needed a UI.
    return []

  environment.set_value('DISPLAY', DISPLAY)

  print('Creating virtual display...')
  xvfb_runner = new_process.ProcessRunner('/usr/bin/Xvfb')
  xvfb_process = xvfb_runner.run(additional_args=[
      DISPLAY, '-screen', '0', '1280x1024x24', '-ac', '-nolisten', 'tcp'
  ])
  time.sleep(PROCESS_START_WAIT_SECONDS)

  blackbox_runner = new_process.ProcessRunner('/usr/bin/blackbox')
  blackbox_process = blackbox_runner.run()
  time.sleep(PROCESS_START_WAIT_SECONDS)

  # Return all handles we create so they can be terminated properly at exit.
  return [xvfb_process, blackbox_process]


def _prepare_initial_environment(build_directory, iterations, verbose):
  """Prepare common environment variables that don't depend on the job."""
  # Create a temporary directory to use as ROOT_DIR with a copy of the default
  # bot and configuration directories nested under it.
  root_dir = environment.get_value('ROOT_DIR')
  temp_root_dir = tempfile.mkdtemp()
  environment.set_value('ROOT_DIR', temp_root_dir)

  def _update_directory(directory_name, destination, ignore_paths=None):
    """Copy a subdirectory from a checkout to a temp directory."""
    if not ignore_paths:
      ignore_paths = []

    shutil.copytree(
        os.path.join(root_dir, directory_name),
        os.path.join(temp_root_dir, destination),
        ignore=lambda directory, contents:
        contents if directory in ignore_paths else [])

  _update_directory('src/pingubot/src', 'src/bot')
  _update_directory('configs', 'configs')
  _update_directory('src/pingubot/resources', 'resources')
  _update_directory('src/pingubot/bot_working_directory','bot_working_directory')


  environment.set_value('CONFIG_DIR_OVERRIDE',
                        os.path.join(temp_root_dir, 'configs', 'test'))
  environment.set_value(
      'PYTHONPATH',
      os.path.join(temp_root_dir, 'src')
  )

  local_config.ProjectConfig().set_environment()
  environment.set_bot_environment()

  # Overrides that should not be set to the default values.
  environment.set_value('APP_DIR', build_directory)
  environment.set_value('BUILD_DIR', build_directory)
  environment.set_value('BUILDS_DIR', build_directory)

  # Some functionality must be disabled when running the tool.
  environment.set_value('REPRODUCE_TOOL', True)

  environment.set_value('TASK_NAME', 'reproduce')

  # Force logging to console for this process and child processes.
  if verbose:
    environment.set_value('LOG_TO_CONSOLE', True)

  if iterations:
    environment.set_value('CRASH_RETRIES', iterations)


def _verify_target_exists(build_directory):
  """Ensure that we can find the test target before running it.

  Separated into its own function to simplify test behavior."""
  if not build_manager.check_app_path():
    raise errors.ReproduceToolUnrecoverableError(
        'Unable to locate app binary in {build_directory}.'.format(
            build_directory=build_directory))


def _update_environment_for_testcase(testcase: data_types.Testcase, testcase_related_job: data_types.Job,
                                     tesetcase_related_fuzzer: data_types.Fuzzer,
                                     build_directory,
                                     application_override):
  """Update environment variables that depend on the test case."""
  commands.update_environment_for_job(testcase_related_job.environment_string)
  environment.set_value('JOB_NAME', testcase_related_job.id)
  
  # Override app name if explicitly specified.
  if application_override:
    environment.set_value('APP_NAME', application_override)

  if tesetcase_related_fuzzer.name:
    fuzzer_directory = setup.get_fuzzer_directory(tesetcase_related_fuzzer.name)
  else:
    fuzzer_directory = os.path.join(environment.get_value('ROOT_DIR'), 'fuzzer')
    shell.create_directory(fuzzer_directory)

  environment.set_value('FUZZER_DIR', fuzzer_directory)

  task_name = environment.get_value('TASK_NAME')
  setup.prepare_environment_for_testcase(testcase, testcase_related_job.id, task_name)

  build_manager.set_environment_vars(
      [environment.get_value('FUZZER_DIR'), build_directory])

  _verify_target_exists(build_directory)


def _print_stacktrace(result):
  """Display the output from a test case run."""
  print('#' * 80)
  print(result.get_stacktrace())
  print('#' * 80)
  print()


def _reproduce_crash(testcase_id, build_directory, iterations, disable_xvfb,
                     verbose, disable_android_setup, application):
  """Reproduce a crash."""
  _prepare_initial_environment(build_directory, iterations, verbose)

  # Validate the test case URL and fetch the tool's configuration.
  #configuration = config.ReproduceToolConfiguration(testcase_id)
  testcase = get_testcase_by_id(testcase_id=testcase_id)
  testcase_related_job = get_job(job_id=str(testcase.job_id))
  testcase_raelated_crash = get_crash_by_testcase(testcase_id=str(testcase.id))

  # For new user uploads, we'll fail without the metadata set by analyze task.
  if not testcase_related_job.platform:
    raise errors.ReproduceToolUnrecoverableError(
        'This test case has not yet been processed. Please try again later.')

  # Ensure that we support this test case's platform.
  if testcase_related_job.platform.lower() not in SUPPORTED_PLATFORMS:
    raise errors.ReproduceToolUnrecoverableError(
        'The reproduce tool is not yet supported on {platform}.'.format(
            platform=testcase_related_job.platform))

  # Print warnings for this test case.
  if testcase.one_time_crasher_flag:
    print('Warning: this test case was a one-time crash. It may not be '
          'reproducible.')
  if testcase_raelated_crash.flaky_stack:
    print('Warning: this test case is known to crash with different stack '
          'traces.')

  testcase_path = prepare_testcase(testcase)
  tesetcase_related_fuzzer = get_fuzzer_by_id(testcase.fuzzer_id)

  _update_environment_for_testcase(testcase, testcase_related_job, tesetcase_related_fuzzer, build_directory, application)

  # Validate that we're running on the right platform for this test case.
  platform = environment.platform().lower()
  if testcase_related_job.platform.lower() == 'android' and platform == 'linux':
    android.prepare_environment(disable_android_setup)
  elif testcase_related_job.platform.lower() == 'android' and platform != 'linux':
    raise errors.ReproduceToolUnrecoverableError(
        'The ClusterFuzz environment only supports running Android test cases '
        'on Linux host machines. Unable to reproduce the test case on '
        '{current_platform}.'.format(current_platform=platform))
  elif testcase_related_job.platform.lower() != platform:
    raise errors.ReproduceToolUnrecoverableError(
        'The specified test case was discovered on {testcase_platform}. '
        'Unable to attempt to reproduce it on {current_platform}.'.format(
            testcase_platform=testcase_related_job.platform, current_platform=platform))

  x_processes = []
  if not disable_xvfb:
    _setup_x(tesetcase_related_fuzzer.name)
  timeout = environment.get_value('TEST_TIMEOUT')

  print('Running testcase...')
  try:
    result = testcase_manager.test_for_crash_with_retries(
        testcase, testcase_path, timeout, testcase_raelated_crash, crash_retries=1)

    # If we can't reproduce the crash, prompt the user to try again.
    if not result.is_crash():
      _print_stacktrace(result)
      result = None
      use_default_retries = prompts.get_boolean(
          'Failed to find the desired crash on first run. Re-run '
          '{crash_retries} times?'.format(
              crash_retries=environment.get_value('CRASH_RETRIES')))
      if use_default_retries:
        print('Attempting to reproduce test case. This may take a while...')
        result = testcase_manager.test_for_crash_with_retries(
            testcase, testcase_path, timeout, testcase_raelated_crash)

  except KeyboardInterrupt:
    print('Aborting...')
    result = None

  # Terminate Xvfb and blackbox.
  for process in x_processes:
    process.terminate()

  return result


def _cleanup():
  """Clean up after running the tool."""
  temp_directory = environment.get_value('ROOT_DIR')
  assert 'tmp' in temp_directory
  shell.remove_directory(temp_directory)


def execute(args):
  """Attempt to reproduce a crash then report on the result."""
  # Initialize fuzzing engines.
  init.run()

  # Prepare the emulator if needed.
  emulator_process = None
  if args.emulator:
    print('Starting emulator...')
    emulator_process = android.start_emulator()

  # The current working directory may change while we're running.
  absolute_build_dir = os.path.abspath(args.build_dir)
  try:
    result = _reproduce_crash(args.testcase, absolute_build_dir,
                              args.iterations, args.disable_xvfb, args.verbose,
                              args.disable_android_setup, args.application)
  except errors.ReproduceToolUnrecoverableError as exception:
    print(exception)
    return
  finally:
    if emulator_process:
      emulator_process.terminate()

  if not result:
    return

  _print_stacktrace(result)

  if result.is_crash():
    status_message = 'Test case reproduced successfully.'
  else:
    status_message = 'Unable to reproduce the desired crash.'
  print(status_message)

  _cleanup()
