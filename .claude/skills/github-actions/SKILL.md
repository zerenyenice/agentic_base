---
name: github-actions
description: Author and modify GitHub Actions workflows for this team's stack — Python/FastAPI backend and React/TypeScript frontend CI, with pinned actions, least-privilege permissions, caching, concurrency, and the 80% coverage gate. Use when creating or changing anything under .github/workflows/.
---

# GitHub Actions Authoring

Patterns for writing workflows that satisfy `rules/devops/github-actions.md`.
Start from the closest template below; never start from a blank file.

## Baseline CI Template (team stack)

```yaml
name: CI

on:
  pull_request:
    branches: [main, dev]
  push:
    branches: [main, dev]

# Least privilege — grant more per job only when needed
permissions:
  contents: read

# Superseded runs on the same ref are wasted money
concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  backend:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      # Pin to full SHA; keep the version comment for humans/Dependabot
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b # v5.3.0
        with:
          python-version: "3.12"
          cache: pip
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt
      - name: Lint and format check
        run: |
          ruff check .
          black --check .
      - name: Typecheck
        run: mypy src/
      - name: Tests with coverage gate
        run: pytest --cov=src --cov-report=term-missing --cov-fail-under=80
      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@b4b15b8c7c6ac21ea08fcf65892d2ee8f75cf882 # v4.4.3
        with:
          name: backend-coverage
          path: coverage.xml
          retention-days: 7

  frontend:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
      - uses: actions/setup-node@39370e3970a6d050c480ffad4ff0ed4d3fdee5af # v4.1.0
        with:
          node-version: 22
          cache: npm
      - name: Install dependencies
        run: npm ci                 # never bare `npm install` in CI
      - name: Lint
        run: npm run lint
      - name: Typecheck
        run: npx tsc --noEmit
      - name: Tests with coverage
        run: npm test -- --coverage
      - name: Production build
        run: npm run build
```

Adjust paths/commands to the actual project layout — but every job keeps
`timeout-minutes`, pinned SHAs, and the coverage gate. **Verify current
action SHAs when authoring** (`gh api repos/actions/checkout/tags`, or the
action's releases page) — the SHAs above are illustrative of the format.

## Recurring Patterns

### Untrusted input → env, never inline

```yaml
# WRONG — script injection via PR title
- run: echo "Checking ${{ github.event.pull_request.title }}"

# CORRECT
- env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "Checking $PR_TITLE"
```

Untrusted: PR titles/bodies, branch names, commit messages, issue text,
review comments — anything a contributor types.

### Per-job permission escalation

```yaml
permissions:
  contents: read          # workflow level: floor

jobs:
  comment:
    permissions:
      contents: read
      pull-requests: write   # only this job may comment
```

### Matrix testing

```yaml
strategy:
  fail-fast: false          # per-version results individually meaningful
  matrix:
    python-version: ["3.11", "3.12"]
```

### Reusable workflow (shared across repos/workflows)

```yaml
# .github/workflows/test-backend.yml
on:
  workflow_call:
    inputs:
      python-version: { required: true, type: string }
# caller:
jobs:
  test:
    uses: ./.github/workflows/test-backend.yml
    with: { python-version: "3.12" }
```

### Diagnostics survive failure

```yaml
- name: Upload Playwright traces
  if: always()
  uses: actions/upload-artifact@b4b15b8c7c6ac21ea08fcf65892d2ee8f75cf882 # v4.4.3
  with: { name: traces, path: test-results/, retention-days: 7 }
```

## Danger Zone (security-reviewer sign-off required)

- `pull_request_target` — write token + fork code; almost always the wrong
  trigger. Justify or replace with `pull_request`.
- `workflow_run` chaining — inherits context across trust boundaries.
- Self-hosted runners on public repos.
- Any new secret consumer or deploy credential — prefer OIDC federation.

See `rules/devops/security.md` for the full trigger list.

## Pre-Handback Checklist

- [ ] `actionlint` clean (or YAML parses if actionlint unavailable)
- [ ] Every third-party action pinned to a full commit SHA + version comment
- [ ] `permissions:` explicit at workflow level
- [ ] `timeout-minutes` on every job
- [ ] `concurrency` group on PR-triggered workflows
- [ ] No untrusted input interpolated into `run:`
- [ ] Commands dry-run locally where possible
- [ ] Coverage gate intact (80% — never lowered to pass)

## Related

- Rules: `rules/devops/github-actions.md`, `rules/devops/ci-cd.md`, `rules/devops/security.md`
- Skills: `ci-triage` (diagnosing runs of these workflows)
