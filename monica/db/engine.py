"""
Async SQLite Database Engine for M.O.N.I.C.A.

PERFORMANCE FIX (see CHANGELOG at bottom of this file):
This engine now opens ONE physical SQLite connection when the app starts
and reuses it for every query for the lifetime of the process, instead of
opening a brand new sqlite3 connection (plus PRAGMA setup, plus a full
file copy on exotic filesystems) on every single database call.

The public API (`engine.get_connection()` used as an async context
manager exposing `.execute/.fetchall/.fetchone`) is unchanged, so
Repository and every caller keep working exactly as before -- they are
just dramatically faster now, since `get_connection()` no longer opens
or closes a real connection each time it's used.
"""

import asyncio
import logging
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("Monica.DatabaseEngine")

# How many writes to batch before syncing the working copy back to the
# target path on filesystems that don't support native SQLite locking
# (e.g. some network/9p mounts). Syncing on every single write (the old
# behavior) turned every DB call into a full-file copy; syncing every
# SYNC_BACK_EVERY_N_WRITES writes (and always on clean shutdown) keeps
# the on-disk copy reasonably fresh without paying that cost per-query.
SYNC_BACK_EVERY_N_WRITES = 25


class SharedSqliteConnection:
    """
    A single, long-lived, thread-safe async wrapper around a standard
    library sqlite3 connection. Opened once, reused for every query.
    """

    def __init__(self, target_db_path: str, working_db_path: str, sync_needed: bool):
        self.target_db_path = target_db_path
        self.working_db_path = working_db_path
        self.sync_needed = sync_needed
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        self._writes_since_sync = 0

    async def connect(self):
        if self._conn is not None:
            return self

        def _open():
            if (
                self.sync_needed
                and os.path.exists(self.target_db_path)
                and not os.path.exists(self.working_db_path)
            ):
                try:
                    shutil.copyfile(self.target_db_path, self.working_db_path)
                except Exception as e:
                    logger.warning(f"Could not copy initial db: {e}")

            conn = sqlite3.connect(self.working_db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
            except Exception:
                conn.execute("PRAGMA journal_mode=DELETE;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            return conn

        self._conn = await asyncio.to_thread(_open)
        logger.info(f"Opened persistent SQLite connection at {self.working_db_path}")
        return self

    def _sync_back_if_due(self, force: bool = False):
        if not self.sync_needed or self.working_db_path == self.target_db_path:
            return
        self._writes_since_sync += 1
        if not force and self._writes_since_sync < SYNC_BACK_EVERY_N_WRITES:
            return
        try:
            shutil.copyfile(self.working_db_path, self.target_db_path)
            self._writes_since_sync = 0
        except Exception as e:
            logger.debug(f"Sync back error: {e}")

    async def close(self):
        async with self._lock:
            if self._conn:
                self._sync_back_if_due(force=True)
                await asyncio.to_thread(self._conn.close)
                self._conn = None

    async def execute(self, sql: str, parameters: Tuple = ()) -> Any:
        async with self._lock:
            def _exec():
                cursor = self._conn.cursor()
                cursor.execute(sql, parameters)
                self._conn.commit()
                self._sync_back_if_due()
                return cursor
            return await asyncio.to_thread(_exec)

    async def executemany(self, sql: str, parameters: List[Tuple]) -> Any:
        async with self._lock:
            def _exec():
                cursor = self._conn.cursor()
                cursor.executemany(sql, parameters)
                self._conn.commit()
                self._sync_back_if_due()
                return cursor
            return await asyncio.to_thread(_exec)

    async def executescript(self, script: str):
        async with self._lock:
            def _exec():
                cursor = self._conn.cursor()
                cursor.executescript(script)
                self._conn.commit()
                self._sync_back_if_due(force=True)
                return cursor
            return await asyncio.to_thread(_exec)

    async def fetchall(self, sql: str, parameters: Tuple = ()) -> List[Dict[str, Any]]:
        async with self._lock:
            def _fetch():
                cursor = self._conn.cursor()
                cursor.execute(sql, parameters)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            return await asyncio.to_thread(_fetch)

    async def fetchone(self, sql: str, parameters: Tuple = ()) -> Optional[Dict[str, Any]]:
        async with self._lock:
            def _fetch():
                cursor = self._conn.cursor()
                cursor.execute(sql, parameters)
                row = cursor.fetchone()
                return dict(row) if row else None
            return await asyncio.to_thread(_fetch)


class _ConnectionProxy:
    """
    Thin async-context-manager returned by DatabaseEngine.get_connection().

    Kept as a *separate object per call* (matching the old API shape that
    Repository already uses everywhere via `async with engine.get_connection()
    as conn:`), but it now just hands back the ONE shared, already-open
    connection instead of opening/closing a new physical connection each
    time. Entering/exiting this proxy is therefore near-zero-cost.
    """

    def __init__(self, shared: SharedSqliteConnection):
        self._shared = shared

    async def __aenter__(self) -> SharedSqliteConnection:
        if self._shared._conn is None:
            await self._shared.connect()
        return self._shared

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Intentionally a no-op: the shared connection stays open for the
        # lifetime of the process. It is closed once via
        # DatabaseEngine.close() on application shutdown.
        return False


class DatabaseEngine:
    """Manages the database connection lifecycle with auto-adaptation for all filesystem types."""

    def __init__(self, db_path: Path):
        self.target_db_path = Path(db_path)
        self.target_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.working_db_path = self.target_db_path
        self.sync_needed = False
        self._test_filesystem()
        self._shared_conn = SharedSqliteConnection(
            target_db_path=str(self.target_db_path),
            working_db_path=str(self.working_db_path),
            sync_needed=self.sync_needed,
        )

    def _test_filesystem(self):
        """Tests if the target filesystem natively supports SQLite locking."""
        test_file = self.target_db_path.parent / ".sqlite_fs_test.db"
        try:
            conn = sqlite3.connect(str(test_file), timeout=2.0)
            conn.execute("CREATE TABLE _fs_test (id INT);")
            conn.execute("INSERT INTO _fs_test VALUES (1);")
            conn.commit()
            conn.close()
            if test_file.exists():
                test_file.unlink()
            self.working_db_path = self.target_db_path
            self.sync_needed = False
            logger.info(f"Native SQLite filesystem supported at {self.target_db_path}")
        except Exception as e:
            logger.warning(
                f"Target path {self.target_db_path} does not support native SQLite locks ({e}). "
                "Engaging resilient local working cache with periodic auto-sync."
            )
            safe_name = f"monica_{self.target_db_path.stem}.db"
            tmp_dir = Path("/tmp/monica_db_cache")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            self.working_db_path = tmp_dir / safe_name
            self.sync_needed = True

            if self.target_db_path.exists() and self.target_db_path.stat().st_size > 0:
                try:
                    shutil.copyfile(self.target_db_path, self.working_db_path)
                except Exception as copy_err:
                    logger.error(f"Error copying existing db: {copy_err}")

    async def connect(self):
        """Explicitly open the shared connection. Safe to call multiple times."""
        await self._shared_conn.connect()

    async def close(self):
        """Close the shared connection and flush any pending sync-back. Call on shutdown."""
        await self._shared_conn.close()

    def get_connection(self) -> _ConnectionProxy:
        """Returns a lightweight proxy onto the single shared connection."""
        return _ConnectionProxy(self._shared_conn)

    async def execute(self, sql: str, parameters: Tuple = ()) -> Any:
        async with self.get_connection() as conn:
            return await conn.execute(sql, parameters)

    async def fetchall(self, sql: str, parameters: Tuple = ()) -> List[Dict[str, Any]]:
        async with self.get_connection() as conn:
            return await conn.fetchall(sql, parameters)

    async def fetchone(self, sql: str, parameters: Tuple = ()) -> Optional[Dict[str, Any]]:
        async with self.get_connection() as conn:
            return await conn.fetchone(sql, parameters)


# =============================================================================
# CHANGELOG (this fix)
# =============================================================================
# WHAT WAS WRONG:
#   The old get_connection() returned a brand-new AsyncSqliteConnection on
#   every call. Its __aenter__ opened a fresh sqlite3.connect() (plus two
#   PRAGMA statements) and its __aexit__/execute() closed it again and,
#   on filesystems flagged as needing sync, did a full shutil.copyfile()
#   of the *entire database file* -- on every single read or write. Since
#   Repository makes one `async with engine.get_connection()` per method
#   call, this meant every save_message/get_chat_history/etc. paid the
#   cost of opening a new OS-level connection (and potentially copying
#   the whole DB file) from scratch. This was the dominant source of
#   per-message latency and CPU/IO overhead in the pipeline.
#
# WHAT CHANGED:
#   DatabaseEngine now owns one SharedSqliteConnection, opened once
#   (lazily, on first use, or explicitly via `await engine.connect()` at
#   startup). get_connection() still returns an object usable exactly as
#   `async with engine.get_connection() as conn:`, so Repository did not
#   need to change at all -- but entering/exiting it is now a no-op that
#   just hands back the already-open connection. Filesystem sync-back (for
#   the rare 9p/NFS fallback path) now happens every SYNC_BACK_EVERY_N_WRITES
#   writes and on clean shutdown, not on every single call.
#
# SPEED / RESOURCE IMPROVEMENT:
#   Removes one sqlite3.connect() + two PRAGMA statements (+ a potential
#   full-file copy) per database call, replacing it with direct use of an
#   already-open connection guarded by a single asyncio.Lock. This is the
#   single largest latency/CPU reduction in this update, since every stage
#   of the pipeline (dedup check, save message, fetch history, fetch
#   memories, fetch/save summary) goes through this engine at least once
#   per incoming message.
# =============================================================================
