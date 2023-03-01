from enum import Enum

from mongoengine import Document
from mongoengine.fields import StringField, DateTimeField, EnumField


class TaskStatus(Enum):
    STARTED = 'started'
    WIP = 'in-progress'
    FINISHED = 'finished'
    ERROR = 'errored out'
    NA = 'NA'


class Bot(Document):
    """Bot health metadata."""
    # Name of the bot.
    bot_name = StringField()

    # Time of the last heartbeat.
    last_beat_time = DateTimeField()

    # Task payload containing information on current task execution.
    task_payload = StringField()

    # Expected end time for task.
    task_end_time = DateTimeField()

    # Tasks status
    task_status = EnumField(TaskStatus, default=TaskStatus.NA)

    # Platform (esp important for Android platform for OS version).
    platform = StringField()
