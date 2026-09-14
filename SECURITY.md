# Security Policy

## 🔐 M.O.N.I.C.A. Security

Security and privacy are important to the M.O.N.I.C.A. project.

M.O.N.I.C.A. may interact with:

* Telegram accounts
* Telegram messages
* AI services
* Local databases
* Conversation memory
* API credentials
* Authentication sessions
* External integrations

Please treat authentication information and personal data as sensitive.

---

## 🚨 Reporting a Security Vulnerability

If you discover a security vulnerability, **do not publicly disclose it through a GitHub Issue**.

Instead, report it privately to the project maintainer.

When reporting a vulnerability, please include:

* A description of the vulnerability
* Steps to reproduce it
* Affected component
* Potential impact
* Suggested mitigation, if available

Please provide enough technical information for the issue to be reproduced and investigated.

---

## 🔑 Never Share Credentials

Never publish or commit:

```text
.env
Telegram API ID
Telegram API Hash
Telegram session strings
Discord bot tokens
API keys
OAuth tokens
Passwords
Private keys
Database credentials
```

Do not put credentials directly inside source code.

Use environment variables instead.

---

## 🗄️ Personal Data

M.O.N.I.C.A. may store local information such as:

* Conversation history
* Memory
* Preferences
* User information
* Scheduler information
* Application logs

Do not submit real personal conversation data to GitHub.

Use synthetic or anonymized test data when reporting bugs.

---

## 📋 Logs

Before uploading logs to an Issue or Pull Request, check them for:

* Phone numbers
* Telegram IDs
* Usernames
* Private messages
* API keys
* Tokens
* Session information
* Personal file paths
* Other private information

Remove sensitive information before sharing logs publicly.

---

## 🛡️ Dependency Security

Contributors should avoid adding dependencies unless they are necessary.

New dependencies should be:

* Actively maintained
* Relevant to the feature
* Properly licensed
* Reasonably secure

---

## 🔄 Security Updates

Security fixes may be released separately from normal feature releases when necessary.

Users should keep M.O.N.I.C.A. and its dependencies reasonably up to date.

---

## ⚠️ Responsible Disclosure

Please allow project maintainers reasonable time to investigate and address a security vulnerability before publicly disclosing technical details.

Do not exploit a vulnerability against other users, accounts, systems, or services.

---

## 🔒 Session Security

Telegram session information can provide access to an authenticated account.

Never:

* Upload session files to GitHub
* Share session strings publicly
* Include sessions in screenshots
* Paste sessions into Issues or Pull Requests
* Store sessions in source code

If a Telegram session is accidentally exposed, revoke the affected session as soon as possible.

---

## ❤️ Thank You

Thank you for helping keep M.O.N.I.C.A., its contributors, and its users secure.
