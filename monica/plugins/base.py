"""
Base Plugin Interface for M.O.N.I.C.A.
Provides an extensible framework for safe local plugins with lifecycle management,
command registration, callback registration, and automated help cataloging.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from monica.core.router import CommandRouter

logger = logging.getLogger("Monica.PluginBase")


class BasePlugin:
    """Base class for all local M.O.N.I.C.A. plugins."""

    name: str = "BasePlugin"
    version: str = "1.0.0"
    description: str = "Base plugin interface"
    author: str = "Siva Kumar R"
    category: str = "General"

    def __init__(self, router: CommandRouter, app_context: Dict[str, Any]):
        self.router = router
        self.app = app_context
        self._registered_commands: List[str] = []
        self._registered_callbacks: List[str] = []

    async def on_load(self) -> None:
        """Invoked when the plugin is loaded into the system."""
        pass

    async def on_unload(self) -> None:
        """Invoked when the plugin is unloaded or reloaded."""
        pass

    def register_command(
        self,
        command: str,
        handler: Callable,
        description: str = "",
        usage: str = "",
        admin_only: bool = True,
        category: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        requires_bot_token: bool = False,
    ):
        """Registers a command into the application router on behalf of this plugin."""
        cat = category or self.category
        self.router.register(
            command=command,
            description=description,
            usage=usage,
            admin_only=admin_only,
            category=cat,
            aliases=aliases,
            examples=examples,
            requires_bot_token=requires_bot_token,
        )(handler)
        self._registered_commands.append(command.strip().lower().lstrip("/."))

    def register_callback(self, pattern: str, handler: Callable):
        """
        Registers a Telegram inline-button callback handler on behalf of this
        plugin, using the shared CallbackRouter (app_context["callback_router"]).

        `pattern` is a regex matched against the raw callback_data string;
        named groups are passed as kwargs to `handler(event, **groups)`.
        """
        cb_router = self.app.get("callback_router")
        if not cb_router:
            logger.warning(
                f"Plugin '{self.name}' tried to register callback '{pattern}' "
                "but no callback_router is available in app_context."
            )
            return
        cb_router.register(pattern)(handler)
        self._registered_callbacks.append(pattern)
