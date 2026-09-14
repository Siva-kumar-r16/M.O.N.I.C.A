"""
Short-term Memory & Debouncing Buffer for M.O.N.I.C.A.
Handles short-term message aggregation, debouncing rapid bursts of user messages,
and retrieving the immediate recent context window.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("Monica.ShortTermMemory")


class ShortTermMemory:
    def __init__(self, debounce_seconds: float = 3.0, max_buffer_size: int = 50):
        self.debounce_seconds = debounce_seconds
        self.max_buffer_size = max_buffer_size
        self._buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._debounce_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()

    async def add_incoming_message(
        self,
        chat_id: str,
        message_data: Dict[str, Any],
        on_debounced_ready: Optional[Callable[[str, List[Dict[str, Any]]], Any]] = None,
    ) -> None:
        """
        Adds an incoming message to the chat's buffer and sets/resets the debounce timer.
        When the user stops typing for `debounce_seconds`, `on_debounced_ready` is invoked.
        """
        async with self._lock:
            if chat_id not in self._buffers:
                self._buffers[chat_id] = []
            self._buffers[chat_id].append(message_data)

            # Limit buffer size
            if len(self._buffers[chat_id]) > self.max_buffer_size:
                self._buffers[chat_id] = self._buffers[chat_id][-self.max_buffer_size:]

            # Cancel existing debounce timer for this chat
            if chat_id in self._debounce_tasks and not self._debounce_tasks[chat_id].done():
                self._debounce_tasks[chat_id].cancel()

            if on_debounced_ready:
                self._debounce_tasks[chat_id] = asyncio.create_task(
                    self._debounce_worker(chat_id, on_debounced_ready)
                )

    async def _debounce_worker(self, chat_id: str, callback: Callable[[str, List[Dict[str, Any]]], Any]):
        try:
            await asyncio.sleep(self.debounce_seconds)
            async with self._lock:
                messages = list(self._buffers.get(chat_id, []))
                # Do not clear the historical buffer, but mark debounce complete
                self._debounce_tasks.pop(chat_id, None)

            if messages:
                await callback(chat_id, messages)
        except asyncio.CancelledError:
            # Debounce timer reset by another incoming message
            pass
        except Exception as e:
            logger.error(f"Error in debounce worker for chat {chat_id}: {e}", exc_info=True)

    def get_recent_messages(self, chat_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns recent short-term messages from memory."""
        msgs = self._buffers.get(chat_id, [])
        return msgs[-limit:]

    def clear(self, chat_id: Optional[str] = None):
        """Clears short-term buffer."""
        if chat_id:
            self._buffers.pop(chat_id, None)
            if chat_id in self._debounce_tasks:
                self._debounce_tasks[chat_id].cancel()
                self._debounce_tasks.pop(chat_id, None)
        else:
            self._buffers.clear()
            for t in self._debounce_tasks.values():
                t.cancel()
            self._debounce_tasks.clear()
