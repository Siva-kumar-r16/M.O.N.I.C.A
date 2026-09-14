"""
Central AI Orchestration Manager for M.O.N.I.C.A.

Responsibilities:
- Build Monica's system prompt
- Retrieve long-term memory
- Retrieve personal facts
- Assemble recent conversation history
- Generate Ollama response
- Enforce English default replies
- Parse Telegram button markup
- Handle [NO_REPLY]
- Automatically learn explicit durable facts
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from monica.ai.provider import BaseAIProvider
from monica.ai.tools import ToolRegistry
from monica.persona import PersonaLoader
from monica.memory import MemoryManager
from monica.telegram.buttons import ButtonParser

logger = logging.getLogger("Monica.AIManager")


class MonicaAIManager:

    def __init__(
        self,
        provider: BaseAIProvider,
        persona_loader: PersonaLoader,
        memory_manager: MemoryManager,
        tool_registry: Optional[ToolRegistry] = None,
    ):
        self.provider = provider
        self.persona = persona_loader
        self.memory = memory_manager
        self.tools = tool_registry or ToolRegistry()

    # ==================================================================
    # RESPONSE GENERATION
    # ==================================================================

    async def generate_response(
        self,
        chat_id: str,
        sender_name: str,
        incoming_messages: List[Dict[str, Any]],
        is_first_contact: bool = False,
        custom_tone: Optional[str] = None,
    ) -> Tuple[
        Optional[str],
        Optional[List[List[Any]]]
    ]:
        """
        Generate an intelligent, personalized Monica reply.

        Returns:
            (clean_text, buttons)

        If Monica should not reply:
            (None, None)
        """

        logger.info(
            "Generating AI response for chat %s",
            chat_id,
        )

        # ==============================================================
        # 1. RETRIEVE MEMORY
        # ==============================================================

        try:
            mem_ctx = await self.memory.get_context_for_prompt(
                chat_id,
                sender_name=sender_name,
            )
        except Exception as exc:
            logger.error(
                "Memory retrieval failed for chat %s: %s",
                chat_id,
                exc,
                exc_info=True,
            )

            mem_ctx = {
                "memories": [],
                "conversation_summary": None,
                "short_term_messages": [],
            }

        memories = mem_ctx.get(
            "memories",
            [],
        )

        conversation_summary = mem_ctx.get(
            "conversation_summary"
        )

        logger.info(
            "🧠 Memory loaded | chat=%s | facts=%d | summary=%s",
            chat_id,
            len(memories),
            "yes" if conversation_summary else "no",
        )

        # ==============================================================
        # 2. BUILD PERSONA SYSTEM PROMPT
        # ==============================================================

        system_prompt = self.persona.get_system_prompt(
            sender_name=sender_name,
            is_first_contact=is_first_contact,
            memories=memories,
            conversation_summary=conversation_summary,
            custom_tone=custom_tone,
        )

        # ==============================================================
        # 3. LANGUAGE POLICY
        # ==============================================================

        language_instruction = """

LANGUAGE RULE:
- Understand whatever language the user writes in.
- The user may write in Tamil, Hindi, Telugu, Malayalam, Kannada,
  Bengali, Tanglish, Hinglish, Manglish, or another language.
- Unless the user explicitly asks you to reply in another language,
  write the final conversational response in natural English.
- Do NOT automatically switch your reply language just because the
  user used another language.
- If the user explicitly asks for translation, perform the translation.
- If the user explicitly asks you to answer in a specific language,
  follow that request.
- Do not mention this language policy to the user.
"""

        system_prompt += language_instruction

        # ==============================================================
        # 4. FORMAT CONVERSATION
        # ==============================================================

        formatted_messages: List[Dict[str, str]] = []

        # Keep only the most relevant recent messages.
        recent_messages = incoming_messages[-12:]

        for msg in recent_messages:

            role = (
                "assistant"
                if msg.get("direction") == "outgoing"
                else "user"
            )

            content = (
                msg.get("message", "")
                or ""
            ).strip()

            if not content:
                continue

            formatted_messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        if not formatted_messages:
            logger.warning(
                "No usable messages for AI generation in chat %s",
                chat_id,
            )
            return None, None

        # ==============================================================
        # 5. LOG CURRENT MESSAGE
        # ==============================================================

        last_message = formatted_messages[-1].get(
            "content",
            "",
        )

        logger.info(
            "📩 Message for AI [%s]: %s",
            sender_name,
            last_message[:200],
        )

        # ==============================================================
        # 6. OLLAMA
        # ==============================================================

        try:

            logger.info(
                "🤖 Asking Ollama model to generate reply..."
            )

            raw_reply = await self.provider.generate_reply(
                system_prompt=system_prompt,
                messages=formatted_messages,
                temperature=0.5,
            )

        except Exception as exc:

            logger.error(
                "AI provider failed for chat %s: %s",
                chat_id,
                exc,
                exc_info=True,
            )

            return None, None

        # ==============================================================
        # 7. EMPTY RESPONSE
        # ==============================================================

        if not raw_reply or not raw_reply.strip():

            logger.info(
                "AI returned an empty response for chat %s",
                chat_id,
            )

            return None, None

        clean_raw = raw_reply.strip()

        logger.info(
            "🤖 Raw AI response [%s]: %s",
            sender_name,
            clean_raw[:500],
        )

        # ==============================================================
        # 8. NO_REPLY
        # ==============================================================

        if "[NO_REPLY]" in clean_raw:

            logger.info(
                "AI issued [NO_REPLY] for chat %s",
                chat_id,
            )

            return None, None

        # ==============================================================
        # 9. BUTTON MARKUP
        # ==============================================================

        clean_text, buttons = ButtonParser.parse_markup(
            clean_raw
        )

        clean_text = clean_text.strip()

        if not clean_text:

            logger.info(
                "Response became empty after button parsing."
            )

            return None, None

        # ==============================================================
        # 10. LOG FINAL RESPONSE
        # ==============================================================

        logger.info(
            "💬 Monica reply [%s]: %s",
            sender_name,
            clean_text[:500],
        )

        if buttons:
            logger.info(
                "🔘 Generated %d button rows",
                len(buttons),
            )

        # ==============================================================
        # 11. AUTOMATIC FACT MEMORY
        # ==============================================================

        try:

            memory_result = await self.memory.discrete.extract_and_store_auto(
                chat_id=chat_id,
                user_text=last_message,
                ai_reply=clean_text,
            )

            if memory_result:

                logger.info(
                    "🧠 Learned memory: %s",
                    memory_result,
                )

        except Exception as exc:

            # Memory failure must NEVER prevent Monica from replying.
            logger.warning(
                "Automatic memory extraction failed: %s",
                exc,
                exc_info=True,
            )

        return clean_text, buttons