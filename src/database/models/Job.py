from mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, \
    BooleanField, ReferenceField, IntField

from src.database.models.FuzzTarget import FuzzTarget
from src.database.models.JobTemplate import JobTemplate
from src.database.models.User import User


class Job(Document):
    # Job type name.
    name = StringField()
    # Description of the job.
    description = StringField()
    # Project name.
    project = StringField()
    # Creation date
    date = DateTimeField()
    # Enable state
    enabled = BooleanField()
    # Archive state
    archived = BooleanField()
    # Job Owner
    owner = ReferenceField(User, blank=True, null=True, default=None)
    # The platform that this job can run on.
    platform = StringField()
    # Job environment string.
    environment_string = StringField(blank=True, null=True, default=None)
    # Template to use, if any.
    template = ReferenceField(JobTemplate, blank=True, null=True, default=None)
    # Blobstore path of the custom binary for this job.
    custom_binary_path = StringField(blank=True, null=True, default=None)
    # Filename for the custom binary.
    custom_binary_filename = StringField(blank=True, null=True, default=None)
    # Revision of the custom binary.
    custom_binary_revision = IntField(blank=True, null=True, default=1)
