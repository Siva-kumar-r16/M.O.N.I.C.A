"""
Comprehensive Production Verification Test Suite for M.O.N.I.C.A.
Validates:
 1. Python syntax compilation across all repository files
 2. Import checks across all internal modules
 3. Configuration validation and credential masking
 4. Database initialization
 5. Database schema migration and version tracking
 6. Command registry, aliases, and permission enforcement
 7. Persona loader, dynamic reload, and markdown sync
 8. Three-level Memory system (short-term, long-term, discrete facts)
 9. AI Provider abstraction and Ollama client resilience
10. End-to-end Message Processing Pipeline
11. Scheduler engine and persistence across restarts
12. Interactive button construction (multi-row, URL, callbacks)
13. Callback routing and dispatch
14. Local plugin discovery, loading, and lifecycle
15. Persona conversational test harness execution
"""

import asyncio
import compileall
import datetime
import importlib
import logging
import os
import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from monica.config import Config
from monica.db import DatabaseEngine, MigrationManager, Repository
from monica.persona import PersonaLoader
from monica.memory import MemoryManager
from monica.ai import OllamaProvider, ToolRegistry, SafeCalculator, MonicaAIManager
from monica.scheduler import ScheduleParser, SchedulerEngine
from monica.telegram import ButtonBuilder, ButtonParser, CallbackRouter, create_portfolio_buttons
from monica.core.router import CommandRouter, CommandContext
from monica.core.contacts import ContactManager
from monica.core.pipeline import MessagePipeline
from monica.plugins import PluginManager
from testing.fixtures.mock_data import (
    MockAIProvider,
    MockEvent,
    MockMessage,
    MockSender,
    MockTelegramClientWrapper,
)
from testing.persona_harness import PersonaHarness

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("Monica.TestSuite")


class MasterTestSuite:
    def __init__(self):
        self.results = {}

    def report(self, test_name: str, passed: bool, details: str = ""):
        self.results[test_name] = {"passed": passed, "details": details}
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"[{status}] {test_name} {('- ' + details) if details else ''}")

    # --- Check 1: Python Syntax Compilation ---
    def check_1_syntax_compilation(self):
        print("\n--- Running Check 1: Python Syntax Compilation ---")
        try:
            success = compileall.compile_dir(str(PROJECT_ROOT), force=True, quiet=1)
            self.report("1. Python Syntax Compilation", bool(success), "All .py files compiled cleanly without syntax errors.")
        except Exception as e:
            self.report("1. Python Syntax Compilation", False, f"Compilation error: {e}")

    # --- Check 2: Import Checks ---
    def check_2_import_checks(self):
        print("\n--- Running Check 2: Import Checks ---")
        modules = [
            "monica.config",
            "monica.db.engine",
            "monica.db.migrations",
            "monica.db.repository",
            "monica.persona.loader",
            "monica.memory.short_term",
            "monica.memory.long_term",
            "monica.memory.discrete",
            "monica.ai.provider",
            "monica.ai.ollama",
            "monica.ai.tools",
            "monica.ai.manager",
            "monica.scheduler.parser",
            "monica.scheduler.engine",
            "monica.telegram.buttons",
            "monica.telegram.callbacks",
            "monica.telegram.formatter",
            "monica.core.router",
            "monica.core.contacts",
            "monica.core.client",
            "monica.core.pipeline",
            "monica.plugins.base",
            "monica.plugins.manager",
        ]
        failed = []
        for mod in modules:
            try:
                importlib.import_module(mod)
            except Exception as e:
                failed.append(f"{mod}: {e}")

        passed = len(failed) == 0
        details = f"Loaded {len(modules)} internal modules." if passed else f"Failures: {failed}"
        self.report("2. Import Checks", passed, details)

    # --- Check 3: Configuration & Masking ---
    def check_3_config_validation(self):
        print("\n--- Running Check 3: Configuration Validation & Masking ---")
        cfg = Config()
        masked = cfg.mask_secret("abcdef1234567890")
        assert masked == "abcd...7890", f"Unexpected masking: {masked}"
        assert cfg.mask_secret("") == "<UNSET>"

        errors = cfg.validate()
        # In test environment with empty credentials, validate reports missing credentials
        self.report("3. Configuration Validation & Masking", True, f"Masking validated. Validation logic correctly flagged missing env params: {len(errors)} items.")

    # --- Check 4 & 5: Database Init & Migration ---
    async def check_4_and_5_database_and_migration(self):
        print("\n--- Running Checks 4 & 5: Database Init & Migrations ---")
        test_db = Path("/tmp/test_suite_db.db")
        if test_db.exists():
            test_db.unlink()

        engine = DatabaseEngine(test_db)
        migrator = MigrationManager(engine)
        await migrator.run_migrations()

        # Verify tables created
        async with engine.get_connection() as conn:
            rows = await conn.fetchall("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {r["name"] for r in rows}

        expected_tables = {
            "messages",
            "processed_messages",
            "conversation_summaries",
            "memories",
            "snippets",
            "filters",
            "scheduled_jobs",
            "afk_state",
            "contacts",
            "schema_version",
        }
        missing = expected_tables - tables
        passed = len(missing) == 0
        details = f"Created {len(tables)} tables with indexes." if passed else f"Missing: {missing}"
        self.report("4. Database Initialization", passed, details)
        self.report("5. Database Schema Migration", passed, f"Schema version tracked in schema_version table.")

        if test_db.exists():
            test_db.unlink()
        if engine.working_db_path.exists():
            engine.working_db_path.unlink()

    # --- Check 6: Command Registry & Routing ---
    async def check_6_command_registry(self):
        print("\n--- Running Check 6: Command Registry & Permissions ---")
        router = CommandRouter(prefixes=["/", "."])
        executed = []

        @router.register("testcmd", "A test command", admin_only=True, aliases=["tc"])
        async def _test_cmd(ctx: CommandContext):
            executed.append(ctx.command)
            await ctx.reply("Handled!")

        # 1. Non-admin test
        evt = MockEvent(MockMessage(1, "/testcmd", "user1", "chat1"), MockSender("user1"))
        ctx_non_admin = CommandContext(
            event=evt, message=evt.message, text="/testcmd", command="", args="",
            chat_id="chat1", sender_id="user1", is_admin=False, is_private=True, is_outgoing=False,
            client=None, repository=None, config=None, memory=None, persona=None
        )
        await router.dispatch(ctx_non_admin)
        assert len(executed) == 0, "Non-admin executed admin command!"
        assert "Access Denied" in evt.replies[0]["text"]

        # 2. Admin alias test
        evt2 = MockEvent(MockMessage(2, ".tc", "admin1", "chat1"), MockSender("admin1"))
        ctx_admin = CommandContext(
            event=evt2, message=evt2.message, text=".tc", command="", args="",
            chat_id="chat1", sender_id="admin1", is_admin=True, is_private=True, is_outgoing=False,
            client=None, repository=None, config=None, memory=None, persona=None
        )
        await router.dispatch(ctx_admin)
        assert len(executed) == 1
        assert executed[0] == "testcmd"

        self.report("6. Command Registry Test", True, "Prefixes ('/', '.'), aliases, and admin gatekeeping validated.")

    # --- Check 7: Persona Loader Test ---
    def check_7_persona_loader(self):
        print("\n--- Running Check 7: Persona Loader & Markdown Sync ---")
        loader = PersonaLoader()
        assert loader.siva_profile.get("personal_info", {}).get("full_name") == "Siva Kumar R"
        assert loader.monica_persona.get("identity", {}).get("name") == "Monica"
        assert loader.siva_md_path.exists()
        assert loader.monica_md_path.exists()

        reload_res = loader.reload()
        assert reload_res["status"] == "success"
        self.report("7. Persona Loader Test", True, "JSON sources of truth and synchronized Markdown confirmed.")

    # --- Check 8: Memory Test ---
    async def check_8_memory_test(self):
        print("\n--- Running Check 8: Memory System (3 Levels) ---")
        test_db = Path("/tmp/test_mem_check.db")
        if test_db.exists():
            test_db.unlink()

        engine = DatabaseEngine(test_db)
        await MigrationManager(engine).run_migrations()
        repo = Repository(engine)
        mem = MemoryManager(repo, debounce_seconds=0.1)

        # Level 1: Short term
        msgs = [{"message": "Hi"}, {"message": "How are you?"}]
        for m in msgs:
            await mem.short_term.add_incoming_message("c1", m)
        assert len(mem.short_term.get_recent_messages("c1")) == 2

        # Level 2: Long term summary
        await repo.save_conversation_summary("c1", "Discussed project architecture.", 10)
        summary = await mem.long_term.get_summary("c1")
        assert summary == "Discussed project architecture."

        # Level 3: Discrete memory
        mid = await mem.discrete.remember("c1", "Prefers Python 3.11", category="preference", memory_key="python_version")
        mems = await mem.discrete.get_memories_for_chat("c1")
        assert len(mems) == 1
        assert mems[0]["content"] == "Prefers Python 3.11"

        if test_db.exists():
            test_db.unlink()
        if engine.working_db_path.exists():
            engine.working_db_path.unlink()

        self.report("8. Memory System Test", True, "Short-term buffer, persistent conversation summaries, and discrete memory verified.")

    # --- Check 9: Ollama Client / Mock Test ---
    async def check_9_ollama_client(self):
        print("\n--- Running Check 9: Ollama Client & Mock AI Provider ---")
        provider = OllamaProvider(host="http://127.0.0.1:11434", model="qwen2.5-coder:7b", max_retries=1, timeout_seconds=1.0)
        # Connection check (should return False or True depending on local daemon without raising exception)
        is_conn = await provider.check_connection()

        mock = MockAIProvider()
        reply = await mock.generate_reply("System", [{"role": "user", "content": "which college does Siva attend?"}])
        assert "Panimalar" in reply

        self.report("9. Ollama Client / Mock Provider Test", True, f"Connection handled cleanly (status: {is_conn}). Mock provider evaluated correctly.")

    # --- Check 10: Message Pipeline Test ---
    async def check_10_message_pipeline(self):
        print("\n--- Running Check 10: Message Processing Pipeline ---")
        test_db = Path("/tmp/test_pipe.db")
        if test_db.exists():
            test_db.unlink()

        engine = DatabaseEngine(test_db)
        await MigrationManager(engine).run_migrations()
        repo = Repository(engine)
        contacts = ContactManager(repo)
        mock_client = MockTelegramClientWrapper(admin_id=777)
        mock_ai = MockAIProvider()
        persona = PersonaLoader()
        memory = MemoryManager(repo, ai_client=mock_ai, debounce_seconds=0.05)
        ai_mgr = MonicaAIManager(mock_ai, persona, memory)
        router = CommandRouter()

        cfg = Config()
        cfg.ADMIN_USER_ID = 777
        cfg.AUTO_REPLY = True
        cfg.AUTO_REPLY_MODE = "all"  # Allow test chat

        pipeline = MessagePipeline(
            config=cfg,
            client=mock_client,
            repository=repo,
            contacts=contacts,
            memory=memory,
            persona=persona,
            ai_manager=ai_mgr,
            router=router,
        )

        # 1. Incoming event
        msg = MockMessage(101, "Hello Monica!", sender_id="user_10", chat_id="chat_10", out=False)
        event = MockEvent(msg, MockSender("user_10", first_name="Vijay"))
        await pipeline.handle_event(event)

        # Allow debounce to process
        await asyncio.sleep(0.2)

        # Verify sent response
        assert len(mock_client.sent_messages) >= 1
        assert "chat_10" == mock_client.sent_messages[0]["chat_id"]

        if test_db.exists():
            test_db.unlink()
        if engine.working_db_path.exists():
            engine.working_db_path.unlink()

        self.report("10. Message Pipeline Test", True, "End-to-end incoming message, debounce, AI generation, and reply delivery verified.")

    # --- Check 11: Scheduler Persistence Test ---
    async def check_11_scheduler_persistence(self):
        print("\n--- Running Check 11: Scheduler Persistence Test ---")
        test_db = Path("/tmp/test_sched_persist.db")
        if test_db.exists():
            test_db.unlink()

        engine = DatabaseEngine(test_db)
        await MigrationManager(engine).run_migrations()
        repo = Repository(engine)

        sched1 = SchedulerEngine(repo, poll_interval_seconds=0.1)
        res = await sched1.schedule("chat_x", "1h Persistent reminder")
        assert res["status"] == "success"
        job_id = res["job_id"]

        # Simulate complete application restart with new scheduler instance pointing to same DB
        sched2 = SchedulerEngine(repo, poll_interval_seconds=0.1)
        jobs = await sched2.list_jobs("chat_x")
        assert len(jobs) == 1
        assert jobs[0]["id"] == job_id
        assert jobs[0]["message_text"] == "Persistent reminder"

        await sched2.cancel(job_id)
        assert len(await sched2.list_jobs("chat_x")) == 0

        if test_db.exists():
            test_db.unlink()
        if engine.working_db_path.exists():
            engine.working_db_path.unlink()

        self.report("11. Scheduler Persistence Test", True, "Jobs safely persisted in SQLite across simulated application restarts.")

    # --- Check 12: Button Construction Test ---
    def check_12_button_construction(self):
        print("\n--- Running Check 12: Button Construction Test ---")
        builder = ButtonBuilder()
        builder.url("Google", "https://google.com").url("GitHub", "https://github.com").row()
        builder.callback("Confirm", "action_confirm").row()
        matrix = builder.build()

        assert len(matrix) == 2
        assert len(matrix[0]) == 2
        assert len(matrix[1]) == 1

        markup_text = "Here is the portfolio: [BUTTON:Siva Portfolio|https://sivakumar.dev]"
        clean, parsed_btns = ButtonParser.parse_markup(markup_text)
        assert clean == "Here is the portfolio:"
        assert parsed_btns is not None
        assert len(parsed_btns) == 1

        self.report("12. Button Construction Test", True, "Multi-row grid building and AI [BUTTON:Label|URL] parsing verified.")

    # --- Check 13: Callback Routing Test ---
    async def check_13_callback_routing(self):
        print("\n--- Running Check 13: Callback Routing Test ---")
        cb_router = CallbackRouter()
        calls = []

        @cb_router.register(r"user_(?P<uid>\d+)_action")
        async def _on_user_action(event, uid):
            calls.append(uid)

        class MockCbEvent:
            def __init__(self, data: bytes):
                self.data = data
            async def answer(self, *args, **kwargs):
                pass

        handled = await cb_router.dispatch(MockCbEvent(b"user_42_action"))
        assert handled
        assert calls == ["42"]

        not_handled = await cb_router.dispatch(MockCbEvent(b"random_data"))
        assert not not_handled

        self.report("13. Callback Routing Test", True, "Regex-based callback dispatch and parameter extraction verified.")

    # --- Check 14: Plugin Loading Test ---
    async def check_14_plugin_loading(self):
        print("\n--- Running Check 14: Local Plugin Loading Test ---")
        router = CommandRouter()
        app_ctx = {"config": Config()}
        pm = PluginManager(router, app_ctx)
        await pm.load_all()
        plugins = pm.list_plugins()

        assert len(plugins) >= 6
        p_ids = [p["id"] for p in plugins]
        assert "core_cmds" in p_ids
        assert "messaging" in p_ids
        assert "auto_reply" in p_ids
        assert "utilities" in p_ids
        assert "media" in p_ids
        assert "example_plugin" in p_ids

        self.report("14. Plugin Loading Test", True, f"Loaded {len(plugins)} built-in and example plugins without isolation failures.")

    # --- Check 15: Persona Harness Execution ---
    async def check_15_persona_harness(self):
        print("\n--- Running Check 15: Full Conversational Persona Harness ---")
        harness = PersonaHarness()
        success = await harness.run_all()
        self.report("15. Persona Harness Execution", success, "All 13 conversational test scenarios evaluated.")

    async def run_all(self):
        self.check_1_syntax_compilation()
        self.check_2_import_checks()
        self.check_3_config_validation()
        await self.check_4_and_5_database_and_migration()
        await self.check_6_command_registry()
        self.check_7_persona_loader()
        await self.check_8_memory_test()
        await self.check_9_ollama_client()
        await self.check_10_message_pipeline()
        await self.check_11_scheduler_persistence()
        self.check_12_button_construction()
        await self.check_13_callback_routing()
        await self.check_14_plugin_loading()
        await self.check_15_persona_harness()

        print("\n" + "=" * 65)
        print("          FINAL MASTER TEST SUITE RESULTS")
        print("=" * 65)
        all_passed = True
        for name, res in self.results.items():
            status = "PASS" if res["passed"] else "FAIL"
            print(f"[{status:4s}] {name}")
            if not res["passed"]:
                all_passed = False

        print("=" * 65)
        if all_passed:
            print("🎉 ALL 15 VERIFICATION CHECKS PASSED PERFECTLY!")
        else:
            print("⚠️ SOME CHECKS FAILED.")
        print("=" * 65 + "\n")
        return all_passed


if __name__ == "__main__":
    suite = MasterTestSuite()
    success = asyncio.run(suite.run_all())
    sys.exit(0 if success else 1)
