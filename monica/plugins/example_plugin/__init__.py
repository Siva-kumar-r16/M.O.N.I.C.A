"""
Example Plugin for M.O.N.I.C.A.
Demonstrates the local plugin architecture with custom commands, callback handlers,
and lifecycle hooks for developers.
"""

from monica.core.router import CommandContext
from monica.plugins.base import BasePlugin


class ExamplePlugin(BasePlugin):
    name = "Example Plugin"
    version = "1.0.0"
    description = "Demonstrates how to author custom modular plugins for M.O.N.I.C.A."
    author = "Siva Kumar R"
    category = "Examples"

    async def on_load(self):
        """Register custom commands and resources when the plugin starts."""
        self.register_command(
            command="hello_example",
            handler=self.cmd_hello,
            description="A demonstration command greeting the user.",
            usage="/hello_example",
            admin_only=False,
            category="Examples",
            aliases=["hi_example"],
        )

    async def on_unload(self):
        """Cleanup any active tasks or connections when unloaded."""
        pass

    async def cmd_hello(self, ctx: CommandContext):
        sender = ctx.sender_id
        await ctx.reply(
            f"👋 Hello `{sender}`! This response was served by the **Example Plugin** in M.O.N.I.C.A."
        )
