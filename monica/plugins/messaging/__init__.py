"""
Messaging Utilities Plugin for M.O.N.I.C.A. (Ultroid Feature Parity)
Implements:
/del: Delete replied message or last N messages
/editlast: Quick editing of the userbot's last outgoing message
/copy: Copy replied message text or media to Saved Messages
/replyto: Reply to a specific message ID with text
/save: Forward or save message to Saved Messages
"""

from typing import Any
from monica.core.router import CommandContext
from monica.plugins.base import BasePlugin


class MessagingPlugin(BasePlugin):
    name = "Messaging Utilities"
    version = "1.0.0"
    description = "Message deletion, editing, saving, and targeting utilities inspired by Ultroid."
    category = "Messaging"

    async def on_load(self):
        self.register_command("del", self.cmd_del, "Deletes the replied message or last message.", "/del [count]")
        self.register_command("editlast", self.cmd_editlast, "Edits the last message sent by you in this chat.", "/editlast <new_text>")
        self.register_command("copy", self.cmd_copy, "Copies replied message content to Saved Messages.", "/copy")
        self.register_command("save", self.cmd_copy, "Saves replied message to Saved Messages.", "/save")
        self.register_command("replyto", self.cmd_replyto, "Replies to a specific message ID.", "/replyto <msg_id> <text>")

    async def cmd_del(self, ctx: CommandContext):
        # 1. If replying to a message, delete it
        if ctx.message and hasattr(ctx.message, "is_reply") and ctx.message.is_reply:
            reply_msg = await ctx.event.get_reply_message()
            if reply_msg:
                try:
                    await reply_msg.delete()
                    await ctx.message.delete()
                    return
                except Exception as e:
                    await ctx.reply(f"⚠️ Could not delete message: {e}")
                    return

        # 2. If count specified or default last message
        count = 1
        if ctx.args.isdigit():
            count = min(int(ctx.args), 20)

        history = await ctx.repository.get_chat_history(ctx.chat_id, limit=count + 1)
        outgoing_ids = [h["message_id"] for h in history if h["direction"] == "outgoing"]

        if outgoing_ids and ctx.client:
            try:
                await ctx.client.delete_messages(ctx.chat_id, outgoing_ids[:count])
                if ctx.message:
                    await ctx.message.delete()
            except Exception as e:
                await ctx.reply(f"⚠️ Delete error: {e}")
        else:
            await ctx.reply("ℹ️ Reply to a message with `/del` or specify a count: `/del 3`")

    async def cmd_editlast(self, ctx: CommandContext):
        if not ctx.args.strip():
            await ctx.reply("Usage: `/editlast <new text>`")
            return

        last_msg = await ctx.repository.get_last_outgoing_message(ctx.chat_id)
        if not last_msg:
            await ctx.reply("⚠️ No recent outgoing message found to edit.")
            return

        msg_id = last_msg["message_id"]
        new_text = ctx.args.strip()

        if ctx.client:
            try:
                await ctx.client.edit_message(ctx.chat_id, msg_id, new_text)
                if ctx.message and ctx.message.out:
                    await ctx.message.delete()
                else:
                    await ctx.reply("✅ Message edited successfully.")
            except Exception as e:
                await ctx.reply(f"⚠️ Edit failed: {e}")
        else:
            await ctx.reply("✅ [Mock] Message edited.")

    async def cmd_copy(self, ctx: CommandContext):
        if not ctx.event or not hasattr(ctx.event, "get_reply_message"):
            await ctx.reply("Please reply to a message to copy/save it.")
            return

        reply_msg = await ctx.event.get_reply_message()
        if not reply_msg:
            await ctx.reply("⚠️ No replied message detected.")
            return

        admin_id = ctx.config.ADMIN_USER_ID
        if ctx.client:
            try:
                await ctx.client.send_message(
                    admin_id,
                    f"📥 **Saved from chat** `{ctx.chat_id}`:\n\n{reply_msg.text or '[Media Content]'}"
                )
                await ctx.reply("💾 **Message saved to your Saved Messages!**")
            except Exception as e:
                await ctx.reply(f"⚠️ Could not save message: {e}")
        else:
            await ctx.reply("💾 [Mock] Message saved to Saved Messages.")

    async def cmd_replyto(self, ctx: CommandContext):
        parts = ctx.args.split(maxsplit=1)
        if len(parts) < 2 or not parts[0].isdigit():
            await ctx.reply("Usage: `/replyto <message_id> <reply text>`")
            return

        target_msg_id = int(parts[0])
        reply_text = parts[1]

        if ctx.client:
            try:
                await ctx.client.send_message(ctx.chat_id, reply_text, reply_to=target_msg_id)
                if ctx.message and ctx.message.out:
                    await ctx.message.delete()
            except Exception as e:
                await ctx.reply(f"⚠️ Error sending reply: {e}")
        else:
            await ctx.reply(f"Reply to #{target_msg_id}: {reply_text}")
