from enum import Enum

from mongoengine import Document, ReferenceField, EnumField, BooleanField, StringField, IntField

from database.models.Job import Job
from database.models.TestCase import TestCase


class TestcaseVariantStatus(Enum):
    PENDING = 0
    REPRODUCIBLE = 1
    FLAKY = 2
    UNREPRODUCIBLE = 3


class TestCaseVariant(Document):
    # Status of the testcase variant (pending, reproducible, unreproducible, etc).
    status = EnumField(TestcaseVariantStatus, default=TestcaseVariantStatus.PENDING)

    # References
    testcase_id = ReferenceField(TestCase)
    job_id = ReferenceField(Job)

    # Revision that the testcase variant was tried against.
    revision = IntField(default=1)

    # Crash type.
    crash_type = StringField(default="")

    # Crash state.
    crash_state = StringField(default="")

    # Bool to indicate if it is a security bug?
    security_flag = BooleanField(default=False)

    # Bool to indicate if crash is similar to original testcase.
    is_similar = BooleanField(default=False)

    # Similar testcase reproducer key (optional). This is set in case we notice a
    # similar crash on another platform.
    reproducer_key = StringField(default="")

    # Platform (e.g. windows, linux, android).
    platform = StringField(default="")
