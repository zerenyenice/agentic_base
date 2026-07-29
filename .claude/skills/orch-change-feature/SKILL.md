---
name: orch-change-feature
description: Orchestrate altering an existing, working feature to new desired behavior — update its tests to the new spec, change the implementation to match, review, and gated commit. Use when behavior is not broken but should be different.
metadata:
  origin: ECC
---

# orch-change-feature

Actor · action · target: **orch · change · feature**. Thin wrapper over the
shared engine in [`orch-pipeline`](../orch-pipeline/SKILL.md).

## When to Use

- An existing feature **works**, but the desired behavior is different ("change",
  "adjust", "make it also …", "instead of X do Y").
- Distinguish from siblings:
  - **not** broken → not `orch-fix-defect` (no bug to reproduce).
  - **not** new → not `orch-add-feature` (the capability already exists).

## Operation settings

- **Default size floor:** small — most tweaks are a function or two.
- **Phase mask:** 0 → (1 only if the new behavior needs research) → light 2 →
  4 → 5 → 6.
- **First move (phase 4):** update the *existing* tests to express the new
  desired behavior, then change the implementation until they pass. Changing the
  tests first is what separates a tweak from a fix.

## How It Works

1. Run the `orch-pipeline` engine with the settings above.
2. Keep the plan light — only `standard`+ size warrants the Lead's full
   planning pass (there is no dedicated planning subagent to delegate to).
3. Stop at **Gate 1** (plan / changed-test approval) and **Gate 2** (merge/push).
4. Add `security-reviewer` if the change touches a security trigger.
5. Git choreography (B5 in `rules/common/git-workflow.md`): the
   tests-updated-to-new-spec commit (`test: update <feature> tests to new
   spec`) comes first, then the implementation change.

## Example

```
orch-change-feature: make nws-poller alert at 2 warnings instead of 3
→ branch feat/alert-threshold-2 → commit updated threshold tests to new spec
→ change impl to green → backend-reviewer/frontend-reviewer
→ merge --no-ff into base  [GATE 2: confirm]
```
