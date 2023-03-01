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
"""Helper functions related to fuzz target entities."""
from src.bot.datastore import data_types, data_handler


def get_fuzz_targets_for_target_jobs(target_jobs):
    """Return corresponding FuzzTargets for the given FuzzTargetJobs."""
    fuzz_targets = []
    for target_job in target_jobs:
        fuzz_target = data_handler.get_fuzz_target_by_id(target_job.fuzzing_target)
        fuzz_targets.append(fuzz_target)
    return fuzz_targets


def get_fuzz_target_jobs(engine=None,
                         job=None):
    """Return a Datastore query for fuzz target to job mappings."""

    if job:
        fuzz_target_jobs = data_handler.get_fuzz_target_job_by_job(job_id=job)
        return fuzz_target_jobs

    elif engine:
        fuzz_target_jobs = data_handler.get_fuzz_target_job_by_engine(engine=engine)
        return fuzz_target_jobs




