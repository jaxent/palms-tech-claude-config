# /palm-review — Pre-PR Code Review
# Palms Technology Group
# Run this before submitting any pull request.
# Usage: /palm-review
# Claude will review all staged/modified files automatically.

Review the current changes in this branch as a senior Palms Technology 
Group engineer would. Work through each section below systematically.

## 1. Security Check (BLOCKING — fix before PR)

- [ ] No hardcoded credentials, API keys, or secrets
- [ ] No guest PII in log statements
- [ ] No PII in URL parameters or query strings
- [ ] Must meet PCI compliance standards
- [ ] All database queries parameterized — no string concatenation
- [ ] No stack traces exposed in API responses
- [ ] Authentication and authorization logic unchanged or explicitly reviewed

## 2. Hospitality Domain Rules (BLOCKING — fix before PR)

- [ ] Reservation operations are idempotent
- [ ] Reservation changes are auditable 
- [ ] Rate availability cache TTL does not exceed 60 seconds
- [ ] Currency values stored as integer cents — no floating point
- [ ] All dates stored as UTC
- [ ] All dates displayed to user are in Property Local time
- [ ] PMS API calls use mocks in tests — no live API calls in test suite
- [ ] Schema changes have corresponding Alembic migration file

## 3. Code Quality (NON-BLOCKING — note but can merge)

- [ ] Functions under 50 lines
- [ ] Files under 300 lines
- [ ] Public functions have docstrings
- [ ] Type hints present on all Python functions
- [ ] Error objects include: error_code, message, is_retryable, context
- [ ] Async functions have explicit error handling
- [ ] No silent exception swallowing

## 4. Test Coverage

- [ ] New code has corresponding unit tests
- [ ] PMS connector changes have integration tests
- [ ] Tests follow naming convention: test_<module_name>.py
- [ ] Coverage does not drop below 80%

## 5. PR Hygiene

- [ ] Commit messages follow format: type(scope): description
- [ ] Jira ticket referenced in PR description
- [ ] PR title follows format: [TYPE] Short description
- [ ] No files modified in /vendor/**, /generated/**, /migrations/**

## Output Format

Provide your review in this structure:

**BLOCKING ISSUES** (must fix before merge)
List each with: file, line number, issue, recommended fix

**WARNINGS** (should fix, can merge with acknowledgment)
List each with: file, issue, recommendation

**SUGGESTIONS** (optional improvements)
Brief list only

**VERDICT**
One of: APPROVE | APPROVE WITH NOTES | REQUEST CHANGES

If no blocking issues found, say so explicitly.