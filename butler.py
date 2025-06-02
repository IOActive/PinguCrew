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

"""Butler is here to help you with command-line tasks (e.g. running unit tests,
   deploying).

   You should code a task in Butler if any of the belows is true:
   - you run multiple commands to achieve the task.
   - you keep forgetting how to achieve the task.

   Please do `python butler.py --help` to see what Butler can help you.
"""

import click
import importlib
import os
import sys
from argparse import Namespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.local.butler import common, constants, guard
from src.local.butler.modules import fix_module_search_paths

guard.check()

@click.group()
def cli():
    """Butler is here to help you with command-line tasks."""
    pass

@cli.command()
@click.option('-r', '--only-reproduce', is_flag=True, help='Only install dependencies needed for the reproduce tool.')
@click.option('-p', '--packages', multiple=True, default=['bot', 'backend', 'frontend'], help='List of packages to install.')
def bootstrap(only_reproduce, packages):
    """Install all required dependencies for running locally."""
    command = importlib.import_module('src.local.butler.bootstrap')
    _setup(None)
    args = Namespace(only_reproduce=only_reproduce, packages=list(packages))
    command.execute(args)

@cli.command()
@click.option('-b', '--bootstrap', is_flag=True, help='Bootstrap the local database.')
@click.option('--storage-path', default='local/storage', help='Storage path for local database.')
@click.option('--skip-install-deps', is_flag=True, help='Skip installing dependencies before running.')
@click.option('--log-level', default='info', help='Logging level.')
@click.option('--clean', is_flag=True, help='Clear existing database data.')
def run_server(bootstrap, storage_path, skip_install_deps, log_level, clean):
    """Run the local PinguCrew server."""
    command = importlib.import_module('src.local.butler.run_server')
    _setup('backend')
    args = Namespace(bootstrap=bootstrap, storage_path=storage_path, skip_install_deps=skip_install_deps, log_level=log_level, clean=clean)
    command.execute(args)

@cli.command()
@click.argument('script_name')
@click.option('--non-dry-run', is_flag=True, help='Run with actual datastore writes.')
@click.option('-c', '--config-dir', required=True, help='Path to application config.')
@click.option('--local', is_flag=True, help='Run against local server instance.')
def run(script_name, non_dry_run, config_dir, local):
    """Run a one-off script against a datastore."""
    command = importlib.import_module(f'src.local.butler.scripts.{script_name}')
    _setup(None)
    args = Namespace(script_name=script_name, non_dry_run=non_dry_run, config_dir=config_dir, local=local)
    command.execute(args)

@cli.command()
@click.option('-c', '--config-dir', required=True, help='Path to application config.')
@click.option('--name', default='test-bot', help='Name of the bot.')
@click.option('--server-storage-path', default='local/storage', help='Server storage path.')
@click.argument('directory')
@click.option('--android-serial', help='Serial number of an Android device to connect to.')
@click.option('--testing', is_flag=True, help='Run in testing mode.')
def run_bot(config_dir, name, server_storage_path, directory, android_serial, testing):
    """Run a local bot."""
    command = importlib.import_module('src.local.butler.run_bot')
    _setup('pingubot')
    args = Namespace(config_dir=config_dir, name=name, server_storage_path=server_storage_path, directory=directory, android_serial=android_serial, testing=testing)
    command.execute(args)

@cli.command()
@click.option('-t', '--testcase', required=True, help='Testcase URL.')
@click.option('-b', '--build-dir', required=True, help='Build directory containing the target app and dependencies.')
@click.option('-i', '--iterations', default=10, help='Number of times to attempt reproduction.')
@click.option('-dx', '--disable-xvfb', is_flag=True, help='Disable running test case in a virtual frame buffer.')
@click.option('-da', '--disable-android-setup', is_flag=True, help='Skip Android device setup.')
@click.option('-v', '--verbose', is_flag=True, help='Print additional log messages.')
@click.option('-e', '--emulator', is_flag=True, help='Run using the Android emulator.')
@click.option('-a', '--application', help='Name of the application binary to run.')
def reproduce(testcase, build_dir, iterations, disable_xvfb, disable_android_setup, verbose, emulator, application):
    """Reproduce a crash or error from a test case."""
    command = importlib.import_module('src.local.butler.reproduce')
    _setup(None)
    args = Namespace(testcase=testcase, build_dir=build_dir, iterations=iterations, disable_xvfb=disable_xvfb, disable_android_setup=disable_android_setup, verbose=verbose, emulator=emulator, application=application)
    command.execute(args)

@cli.command()
@click.option('--skip-install-deps', is_flag=True, help='Skip installing dependencies before running.')
def run_web(skip_install_deps):
    """Run the frontend web server."""
    command = importlib.import_module('src.local.butler.run_web')
    _setup('frontend')
    args = Namespace(skip_install_deps=skip_install_deps)
    command.execute(args)

def _setup(submodule_root=None):
    """Set up import paths."""
    if submodule_root:
        os.environ['ROOT_DIR'] = os.path.abspath(f'./src/{submodule_root}')
    else:
        os.environ['ROOT_DIR'] = os.path.abspath(f'.')

    os.environ['PYTHONIOENCODING'] = 'UTF-8'
    sys.path.insert(0, os.path.abspath(os.path.join('src')))
    fix_module_search_paths(submodule_root)

if __name__ == '__main__':
    cli()
