---
name: orch-fix-defect
description: Orchestrate fixing a bug — reproduce it as a failing regression test, fix to green, review, and gated commit — by delegating each phase to the matching ECC agent. Use when existing behavior is broken or wrong.
metadata:
  origin: ECC
---

# orch-fix-defect

Actor · action · target: **orch · fix · defect**. Thin wrapper over the shared
engine in [`orch-pipeline`](../orch-pipeline/SKILL.md).

## When to Use

- Something is **broken**: wrong output, an error, a crash, a regression.
- Distinguish from siblings:
  - behavior is correct but you want it different → `orch-change-feature`.
  - the capability does not exist yet → `orch-add-feature`.

## Operation settings

- **Default size floor:** small (often trivial).
- **Phase mask:** 0 → (light 2 only if root cause is non-obvious or standard+) →
  4 → 5 → 6. Research (1) is usually skipped.
- **First move (phase 4):** reproduce the bug as a **new failing** test
  (regression test), then fix until it goes green. Proving the bug exists first
  is what separates a fix from a tweak.

## How It Works

1. Run the `orch-pipeline` engine with the settings above.
2. If the root cause is unclear, scope it with the Explore agent / Grep before
   the red test; escalate build breaks to `/build-fix` or `/frontend-build`.
3. Stop at **Gate 1** (only if a plan was produced) and **Gate 2** (merge/push).
4. Add `security-reviewer` if the defect sits in a security-sensitive path.
5. Git choreography (B4 in `rules/common/git-workflow.md`): the regression
   test commits first (`test: reproduce <bug> (RED)`), the fix commits as
   `fix:`, and the ticket key (if any) goes in the `Refs:` trailer.

## Example

```
orch-fix-defect: poller crashes on empty NWS response
→ branch fix/empty-poller-crash → commit failing regression test (RED)
→ fix to green (commit: fix:, Refs: ticket) → code-review
→ merge --no-ff into base  [GATE 2: confirm]
```
