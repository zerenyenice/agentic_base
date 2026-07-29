# CI/CD Standards

> This file extends [common/development-workflow.md](../common/development-workflow.md)
> and [common/testing.md](../common/testing.md) with pipeline-specific standards.
> Owner agent: `devops`.

## Principles

- **Pipeline as code** — all CI/CD lives in versioned files
  (`.github/workflows/`, Dockerfiles). No pipeline behavior configured only
  through the GitHub UI; if it can't be reviewed in a diff, it doesn't exist.
- **CI mirrors the merge gate** — the required checks on a PR are the same
  bar as Gate 2: full test suite green + coverage ≥ 80%. A pipeline that
  passes while the local suite fails (or vice versa) is a defect in the
  pipeline.
- **Fail fast, fail loud** — cheap checks (lint, typecheck) run before
  expensive ones (tests, builds); a red pipeline must point at the failing
  step in its name/summary, never require log archaeology for the headline.
- **Deterministic builds** — pin tool and dependency versions (lockfiles
  committed, action versions pinned). "Works on the runner today" is not
  reproducibility.
- **Never weaken to go green** — deleting a failing step, adding
  `continue-on-error` to a required check, or lowering the coverage threshold
  are gate overrides, which only the user can grant (recorded per
  `common/git-workflow.md`). Agents never do this unilaterally.

## Required Pipeline Stages

For this team's stack, a CI workflow must cover, in fail-fast order:

1. **Lint/format** — `ruff` + `black --check` (backend), `eslint` +
   `prettier --check` (frontend)
2. **Typecheck** — `mypy`/`pyright` (backend), `tsc --noEmit` (frontend)
3. **Tests with coverage** — `pytest --cov` / `vitest --coverage`, failing
   the job under 80%
4. **Build** — frontend production build; container image build when the
   service ships as one
5. **Security** — dependency audit (`pip-audit` / `npm audit`) and secret
   scan on the diff

## Hygiene Requirements

- Every job sets `timeout-minutes` — no default 6-hour hangs.
- Concurrency groups cancel superseded runs on the same branch/PR
  (`concurrency: { group: ..., cancel-in-progress: true }`).
- Cache dependency installs (pip/npm) keyed on the lockfile hash.
- Artifacts (coverage reports, build outputs, screenshots) get explicit,
  short retention — they are debugging aids, not storage.
- Scheduled/cron workflows state in a comment why they exist and who owns
  them.

## Failure Handling

- A flaky test discovered in CI is **reported to the Lead and routed to
  `tester`** — not solved by auto-retrying the job forever. One authorized
  rerun to confirm flakiness is diagnosis; retry-until-green as a policy is
  concealment.
- Infrastructure failures (runner outages, network timeouts) are labeled as
  such in the report, with evidence, so they don't masquerade as code
  regressions.

## Tooling

The CI interaction channel is the **`gh` CLI** (`gh run list`,
`gh run view --log-failed`, `gh pr checks`, `gh workflow view`). The GitHub
MCP server is a complement for cross-repo search and PR review flows — not a
replacement for `gh` in pipeline work. See skill: `ci-triage`.
