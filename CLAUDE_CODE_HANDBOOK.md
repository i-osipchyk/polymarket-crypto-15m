# Claude Code Handbook

A quick-reference guide for working with Claude Code in your project.

---

## Table of Contents

1. [Claude Code Setup](#1-claude-code-setup)
2. [Project Setup](#2-project-setup)
3. [Adding Context](#3-adding-context)
4. [Making Changes](#4-making-changes)
5. [Controlling Context](#5-controlling-context)
6. [Custom Commands](#6-custom-commands)
7. [MCP Servers](#7-mcp-servers)
8. [GitHub Integration](#8-github-integration)

---

## 1. Claude Code Setup

### Installation

```bash
npm install -g @anthropic-ai/claude-code
```

Requires Node.js. After installing, authenticate with your Anthropic account:

```bash
claude
```

This opens a browser to log in with your Claude Pro / Max account (or set an API key).

### Useful Launch Flags

| Flag | Description |
|------|-------------|
| `claude` | Start interactive session |
| `claude -p "prompt"` | One-shot, non-interactive prompt |
| `claude --model claude-opus-4-6` | Specify a model |
| `claude --dangerously-skip-permissions` | Skip all permission prompts (use carefully) |

### Global Config Location

```
~/.claude/           ← your global Claude Code folder
~/.claude/CLAUDE.md  ← global context loaded in every session
~/.claude/commands/  ← global custom slash commands
~/.claude/settings.json ← global settings
```

---

## 2. Project Setup

### Initialize a Project

Run inside your project folder:

```bash
claude
/init
```

`/init` scans your project and creates a `.claude/` folder with a starter `CLAUDE.md`.

### Project File Structure

```
your-project/
├── CLAUDE.md              ← project-level context (auto-loaded)
├── .claude/
│   ├── settings.json      ← project-level settings & permissions
│   ├── commands/          ← project-specific slash commands
│   └── skills/            ← project-specific skills (optional)
```

### settings.json Example

```json
{
  "model": "claude-sonnet-4-20250514",
  "permissions": {
    "allowedTools": ["Read", "Write", "Bash(git *)"],
    "deny": [
      "Read(./.env)",
      "Write(./production.config.*)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write(*.py)",
        "hooks": [{ "type": "command", "command": "python -m black $file" }]
      }
    ]
  }
}
```

---

## 3. Adding Context

### CLAUDE.md — Your Project Brain

`CLAUDE.md` is loaded automatically at the start of every session. Put anything Claude should always know here.

**What to include:**

- Project description and goals
- Tech stack and key dependencies
- How to build, test, and run the project
- Coding conventions and style rules
- Folder structure overview
- Important files to know about

**Example CLAUDE.md:**

```markdown
# My Project

A Node.js REST API for task management.

## Tech Stack
- Node.js + Express
- PostgreSQL (via Prisma)
- Jest for tests

## Commands
- `npm run dev`   → start dev server
- `npm test`      → run tests
- `npm run lint`  → ESLint

## Conventions
- Use async/await, no callbacks
- All routes in `src/routes/`
- Env vars via `.env` (never commit)
```

### Referencing Files in a Prompt

Use `@` to include specific files inline:

```
@src/routes/users.js refactor this to use async/await
```

### CLAUDE.md Hierarchy

Claude loads CLAUDE.md files from multiple levels — more specific ones override general ones:

```
~/.claude/CLAUDE.md          ← global (all projects)
~/your-project/CLAUDE.md     ← project root
~/your-project/src/CLAUDE.md ← subfolder (loaded when working in src/)
```

---

## 4. Making Changes

### How to Give Instructions

Describe what you want in plain English. Be specific about files or scope:

```
Add input validation to the POST /users endpoint in src/routes/users.js
```

### Reviewing Changes

Claude shows diffs before writing. You can:

- **Accept** — apply the change
- **Reject** — discard it
- **Edit** — modify the diff before applying

### Useful Built-in Commands During a Session

| Command | What it does |
|---------|--------------|
| `/help` | Show all available commands |
| `/clear` | Clear conversation history (start fresh) |
| `/context` | Show current context window usage |
| `/compact` | Summarize older history to free up context |
| `/undo` | Undo the last file change |
| `/diff` | Show changes made in this session |
| `/model` | Switch the Claude model |
| `/init` | (Re)initialize CLAUDE.md for current project |

### Switching Models Mid-Session

```
/model claude-opus-4-6
/model claude-sonnet-4-20250514
/model claude-haiku-4-5-20251001
```

---

## 5. Controlling Context

### Why Context Management Matters

Claude has a limited context window. As conversations grow, older content is dropped. Managing context intentionally keeps Claude focused and responses fast.

### Key Strategies

**Start fresh for new tasks:**
```
/clear
```
Always clear before switching to a different task — old history wastes tokens and can confuse Claude.

**Compact when getting long:**
```
/compact
```
Summarizes older messages while keeping key decisions and code changes in memory.

**Check usage anytime:**
```
/context
```
Shows a breakdown of how your context window is being used.

### What to Include vs. Exclude

Include with `@filename` only what's relevant to the current task. Avoid loading entire large files unless needed — describe the relevant part instead.

### Hooks — Automate Context Loading

Hooks let you run shell commands before or after tool use. Useful for auto-formatting, type checking, or injecting dynamic context.

```json
"hooks": {
  "PostToolUse": [
    {
      "matcher": "Write(*.ts)",
      "hooks": [{ "type": "command", "command": "npx tsc --noEmit $file" }]
    }
  ]
}
```

Common hook events: `PreToolUse`, `PostToolUse`, `SessionStart`, `SessionEnd`.

---

## 6. Custom Commands

Custom commands are slash commands you define as Markdown files. They save long or frequent prompts as one-word shortcuts.

### Two Scopes

| Location | Scope |
|----------|-------|
| `.claude/commands/` (project) | Only available in this project |
| `~/.claude/commands/` (global) | Available in all projects |

### Creating a Command

Create a `.md` file — the filename becomes the command name:

```bash
mkdir -p .claude/commands
```

`.claude/commands/optimize.md`:
```markdown
Analyze the following code for performance issues and suggest optimizations.
Focus on: time complexity, unnecessary re-renders, and database query efficiency.
```

Use it with: `/optimize`

### Using Arguments

Use `$ARGUMENTS` (all args) or `$1`, `$2` (positional):

`.claude/commands/fix-issue.md`:
```markdown
Fix GitHub issue #$ARGUMENTS following our project coding standards.
Check the related files, understand the context, and implement a clean fix.
```

Use it with: `/fix-issue 42`

### Advanced: Frontmatter Options

```markdown
---
description: Create a conventional git commit
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
model: claude-haiku-4-5-20251001
---

## Context
- Current status: !`git status`
- Current diff: !`git diff HEAD`

## Task
Create a git commit with a concise conventional commit message based on the changes above.
```

The `!` prefix runs a shell command and injects the output into the prompt.

### Useful Commands to Build

| Command file | Purpose |
|---|---|
| `commit.md` | Auto-generate conventional commit messages |
| `review.md` | Code review a file or diff |
| `catchup.md` | Reload context after `/clear` |
| `optimize.md` | Performance analysis |
| `security.md` | Security vulnerability scan |
| `docs.md` | Generate or update documentation |

---

## 7. MCP Servers

MCP (Model Context Protocol) is an open standard that connects Claude Code to external tools — databases, APIs, services — without custom code.

### Adding an MCP Server

```bash
# HTTP server (recommended for remote/cloud services)
claude mcp add --transport http <name> <url>

# Local process via stdio
claude mcp add <name> -- npx -y <package-name>
```

### Scopes

| Scope | Flag | Config stored in |
|-------|------|-----------------|
| Local (default) | _(none)_ | Local project config (not shared) |
| Project (shared) | `--scope project` | `.mcp.json` in project root |
| User (global) | `--scope user` | `~/.claude/` |

### Managing Servers

```bash
claude mcp list              # list all configured servers
claude mcp get <name>        # see details for a server
claude mcp remove <name>     # remove a server
```

Inside a session:
```
/mcp                         # check server status
```

### Example: Notion

```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

### Example: Local Server via npx

```bash
claude mcp add my-server -- npx -y @modelcontextprotocol/server-filesystem /path/to/dir
```

### Setting a Startup Timeout

```bash
MCP_TIMEOUT=10000 claude    # 10 second timeout for MCP startup
```

---

## 8. GitHub Integration

### Option A: GitHub MCP Server (Recommended)

Lets Claude read issues, PRs, and repos directly from inside a session.

**Step 1:** Create a GitHub Personal Access Token at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope.

**Step 2:** Add the MCP server:

```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp \
  --header "Authorization: Bearer YOUR_GITHUB_PAT"
```

Or using an env variable:

```bash
claude mcp add --transport http github https://api.githubcopilot.com/mcp \
  --header "Authorization: Bearer $(grep GITHUB_PAT .env | cut -d '=' -f2)"
```

**Step 3:** Use it naturally in conversation:

```
What are the open issues in this repo?
Implement the feature described in issue #14 and create a PR
Summarize the last 5 merged PRs
```

### Option B: GitHub CLI Integration

Install and authenticate the GitHub CLI:

```bash
brew install gh
gh auth login
```

This enables Claude to run `gh` commands in your shell — for creating branches, PRs, checking CI, etc.

### Option C: PR Auto-Review with GitHub App

Inside a session, run:

```
/install-github-app
```

This installs a Claude Code GitHub App that automatically reviews your PRs. You can customize the review prompt in `.claude/claude-code-review.yml`.

### Useful GitHub Workflows with Claude Code

**Load a GitHub issue into context:**
```
Load issue #42 from this repo into context so we can work on it
```

**Catchup command with GitHub context** (`.claude/commands/catchup.md`):
```markdown
Read all uncommitted git changes into this conversation.
Also find issue #$ARGUMENTS on this repo and load its contents.
```

**Create a PR:**
```
Stage all changes, write a commit message, push to a new branch, and open a PR
```

---

## Quick Reference Cheatsheet

### Most Used Commands

```
/clear        → fresh start (do this between tasks)
/compact      → summarize old history
/context      → check context usage
/undo         → undo last file change
/diff         → show session changes
/model        → switch model
/mcp          → check MCP server status
/init         → (re)create CLAUDE.md
```

### Key File Locations

```
~/.claude/CLAUDE.md              global context
~/.claude/commands/              global slash commands
~/.claude/settings.json          global settings

./CLAUDE.md                      project context (auto-loaded)
./.claude/settings.json          project settings & permissions
./.claude/commands/              project slash commands
./.mcp.json                      shared MCP server config
```

### Tips

- Run `/clear` every time you switch tasks — old context is noise
- Keep `CLAUDE.md` updated with build commands so Claude never has to guess
- Use `@filename` to pull in only what's relevant, not whole directories
- Scope MCP servers to `--scope project` and commit `.mcp.json` so teammates share the same tools
- Use `--scope user` for personal MCP servers with tokens you don't want in the repo
