# /palm-ticket — Generate Ticket from Description
# Palms Technology Group
# Generates a properly formatted ticket for Jira or GitHub Issues.
# Usage: /palm-ticket <description of work>
#
# CONFIG — set for your environment:
# TICKET_SYSTEM: jira
# JIRA_PROJECT_KEY: PALMS
# GITHUB_REPO: jaxent/palms-tech-claude-config
#
# Claude will format output for the configured ticket system.

Generate a ticket for the Palms Technology Group engineering backlog.
Check the CONFIG section above and format output accordingly:

- If TICKET_SYSTEM is "jira" — format as a Jira story with all fields
- If TICKET_SYSTEM is "github-issues" — format as a GitHub Issue with
  labels and markdown body
- If both are needed — generate both formats separated by a divider

## Jira Format

**Title:** [TYPE] Short imperative description (max 60 chars)
Types: Feature / Bug / Chore / Refactor / Security

**Project:** (from JIRA_PROJECT_KEY config above)

**Issue Type:** Story / Bug / Task / Sub-task

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
- Documentation needed: GitHub doc / Confluence ADR / Both / None
- Estimated complexity: XS / S / M / L / XL

**Definition of Done:**
- [ ] Code complete and reviewed
- [ ] Unit tests passing with 80%+ coverage
- [ ] Integration tests passing (if PMS connector touched)
- [ ] /palm-review clean
- [ ] GitHub doc updated if public API changed
- [ ] Confluence ADR created if architecture decision made
- [ ] Deployed to staging and smoke tested

**Labels:** (apply all relevant)
pms-integration, guest-pii, breaking-change, needs-migration,
needs-github-doc, needs-confluence-adr, performance, security, tech-debt

---

## GitHub Issues Format

**Title:** [TYPE] Short imperative description

**Labels:** (choose all relevant)
- Type: `bug` `enhancement` `chore` `security` `refactor`
- Domain: `pms` `loyalty` `reservations` `guest-api` `cruise` `infra`
- Flags: `pii` `breaking-change` `needs-migration` `needs-docs`
- Docs: `needs-github-doc` `needs-confluence-adr`

**Body:**

## Summary
2-3 sentences describing what needs to be done and why.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Technical Notes
- Affected files/systems
- Hospitality domain considerations
- Documentation needed

## Definition of Done
- [ ] Code complete and /palm-review clean
- [ ] Tests passing at 80%+ coverage
- [ ] Docs updated (GitHub and/or Confluence as appropriate)
- [ ] Staging verified