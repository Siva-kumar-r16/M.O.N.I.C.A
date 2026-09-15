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
        """
        Records a discrete fact into SQLite.

        If a memory_key is given and a memory with that exact key already
        exists for this chat, its content is UPDATED IN PLACE rather than
        inserting a duplicate row -- this is what lets facts like "my name
        is X" get refreshed if the user later says "my name is Y", instead
        of both versions being remembered forever.
        """
        content = content.strip()

        if memory_key:
            existing = await self.repo.get_memory_by_key(chat_id, memory_key)
            if existing:
                if existing.get("content", "").strip() == content:
                    # Nothing changed -- avoid a pointless duplicate write.
                    return existing["id"]
                await self.repo.update_memory_content(existing["id"], content)
                logger.info(
                    f"Updated memory #{existing['id']} for chat {chat_id}: [{category}] {content}"
                )
                return existing["id"]

        mem_id = await self.repo.add_memory(
            chat_id=chat_id,
            category=category,
            content=content,
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

        # Rule-based heuristics for quick, high-precision detection.
        # `singular=True` fields have exactly one true value at a time (a
        # person only has one name/birthday/location/occupation), so a
        # fixed memory_key means a newer statement correctly overwrites
        # the old one instead of creating a duplicate.
        # `singular=False` fields (open-ended preferences/dislikes) get a
        # key derived from *what* was liked/disliked, so "I like coffee"
        # and "I like hiking" are both kept, while repeating the same
        # preference just refreshes it instead of duplicating it.
        patterns = [
            (r"\bmy name is ([a-zA-Z\s]+)", "preference", "user_name", True),
            (r"\bcall me ([a-zA-Z\s]+)", "preference", "user_nickname", True),
            (r"\bi (?:prefer|like|love) (.+)", "preference", "preference", False),
            (r"\bi (?:hate|dislike|can't stand) (.+)", "preference", "dislike", False),
            (r"\bmy (?:birthday|bday) is (.+)", "fact", "birthday", True),
            (r"\bi live in (.+)", "fact", "location", True),
            (r"\bi work as (?:a|an)? (.+)", "fact", "occupation", True),
        ]

        for pat, cat, base_key, singular in patterns:
            match = re.search(pat, text)
            if match:
                fact_content = user_text.strip()
                if singular:
                    memory_key = base_key
                else:
                    captured = re.sub(r"[^a-z0-9]+", "_", match.group(1).strip().lower()).strip("_")
                    memory_key = f"{base_key}:{captured[:40]}" if captured else base_key

                await self.remember(chat_id, fact_content, category=cat, memory_key=memory_key)
                return {"category": cat, "key": memory_key, "content": fact_content}

        return None
