from mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, \
    ReferenceField, FloatField

from database.models.Fuzzer import Fuzzer
from src.database.models.FuzzTarget import FuzzTarget
from src.database.models.Job import Job


class FuzzTargetJob(Document):
    # Fully qualified fuzz target name.
    fuzzing_target = ReferenceField(FuzzTarget, blank=True, null=True, default=None)

    # Job this target ran as.
    job = ReferenceField(Job, blank=True, null=True, default=None)

    # Engine this ran as.
    engine = ReferenceField(Fuzzer)

    # Relative frequency with which to select this fuzzer.
    weight = FloatField(default=1.0)

    # Approximate last time this target was run.
    last_run = DateTimeField()
