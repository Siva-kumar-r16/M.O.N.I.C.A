"""
AI Provider Abstraction for M.O.N.I.C.A.
Defines the standard contract allowing seamless swapping or extension of AI backends
(e.g., local Ollama, vLLM, OpenAI-compatible APIs, Anthropic) without touching business logic.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseAIProvider(ABC):
    """Abstract interface for AI conversational providers."""

    @abstractmethod
    async def check_connection(self) -> bool:
        """Verifies if the AI backend service is online and reachable."""
        pass

    @abstractmethod
    async def generate_reply(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """Generates a text completion for a chat conversation."""
        pass
