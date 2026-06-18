# /palm-deploy-check — Pre-Deployment Verification
# Palms Technology Group
# Run before deploying any change to staging or production.
# Usage: /palm-deploy-check
# Claude will analyze the diff against main and verify deployment readiness.

Perform a pre-deployment verification for the current branch as a 
Palms Technology Group senior engineer preparing a production deployment.

## 1. Change Impact Assessment

Analyze the diff and categorize impact:

**Database changes?**
- Migration files present and reviewed?
- Rollback migration exists?
- Migration tested on staging data volume?

**PMS connector changes?**
- Opera / Apaleo / Cloudbeds integration affected?
- PMS vendor notified if API contract changed?
- Fallback behavior if PMS is unavailable?

**Guest PII handling changes?**
- Encryption unchanged or explicitly reviewed?
- Logging changes reviewed for PII exposure?
- GDPR/CCPA impact assessed?
- Must meet PCI compliance standards

**API contract changes?**
- Breaking changes to public endpoints?
- Version bump applied?
- Consumer teams notified?

**UX Changes **
- All dates displayed to user are in Property Local time

## 2. Deployment Risk Rating

Rate the deployment: LOW / MEDIUM / HIGH / CRITICAL

LOW — isolated change, no schema, no PMS, no PII
MEDIUM — new feature, no schema change, limited blast radius  
HIGH — schema change, PMS connector change, or PII handling change
CRITICAL — authentication change, encryption change, or multi-system impact

## 3. Rollback Plan

Based on the changes, describe:
- How to roll back if deployment fails
- Estimated rollback time
- Whether database rollback is required
- Who needs to be notified on rollback

## 4. Deployment Checklist

- [ ] All tests passing on CI
- [ ] /palm-review completed with no blocking issues
- [ ] Staging deployment successful
- [ ] Smoke tests passing on staging
- [ ] Database migration tested on staging
- [ ] Monitoring and alerts configured for new code paths
- [ ] On-call engineer aware of deployment
- [ ] Rollback plan documented and tested

## 5. Go / No-Go Recommendation

Provide explicit GO or NO-GO with reasoning.

If NO-GO, list exactly what must be resolved before deploying.
If GO, note any monitoring to watch in the first 30 minutes post-deploy.