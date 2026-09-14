"""
Persistent SQLite-backed Scheduling Engine for M.O.N.I.C.A.
Periodically polls for due jobs, survives application restarts and crashes,
and dispatches notifications reliably.
"""

import asyncio
import datetime
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional
from monica.db.repository import Repository
from monica.scheduler.parser import ScheduleParser

logger = logging.getLogger("Monica.Scheduler")


class SchedulerEngine:
    def __init__(self, repository: Repository, poll_interval_seconds: float = 5.0):
        self.repo = repository
        self.poll_interval = poll_interval_seconds
        self._dispatch_callback: Optional[Callable[[str, str], Any]] = None
        self._poll_task: Optional[asyncio.Task] = None
        self._is_running = False

    def set_dispatcher(self, callback: Callable[[str, str], Any]):
        """Registers the callback invoked when a scheduled reminder is due."""
        self._dispatch_callback = callback

    async def start(self):
        """Starts the background polling loop."""
        if self._is_running:
            return
        self._is_running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("Persistent scheduler engine started.")

    async def stop(self):
        """Gracefully halts the scheduler."""
        self._is_running = False
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        logger.info("Persistent scheduler engine stopped.")

    async def _poll_loop(self):
        while self._is_running:
            try:
                now_str = datetime.datetime.now().isoformat()
                due_jobs = await self.repo.get_due_scheduled_jobs(now_str)

                for job in due_jobs:
                    await self._process_due_job(job)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler poll loop: {e}", exc_info=True)

            await asyncio.sleep(self.poll_interval)

    async def _process_due_job(self, job: Dict[str, Any]):
        job_id = job["id"]
        chat_id = job["chat_id"]
        msg_text = job["message_text"]
        interval = job.get("interval_seconds")
        is_recurring = bool(job.get("is_recurring"))

        logger.info(f"Firing scheduled reminder #{job_id} for chat {chat_id}: {msg_text}")

        # 1. Dispatch reminder message
        if self._dispatch_callback:
            try:
                formatted_reminder = f"⏰ **Scheduled Reminder**:\n\n{msg_text}"
                if asyncio.iscoroutinefunction(self._dispatch_callback):
                    await self._dispatch_callback(chat_id, formatted_reminder)
                else:
                    self._dispatch_callback(chat_id, formatted_reminder)
            except Exception as e:
                logger.error(f"Failed to dispatch reminder #{job_id} to chat {chat_id}: {e}")

        # 2. Update or deactivate
        if is_recurring and interval and interval > 0:
            next_run = (datetime.datetime.now() + datetime.timedelta(seconds=interval)).isoformat()
            await self.repo.update_job_run(job_id, next_run=next_run, deactivate=False)
        else:
            await self.repo.update_job_run(job_id, deactivate=True)

    async def schedule(
        self,
        chat_id: str,
        schedule_input: str,
    ) -> Dict[str, Any]:
        """
        Parses schedule expression and persists the job to SQLite.
        Example inputs:
        - "10m Call Arun"
        - "every 1h Hydrate"
        """
        run_at, interval_secs, message = ScheduleParser.parse_schedule(schedule_input)
        if not run_at:
            return {"status": "error", "message": "Could not parse scheduled time. Use e.g. `/schedule 10m Call Arun` or `/schedule every 1h Drink water`."}

        if not message.strip():
            return {"status": "error", "message": "Please provide a reminder message."}

        job_id = f"rem_{uuid.uuid4().hex[:8]}"
        is_recurring = interval_secs is not None and interval_secs > 0
        schedule_type = "interval" if is_recurring else "once"

        await self.repo.create_scheduled_job(
            job_id=job_id,
            chat_id=chat_id,
            schedule_type=schedule_type,
            run_at=run_at.isoformat(),
            message_text=message.strip(),
            interval_seconds=interval_secs,
            is_recurring=is_recurring,
        )

        return {
            "status": "success",
            "job_id": job_id,
            "run_at": run_at.strftime("%Y-%m-%d %I:%M:%S %p"),
            "is_recurring": is_recurring,
            "message": message.strip(),
        }

    async def cancel(self, job_id: str) -> bool:
        """Cancels a scheduled job by ID."""
        return await self.repo.cancel_scheduled_job(job_id)

    async def list_jobs(self, chat_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all currently active scheduled jobs."""
        return await self.repo.list_active_jobs(chat_id)
