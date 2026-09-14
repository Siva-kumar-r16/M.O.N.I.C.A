"""
Telegram Text & Formatting Utilities for M.O.N.I.C.A.
Provides clean formatting, message truncation, code-block escaping, and metadata styling.
"""

import html
import re
from typing import Optional


def truncate(text: str, max_length: int = 4000) -> str:
    """Truncates text safely to Telegram's 4096 character limit."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 20] + "\n\n...[Truncated]"


def format_code(code: str, language: str = "") -> str:
    """Wraps text in a markdown code block."""
    return f"```{language}\n{code}\n```"


def escape_markdown(text: str) -> str:
    """Escapes markdown control characters where required."""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(r"([%s])" % re.escape(escape_chars), r"\\\1", text)


def format_header(title: str, subtitle: Optional[str] = None) -> str:
    """Generates a styled header box for bot output."""
    header = f"✨ **{title}** ✨\n"
    if subtitle:
        header += f"_{subtitle}_\n"
    header += "—" * 25 + "\n"
    return header
