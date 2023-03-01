import re

from mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, \
    BooleanField, ReferenceField, IntField, ListField

from src.database.models.FuzzTarget import FuzzTarget
from src.database.models.JobTemplate import JobTemplate
from src.database.models.User import User


class DataBundle(Document):
    VALID_NAME_REGEX = StringField(blank=True, null=True, default="")
    # The data bundle's name (important for identifying shared bundles).
    name = StringField()

    # Name of cloud storage bucket on GCS.
    bucket_name = StringField()

    # Data bundle's source (for accountability).
    source = StringField(blank=True, null=True, default="")

    # If data bundle can be unpacked locally or needs nfs.
    is_local = BooleanField(default=True)

    # Creation timestamp.
    timestamp = DateTimeField()

    # Whether or not bundle should be synced to worker instead.
    # Fuzzer scripts are usually run on trusted hosts, so data bundles are synced
    # there. In libFuzzer's case, we want the bundle to be on the same machine as
    # where the libFuzzer binary will run (untrusted).
    sync_to_worker = BooleanField(default=False)
