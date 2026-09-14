"""
Auto-Reply & Moderation Suite for M.O.N.I.C.A. (Ultroid Feature Parity)
Implements:
- AFK mode (/afk [reason]) with auto-recovery on user activity
- Snippets / Notes (/save_note, /get_note, /notes, /del_note)
- Keyword Filters (/filter, /filters, /stop_filter)
- PM Gatekeeper / Permit controls (/pmpermit)
"""

import datetime
from typing import Any
from monica.core.router import CommandContext
from monica.plugins.base import BasePlugin


class AutoReplyPlugin(BasePlugin):
    name = "Auto-Reply & Assistant Tools"
    version = "1.0.0"
    description = "AFK status management, persistent notes/snippets, keyword filters, and PM gatekeeper."
    category = "Auto-Reply"

    async def on_load(self):
        # AFK
        self.register_command("afk", self.cmd_afk, "Sets AFK status with an optional custom reason.", "/afk [reason]")
        self.register_command("unafk", self.cmd_unafk, "Disables AFK status manually.", "/unafk")

        # Notes / Snippets
        self.register_command("save_note", self.cmd_save_note, "Saves a reusable snippet/note.", "/save_note <trigger> <content>", aliases=["note", "snip"])
        self.register_command("get_note", self.cmd_get_note, "Fetches a saved snippet/note.", "/get_note <trigger>")
        self.register_command("notes", self.cmd_notes, "Lists all saved snippets/notes.", "/notes", aliases=["snippets"])
        self.register_command("del_note", self.cmd_del_note, "Deletes a saved snippet/note.", "/del_note <trigger>", aliases=["delnote"])

        # Filters
        self.register_command("filter", self.cmd_filter, "Adds an auto-reply keyword filter.", "/filter <keyword> <reply_text>")
        self.register_command("filters", self.cmd_filters, "Lists all active keyword filters.", "/filters")
        self.register_command("stop_filter", self.cmd_stop_filter, "Removes an auto-reply filter.", "/stop_filter <keyword>", aliases=["stop"])

        # PM Permit
        self.register_command("pmpermit", self.cmd_pmpermit, "Toggles PM approval gatekeeper.", "/pmpermit [on|off]")

    # --- AFK Handlers ---

    async def cmd_afk(self, ctx: CommandContext):
        reason = ctx.args.strip() or "Busy right now"
        await ctx.repository.set_afk(reason)
        now_time = datetime.datetime.now().strftime("%I:%M %p")
        await ctx.reply(f"🌙 **AFK Mode Activated** ({now_time})\nReason: _{reason}_\n\nMonica will inform private contacts while you are away.")

    async def cmd_unafk(self, ctx: CommandContext):
        await ctx.repository.clear_afk()
        await ctx.reply("☀️ **Welcome back! AFK mode has been deactivated.**")

    # --- Notes / Snippets Handlers ---

    async def cmd_save_note(self, ctx: CommandContext):
        parts = ctx.args.split(maxsplit=1)
        if len(parts) < 2:
            await ctx.reply("Usage: `/save_note <trigger> <content>`")
            return
        trigger, content = parts[0].lower().strip("#"), parts[1].strip()
        await ctx.repository.add_snippet(trigger, content)
        await ctx.reply(f"📌 **Note Saved**: Trigger `#{trigger}` is now active.")

    async def cmd_get_note(self, ctx: CommandContext):
        trigger = ctx.args.strip().lower().strip("#")
        if not trigger:
            await ctx.reply("Usage: `/get_note <trigger>`")
            return
        snip = await ctx.repository.get_snippet(trigger)
        if snip:
            await ctx.reply(f"📝 **Note (#{trigger})**:\n\n{snip['content']}")
        else:
            await ctx.reply(f"⚠️ No note found for trigger `#{trigger}`.")

    async def cmd_notes(self, ctx: CommandContext):
        snips = await ctx.repository.list_snippets()
        if not snips:
            await ctx.reply("No notes or snippets currently saved.")
            return
        lines = ["📚 **Saved Notes & Snippets:**\n"]
        for s in snips:
            lines.append(f"• `#{s['trigger']}`: {s['content'][:40]}...")
        await ctx.reply("\n".join(lines))

    async def cmd_del_note(self, ctx: CommandContext):
        trigger = ctx.args.strip().lower().strip("#")
        if not trigger:
            await ctx.reply("Usage: `/del_note <trigger>`")
            return
        success = await ctx.repository.delete_snippet(trigger)
        if success:
            await ctx.reply(f"🗑 Note `#{trigger}` deleted.")
        else:
            await ctx.reply(f"⚠️ Note `#{trigger}` not found.")

    # --- Filters Handlers ---

    async def cmd_filter(self, ctx: CommandContext):
        parts = ctx.args.split(maxsplit=1)
        if len(parts) < 2:
            await ctx.reply("Usage: `/filter <keyword> <reply_text>`")
            return
        trigger, reply_text = parts[0].lower().strip(), parts[1].strip()
        await ctx.repository.add_filter(trigger, reply_text, chat_id=ctx.chat_id)
        await ctx.reply(f"🎯 **Filter Added**: When someone mentions `{trigger}`, Monica will automatically reply.")

    async def cmd_filters(self, ctx: CommandContext):
        filters = await ctx.repository.list_filters(chat_id=ctx.chat_id)
        if not filters:
            await ctx.reply("No keyword filters configured.")
            return
        lines = ["🎯 **Active Keyword Filters:**\n"]
        for f in filters:
            lines.append(f"• Keyword: `{f['trigger']}` ➔ _{f['reply_text'][:40]}..._")
        await ctx.reply("\n".join(lines))

    async def cmd_stop_filter(self, ctx: CommandContext):
        trigger = ctx.args.strip().lower()
        if not trigger:
            await ctx.reply("Usage: `/stop_filter <keyword>`")
            return
        success = await ctx.repository.delete_filter(trigger, chat_id=ctx.chat_id)
        if success:
            await ctx.reply(f"🛑 Filter `{trigger}` removed.")
        else:
            await ctx.reply(f"⚠️ Filter `{trigger}` not found.")

    # --- PM Permit Handlers ---

    async def cmd_pmpermit(self, ctx: CommandContext):
        arg = ctx.args.strip().lower()
        if arg in ("on", "enable", "1"):
            ctx.config.AUTO_REPLY_MODE = "allowlist"
            await ctx.reply("🛡 **PM Permit Activated**: Unapproved private contacts will be gated.")
        elif arg in ("off", "disable", "0"):
            ctx.config.AUTO_REPLY_MODE = "all_private"
            await ctx.reply("🔓 **PM Permit Deactivated**: All private messages can receive AI replies.")
        else:
            current = "Active (Allowlist Mode)" if ctx.config.AUTO_REPLY_MODE == "allowlist" else "Inactive"
            await ctx.reply(f"ℹ️ **PM Permit Status**: `{current}`\nUsage: `/pmpermit on` or `/pmpermit off`")
