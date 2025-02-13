from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, ListItem, ListView, Static

from mcp_server_imessage.AddressBook import AddressBook
from mcp_server_imessage.iMessage import MessageDTO, iMessageServer


class MessageListItem(ListItem):
    def __init__(self, message: MessageDTO):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        date_str = self.message.datetime.strftime("%H:%M") if self.message.datetime else "Unknown"
        sender = self.message.full_name or self.message.phone_number
        direction = "→" if self.message.is_from_me else "←"
        body = self.message.body or "(No message content)"
        yield Static(f"[{date_str}] {direction} {sender}: {body[:50]}...")


class MessageViewer(Static):
    def __init__(self):
        super().__init__("")
        self.current_message = None

    def show_message(self, message: MessageDTO):
        self.current_message = message
        date_str = message.datetime.strftime("%Y-%m-%d %H:%M") if message.datetime else "Unknown"
        sender = message.full_name or message.phone_number
        direction = "Sent to" if message.is_from_me else "From"
        body = message.body or "(No message content)"
        self.update(f"""{direction}: {sender}
Date: {date_str}
Service: iMessage

{body}""")


class iMessageTUI(App):
    CSS = """
    ListView {
        width: 100%;
        height: 50%;
        border: solid green;
        scrollbar-gutter: stable;
    }

    MessageViewer {
        width: 100%;
        height: 50%;
        border: solid blue;
        overflow: auto;
        padding: 1 2;
    }

    Static {
        width: 100%;
        text-align: left;
        padding: 0 1;
    }

    ListItem {
        padding: 0;
    }

    ListItem:focus {
        background: $accent;
        color: $text;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("q", "quit", "Quit"),
        Binding("j", "move_down", "Down"),
        Binding("k", "move_up", "Up"),
    ]

    def __init__(self):
        super().__init__()
        self.book = AddressBook()
        self.server = iMessageServer(address_book=self.book)
        self.messages = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView()
        yield MessageViewer()
        yield Footer()

    def on_mount(self):
        self.messages = self.server.read_messages(50)  # Load last 50 messages
        list_view = self.query_one(ListView)
        for message in self.messages:
            list_view.append(MessageListItem(message))

    def on_list_view_selected(self, event):
        message_viewer = self.query_one(MessageViewer)
        message_viewer.show_message(event.item.message)

    def action_move_down(self):
        list_view = self.query_one(ListView)
        current = list_view.index
        if current < len(self.messages) - 1:
            list_view.index = current + 1

    def action_move_up(self):
        list_view = self.query_one(ListView)
        current = list_view.index
        if current > 0:
            list_view.index = current - 1


def main():
    app = iMessageTUI()
    app.run()


if __name__ == "__main__":
    main()
