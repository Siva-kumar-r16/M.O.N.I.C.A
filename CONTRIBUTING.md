# Contributing to M.O.N.I.C.A.

Thank you for your interest in contributing to **M.O.N.I.C.A.** 🎉

M.O.N.I.C.A. is an AI-powered Telegram personal manager and conversational assistant designed to combine conversational AI, memory, automation, plugins, and personal productivity into one modular system.

We welcome bug fixes, improvements, documentation updates, plugins, performance improvements, tests, and new ideas.

---

## 🧠 Before You Start

Before contributing, please read:

* [`README.md`](README.md)
* [`LICENSE`](LICENSE)
* [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
* [`SECURITY.md`](SECURITY.md)

Also check existing **Issues** and **Pull Requests** before creating a new one.

---

## 🚀 Ways You Can Contribute

You can contribute by:

* 🐛 Fixing bugs
* ✨ Adding features
* 🤖 Improving AI behavior
* 🧠 Improving memory systems
* ⚡ Improving performance
* 🔌 Creating plugins
* 📱 Improving Telegram functionality
* 🔘 Improving buttons and interactive features
* 🗄️ Improving database functionality
* ⏰ Improving scheduling and automation
* 📚 Improving documentation
* 🧪 Adding tests
* 🔒 Improving security
* 🎨 Improving developer experience

---

## 🛠️ Development Setup

### 1. Fork the Repository

Fork the M.O.N.I.C.A. repository to your GitHub account.

### 2. Clone Your Fork

```bash
git clone https://github.com/Siva-kumar-r16/M.O.N.I.C.A.git
cd M.O.N.I.C.A
```

### 3. Create a Virtual Environment

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

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a local `.env` file based on `.env.example`.

Never commit your real `.env` file.

---

## 🔐 Never Commit Secrets

Do **not** commit:

```text
.env
Telegram API credentials
Telegram session strings
Discord tokens
API keys
Passwords
Private keys
Personal databases
Private conversation data
Authentication files
Personal logs
```

If you accidentally expose a credential, revoke or rotate it immediately.

---

## 🌿 Branching

Do not normally work directly on `main`.

Create a separate branch for your changes:

```bash
git checkout -b feature/my-feature
```

Examples:

```text
feature/discord-support
feature/better-memory
feature/new-plugin
fix/message-resolution
fix/ollama-timeout
docs/plugin-guide
```

---

## 💻 Coding Guidelines

Please keep contributions:

* Simple
* Readable
* Maintainable
* Modular
* Well documented
* Compatible with the existing architecture

Avoid unnecessary dependencies.

Before submitting a Pull Request:

* Remove debugging code
* Remove personal information
* Remove credentials
* Check error handling
* Check logs
* Test the affected functionality

---

## 🔌 Plugin Contributions

New functionality that can be isolated should preferably be implemented as a plugin.

Plugins should:

* Have a clear purpose
* Avoid unnecessary global state
* Handle errors gracefully
* Avoid blocking the event loop
* Follow the existing plugin architecture
* Include documentation when necessary

---

## 🧪 Testing

Before opening a Pull Request, test your changes locally.

At minimum:

```bash
python main.py
```

Verify that:

* M.O.N.I.C.A. starts correctly
* Telegram authentication works
* AI responses work
* Existing commands still work
* Your new feature works
* No secrets are exposed in logs

If automated tests are available, run them as well.

---

## 📝 Commit Messages

Use clear and descriptive commit messages.

### Good Examples

```text
Add Telegram message reaction support
Fix Ollama connection handling
Improve conversation memory
Add plugin documentation
Optimize AI response latency
```

### Avoid

```text
update
changes
fix
test
asdf
final
```

---

## 🔄 Pull Request Process

1. Fork the repository.
2. Create a branch.
3. Make your changes.
4. Test your changes.
5. Commit your changes.
6. Push your branch.
7. Open a Pull Request.

Example:

```bash
git add .
git commit -m "Add improved memory retrieval"
git push origin feature/my-feature
```

Then create a Pull Request on GitHub.

---

## 📋 Pull Request Requirements

Please explain the following:

### What changed?

Describe what you changed.

### Why?

Explain the reason for the change.

### How was it tested?

Explain how you tested the changes.

### Screenshots or Logs

Add screenshots or relevant logs when useful.

> ⚠️ Never include private information, Telegram session data, API keys, passwords, or personal conversations.

---

## 🐛 Bug Reports

Before opening a bug report:

* Search existing Issues.
* Make sure you are using a supported version.
* Try reproducing the problem.
* Remove sensitive information from logs.

Use the Bug Report template when available.

---

## 💡 Feature Requests

Feature requests are welcome.

Please explain:

* What the feature should do
* Why it would be useful
* How you think it could work
* Whether it should be a core feature or plugin

---

## 🤝 Respect Existing Architecture

Please review the existing architecture before replacing major components.

Large architectural changes should ideally be discussed in an Issue before implementation.

---

## 📜 License

By contributing to M.O.N.I.C.A., you agree that your contributions will be licensed under the same license as the project.

M.O.N.I.C.A. is currently licensed under the **MIT License**.

---

## ❤️ Thank You

Every contribution matters.

Whether you submit one line of documentation or a major feature, thank you for helping make M.O.N.I.C.A. better.

**Build. Improve. Share. 🤖**
