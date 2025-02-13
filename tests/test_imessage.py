import pytest

from mcp_server_imessage.iMessage import MessageDTO, iMessageServer
from mcp_server_imessage.models import Handle
from mcp_server_imessage.models import Message as Message


@pytest.fixture
def imessage_server():
    server = iMessageServer(db_location=":memory:")
    return server


def test_read_messages_empty(imessage_server):
    messages = imessage_server.read_messages()
    assert isinstance(messages, list)
    assert len(messages) == 0


def test_create_and_read_message(imessage_server):
    # Create a test handle
    handle = Handle.create(id="+1234567890", uncanonicalized_id="+1 (234) 567-890")

    # Create a test message and store reference for cleanup if needed
    Message.create(
        text="Hello, world!",
        is_from_me=False,
        date=1738899785633,  # Example timestamp
        handle=handle,
        cache_roomnames=None,
    )

    # Read messages
    messages = imessage_server.read_messages()
    assert len(messages) == 1

    message = messages[0]
    assert isinstance(message, MessageDTO)
    assert message.body == "Hello, world!"
    assert message.phone_number == "+1234567890"
    assert not message.is_from_me
