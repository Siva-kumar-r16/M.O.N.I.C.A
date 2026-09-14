"""
Database Migration Manager for M.O.N.I.C.A.
Performs safe, non-destructive schema migrations, preserves existing records,
and creates necessary indexes for high-throughput userbot operations.
"""

import logging
from monica.db.engine import DatabaseEngine

logger = logging.getLogger("Monica.Migrations")

CURRENT_SCHEMA_VERSION = 2

SCHEMA_V1_V2_SQL = """
-- 1. Messages table (compatible with existing Telegram Personal Manager)
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    message_id INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    message TEXT NOT NULL,
    direction TEXT NOT NULL,
    sender_name TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_timestamp ON messages (chat_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_lookup ON messages (message_id, chat_id);

-- 2. Processed messages table for deduplication
CREATE TABLE IF NOT EXISTS processed_messages (
    message_id INTEGER NOT NULL,
    chat_id TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    PRIMARY KEY (message_id, chat_id)
);

-- 3. Conversation summaries table
CREATE TABLE IF NOT EXISTS conversation_summaries (
    chat_id TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    message_count INTEGER DEFAULT 0
);

-- 4. Discrete long-term memories table
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'fact', -- 'fact', 'preference', 'topic', 'relationship'
    memory_key TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_memories_chat_active ON memories (chat_id, is_active);
CREATE INDEX IF NOT EXISTS idx_memories_category ON memories (category);

-- 5. Snippets / Notes table (Ultroid feature parity)
CREATE TABLE IF NOT EXISTS snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    media_path TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snippets_trigger ON snippets (trigger);

-- 6. Keyword auto-reply filters (Ultroid feature parity)
CREATE TABLE IF NOT EXISTS filters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL DEFAULT 'global',
    trigger TEXT NOT NULL,
    reply_text TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_filters_chat_trigger ON filters (chat_id, trigger);

-- 7. Persistent scheduled jobs & reminders table
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    schedule_type TEXT NOT NULL, -- 'once', 'interval', 'cron'
    run_at TEXT,
    cron_expr TEXT,
    interval_seconds INTEGER,
    message_text TEXT NOT NULL,
    is_recurring INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    last_run TEXT
);

CREATE INDEX IF NOT EXISTS idx_scheduled_active_run ON scheduled_jobs (is_active, run_at);

-- 8. AFK status table (Ultroid feature parity)
CREATE TABLE IF NOT EXISTS afk_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    is_afk INTEGER DEFAULT 0,
    reason TEXT,
    afk_time TEXT
);

INSERT OR IGNORE INTO afk_state (id, is_afk, reason, afk_time)
VALUES (1, 0, '', '');

-- 9. Contact states and permissions table
CREATE TABLE IF NOT EXISTS contacts (
    chat_id TEXT PRIMARY KEY,
    first_name TEXT DEFAULT '',
    last_name TEXT DEFAULT '',
    username TEXT DEFAULT '',
    custom_tone TEXT DEFAULT '',
    is_allowed INTEGER DEFAULT 1,
    auto_reply_enabled INTEGER DEFAULT 1,
    approved_pm INTEGER DEFAULT 0,
    is_blocked INTEGER DEFAULT 0,
    last_interaction TEXT,
    notes TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_contacts_username ON contacts (username);

-- 10. Schema version tracking table
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    migrated_at TEXT NOT NULL
);
"""


class MigrationManager:
    def __init__(self, engine: DatabaseEngine):
        self.engine = engine

    async def run_migrations(self):
        """Executes idempotent schema migrations and records schema version."""
        logger.info("Initializing database schema and checking migrations...")
        async with self.engine.get_connection() as conn:
            await conn.executescript(SCHEMA_V1_V2_SQL)
            
            # Check schema version
            row = await conn.fetchone("SELECT MAX(version) as current_version FROM schema_version;")
            cur_ver = row.get("current_version") if row and row.get("current_version") else 0

            if cur_ver < CURRENT_SCHEMA_VERSION:
                import datetime
                now_str = datetime.datetime.now().isoformat()
                await conn.execute(
                    "INSERT INTO schema_version (version, migrated_at) VALUES (?, ?);",
                    (CURRENT_SCHEMA_VERSION, now_str)
                )
                logger.info(f"Database migrated to schema version {CURRENT_SCHEMA_VERSION}.")
            else:
                logger.info(f"Database schema is already at version {cur_ver}.")
