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


"""run_server.py run the Clusterfuzz server locally."""
import os
import shlex
import shutil
import threading
import time
import urllib.request

from pingubot.src.bot.config import local_config
from src.local.butler import appengine
from src.local.butler import common
from src.local.butler import constants
from pingubot.src.bot.datastore.storage import MinioProvider


def bootstrap_db():
  """Bootstrap the DB."""

  def bootstrap():
    # Wait for the server to run.
    time.sleep(10)
    print('Bootstrapping datastore...')
    command_line = f'python butler.py run setup --non-dry-run --local --config-dir={constants.TEST_CONFIG_DIR}'
    command = shlex.split(command_line, posix=True)

    common.execute(
        command=command,
        exit_on_error=False)

  thread = threading.Thread(target=bootstrap)
  thread.start()

def create_backend_admin_account(config):
      # Django run server command
    command_line = f"python manage.py createsuperuser --username {config.get('env.BACKEND_SUPERUSER')} --settings PinguBackend.settings.development"
    command = shlex.split(command_line, posix=True)

    common.execute(
      command,
      cwd=os.environ['ROOT_DIR']
    )

def create_minio_bucket(provider, name):
  """Create a local bucket."""
  try:
      provider.create_bucket(name)
  except Exception as e:
      print(f'{e}')


def bootstrap_buckets(config):
  """Bootstrap GCS."""
  test_blobs_bucket = os.environ.get('TEST_BLOBS_BUCKET')
  provider = MinioProvider()
  
  if test_blobs_bucket:
    create_minio_bucket(provider, test_blobs_bucket)
  else:
    create_minio_bucket(provider, config.get('blobs.bucket'))

  create_minio_bucket(provider, config.get('deployment.bucket'))
  create_minio_bucket(provider, config.get('bigquery.bucket'))
  create_minio_bucket(provider, config.get('backup.bucket'))
  create_minio_bucket(provider, config.get('logs.fuzzer.bucket'))
  create_minio_bucket(provider, config.get('env.CORPUS_BUCKET'))
  create_minio_bucket(provider, config.get('env.QUARANTINE_BUCKET'))
  create_minio_bucket(provider, config.get('env.SHARED_CORPUS_BUCKET'))
  create_minio_bucket(provider, config.get('env.FUZZ_LOGS_BUCKET'))
  create_minio_bucket(provider, config.get('env.FUZZERS_BUCKET'))
  create_minio_bucket(provider, config.get('env.RELEASE_BUILD_BUCKET'))
  create_minio_bucket(provider, config.get('env.SYM_RELEASE_BUILD_BUCKET'))
  create_minio_bucket(provider, config.get('env.SYM_DEBUG_BUILD_BUCKET'))
  create_minio_bucket(provider, config.get('env.STABLE_BUILD_BUCKET'))
  create_minio_bucket(provider, config.get('env.BETA_BUILD_BUCKET'))


def execute(args):
  """Run the server."""
  #os.environ['LOCAL_DEVELOPMENT'] = 'True'

  if not args.skip_install_deps:
    common.install_dependencies(packages=["backend"], )

  # Do this everytime as a past deployment might have changed these.
  appengine.symlink_dirs(src_dir_py=os.path.join('src', 'backend'))

  # TODO: Clean DB and Butckets if needed.
  #if args.bootstrap or args.clean:

  config = local_config.ProjectConfig()

  config.set_environment()

  # Shout down all dockers to ensure everything starts correctly
  common.execute(['/bin/bash', '-c', 'docker-compose down'])

  # Run Bucket server, redis and mongo DB
  common.execute(['/bin/bash', '-c', 'docker-compose up --no-log-prefix -d database queue minio'])
  time.sleep(5)
  if args.bootstrap:
    create_backend_admin_account(config)
    # Set up local buckets and symlinks.
    bootstrap_buckets(config)
    bootstrap_db()

  os.environ['APPLICATION_ID'] = constants.TEST_APP_ID
  os.environ['LOCAL_DEVELOPMENT'] = 'True'
  os.environ['PINGU_ENV'] = 'dev'
  try:
    # Django run server command
    command_line = f"python manage.py runserver {constants.DEV_APPSERVER_PORT} --settings PinguBackend.settings.development"
    command = shlex.split(command_line, posix=True)

    common.execute(
      command,
      cwd=os.environ['ROOT_DIR']
    )
    
  except KeyboardInterrupt:
    print('Server has been stopped. Exit.')
    #cron_server.terminate()
    # Shout down all dockers to ensure everything starts correctly
    common.execute(['/bin/bash', '-c', 'docker-compose down'])
