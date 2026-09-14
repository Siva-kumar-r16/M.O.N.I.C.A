"""
Telethon Client Wrapper for M.O.N.I.C.A.

Handles MTProto connection lifecycle using StringSession,
user account authentication, button attachment rendering,
message sending, message editing, and event listener registration.
"""

import logging
from typing import Any, Callable, List, Optional, Union

logger = logging.getLogger("Monica.Client")

try:
    from telethon import TelegramClient, events
    from telethon.sessions import StringSession
    from telethon.tl.types import User

    HAS_TELETHON = True

except ImportError:
    HAS_TELETHON = False
    TelegramClient = None
    events = None
    StringSession = None
    User = None


class TelegramClientWrapper:
    """Manages the MTProto connection using Telethon and StringSession."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        session_string: str,
    ):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_string = session_string

        self.client: Optional[Any] = None
        self.me: Optional[Any] = None

        if HAS_TELETHON and api_id and api_hash and session_string:
            self.client = TelegramClient(
                StringSession(session_string),
                api_id,
                api_hash,
            )

    # ============================================================
    # CONNECTION
    # ============================================================

    async def start(self) -> None:
        """Connects and verifies the Telegram user session."""

        if not HAS_TELETHON:
            logger.warning(
                "Telethon is not installed; "
                "running in mock/offline mode."
            )
            return

        if not self.client:
            raise RuntimeError(
                "Cannot start Telegram client: "
                "API_ID, API_HASH, or SESSION_STRING missing."
            )

        logger.info("Connecting to Telegram MTProto...")

        await self.client.connect()

        if not await self.client.is_user_authorized():
            raise RuntimeError(
                "Provided SESSION_STRING is invalid or not authorized. "
                "Run 'python generate_session.py' to generate "
                "a fresh StringSession."
            )

        self.me = await self.client.get_me()

        logger.info(
            f"Authenticated as: {self.me.first_name} "
            f"(@{self.me.username or 'NoUsername'}) "
            f"[ID: {self.me.id}]"
        )

    # ============================================================
    # EVENT LISTENERS
    # ============================================================

    def register_message_listener(
        self,
        handler_callback: Callable,
    ):
        """Registers a listener for incoming/outgoing Telegram messages."""

        if not HAS_TELETHON or not self.client:
            return

        @self.client.on(events.NewMessage)
        async def on_new_message(event):
            await handler_callback(event)

    def register_callback_listener(
        self,
        handler_callback: Callable,
    ):
        """Registers a listener for interactive button callbacks."""

        if not HAS_TELETHON or not self.client:
            return

        @self.client.on(events.CallbackQuery)
        async def on_callback_query(event):
            await handler_callback(event)

    # ============================================================
    # ENTITY RESOLUTION
    # ============================================================

    async def resolve_entity(
        self,
        entity_id: Union[int, str],
    ) -> Any:
        """
        Resolves a Telegram entity safely.

        Numeric Telegram IDs may arrive from the database or
        message pipeline as strings. Telethon expects numeric
        IDs to be passed as integers, so convert them first.
        """

        if not self.client:
            return None

        entity = entity_id

        if isinstance(entity_id, str):
            value = entity_id.strip()

            if value.lstrip("-").isdigit():
                entity = int(value)
            else:
                entity = value

        return await self.client.get_input_entity(entity)

    # ============================================================
    # SEND MESSAGE
    # ============================================================

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        reply_to: Optional[int] = None,
        buttons: Optional[List[List[Any]]] = None,
        parse_mode: str = "md",
    ) -> Any:
        """Sends a message with optional reply and buttons."""

        if not self.client:
            logger.debug(
                f"[Mock Client] Sending to {chat_id}: "
                f"{text[:60]}... "
                f"(buttons={bool(buttons)})"
            )
            return None

        # --------------------------------------------------------
        # IMPORTANT:
        # Convert numeric string IDs to integers.
        #
        # Example:
        #     "8348556198"
        # becomes:
        #     8348556198
        #
        # This prevents Telethon from treating the ID as a
        # username/entity string.
        # --------------------------------------------------------

        entity = chat_id

        if isinstance(chat_id, str):
            value = chat_id.strip()

            if value.lstrip("-").isdigit():
                entity = int(value)

        return await self.client.send_message(
            entity,
            text,
            reply_to=reply_to,
            buttons=buttons,
            parse_mode=parse_mode,
        )

    # ============================================================
    # EDIT MESSAGE
    # ============================================================

    async def edit_message(
        self,
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        buttons: Optional[List[List[Any]]] = None,
        parse_mode: str = "md",
    ) -> Any:
        """Edits an existing message."""

        if not self.client:
            logger.debug(
                f"[Mock Client] Editing in {chat_id} "
                f"msg {message_id}: {text[:60]}..."
            )
            return None

        # Convert numeric string IDs to integers.
        entity = chat_id

        if isinstance(chat_id, str):
            value = chat_id.strip()

            if value.lstrip("-").isdigit():
                entity = int(value)

        return await self.client.edit_message(
            entity,
            message_id,
            text,
            buttons=buttons,
            parse_mode=parse_mode,
        )

    # ============================================================
    # DELETE MESSAGES
    # ============================================================

    async def delete_messages(
        self,
        chat_id: Union[int, str],
        message_ids: List[int],
    ) -> Any:
        """Deletes messages by ID."""

        if not self.client:
            logger.debug(
                f"[Mock Client] Deleting in {chat_id} "
                f"msgs: {message_ids}"
            )
            return None

        # Convert numeric string IDs to integers.
        entity = chat_id

        if isinstance(chat_id, str):
            value = chat_id.strip()

            if value.lstrip("-").isdigit():
                entity = int(value)

        return await self.client.delete_messages(
            entity,
            message_ids,
        )

    # ============================================================
    # GET ENTITY
    # ============================================================

    async def get_entity(
        self,
        entity_id: Union[int, str],
    ) -> Any:
        """Gets a Telegram entity by ID, username, or other reference."""

        if not self.client:
            return None

        entity = entity_id

        if isinstance(entity_id, str):
            value = entity_id.strip()

            if value.lstrip("-").isdigit():
                entity = int(value)

        return await self.client.get_entity(entity)

    # ============================================================
    # DISCONNECT
    # ============================================================

    async def stop(self):
        """Disconnects the Telegram client."""

        if self.client:
            logger.info("Disconnecting from Telegram...")

            await self.client.disconnect()

            logger.info("Telegram client disconnected.")