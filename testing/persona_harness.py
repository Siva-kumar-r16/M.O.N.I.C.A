"""
Persona Test Harness for M.O.N.I.C.A.
Executes the comprehensive persona test matrix:
- First contact vs continuing contact behavior
- Tone calibration (normal question, teasing, sarcasm, serious)
- Multilingual support (English, Tamil, Tanglish, Malayalam)
- Zero-hallucination guardrails & private info protection
- AI identity disclosure
- Spam [NO_REPLY] suppression
- Button markup conversion
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from monica.persona import PersonaLoader
from monica.ai import MonicaAIManager
from monica.memory import MemoryManager
from monica.db import DatabaseEngine, MigrationManager, Repository
from testing.fixtures.mock_data import MockAIProvider


class PersonaHarness:
    def __init__(self):
        self.fixtures_path = PROJECT_ROOT / "testing" / "fixtures" / "messages.json"
        with open(self.fixtures_path, "r", encoding="utf-8") as f:
            self.scenarios = json.load(f)["test_scenarios"]

        self.db_path = Path("/tmp/harness_persona.db")
        if self.db_path.exists():
            self.db_path.unlink()

        self.engine = DatabaseEngine(self.db_path)
        self.repo = Repository(self.engine)
        self.mock_ai = MockAIProvider()
        self.persona = PersonaLoader()
        self.memory = MemoryManager(self.repo, ai_client=self.mock_ai)
        self.ai_manager = MonicaAIManager(
            provider=self.mock_ai,
            persona_loader=self.persona,
            memory_manager=self.memory,
        )

    async def setup(self):
        await MigrationManager(self.engine).run_migrations()

    async def teardown(self):
        if self.db_path.exists():
            self.db_path.unlink()
        if self.engine.working_db_path.exists():
            self.engine.working_db_path.unlink()

    async def run_all(self) -> bool:
        await self.setup()
        print("\n" + "=" * 65)
        print("   M.O.N.I.C.A. Persona & Conversational Test Harness")
        print("=" * 65)

        passed = 0
        failed = 0

        for sc in self.scenarios:
            sc_id = sc["id"]
            desc = sc["description"]
            sender = sc["sender_name"]
            is_first = sc["is_first_contact"]
            msg_text = sc["message"]
            crit = sc.get("expected_criteria", {})
            chat_id = f"test_chat_{sc_id}"

            print(f"\n[SCENARIO] {sc_id.upper()}: {desc}")
            print(f"  Input ({sender}): \"{msg_text}\"")

            # Setup stored memory if required
            if "stored_memory" in sc:
                await self.memory.discrete.remember(chat_id, sc["stored_memory"], category="preference")

            incoming = [{"message_id": 1, "message": msg_text, "direction": "incoming", "sender_name": sender}]

            reply_text, buttons = await self.ai_manager.generate_response(
                chat_id=chat_id,
                sender_name=sender,
                incoming_messages=incoming,
                is_first_contact=is_first,
            )

            print(f"  Monica: {repr(reply_text)} (buttons: {bool(buttons)})")

            # Evaluation
            errors = self._evaluate_criteria(sc_id, reply_text, buttons, crit, self.mock_ai.last_system_prompt)

            if not errors:
                print(f"  Status: ✅ PASS")
                passed += 1
            else:
                print(f"  Status: ❌ FAIL - {', '.join(errors)}")
                failed += 1

        print("\n" + "=" * 65)
        print(f"Harness Summary: {passed} PASSED | {failed} FAILED | Total: {len(self.scenarios)}")
        print("=" * 65 + "\n")

        await self.teardown()
        return failed == 0

    def _evaluate_criteria(self, sc_id: str, reply: str, buttons: Any, crit: dict, prompt: str) -> list:
        errors = []

        if crit.get("expects_no_reply"):
            if reply is not None:
                errors.append(f"Expected suppressed output, got: {reply}")
            return errors

        if reply is None:
            errors.append("Expected valid reply text, got None")
            return errors

        low = reply.lower()

        if crit.get("should_mention_monica") and "monica" not in low:
            errors.append("Did not identify as Monica")

        if crit.get("should_mention_siva") and "siva" not in low:
            errors.append("Did not mention Siva")

        if crit.get("should_contain_college") and crit["should_contain_college"].lower() not in low:
            errors.append(f"Missing college name: {crit['should_contain_college']}")

        if crit.get("should_not_repeat_intro"):
            if "i am monica" in low or "i'm monica" in low:
                errors.append("Unnecessarily repeated introduction on subsequent turn")

        if crit.get("admits_ai"):
            if not any(w in low for w in ("ai", "assistant", "manager", "bot")):
                errors.append("Did not clarify AI status")

        if crit.get("refuses_or_states_unknown"):
            if not any(w in low for w in ("do not have", "cannot", "private", "access")):
                errors.append("Failed to state lack of private info")

        if crit.get("recalls_memory"):
            if "11 am" not in low and "morning" not in low:
                errors.append("Failed to recall stored morning meeting preference")

        if crit.get("includes_button_markup") or crit.get("attaches_portfolio_button"):
            if not buttons or len(buttons) == 0:
                errors.append("Expected attached buttons, found None")

        return errors


if __name__ == "__main__":
    harness = PersonaHarness()
    success = asyncio.run(harness.run_all())
    sys.exit(0 if success else 1)
