"""
Modular Command Router & Registry for M.O.N.I.C.A.
Replaces monolithic if/elif branching with a clean, extensible decorator-based registry.
Enforces admin-only permissions, supports aliases, and provides auto-generated help documentation.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("Monica.CommandRouter")


@dataclass
class CommandContext:
    """Encapsulates execution context for a command invocation."""
    event: Any
    message: Any
    text: str
    command: str
    args: str
    chat_id: str
    sender_id: str
    is_admin: bool
    is_private: bool
    is_outgoing: bool
    client: Any
    repository: Any
    config: Any
    memory: Any
    persona: Any
    scheduler: Any = None
    ai_manager: Any = None

    async def reply(self, text: str, buttons: Any = None, parse_mode: str = "md") -> Any:
        """Helper to reply to the command message."""
        if hasattr(self.event, "reply"):
            return await self.event.reply(text, buttons=buttons, parse_mode=parse_mode)
        elif self.client and hasattr(self.client, "send_message"):
            return await self.client.send_message(self.chat_id, text, reply_to=self.message.id if self.message else None, buttons=buttons)
        return None

    async def respond(self, text: str, buttons: Any = None) -> Any:
        """Sends a response in the current chat."""
        if hasattr(self.event, "respond"):
            return await self.event.respond(text, buttons=buttons)
        elif self.client and hasattr(self.client, "send_message"):
            return await self.client.send_message(self.chat_id, text, buttons=buttons)
        return None

    async def edit(self, text: str, buttons: Any = None) -> Any:
        """Edits the command message (if outgoing)."""
        if self.message and hasattr(self.message, "edit"):
            return await self.message.edit(text, buttons=buttons)
        return await self.reply(text, buttons=buttons)


@dataclass
class CommandDefinition:
    command: str
    handler: Callable
    description: str = ""
    usage: str = ""
    admin_only: bool = True
    category: str = "General"
    aliases: List[str] = field(default_factory=list)


class CommandRouter:
    """Central registry and dispatcher for all M.O.N.I.C.A. commands."""

    def __init__(self, prefixes: Optional[List[str]] = None):
        self.prefixes: List[str] = prefixes or ["/", "."]
        self._commands: Dict[str, CommandDefinition] = {}
        self._aliases: Dict[str, str] = {}

    def register(
        self,
        command: str,
        description: str = "",
        usage: str = "",
        admin_only: bool = True,
        category: str = "General",
        aliases: Optional[List[str]] = None,
    ):
        """Decorator to register a command handler."""
        cmd_clean = command.strip().lower().lstrip("/.")

        def decorator(func: Callable):
            defn = CommandDefinition(
                command=cmd_clean,
                handler=func,
                description=description,
                usage=usage or f"/{cmd_clean}",
                admin_only=admin_only,
                category=category,
                aliases=aliases or [],
            )
            self._commands[cmd_clean] = defn
            if aliases:
                for alias in aliases:
                    alias_clean = alias.strip().lower().lstrip("/.")
                    self._aliases[alias_clean] = cmd_clean
            return func

        return decorator

    def is_command(self, text: str) -> bool:
        """Checks if text starts with a command prefix."""
        if not text:
            return False
        stripped = text.strip()
        return any(stripped.startswith(p) for p in self.prefixes)

    def parse_command(self, text: str) -> Optional[Tuple[str, str]]:
        """Parses command name and arguments."""
        if not self.is_command(text):
            return None
        stripped = text.strip()
        prefix = next(p for p in self.prefixes if stripped.startswith(p))
        content = stripped[len(prefix) :].strip()
        parts = content.split(maxsplit=1)
        cmd = parts[0].lower().split("@")[0]  # strip @botname if present
        args = parts[1].strip() if len(parts) > 1 else ""
        return cmd, args

    async def dispatch(self, ctx: CommandContext) -> bool:
        """Dispatches a command execution context to the appropriate handler."""
        parsed = self.parse_command(ctx.text)
        if not parsed:
            return False

        cmd_name, args = parsed
        canonical = self._aliases.get(cmd_name, cmd_name)
        ctx.command = canonical
        ctx.args = args

        if canonical not in self._commands:
            return False

        defn = self._commands[canonical]

        # Permission check
        if defn.admin_only and not ctx.is_admin:
            logger.warning(
                f"Unauthorized command attempt: /{cmd_name} by user {ctx.sender_id} in chat {ctx.chat_id}"
            )
            await ctx.reply("⛔ **Access Denied**: This command is restricted to the administrator.")
            return True

        try:
            logger.info(f"Executing command: /{canonical} [args: '{args}'] by {ctx.sender_id}")
            await defn.handler(ctx)
            return True
        except Exception as e:
            logger.error(f"Error executing command /{canonical}: {e}", exc_info=True)
            await ctx.reply(f"⚠️ **Command Error**: An unexpected error occurred while executing `/{canonical}`.")
            return True

    def get_help_catalog(self, is_admin: bool = False) -> Dict[str, List[CommandDefinition]]:
        """Organizes registered commands by category for the /help command."""
        catalog: Dict[str, List[CommandDefinition]] = {}
        for cmd_name, defn in sorted(self._commands.items()):
            if defn.admin_only and not is_admin:
                continue
            if defn.category not in catalog:
                catalog[defn.category] = []
            catalog[defn.category].append(defn)
        return catalog


# Global default command router
default_router = CommandRouter()
register_command = default_router.register
