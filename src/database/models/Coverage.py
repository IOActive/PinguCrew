import datetime
from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField, BinaryField, ReferenceField

from src.database.models.TestCase import TestCase


class Coverage(Document):
    """Coverage info."""
    date = DateTimeField()
    fuzzer = StringField()

    # Function coverage information.
    functions_covered = IntField()
    functions_total = IntField()

    # Edge coverage information.
    edges_covered = IntField()
    edges_total = IntField()

    # Corpus size information.
    corpus_size_units = IntField()
    corpus_size_bytes = IntField()
    corpus_location = StringField()

    # Corpus backup information.
    corpus_backup_location = StringField()

    # Quarantine size information.
    quarantine_size_units = IntField()
    quarantine_size_bytes = IntField()
    quarantine_location = StringField()

    # Link to the HTML report.
    html_report_url = BinaryField

    # References
    testcase = ReferenceField(TestCase)
