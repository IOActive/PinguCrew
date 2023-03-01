from enum import Enum

from mongoengine import Document, StringField, FloatField


class Trial(Document):
    # App name that this trial is applied to. E.g. "d8" or "chrome".
    app_name = StringField(required=True)

    # Chance to select this set of arguments. Zero to one.
    probability = FloatField(default=1.0)

    # Additional arguments to apply if selected.
    app_args = StringField(default="")
