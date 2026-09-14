# Plugin Development Guide for M.O.N.I.C.A.

M.O.N.I.C.A. features a safe, modular local plugin architecture inspired by the best aspects of Ultroid, but fortified with strict local execution isolation and type safety.

## Creating a New Plugin

1. Create a new folder under `monica/plugins/<your_plugin_name>/`
2. Create an `__init__.py` inside your plugin folder.
3. Inherit from `monica.plugins.base.BasePlugin`.
4. Implement `async def on_load(self)`.
5. Register your commands via `self.register_command(...)`.

```python
from monica.core.router import CommandContext
from monica.plugins.base import BasePlugin

class MyCustomPlugin(BasePlugin):
    name = "My Custom Plugin"
    version = "1.0.0"
    description = "Adds specialized tools"
    category = "Custom"

    async def on_load(self):
        self.register_command(
            command="mytool",
            handler=self.cmd_mytool,
            description="Executes my custom tool",
            usage="/mytool <argument>",
            admin_only=True,
        )

    async def cmd_mytool(self, ctx: CommandContext):
        await ctx.reply(f"Custom tool received: {ctx.args}")
```

## Security Rules
- All plugins must be local.
- No remote code downloads or arbitrary shell evaluations (`eval`, `exec`, `bash`).
- Use `ctx.repository` for persistent database storage.
