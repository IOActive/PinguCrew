"""Butler is here to help you with command-line tasks (e.g. running unit tests,
   deploying).

   You should code a task in Butler if any of the belows is true:
   - you run multiple commands to achieve the task.
   - you keep forgetting how to achieve the task.

   Please do `python butler.py --help` to see what Butler can help you.
"""

import argparse
import importlib
import os
import subprocess
import sys
import venv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# guard needs to be at the top because it checks Python dependecies.
from src.local.butler import common, constants, guard

guard.check()


class _ArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser."""

    def __init__(self, *args, **kwargs):
        """Override formatter_class to show default argument values in message."""
        kwargs['formatter_class'] = argparse.ArgumentDefaultsHelpFormatter
        argparse.ArgumentParser.__init__(self, *args, **kwargs)

    def error(self, message):
        """Override to print full help for ever error."""
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def main():
    """Parse the command-line args and invoke the right command."""
    parser = _ArgumentParser(
        description='Butler is here to help you with command-line tasks.')
    subparsers = parser.add_subparsers(dest='command')

    parser_bootstrap = subparsers.add_parser(
        'bootstrap',
        help=('Install all required dependencies for running an appengine, a bot,'
              'and a mapreduce locally.'))
    parser_bootstrap.add_argument(
        '-r',
        '--only-reproduce',
        action='store_true',
        help='Only install dependencies needed for the reproduce tool.')
   
    parser_run_server = subparsers.add_parser(
        'run_server', help='Run the local PinguCrew server.')
    parser_run_server.add_argument(
        '-b',
        '--bootstrap',
        action='store_true',
        help='Bootstrap the local database.')
    parser_run_server.add_argument(
        '--storage-path',
        default='local/storage',
        help='storage path for local database.')
    parser_run_server.add_argument(
        '--skip-install-deps',
        action='store_true',
        help=('Don\'t install dependencies before running this command (useful '
              'when you\'re restarting the server often).'))
    parser_run_server.add_argument(
        '--log-level', default='info', help='Logging level')
    parser_run_server.add_argument(
        '--clean', action='store_true', help='Clear existing database data.')

    parser_run = subparsers.add_parser(
        'run', help='Run a one-off script against a datastore (e.g. migration).')
    parser_run.add_argument(
        'script_name',
        help='The script module name under `./local/butler/scripts`.')
    parser_run.add_argument(
        '--non-dry-run',
        action='store_true',
        help='Run with actual datastore writes. Default to dry-run.')
    parser_run.add_argument(
        '-c', '--config-dir', required=True, help='Path to application config.')
    parser_run.add_argument(
        '--local', action='store_true', help='Run against local server instance.')

    parser_run_bot = subparsers.add_parser(
        'run_bot', help='Run a local bot bot.')

    parser_run_bot.add_argument(
        '-c', '--config-dir', required=True, help='Path to application config.')
    parser_run_bot.add_argument(
        '--name', default='test-bot', help='Name of the bot.')
    parser_run_bot.add_argument(
        '--server-storage-path',
        default='local/storage',
        help='Server storage path.')
    parser_run_bot.add_argument('directory', help='Directory to create bot in.')
    parser_run_bot.add_argument(
        '--android-serial',
        help='Serial number of an Android device to connect to instead of '
             'running normally.')
    parser_run_bot.add_argument('--testing', dest='testing', action='store_true')

    parser_reproduce = subparsers.add_parser(
        'reproduce', help='Reproduce a crash or error from a test case.')
    parser_reproduce.add_argument(
        '-t', '--testcase', required=True, help='Testcase URL.')
    parser_reproduce.add_argument(
        '-b',
        '--build-dir',
        required=True,
        help='Build directory containing the target app and dependencies.')
    parser_reproduce.add_argument(
        '-i',
        '--iterations',
        default=10,
        help='Number of times to attempt reproduction.')
    parser_reproduce.add_argument(
        '-dx',
        '--disable-xvfb',
        action='store_true',
        help='Disable running test case in a virtual frame buffer.')
    parser_reproduce.add_argument(
        '-da',
        '--disable-android-setup',
        action='store_true',
        help='Skip Android device setup. Speeds up Android reproduction, but '
             'assumes the device has already been configured by the tool.')
    parser_reproduce.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Print additional log messages while running.')
    parser_reproduce.add_argument(
        '-e',
        '--emulator',
        action='store_true',
        help='Run and attempt to reproduce a crash using the Android emulator.')
    parser_reproduce.add_argument(
        '-a',
        '--application',
        help='Name of the application binary to run. Only required if it '
             'differs from the one the test case was discovered with.')
    
    parser_run_web = subparsers.add_parser('run_web', help="Run Frontend web server")
    parser_run_web.add_argument(
        '--skip-install-deps',
        action='store_true',
        help=('Don\'t install dependencies before running this command (useful '
              'when you\'re restarting the server often).'))


    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    submodule_root=None

    if args.command == "run_bot":
        submodule_root="pingubot"
        _setup(submodule_root)
        #command = importlib.import_module(f'src.pingubot.src.local.butler.{args.command}')
        common.symlink(src=args.config_dir, target=os.path.join('src/pingubot', 'config'))
        #os.environ['CONFIG_DIR_OVERRIDE'] = os.path.join('src/pingubot', 'config')
        command = importlib.import_module(f'src.local.butler.{args.command}')

    elif args.command == "run_server" or args.command == "run":
        submodule_root='backend'
        _setup(submodule_root)
        sys.path.insert(0, os.path.abspath(os.path.join('src/pingubot/src/')))
        sys.path.insert(0, os.path.abspath(os.path.join('src/pingubot/third_party/')))
        command = importlib.import_module(f'src.local.butler.{args.command}')

    elif args.command == "run_web":
        submodule_root='frontend'
        _setup(submodule_root)
        command = importlib.import_module(f'src.local.butler.{args.command}')
        
    else:
        _setup(submodule_root)
        sys.path.insert(0, os.path.abspath(os.path.join('src/pingubot/src/')))
        sys.path.insert(0, os.path.abspath(os.path.join('src/pingubot/third_party/')))
        command = importlib.import_module(f'src.local.butler.{args.command}')

    command.execute(args)


def _setup(submodule_root=None):
    """Set up configs and import paths."""

    if submodule_root:
        os.environ['ROOT_DIR'] = os.path.abspath(f'./src/{submodule_root}')
    else:
        os.environ['ROOT_DIR'] = os.path.abspath(f'.')

    os.environ['PYTHONIOENCODING'] = 'UTF-8'

    sys.path.insert(0, os.path.abspath(os.path.join('src')))
    from src.pingubot.src.bot.system import modules
    modules.fix_module_search_paths(submodule_root)

if __name__ == '__main__':
    main()
