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

"""run_bot.py run a PinguCrew bot locally."""
import os
import shlex
import signal
import sys
from local.butler import common
from local.butler import constants
from src.local.butler import appengine

_fuzzBot_handle = None


def _setup_bot_directory(args):
    """Set up the bot directory."""
    
    src_root_dir = os.environ['ROOT_DIR'] #os.path.abspath('.')
    if os.path.exists(args.directory):
        print('Bot directory already exists. Re-using...')
    else:
        print('Creating new bot directory...')
        os.makedirs(args.directory)

    working_directory = os.path.join(args.directory, 'working_directory')
    bot_src_dir = os.path.join(args.directory, 'src')
    bot_config_dir = os.path.join(args.directory, 'config')
    if not os.path.exists(working_directory):
        os.makedirs(working_directory)
        os.mkdir(bot_src_dir)
        os.mkdir(bot_config_dir)

    common.update_dir(
        os.path.join(src_root_dir, 'src', 'bot', 'startup'),
        os.path.join(bot_src_dir, 'startup')
    )

    common.update_dir(
        os.path.join(src_root_dir, 'src', 'bot'),
        os.path.join(bot_src_dir, 'bot')
    )

    common.update_dir(
        os.path.join(src_root_dir, 'config'),
        os.path.join(bot_config_dir)
    )

    common.update_dir(
        os.path.join(src_root_dir, 'third_party'),
        os.path.join(args.directory, 'third_party'))

    common.update_dir(
        os.path.join(src_root_dir, 'resources'),
        os.path.join(working_directory, 'resources'))

    common.update_dir(
        os.path.join(src_root_dir, 'working_directory'),
        os.path.join(working_directory))


def _setup_environment_and_configs(args):
    """Set up environment variables and configuration files."""
    bot_dir = os.path.abspath(os.path.join(args.directory, 'working_directory'))

    root_source = os.path.abspath(os.path.join(args.directory))
    # Matches startup scripts.
    if not args.testing:
        os.environ['PYTHONPATH'] = ''
        os.environ['PYTHONPATH'] = ':'.join([
        os.path.join(root_source, 'third_party/'),
        os.path.join(root_source, 'src/'),
        os.getenv('PYTHONPATH', '')
        ])
        # Remove specific paths from sys.path
        # Remove specific paths from sys.path
        sys.path = [p for p in sys.path if not (p.endswith('src') or p.endswith('pingubot/third_party'))]
        sys.path.insert(0, os.path.join(root_source, 'src/'))
        sys.path.insert(0, os.path.join(root_source, 'src/third_party'))

    os.environ['ROOT_DIR'] = os.path.abspath(os.path.join(root_source))
    
    os.environ['BOT_DIR'] = bot_dir
    if not os.getenv('BOT_NAME'):
        os.environ['BOT_NAME'] = args.name

    os.environ['LD_LIBRARY_PATH'] = '{0}:{1}'.format(
        os.path.join(root_source, 'src', 'bot',
                     'scripts'), os.getenv('LD_LIBRARY_PATH', ''))

    tmpdir = os.path.join(bot_dir, 'bot_tmpdir')
    if not os.path.exists(tmpdir):
        os.mkdir(tmpdir)
    os.environ['TMPDIR'] = tmpdir
    os.environ['BOT_TMPDIR'] = tmpdir

    os.environ['KILL_STALE_INSTANCES'] = 'False'
    os.environ['LOCAL_DEVELOPMENT'] = 'True'
    #os.environ['DATASTORE_EMULATOR_HOST'] = constants.DATASTORE_EMULATOR_HOST
    #os.environ['PUBSUB_EMULATOR_HOST'] = constants.PUBSUB_EMULATOR_HOST
    os.environ['APPLICATION_ID'] = constants.TEST_APP_ID

    # if not os.getenv('UNTRUSTED_WORKER'):
    #  local_buckets_path = os.path.abspath(
    #      os.path.join(args.server_storage_path, 'local_storage'))
    #  assert os.path.exists(local_buckets_path), (
    #      'Server storage path not found, make sure to start run_server with '
    #      'the same storage path.')

    #  os.environ['LOCAL_BUCKETS_PATH'] = local_buckets_path

    if args.android_serial:
        if not os.getenv('OS_OVERRIDE'):
            os.environ['OS_OVERRIDE'] = 'ANDROID'

        os.environ['ANDROID_SERIAL'] = args.android_serial


def execute(args):
    """Run the bot."""
    
    bot_path = os.path.join(os.environ['ROOT_DIR'], 'src/bot')
    # Do this everytime as a past deployment might have changed these.
    appengine.sync_dirs(src_dir_py=os.environ['ROOT_DIR'], sub_configs=['bot', 'suppressions'])

    _setup_bot_directory(args)
    _setup_environment_and_configs(args)
    
    if args.testing:
        os.chdir(bot_path)
        os.environ['BASE_DIR'] = bot_path
    else:
        bot_path = os.path.join(os.environ['ROOT_DIR'], 'src/bot')
        os.chdir(bot_path)
        os.environ['BASE_DIR'] = bot_path

    run_interpreter = sys.executable

    assert run_interpreter
    command_line = '%s %s ' % (run_interpreter, 'startup/run.py')
    command = shlex.split(command_line, posix=True)

    try:
        proc = common.execute_async(command)

        def _stop_handler(*_):
            print('Bot has been stopped. Exit.')
            proc.kill()

        signal.signal(signal.SIGTERM, _stop_handler)
        common.process_proc_output(proc)
        proc.wait()

    except KeyboardInterrupt:
        _stop_handler()
