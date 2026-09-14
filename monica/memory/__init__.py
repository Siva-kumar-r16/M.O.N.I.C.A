"""
Unified Memory System for M.O.N.I.C.A.

Combines:
    Level 1: Short-term memory & debouncing buffer
    Level 2: Long-term conversation summarization
    Level 3: Discrete facts, preferences, and curated memory bank

The memory system is designed so that:
- Recent conversation is fast.
- Long-term summaries are persistent.
- Personal facts are persistent.
- Background consolidation does not block Telegram replies.
"""

import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional

from monica.db.repository import Repository
from monica.memory.short_term import ShortTermMemory
from monica.memory.long_term import LongTermMemory
from monica.memory.discrete import DiscreteMemory

logger = logging.getLogger("Monica.MemoryManager")


class MemoryManager:
    def __init__(
        self,
        repository: Repository,
        ai_client: Optional[Any] = None,
        debounce_seconds: float = 0.0,
    ):
        self.repo = repository
        self.ai = ai_client

        # Level 1
        self.short_term = ShortTermMemory(
            debounce_seconds=debounce_seconds
        )

        # Level 2
        self.long_term = LongTermMemory(
            repository=repository,
            ai_client=ai_client,
        )

        # Level 3
        self.discrete = DiscreteMemory(
            repository=repository,
            ai_client=ai_client,
        )

        # Prevent multiple summary jobs for the same chat.
        self._summary_tasks: Dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # CONTEXT
    # ------------------------------------------------------------------

    async def get_context_for_prompt(
        self,
        chat_id: str,
        sender_name: str = "User",
    ) -> Dict[str, Any]:
        """
        Build the memory context used by Monica's AI manager.

        Returns:
            - discrete memories
            - long-term conversation summary
            - recent short-term messages
        """

        try:
            memories = await self.discrete.get_memories_for_chat(
                chat_id,
                limit=8,
            )
        except Exception as exc:
            logger.error(
                "Failed to retrieve discrete memories for %s: %s",
                chat_id,
                exc,
                exc_info=True,
            )
            memories = []

        try:
            summary = await self.long_term.get_summary(chat_id)
        except Exception as exc:
            logger.error(
                "Failed to retrieve conversation summary for %s: %s",
                chat_id,
                exc,
                exc_info=True,
            )
            summary = None

        try:
            recent = self.short_term.get_recent_messages(
                chat_id,
                limit=10,
            )
        except Exception as exc:
            logger.error(
                "Failed to retrieve short-term memory for %s: %s",
                chat_id,
                exc,
                exc_info=True,
            )
            recent = []

        return {
            "memories": memories,
            "conversation_summary": summary,
            "short_term_messages": recent,
        }

    # ------------------------------------------------------------------
    # INTERACTION RECORDING
    # ------------------------------------------------------------------

    async def record_interaction(
        self,
        chat_id: str,
        sender_id: str,
        message_id: int,
        text: str,
        direction: str,
        sender_name: str = "",
    ) -> None:
        """
        Record an interaction in SQLite.

        Incoming messages can trigger background long-term
        memory consolidation.

        IMPORTANT:
        This function should be used by the pipeline instead of
        directly calling repository.save_message() for incoming
        messages.
        """

        now = datetime.datetime.now()

        # --------------------------------------------------------------
        # 1. Persistent SQLite message history
        # --------------------------------------------------------------

        await self.repo.save_message(
            chat_id=chat_id,
            sender_id=sender_id,
            message_id=message_id,
            timestamp=now,
            message=text,
            direction=direction,
            sender_name=sender_name,
        )

        # --------------------------------------------------------------
        # 2. Short-term memory
        # --------------------------------------------------------------

        if direction == "incoming":
            try:
                self.short_term_message = {
                    "message_id": message_id,
                    "message": text,
                    "sender_name": sender_name,
                    "direction": "incoming",
                }
            except Exception:
                pass

        # --------------------------------------------------------------
        # 3. Long-term summarization
        # --------------------------------------------------------------

        if direction != "incoming":
            return

        try:
            should_update = await self.long_term.should_update_summary(
                chat_id
            )
        except Exception as exc:
            logger.error(
                "Failed checking summary trigger for %s: %s",
                chat_id,
                exc,
                exc_info=True,
            )
            return

        if not should_update:
            return

        # Avoid creating multiple summary jobs for the same chat.
        existing_task = self._summary_tasks.get(chat_id)

        if existing_task and not existing_task.done():
            logger.debug(
                "Summary already running for chat %s",
                chat_id,
            )
            return

        logger.info(
            "🧠 Scheduling background memory consolidation for chat %s",
            chat_id,
        )

        task = asyncio.create_task(
            self._run_background_summary(
                chat_id=chat_id,
                sender_name=sender_name,
            )
        )

        self._summary_tasks[chat_id] = task

        task.add_done_callback(
            lambda completed_task, cid=chat_id:
            self._summary_tasks.pop(cid, None)
        )

    # ------------------------------------------------------------------
    # BACKGROUND SUMMARY
    # ------------------------------------------------------------------

    async def _run_background_summary(
        self,
        chat_id: str,
        sender_name: str,
    ) -> None:
        """
        Run long-term summarization without blocking the reply.
        """

        try:
            logger.info(
                "🧠 Updating long-term memory for chat %s...",
                chat_id,
            )

            summary = await self.long_term.summarize_and_save(
                chat_id=chat_id,
                sender_name=sender_name,
            )

            if summary:
                logger.info(
                    "🧠 Long-term memory updated for chat %s",
                    chat_id,
                )
            else:
                logger.debug(
                    "No long-term summary generated for chat %s",
                    chat_id,
                )

        except asyncio.CancelledError:
            logger.debug(
                "Background summary cancelled for chat %s",
                chat_id,
            )
            raise

        except Exception as exc:
            logger.error(
                "Background summary failed for chat %s: %s",
                chat_id,
                exc,
                exc_info=True,
            )

    # ------------------------------------------------------------------
    # MANUAL MEMORY
    # ------------------------------------------------------------------

    async def remember(
        self,
        chat_id: str,
        content: str,
        category: str = "fact",
        memory_key: Optional[str] = None,
    ) -> int:
        """
        Convenience wrapper for manually storing a memory.
        """

        return await self.discrete.remember(
            chat_id=chat_id,
            content=content,
            category=category,
            memory_key=memory_key,
        )

    async def forget(
        self,
        memory_id: int,
    ) -> bool:
        """
        Remove/deactivate one discrete memory.
        """

        return await self.discrete.forget(memory_id)

    async def reset(
        self,
        chat_id: Optional[str] = None,
    ) -> int:
        """
        Clear discrete memories for a chat or globally.
        """

        return await self.discrete.reset(chat_id)

    # ------------------------------------------------------------------
    # SHUTDOWN
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """
        Cancel active background memory jobs.
        """

        tasks = list(self._summary_tasks.values())

        for task in tasks:
            if not task.done():
                task.cancel()

        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

        self._summary_tasks.clear()

        logger.info("Memory manager closed.")