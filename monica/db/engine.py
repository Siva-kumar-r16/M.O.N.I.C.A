"""
Async SQLite Database Engine for M.O.N.I.C.A.
Supports aiosqlite when installed, with seamless fallback to an async thread-pool wrapper
around standard library sqlite3 for maximum portability and zero-crash reliability.
Handles network filesystems (e.g. 9p, NFS) gracefully with automatic synchronization.
"""

import asyncio
import logging
import os
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("Monica.DatabaseEngine")


class AsyncSqliteConnection:
    """Thread-safe async wrapper around standard library sqlite3 with filesystem adaptation."""

    def __init__(self, target_db_path: str, working_db_path: str, sync_needed: bool):
        self.target_db_path = target_db_path
        self.working_db_path = working_db_path
        self.sync_needed = sync_needed
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self):
        def _open():
            # If working path is separate, copy target if exists
            if self.sync_needed and os.path.exists(self.target_db_path) and not os.path.exists(self.working_db_path):
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
        return self

    def _sync_back(self):
        if self.sync_needed and self.working_db_path != self.target_db_path:
            try:
                shutil.copyfile(self.working_db_path, self.target_db_path)
            except Exception as e:
                logger.debug(f"Sync back error: {e}")

    async def close(self):
        if self._conn:
            await asyncio.to_thread(self._conn.close)
            self._conn = None
            await asyncio.to_thread(self._sync_back)

    async def execute(self, sql: str, parameters: Tuple = ()) -> Any:
        async with self._lock:
            def _exec():
                cursor = self._conn.cursor()
                cursor.execute(sql, parameters)
                self._conn.commit()
                self._sync_back()
                return cursor
            return await asyncio.to_thread(_exec)

    async def executemany(self, sql: str, parameters: List[Tuple]) -> Any:
        async with self._lock:
            def _exec():
                cursor = self._conn.cursor()
                cursor.executemany(sql, parameters)
                self._conn.commit()
                self._sync_back()
                return cursor
            return await asyncio.to_thread(_exec)

    async def executescript(self, script: str):
        async with self._lock:
            def _exec():
                cursor = self._conn.cursor()
                cursor.executescript(script)
                self._conn.commit()
                self._sync_back()
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

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class DatabaseEngine:
    """Manages the database connection lifecycle with auto-adaptation for all filesystem types."""

    def __init__(self, db_path: Path):
        self.target_db_path = Path(db_path)
        self.target_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.working_db_path = self.target_db_path
        self.sync_needed = False
        self._test_filesystem()

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
            # Filesystem does not support native locking (e.g. 9p, NFS)
            logger.warning(
                f"Target path {self.target_db_path} does not support native SQLite locks ({e}). "
                "Engaging resilient local working cache with auto-sync."
            )
            safe_name = f"monica_{self.target_db_path.stem}.db"
            tmp_dir = Path("/tmp/monica_db_cache")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            self.working_db_path = tmp_dir / safe_name
            self.sync_needed = True

            # If target exists and has content, copy to working path
            if self.target_db_path.exists() and self.target_db_path.stat().st_size > 0:
                try:
                    shutil.copyfile(self.target_db_path, self.working_db_path)
                except Exception as copy_err:
                    logger.error(f"Error copying existing db: {copy_err}")

    def get_connection(self) -> AsyncSqliteConnection:
        """Returns an async connection context manager."""
        return AsyncSqliteConnection(
            target_db_path=str(self.target_db_path),
            working_db_path=str(self.working_db_path),
            sync_needed=self.sync_needed,
        )

    async def execute(self, sql: str, parameters: Tuple = ()) -> Any:
        async with self.get_connection() as conn:
            return await conn.execute(sql, parameters)

    async def fetchall(self, sql: str, parameters: Tuple = ()) -> List[Dict[str, Any]]:
        async with self.get_connection() as conn:
            return await conn.fetchall(sql, parameters)

    async def fetchone(self, sql: str, parameters: Tuple = ()) -> Optional[Dict[str, Any]]:
        async with self.get_connection() as conn:
            return await conn.fetchone(sql, parameters)
