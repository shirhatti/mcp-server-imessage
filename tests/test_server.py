import pytest

from mcp_server_imessage.iMessage import Message, iMessageServer


def test_server_creation():
    server = iMessageServer()
    assert server.serverName == "iMessage"


@pytest.mark.local
def test_read_messages():
    server = iMessageServer()
    messages = server.read_messages(1)
    assert isinstance(messages, list)
    if len(messages) > 0:
        assert isinstance(messages[0], Message)
