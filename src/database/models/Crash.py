import datetime
from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField, \
    BooleanField, ObjectIdField, BinaryField, ListField, ReferenceField, DictField

from src.database.models.TestCase import TestCase


class Crash(Document):
    crash_signal = IntField()
    exploitability = StringField()
    crash_time = DateTimeField(default=datetime.datetime.now())
    crash_hash = StringField()
    verified = BooleanField()
    additional = StringField()
    #test_case = BinaryField()
    iteration = IntField()
    # Crash on an invalid read/write.
    crash_type = StringField()
    # Crashing address.
    crash_address = StringField()
    # First x stack frames.
    crash_state = StringField()
    # Complete stacktrace.
    crash_stacktrace = BinaryField()
    # Regression range.
    regression = StringField()
    # Security severity of the bug.
    security_severity = IntField()
    # The file on the bot that generated the testcase.
    absolute_path = StringField()
    # Security_flag
    security_flag = BooleanField()
    reproducible_flag = BooleanField()
    return_code = StringField()
    gestures = ListField(StringField(), default=list)
    resource_list = ListField(StringField(), default=list)
    fuzzing_strategy = DictField()
    should_be_ignored = BooleanField()
    application_command_line = StringField()
    unsymbolized_crash_stacktrace = BinaryField()
    crash_frame = ListField(ListField(StringField(), default=list), default=list)
    crash_info = StringField()
    # Optional. Revision that we discovered the crash in.
    crash_revision = IntField(default=1)
    # References
    testcase_id = ReferenceField(TestCase)


