from mongoengine import Document
from mongoengine.fields import IntField, ObjectIdField, DateTimeField, StringField


class Statistic(Document):
    job_id = ObjectIdField()
    iteration = IntField()
    runtime = IntField()
    execs_per_sec = IntField()
    date = DateTimeField()
    last_beat_time = DateTimeField()
    status = StringField()
    task_payload = StringField()