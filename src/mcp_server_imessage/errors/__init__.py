"""Common exceptions used across the application."""


class ContactAccessDeniedError(PermissionError):
    """Raised when contact access is denied."""

    def __init__(self) -> None:
        super().__init__(
            "Contact access denied. Please enable in System Preferences -> Security & Privacy -> Privacy -> Contacts"
        )


class MessageNotFoundException(ValueError):
    """Raised when a message is not found."""

    def __init__(self) -> None:
        super().__init__("Message not found")
