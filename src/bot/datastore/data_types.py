import re
from datetime import time, datetime
from enum import Enum
from typing import List, Any, Dict

import six
from bson import ObjectId
from pydantic import BaseModel, Field, PrivateAttr

from bot.crash_analysis.stack_parsing.stack_parser import StackFrame
from src.bot.system import environment
from src.bot.utils import json_utils, utils

MISSING_VALUE_STRING = '---'

# Maximum size allowed for an appengine entity type.
# Explicily kept slightly lower than 1 MB.
ENTITY_SIZE_LIMIT = 900000

# Prefix used when a large testcase is stored in the blobstore.
BLOBSTORE_STACK_PREFIX = 'BLOB_KEY='

# List of builtin fuzzers.
BUILTIN_FUZZERS = ['afl', 'libFuzzer']

# Time to look back to find a corpus backup that is marked public.
CORPUS_BACKUP_PUBLIC_LOOKBACK_DAYS = 30

# Marker to indicate end of crash stacktrace. Anything after that is excluded
# from being stored as part of crash stacktrace (e.g. merge content, etc).
CRASH_STACKTRACE_END_MARKER = 'CRASH OUTPUT ENDS HERE'

# Skips using crash state similarity for these types.
CRASH_TYPES_WITH_UNIQUE_STATE = [
    'Missing-library',
    'Out-of-memory',
    'Overwrites-const-input',
    'Timeout',
    # V8 correctness failures use metadata from the fuzz test cases as crash
    # state. This is not suitable for using levenshtein distance for
    # similarity.
    'V8 correctness failure',
]

# Minimum number of unreproducible crashes to see before filing it.
FILE_UNREPRODUCIBLE_TESTCASE_MIN_CRASH_THRESHOLD = 100

# Heartbeat wait interval.
HEARTBEAT_WAIT_INTERVAL = 10 * 60

# FIXME: Move this to configuration.
# List of internal sandboxed data types. This gives a warning on testcase
# uploads on unsandboxed job types.
INTERNAL_SANDBOXED_JOB_TYPES = [
    'linux_asan_chrome_media', 'linux_asan_chrome_mp',
    'linux_asan_chrome_v8_arm', 'mac_asan_chrome', 'windows_asan_chrome'
]

# Time to wait after a report is marked fixed and before filing another similar
# one (hours).
MIN_ELAPSED_TIME_SINCE_FIXED = 2 * 24

# Time to wait for grouping task to finish, before filing the report (hours).
MIN_ELAPSED_TIME_SINCE_REPORT = 4

# Valid name check for fuzzer, job, etc.
NAME_CHECK_REGEX = re.compile(r'^[a-zA-Z0-9_-]+$')

# Regex to match special chars in project name.
SPECIAL_CHARS_REGEX = re.compile('[^a-zA-Z0-9_-]')

# List of supported platforms.
PLATFORMS = [
    'LINUX',
    'ANDROID',
    'CHROMEOS',
    'MAC',
    'WINDOWS',
    'FUCHSIA',
    'ANDROID_KERNEL',
    'ANDROID_AUTO',
]

# Maximum size allowed for an appengine pubsub request.
# Explicily kept slightly lower than 1 MB.
PUBSUB_REQUEST_LIMIT = 900000

# We store at most 3 stacktraces per Testcase entity (original, second, latest).
STACKTRACE_LENGTH_LIMIT = ENTITY_SIZE_LIMIT // 3

# Maximum size allowed for testcase comments.
# 1MiB (maximum Datastore entity size) - ENTITY_SIZE_LIMIT (our limited entity
# size with breathing room), divided by 2 to leave room for other things in the
# entity. This is around 74KB.
TESTCASE_COMMENTS_LENGTH_LIMIT = (1024 * 1024 - ENTITY_SIZE_LIMIT) // 2

# Maximum number of testcase entities to query in one batch.
TESTCASE_ENTITY_QUERY_LIMIT = 256

# Deadlines for testcase filing, closures and deletions (in days).
DUPLICATE_TESTCASE_NO_BUG_DEADLINE = 3
CLOSE_TESTCASE_WITH_CLOSED_BUG_DEADLINE = 14
FILE_CONSISTENT_UNREPRODUCIBLE_TESTCASE_DEADLINE = 14
NOTIFY_CLOSED_BUG_WITH_OPEN_TESTCASE_DEADLINE = 7
UNREPRODUCIBLE_TESTCASE_NO_BUG_DEADLINE = 7
UNREPRODUCIBLE_TESTCASE_WITH_BUG_DEADLINE = 14

# Chromium specific issue state tracking labels.
CHROMIUM_ISSUE_RELEASEBLOCK_BETA_LABEL = 'ReleaseBlock-Beta'
# TODO(ochang): Find some way to remove these.
CHROMIUM_ISSUE_PREDATOR_AUTO_CC_LABEL = 'Test-Predator-Auto-CC'
CHROMIUM_ISSUE_PREDATOR_AUTO_COMPONENTS_LABEL = 'Test-Predator-Auto-Components'
CHROMIUM_ISSUE_PREDATOR_AUTO_OWNER_LABEL = 'Test-Predator-Auto-Owner'
CHROMIUM_ISSUE_PREDATOR_WRONG_COMPONENTS_LABEL = (
    'Test-Predator-Wrong-Components')
CHROMIUM_ISSUE_PREDATOR_WRONG_CL_LABEL = 'Test-Predator-Wrong-CLs'

MISSING_VALUE_STRING = '---'

COVERAGE_INFORMATION_DATE_FORMAT = '%Y-%m-%d'


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")

        return ObjectId(v)

    @classmethod
    def to_python(cls, value):
        """convert type to a python type"""
        return str(value)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class Fuzzer(BaseModel):
    """Represents a fuzzer."""

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Additionally allows '.' and '@' over NAME_CHECK_REGEX.
    VALID_NAME_REGEX: str = re.compile(r'^[a-zA-Z0-9_@.-]+$')

    # Last update time.
    timestamp: datetime = None

    # Fuzzer Name.
    name: str

    # The name of the archive that the user uploaded.
    filename: str

    # String representation of the file size.
    file_size: str

    # Blobstore path or URL for this fuzzer.
    blobstore_path: str

    # Fuzzer's main executable path, relative to root.
    executable_path: str

    # Testcase timeout.
    timeout: int

    # Supported platforms.
    supported_platforms: str

    # Custom script that should be used to launch for this fuzzer.
    launcher_script: str

    # Job types for this fuzzer.
    # jobs: str

    # Max testcases to generate for this fuzzer.
    max_testcases: int

    # Additional environment variables that need to be set for this fuzzer.
    additional_environment_string: str

    # Column specification for stats.
    stats_columns: str = None

    # Helpful descriptions for the stats_columns. In a yaml format.
    stats_column_descriptions: str = None
    # Whether this is a builtin fuzzer.
    builtin: bool

    # Whether this is a differential fuzzer.
    differential: bool

    # Does it run un-trusted content ? Examples including running live sites.
    untrusted_content: bool

    # If this flag is set, fuzzer generates the testcase in the larger directory
    # on disk |FUZZ_INPUTS_DISK|, rather than smaller tmpfs one (FUZZ_INPUTS).
    has_large_testcases: bool = False

    # Result from the last fuzzer run showing the number of testcases generated.
    result: str = ""

    # Last result update timestamp.
    result_timestamp: datetime = None

    # Console output from last fuzzer run.
    console_output: str = ""

    # Return code from last fuzzer run.
    return_code: int = 0

    # Blobstore key for the sample testcase generated by the fuzzer.
    sample_testcase: str = ""

    # Revision number of the fuzzer.
    revision: float = 1.0

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class JobTemplate(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    # Job template name.
    name: str
    # Environment string.
    environment_string: str


# Archive state enums.
class ArchiveStatus(object):
    NONE = 0
    FUZZED = 1
    MINIMIZED = 2
    ALL = FUZZED | MINIMIZED


class Job(BaseModel):
    """Definition of a job type used by the bots."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    project: str
    description: str
    date: datetime
    enabled: bool
    archived: bool
    fuzzing_target: PyObjectId = Field(default_factory=PyObjectId, alias="fuzzing_target")
    owner: PyObjectId = Field(default=None, alias="owner")
    templates: PyObjectId = Field(default=None, alias="template")
    environment_string: str
    platform: str

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

    # def __init__(self, json_job):
    #     self.name = json_job['name']
    #     self.description = json_job['description']
    #     self.date = json_job['date']['$date']
    #     self.enabled = json_job['enabled']
    #     self.archived = json_job['archived']
    #     self.fuzzing_target = json_job['fuzzing_target']['$oid']
    #     self.owner = json_job['owner']
    #     self.platform = json_job['platform']
    #     self.templates = json_job['template']
    #     self.environment_string = json_job['environment_string']

    def get_environment(self):
        """Get the environment as a dict for this job, including any environment
        variables in its template."""
        if not self.templates:
            return environment.parse_environment_definition(self.environment_string)

        job_environment = {}
        for template in self.templates:
            if not template:
                continue

            template_environment = environment.parse_environment_definition(
                template.environment_string)

            job_environment.update(template_environment)

        environment_overrides = environment.parse_environment_definition(
            self.environment_string)

        job_environment.update(environment_overrides)
        return job_environment

    def get_environment_string(self):
        """Get the environment string for this job, including any environment
        variables in its template. Avoid using this if possible."""
        environment_string = ''
        job_environment = self.get_environment()
        for key, value in six.iteritems(job_environment):
            environment_string += '%s = %s\n' % (key, value)

        return environment_string


class FuzzStrategyProbability(BaseModel):
    """Mapping between fuzz strategies and probabilities with which they
  should be selected."""
    strategy_name: str
    probability: float
    engine: PyObjectId = Field(default_factory=PyObjectId, alias="fuzzer_id")


class Status(str, Enum):
    PENDING = 'pending'
    ONGOING = 'processed'
    UNREPRODUCIBLE = 'unreproducible'
    DONE = 'done'


class Crash(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    crash_signal: int = 1
    exploitability: str = ""
    crash_time: datetime
    crash_hash: str = ""
    verified: bool = False
    additional: str = ""
    iteration: int = 0
    # Crash on an invalid read/write.
    crash_type: str = ""
    # Crashing address.
    crash_address: str = ""
    # First x stack frames.
    crash_state: str = ""
    # Complete stacktrace.
    crash_stacktrace: str = ""
    # Regression range.
    regression: str = ""
    # Security severity of the bug.
    security_severity: int = None
    # The file on the bot that generated the testcase.
    absolute_path: str = ""
    # Security_flag
    security_flag: bool = False
    reproducible_flag: bool = False
    return_code: str = '-1'
    gestures: List[str] = None
    resource_list: List[str] = None
    fuzzing_strategy: dict = {}
    should_be_ignored: bool = False
    application_command_line: str = ""
    unsymbolized_crash_stacktrace: str = ""
    crash_frame: List[List[StackFrame]] = None
    crash_info: str = None
    # Optional. Revision that we discovered the crash in.
    crash_revision: int = 1

    # References
    testcase_id: PyObjectId = Field(default_factory=PyObjectId, alias="testcase_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True  # required for the _id
        json_encoders = {ObjectId: str}


class Testcase(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    bug_information: str = ""
    # Testcase file
    test_case: bytes
    fixed: bool = False
    # Did the bug only reproduced once ?
    one_time_crasher_flag: bool
    comments: str = ""
    # The file on the bot that generated the testcase.
    absolute_path: str = "/"
    # Queue to publish tasks
    queue: str = ""
    archived: bool = False
    timestamp: datetime
    status: Status = Status.PENDING
    # indicating if cleanup triage needs to be done.
    triaged: bool = False
    # Whether testcase has a bug (either bug_information or group_bug_information).
    has_bug_flag: bool = False
    open: bool = True
    # State representing whether the fuzzed or minimized testcases are archived.
    archive_state: int = 0
    # store paths for various things like original testcase, minimized
    # testcase, etc.
    testcase_path: str = ""
    minimized_keys: str = ""
    minidump_keys: str = ""
    fuzzed_keys: str = ""

    # Metadata Cache
    additional_metadata: str = ""

    # Flag indicating if UBSan detection should be disabled. This is needed for
    # cases when ASan and UBSan are bundled in the same build configuration
    # and we need to disable UBSan in some runs to find the potentially more
    # interesting ASan bugs.
    disable_ubsan: bool = False

    # Minimized argument list.
    minimized_arguments: str = ""

    # Regression range.
    regression: str = ""

    # Adjusts timeout based on multiplier value.
    timeout_multiplier: float = 1.0

    # ASAN redzone size in bytes.
    redzone: int = 128

    # References
    job_id: PyObjectId = Field(default_factory=PyObjectId, alias="job_id")
    fuzzer_id: PyObjectId = Field(default_factory=PyObjectId, alias="fuzzer_id")

    __metadata_cache__: Dict[str, int] = PrivateAttr(default_factory=dict)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True  # required for the _id
        json_encoders = {ObjectId: str}

    def _ensure_metadata_is_cached(self):
        """Ensure that the metadata for this has been cached."""
        if hasattr(self, '__metadata_cache__'):
            return

        try:
            cache = json_utils.loads(self.additional_metadata)
        except (TypeError, ValueError):
            cache = {}

        setattr(self, '__metadata_cache__', cache)

    def get_metadata(self, key=None, default=None):
        """Get metadata for a test case. Slow on first access."""
        self._ensure_metadata_is_cached()

        # If no key is specified, return all metadata.
        if not key:
            return self.__metadata_cache__

        try:
            return self.__metadata_cache__[key]
        except KeyError:
            return default

    def set_metadata(self, key, value, update_testcase=True):
        """Set metadata for a test case."""
        self._ensure_metadata_is_cached()
        self.__metadata_cache__[key] = value

        self.additional_metadata = json_utils.dumps(self.__metadata_cache__)

    def delete_metadata(self, key, update_testcase=True):
        """Remove metadata key for a test case."""
        self._ensure_metadata_is_cached()

        # Make sure that the key exists in cache. If not, no work to do here.
        if key not in self.__metadata_cache__:
            return

        del self.__metadata_cache__[key]
        self.additional_metadata = json_utils.dumps(self.__metadata_cache__)


# Task state string mappings.
class TaskState(object):
    STARTED = 'started'
    WIP = 'in-progress'
    FINISHED = 'finished'
    ERROR = 'errored out'
    NA = ''


class FuzzTarget(BaseModel):
    """Mapping between fuzz target and jobs with additional metadata for
      selection."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Selected Fuzzer
    fuzzer_engine: str

    # Project name.
    project: str

    # Binary name.
    binary: str

    # Target File
    # fuzzing_target: bytes

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True  # required for the _id
        json_encoders = {ObjectId: str}

    def fully_qualified_name(self):
        """Get the fully qualified name for this fuzz target."""
        return fuzz_target_fully_qualified_name(self.fuzzer_engine, self.project,
                                                self.binary)

    def project_qualified_name(self):
        """Get the name qualified by project."""
        return fuzz_target_project_qualified_name(self.project, self.binary)


def fuzz_target_fully_qualified_name(engine, project, binary):
    """Get a fuzz target's fully qualified name."""
    return engine + '_' + fuzz_target_project_qualified_name(project, binary)


def normalized_name(name):
    """Return normalized name with special chars like slash, colon, etc normalized
  to hyphen(-). This is important as otherwise these chars break local and cloud
  storage paths."""
    return SPECIAL_CHARS_REGEX.sub('-', name).strip('-')


def fuzz_target_project_qualified_name(project, binary):
    """Get a fuzz target's project qualified name."""
    binary = normalized_name(binary)
    if not project:
        return binary

    if project == utils.default_project_name():
        # Don't prefix with project name if it's the default project.
        return binary

    normalized_project_prefix = normalized_name(project) + '_'
    if binary.startswith(normalized_project_prefix):
        return binary

    return normalized_project_prefix + binary


class FuzzTargetsCount(BaseModel):
    """Fuzz targets count for every job. Key IDs are the job name."""
    id: str
    count: int


def fuzz_target_job_key(fuzz_target_name, job):
    """Return the key for FuzzTargetJob."""
    return '{}/{}'.format(fuzz_target_name, job)


class FuzzTargetJob(BaseModel):
    """Mapping between fuzz target and jobs with additional metadata for
      selection."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Fully qualified fuzz target.
    fuzzing_target: PyObjectId = Field(default_factory=PyObjectId, alias="fuzzing_target")

    # Job this target ran as.
    job: PyObjectId = Field(default_factory=PyObjectId, alias="job")

    # Engine this ran as.
    engine: str

    # Relative frequency with which to select this fuzzer.
    weight: float = 1.0

    # Approximate last time this target was run.
    last_run: datetime

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True  # required for the _id
        json_encoders = {ObjectId: str}


class BuildMetadata(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    """Metadata associated with a particular archived build."""
    # Job type that this build belongs to.
    job: PyObjectId = Field(default_factory=PyObjectId, alias="job")

    # Revision of the build.
    revision: int

    # Good build or bad build
    bad_build: bool = False

    # Stdout and stderr.
    console_output: str

    # Bot name.
    bot_name: str

    # Symbol data.
    symbols: str

    # Creation timestamp.
    timestamp: datetime


# Build state.
class BuildState(object):
    UNMARKED = 0
    GOOD = 1
    BAD = 2


class DataBundle(BaseModel):
    """Represents a data bundle associated with a fuzzer."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    VALID_NAME_REGEX: str

    # The data bundle's name (important for identifying shared bundles).
    name: str

    # Name of cloud storage bucket on Minio.
    bucket_name: str

    # Data bundle's source (for accountability).
    # TODO(ochang): Remove.
    source: str

    # If data bundle can be unpacked locally or needs nfs.
    is_local: bool = True

    # Creation timestamp.
    timestamp: datetime

    # Whether or not bundle should be synced to worker instead.
    # Fuzzer scripts are usually run on trusted hosts, so data bundles are synced
    # there. In libFuzzer's case, we want the bundle to be on the same machine as
    # where the libFuzzer binary will run (untrusted).
    sync_to_worker: bool = False


def coverage_information_date_to_string(date):
    """Returns string representation of the date in a format used for coverage."""
    return date.strftime(COVERAGE_INFORMATION_DATE_FORMAT)


class TestcaseVariantStatus(int, Enum):
    PENDING = 0
    REPRODUCIBLE = 1
    FLAKY = 2
    UNREPRODUCIBLE = 3


class TestcaseVariant(BaseModel):
    """Represent a testcase variant on another job (another platform / sanitizer / config)."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    # Testcase ID of the testcase for which the variant is being evaluated.
    testcase_id: PyObjectId = Field(default_factory=PyObjectId, alias="testcase_id")

    # Status of the testcase variant (pending, reproducible, unreproducible, etc).
    status: TestcaseVariantStatus = TestcaseVariantStatus.PENDING

    # Job type for the testcase variant.
    job_id: PyObjectId = Field(default_factory=PyObjectId, alias="job_id")

    # Revision that the testcase variant was tried against.
    revision: int = 0

    # Crash type.
    crash_type: str = ""

    # Crash state.
    crash_state: str = ""

    # Bool to indicate if it is a security bug?
    security_flag: bool = False

    # Bool to indicate if crash is similar to original testcase.
    is_similar: bool = False

    # Similar testcase reproducer key (optional). This is set in case we notice a
    # similar crash on another platform.
    reproducer_key: str = ""

    # Platform (e.g. windows, linux, android).
    platform: str = ""

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True  # required for the _id
        json_encoders = {ObjectId: str}


class Trial(BaseModel):
    """Trials for specific binaries."""
    # App name that this trial is applied to. E.g. "d8" or "chrome".
    app_name: str

    # Chance to select this set of arguments. Zero to one.
    probability: float

    # Additional arguments to apply if selected.
    app_args: str
