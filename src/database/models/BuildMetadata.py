import datetime
from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField, BinaryField, ReferenceField, BooleanField

from src.database.models.Job import Job
from src.database.models.TestCase import TestCase


class BuildMetadata(Document):
    """Metadata associated with a particular archived build."""
    # Job type that this build belongs to.
    job = ReferenceField(Job, blank=True, null=True, default=None)

    # Revision of the build.
    revision = IntField()

    # Good build or bad build.
    bad_build = BooleanField(default=False)

    # Stdout and stderr.
    console_output = StringField(blank=True, null=True, default=None)

    # Bot name.
    bot_name = StringField()

    # Symbol data.
    symbols = StringField(blank=True, null=True, default=None)

    # Creation timestamp.
    timestamp = DateTimeField()

