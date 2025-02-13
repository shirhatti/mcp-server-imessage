from peewee import AutoField, TextField

from .base import BaseModel


class Handle(BaseModel):
    ROWID = AutoField()  # Changed from TextField to AutoField
    id = TextField(null=True)
    uncanonicalized_id = TextField(null=True)

    class Meta:
        table_name = "handle"
