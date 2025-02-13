import os
import platform

import pytest

from mcp_server_imessage.AddressBook import AddressBook


def test_addressbook_creation():
    if platform.system() != "Darwin":
        with pytest.raises(NotImplementedError):
            AddressBook()
    else:
        book = AddressBook()
        assert hasattr(book, "store")
        assert hasattr(book, "keys_to_fetch")


@pytest.mark.skipif(
    platform.system() != "Darwin" or "CI" in os.environ, reason="Test runs only on macOS and not in CI environment"
)
def test_get_contact_by_phone():
    book = AddressBook()
    result = book.get_contact_by_phone("+1234567890")
    assert result is None
