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
"""Generic helper functions useful in tests."""

import datetime
import io
import os
import unittest

from bot.datastore import data_types
from bot.system import environment

from mockupdb import MockupDB

from frontend import app

CURRENT_TIME = datetime.datetime.utcnow()
EMULATOR_TIMEOUT = 20

# Per-process emulator instances.
_emulators = {}


def create_generic_testcase(created_days_ago=28):
    """Create a simple test case."""
    testcase = data_types.Testcase()

    # Add more values here as needed. Intended to be the bare minimum for what we
    # need to simulate a test case.
    testcase.absolute_path = '/a/b/c/test.html'
    testcase.crash_address = '0xdeadbeef'
    testcase.crash_revision = 1
    testcase.crash_state = 'crashy_function()'
    testcase.crash_stacktrace = testcase.crash_state
    testcase.crash_type = 'fake type'
    testcase.comments = 'Fuzzer: test'
    testcase.fuzzed_keys = 'abcd'
    testcase.minimized_keys = 'efgh'
    testcase.fuzzer_name = 'fuzzer1'
    testcase.open = True
    testcase.one_time_crasher_flag = False
    testcase.job_type = 'test_content_shell_drt'
    testcase.status = 'Processed'
    testcase.timestamp = CURRENT_TIME - datetime.timedelta(days=created_days_ago)
    testcase.project_name = 'project'
    testcase.platform = 'linux'

    return testcase


def entities_equal(entity_1, entity_2, check_key=True):
    """Return a bool on whether two input entities are the same."""
    if check_key:
        return entity_1.key == entity_2.key

    return entity_1.to_dict() == entity_2.to_dict()


def entity_exists(entity):
    """Return a bool on where the entity exists in datastore."""
    return entity.get_by_id(entity.key.id())


def adhoc(func):
    """Mark the testcase as an adhoc. Adhoc tests are NOT expected to run before
    merging and are NOT counted toward test coverage; they are used to test
    tricky situations.

    Another way to think about it is that, if there was no adhoc test, we
    would write a Python script (which is not checked in) to test what we want
    anyway... so, it's better to check in the script.

    For example, downloading a chrome revision (10GB) and
    unpacking it. It can be enabled using the env ADHOC=1."""
    return unittest.skipIf(not environment.get_value('ADHOC', False),
                           'Adhoc tests are not enabled.')(
        func)


def integration(func):
    """Mark the testcase as integration because it depends on network resources
    and/or is slow. The integration tests should, at least, be run before
    merging and are counted toward test coverage. It can be enabled using the
    env INTEGRATION=1."""
    return unittest.skipIf(not environment.get_value('INTEGRATION', False),
                           'Integration tests are not enabled.')(
        func)


def slow(func):
    """Slow tests which are skipped during presubmit."""
    return unittest.skipIf(not environment.get_value('SLOW_TESTS', True),
                           'Skipping slow tests.')(
        func)


def android_device_required(func):
    """Skip Android-specific tests if we cannot run them."""
    reason = None
    if not environment.get_value('ANDROID_SERIAL'):
        reason = 'Android device tests require that ANDROID_SERIAL is set.'
    elif not environment.get_value('INTEGRATION'):
        reason = 'Integration tests are not enabled.'
    elif environment.platform() != 'LINUX':
        reason = 'Android device tests can only run on a Linux host.'

    return unittest.skipIf(reason is not None, reason)(func)


def set_up_pyfakefs(test_self, allow_root_user=True):
    """Helper to set up Pyfakefs."""
    real_cwd = os.path.realpath(os.getcwd())
    config_dir = os.path.realpath(environment.get_config_directory())
    test_self.setUpPyfakefs(allow_root_user=allow_root_user)
    test_self.fs.add_real_directory(config_dir, lazy_read=False)
    os.chdir(real_cwd)


def supported_platforms(*platforms):
    """Decorator for enabling tests only on certain platforms."""

    def decorator(func):  # pylint: disable=unused-argument
        """Decorator."""
        return unittest.skipIf(environment.platform() not in platforms,
                               'Unsupported platform.')(
            func)

    return decorator


class GetDataSourceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.server = MockupDB(auto_ismaster=True, verbose=True)
        self.server.run()
        # create mongo connection to mock server

        app.testing = True
        app.config['MONGO_URI'] = self.server.uri
        self.app = app.test_client()

    @classmethod
    def tearDownClass(self):
        self.server.stop()


MockStdout = io.StringIO  # pylint: disable=invalid-name
