import logging
import sys
import time
from dataclasses import dataclass
from typing import Any, ClassVar, Optional

# Only import macOS specific modules on Darwin
if sys.platform == "darwin":
    from Contacts import (  # type: ignore[import-untyped]
        CNContactFamilyNameKey,
        CNContactGivenNameKey,
        CNContactPhoneNumbersKey,
        CNContactStore,
    )
    from Foundation import NSPredicate  # type: ignore[import-untyped]

from .errors import ContactAccessDeniedError

__all__ = ["AddressBook", "Contact"]


@dataclass
class Contact:
    given_name: str
    family_name: str
    phone_numbers: list[str]

    @property
    def full_name(self) -> str:
        return f"{self.given_name} {self.family_name}".strip()


class AddressBook:
    # Define keys_to_fetch only on macOS
    if sys.platform == "darwin":
        keys_to_fetch: ClassVar[list[str]] = [CNContactGivenNameKey, CNContactFamilyNameKey, CNContactPhoneNumbersKey]

    def __init__(self) -> None:
        if sys.platform != "darwin":
            raise NotImplementedError("AddressBook is only supported on macOS")

        self.store = CNContactStore.alloc().init()
        self._ensure_access()
        self._contacts_cache: dict[str, Contact] = {}
        self._last_cache_update: int = 0
        self._cache_ttl: int = 300  # 5 minutes cache TTL

    def _ensure_access(self) -> None:
        """Check and request contacts access if needed"""
        authorization_status = CNContactStore.authorizationStatusForEntityType_(0)
        if authorization_status == 0:  # Not Determined
            self.request_contacts_access()
        elif authorization_status == 2:  # Denied
            raise ContactAccessDeniedError()

    def request_contacts_access(self) -> None:
        """Request permission to access contacts"""

        def completion_handler(granted: bool, error: Optional[Any]) -> None:
            if error:
                logging.error(f"Error requesting contacts access: {error}")
            else:
                logging.info(f"Contacts access granted: {granted}")

        self.store.requestAccessForEntityType_completionHandler_(
            0,  # CNEntityTypeContacts
            completion_handler,
        )

    def _fetch_all_contacts(self) -> dict[str, Contact]:
        """Fetch all contacts and build phone number to Contact mapping"""
        contacts_map = {}
        try:
            predicate = NSPredicate.predicateWithValue_(True)
            result = self.store.unifiedContactsMatchingPredicate_keysToFetch_error_(
                predicate, self.keys_to_fetch, None
            )[0]

            for contact in result:
                contact_obj = Contact(
                    given_name=contact.givenName() or "",
                    family_name=contact.familyName() or "",
                    phone_numbers=[number.value().stringValue() for number in contact.phoneNumbers()],
                )
                # Store each phone number variant as a key
                for phone in contact_obj.phone_numbers:
                    clean_number = "".join(filter(str.isdigit, phone))
                    contacts_map[clean_number] = contact_obj
        except Exception:
            logging.exception("Failed to fetch contacts")
        return contacts_map

    def _update_cache_if_needed(self) -> None:
        """Update the cache if it's expired"""
        current_time = int(time.time())
        if current_time - self._last_cache_update > self._cache_ttl:
            self._contacts_cache = self._fetch_all_contacts()
            self._last_cache_update = current_time

    def get_contact_by_phone(self, phone_number: str) -> Optional[Contact]:
        """
        Look up a contact by phone number.
        Args:
            phone_number: Phone number to search for (any format)
        Returns:
            Contact object if found, None otherwise
        """
        try:
            # Update cache if needed
            self._update_cache_if_needed()

            # Clean up the phone number
            clean_number = "".join(filter(str.isdigit, phone_number))

            # Try exact match first
            if clean_number in self._contacts_cache:
                return self._contacts_cache[clean_number]
            else:
                # Try partial match
                for cached_number, contact in self._contacts_cache.items():
                    if clean_number in cached_number:
                        return contact
        except Exception:
            logging.exception("Failed to lookup contact")
            return None
        else:
            return None
