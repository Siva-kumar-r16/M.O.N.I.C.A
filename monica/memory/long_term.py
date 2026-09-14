"""
Long-term Conversation Summary System for M.O.N.I.C.A.
Periodically condenses extensive dialogue histories into dense, high-signal
conversation summaries stored in SQLite.
"""

import logging
from typing import Any, Dict, List, Optional
from monica.db.repository import Repository

logger = logging.getLogger("Monica.LongTermMemory")

SUMMARY_TRIGGER_THRESHOLD = 15  # Generate summary every 15 new messages


class LongTermMemory:
    def __init__(self, repository: Repository, ai_client: Optional[Any] = None):
        self.repo = repository
        self.ai_client = ai_client

    async def get_summary(self, chat_id: str) -> Optional[str]:
        """Fetches stored summary from SQLite."""
        return await self.repo.get_conversation_summary(chat_id)

    async def should_update_summary(self, chat_id: str) -> bool:
        """Determines if conversation length warrants re-summarization."""
        count = await self.repo.get_message_count(chat_id)
        if count < 6:
            return False
        # If we have reached threshold
        return (count % SUMMARY_TRIGGER_THRESHOLD) == 0

    async def summarize_and_save(self, chat_id: str, sender_name: str = "User") -> Optional[str]:
        """Extracts recent conversation and generates a persistent rolling summary."""
        if not self.ai_client:
            logger.debug("AI client not available for summarization.")
            return None

        history = await self.repo.get_chat_history(chat_id, limit=30)
        if not history or len(history) < 4:
            return None

        current_summary = await self.get_summary(chat_id) or "None"

        conversation_text = "\n".join(
            f"{'Monica' if h.get('direction') == 'outgoing' else h.get('sender_name') or sender_name}: {h.get('message')}"
            for h in history
        )

        prompt = f"""You are Monica's internal memory consolidation system.
Your task is to summarize the key points, agreements, personal details, and ongoing topics from this conversation.
Keep the summary concise (max 4-5 bullet points), factual, and objective.

EXISTING SUMMARY:
{current_summary}

RECENT DIALOGUE:
{conversation_text}

OUTPUT FORMAT:
Provide only the updated bullet points. Do not include introductory or concluding conversational filler.
"""

        try:
            summary = await self.ai_client.generate_reply(
                system_prompt="You are a precise, factual dialogue summarization agent.",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            if summary and summary.strip() and "[NO_REPLY]" not in summary:
                clean_summary = summary.strip()
                count = await self.repo.get_message_count(chat_id)
                await self.repo.save_conversation_summary(chat_id, clean_summary, count)
                logger.info(f"Updated conversation summary for chat {chat_id}.")
                return clean_summary
        except Exception as e:
            logger.error(f"Failed to generate summary for chat {chat_id}: {e}")

        return None
