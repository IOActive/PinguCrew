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

"""App Engine helpers."""

from distutils import spawn
import os
import shutil

from local.butler import common
from local.butler import constants

SRC_DIR_PY = os.path.join('src', 'backend')


def _add_env_vars_if_needed(yaml_path, additional_env_vars):
    """Add environment variables to yaml file if necessary."""
    # Defer imports since our python paths have to be set up first.
    import yaml

    from pingu_sdk.config import project_config

    env_values = project_config.ProjectConfig().get('env')
    if additional_env_vars:
        env_values.update(additional_env_vars)

    if not env_values:
        return

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or 'service' not in data:
        # Not a service.
        return

    data.setdefault('env_variables', {}).update(env_values)
    with open(yaml_path, 'w') as f:
        yaml.safe_dump(data, f)


def copy_yamls_and_preprocess(paths, additional_env_vars=None):
    """Copy paths to appengine source directories since they reference sources
  and otherwise, deployment fails."""
    rebased_paths = []
    for path in paths:
        target_filename = os.path.basename(path)
        rebased_path = os.path.join(SRC_DIR_PY, target_filename)

        # Remove target in case it's a symlink, since shutil.copy follows symlinks.
        if os.path.exists(rebased_path):
            os.remove(rebased_path)
        shutil.copy(path, rebased_path)
        os.chmod(rebased_path, 0o600)

        _add_env_vars_if_needed(rebased_path, additional_env_vars)
        rebased_paths.append(rebased_path)

    return rebased_paths

def sync_dirs(src_dir_py, sub_configs):
    """Symlink folders for use on appengine."""
    syc_config_dir(src_dir_py, sub_configs)


def build_templates():
    """Build template files used in appengine."""
    common.execute('python polymer_bundler.py', cwd='local')


def syc_config_dir(src_dir_py, sub_configs):
    """Symlink config directory in appengine directory."""
    if os.path.exists(os.path.join(src_dir_py, 'config')):
        shutil.rmtree(os.path.join(src_dir_py, 'config'))
        
    os.mkdir(os.path.join(src_dir_py, 'config'))
    config_dir = os.getenv('CONFIG_DIR_OVERRIDE', constants.TEST_CONFIG_DIR)

    for sub_config in sub_configs:  
        shutil.copytree(
            src=os.path.join(config_dir, sub_config),
            dst=os.path.join(src_dir_py, 'config', sub_config)
        )
    


def region_from_location(location):
    """Convert an app engine location ID to a region."""
    if not location[-1].isdigit():
        # e.g. us-central -> us-central1
        location += '1'

    return location


def region(project):
    """Get the App Engine region."""
    return_code, location = common.execute(
        'gcloud app describe --project={project} '
        '--format="value(locationId)"'.format(project=project))
    if return_code:
        raise RuntimeError('Could not get App Engine region')

    return region_from_location(location.strip().decode('utf-8'))
