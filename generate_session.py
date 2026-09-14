"""
Telethon StringSession Generator for M.O.N.I.C.A.
Safely prompts for Telegram credentials and produces a StringSession for MTProto user accounts.
"""

import asyncio
import os
import sys

try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
except ImportError:
    print("Telethon is required to generate a session string.")
    print("Please install requirements: pip install -r requirements.txt")
    sys.exit(1)


async def main():
    print("=" * 60)
    print("      M.O.N.I.C.A. — Telegram StringSession Generator")
    print("=" * 60)
    print("This script will generate a Telethon StringSession for your user account.")
    print("Obtain API_ID and API_HASH from https://my.telegram.org\n")

    api_id_input = input("Enter your API_ID: ").strip()
    api_hash_input = input("Enter your API_HASH: ").strip()

    if not api_id_input.isdigit() or not api_hash_input:
        print("\n[!] Error: API_ID must be a number and API_HASH cannot be empty.")
        return

    api_id = int(api_id_input)
    api_hash = api_hash_input

    print("\nConnecting to Telegram servers...")
    client = TelegramClient(StringSession(), api_id, api_hash)

    try:
        await client.start()
        session_str = client.session.save()
        me = await client.get_me()

        print("\n" + "=" * 60)
        print("🎉 SUCCESS! Authorized as:", me.first_name, f"(@{me.username or 'NoUsername'}) [ID: {me.id}]")
        print("=" * 60)
        print("\nYour SESSION_STRING is:\n")
        print(session_str)
        print("\n" + "=" * 60)
        print("⚠️  KEEP THIS SECRET! Paste it into your .env file as:")
        print(f"SESSION_STRING={session_str}")
        print(f"ADMIN_USER_ID={me.id}")
        print("=" * 60)
    except Exception as e:
        print(f"\n[!] Failed to generate session string: {e}")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
