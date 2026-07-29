---
applyTo: ".github/workflows/**,**/Dockerfile*,**/docker-compose*.yml,**/docker-compose*.yaml"
---

> Generated from `.claude/rules/devops/github-actions.md` by setup-harness.py — do not edit by hand.

# GitHub Actions Standards

> This file extends [ci-cd.md](ci-cd.md) with GitHub-Actions-specific rules.
> Owner agent: `devops`. See skill: `github-actions` for full authoring
> patterns and templates.

## Workflow Structure

- One workflow file per concern (`ci.yml`, `release.yml`, `security.yml`) —
  not one mega-workflow. Same cohesion rule as source files.
- Every workflow declares explicit `on:` triggers with branch/path filters —
  no bare `on: push` that runs the full suite for a README typo.
- Shared logic across workflows goes into **reusable workflows**
  (`workflow_call`) or composite actions — no copy-paste drift between YAML
  files (DRY applies to pipelines too).
- Job and step names describe intent (`Run backend tests with coverage`),
  because they are the first thing a human sees on a red X.

## Security (non-negotiable)

- **Pin third-party actions to a full commit SHA** with a version comment:
  `uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2`.
  Mutable tags (`@v4`, `@main`) are a supply-chain door.
- **Least-privilege `permissions:`** — set `permissions: contents: read` at
  workflow level and grant additions per job. Never rely on the permissive
  default token.
- **Injection-safe expressions** — never interpolate untrusted input
  (`github.event.pull_request.title`, branch names, issue bodies, commit
  messages) directly into `run:` scripts. Pass through `env:` and quote:

  ```yaml
  env:
    PR_TITLE: ${{ github.event.pull_request.title }}
  run: echo "$PR_TITLE"
  ```

- **`pull_request_target` is a security review trigger** — it runs with
  write-token access against fork code. Any use of it (or of
  `workflow_run` chaining) requires `security-reviewer` sign-off before
  merge.
- Secrets only via `secrets:`/environments — never in YAML, never echoed to
  logs, never passed as command-line arguments (visible in process lists).
  Prefer **OIDC federation** over long-lived cloud credentials for deploys.
- Fork PRs never get secrets or write tokens; jobs needing secrets must not
  run on `pull_request` from forks.

## Reliability

- `timeout-minutes` on every job (required by [ci-cd.md](ci-cd.md)).
- `concurrency` groups on PR-triggered workflows with
  `cancel-in-progress: true`.
- Cache with `actions/cache` (or setup-* built-in caching) keyed on lockfile
  hashes; a cache miss must still produce a correct build.
- Matrix builds (`strategy.matrix`) for multi-version testing;
  `fail-fast: false` when per-version results are individually meaningful.
- Steps that upload diagnostics (coverage, logs, screenshots) run with
  `if: always()` so failures still produce evidence.

## Validation Before Handing Back

- Run `actionlint` on changed workflow files when available; at minimum a
  YAML parse check.
- Dry-run the commands a workflow executes (locally or in a scratch dir) —
  a workflow is code and gets the same "run it before reporting done" bar as
  application code.
