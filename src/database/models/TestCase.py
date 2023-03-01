from enum import Enum

from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField, \
    BooleanField, BinaryField, ReferenceField, ListField, EnumField, FloatField

from database.models.Fuzzer import Fuzzer
from src.database.models.Job import Job


class Status(Enum):
    PENDING = 'pending'
    ONGOING = 'processed'
    UNREPRODUCIBLE = 'unreproducible'
    DONE = 'done'


class TestCase(Document):
    bug_information = StringField()

    # Testcase file
    test_case = BinaryField()
    fixed = StringField()

    # Did the bug only reproduced once ?
    one_time_crasher_flag = BooleanField()
    comments = StringField()
    # The file on the bot that generated the testcase.
    absolute_path = StringField()
    # Queue to publish tasks
    queue = StringField()
    archived = BooleanField()
    timestamp = DateTimeField()
    status = EnumField(Status, default=Status.PENDING)
    # indicating if cleanup triage needs to be done.
    triaged = BooleanField()
    # Whether testcase has a bug (either bug_information or group_bug_information).
    has_bug_flag = BooleanField()
    open = BooleanField()

    # store paths for various things like original testcase, minimized
    # testcase, etc.
    testcase_path = StringField()
    additional_metadata = StringField()

    # Blobstore keys for various things like original testcase, minimized
    # testcase, etc.
    fuzzed_keys = StringField()
    minimized_keys = StringField()
    minidump_keys = StringField()

    # Minimized argument list.
    minimized_arguments = StringField()

    # Flag indicating if UBSan detection should be disabled. This is needed for
    # cases when ASan and UBSan are bundled in the same build configuration
    # and we need to disable UBSan in some runs to find the potentially more
    # interesting ASan bugs.
    disable_ubsan = BooleanField(default=False)

    # Regression range.
    regression = StringField(default='')

    # Adjusts timeout based on multiplier value.
    timeout_multiplier = FloatField(default=1.0)

    # State representing whether the fuzzed or minimized testcases are archived.
    archive_state = IntField()

    # ASAN redzone size in bytes.
    redzone = IntField(default=128)

    # References
    job_id = ReferenceField(Job)
    fuzzer_id = ReferenceField(Fuzzer)
