---
name: ci-triage
description: Diagnose failing CI pipelines with the gh CLI — locate the failing run/job/step, extract the real error, classify the failure (code, test, config, flaky, secrets), and route it to the right agent. Use when a GitHub Actions run is red, PR checks fail, or the Lead needs pipeline status before a Gate 2 merge.
---

# CI Failure Triage

A repeatable diagnosis loop for red pipelines. CI state lives on GitHub —
local git cannot see it; the `gh` CLI is the channel. Diagnosis is
**read-only**: none of the commands below mutate anything.

## The Loop

### 1. Locate the failing run

```bash
gh run list --branch <branch> --limit 10          # recent runs on the branch
gh pr checks <pr-number>                          # all checks for a PR
gh run list --workflow ci.yml --status failure    # failures of one workflow
```

Note the run ID, the workflow, the head SHA, and whether older runs on the
same SHA passed (a pass→fail flip on the *same* commit already suggests
flakiness or infrastructure).

### 2. Narrow to the failing step

```bash
gh run view <run-id>                    # job summary — which job is red
gh run view <run-id> --log-failed       # logs of failed steps only
gh run view <run-id> --job <job-id> --log   # full log of one job if needed
```

Extract the **exact error lines** — assertion text, traceback, exit code —
not a paraphrase. The error excerpt goes in the report verbatim.

### 3. Reproduce locally (for suspected code/test failures)

Open the workflow file, find the command the failing step runs, and run the
same command locally on the same SHA. Same failure → confirmed code/test
defect. Passes locally → look at environment deltas (versions, env vars,
services, cache) before blaming the code.

### 4. Classify

Exactly one bucket per failure:

| Class | Typical evidence | Route to |
|-------|------------------|----------|
| **Code defect** | Test/type/lint failure, reproduces locally | Lead → `backend-coder` / `frontend-coder` (+ `tester` for a RED regression test) |
| **Test defect** | Implementation verifiably correct; assertion wrong/brittle | Lead → `tester` (coders never edit tests) |
| **Pipeline config** | YAML/syntax error, wrong command, missing dep or cache key, bad matrix entry | `devops` fixes the workflow |
| **Infra/flaky** | Runner outage, network timeout, pass/fail flips on same SHA | `devops` reports; rerun only with Lead authorization |
| **Secrets/permissions** | "secret not found", 401/403 from token scope, forbidden API call | `devops` reports the config fix — never prints secret values |

If evidence is ambiguous between code and flaky, say so explicitly and state
what would disambiguate (e.g. one authorized rerun, or a local repro attempt).

### 5. Report

Hand the Lead a structured diagnosis:

```
Run:            <workflow> #<run-number> — <run URL>
Branch/SHA:     <branch> @ <short-sha>
Failing step:   <job> → <step>
Error:          <verbatim excerpt, trimmed to the relevant lines>
Classification: <one bucket from the table>
Evidence:       <local repro result / same-SHA history / env delta>
Recommended:    <which agent should act, and on what>
Out of scope:   <anything noticed but not part of this diagnosis>
```

## Rules of Engagement

- **Read-only by default.** `gh run rerun`, `gh run cancel`,
  `gh workflow run` and any other mutation happen only when the Lead's task
  scope explicitly authorizes that specific action.
- **One confirming rerun ≠ retry-until-green.** Retrying to conceal flakiness
  is forbidden; flaky tests route to `tester`.
- **Never weaken the pipeline to go green** — that's a gate override, which
  only the user grants (see `rules/devops/ci-cd.md`).
- **Never print secret values**, even masked ones, in reports.

## Related

- Rules: `rules/devops/ci-cd.md`, `rules/devops/github-actions.md`, `rules/devops/security.md`
- Skills: `github-actions` (fixing/authoring workflows once config is the diagnosis)
- Commands: `/build-fix` (local build failures — use this skill only for CI-side failures)
