"""
Startup Wiring Smoke Test for M.O.N.I.C.A.

Runs the REAL `main()` coroutine end-to-end (the actual entry point used by
`python main.py`), but with:
  - a disposable scratch database (never the real data/monica.db)
  - Telegram credentials blanked in-memory (so it takes the safe
    "credentials not fully configured -> background worker mode" path
    instead of opening a real MTProto connection)
  - BOT_TOKEN blanked in-memory (proving it's genuinely optional)
  - no dependency on a running Ollama instance (the connectivity check
    is a fire-and-forget background task that fails gracefully offline,
    exactly as already verified in isolation)
  - the shutdown signal fired immediately, so `main()` runs its full
    startup + shutdown sequence and returns instead of blocking forever

This specifically catches the class of bug a plain "import every module"
check CANNOT catch: a NameError for a name that is only referenced inside
a function body (like `default_callback_router` used inside `async def
main()`), which only surfaces when that line actually EXECUTES, not when
the module is merely imported.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import main as monica_main  # noqa: E402
from monica.config import config  # noqa: E402


async def run_smoke_test():
    print("=" * 65)
    print("  M.O.N.I.C.A. — Startup Wiring Smoke Test")
    print("  (no real Telegram credentials, BOT_TOKEN, or Ollama required)")
    print("=" * 65)

    scratch_dir = Path("/tmp/monica_smoke_test")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    scratch_db = scratch_dir / "smoke.db"
    if scratch_db.exists():
        scratch_db.unlink()

    # Redirect everything sensitive/persistent to disposable scratch paths
    # and blank credentials IN MEMORY ONLY. This never reads or writes the
    # real .env file, the real database, or any real secret.
    config.DATABASE_PATH = scratch_db
    config.LOG_FILE = scratch_dir / "smoke.log"
    config.API_ID = 0
    config.API_HASH = ""
    config.SESSION_STRING = ""
    config.BOT_TOKEN = ""
    config.ADMIN_USER_ID = 999999

    # main.py deliberately blocks startup if config.validate() fails,
    # UNLESS run in headless test mode via --test/--mock (this is an
    # existing, pre-existing safeguard in main.py, not something added
    # here). We rely on that same bypass so this smoke test genuinely
    # exercises the app_context/callback-router wiring instead of
    # exiting early at the validation guard.
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0], "--test"]

    # main() waits on `stop_event.wait()` until a signal handler fires it.
    # There's no signal to send in this harness, so we make Event.wait()
    # resolve immediately -- this exercises the exact same shutdown code
    # path (finally: block) that a real Ctrl+C would.
    original_wait = asyncio.Event.wait

    async def _immediate_wait(self):
        return True

    passed = False
    error = None
    try:
        with patch.object(asyncio.Event, "wait", _immediate_wait):
            await asyncio.wait_for(monica_main.main(), timeout=30)
        passed = True
    except Exception as e:
        error = e
    finally:
        asyncio.Event.wait = original_wait
        sys.argv = original_argv

    print()
    if passed:
        print("[PASS] main() executed fully: config validation, DB init,")
        print("       persona/memory/AI wiring, plugin loading, callback-")
        print("       router wiring, and clean shutdown -- with NO NameError")
        print("       and NO real Telegram/BOT_TOKEN/Ollama dependency.")
    else:
        print(f"[FAIL] main() raised: {type(error).__name__}: {error}")

    return passed


if __name__ == "__main__":
    ok = asyncio.run(run_smoke_test())
    sys.exit(0 if ok else 1)
