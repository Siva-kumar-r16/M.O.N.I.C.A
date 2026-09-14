"""
Contact Management & Permission Subsystem for M.O.N.I.C.A.
Maintains contact approval states, PM permits, per-chat custom tones, and auto-reply permissions.
Dual-layer support: SQLite repository with optional JSON synchronization for legacy compatibility.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from monica.db.repository import Repository

logger = logging.getLogger("Monica.Contacts")


class ContactManager:
    def __init__(self, repository: Repository, legacy_json_path: Optional[Path] = None):
        self.repo = repository
        self.legacy_json_path = legacy_json_path
        self._cache: Dict[str, Dict[str, Any]] = {}

    async def init_from_legacy_if_needed(self):
        """Imports legacy trusted_contacts.json into SQLite if not already imported."""
        if not self.legacy_json_path or not self.legacy_json_path.exists():
            return

        try:
            with open(self.legacy_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for chat_id, entry in data.items():
                    existing = await self.repo.get_contact(str(chat_id))
                    if not existing:
                        await self.repo.upsert_contact(
                            chat_id=str(chat_id),
                            first_name=entry.get("first_name", ""),
                            last_name=entry.get("last_name", ""),
                            username=entry.get("username", ""),
                            custom_tone=entry.get("custom_style", ""),
                            is_allowed=entry.get("enabled", True),
                            approved_pm=True,
                        )
            logger.info("Migrated legacy trusted contacts into SQLite database.")
        except Exception as e:
            logger.error(f"Failed to load legacy contacts: {e}")

    async def is_allowed(
        self,
        chat_id: str,
        username: Optional[str],
        mode: str,
        is_private: bool,
    ) -> bool:
        """
        Evaluates auto-reply policy:
        - 'disabled': No auto-replies
        - 'all': Auto-reply to all chats
        - 'all_private': Auto-reply to all 1:1 private chats
        - 'allowlist': Auto-reply only to approved/allowed contacts
        """
        if mode == "disabled":
            return False
        if mode == "all":
            return True
        if mode == "all_private":
            return is_private

        # allowlist mode
        contact = await self.repo.get_contact(str(chat_id))
        if contact:
            if contact.get("is_blocked"):
                return False
            return bool(contact.get("is_allowed") and contact.get("auto_reply_enabled", 1))

        return False

    async def approve_pm(self, chat_id: str) -> None:
        """Approves a contact in private message (pmpermit)."""
        await self.repo.upsert_contact(str(chat_id), is_allowed=True, approved_pm=True)

    async def is_pm_approved(self, chat_id: str) -> bool:
        """Checks whether a user has been approved via PM permit."""
        contact = await self.repo.get_contact(str(chat_id))
        return bool(contact and contact.get("approved_pm"))

    async def block_contact(self, chat_id: str) -> None:
        """Blocks a contact from receiving automated replies."""
        await self.repo.upsert_contact(str(chat_id), is_allowed=False, is_blocked=True)

    async def unblock_contact(self, chat_id: str) -> None:
        """Unblocks a contact."""
        await self.repo.upsert_contact(str(chat_id), is_blocked=False, is_allowed=True)

    async def set_custom_tone(self, chat_id: str, custom_tone: str) -> None:
        """Sets a specialized tone or instruction override for a specific contact."""
        await self.repo.upsert_contact(str(chat_id), custom_tone=custom_tone)

    async def get_custom_tone(self, chat_id: str) -> Optional[str]:
        contact = await self.repo.get_contact(str(chat_id))
        return contact.get("custom_tone") if contact else None

    async def list_contacts(self) -> List[Dict[str, Any]]:
        return await self.repo.list_all_contacts()
