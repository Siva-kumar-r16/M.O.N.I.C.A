"""
Core Management & Admin Commands Plugin for M.O.N.I.C.A.
Implements:
/help, /status, /auto, /mode, /model, /reload, /profile, /persona, /monica, /ping
/add, /remove, /list, /approve, /block, /unblock
/remember, /forget, /memory, /reset
/schedule, /reminders, /cancelreminder
"""

import datetime
import time
from typing import Any, Dict
from monica.core.router import CommandContext
from monica.plugins.base import BasePlugin
from monica.telegram.buttons import ButtonBuilder, create_portfolio_buttons

START_TIME = datetime.datetime.now()


class CoreCommandsPlugin(BasePlugin):
    name = "Core Commands"
    version = "1.0.0"
    description = "Core administrative management, configuration, contacts, and memory controls."
    category = "Core"

    async def on_load(self):
        # System & Status
        self.register_command("help", self.cmd_help, "Displays categorized command catalog.", "/help [category/command]")
        self.register_command("status", self.cmd_status, "Displays system health and operational statistics.", "/status")
        self.register_command("auto", self.cmd_auto, "Toggles automated AI replies on or off.", "/auto [on|off]")
        self.register_command("mode", self.cmd_mode, "Views or changes auto-reply filter mode.", "/mode [allowlist|all_private|all|disabled]")
        self.register_command("model", self.cmd_model, "Views or updates current local Ollama model.", "/model [model_name]")
        self.register_command("reload", self.cmd_reload, "Reloads persona, profile, and plugins on the fly.", "/reload")
        self.register_command("profile", self.cmd_profile, "Displays Siva Kumar's professional profile & portfolio.", "/profile")
        self.register_command("persona", self.cmd_persona, "Displays Monica's current persona and tone parameters.", "/persona")
        self.register_command("monica", self.cmd_monica, "Information about M.O.N.I.C.A. architecture.", "/monica")
        self.register_command("ping", self.cmd_ping, "Checks bot latency and responsiveness.", "/ping")

        # Contact Management
        self.register_command("add", self.cmd_add, "Adds a user to the approved auto-reply allowlist.", "/add <chat_id> [custom_style]", category="Contacts")
        self.register_command("remove", self.cmd_remove, "Removes a user from the approved allowlist.", "/remove <chat_id>", category="Contacts")
        self.register_command("list", self.cmd_list, "Lists all configured contacts and settings.", "/list", category="Contacts")
        self.register_command("approve", self.cmd_approve, "Approves a user in private messages (PM Permit).", "/approve [chat_id]", category="Contacts")
        self.register_command("block", self.cmd_block, "Blocks a contact from receiving automated replies.", "/block <chat_id>", category="Contacts")
        self.register_command("unblock", self.cmd_unblock, "Unblocks a previously blocked contact.", "/unblock <chat_id>", category="Contacts")

        # Memory Controls
        self.register_command("remember", self.cmd_remember, "Saves a discrete fact or preference to memory.", "/remember <fact>", category="Memory")
        self.register_command("forget", self.cmd_forget, "Deactivates a memory record by ID.", "/forget <id>", category="Memory")
        self.register_command("memory", self.cmd_memory, "Views or searches stored memories for this chat.", "/memory [query]", category="Memory")
        self.register_command("reset", self.cmd_reset, "Clears memories for the current chat or globally.", "/reset [all]", category="Memory")

        # Automation / Scheduling
        self.register_command("schedule", self.cmd_schedule, "Schedules a persistent one-off or recurring reminder.", "/schedule <time> <message>", category="Automation")
        self.register_command("reminders", self.cmd_reminders, "Lists all active scheduled reminders.", "/reminders", category="Automation")
        self.register_command("cancelreminder", self.cmd_cancelreminder, "Cancels an active reminder by ID.", "/cancelreminder <job_id>", category="Automation")

    # --- Handlers ---

    async def cmd_help(self, ctx: CommandContext):
        catalog = self.router.get_help_catalog(is_admin=ctx.is_admin)
        lines = ["✨ **M.O.N.I.C.A. Command Catalog** ✨\n"]
        for cat, cmds in catalog.items():
            lines.append(f"📁 **{cat}**:")
            for c in cmds:
                lines.append(f"  • `/{c.command}`: {c.description}")
            lines.append("")
        lines.append("💡 _Tip: Admin commands are strictly restricted to your authorized account._")
        await ctx.reply("\n".join(lines))

    async def cmd_status(self, ctx: CommandContext):
        uptime = str(datetime.datetime.now() - START_TIME).split(".")[0]
        cfg = ctx.config
        repo = ctx.repository
        msg_count = await repo.get_message_count(ctx.chat_id)
        mems = await repo.get_memories_for_context(ctx.chat_id)
        active_jobs = await repo.list_active_jobs(ctx.chat_id)

        status_text = f"""🤖 **M.O.N.I.C.A. System Status**
━━━━━━━━━━━━━━━━━━━━━
⏱ **Uptime**: `{uptime}`
🧠 **AI Model**: `{cfg.OLLAMA_MODEL}`
⚡ **Auto-Reply**: `{'Enabled' if cfg.AUTO_REPLY else 'Disabled'}`
🛡 **Mode**: `{cfg.AUTO_REPLY_MODE}`
💬 **Messages Logged (Chat)**: `{msg_count}`
🧬 **Active Memories**: `{len(mems)}`
⏰ **Active Reminders**: `{len(active_jobs)}`
━━━━━━━━━━━━━━━━━━━━━
System healthy. Ollama backend operational."""
        await ctx.reply(status_text)

    async def cmd_auto(self, ctx: CommandContext):
        arg = ctx.args.lower().strip()
        if arg in ("on", "true", "1", "enable"):
            ctx.config.AUTO_REPLY = True
            await ctx.reply("✅ **Auto-Reply Enabled**: Monica will process eligible incoming messages.")
        elif arg in ("off", "false", "0", "disable"):
            ctx.config.AUTO_REPLY = False
            await ctx.reply("⏸ **Auto-Reply Disabled**: Monica will remain silent.")
        else:
            state = "Enabled" if ctx.config.AUTO_REPLY else "Disabled"
            await ctx.reply(f"ℹ️ **Auto-Reply is currently**: `{state}`. Use `/auto on` or `/auto off`.")

    async def cmd_mode(self, ctx: CommandContext):
        valid_modes = ["allowlist", "all_private", "all", "disabled"]
        arg = ctx.args.lower().strip()
        if arg in valid_modes:
            ctx.config.AUTO_REPLY_MODE = arg
            await ctx.reply(f"⚙️ **Auto-Reply Mode updated to**: `{arg}`")
        else:
            await ctx.reply(
                f"ℹ️ **Current Mode**: `{ctx.config.AUTO_REPLY_MODE}`\n"
                f"Available modes: `{', '.join(valid_modes)}`\n"
                f"Usage: `/mode <mode_name>`"
            )

    async def cmd_model(self, ctx: CommandContext):
        if ctx.args.strip():
            new_model = ctx.args.strip()
            ctx.config.OLLAMA_MODEL = new_model
            if hasattr(self.app.get("ollama"), "model"):
                self.app["ollama"].model = new_model
            await ctx.reply(f"🤖 **Ollama Model changed to**: `{new_model}`")
        else:
            await ctx.reply(f"ℹ️ **Current Ollama Model**: `{ctx.config.OLLAMA_MODEL}`\nUsage: `/model <model_name>`")

    async def cmd_reload(self, ctx: CommandContext):
        res = ctx.persona.reload()
        # Also reload plugins
        pm = self.app.get("plugin_manager")
        if pm:
            await pm.load_all()
        await ctx.reply(f"🔄 **Reload Complete**:\n- Persona: `{res['persona_name']}`\n- Owner: `{res['owner']}`\n- Markdown profile & persona synchronized.")

    async def cmd_profile(self, ctx: CommandContext):
        p = ctx.persona.siva_profile.get("personal_info", {})
        skills = ctx.persona.siva_profile.get("technical_skills", {})
        text = f"""👤 **Profile: {p.get('full_name')}**
━━━━━━━━━━━━━━━━━━━━━
🎓 **Role**: {p.get('role')}
🏛 **Institution**: {p.get('institution')}
📍 **Location**: {p.get('location')}
🛠 **Core Domains**: {', '.join(skills.get('domains', []))}
💻 **Languages**: {', '.join(skills.get('languages', []))}
━━━━━━━━━━━━━━━━━━━━━"""
        buttons = create_portfolio_buttons(p.get("portfolio_url", "https://sivakumar.dev"), p.get("github_url", ""))
        await ctx.reply(text, buttons=buttons)

    async def cmd_persona(self, ctx: CommandContext):
        ident = ctx.persona.monica_persona.get("identity", {})
        pers = ctx.persona.monica_persona.get("personality", {})
        text = f"""🎭 **Monica AI Persona Configuration**
━━━━━━━━━━━━━━━━━━━━━
✨ **Name**: {ident.get('name')}
👑 **Role**: {ident.get('role')}
💎 **Core Traits**: {', '.join(pers.get('core_traits', []))}
😏 **Sarcasm Level**: {pers.get('sarcasm_level')}
🎨 **Emoji Level**: {pers.get('emoji_level')}
━━━━━━━━━━━━━━━━━━━━━"""
        await ctx.reply(text)

    async def cmd_monica(self, ctx: CommandContext):
        about = """🌟 **M.O.N.I.C.A.**
_Multimodal Operational Neural Intelligence & Conversational Assistant_

An AI-first personal manager running directly on Telegram MTProto through Telethon with local Ollama inference.
Engineered for intelligent conversational communication, strong memory, persistent scheduling, and Ultroid-level userbot capabilities."""
        await ctx.reply(about)

    async def cmd_ping(self, ctx: CommandContext):
        start = time.perf_counter()
        msg = await ctx.reply("🏓 **Pinging...**")
        delta = (time.perf_counter() - start) * 1000
        if msg and hasattr(msg, "edit"):
            await msg.edit(f"🏓 **Pong!** Latency: `{delta:.2f}ms`")

    # --- Contact Management Handlers ---

    async def cmd_add(self, ctx: CommandContext):
        parts = ctx.args.split(maxsplit=1)
        if not parts:
            await ctx.reply("Usage: `/add <chat_id> [custom_style]`")
            return
        target_id = parts[0]
        style = parts[1] if len(parts) > 1 else ""
        await ctx.repository.upsert_contact(target_id, custom_tone=style, is_allowed=True, approved_pm=True)
        await ctx.reply(f"✅ Contact `{target_id}` added to allowlist with style: `{style or 'Default'}`.")

    async def cmd_remove(self, ctx: CommandContext):
        if not ctx.args.strip():
            await ctx.reply("Usage: `/remove <chat_id>`")
            return
        target_id = ctx.args.strip()
        await ctx.repository.upsert_contact(target_id, is_allowed=False)
        await ctx.reply(f"🗑 Contact `{target_id}` removed from allowlist.")

    async def cmd_list(self, ctx: CommandContext):
        contacts = await ctx.repository.list_all_contacts()
        if not contacts:
            await ctx.reply("No customized contacts found in database.")
            return
        lines = ["👥 **Configured Contacts & States:**\n"]
        for c in contacts:
            allowed = "Allowed" if c.get("is_allowed") else "Disabled"
            blocked = "Blocked" if c.get("is_blocked") else "Active"
            name = c.get("first_name") or c.get("username") or c.get("chat_id")
            lines.append(f"• **{name}** (`{c.get('chat_id')}`): {allowed} | {blocked} | Style: _{c.get('custom_tone') or 'None'}_")
        await ctx.reply("\n".join(lines))

    async def cmd_approve(self, ctx: CommandContext):
        target = ctx.args.strip() or ctx.chat_id
        await ctx.repository.upsert_contact(target, is_allowed=True, approved_pm=True)
        await ctx.reply(f"✅ User `{target}` approved for PM interactions.")

    async def cmd_block(self, ctx: CommandContext):
        target = ctx.args.strip() or ctx.chat_id
        await ctx.repository.upsert_contact(target, is_blocked=True, is_allowed=False)
        await ctx.reply(f"🚫 User `{target}` blocked from auto-replies.")

    async def cmd_unblock(self, ctx: CommandContext):
        target = ctx.args.strip() or ctx.chat_id
        await ctx.repository.upsert_contact(target, is_blocked=False, is_allowed=True)
        await ctx.reply(f"🔓 User `{target}` unblocked.")

    # --- Memory Handlers ---

    async def cmd_remember(self, ctx: CommandContext):
        if not ctx.args.strip():
            await ctx.reply("Usage: `/remember <fact or preference to save>`")
            return
        mem_id = await ctx.memory.discrete.remember(ctx.chat_id, ctx.args.strip(), category="fact")
        await ctx.reply(f"🧠 **Memory Saved** [#{mem_id}]:\n_{ctx.args.strip()}_")

    async def cmd_forget(self, ctx: CommandContext):
        if not ctx.args.strip() or not ctx.args.strip().isdigit():
            await ctx.reply("Usage: `/forget <memory_id>`")
            return
        mem_id = int(ctx.args.strip())
        success = await ctx.memory.discrete.forget(mem_id)
        if success:
            await ctx.reply(f"🗑 Memory `#{mem_id}` has been forgotten.")
        else:
            await ctx.reply(f"⚠️ Memory `#{mem_id}` not found or already deactivated.")

    async def cmd_memory(self, ctx: CommandContext):
        query = ctx.args.strip()
        if query:
            mems = await ctx.memory.discrete.search(query, ctx.chat_id)
        else:
            mems = await ctx.memory.discrete.get_memories_for_chat(ctx.chat_id)

        if not mems:
            await ctx.reply("No matching memories recorded for this context.")
            return

        lines = ["🧠 **Active Memories:**\n"]
        for m in mems:
            lines.append(f"• `[#{m['id']}]` [{m.get('category', 'fact')}]: {m['content']}")
        await ctx.reply("\n".join(lines))

    async def cmd_reset(self, ctx: CommandContext):
        is_all = ctx.args.strip().lower() == "all"
        target_chat = None if is_all else ctx.chat_id
        count = await ctx.memory.discrete.reset(target_chat)
        scope = "all chats" if is_all else "this chat"
        await ctx.reply(f"🧹 Reset {count} memories for {scope}.")

    # --- Scheduling Handlers ---

    async def cmd_schedule(self, ctx: CommandContext):
        if not ctx.args.strip():
            await ctx.reply("Usage: `/schedule <10m / 2h / tomorrow 18:00> <message>`\nExample: `/schedule 15m Check database backup`")
            return

        sched = ctx.scheduler or self.app.get("scheduler")
        if not sched:
            await ctx.reply("⚠️ Scheduler is currently unavailable.")
            return

        res = await sched.schedule(ctx.chat_id, ctx.args.strip())
        if res.get("status") == "success":
            rec_str = " (Recurring)" if res.get("is_recurring") else ""
            await ctx.reply(f"⏰ **Reminder Scheduled** [#{res['job_id']}]{rec_str}:\n- Run At: `{res['run_at']}`\n- Message: _{res['message']}_")
        else:
            await ctx.reply(f"❌ **Failed to schedule**: {res.get('message')}")

    async def cmd_reminders(self, ctx: CommandContext):
        sched = ctx.scheduler or self.app.get("scheduler")
        if not sched:
            await ctx.reply("⚠️ Scheduler is currently unavailable.")
            return
        jobs = await sched.list_jobs(ctx.chat_id)
        if not jobs:
            await ctx.reply("No active reminders for this chat.")
            return
        lines = ["⏰ **Active Scheduled Reminders:**\n"]
        for j in jobs:
            rec = " (Recurring)" if j.get("is_recurring") else ""
            lines.append(f"• `[#{j['id']}]` `{j['run_at']}`: {j['message_text']}{rec}")
        await ctx.reply("\n".join(lines))

    async def cmd_cancelreminder(self, ctx: CommandContext):
        if not ctx.args.strip():
            await ctx.reply("Usage: `/cancelreminder <job_id>`")
            return
        job_id = ctx.args.strip()
        sched = ctx.scheduler or self.app.get("scheduler")
        if not sched:
            await ctx.reply("⚠️ Scheduler is currently unavailable.")
            return
        success = await sched.cancel(job_id)
        if success:
            await ctx.reply(f"✅ Reminder `#{job_id}` has been cancelled.")
        else:
            await ctx.reply(f"⚠️ Reminder `#{job_id}` not found or already cancelled.")
