"""
Callback Router & Dispatcher for M.O.N.I.C.A.
Manages callback query routing, button action execution, message edits,
and contextual AI follow-ups.
"""

import asyncio
import logging
import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple

logger = logging.getLogger("Monica.Callbacks")


class CallbackRouter:
    """Registers and dispatches callback queries."""

    def __init__(self):
        self._handlers: List[Tuple[Pattern, Callable]] = []

    def register(self, pattern: str):
        """Decorator to register a callback handler matching a regex pattern."""
        regex = re.compile(pattern)

        def decorator(func: Callable):
            self._handlers.append((regex, func))
            return func

        return decorator

    async def dispatch(self, event: Any) -> bool:
        """Dispatches an incoming Telethon CallbackQuery event to matching handlers."""
        data = getattr(event, "data", b"")
        if isinstance(data, bytes):
            data_str = data.decode("utf-8", errors="ignore")
        else:
            data_str = str(data)

        for regex, handler in self._handlers:
            match = regex.match(data_str)
            if match:
                try:
                    kwargs = match.groupdict()
                    await handler(event, **kwargs)
                    return True
                except Exception as e:
                    logger.error(f"Error executing callback handler for '{data_str}': {e}", exc_info=True)
                    try:
                        if hasattr(event, "answer"):
                            await event.answer("Error processing button action.", alert=True)
                    except Exception:
                        pass
                    return False
        return False
