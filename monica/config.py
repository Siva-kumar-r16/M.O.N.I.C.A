"""
Configuration Management for M.O.N.I.C.A.
Loads environment variables from .env, validates required parameters,
and provides safe masking so secrets are never printed to logs or console.
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Make sure required directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(dotenv_path=ENV_FILE)


# ============================================================
# CONFIGURATION CLASS
# ============================================================

class Config:
    """Central configuration with validation and secret masking."""

    def __init__(self):
        self.reload()

    def reload(self):
        """Reload all configuration values from the .env file."""

        load_dotenv(dotenv_path=ENV_FILE, override=True)

        # ----------------------------------------------------
        # Directory paths
        # ----------------------------------------------------
        # These are exposed on the Config instance because
        # other parts of M.O.N.I.C.A. use config.DATA_DIR, etc.
        self.BASE_DIR = BASE_DIR
        self.DATA_DIR = DATA_DIR
        self.LOGS_DIR = LOGS_DIR
        self.ENV_FILE = ENV_FILE

        # ----------------------------------------------------
        # Telegram API configuration
        # ----------------------------------------------------
        raw_api_id = os.getenv("API_ID", "").strip()

        if raw_api_id and raw_api_id.isdigit():
            self.API_ID: int = int(raw_api_id)
        else:
            self.API_ID = 0

        self.API_HASH: str = os.getenv("API_HASH", "").strip()
        self.SESSION_STRING: str = os.getenv("SESSION_STRING", "").strip()

        # ----------------------------------------------------
        # Admin configuration
        # ----------------------------------------------------
        raw_admin_id = os.getenv("ADMIN_USER_ID", "").strip()

        if raw_admin_id and (
            raw_admin_id.isdigit()
            or (
                raw_admin_id.startswith("-")
                and raw_admin_id[1:].isdigit()
            )
        ):
            self.ADMIN_USER_ID: int = int(raw_admin_id)
        else:
            self.ADMIN_USER_ID = 0

        # ----------------------------------------------------
        # Ollama configuration
        # ----------------------------------------------------
        self.OLLAMA_HOST: str = os.getenv(
            "OLLAMA_HOST",
            "http://127.0.0.1:11434"
        ).rstrip("/")

        self.OLLAMA_MODEL: str = os.getenv(
            "OLLAMA_MODEL",
            "qwen2.5-coder:7b"
        ).strip()

        # ----------------------------------------------------
        # Auto-reply configuration
        # ----------------------------------------------------
        self.AUTO_REPLY: bool = os.getenv(
            "AUTO_REPLY",
            "true"
        ).lower() in ("true", "1", "yes")

        self.AUTO_REPLY_MODE: str = os.getenv(
            "AUTO_REPLY_MODE",
            "allowlist"
        ).lower().strip()

        # ----------------------------------------------------
        # Message debounce configuration
        # ----------------------------------------------------
        raw_debounce = os.getenv(
            "MESSAGE_DEBOUNCE_SECONDS",
            "3.0"
        ).strip()

        try:
            self.MESSAGE_DEBOUNCE_SECONDS: float = float(raw_debounce)
        except ValueError:
            self.MESSAGE_DEBOUNCE_SECONDS = 3.0

        # ----------------------------------------------------
        # Database configuration
        # ----------------------------------------------------
        raw_db_path = os.getenv(
            "DATABASE_PATH",
            ""
        ).strip()

        if raw_db_path:
            self.DATABASE_PATH: Path = Path(raw_db_path)
        else:
            self.DATABASE_PATH = DATA_DIR / "monica.db"

        # ----------------------------------------------------
        # Logging configuration
        # ----------------------------------------------------
        self.LOG_FILE: Path = LOGS_DIR / "monica.log"

        self.LOG_LEVEL: str = os.getenv(
            "LOG_LEVEL",
            "INFO"
        ).upper().strip()

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(self) -> List[str]:
        """
        Validate configuration parameters.

        Returns:
            List[str]: A list of configuration errors.
                       Empty list means configuration is valid.
        """

        errors = []

        if not self.API_ID:
            errors.append(
                "API_ID is missing or not a valid positive integer."
            )

        if not self.API_HASH:
            errors.append(
                "API_HASH is missing."
            )

        if not self.SESSION_STRING:
            errors.append(
                "SESSION_STRING is missing. "
                "Run 'python generate_session.py' to generate one."
            )

        if not self.ADMIN_USER_ID:
            errors.append(
                "ADMIN_USER_ID is missing."
            )

        if self.AUTO_REPLY_MODE not in (
            "disabled",
            "allowlist",
            "all_private",
            "all",
        ):
            errors.append(
                f"Invalid AUTO_REPLY_MODE "
                f"'{self.AUTO_REPLY_MODE}'. "
                "Must be: disabled, allowlist, all_private, all."
            )

        if self.MESSAGE_DEBOUNCE_SECONDS < 0:
            errors.append(
                "MESSAGE_DEBOUNCE_SECONDS cannot be negative."
            )

        if not self.OLLAMA_HOST:
            errors.append(
                "OLLAMA_HOST is missing."
            )

        if not self.OLLAMA_MODEL:
            errors.append(
                "OLLAMA_MODEL is missing."
            )

        return errors

    # ========================================================
    # SECRET MASKING
    # ========================================================

    @staticmethod
    def mask_secret(
        value: str,
        visible_chars: int = 4
    ) -> str:
        """
        Masks sensitive credentials for safe logging.

        Example:
            abcdefghijkl -> abcd...ijkl
        """

        if not value:
            return "<UNSET>"

        if len(value) <= visible_chars * 2:
            return "****"

        return (
            f"{value[:visible_chars]}"
            f"..."
            f"{value[-visible_chars:]}"
        )


# ============================================================
# GLOBAL CONFIGURATION INSTANCE
# ============================================================

config = Config()