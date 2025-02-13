from peewee import TextField

from .base import BaseModel


class Chat(BaseModel):
    guid = TextField(null=True)
    room_name = TextField(null=True)
    display_name = TextField(null=True)

    class Meta:
        table_name = "chat"
