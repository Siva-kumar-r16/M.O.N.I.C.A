"""
Interactive Telegram Buttons Helper for M.O.N.I.C.A.
Supports URL buttons, callback buttons, multi-row layouts, and automatic parsing
of AI markup tags like [BUTTON:Text|URL] into Telethon button grids.
"""

import re
import logging
from typing import Any, List, Optional, Tuple, Union

logger = logging.getLogger("Monica.Buttons")

try:
    from telethon import Button as TelethonButton
    HAS_TELETHON = True
except ImportError:
    HAS_TELETHON = False

    class MockButton:
        @staticmethod
        def url(text: str, url: str):
            return {"type": "url", "text": text, "url": url}

        @staticmethod
        def inline(text: str, data: Any = None):
            return {"type": "inline", "text": text, "data": data}

    TelethonButton = MockButton


class ButtonBuilder:
    """Convenient builder for constructing multi-row Telegram interactive buttons."""

    def __init__(self):
        self.rows: List[List[Any]] = []
        self._current_row: List[Any] = []

    def url(self, text: str, url: str) -> "ButtonBuilder":
        """Adds a URL button to the current row."""
        self._current_row.append(TelethonButton.url(text=text, url=url))
        return self

    def callback(self, text: str, data: Union[str, bytes] = "") -> "ButtonBuilder":
        """Adds a callback button to the current row."""
        bdata = data.encode("utf-8") if isinstance(data, str) else data
        self._current_row.append(TelethonButton.inline(text=text, data=bdata))
        return self

    def row(self) -> "ButtonBuilder":
        """Finalizes the current row and starts a new one."""
        if self._current_row:
            self.rows.append(self._current_row)
            self._current_row = []
        return self

    def build(self) -> Optional[List[List[Any]]]:
        """Builds the 2D button matrix for Telethon."""
        if self._current_row:
            self.rows.append(self._current_row)
            self._current_row = []
        return self.rows if self.rows else None


class ButtonParser:
    """Parses AI-generated text containing [BUTTON:Label|URL] or [CALLBACK:Label|Data]."""

    URL_BUTTON_REGEX = re.compile(r"\[BUTTON:([^\|\]]+)\|([^\]]+)\]", re.IGNORECASE)
    CALLBACK_BUTTON_REGEX = re.compile(r"\[CALLBACK:([^\|\]]+)\|([^\]]+)\]", re.IGNORECASE)

    @classmethod
    def parse_markup(cls, text: str) -> Tuple[str, Optional[List[List[Any]]]]:
        """
        Extracts button markup tags from the message text, removes them from the clean text,
        and constructs a Telethon-compatible button matrix.
        """
        if not text:
            return text, None

        builder = ButtonBuilder()
        has_buttons = False

        # Find URL buttons
        url_matches = cls.URL_BUTTON_REGEX.findall(text)
        for label, url in url_matches:
            clean_label = label.strip()
            clean_url = url.strip()
            if clean_url.startswith("http://") or clean_url.startswith("https://"):
                builder.url(clean_label, clean_url)
                builder.row()
                has_buttons = True

        # Find Callback buttons
        cb_matches = cls.CALLBACK_BUTTON_REGEX.findall(text)
        for label, data in cb_matches:
            builder.callback(label.strip(), data.strip())
            builder.row()
            has_buttons = True

        # Strip button tags from the text
        clean_text = cls.URL_BUTTON_REGEX.sub("", text)
        clean_text = cls.CALLBACK_BUTTON_REGEX.sub("", clean_text).strip()

        return clean_text, (builder.build() if has_buttons else None)


def create_quick_url_button(label: str, url: str) -> List[List[Any]]:
    """Helper to create a single URL button."""
    return [[TelethonButton.url(text=label, url=url)]]


def create_portfolio_buttons(portfolio_url: str, github_url: str = "") -> List[List[Any]]:
    """Generates standard portfolio and link buttons for Siva."""
    builder = ButtonBuilder()
    builder.url("🌐 Open Portfolio", portfolio_url)
    if github_url:
        builder.url("💻 GitHub", github_url)
    builder.row()
    return builder.build()
