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

"""Constants shared across butler commands."""

import collections
import os
import sys

# Chromedriver related constants.
#CHROMEDRIVER_VERSION_URL = (
#    'https://commondatastorage.googleapis.com/chromedriver/LATEST_RELEASE_101')
#CHROMEDRIVER_DOWNLOAD_PATTERN = (
#    'https://commondatastorage.googleapis.com/chromedriver/{version}/'
#    '{archive_name}')

# Supported Platforms and ABIS (newer to older order).
PLATFORMS = collections.OrderedDict([
    ('windows', 'win_amd64'),
    ('macos', ('macosx_10_14_x86_64', 'macosx_10_9_x86_64',
               'macosx_10_12_x86_64')),
    ('linux', ('manylinux2010_x86_64', 'manylinux1_x86_64')),
])

if sys.version_info.major == 3 and sys.version_info.minor == 7:
  ABIS = {'linux': 'cp37m', 'windows': 'cp37m', 'macos': 'cp37m'}
elif sys.version_info.major == 3 and sys.version_info.minor == 8:
  ABIS = {'linux': 'cp38', 'windows': 'cp38', 'macos': 'cp38'}
elif sys.version_info.major == 3 and sys.version_info.minor == 9:
  ABIS = {'linux': 'cp39', 'windows': 'cp39', 'macos': 'cp39'}
elif sys.version_info.major == 3 and sys.version_info.minor == 10:
  ABIS = {'linux': 'cp10', 'windows': 'cp10', 'macos': 'cp10'}
elif sys.version_info.major == 3 and sys.version_info.minor == 11:
    ABIS = {'linux': 'cp11', 'windows': 'cp11', 'macos': 'cp11'}
elif sys.version_info.major == 3 and sys.version_info.minor == 12:
    ABIS = {'linux': 'cp12', 'windows': 'cp12', 'macos': 'cp12'}
elif sys.version_info.major == 3 and sys.version_info.minor == 13:
    ABIS = {'linux': 'cp13', 'windows': 'cp13', 'macos': 'cp13'}
else:
  raise Exception('Only python versions 3.7-3.12 are supported.')

# Config directory to use for tests.
TEST_CONFIG_DIR = os.path.join('configs')

# Application id for local testing.
TEST_APP_ID = 'test-bot'
TEST_APP_ID_WITH_DEV_PREFIX = 'dev~' + TEST_APP_ID

DEV_APPSERVER_PORT = 8086
DEV_APPSERVER_HOST = 'localhost:' + str(DEV_APPSERVER_PORT)