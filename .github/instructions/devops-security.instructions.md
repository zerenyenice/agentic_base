---
applyTo: ".github/workflows/**,**/Dockerfile*,**/docker-compose*.yml,**/docker-compose*.yaml"
---

> Generated from `.claude/rules/devops/security.md` by setup-harness.py — do not edit by hand.

# DevOps Security

> This file extends [common/security.md](../common/security.md) with CI/CD and
> pipeline-specific security content. Owner agent: `devops`; escalation path:
> `security-reviewer`.

## Secrets in Pipelines

- CI secrets live in GitHub Actions secrets / environments — never in
  workflow YAML, repo files, or logs. Refer to secrets **by name only** in
  reports and diagnoses; a masked value pattern (`***`) in a log excerpt is
  still treated as sensitive context.
- Prefer **OIDC federation** (short-lived, scoped tokens exchanged at run
  time) over long-lived cloud keys stored as secrets.
- Deployment environments with production access require GitHub environment
  protection rules (required reviewers) — an agent never bypasses or edits
  protection rules.
- A secret exposed in a CI log or artifact follows the same
  **Committed-Secret Incident Protocol** as one committed to git
  (`common/security.md`): rotate first, then clean up.

## Supply Chain

- Actions pinned to full commit SHAs ([github-actions.md](github-actions.md)).
- Dependencies installed from lockfiles (`pip install`-from-lock /
  `npm ci`, never bare `npm install` in CI).
- Dependency audit runs in CI (`pip-audit`, `npm audit --audit-level=high`);
  new HIGH/CRITICAL advisories are review findings, not noise to silence.
- Container images: pin base image digests for release builds; build images
  scanned (e.g. `trivy`) before publish; images run as non-root.

## Untrusted Input Surfaces

CI is an input boundary like any API endpoint. Treat as untrusted:

- PR titles/bodies, branch names, commit messages, issue text (injection
  into `run:` — see [github-actions.md](github-actions.md))
- Fork PR code (no secrets, no write tokens)
- Third-party action outputs and downloaded artifacts

## Security-Reviewer Triggers

Dispatch `security-reviewer` before merging any change that:

- Uses `pull_request_target`, `workflow_run` chaining, or self-hosted runners
- Grants a workflow write permissions or repo-scoped tokens
- Adds a deploy step, cloud credential, or new secret consumer
- Changes who/what can trigger a workflow (`workflow_dispatch` inputs,
  `repository_dispatch`)
