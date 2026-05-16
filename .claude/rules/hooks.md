# Hooks System

Hooks are automated checks and actions that enforce workflow discipline.
They should reduce cognitive load, not replace reasoning.

---

## Hook Types

- **PreToolUse**
  - Runs before tool execution
  - Used for validation, reminders, and blocking unsafe actions

- **PostToolUse**
  - Runs after tool execution
  - Used for formatting, verification, and feedback loops

- **Stop**
  - Runs when the session ends
  - Acts as a final quality gate before considering work complete

---

## Current Hooks (defined in ~/.claude/settings.json)

### PreToolUse Hooks

- **tmux reminder** (WARN)
  - Suggest tmux for long-running commands
  - Applies to npm, pnpm, yarn, cargo, pytest, etc.
  - Does not block execution

- **git push review** (BLOCK)
  - Opens editor for manual review before `git push`
  - Prevents accidental pushing of unreviewed changes

- **doc blocker** (BLOCK)
  - Blocks creation of unnecessary `.md` / `.txt` files
  - Allows only README.md, CLAUDE.md, or explicitly approved docs

---

### PostToolUse Hooks

- **PR creation logger** (INFO)
  - Logs PR URL and GitHub Actions status after PR creation

- **Prettier auto-format** (AUTO)
  - Runs Prettier after editing `.js`, `.jsx`, `.ts`, `.tsx` files
  - Skips if Prettier config is missing

- **TypeScript check** (WARN)
  - Runs `tsc --noEmit` after `.ts` / `.tsx` edits
  - Only when TypeScript configuration exists
  - Should not block exploratory or partial changes

- **console.log warning** (WARN)
  - Warns when `console.log` is introduced in edited files
  - Does not automatically modify code

---

### Stop Hooks (Final Gate)

- **console.log audit** (BLOCK)
  - Scans all modified files for `console.log` statements
  - Session is considered incomplete until resolved or explicitly approved

---

## Auto-Accept Permissions

Use with extreme caution.

Guidelines:
- Enable only for trusted, well-defined execution plans
- Disable for exploratory or ambiguous tasks
- Never use `--dangerously-skip-permissions`
- Prefer granular control via `allowedTools` in `~/.claude.json`

Auto-accept should reduce friction, not remove safeguards.

---

## TodoWrite Best Practices

Use the TodoWrite tool to:
- Track progress on multi-step or long-running tasks
- Verify understanding before implementation begins
- Enable real-time steering and correction
- Make reasoning and execution order explicit

A well-structured todo list helps reveal:
- Steps executed out of order
- Missing or implicit requirements
- Unnecessary or redundant work
- Incorrect task granularity
- Misinterpreted goals or constraints
