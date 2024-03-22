import os
from src.local.butler import appengine, common


def execute(args):
    """Run the server."""
    if not args.skip_install_deps:
        common.install_dependencies(packages=["frontend"])

    # Do this everytime as a past deployment might have changed these.
    appengine.symlink_dirs(src_dir_py=os.path.join('src', 'frontend'))
  
    # Run Web server
    try:
        common.execute(['/bin/bash', '-c', 'npm start'], cwd=os.environ['ROOT_DIR'])
    except KeyboardInterrupt:
        print('Server has been stopped. Exit.')