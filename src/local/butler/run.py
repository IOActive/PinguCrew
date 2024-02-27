"""run.py runs a one-off script (e.g. migration) with appropriate envs (e.g.
  datastore)."""

import importlib
import os

from local.butler import constants
from src.pingubot.src.bot.config import local_config


def execute(args):
    """Run Python u.. For unittests involved appengine, sys.path
     needs certain modification."""
    os.environ['CONFIG_DIR_OVERRIDE'] = args.config_dir
    local_config.ProjectConfig().set_environment()

    if args.local:
        os.environ['DATASTORE_USE_PROJECT_ID_AS_APP_ID'] = 'true'
        os.environ['LOCAL_DEVELOPMENT'] = 'True'

    if not args.non_dry_run:
        print('Running in dry-run mode, no datastore writes are committed. '
              'For permanent modifications, re-run with --non-dry-run.')
    
    script = importlib.import_module(
        'local.butler.scripts.%s' % args.script_name)
    script.execute(args)

    if not args.local:
        print()
        print('Please remember to run the migration individually on all projects.')
        print()
