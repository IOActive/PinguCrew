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
"""Fuzzing engine initialization."""

import importlib

from src.bot import fuzzing
from src.bot.fuzzers.templates.python.PythonTemplateEngine import PythonFuzzerEngine as engine


def run(include_private=True, include_lowercase=False):
    """Initialise builtin fuzzing engines."""
    if include_private:
        engines = fuzzing.ENGINES
    else:
        engines = fuzzing.PUBLIC_ENGINES

    for engine_name in engines:
        try:
            module = f'src.bot.fuzzers.{engine_name}.engine'
            mod = importlib.import_module(module)
            engine.register(engine_name, mod.Engine)
            if include_lowercase and engine_name.lower() != engine_name:
                engine.register(engine_name.lower(), mod.Engine)
        except Exception as e:
              print(e)


