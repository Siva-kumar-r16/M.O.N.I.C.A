"""
Schedule & Reminder Expression Parser for M.O.N.I.C.A.
Parses relative durations ("10m", "2h", "1d"), ISO dates, and natural language prompts
such as "in 10m call Arun" or "tomorrow at 6pm check email".
"""

import datetime
import re
from typing import Optional, Tuple


class ScheduleParser:
    """Parses date/time strings and reminder commands into structured execution times."""

    RELATIVE_PATTERN = re.compile(
        r"^(?:in\s+)?(?:(\d+)\s*d(?:ays?)?)?\s*(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:in(?:ute)?s?)?)?\s*(?:(\d+)\s*s(?:ec(?:ond)?s?)?)?$",
        re.IGNORECASE,
    )

    INTERVAL_PATTERN = re.compile(
        r"^every\s+(?:(\d+)\s*d(?:ays?)?)?\s*(?:(\d+)\s*h(?:ours?)?)?\s*(?:(\d+)\s*m(?:in(?:ute)?s?)?)?\s*(?:(\d+)\s*s(?:ec(?:ond)?s?)?)?$",
        re.IGNORECASE,
    )

    @classmethod
    def parse_relative_seconds(cls, time_str: str) -> Optional[int]:
        """Parses strings like '10m', '2h', '1d', '30s' into total seconds."""
        match = cls.RELATIVE_PATTERN.match(time_str.strip())
        if not match:
            return None

        days, hours, minutes, seconds = match.groups()
        total_sec = 0
        if days:
            total_sec += int(days) * 86400
        if hours:
            total_sec += int(hours) * 3600
        if minutes:
            total_sec += int(minutes) * 60
        if seconds:
            total_sec += int(seconds)

        return total_sec if total_sec > 0 else None

    @classmethod
    def parse_schedule(cls, input_str: str) -> Tuple[Optional[datetime.datetime], Optional[int], str]:
        """
        Parses combined schedule strings like:
        - "10m Call Arun" -> (datetime, None, "Call Arun")
        - "every 2h Check logs" -> (datetime, 7200, "Check logs")
        - "2026-09-14 18:00 Team meeting" -> (datetime, None, "Team meeting")
        - "tomorrow 18:00 Review PR" -> (datetime, None, "Review PR")
        """
        clean = input_str.strip()
        parts = clean.split(maxsplit=1)
        if not parts:
            return None, None, ""

        now = datetime.datetime.now()

        # Check for 'every <duration> <msg>'
        if clean.lower().startswith("every "):
            sub_parts = clean[6:].strip().split(maxsplit=1)
            interval_str = sub_parts[0]
            msg = sub_parts[1] if len(sub_parts) > 1 else ""
            secs = cls.parse_relative_seconds(interval_str)
            if secs:
                run_at = now + datetime.timedelta(seconds=secs)
                return run_at, secs, msg

        # Check relative "10m", "2h", "1d"
        time_token = parts[0]
        msg = parts[1] if len(parts) > 1 else ""
        rel_secs = cls.parse_relative_seconds(time_token)
        if rel_secs:
            run_at = now + datetime.timedelta(seconds=rel_secs)
            return run_at, None, msg

        # Check "tomorrow 18:00 <msg>"
        if time_token.lower() == "tomorrow" and len(parts) > 1:
            next_parts = parts[1].split(maxsplit=1)
            time_part = next_parts[0]
            msg = next_parts[1] if len(next_parts) > 1 else ""
            try:
                hour, minute = map(int, time_part.split(":"))
                tomorrow = now + datetime.timedelta(days=1)
                run_at = tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return run_at, None, msg
            except Exception:
                pass

        # Check ISO / standard date format "YYYY-MM-DD HH:MM <msg>"
        if len(parts) > 1:
            try:
                date_str = f"{parts[0]} {parts[1].split()[0]}"
                run_at = datetime.datetime.fromisoformat(date_str)
                msg_parts = parts[1].split(maxsplit=1)
                msg = msg_parts[1] if len(msg_parts) > 1 else ""
                return run_at, None, msg
            except Exception:
                pass

        return None, None, clean
