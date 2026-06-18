# /palm-ticket — Generate Jira Ticket from Description
# Palms Technology Group
# Generates a properly formatted Jira ticket from a natural language description.
# Usage: /palm-ticket <description of work>
# Example: /palm-ticket Add idempotency key to the booking endpoint

Generate a Jira ticket for the Palms Technology Group engineering backlog
based on the description provided. Use this structure:

## Ticket Output Format

**Title:** [TYPE] Short imperative description (max 60 chars)
Types: Feature / Bug / Chore / Refactor / Security

**Epic:** (infer from description — choose one)
- PMS Integration
- Guest Experience API  
- Reservation Engine
- Loyalty Platform
- Cruise Line Integration
- Infrastructure
- Security & Compliance

**Priority:** (infer from description)
- Critical — production down or security issue
- High — major feature or significant bug
- Medium — standard feature work
- Low — chore, refactor, minor improvement

**Description:**
2-3 sentences. What needs to be done and why.

**Acceptance Criteria:**
3-5 specific, testable criteria.
Format: Given/When/Then where appropriate.

**Technical Notes:**
- Affected systems and files (infer from description)
- Dependencies or blockers if any
- Hospitality domain considerations (PII, idempotency, PMS impact)
- Estimated complexity: XS / S / M / L / XL

**Definition of Done:**
- [ ] Code complete and reviewed
- [ ] Unit tests passing with 80%+ coverage
- [ ] Integration tests passing (if PMS connector touched)
- [ ] Security checklist passed (/palm-review clean)
- [ ] Documentation updated if public API changed
- [ ] Deployed to staging and smoke tested

**Labels:** (apply all relevant)
pms-integration, guest-pii, breaking-change, needs-migration,
performance, security, tech-debt