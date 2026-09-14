# 🧠 M.O.N.I.C.A.

### Multimodal Operational Neural Intelligence & Conversational Assistant

M.O.N.I.C.A. is a personal AI-powered Telegram manager and conversational assistant built with **Python, Telethon, Telegram MTProto, Ollama, and local Large Language Models**.

The project combines **AI, memory, automation, communication, plugins, and personal assistance** into one modular local system.

---

## ✨ Features

* 🤖 **Local AI** powered by Ollama
* 🧠 **Short-term conversation memory**
* 💾 **Long-term conversation summaries**
* 👤 **Personal facts and preferences**
* 💬 **Telegram personal-account integration**
* 🔘 **Telegram inline and hyperlink buttons**
* ⚙️ **Modular plugin architecture**
* ⏰ **Persistent scheduler**
* 🛠️ **Command system**
* 👥 **Contact and auto-reply management**
* 📝 **Keyword filters and snippets**
* 🎭 **Custom AI persona**
* 🔐 **Local credential and runtime-data protection**
* 🧩 **Extensible AI tools**
* 🧪 **Testing utilities**
* 🌍 **Multilingual message understanding**
* 🇬🇧 **English replies by default**

---

## 🏗️ Architecture

```text
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
                🧠 Memory       🎭 Persona       🛠️ Tools
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
```

---

## 🔄 Message Flow

A normal incoming message follows this pipeline:

```text
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
```

---

## 🧠 Memory System

M.O.N.I.C.A. uses a multi-level memory architecture.

### Level 1: Short-Term Memory

Stores recent conversation context for fast AI responses.

```text
Recent Messages
       ↓
Short-Term Buffer
       ↓
AI Context
```

This allows M.O.N.I.C.A. to understand the current conversation without repeatedly processing the entire chat.

### Level 2: Long-Term Memory

Older conversations can be summarized and stored as persistent conversation summaries.

```text
Conversation
       ↓
Message Threshold
       ↓
AI Summarization
       ↓
SQLite
       ↓
Long-Term Context
```

Long-term summarization is performed in the background so it does not intentionally block normal Telegram replies.

### Level 3: Discrete Memory

M.O.N.I.C.A. can store useful personal facts and preferences.

Examples:

```text
"My name is Rahul."
"I prefer Python."
"I like coffee."
"I live in Chennai."
```

These memories can later be retrieved and used to personalize conversations.

---

## 🤖 AI Backend

M.O.N.I.C.A. currently uses:

```text
Ollama
   ↓
Qwen 2.5 Coder 7B
```

The AI model runs locally through Ollama.

The AI provider is separated from the rest of the application, allowing the model or backend to be changed later without redesigning the entire system.

---

## 🌍 Language Handling

M.O.N.I.C.A. is designed to understand messages written in different languages and mixed-language forms.

Supported examples include:

* 🇬🇧 English
* 🇮🇳 Tamil
* 🗣️ Tanglish
* 🇮🇳 Hindi
* 🗣️ Hinglish
* 🇮🇳 Telugu
* 🇮🇳 Malayalam
* 🇮🇳 Kannada
* 🇮🇳 Bengali
* 🌐 Other languages supported by the configured model

By default, M.O.N.I.C.A. responds in natural English unless the user explicitly requests another language.

---

## 💬 Telegram Integration

M.O.N.I.C.A. uses **Telegram MTProto through Telethon**.

Unlike a traditional Telegram Bot API application, M.O.N.I.C.A. is designed to operate through a personal Telegram account.

Current capabilities include:

* 📩 Receiving messages
* 📤 Sending messages
* ↩️ Replying to messages
* ✏️ Editing messages
* 🗑️ Deleting messages
* 🔘 Inline buttons
* 🔗 Hyperlink buttons
* 🛠️ Commands
* 👥 Contact management
* 🤖 Automated replies
* 📝 Keyword filters
* 📌 Snippets

---

## 🔘 Interactive Buttons

M.O.N.I.C.A. includes a Telegram button parser for interactive responses.

Example:

```text
Choose an option:

[ Open Website ]
[ Continue ]
[ Cancel ]
```

Buttons can be generated and handled through the Telegram module.

---

## 🧩 Plugin System

M.O.N.I.C.A. uses a modular plugin architecture.

Current plugin areas include:

```text
monica/plugins/
│
├── auto_reply/
├── core_cmds/
├── example_plugin/
├── media/
├── messaging/
└── utilities/
```

The plugin architecture allows functionality to be added independently without modifying the entire core application.

---

## ⏰ Scheduler

M.O.N.I.C.A. includes a persistent scheduler system for automation and scheduled tasks.

Potential uses include:

* ⏰ Reminders
* 📩 Scheduled messages
* 🔄 Periodic tasks
* 🤖 Future automation

---

## 🎭 Persona System

M.O.N.I.C.A. separates AI personality and user profile information from the core application.

Persona files are located inside:

```text
monica/persona/
```

The persona system can control:

* Personality
* Communication style
* Assistant identity
* User profile
* Behavioral instructions
* Response preferences

---

## 🗄️ Database

M.O.N.I.C.A. uses **SQLite** for local persistent storage.

The database layer can store application information such as:

* Message history
* Conversation information
* Memories
* Conversation summaries
* Scheduler state
* Other persistent application data

Runtime databases are intentionally excluded from Git.

---

## 🔐 Security

Sensitive credentials and runtime information are intentionally kept outside the public source repository.

### Never commit

```text
.env
Telegram API credentials
Telegram session strings
Bot tokens
Discord tokens
Passwords
Private API keys
Personal databases
Private conversation logs
```

### Runtime files excluded from Git

```text
data/
logs/
*.db
*.sqlite
*.session
*.session-journal
```

The repository's `.gitignore` is configured to help prevent accidental commits of these files.

> ⚠️ **Never share your Telegram session string or API credentials publicly.**

---

## 📁 Project Structure

```text
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
```

---

## ⚙️ Requirements

Before running M.O.N.I.C.A., make sure you have:

* 🐍 Python 3.x
* 📱 A Telegram account
* 🔑 Telegram API credentials
* 📦 Telethon
* 🤖 Ollama
* 🧠 A compatible local LLM
* 🗄️ SQLite
* 🌐 Internet connection for Telegram communication

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/Siva-kumar-r16/M.O.N.I.C.A.git
cd M.O.N.I.C.A
```

### 2. Create a virtual environment

#### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔐 Configuration

Create a local `.env` file in the root directory.

> ⚠️ **Do not commit `.env` to Git.**

Example:

```env
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
SESSION_STRING=your_telegram_session

OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5-coder:7b
```

Use your actual credentials only in your local `.env` file.

---

## 🧠 Ollama Setup

Install Ollama and make sure the Ollama server is running.

Pull the configured model:

```bash
ollama pull qwen2.5-coder:7b
```

Check installed models:

```bash
ollama list
```

M.O.N.I.C.A. connects to the local Ollama server.

> 🔒 Ollama does not need to be exposed publicly.

---

## ▶️ Running M.O.N.I.C.A.

Start the application:

```bash
python main.py
```

A successful startup should indicate that M.O.N.I.C.A. has authenticated with Telegram and is listening for messages.

Example:

```text
M.O.N.I.C.A. is active and listening for messages!
```

---

## 🧪 Testing

Testing utilities are located under:

```text
testing/
```

Current testing areas include:

* Message fixtures
* Mock data
* Persona testing
* Test suite

---

## 🔄 Development Workflow

The recommended development workflow is:

```text
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
```

Example:

```bash
git status
git add .
git commit -m "Update M.O.N.I.C.A."
git push
```

---

## 🌐 Future Multi-Platform Architecture

M.O.N.I.C.A. is designed to eventually support multiple communication platforms.

```text
                         M.O.N.I.C.A.
                              │
                 ┌────────────┼────────────┐
                 │            │            │
                 ▼            ▼            ▼
             Telegram      Discord       Future
             Integration   Integration   Platforms
                 │            │            │
                 └────────────┼────────────┘
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
```

The goal is to keep the following layers shared:

* AI
* Memory
* Personality
* Tools
* Automation

Platform integrations should handle communication-specific functionality.

---

## 🛣️ Roadmap

### Core

* [x] Telegram MTProto integration
* [x] Local Ollama integration
* [x] AI response generation
* [x] Persona system
* [x] Plugin architecture

### Memory

* [x] Short-term memory
* [x] Long-term memory architecture
* [x] Discrete memory system
* [ ] Improved automatic memory extraction

### Telegram

* [x] Telegram buttons
* [x] Contact management
* [x] Auto-reply system
* [x] Keyword filters
* [x] Snippets

### Automation

* [x] Scheduler architecture
* [ ] Advanced automation
* [ ] Improved error recovery

### AI Capabilities

* [ ] Advanced AI tools
* [ ] Media understanding
* [ ] Voice interaction
* [ ] Vision capabilities
* [ ] Improved performance optimization

### Platforms

* [ ] Discord integration
* [ ] Multi-platform messaging

### Testing & Development

* [ ] Expanded testing
* [ ] CI/CD

---

## 📜 License

See the [`LICENSE`](LICENSE) file included in this repository.

---

## ⚠️ Disclaimer

M.O.N.I.C.A. is a personal software project intended for:

* Experimentation
* Learning
* AI integration
* Automation
* Personal productivity

Users are responsible for:

* 🔐 Protecting their credentials
* 🔑 Protecting their Telegram session
* 📜 Following Telegram's terms and policies
* 📜 Following Discord's terms and policies when Discord integration is used
* ⚖️ Following applicable laws and regulations
* 👀 Reviewing automated actions before enabling them
* 🚫 Never publishing private authentication credentials, session strings, passwords, or private user data

---

## 👨‍💻 Project

**M.O.N.I.C.A.**

**Multimodal Operational Neural Intelligence & Conversational Assistant**

> A personal AI system designed to communicate, remember, automate, and evolve.
