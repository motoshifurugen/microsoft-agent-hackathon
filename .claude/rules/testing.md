# Testing Requirements (Recommended)

## Purpose

This document defines mandatory testing rules to ensure code quality
and prevent regressions for both humans and AI.

Testing is treated as a quality gate, not an optional activity.

---

## Minimum Test Coverage

Target coverage: 80%

Coverage rules:
- Coverage is required where measurement tooling exists
- Lack of tooling does not block progress, but must be documented
- Coverage numbers do not replace meaningful test cases

---

## Required Test Types

The following test types are required based on change impact:

1. Unit Tests
   - Functions, utilities, hooks, components
   - Required for all logic changes

2. Integration Tests
   - APIs, database interactions, service boundaries
   - Required when data flow or side effects are involved

3. E2E Tests
   - Critical user flows only
   - Required for authentication, payments, and core journeys

Not all changes require all test types.

---

## Test-Driven Development (TDD)

Default workflow for feature development:

1. Write a test first (RED)
2. Run the test and confirm it fails
3. Write the minimum implementation (GREEN)
4. Run the test and confirm it passes
5. Refactor for clarity and structure (IMPROVE)
6. Re-run tests and verify coverage

TDD is mandatory for:
- New features
- Business logic
- Bug fixes

---

## Exceptions

Tests may be skipped only for:
- Pure refactors with no behavior change
- Comment or documentation changes
- Type-only or configuration-only changes

Skipped tests must be explicitly stated in the PR.

---

## Troubleshooting Test Failures

When tests fail:

1. Use the tdd-guide agent
2. Verify test isolation
3. Review mocks and fixtures
4. Fix implementation before modifying tests
5. Change tests only if they are proven incorrect

---

## Agent Support

- tdd-guide
  - Use proactively for new features
  - Enforces write-tests-first behavior

- e2e-runner
  - Specialist for Playwright-based E2E testing
  - Use for critical flow verification
