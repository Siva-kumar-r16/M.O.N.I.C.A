"""
Mock Fixtures & Simulators for M.O.N.I.C.A. Testing Suite.
Allows end-to-end verification without live Telegram credentials or external Ollama daemons.
"""

import datetime
from typing import Any, Dict, List, Optional
from monica.ai.provider import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """Deterministic AI Provider returning scenario-matched responses for automated testing."""

    def __init__(self):
        self.last_system_prompt: str = ""
        self.last_messages: List[Dict[str, str]] = []
        self.custom_responses: Dict[str, str] = {}

    async def check_connection(self) -> bool:
        return True

    def set_response_for_keyword(self, keyword: str, response: str):
        self.custom_responses[keyword.lower()] = response

    async def generate_reply(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[str]:
        self.last_system_prompt = system_prompt
        self.last_messages = messages

        if not messages:
            return "[NO_REPLY]"

        user_content = messages[-1].get("content", "").lower()

        # Check custom keyword response mappings
        for k, v in self.custom_responses.items():
            if k in user_content:
                return v

        # Scenario-based deterministic matching
        if "you won 10,000 usdt" in user_content:
            return "[NO_REPLY]"

        if "is siva available" in user_content:
            if "FIRST INTERACTION NOTE" in system_prompt:
                return "Hello! I'm Monica, Siva Kumar's personal manager. Siva is currently away. How can I assist you?"
            return "Siva is still away, but I can pass a note to him right away."

        if "which college" in user_content or "panimalar" in user_content:
            return "Siva is studying Computer Science at Panimalar Engineering College in Chennai. He has developed projects such as M.O.N.I.C.A., LogLens, and IoT safety systems."

        if "sleeping again" in user_content or "hiding behind your bot" in user_content:
            return "Not sleeping—just engineering! He builds the code and I handle witty remarks from friends. 😉 What's up?"

        if "bow down" in user_content:
            return "A respectful nod will suffice! How can his chief of staff help you today?"

        if "portfolio" in user_content or "resume" in user_content or "github" in user_content:
            return "Here is Siva's portfolio showcasing his projects and code: [BUTTON:Open Portfolio|https://sivakumar.dev]"

        if "வணக்கம்" in user_content or "சிவா" in user_content:
            return "வணக்கம்! நான் மோனிகா, சிவாவின் தனிப்பட்ட உதவியாளர். சிவா தற்போது பிஸியாக இருக்கிறார், நான் என்ன உதவி செய்ய வேண்டும்?"

        if "enna pandran" in user_content or "machi" in user_content:
            return "Siva konjam busy-ah irukaaru bro. Enna matter-nu sonneenga na naan inform pandren!"

        if "evidaya bro" in user_content or "chodhikkan" in user_content:
            return "Siva ippo kurachu busy aanu bro. Entha karyam? Njan message ariyikkam!"

        if "are you a bot" in user_content or "are you typing this" in user_content:
            return "I am Monica, an AI personal manager created by Siva Kumar to manage his communications and digital workflow."

        if "private home address" in user_content or "bank account" in user_content:
            return "I do not have access to Siva's private personal or financial information."

        if "schedule our sync" in user_content and "morning meetings before 11 am" in system_prompt.lower():
            return "Based on your preference for morning meetings before 11 AM, would tomorrow at 10:00 AM work for you?"

        return "I understand. I have noted that down for Siva."


class MockMessage:
    def __init__(self, id: int, text: str, sender_id: str, chat_id: str, out: bool = False):
        self.id = id
        self.text = text
        self.message = text
        self.sender_id = sender_id
        self.chat_id = chat_id
        self.out = out
        self.date = datetime.datetime.now()
        self.media = None
        self.is_reply = False
        self._reply_message = None

    def set_reply_to(self, msg: "MockMessage"):
        self.is_reply = True
        self._reply_message = msg

    async def delete(self):
        pass

    async def edit(self, text: str, **kwargs):
        self.text = text
        self.message = text
        return self


class MockSender:
    def __init__(self, id: str, first_name: str = "User", last_name: str = "", username: Optional[str] = None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.title = first_name


class MockEvent:
    def __init__(self, message: MockMessage, sender: MockSender, is_private: bool = True):
        self.message = message
        self.chat_id = message.chat_id
        self.sender_id = message.sender_id
        self.is_private = is_private
        self.sender = sender
        self.replies: List[Dict[str, Any]] = []

    async def get_sender(self):
        return self.sender

    async def get_reply_message(self):
        return self.message._reply_message

    async def reply(self, text: str, buttons: Any = None, **kwargs):
        self.replies.append({"text": text, "buttons": buttons})
        return MockMessage(id=self.message.id + 1, text=text, sender_id="bot", chat_id=self.chat_id, out=True)

    async def respond(self, text: str, buttons: Any = None, **kwargs):
        return await self.reply(text, buttons=buttons, **kwargs)


class MockTelegramClientWrapper:
    def __init__(self, admin_id: int = 12345):
        self.me = MockSender(id=str(admin_id), first_name="Siva", last_name="Kumar", username="sivakumar")
        self.sent_messages: List[Dict[str, Any]] = []

    async def send_message(self, chat_id, text, reply_to=None, buttons=None, parse_mode="md"):
        msg = MockMessage(
            id=len(self.sent_messages) + 1000,
            text=text,
            sender_id=str(self.me.id),
            chat_id=str(chat_id),
            out=True,
        )
        self.sent_messages.append({"chat_id": str(chat_id), "text": text, "reply_to": reply_to, "buttons": buttons})
        return msg

    async def edit_message(self, chat_id, message_id, text, buttons=None, parse_mode="md"):
        return MockMessage(id=message_id, text=text, sender_id=str(self.me.id), chat_id=str(chat_id), out=True)

    async def delete_messages(self, chat_id, message_ids):
        pass

    async def stop(self):
        pass
