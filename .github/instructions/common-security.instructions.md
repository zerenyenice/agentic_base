---
applyTo: "**"
---

> Generated from `.claude/rules/common/security.md` by setup-harness.py — do not edit by hand.

# Security Guidelines

## Mandatory Security Checks

Before ANY commit:
- [ ] Staged diff scanned for secrets (`git diff --staged`) — the Lead runs
      this scan before every commit, no exceptions
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on all endpoints
- [ ] Error messages don't leak sensitive data

## Secret Management

- NEVER hardcode secrets in source code
- ALWAYS use environment variables or a secret manager
- Validate that required secrets are present at startup
- Rotate any secrets that may have been exposed

## Committed-Secret Incident Protocol

If a secret is found already committed to git history:
1. **Rotate the secret immediately** — treat it as leaked no matter how fast
   the removal
2. Remove it from the working tree and commit the removal
3. History purging (`git filter-repo` etc.) only with explicit user direction —
   it rewrites history and requires coordination if the repo was pushed

(See `git-workflow.md` for the full git-side protocol.)

## Security Response Protocol

If security issue found:
1. STOP immediately
2. Use **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
