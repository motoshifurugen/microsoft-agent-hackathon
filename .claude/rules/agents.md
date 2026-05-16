# Agent Orchestration (Recommended)

## Purpose

This document defines how specialized agents are orchestrated
to maintain code quality, safety, and consistency.

Agents are treated as mandatory collaborators, not optional helpers.

---

## Available Agents

All agents are located in ~/.claude/agents/

planner
- Purpose: Implementation planning
- Use when: Complex features, refactoring, unclear requirements

architect
- Purpose: System and architectural design
- Use when: Making structural or long-term decisions

tdd-guide
- Purpose: Test-driven development guidance
- Use when: New features, bug fixes, logic changes

code-reviewer
- Purpose: Code review and quality checks
- Use when: After writing or modifying code

security-reviewer
- Purpose: Security analysis
- Use when: Before commits or when handling sensitive logic

build-error-resolver
- Purpose: Fixing build and CI errors
- Use when: Build or type checks fail

e2e-runner
- Purpose: End-to-end testing
- Use when: Verifying critical user flows

refactor-cleaner
- Purpose: Removing dead code and improving structure
- Use when: Code maintenance and cleanup

doc-updater
- Purpose: Documentation updates
- Use when: Behavior or APIs change

---

## Immediate Agent Usage Rules

The following agent invocations require no user confirmation:

- Complex feature requests
  -> Use planner

- Code written or modified
  -> Use code-reviewer

- Bug fixes or new features
  -> Use tdd-guide

- Architectural or structural decisions
  -> Use architect

Skipping these steps is not allowed.

---

## Parallel Agent Execution

Parallel execution is recommended ONLY when tasks are independent.

Allowed examples:
- Security review and performance review on separate files
- Type checking and documentation review

Not allowed:
- Planning and implementation at the same time
- Code review before implementation is complete
- Refactoring while tests are still failing

When in doubt, prefer sequential execution.

---

## Multi-Perspective Analysis

Use multi-perspective analysis for complex or high-risk changes.

Typical roles:
- Factual reviewer (correctness and assumptions)
- Senior engineer (design and maintainability)
- Security expert (attack surface and misuse)
- Consistency reviewer (style and conventions)
- Redundancy checker (unnecessary complexity)

This approach is recommended for:
- Authentication and authorization logic
- Public APIs
- Cross-cutting refactors
- High-impact business rules

---

## Guiding Principle

If unsure which agent to use:
- Prefer more review, not less
- Default to safety and clarity
