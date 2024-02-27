"""Install all required dependencies for running an appengine, a bot, and a
  mapreduce locally."""

from local.butler import appengine
from local.butler import common


def execute(args):
    """Install all required dependencies for running tests, the appengine,
    and the bot."""
    is_reproduce_tool_setup = args.only_reproduce
    common.install_dependencies(packages=["bot", "backend", "frontend"], is_reproduce_tool_setup=is_reproduce_tool_setup)

    # App engine setup is not needed for the reproduce tool.
    #if not is_reproduce_tool_setup:
    #    appengine.symlink_dirs()

    print('Bootstrap successfully finished.')
