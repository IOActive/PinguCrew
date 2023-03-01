from mongoengine import Document
from mongoengine.fields import StringField, ReferenceField

from database.models.Fuzzer import Fuzzer


class FuzzTarget(Document):
    # Selected Fuzzer
    fuzzer_engine = ReferenceField(Fuzzer)
    # Target File
    project = StringField()
    # Binary name.
    binary = StringField()

