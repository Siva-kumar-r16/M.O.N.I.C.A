🧠 M.O.N.I.C.A.

Multimodal Operational Neural Intelligence & Conversational Assistant

M.O.N.I.C.A. is a personal AI-powered Telegram manager and conversational assistant built with Python, Telegram MTProto, Telethon, Ollama, and local Large Language Models.

The goal of M.O.N.I.C.A. is to combine AI, memory, automation, communication, plugins, and personal assistance into one modular system.

✨ Features

🤖 Local AI using Ollama

🧠 Short-term conversation memory

💾 Long-term conversation summaries

👤 Personal facts and preferences

💬 Telegram personal-account integration

🔘 Telegram inline and hyperlink buttons

⚙️ Modular plugin architecture

⏰ Persistent scheduler

🛠️ Command system

👥 Contact and auto-reply management

📝 Keyword filters and snippets

🎭 Custom AI persona

🔐 Local credential and runtime-data protection

🧩 Extensible AI tools

🧪 Testing utilities

🌍 Multilingual message understanding

🇬🇧 English replies by default

🧠 Architecture

                         ┌──────────────────────┐
                         │       Telegram       │
                         │   Personal Account   │
                         └──────────┬───────────┘
                                    │
                                  MTProto
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     M.O.N.I.C.A.     │
                         │                      │
                         │  Message Pipeline    │
                         │  Command Router      │
                         │  Contact Manager     │
                         │  Plugin Manager      │
                         │  Scheduler           │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
                🧠 Memory        🎭 Persona        🛠️ Tools
                    │               │                │
                    └───────────────┼────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      AI Manager      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │        Ollama        │
                         │                      │
                         │      Local LLM       │
                         │   Qwen 2.5 Coder 7B  │
                         └──────────────────────┘


🔄 Message Flow

A normal incoming message follows this architecture:

Telegram Message
       ↓
Telegram Client
       ↓
Message Pipeline
       ↓
Command / Filter / Contact Checks
       ↓
Memory Context
       ↓
Persona Context
       ↓
AI Manager
       ↓
Ollama
       ↓
Qwen 2.5 Coder 7B
       ↓
Response Parser
       ↓
Telegram Reply
       ↓
Background Memory Consolidation


🧠 Memory System

M.O.N.I.C.A. uses a multi-level memory architecture.

Level 1 — Short-Term Memory
Stores recent conversation context for fast AI responses.

Recent Messages
      ↓
Short-Term Buffer
      ↓
AI Context


This allows M.O.N.I.C.A. to understand the current conversation without repeatedly processing the entire chat.

Level 2 — Long-Term Memory
Older conversations can be summarized and stored as persistent conversation summaries.

Conversation
     ↓
Message Threshold
     ↓
AI Summarization
     ↓
SQLite
     ↓
Long-Term Context


Long-term summarization is performed in the background so it does not intentionally block normal Telegram replies.

Level 3 — Discrete Memory
M.O.N.I.C.A. can store useful personal facts and preferences.
Examples:

"My name is Rahul."

"I prefer Python."

"I like coffee."

"I live in Chennai."

These memories can later be retrieved and used to personalize conversations.

🤖 AI Backend

M.O.N.I.C.A. currently uses:

Ollama
   ↓
Qwen 2.5 Coder 7B


The AI model runs locally through Ollama. The AI provider is separated from the rest of the application so the model/backend can be changed later without redesigning the entire system.

🌍 Language Handling

M.O.N.I.C.A. is designed to understand messages written in different languages and mixed-language forms.
Examples include:

English

Tamil

Tanglish

Hindi

Hinglish

Telugu

Malayalam

Kannada

Bengali

Other languages

By default, M.O.N.I.C.A. responds in natural English unless the user explicitly requests another language.

💬 Telegram Integration

M.O.N.I.C.A. uses Telegram MTProto through Telethon.
Unlike a traditional Telegram Bot API application, M.O.N.I.C.A. is designed to operate through a personal Telegram account.
Current capabilities include:

📩 Receiving messages

📤 Sending messages

↩️ Replying to messages

✏️ Editing messages

🗑️ Deleting messages

🔘 Inline buttons

🔗 Hyperlink buttons

🛠️ Commands

👥 Contact management

🤖 Automated replies

📝 Keyword filters

📌 Snippets

🔘 Interactive Buttons

M.O.N.I.C.A. includes a Telegram button parser for interactive responses.
Example:

Choose an option:

[ Open Website ]
[ Continue ]
[ Cancel ]


Buttons can be generated and handled through the Telegram module.

🧩 Plugin System

M.O.N.I.C.A. uses a modular plugin architecture.
Current plugin areas include:

monica/plugins/
│
├── auto_reply/
├── core_cmds/
├── example_plugin/
├── media/
├── messaging/
└── utilities/


The plugin architecture allows functionality to be added independently without modifying the entire core application.

⏰ Scheduler

M.O.N.I.C.A. includes a persistent scheduler system for automation and scheduled tasks.
Potential uses include:

Reminders

Scheduled messages

Periodic tasks

Future automation

🎭 Persona System

M.O.N.I.C.A. separates AI personality and user profile information from the core application.
Persona files are located inside:

monica/persona/


The persona system can control:

Personality

Communication style

Assistant identity

User profile

Behavioral instructions

Response preferences

🗄️ Database

M.O.N.I.C.A. uses SQLite for local persistent storage.
The database layer can store application information such as:

Message history

Conversation information

Memories

Conversation summaries

Scheduler state

Other persistent application data

Runtime databases are intentionally excluded from Git.

🔐 Security

Sensitive credentials and runtime information are intentionally kept outside the public source repository.
The following should never be committed:

.env

Telegram API credentials

Telegram session strings

Bot tokens

Discord tokens

Passwords

Private API keys

Personal databases

Private conversation logs

Runtime files such as the following are also excluded:

data/

logs/

*.db

*.sqlite

*.session

*.session-journal

The repository's .gitignore is configured to help prevent accidental commits of these files.

⚠️ Never share your Telegram session string or API credentials publicly.

📁 Project Structure

M.O.N.I.C.A/
│
├── main.py
├── config.py
├── generate_session.py
├── requirements.txt
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .gitignore
│
├── monica/
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   ├── ollama.py
│   │   ├── provider.py
│   │   └── tools.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── contacts.py
│   │   ├── pipeline.py
│   │   └── router.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── migrations.py
│   │   └── repository.py
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── discrete.py
│   │   ├── long_term.py
│   │   └── short_term.py
│   │
│   ├── persona/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── monica_persona.json
│   │   ├── monica_persona.md
│   │   ├── siva_profile.json
│   │   └── siva_profile.md
│   │
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── auto_reply/
│   │   ├── core_cmds/
│   │   ├── example_plugin/
│   │   ├── media/
│   │   ├── messaging/
│   │   └── utilities/
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   └── parser.py
│   │
│   └── telegram/
│       ├── __init__.py
│       ├── buttons.py
│       ├── callbacks.py
│       └── formatter.py
│
└── testing/
    ├── __init__.py
    ├── fixtures/
    │   ├── messages.json
    │   └── mock_data.py
    ├── persona_harness.py
    └── test_suite.py


⚙️ Requirements

Python 3.x

Telegram account

Telegram API credentials

Telethon

Ollama

Compatible local LLM

SQLite

Internet connection for Telegram communication

🚀 Installation

1. Clone the repository

git clone https://github.com/Siva-kumar-r16/M.O.N.I.C.A.git
cd M.O.N.I.C.A


2. Create a virtual environment

Windows:

python -m venv .venv
.venv\Scripts\activate


Linux / macOS:

python3 -m venv .venv
source .venv/bin/activate


3. Install dependencies

pip install -r requirements.txt


🔐 Configuration

Create a local .env file in the root directory.

⚠️ Do not commit .env to Git.

Example .env:

API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
SESSION_STRING=your_telegram_session

OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5-coder:7b


Use your actual credentials only in your local .env.

🧠 Ollama Setup

Install Ollama and make sure the Ollama server is running.
Pull the configured model:

ollama pull qwen2.5-coder:7b


Check installed models:

ollama list


M.O.N.I.C.A. connects to the local Ollama server. Ollama does not need to be exposed publicly.

▶️ Running M.O.N.I.C.A.

Start the application:

python main.py


A successful startup should indicate that M.O.N.I.C.A. has authenticated with Telegram and is listening for messages.
Example output:

M.O.N.I.C.A. is active and listening for messages!


🧪 Testing

Testing utilities are located under testing/.
Current testing areas include:

Message fixtures

Mock data

Persona testing

Test suite

🔄 Development Workflow

The recommended development workflow is:

1. Modify code
      ↓
2. Test locally
      ↓
3. git status
      ↓
4. git add .
      ↓
5. git commit
      ↓
6. git push


Example commands:

git add .
git commit -m "Update M.O.N.I.C.A."
git push


🌐 Future Multi-Platform Architecture

M.O.N.I.C.A. is designed to eventually support multiple communication platforms.

                    M.O.N.I.C.A.
                         │
           ┌─────────────┼─────────────┐
           │             │             │
           ▼             ▼             ▼
       Telegram       Discord       Future
       Integration    Integration   Platforms
           │             │             │
           └─────────────┼─────────────┘
                         │
                         ▼
                    AI Manager
                         │
                         ▼
                      Ollama
                         │
                         ▼
                    Local LLM
                         │
                         ▼
                   Shared Memory


The goal is to keep the AI, memory, personality, tools, and automation layers shared while platform integrations handle platform-specific communication.

🛣️ Roadmap

[x] Telegram MTProto integration

[x] Local Ollama integration

[x] AI response generation

[x] Persona system

[x] Short-term memory

[ ] Long-term memory architecture

[ ] Discrete memory system

[ ] Telegram buttons

[x] Plugin architecture

[ ] Scheduler architecture

[ ] Contact management

[ ] Auto-reply system

[ ] Discord integration

[ ] Multi-platform messaging

[ ] Improved automatic memory extraction

[ ] Advanced AI tools

[ ] Media understanding

[ ] Voice interaction

[ ] Vision capabilities

[ ] Advanced automation

[ ] Improved error recovery

[ ] Further performance optimization

[ ] Expanded testing

[ ] CI/CD

📜 License

See the LICENSE file included in this repository.

⚠️ Disclaimer

M.O.N.I.C.A. is a personal software project intended for experimentation, learning, AI integration, automation, and personal productivity.

Users are responsible for:

Protecting their credentials

Protecting their Telegram session

Following Telegram's terms and policies

Following Discord's terms and policies when Discord integration is used

Following applicable laws and regulations

Reviewing automated actions before enabling them

Never publish private authentication credentials, session strings, passwords, or private user data.

👨‍💻 Project
M.O.N.I.C.A.
Multimodal Operational Neural Intelligence & Conversational Assistant
A personal AI system designed to communicate, remember, automate, and evolve.
