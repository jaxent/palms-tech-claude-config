# Palms Technology Group — Claude Code Configuration
# Team/Project Level | Committed to repo | Read-only for most engineers
# Last updated: 2026-06-15
# Maintainers: Lead Engineering (@jaxent)

---

## About This Project

Palms Technology Group builds and maintains hospitality technology systems
for Grand Palms Resort properties including hotel management, reservations,
guest experience, timeshare operations, and cruise line integrations.

Primary systems:
- **PMS Integration Layer** — Opera, Apaleo, Cloudbeds connectors
- **Guest Experience API** — Mobile app backend, in-room services
- **Reservation Engine** — Real-time availability, rate management
- **Loyalty Platform** — Points, tiers, redemption workflows
- **Cruise Line Integration** — Manifest, shore excursions, onboard billing

---

## Non-Negotiable Rules
<!-- These apply to ALL engineers regardless of personal config -->
<!-- Do not override these in subdirectory CLAUDE.md files -->

- NEVER commit API keys, credentials, or secrets to any file
- NEVER modify files in /generated/** or /vendor/** directories
- NEVER push directly to main or production branches
- NEVER make schema changes without a corresponding migration file
- NEVER call external PMS APIs in unit tests — use mocks only
- ALL async functions must have explicit error handling
- ALL database queries must be parameterized — no string concatenation
- ALL guest PII must be encrypted at rest and masked in logs

---

## Coding Standards

### General
- Language: Python 3.11+ (backend), TypeScript (frontend/API layer)
- Style: PEP 8 for Python, ESLint airbnb config for TypeScript
- Max function length: 50 lines — extract if longer
- Max file length: 300 lines — split if longer
- Docstrings required on all public functions and classes
- Type hints required on all Python functions

### Error Handling
- Use structured error objects — never bare strings
- Always include: error_code, message, is_retryable, context
- Log errors with correlation_id for distributed tracing
- Never swallow exceptions silently

### Testing
- Minimum 80% coverage on all new code
- Unit tests required before PR — TDD preferred
- Integration tests required for all PMS connector changes
- Test file naming: test_<module_name>.py

### Database
- ORM: SQLAlchemy (Python), Prisma (TypeScript)
- All migrations via Alembic — never raw ALTER TABLE in production
- Index all foreign keys and frequently queried columns
- Use connection pooling — never create connections in request handlers

---

## MCP Server Connections
<!-- Claude Code connects to these automatically -->

- **palms-hotel-mcp** — Grand Palms PMS data (reservations, inventory)
- **palms-loyalty-mcp** — Loyalty platform (profiles, points, tiers)
- **palms-jira-mcp** — Ticket creation and project tracking
- **palms-github-mcp** — PR creation, code review, branch management

---

## Protected Files and Directories
<!-- Claude should never modify these without explicit instruction -->

Never touch:
- /vendor/**
- /generated/**
- *.auto.py
- *.auto.ts
- /migrations/** (read only — create new, never edit existing)
- /infrastructure/** (Terraform — separate review process)
- .env files of any kind
- /scripts/deploy/**

---

## Architecture Patterns

### API Design
- RESTful for external APIs, JSON-RPC for internal MCP servers
- Always version APIs: /api/v1/, /api/v2/
- Rate limit all public endpoints
- Return structured errors — never expose stack traces externally

### Hospitality-Specific Patterns
- All reservation operations must be idempotent
- Rate availability calls must never cache longer than 60 seconds
- Guest PII fields: mask in logs, encrypt in storage, never in URLs
- Currency: always store as integer cents, never floating point
- Dates: always UTC in storage, convert to local on display

### Agent and AI Patterns
- Use stop_reason for agentic loop termination — never prompt-based
- Structured error responses on all tool implementations
- Maximum 5 tools per agent for reliable tool selection
- Escalate to human review after 3 failed validation retries
- Never store guest PII in Claude conversation context longer than session

---

## Plan Mode Requirements
<!-- Use /plan before executing in these scenarios -->

Always use plan mode before:
- Any database schema change
- Any change to /src/connectors/** (PMS integrations)
- Any change touching guest PII handling
- Refactoring more than 3 files simultaneously
- Any infrastructure or deployment script change

Direct execution is fine for:
- Adding new API endpoints (no schema change)
- Writing or updating unit tests
- Documentation updates
- Bug fixes in isolated functions

---

## PR and Review Standards

- PR title format: [TYPE] Short description (TYPE: feat/fix/refactor/chore)
- All PRs require at least 1 reviewer
- PRs touching PMS connectors require 2 reviewers
- Link Jira ticket in every PR description
- Run /palm-review before submitting any PR
- Squash commits on merge to main

---

## Commit Message Format

Format: type(scope): short description

Body (optional) — what and why, not how
Footer: TICKET: PALMS-1234

Types: feat, fix, refactor, chore, test, docs
Scopes: pms, loyalty, reservations, guest-api, cruise, infra

Example:

    feat(reservations): add idempotency key to booking endpoint

    Prevents duplicate reservations on network retry.
    Idempotency key stored in Redis with 24hr TTL.

    TICKET: PALMS-892
	
---

## Dependency Management

- Pin all production dependencies to exact versions
- Use requirements.txt for Python, package-lock.json for Node
- Security scan on every dependency addition: pip-audit / npm audit
- No dependencies with known critical CVEs
- Review license compatibility before adding new packages

---

## When to Ask vs When to Proceed

**Always ask before:**
- Deleting any file
- Changing database schema
- Modifying authentication or authorization logic
- Adding external dependencies
- Changing environment variable names

**Proceed without asking:**
- Writing tests for existing code
- Adding docstrings or type hints
- Fixing linting errors
- Creating new files in established patterns

---

## Documentation Standards

### Where Documentation Lives

| Type | Location | Audience |
|---|---|---|
| Code-level docs | Docstrings + GitHub `/docs` | Developers |
| Architecture decisions | Confluence — Engineering Space | Tech leads, architects |
| Operational runbooks | Confluence — Operations Space | DevOps, on-call engineers |
| API reference | GitHub `/docs/api` | Developers, integrators |
| User guides | Confluence — Product Space | Business users, hotel staff |
| Incident post-mortems | Confluence — Operations Space | Engineering, management |

### Documentation Rules

- All public APIs must have a corresponding GitHub doc before merge
- Architecture Decision Records (ADRs) required for:
  - New system integrations (PMS vendors, payment processors)
  - Database schema changes affecting multiple services
  - Security model changes
  - New AI/agent workflow introductions
- Runbooks required for any process that gets paged on-call
- Confluence pages must be reviewed every 6 months — mark stale pages

### ADR Format (Architecture Decision Records)

    Title: ADR-NNNN: Short description
    Date: YYYY-MM-DD
    Status: Proposed | Accepted | Deprecated | Superseded
    
    Context: Why is this decision needed?
    Decision: What did we decide?
    Consequences: What are the tradeoffs?
    Alternatives considered: What else did we evaluate?
	
---

## Contact and Escalation

- Engineering Lead: @jaxent
- PMS Integration questions: #palms-pms-integration (Slack)
- Security issues: security@palmstech.com (do not post in Slack)
- After-hours production issues: PagerDuty escalation policy