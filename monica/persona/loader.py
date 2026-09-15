"""
Persona Loader for M.O.N.I.C.A.
Loads JSON configuration sources of truth and synchronizes markdown representations.
Provides runtime prompts and dynamic reload capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("Monica.PersonaLoader")


class PersonaLoader:
    def __init__(self, persona_dir: Optional[Path] = None):
        if persona_dir is None:
            self.persona_dir = Path(__file__).resolve().parent
        else:
            self.persona_dir = Path(persona_dir)

        self.siva_json_path = self.persona_dir / "siva_profile.json"
        self.monica_json_path = self.persona_dir / "monica_persona.json"
        self.siva_md_path = self.persona_dir / "siva_profile.md"
        self.monica_md_path = self.persona_dir / "monica_persona.md"

        self.siva_profile: Dict[str, Any] = {}
        self.monica_persona: Dict[str, Any] = {}

        self.load()

    def load(self):
        """Loads JSON files as source of truth and generates markdown files."""
        try:
            if self.siva_json_path.exists():
                with open(self.siva_json_path, "r", encoding="utf-8") as f:
                    self.siva_profile = json.load(f)
            else:
                logger.error(f"Missing {self.siva_json_path}")

            if self.monica_json_path.exists():
                with open(self.monica_json_path, "r", encoding="utf-8") as f:
                    self.monica_persona = json.load(f)
            else:
                logger.error(f"Missing {self.monica_json_path}")

            self._generate_markdown()
            logger.info("Persona and profile loaded and synced successfully.")
        except Exception as e:
            logger.error(f"Error loading persona definitions: {e}", exc_info=True)

    def reload(self) -> Dict[str, Any]:
        """Reloads persona definitions on the fly without application restart."""
        self.load()
        return {
            "status": "success",
            "persona_name": self.monica_persona.get("identity", {}).get("name", "Monica"),
            "owner": self.siva_profile.get("personal_info", {}).get("full_name", "Siva Kumar R"),
        }

    def _generate_markdown(self):
        """Generates markdown representations from the JSON source of truth."""
        # Generate siva_profile.md
        p = self.siva_profile.get("personal_info", {})
        skills = self.siva_profile.get("technical_skills", {})
        projects = self.siva_profile.get("projects", [])
        allowed = self.siva_profile.get("allowed_facts", [])
        forbidden = self.siva_profile.get("forbidden_inventions", [])

        siva_md_lines = [
            f"# Profile: {p.get('full_name', 'Siva Kumar R')}",
            f"- **Role**: {p.get('role', 'Developer')}",
            f"- **Institution**: {p.get('institution', 'Panimalar Engineering College')}",
            f"- **Location**: {p.get('location', 'Chennai, Tamil Nadu, India')}",
            f"- **Portfolio**: {p.get('portfolio_url', '')}",
            f"- **GitHub**: {p.get('github_url', '')}",
            f"- **LinkedIn**: {p.get('linkedin_url', '')}",
            "",
            "## Technical Skills",
            f"- **Languages**: {', '.join(skills.get('languages', []))}",
            f"- **Frameworks & Tools**: {', '.join(skills.get('frameworks_and_tools', []))}",
            f"- **Domains**: {', '.join(skills.get('domains', []))}",
            f"- **Architecture Preference**: {skills.get('architecture_preferences', '')}",
            "",
            "## Featured Projects",
        ]
        for proj in projects:
            siva_md_lines.append(f"- **{proj.get('name')}**: {proj.get('description')}")

        siva_md_lines.append("\n## Allowed Facts")
        for fact in allowed:
            siva_md_lines.append(f"- {fact}")

        siva_md_lines.append("\n## Forbidden Inventions")
        for fbd in forbidden:
            siva_md_lines.append(f"- {fbd}")

        self.siva_md_path.write_text("\n".join(siva_md_lines), encoding="utf-8")

        # Generate monica_persona.md
        ident = self.monica_persona.get("identity", {})
        pers = self.monica_persona.get("personality", {})
        lang = self.monica_persona.get("language_policy", {})
        rules = self.monica_persona.get("hard_rules", [])
        examples = self.monica_persona.get("dialogue_examples", [])

        monica_md_lines = [
            f"# Persona: {ident.get('name', 'Monica')}",
            f"**Full Title**: {ident.get('full_title', '')}",
            f"**Role**: {ident.get('role', '')}",
            f"**Creator**: {ident.get('creator', '')}",
            "",
            "## Personality & Tone",
            f"- **Traits**: {', '.join(pers.get('core_traits', []))}",
            f"- **Sarcasm Level**: {pers.get('sarcasm_level', '')}",
            f"- **Emoji Level**: {pers.get('emoji_level', '')}",
            "",
            "### Tone Spectrum",
        ]
        for tone_k, tone_v in pers.get("tone_spectrum", {}).items():
            monica_md_lines.append(f"- **{tone_k.replace('_', ' ').title()}**: {tone_v}")

        monica_md_lines.append("\n## Language Policy")
        monica_md_lines.append(f"- **Supported**: {', '.join(lang.get('supported_languages', []))}")
        monica_md_lines.append(f"- **Policy**: {lang.get('detection_rule', '')}")

        monica_md_lines.append("\n## Hard Rules")
        for r in rules:
            monica_md_lines.append(f"- {r}")

        monica_md_lines.append("\n## Dialogue Examples")
        for ex in examples:
            monica_md_lines.append(f"### Category: {ex.get('category')}")
            monica_md_lines.append(f"- **User**: \"{ex.get('user')}\"")
            monica_md_lines.append(f"- **Monica**: \"{ex.get('response')}\"")
            monica_md_lines.append("")

        self.monica_md_path.write_text("\n".join(monica_md_lines), encoding="utf-8")

    def get_system_prompt(
        self,
        sender_name: str = "User",
        is_first_contact: bool = False,
        memories: Optional[list] = None,
        conversation_summary: Optional[str] = None,
        custom_tone: Optional[str] = None,
    ) -> str:
        """Constructs an intelligent, contextual system prompt for Monica AI."""
        p_info = self.siva_profile.get("personal_info", {})
        allowed = "\n".join(f"- {f}" for f in self.siva_profile.get("allowed_facts", []))
        forbidden = "\n".join(f"- {f}" for f in self.siva_profile.get("forbidden_inventions", []))
        rules = "\n".join(f"- {r}" for r in self.monica_persona.get("hard_rules", []))
        examples = "\n".join(
            f"User: {e.get('user')}\nMonica: {e.get('response')}"
            for e in self.monica_persona.get("dialogue_examples", [])
        )

        memory_section = ""
        if memories:
            mem_items = "\n".join(f"- [{m.get('category', 'fact')}]: {m.get('content')}" for m in memories)
            memory_section = f"\nRELEVANT MEMORIES & FACTS ABOUT USER / CONTEXT:\n{mem_items}\n"

        summary_section = ""
        if conversation_summary:
            summary_section = f"\nPAST CONVERSATION SUMMARY FOR THIS CHAT:\n{conversation_summary}\n"

        first_contact_directive = (
            "FIRST INTERACTION NOTE: This is your FIRST interaction with this contact. "
            "Introduce yourself naturally once as Monica, Siva Kumar's personal manager/assistant, "
            "and offer assistance or provide his portfolio link [BUTTON:Open Portfolio|https://sivakumar.dev] if appropriate."
            if is_first_contact
            else "CONTINUING CONVERSATION NOTE: You have already interacted with this contact. "
                 "DO NOT re-introduce yourself ('Hi, I'm Monica'). Continue the discussion naturally."
        )

        custom_tone_directive = f"\nCUSTOM CHAT STYLE OVERRIDE: {custom_tone}\n" if custom_tone else ""

        prompt = f"""You are Monica (M.O.N.I.C.A. — Multimodal Operational Neural Intelligence & Conversational Assistant).
You are the personal manager, executive assistant, and intelligent communicator for Siva Kumar R.

ABOUT SIVA KUMAR R:
- Full Name: {p_info.get('full_name')}
- Role: {p_info.get('role')} at {p_info.get('institution')}
- Location: {p_info.get('location')}
- Portfolio: {p_info.get('portfolio_url')}

AUTHORIZED KNOWLEDGE (What you know for sure):
{allowed}

STRICT BOUNDARIES (Never fabricate or assume):
{forbidden}

CORE OPERATIONAL RULES:
{rules}
{first_contact_directive}
{custom_tone_directive}
{summary_section}
{memory_section}
LANGUAGE CAPABILITY:
- You can understand English, Tamil (தமிழ்), Malayalam (മലയാളം), Hindi, Tanglish, and Manglish.
- The separate LANGUAGE RULE appended after this prompt governs which language you actually
  REPLY in -- follow that rule exactly; it takes precedence over anything implied here.

CONTINUOUS CONVERSATION -- THIS IS NOT A ONE-OFF Q&A:
- You are in an ongoing relationship with this contact, not answering isolated questions.
- Use PAST CONVERSATION SUMMARY and RELEVANT MEMORIES above to understand context the user
  doesn't repeat. If they reference something from before ("as I said", "that thing I mentioned",
  "do you remember?"), rely on that memory/summary to know what they mean.
- Short or vague follow-ups like "yes", "okay", "then?", "what about that?", "continue" are NOT
  new isolated requests -- read them against the immediately preceding messages and respond as
  the natural next line of that same conversation.
- Never say things like "I don't have information about that", "I remember that...", "According
  to my memory...", or "I have stored this" -- using memory should be invisible. Just respond as
  someone who naturally recalls the relevant context, without narrating that you looked it up.
- Avoid generic filler openers/closers ("That's interesting!", "How can I help you today?",
  "Sure, I can help with that!") unless they genuinely fit what's being said. Respond the way a
  real person continuing a real conversation would.

INTERACTIVE BUTTON CAPABILITY:
- If sharing a link like Siva's portfolio, attach a button markup at the end of your response formatted as:
  [BUTTON:Button Label|https://valid-url.com]
- Example: "Here is Siva's portfolio: [BUTTON:Open Portfolio|https://sivakumar.dev]"
- Do not overuse buttons. Use them when providing URLs, portfolios, or key interactive choices.

STYLE & TONE EXAMPLES:
{examples}

You are talking to: {sender_name}. Respond naturally, concisely, elegantly, and stay in character.
"""
        return prompt.strip()
