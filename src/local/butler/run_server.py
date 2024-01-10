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
  

  

def start_cron_threads():
  """Start threads to trigger essential cron jobs."""

  request_timeout = 10 * 60  # 10 minutes.

  def trigger(interval_seconds, target):
    """Trigger a cron job."""
    while True:
      time.sleep(interval_seconds)

      try:
        url = 'http://{host}/{target}'.format(
            host=constants.CRON_SERVICE_HOST, target=target)
        request = urllib.request.Request(url)
        request.add_header('X-Appengine-Cron', 'true')
        response = urllib.request.urlopen(request, timeout=request_timeout)
        response.read(60)  # wait for request to finish.
      except Exception:
        continue

  crons = (
      (90, 'cleanup'),
      (60, 'triage'),
      (6 * 3600, 'schedule-progression-tasks'),
      (12 * 3600, 'schedule-corpus-pruning'),
  )

  for interval, cron in crons:
    thread = threading.Thread(target=trigger, args=(interval, cron))
    thread.daemon = True
    thread.start()


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
    # Set up local buckets and symlinks.
    bootstrap_buckets(config)
    bootstrap_db()

  start_cron_threads()

  os.environ['APPLICATION_ID'] = constants.TEST_APP_ID
  os.environ['LOCAL_DEVELOPMENT'] = 'True'
  os.environ['PINGU_ENV'] = 'dev'
  try:
    # TODO: Migrate cron tasks to celery
    #cron_server = common.execute_async(
    #    'gunicorn -b :{port} main:app'.format(port=constants.CRON_SERVICE_PORT),
    #    cwd=os.path.join('src', 'backend'))

    #common.execute(
    #    'gunicorn -b :{port} main:app'.format(
    #        port=constants.DEV_APPSERVER_PORT),
    #    cwd=os.path.join('src', 'backend'))

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
