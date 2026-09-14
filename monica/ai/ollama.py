"""
Fast Local Ollama Client for M.O.N.I.C.A.

Optimized for fast Telegram replies:
- Reuses one HTTP connection
- Short response generation
- Keeps Ollama model loaded in memory
- No unnecessary retry delays
- Configurable generation limits
"""

import logging
from typing import Any, Dict, List, Optional

import httpx

from monica.ai.provider import BaseAIProvider

logger = logging.getLogger("Monica.Ollama")


class OllamaProvider(BaseAIProvider):
    def __init__(
        self,
        host: str = "http://127.0.0.1:11434",
        model: str = "qwen2.5-coder:7b",
        timeout_seconds: float = 45.0,
        max_retries: int = 1,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout_seconds
        self.max_retries = max_retries

        # Reuse the same HTTP client instead of creating one per message.
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=3.0,
                read=self.timeout,
                write=5.0,
                pool=3.0,
            ),
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
            ),
        )

    async def check_connection(self) -> bool:
        """Check whether Ollama is running and the configured model exists."""
        url = f"{self.host}/api/tags"

        try:
            response = await self.client.get(url)

            if response.status_code != 200:
                logger.error(
                    "Ollama returned HTTP %s",
                    response.status_code,
                )
                return False

            data = response.json()

            models = [
                model.get("name", "")
                for model in data.get("models", [])
            ]

            has_model = any(
                self.model == name or self.model in name
                for name in models
            )

            if not has_model:
                logger.warning(
                    "Model '%s' not found. Installed: %s",
                    self.model,
                    models,
                )
                return False

            logger.info("Ollama ready: %s", self.model)
            return True

        except Exception as exc:
            logger.warning(
                "Cannot connect to Ollama at %s: %s",
                self.host,
                exc,
            )
            return False

    async def generate_reply(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        """
        Generate a fast response from Ollama.
        """

        url = f"{self.host}/api/chat"

        full_messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        # Keep only the most recent messages.
        # This prevents huge conversation history from slowing Qwen down.
        recent_messages = messages[-8:]

        full_messages.extend(recent_messages)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,

            # We need the complete response before sending Telegram reply.
            "stream": False,

            # Keep the model loaded.
            "keep_alive": "30m",

            "options": {
                # Lower temperature = faster/more predictable responses.
                "temperature": min(temperature, 0.5),

                # Telegram conversations normally don't need huge replies.
                "num_predict": 120,

                # Helps reduce unnecessary internal context processing.
                "num_ctx": 4096,

                # Keep model work focused.
                "top_p": 0.9,
            },
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = await self.client.post(
                    url,
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()

                    content = (
                        data
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                    if content:
                        logger.info(
                            "⚡ Ollama generated reply (%d chars)",
                            len(content),
                        )

                    return content or None

                logger.warning(
                    "Ollama HTTP %s on attempt %d",
                    response.status_code,
                    attempt,
                )

            except httpx.TimeoutException:
                logger.warning(
                    "Ollama timeout on attempt %d/%d",
                    attempt,
                    self.max_retries,
                )

            except httpx.ConnectError as exc:
                logger.warning(
                    "Ollama connection error: %s",
                    exc,
                )

            except Exception as exc:
                logger.error(
                    "Ollama error: %s",
                    exc,
                    exc_info=True,
                )

        return None

    async def close(self):
        """Close the persistent HTTP client."""
        if not self.client.is_closed:
            await self.client.aclose()