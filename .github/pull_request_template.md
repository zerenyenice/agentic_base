<!--
Gate 2 (merge/push gate) checklist for this template repo. See
rules/common/git-workflow.md and rules/common/development-workflow.md.
-->

## Summary

<!-- What changed and why, in 1-3 bullets. -->

-

## Commit protocol confirmation

- [ ] Every commit subject uses a conventional type (`feat|fix|refactor|docs|test|chore|perf|ci`,
      optional `(scope)`, e.g. `chore(process):`)
- [ ] Every commit carries `Agent:` and `Task:` trailers (`Refs:` if there's a ticket)
- [ ] No test files were touched by an implementation (`feat:`/`fix:`) commit

## Coverage

<!-- N/A for docs/process-only PRs (this repo ships no application code). -->

- Coverage: `N/A — docs/process change` <!-- or the tester's measured % -->

## Reviewed-by

<!-- Which reviewer agent(s) ran on this change, e.g. backend-reviewer, security-reviewer. -->

-

## Checklist

- [ ] If any source under `CLAUDE.md`, `.agents_base/`, `.claude/{commands,rules}` changed,
      `python3 setup-harness.py --target all` was re-run and its output committed
- [ ] Secret scan clean (`security.yml` / local `gitleaks detect --source . -v --redact`)
- [ ] Sync invariant holds: `CLAUDE.md` == `.github/copilot-instructions.md` == `AGENTS.md`
- [ ] `harness-sync`, `lint-shell`, `lint-workflows`, `validate-json`, `commit-protocol`,
      `secret-scan` checks are green
