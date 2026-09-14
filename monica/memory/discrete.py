"""
Discrete Facts & Memory Management for M.O.N.I.C.A. (Level 3 Memory)
Supports manual curation (/remember, /forget, /memory, /reset) and careful automatic extraction
of durable user facts, preferences, relationship details, and topics.
"""

import logging
import re
from typing import Any, Dict, List, Optional
from monica.db.repository import Repository

logger = logging.getLogger("Monica.DiscreteMemory")


class DiscreteMemory:
    def __init__(self, repository: Repository, ai_client: Optional[Any] = None):
        self.repo = repository
        self.ai_client = ai_client

    async def remember(
        self, chat_id: str, content: str, category: str = "fact", memory_key: Optional[str] = None
    ) -> int:
        """Manually records a discrete fact into SQLite."""
        mem_id = await self.repo.add_memory(
            chat_id=chat_id,
            category=category,
            content=content.strip(),
            memory_key=memory_key,
        )
        logger.info(f"Saved memory #{mem_id} for chat {chat_id}: [{category}] {content}")
        return mem_id

    async def forget(self, memory_id: int) -> bool:
        """Deactivates a discrete memory by ID."""
        return await self.repo.delete_memory(memory_id)

    async def get_memories_for_chat(self, chat_id: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieves active memories relevant to this chat or global."""
        return await self.repo.get_memories_for_context(chat_id, limit=limit)

    async def search(self, query: str, chat_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches discrete memories by substring / key."""
        return await self.repo.search_memories(query, chat_id)

    async def reset(self, chat_id: Optional[str] = None) -> int:
        """Deactivates all memories for a chat or globally."""
        return await self.repo.clear_memories(chat_id)

    async def extract_and_store_auto(self, chat_id: str, user_text: str, ai_reply: str) -> Optional[Dict[str, str]]:
        """
        Carefully extracts persistent user facts or preferences.
        Only triggers on explicit indicators ('I prefer...', 'My name is...', 'My birthday is...').
        Never stores trivial greetings, temporary status, or spam.
        """
        text = user_text.strip().lower()

        # Rule-based heuristics for quick, high-precision detection
        patterns = [
            (r"\bmy name is ([a-zA-Z\s]+)", "preference", "user_name"),
            (r"\bcall me ([a-zA-Z\s]+)", "preference", "user_nickname"),
            (r"\bi (?:prefer|like|love) (.+)", "preference", "preference"),
            (r"\bi (?:hate|dislike|can't stand) (.+)", "preference", "dislike"),
            (r"\bmy (?:birthday|bday) is (.+)", "fact", "birthday"),
            (r"\bi live in (.+)", "fact", "location"),
            (r"\bi work as (?:a|an)? (.+)", "fact", "occupation"),
        ]

        for pat, cat, key in patterns:
            match = re.search(pat, text)
            if match:
                fact_content = user_text.strip()
                # Check for duplicate
                existing = await self.repo.search_memories(match.group(1), chat_id)
                if not existing:
                    await self.remember(chat_id, fact_content, category=cat, memory_key=key)
                    return {"category": cat, "key": key, "content": fact_content}

        return None
