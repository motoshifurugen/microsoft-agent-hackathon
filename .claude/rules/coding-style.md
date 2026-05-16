# Coding Style

## Immutability (CRITICAL)

Prefer immutable patterns for:
- Function arguments
- Shared state
- React state / props
- Public APIs

Avoid mutating inputs or shared objects.

Local, clearly scoped mutations are acceptable
if they do not escape the function boundary.

## File Organization

Prefer many small, focused files over large ones:
- High cohesion, low coupling
- 200–400 lines is ideal
- 800 lines is a warning threshold
- Extract utilities from large components
- Organize by feature/domain, not by technical type

## Error Handling

Always handle errors explicitly:
- Catch errors at appropriate boundaries
- Use approved logging mechanisms
- Re-throw or propagate meaningful, user-facing messages

## Input Validation

Always validate external inputs:
- API requests
- User input
- Data from external services

Prefer schema-based validation (e.g. zod).
Avoid redundant validation in internal pure functions.

## Code Quality Checklist

Before marking work complete:
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No debug logging left in code
- [ ] No magic numbers or hardcoded config
- [ ] Immutable patterns used for shared data
