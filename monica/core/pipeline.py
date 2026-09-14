"""
Unified Message Processing Pipeline for M.O.N.I.C.A.

Workflow:

Telegram event
    ↓
Validation
    ↓
Command handling
    ↓
Outgoing detection
    ↓
Deduplication
    ↓
Persistent message storage
    ↓
Filters / snippets
    ↓
AFK handling
    ↓
Contact permission
    ↓
Short-term debounce
    ↓
AI context assembly
    ↓
Ollama
    ↓
Fast Telegram reply
    ↓
Background memory consolidation
"""

import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional

from monica.core.router import CommandContext, CommandRouter
from monica.core.contacts import ContactManager
from monica.core.client import TelegramClientWrapper
from monica.db.repository import Repository
from monica.memory import MemoryManager
from monica.persona import PersonaLoader
from monica.ai.manager import MonicaAIManager
from monica.telegram.buttons import ButtonParser

logger = logging.getLogger("Monica.Pipeline")


class MessagePipeline:
    def __init__(
        self,
        config: Any,
        client: TelegramClientWrapper,
        repository: Repository,
        contacts: ContactManager,
        memory: MemoryManager,
        persona: PersonaLoader,
        ai_manager: MonicaAIManager,
        router: CommandRouter,
        scheduler: Optional[Any] = None,
    ):
        self.config = config
        self.client = client
        self.repo = repository
        self.contacts = contacts
        self.memory = memory
        self.persona = persona
        self.ai = ai_manager
        self.router = router
        self.scheduler = scheduler

        # Prevent multiple AI generations from racing.
        self._lock = asyncio.Lock()

    # ==================================================================
    # MAIN EVENT HANDLER
    # ==================================================================

    async def handle_event(self, event: Any) -> None:
        """
        Entry point for incoming Telegram events.
        """

        try:
            message = getattr(event, "message", None)

            if not message:
                return

            text = (
                getattr(message, "text", "")
                or getattr(message, "message", "")
                or ""
            )

            text = text.strip()

            if not text:
                return

            chat_id = str(event.chat_id)
            sender_id = str(event.sender_id)

            my_id = str(
                self.client.me.id
                if self.client and self.client.me
                else self.config.ADMIN_USER_ID
            )

            is_admin = (
                sender_id == str(self.config.ADMIN_USER_ID)
                or sender_id == my_id
            )

            is_private = getattr(
                event,
                "is_private",
                True,
            )

            is_outgoing = (
                getattr(message, "out", False)
                or sender_id == my_id
            )

            logger.debug(
                "📩 Telegram event | chat=%s | sender=%s | outgoing=%s | text=%s",
                chat_id,
                sender_id,
                is_outgoing,
                text[:100],
            )

            # ----------------------------------------------------------
            # 1. OUTGOING MESSAGE
            # ----------------------------------------------------------

            if is_outgoing:
                await self.repo.save_message(
                    chat_id=chat_id,
                    sender_id=sender_id,
                    message_id=message.id,
                    timestamp=message.date or datetime.datetime.now(),
                    message=text,
                    direction="outgoing",
                    sender_name="Siva",
                )

                # Automatically clear AFK when owner sends a message.
                afk_state = await self.repo.get_afk()

                if afk_state.get("is_afk"):
                    await self.repo.clear_afk()

                    logger.info(
                        "Cleared AFK mode due to owner activity."
                    )

                # Commands sent by owner.
                if self.router.is_command(text):
                    ctx = self._create_command_context(
                        event,
                        message,
                        text,
                        chat_id,
                        sender_id,
                        is_admin,
                        is_private,
                        is_outgoing,
                    )

                    await self.router.dispatch(ctx)

                return

            # ----------------------------------------------------------
            # 2. INCOMING COMMAND
            # ----------------------------------------------------------

            if self.router.is_command(text):
                ctx = self._create_command_context(
                    event,
                    message,
                    text,
                    chat_id,
                    sender_id,
                    is_admin,
                    is_private,
                    is_outgoing,
                )

                handled = await self.router.dispatch(ctx)

                if handled:
                    return

            # ----------------------------------------------------------
            # 3. DEDUPLICATION
            # ----------------------------------------------------------

            if await self.repo.is_message_processed(
                message.id,
                chat_id,
            ):
                logger.debug(
                    "Skipping duplicate message #%s in chat %s",
                    message.id,
                    chat_id,
                )
                return

            await self.repo.mark_message_processed(
                message.id,
                chat_id,
            )

            # ----------------------------------------------------------
            # 4. SENDER DETAILS
            # ----------------------------------------------------------

            sender_name = "User"
            username = None

            sender = (
                await event.get_sender()
                if hasattr(event, "get_sender")
                else None
            )

            if sender:
                first = getattr(
                    sender,
                    "first_name",
                    "",
                ) or ""

                last = getattr(
                    sender,
                    "last_name",
                    "",
                ) or ""

                sender_name = (
                    f"{first} {last}".strip()
                    or getattr(
                        sender,
                        "title",
                        "User",
                    )
                )

                username = getattr(
                    sender,
                    "username",
                    None,
                )

            # ----------------------------------------------------------
            # 5. SAVE INCOMING MESSAGE + TRIGGER MEMORY
            # ----------------------------------------------------------

            await self.memory.record_interaction(
                chat_id=chat_id,
                sender_id=sender_id,
                message_id=message.id,
                text=text,
                direction="incoming",
                sender_name=sender_name,
            )

            logger.debug(
                "💾 Saved incoming message for chat %s",
                chat_id,
            )

            # ----------------------------------------------------------
            # 6. KEYWORD FILTER
            # ----------------------------------------------------------

            matching_filters = await self.repo.get_matching_filters(
                text,
                chat_id,
            )

            if matching_filters:
                reply_item = matching_filters[0]

                clean_reply, buttons = ButtonParser.parse_markup(
                    reply_item["reply_text"]
                )

                await self.client.send_message(
                    chat_id,
                    clean_reply,
                    reply_to=message.id,
                    buttons=buttons,
                )

                logger.info(
                    "Triggered keyword filter '%s' for chat %s",
                    reply_item["trigger"],
                    chat_id,
                )

                return

            # ----------------------------------------------------------
            # 7. SNIPPET
            # ----------------------------------------------------------

            if text.startswith("#"):
                trigger = text[1:].strip().lower()

                snip = await self.repo.get_snippet(
                    trigger
                )

                if snip:
                    clean_snip, buttons = ButtonParser.parse_markup(
                        snip["content"]
                    )

                    await self.client.send_message(
                        chat_id,
                        clean_snip,
                        reply_to=message.id,
                        buttons=buttons,
                    )

                    logger.info(
                        "Served snippet '#%s' to chat %s",
                        trigger,
                        chat_id,
                    )

                    return

            # ----------------------------------------------------------
            # 8. AFK NOTICE
            # ----------------------------------------------------------

            afk = await self.repo.get_afk()

            if afk.get("is_afk") and is_private:
                reason = afk.get(
                    "reason",
                    "Busy",
                )

                afk_msg = (
                    f"🌙 **Siva is currently away** ({reason}).\n"
                    "I'm Monica, his AI assistant. "
                    "Leave your message and I will assist you "
                    "or notify Siva!"
                )

                await self.client.send_message(
                    chat_id,
                    afk_msg,
                    reply_to=message.id,
                )

                # Continue to AI response.

            # ----------------------------------------------------------
            # 9. AUTO-REPLY GATE
            # ----------------------------------------------------------

            if not self.config.AUTO_REPLY:
                logger.debug(
                    "Auto-reply disabled. Ignoring chat %s",
                    chat_id,
                )
                return

            is_allowed = await self.contacts.is_allowed(
                chat_id=chat_id,
                username=username,
                mode=self.config.AUTO_REPLY_MODE,
                is_private=is_private,
            )

            if not is_allowed:

                if (
                    self.config.AUTO_REPLY_MODE == "allowlist"
                    and is_private
                ):
                    prior_count = await self.repo.get_message_count(
                        chat_id
                    )

                    if prior_count <= 1:
                        gate_msg = (
                            f"Hello {sender_name}! "
                            "I am Monica, Siva Kumar's personal manager.\n\n"
                            "Siva's account is currently in protected "
                            "manager mode. Your message has been logged "
                            "for his review, and he will get back to you "
                            "shortly."
                        )

                        await self.client.send_message(
                            chat_id,
                            gate_msg,
                            reply_to=message.id,
                        )

                return

            # ----------------------------------------------------------
            # 10. SHORT-TERM DEBOUNCE
            # ----------------------------------------------------------

            msg_payload = {
                "message_id": message.id,
                "message": text,
                "sender_name": sender_name,
                "direction": "incoming",
            }

            async def _on_debounce_ready(
                target_chat_id: str,
                aggregated_msgs: List[Dict[str, Any]],
            ):
                await self._process_ai_response(
                    target_chat_id,
                    sender_name,
                    aggregated_msgs,
                    message.id,
                )

            await self.memory.short_term.add_incoming_message(
                chat_id=chat_id,
                message_data=msg_payload,
                on_debounced_ready=_on_debounce_ready,
            )

        except Exception as exc:
            logger.error(
                "Pipeline error: %s",
                exc,
                exc_info=True,
            )

    # ==================================================================
    # AI PROCESSING
    # ==================================================================

    async def _process_ai_response(
        self,
        chat_id: str,
        sender_name: str,
        messages: List[Dict[str, Any]],
        reply_to_id: int,
    ) -> None:
        """
        Generate and send Monica's response.

        Memory summarization does NOT happen here.
        It is already scheduled in the background when the
        incoming message was recorded.
        """

        async with self._lock:

            try:
                logger.info(
                    "🤖 Processing AI response for chat %s",
                    chat_id,
                )

                # ------------------------------------------------------
                # FIRST CONTACT
                # ------------------------------------------------------

                prior_count = await self.repo.get_message_count(
                    chat_id
                )

                is_first_contact = (
                    prior_count <= len(messages)
                )

                # ------------------------------------------------------
                # CUSTOM CONTACT TONE
                # ------------------------------------------------------

                custom_tone = await self.contacts.get_custom_tone(
                    chat_id
                )

                # ------------------------------------------------------
                # RECENT HISTORY
                # ------------------------------------------------------

                # Keep this reasonably small for speed.
                # Long-term memory handles older conversation context.
                history = await self.repo.get_chat_history(
                    chat_id,
                    limit=12,
                )

                if not history:
                    history = messages

                logger.info(
                    "🧠 Context prepared: %d recent messages for chat %s",
                    len(history),
                    chat_id,
                )

                # ------------------------------------------------------
                # AI GENERATION
                # ------------------------------------------------------

                clean_text, buttons = await self.ai.generate_response(
                    chat_id=chat_id,
                    sender_name=sender_name,
                    incoming_messages=history,
                    is_first_contact=is_first_contact,
                    custom_tone=custom_tone,
                )

                # ------------------------------------------------------
                # NO RESPONSE
                # ------------------------------------------------------

                if not clean_text:
                    logger.info(
                        "No response generated for chat %s",
                        chat_id,
                    )
                    return

                # ------------------------------------------------------
                # SEND IMMEDIATELY
                # ------------------------------------------------------

                logger.info(
                    "💬 Sending Monica reply to chat %s",
                    chat_id,
                )

                sent_msg = await self.client.send_message(
                    chat_id=chat_id,
                    text=clean_text,
                    reply_to=reply_to_id,
                    buttons=buttons,
                )

                # ------------------------------------------------------
                # SAVE MONICA'S RESPONSE
                # ------------------------------------------------------

                sent_id = getattr(
                    sent_msg,
                    "id",
                    0,
                )

                await self.repo.save_message(
                    chat_id=chat_id,
                    sender_id=str(
                        self.config.ADMIN_USER_ID
                    ),
                    message_id=sent_id,
                    timestamp=datetime.datetime.now(),
                    message=clean_text,
                    direction="outgoing",
                    sender_name="Monica",
                )

                logger.info(
                    "✅ Monica reply delivered to chat %s",
                    chat_id,
                )

            except Exception as exc:
                logger.error(
                    "AI pipeline error for chat %s: %s",
                    chat_id,
                    exc,
                    exc_info=True,
                )

    # ==================================================================
    # COMMAND CONTEXT
    # ==================================================================

    def _create_command_context(
        self,
        event,
        message,
        text,
        chat_id,
        sender_id,
        is_admin,
        is_private,
        is_outgoing,
    ) -> CommandContext:

        return CommandContext(
            event=event,
            message=message,
            text=text,
            command="",
            args="",
            chat_id=chat_id,
            sender_id=sender_id,
            is_admin=is_admin,
            is_private=is_private,
            is_outgoing=is_outgoing,
            client=self.client,
            repository=self.repo,
            config=self.config,
            memory=self.memory,
            persona=self.persona,
            scheduler=self.scheduler,
            ai_manager=self.ai,
        )