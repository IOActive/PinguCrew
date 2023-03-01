from mongoengine import Document
from mongoengine.fields import IntField, StringField, DateTimeField, \
    BooleanField, BinaryField, ReferenceField

from src.database.models.FuzzTarget import FuzzTarget
from src.database.models.User import User


class JobTemplate(Document):
    name = StringField()
    environment_string = StringField()