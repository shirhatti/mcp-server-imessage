import os
import sqlite3
from dataclasses import dataclass

__all__ = ["iMessageServer", "Message"]


@dataclass
class Message:
    rowid: int
    date: int
    body: str
    phone_number: str
    is_from_me: bool
    cache_roomname: str
    group_chat_name: str | None


class iMessageServer:
    serverName = "iMessage"

    def __init__(self, db_location: str = "~/Library/Messages/chat.db") -> None:
        self.db_location = os.path.expanduser(db_location)
        self.connection = sqlite3.connect(self.db_location)

    def __del__(self) -> None:
        if hasattr(self, "connection"):
            self.connection.close()

    def get_chat_mapping(self) -> dict[str, str]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT room_name, display_name FROM chat")
        result_set = cursor.fetchall()

        mapping = dict(result_set)
        return mapping

    def read_messages(self, n: int = 10, self_number: str = "Me") -> list[Message]:
        cursor = self.connection.cursor()

        query = """
        SELECT message.ROWID, message.date, message.text, message.attributedBody, handle.id, message.is_from_me, message.cache_roomnames
        FROM message
        LEFT JOIN handle ON message.handle_id = handle.ROWID
        """

        if n is not None:
            query += f" ORDER BY message.date DESC LIMIT {n}"

        results = cursor.execute(query).fetchall()
        messages = []

        for result in results:
            rowid, date, text, attributed_body, handle_id, is_from_me, cache_roomname = result

            phone_number = self_number if handle_id is None else handle_id

            if text is not None:
                body = text
            elif attributed_body is None:
                continue
            else:
                attributed_body = attributed_body.decode("utf-8", errors="replace")

                if "NSNumber" in str(attributed_body):
                    attributed_body = str(attributed_body).split("NSNumber")[0]
                    if "NSString" in attributed_body:
                        attributed_body = str(attributed_body).split("NSString")[1]
                        if "NSDictionary" in attributed_body:
                            attributed_body = str(attributed_body).split("NSDictionary")[0]
                            attributed_body = attributed_body[6:-12]
                            body = attributed_body

            mapping = self.get_chat_mapping()

            try:
                mapped_name = mapping[cache_roomname]
            except KeyError:
                mapped_name = None

            messages.append(
                Message(
                    rowid=rowid,
                    date=date,
                    body=body,
                    phone_number=phone_number,
                    is_from_me=is_from_me,
                    cache_roomname=cache_roomname,
                    group_chat_name=mapped_name,
                )
            )

        return messages
