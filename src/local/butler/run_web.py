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

import os
from src.local.butler import appengine, common


def execute(args):
    """Run the server."""
    if not args.skip_install_deps:
        common.install_dependencies(packages=["frontend"])
        
    # Do this everytime as a past deployment might have changed these.
    appengine.sync_dirs(src_dir_py=os.path.join('src', 'frontend'), sub_configs=['frontend'])
    
    # For testing as CRA is a pain to load from outside src
    appengine.sync_dirs(src_dir_py=os.path.join('src', 'frontend', 'src'), sub_configs=['frontend'])
  
    # Run Web server
    try:
        common.execute(['/bin/bash', '-c', 'npm start'], cwd=os.environ['ROOT_DIR'])
    except KeyboardInterrupt:
        print('Server has been stopped. Exit.')