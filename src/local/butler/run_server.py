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
import sys
import threading
import time
import pika
from src.local.butler import appengine
from src.local.butler import common
from src.local.butler import constants


def execute(args):
  """Run the server."""
  if not args.skip_install_deps:
    common.install_dependencies(packages=["backend"], )

  # Do this everytime as a past deployment might have changed these.
  appengine.sync_dirs(src_dir_py=os.path.join('src', 'backend'), sub_configs=['redis', 'system', 'database', 'minio'])

  # TODO: Clean DB and Butckets if needed.
  #if args.bootstrap or args.clean:
  os.chdir(os.environ['ROOT_DIR'])
  from src.backend.src.bootstrap import bootstrap_db, create_admin_user, load_initial_data, bootstrap_queues
  _redis_config = bootstrap_queues.load_config()
  _db_config = bootstrap_db.load_config()
  _system_admin_config = create_admin_user.load_config()

  # Shout down all dockers to ensure everything starts correctly
  common.execute(
    command=['/bin/bash', '-c', 'docker-compose down database queue minio'],
    cwd=os.environ['ROOT_DIR'])

  # Run Bucket server, redis and mongo DB
  common.execute(
    command=['/bin/bash', '-c', 'docker-compose up database queue minio --no-log-prefix -d'],
    cwd=os.environ['ROOT_DIR'])
  
  if args.bootstrap:
    time.sleep(10)
    # Boostrap DB
    bootstrap_db.create_databases(_db_config)
    bootstrap_db.apply_migrations()
    # Boosttrap Queues
    bootstrap_queues.setup_queues(_redis_config)
    # Boostrap super user
    create_admin_user.create_admin_user(_system_admin_config)
    # Boostrap default DB data
    load_initial_data.setup_templates()
    load_initial_data.setup_fuzzers()
    
    

  os.environ['APPLICATION_ID'] = constants.TEST_APP_ID
  os.environ['LOCAL_DEVELOPMENT'] = 'True'
  os.environ['PINGU_ENV'] = 'dev'
  try:
    # Django run server command
    command_line = f"python manage.py runserver --settings PinguBackend.settings.development"
    command = shlex.split(command_line, posix=True)

    common.execute(
      command,
      cwd=os.environ['ROOT_DIR']
    )
    
    # Celery async beat and worker
    celery_command = f"./celery_runner.sh"
    
    common.execute(
      celery_command,
      cwd=os.environ['ROOT_DIR']
    )
    
  except KeyboardInterrupt:
    print('Server has been stopped. Exit.')
    #cron_server.terminate()
    # Shout down all dockers to ensure everything starts correctly
    common.execute(['/bin/bash', '-c', 'docker-compose down'])
