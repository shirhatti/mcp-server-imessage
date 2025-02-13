from peewee import AutoField, BlobField, BooleanField, ForeignKeyField, IntegerField, TextField

from .base import BaseModel
from .handle import Handle


class Message(BaseModel):
    ROWID = AutoField()
    handle = ForeignKeyField(Handle, backref="messages", null=True, field="ROWID")
    date = IntegerField(null=True)
    text = TextField(null=True)
    attributedBody = BlobField(null=True)
    is_from_me = BooleanField(default=False)
    cache_roomnames = TextField(null=True)

    class Meta:
        table_name = "message"
