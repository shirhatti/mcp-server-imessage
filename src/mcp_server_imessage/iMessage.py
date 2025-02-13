import os
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass, fields
from datetime import datetime
from typing import Any, Optional, cast

from peewee import DoesNotExist as PeeweeDoesNotExist
from playhouse.sqlite_ext import SqliteExtDatabase

from .AddressBook import AddressBook
from .errors import MessageNotFoundException
from .models import BaseModel, Chat, Handle, Message
from .SnowflakeComponents import SnowflakeDecoder


@dataclass
class MessageDTO:
    rowid: int
    datetime: datetime
    body: str
    phone_number: str
    is_from_me: bool
    cache_roomname: str
    group_chat_name: str | None
    full_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Dynamically generate dictionary from dataclass fields"""
        result: dict[str, Any] = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if field.type == datetime:
                result[field.name] = value.isoformat() if value else None
            else:
                result[field.name] = value
        return result


class iMessageServer:
    serverName = "iMessage"

    def __init__(
        self, db_location: str = "~/Library/Messages/chat.db", address_book: Optional[AddressBook] = None
    ) -> None:
        if db_location == ":memory:":
            self.db_location = ":memory:"
            self.db = SqliteExtDatabase(
                ":memory:",
                pragmas={
                    "journal_mode": "memory",
                    "cache_size": -1024 * 64,  # 64MB cache
                },
            )
        else:
            self.db_location = os.path.expanduser(db_location)
            self.db = SqliteExtDatabase(self.db_location)

        self.address_book = address_book
        # Initialize models before attempting any database operations
        self._bind_models()
        # Only create tables for in-memory database
        if db_location == ":memory:":
            self._create_tables()

    def _bind_models(self) -> None:
        """Bind all models to the database"""
        models = [Message, Handle, Chat]
        for model in models:
            model.bind(self.db)
        BaseModel.bind(self.db)

    def _create_tables(self) -> None:
        """Create database tables if they don't exist"""
        with self.connection():
            models = [Message, Handle, Chat]
            self.db.create_tables(models, safe=True)

    @contextmanager
    def connection(self) -> Iterator[SqliteExtDatabase]:
        """Context manager for database connections"""
        if self.db.is_closed():
            self.db.connect()
        try:
            yield self.db
        finally:
            pass  # Keep connection open until explicitly closed

    def __del__(self) -> None:
        """Close database connection when object is destroyed"""
        with suppress(Exception):
            if hasattr(self, "db") and not self.db.is_closed():
                self.db.close()

    def get_chat_mapping(self) -> dict[str, str]:
        with self.connection():
            return {
                str(chat.room_name): str(chat.display_name)
                for chat in Chat.select(Chat.room_name, Chat.display_name)
                if chat.room_name is not None
            }

    def get_group_chat_names(self) -> list[str]:
        with self.connection():
            query = Message.select(Message.cache_roomnames).where(Message.cache_roomnames.is_null(False)).distinct()
            return [str(msg.cache_roomnames) for msg in query]

    def read_messages(self, n: Optional[int] = 10) -> list[MessageDTO]:
        with self.connection():
            query = Message.select(Message, Handle).left_outer_join(Handle).order_by(Message.date.desc())

            if n is not None:
                query = query.limit(n)

            messages = []
            for db_msg in query:
                message = self._create_message_from_model(db_msg)
                if message.body is not None:
                    messages.append(message)

            return messages

    def _process_message_body(self, text: Optional[str], attributed_body: Optional[bytes]) -> Optional[str]:
        if text:
            return text
        if not attributed_body:
            return None

        try:
            text = attributed_body.decode("utf-8", errors="replace")
            if "NSNumber" in text:
                text = text.split("NSNumber")[0]
                if "NSString" in text:
                    text = text.split("NSString")[1]
                    if "NSdictionary" in text:
                        text = text.split("NSdictionary")[0]
                        return text[6:-12]
        except (UnicodeDecodeError, AttributeError):
            return None
        return None

    def _create_message_from_model(self, db_msg: Message) -> MessageDTO:
        try:
            phone_number = "Me" if db_msg.handle is None else db_msg.handle.id
        except PeeweeDoesNotExist:
            phone_number = str(db_msg.handle) if db_msg.handle else "Me"

        full_name = None
        if self.address_book and not db_msg.is_from_me and phone_number != "Me":
            contact = self.address_book.get_contact_by_phone(phone_number)
            if contact:
                full_name = contact.full_name

        body = self._process_message_body(
            str(db_msg.text) if db_msg.text else None, bytes(db_msg.attributedBody) if db_msg.attributedBody else None
        )

        mapping = self.get_chat_mapping()
        mapped_name = mapping.get(str(db_msg.cache_roomnames))

        # Cast field values to their expected types
        rowid = cast(int, db_msg.ROWID)
        date_val = cast(int, db_msg.date) if db_msg.date else None
        datetime_val = SnowflakeDecoder.decode(date_val).datetime_utc if date_val else datetime.now()

        return MessageDTO(
            rowid=rowid,
            datetime=datetime_val,
            body=str(body) if body else "",
            phone_number=phone_number,
            is_from_me=bool(db_msg.is_from_me),
            cache_roomname=str(db_msg.cache_roomnames) if db_msg.cache_roomnames else "",
            group_chat_name=mapped_name,
            full_name=full_name,
        )

    def get_message_by_id(self, row_id: str) -> MessageDTO:
        with self.connection():
            try:
                message = Message.select(Message, Handle).left_outer_join(Handle).where(row_id == Message.ROWID).get()
                return self._create_message_from_model(message)
            except PeeweeDoesNotExist as err:
                raise MessageNotFoundException() from err

    def get_conversation_by_number(self, phone_number: str) -> list[MessageDTO]:
        with self.connection():
            query = (
                Message.select(Message, Handle)
                .left_outer_join(Handle)
                .where(Handle.id == phone_number)
                .order_by(Message.date.desc())
            )
            return [self._create_message_from_model(msg) for msg in query]

    def get_group_chat_by_id(self, cache_roomnames: str) -> list[MessageDTO]:
        with self.connection():
            query = (
                Message.select(Message, Handle)
                .left_outer_join(Handle)
                .where(Message.cache_roomnames == cache_roomnames)
                .order_by(Message.date.desc())
            )
            return [self._create_message_from_model(msg) for msg in query]

    def get_received_messages(self, limit: int = 100) -> list[MessageDTO]:
        with self.connection():
            query = (
                Message.select(Message, Handle)
                .left_outer_join(Handle)
                .where(not Message.is_from_me)
                .order_by(Message.date.desc())
                .limit(limit)
            )
            return [self._create_message_from_model(msg) for msg in query]

    def get_sent_messages(self, limit: int = 100) -> list[MessageDTO]:
        with self.connection():
            query = (
                Message.select(Message, Handle)
                .left_outer_join(Handle)
                .where(Message.is_from_me)
                .order_by(Message.date.desc())
                .limit(limit)
            )
            return [self._create_message_from_model(msg) for msg in query]
