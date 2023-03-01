from flask_security import UserMixin
from src.database.database import db
from src.database.models.Role import Role


class User(db.Document, UserMixin):
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    registration_date = db.DateTimeField()
    api_key = db.StringField(max_length=255)
    roles = db.ListField(db.ReferenceField(Role), default=[])
