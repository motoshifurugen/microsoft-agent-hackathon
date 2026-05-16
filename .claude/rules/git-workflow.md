# Git Workflow

## Commit Message Format

<type>: <description>

<optional body>

### Commit Types
- feat
- fix
- refactor
- docs
- test
- chore
- perf
- ci

### Commit Rules
- Use the imperative mood (e.g. "add", not "added")
- Keep the description concise and under 72 characters
- Scope each commit to a single logical change
- Avoid combining unrelated changes in one commit

Note: Attribution is disabled globally via ~/.claude/settings.json.

---

## Pull Request Workflow

When creating a Pull Request:

1. Review the full commit history (not only the latest commit)
2. Review all changes using:
   git diff <base-branch>...HEAD
3. Write a clear, structured PR summary
   - Prefer bullet points over long paragraphs
   - Focus on what changed and why
4. Include a test plan
   - List executed tests
   - Explicitly mark untested areas as TODO
5. When pushing a new branch, use:
   git push -u origin <branch-name>

---

## Feature Implementation Workflow

### 1. Plan First

- Mandatory for non-trivial features or multi-file changes
- Use the planner agent to draft an implementation plan
- Identify dependencies, risks, and constraints
- Break work into clear, incremental phases

---

### 2. TDD Approach

- Use the tdd-guide agent
- Follow the RED → GREEN → REFACTOR cycle:
  1. Write failing tests (RED)
  2. Implement minimal code to pass tests (GREEN)
  3. Refactor for clarity and structure (REFACTOR)
- Aim for approximately 80% coverage where tooling allows
- Do not block progress due to coverage tooling limitations

---

### 3. Code Review

- Use the code-reviewer agent immediately after implementation
- Address all CRITICAL and HIGH severity issues
- Resolve MEDIUM severity issues when reasonable
- Do not self-approve changes without reviewer agent feedback

---

### 4. Commit & Push

- Follow the commit message format defined above
- Use clear, scoped commits aligned with the implementation phases
- Ensure the working tree is clean before pushing
