# Security Guidelines (Recommended)

## Purpose

This document defines mandatory security rules for both humans and AI.
Security is treated as a blocking condition, not a suggestion.

---

## Scope

Applies to:
- Web applications (frontend / backend)
- APIs and background jobs
- Personal and production projects

Not intended for:
- Throwaway prototypes
- Purely local scripts with no external input
- One-off experiments without persistence

---

## Mandatory Security Checks

Before ANY commit, confirm all of the following:

- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All external user inputs are validated
- [ ] SQL injection is prevented (parameterized queries or ORM)
- [ ] XSS is prevented (sanitized HTML, no unsafe rendering)
- [ ] CSRF protection is enabled (SameSite cookies or CSRF tokens)
- [ ] Authentication is implemented correctly
- [ ] Authorization is enforced for every protected resource
- [ ] Rate limiting is applied to all public endpoints
- [ ] Error messages do not leak sensitive information

Failure to meet any item blocks the commit.

---

## Input Validation

- Validate all external inputs at system boundaries
- Prefer schema-based validation libraries
- Never rely on frontend-only validation

---

## Secret Management

Rules:
- Secrets must never be hardcoded
- Secrets must be loaded from environment variables
- Environment files must not be committed
- Assume all repositories may eventually become public

Example (conceptual):
- BAD: const apiKey = "sk-xxxx"
- GOOD: const apiKey = process.env.OPENAI_API_KEY

If a required secret is missing, the application must fail explicitly.

---

## Authentication and Authorization

- Authentication and authorization are separate concerns
- Every protected resource must enforce authorization
- Never rely on client-side role or permission checks
- When unsure, default to deny access

---

## Rate Limiting

- Required for all public-facing endpoints
- Minimum: per-IP or per-user limiting
- Mandatory for authentication-related routes

---

## Error Handling

- User-facing errors must be generic and safe
- Never expose stack traces, queries, or internal identifiers
- Detailed errors may be logged internally only

---

## Automation Notes

Recommended automation where feasible:
- Secret scanning via pre-commit hooks or CI
- Dependency vulnerability scanning
- Static analysis for unsafe patterns

Automation supports security but does not replace manual review.

---

## Security Response Protocol

If a security issue is discovered:

1. STOP all feature work immediately
2. Use the security-reviewer agent
3. Fix all CRITICAL issues before continuing
4. Rotate any exposed secrets immediately
5. Review the entire codebase for similar issues
6. Add prevention measures (lint rules, hooks, or checks)

Security issues are treated as blocking incidents.

---

## Guiding Principle

If there is uncertainty about safety:
- Assume the implementation is NOT safe
- Stop and review before proceeding
