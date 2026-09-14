"""
Repository Layer for M.O.N.I.C.A. Database.
Provides clean async CRUD interfaces for all application components.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional, Union
from monica.db.engine import DatabaseEngine

logger = logging.getLogger("Monica.Repository")


class Repository:
    def __init__(self, engine: DatabaseEngine):
        self.engine = engine

    # --- Message Operations ---
    async def save_message(
        self,
        chat_id: str,
        sender_id: str,
        message_id: int,
        timestamp: Union[datetime.datetime, str],
        message: str,
        direction: str,
        sender_name: str = "",
    ) -> None:
        if isinstance(timestamp, datetime.datetime):
            timestamp_str = timestamp.isoformat()
        else:
            timestamp_str = str(timestamp)

        sql = """
        INSERT INTO messages (chat_id, sender_id, message_id, timestamp, message, direction, sender_name)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        async with self.engine.get_connection() as conn:
            await conn.execute(
                sql, (str(chat_id), str(sender_id), message_id, timestamp_str, message, direction, sender_name)
            )

    async def get_chat_history(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        sql = """
        SELECT chat_id, sender_id, message_id, timestamp, message, direction, sender_name
        FROM messages
        WHERE chat_id = ?
        ORDER BY id DESC
        LIMIT ?;
        """
        async with self.engine.get_connection() as conn:
            rows = await conn.fetchall(sql, (str(chat_id), limit))
            return list(reversed(rows))

    async def get_message_count(self, chat_id: str) -> int:
        sql = "SELECT COUNT(*) as cnt FROM messages WHERE chat_id = ?;"
        async with self.engine.get_connection() as conn:
            row = await conn.fetchone(sql, (str(chat_id),))
            return row["cnt"] if row else 0

    async def get_last_outgoing_message(self, chat_id: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT message_id, message, timestamp
        FROM messages
        WHERE chat_id = ? AND direction = 'outgoing'
        ORDER BY id DESC
        LIMIT 1;
        """
        async with self.engine.get_connection() as conn:
            return await conn.fetchone(sql, (str(chat_id),))

    async def delete_message(self, chat_id: str, message_id: int) -> None:
        sql = "DELETE FROM messages WHERE chat_id = ? AND message_id = ?;"
        async with self.engine.get_connection() as conn:
            await conn.execute(sql, (str(chat_id), message_id))

    # --- Deduplication ---
    async def is_message_processed(self, message_id: int, chat_id: str) -> bool:
        sql = "SELECT 1 FROM processed_messages WHERE message_id = ? AND chat_id = ?;"
        async with self.engine.get_connection() as conn:
            row = await conn.fetchone(sql, (message_id, str(chat_id)))
            return bool(row)

    async def mark_message_processed(self, message_id: int, chat_id: str) -> None:
        now_str = datetime.datetime.now().isoformat()
        sql = """
        INSERT OR IGNORE INTO processed_messages (message_id, chat_id, processed_at)
        VALUES (?, ?, ?);
        """
        async with self.engine.get_connection() as conn:
            await conn.execute(sql, (message_id, str(chat_id), now_str))

    # --- Conversation Summaries ---
    async def get_conversation_summary(self, chat_id: str) -> Optional[str]:
        sql = "SELECT summary FROM conversation_summaries WHERE chat_id = ?;"
        async with self.engine.get_connection() as conn:
            row = await conn.fetchone(sql, (str(chat_id),))
            return row["summary"] if row else None

    async def save_conversation_summary(self, chat_id: str, summary: str, message_count: int) -> None:
        now_str = datetime.datetime.now().isoformat()
        sql = """
        INSERT INTO conversation_summaries (chat_id, summary, last_updated, message_count)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET
            summary = excluded.summary,
            last_updated = excluded.last_updated,
            message_count = excluded.message_count;
        """
        async with self.engine.get_connection() as conn:
            await conn.execute(sql, (str(chat_id), summary, now_str, message_count))

    # --- Discrete Memories (Level 3 Memory) ---
    async def add_memory(self, chat_id: str, category: str, content: str, memory_key: Optional[str] = None) -> int:
        now_str = datetime.datetime.now().isoformat()
        sql = """
        INSERT INTO memories (chat_id, category, memory_key, content, created_at, updated_at, is_active)
        VALUES (?, ?, ?, ?, ?, ?, 1);
        """
        async with self.engine.get_connection() as conn:
            cur = await conn.execute(sql, (str(chat_id), category, memory_key or "", content, now_str, now_str))
            return cur.lastrowid

    async def get_memories_for_context(self, chat_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        sql = """
        SELECT id, category, memory_key, content, created_at
        FROM memories
        WHERE (chat_id = ? OR chat_id = 'global') AND is_active = 1
        ORDER BY id DESC
        LIMIT ?;
        """
        async with self.engine.get_connection() as conn:
            return await conn.fetchall(sql, (str(chat_id), limit))

    async def search_memories(self, query: str, chat_id: Optional[str] = None) -> List[Dict[str, Any]]:
        like_query = f"%{query}%"
        if chat_id:
            sql = """
            SELECT id, chat_id, category, memory_key, content, created_at
            FROM memories
            WHERE (chat_id = ? OR chat_id = 'global') AND is_active = 1
              AND (content LIKE ? OR memory_key LIKE ?)
            ORDER BY id DESC;
            """
            params = (str(chat_id), like_query, like_query)
        else:
            sql = """
            SELECT id, chat_id, category, memory_key, content, created_at
            FROM memories
            WHERE is_active = 1 AND (content LIKE ? OR memory_key LIKE ?)
            ORDER BY id DESC;
            """
            params = (like_query, like_query)

        async with self.engine.get_connection() as conn:
            return await conn.fetchall(sql, params)

    async def delete_memory(self, memory_id: int) -> bool:
        sql = "UPDATE memories SET is_active = 0 WHERE id = ?;"
        async with self.engine.get_connection() as conn:
            cur = await conn.execute(sql, (memory_id,))
            return cur.rowcount > 0

    async def clear_memories(self, chat_id: Optional[str] = None) -> int:
        if chat_id:
            sql = "UPDATE memories SET is_active = 0 WHERE chat_id = ?;"
            params = (str(chat_id),)
        else:
            sql = "UPDATE memories SET is_active = 0;"
            params = ()
        async with self.engine.get_connection() as conn:
            cur = await conn.execute(sql, params)
            return cur.rowcount

    # --- Snippets (Notes) ---
    async def add_snippet(self, trigger: str, content: str, media_path: Optional[str] = None) -> None:
        now_str = datetime.datetime.now().isoformat()
        sql = """
        INSERT INTO snippets (trigger, content, media_path, created_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(trigger) DO UPDATE SET
            content = excluded.content,
            media_path = excluded.media_path,
            created_at = excluded.created_at;
        """
        async with self.engine.get_connection() as conn:
            await conn.execute(sql, (trigger.strip().lower(), content, media_path, now_str))

    async def get_snippet(self, trigger: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT trigger, content, media_path FROM snippets WHERE trigger = ?;"
        async with self.engine.get_connection() as conn:
            return await conn.fetchone(sql, (trigger.strip().lower(),))

    async def list_snippets(self) -> List[Dict[str, Any]]:
        sql = "SELECT trigger, content, media_path, created_at FROM snippets ORDER BY trigger ASC;"
        async with self.engine.get_connection() as conn:
            return await conn.fetchall(sql)

    async def delete_snippet(self, trigger: str) -> bool:
        sql = "DELETE FROM snippets WHERE trigger = ?;"
        async with self.engine.get_connection() as conn:
            cur = await conn.execute(sql, (trigger.strip().lower(),))
            return cur.rowcount > 0

    # --- Keyword Auto-reply Filters ---
    async def add_filter(self, trigger: str, reply_text: str, chat_id: str = "global") -> None:
        now_str = datetime.datetime.now().isoformat()
        sql = """
        INSERT INTO filters (chat_id, trigger, reply_text, created_at)
        VALUES (?, ?, ?, ?);
        """
        async with self.engine.get_connection() as conn:
            await conn.execute(sql, (str(chat_id), trigger.strip().lower(), reply_text, now_str))

    async def get_matching_filters(self, text: str, chat_id: str) -> List[Dict[str, Any]]:
        sql = """
        SELECT trigger, reply_text
        FROM filters
        WHERE chat_id = ? OR chat_id = 'global';
        """
        text_lower = text.lower()
        async with self.engine.get_connection() as conn:
            rows = await conn.fetchall(sql, (str(chat_id),))
            matches = []
            for row in rows:
                if row["trigger"] in text_lower:
                    matches.append(row)
            return matches

    async def list_filters(self, chat_id: str = "global") -> List[Dict[str, Any]]:
        sql = "SELECT id, trigger, reply_text, chat_id FROM filters WHERE chat_id = ? OR chat_id = 'global';"
        async with self.engine.get_connection() as conn:
            return await conn.fetchall(sql, (str(chat_id),))

    async def delete_filter(self, trigger: str, chat_id: str = "global") -> bool:
        sql = "DELETE FROM filters WHERE trigger = ? AND (chat_id = ? OR chat_id = 'global');"
        async with self.engine.get_connection() as conn:
            cur = await conn.execute(sql, (trigger.strip().lower(), str(chat_id)))
            return cur.rowcount > 0

    # --- Persistent Scheduled Jobs ---
    async def create_scheduled_job(
        self,
        job_id: str,
        chat_id: str,
        schedule_type: str,
        run_at: Optional[str],
        message_text: str,
        cron_expr: Optional[str] = None,
        interval_seconds: Optional[int] = None,
        is_recurring: bool = False,
    ) -> None:
        now_str = datetime.datetime.now().isoformat()
        sql = """
        INSERT INTO scheduled_jobs (
            id, chat_id, schedule_type, run_at, cron_expr,
            interval_seconds, message_text, is_recurring, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
        """
        async with self.engine.get_connection() as conn:
            await conn.execute(
                sql,
                (
                    job_id,
                    str(chat_id),
                    schedule_type,
                    run_at,
                    cron_expr,
                    interval_seconds,
                    message_text,
                    1 if is_recurring else 0,
                    now_str,
                ),
            )

    async def get_due_scheduled_jobs(self, current_time_iso: str) -> List[Dict[str, Any]]:
        sql = """
        SELECT id, chat_id, schedule_type, run_at, cron_expr, interval_seconds, message_text, is_recurring
        FROM scheduled_jobs
        WHERE is_active = 1 AND run_at <= ?;
        """
        async with self.engine.get_connection() as conn:
            return await conn.fetchall(sql, (current_time_iso,))

    async def update_job_run(self, job_id: str, next_run: Optional[str] = None, deactivate: bool = False) -> None:
        now_str = datetime.datetime.now().isoformat()
        if deactivate or not next_run:
            sql = "UPDATE scheduled_jobs SET is_active = 0, last_run = ? WHERE id = ?;"
            params = (now_str, job_id)
        else:
            sql = "UPDATE scheduled_jobs SET run_at = ?, last_run = ? WHERE id = ?;"
            params = (next_run, now_str, job_id)

        async with self.engine.get_connection() as conn:
            await conn.execute(sql, params)

    async def cancel_scheduled_job(self, job_id: str) -> bool:
        sql = "UPDATE scheduled_jobs SET is_active = 0 WHERE id = ?;"
        async with self.engine.get_connection() as conn:
            cur = await conn.execute(sql, (job_id,))
            return cur.rowcount > 0

    async def list_active_jobs(self, chat_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if chat_id:
            sql = "SELECT * FROM scheduled_jobs WHERE is_active = 1 AND chat_id = ? ORDER BY run_at ASC;"
            params = (str(chat_id),)
        else:
            sql = "SELECT * FROM scheduled_jobs WHERE is_active = 1 ORDER BY run_at ASC;"
            params = ()

        async with self.engine.get_connection() as conn:
            return await conn.fetchall(sql, params)

    # --- AFK State ---
    async def get_afk(self) -> Dict[str, Any]:
        sql = "SELECT is_afk, reason, afk_time FROM afk_state WHERE id = 1;"
        async with self.engine.get_connection() as conn:
            row = await conn.fetchone(sql)
            return row if row else {"is_afk": 0, "reason": "", "afk_time": ""}

    async def set_afk(self, reason: str = "") -> None:
        now_str = datetime.datetime.now().isoformat()
        sql = "UPDATE afk_state SET is_afk = 1, reason = ?, afk_time = ? WHERE id = 1;"
        async with self.engine.get_connection() as conn:
            await conn.execute(sql, (reason, now_str))

    async def clear_afk(self) -> None:
        sql = "UPDATE afk_state SET is_afk = 0, reason = '', afk_time = '' WHERE id = 1;"
        async with self.engine.get_connection() as conn:
            await conn.execute(sql)

    # --- Contacts Management & PM Permit ---
    async def get_contact(self, chat_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM contacts WHERE chat_id = ?;"
        async with self.engine.get_connection() as conn:
            return await conn.fetchone(sql, (str(chat_id),))

    async def upsert_contact(
        self,
        chat_id: str,
        first_name: str = "",
        last_name: str = "",
        username: str = "",
        custom_tone: Optional[str] = None,
        is_allowed: Optional[bool] = None,
        approved_pm: Optional[bool] = None,
        is_blocked: Optional[bool] = None,
    ) -> None:
        now_str = datetime.datetime.now().isoformat()
        existing = await self.get_contact(chat_id)
        if existing:
            tone = custom_tone if custom_tone is not None else existing.get("custom_tone", "")
            allowed = (1 if is_allowed else 0) if is_allowed is not None else existing.get("is_allowed", 1)
            pm = (1 if approved_pm else 0) if approved_pm is not None else existing.get("approved_pm", 0)
            blocked = (1 if is_blocked else 0) if is_blocked is not None else existing.get("is_blocked", 0)

            sql = """
            UPDATE contacts SET
                first_name = COALESCE(NULLIF(?, ''), first_name),
                last_name = COALESCE(NULLIF(?, ''), last_name),
                username = COALESCE(NULLIF(?, ''), username),
                custom_tone = ?,
                is_allowed = ?,
                approved_pm = ?,
                is_blocked = ?,
                last_interaction = ?
            WHERE chat_id = ?;
            """
            async with self.engine.get_connection() as conn:
                await conn.execute(sql, (first_name, last_name, username, tone, allowed, pm, blocked, now_str, str(chat_id)))
        else:
            sql = """
            INSERT INTO contacts (chat_id, first_name, last_name, username, custom_tone, is_allowed, approved_pm, is_blocked, last_interaction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            async with self.engine.get_connection() as conn:
                await conn.execute(
                    sql,
                    (
                        str(chat_id),
                        first_name,
                        last_name,
                        username,
                        custom_tone or "",
                        1 if is_allowed is not False else 0,
                        1 if approved_pm else 0,
                        1 if is_blocked else 0,
                        now_str,
                    ),
                )

    async def list_all_contacts(self) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM contacts ORDER BY last_interaction DESC;"
        async with self.engine.get_connection() as conn:
            return await conn.fetchall(sql)
