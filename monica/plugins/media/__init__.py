"""
Media & File Utilities Plugin for M.O.N.I.C.A. (Ultroid Feature Parity)
Implements:
- /info: Inspects replied media metadata, file size, mime-type, and attributes
- /getfile: Downloads replied media/file to local downloads folder
"""

import os
from pathlib import Path
from typing import Any
from monica.core.router import CommandContext
from monica.plugins.base import BasePlugin


class MediaPlugin(BasePlugin):
    name = "Media Utilities"
    version = "1.0.0"
    description = "File metadata inspection and media management utilities."
    category = "Media"

    async def on_load(self):
        self.register_command("info", self.cmd_info, "Inspects metadata of replied media or file.", "/info")
        self.register_command("getfile", self.cmd_getfile, "Downloads replied file to local storage.", "/getfile")

    async def cmd_info(self, ctx: CommandContext):
        if not ctx.event or not hasattr(ctx.event, "get_reply_message"):
            await ctx.reply("Please reply to a media file, document, photo, or audio with `/info`.")
            return

        reply = await ctx.event.get_reply_message()
        if not reply or not reply.media:
            await ctx.reply("⚠️ The replied message contains no media or document.")
            return

        media = reply.media
        media_type = type(media).__name__
        file_size = getattr(reply, "file", None)
        size_str = "Unknown"
        mime_type = "Unknown"
        file_name = "None"

        if file_size:
            if hasattr(file_size, "size") and file_size.size:
                size_mb = file_size.size / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB ({file_size.size} bytes)"
            if hasattr(file_size, "mime_type") and file_size.mime_type:
                mime_type = file_size.mime_type
            if hasattr(file_size, "name") and file_size.name:
                file_name = file_size.name

        info_text = f"""📁 **Media Information**
━━━━━━━━━━━━━━━━━━━━━
📦 **Type**: `{media_type}`
📄 **File Name**: `{file_name}`
📊 **Size**: `{size_str}`
🏷 **MIME**: `{mime_type}`
📩 **Message ID**: `{reply.id}`
━━━━━━━━━━━━━━━━━━━━━"""
        await ctx.reply(info_text)

    async def cmd_getfile(self, ctx: CommandContext):
        if not ctx.event or not hasattr(ctx.event, "get_reply_message"):
            await ctx.reply("Please reply to a media file with `/getfile`.")
            return

        reply = await ctx.event.get_reply_message()
        if not reply or not reply.media:
            await ctx.reply("⚠️ The replied message has no media to download.")
            return

        downloads_dir = Path("data/downloads")
        downloads_dir.mkdir(parents=True, exist_ok=True)

        if ctx.client and hasattr(ctx.client, "client") and ctx.client.client:
            msg_status = await ctx.reply("⏳ **Downloading media...**")
            try:
                path = await ctx.client.client.download_media(reply, file=str(downloads_dir))
                if msg_status:
                    await msg_status.edit(f"✅ **Downloaded to**: `{path}`")
            except Exception as e:
                if msg_status:
                    await msg_status.edit(f"⚠️ Download failed: {e}")
        else:
            await ctx.reply("✅ [Mock] Media saved to `data/downloads/`.")
