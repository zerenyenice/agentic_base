---
name: orch-build-mvp
description: Orchestrate bootstrapping a working MVP from a design or spec document — ingest the doc, plan thin vertical slices, scaffold the first end-to-end slice, then TDD-implement, review, and gated commit. Use to turn an SDD/PRD into a running starting point.
metadata:
  origin: ECC
---

# orch-build-mvp

Actor · action · target: **orch · build · mvp**. Thin wrapper over the shared
engine in [`orch-pipeline`](../orch-pipeline/SKILL.md).

## When to Use

- The user has a **design / spec document** (SDD, PRD, system_design) and wants a
  working vertical slice bootstrapped from it.
- Takes a doc path as its argument, e.g. `civicpulse/docs/SDD-v0.6.md`.

## Operation settings

- **Default size floor:** large — this is the full pipeline including Scaffold.
- **Phase mask:** 0 (read the spec) → 1 → 2 (heavy) → 3 (scaffold) → 4 → 5 → 6.
- **First move (phase 0 → 2):** read the doc; extract scope, locked decisions,
  and the feature list; order it into **thin vertical slices** (one end-to-end
  path first, not all-models-then-all-views). Phase 3 stands up that first slice.

## How It Works

1. Run the `orch-pipeline` engine with the settings above.
2. **Scaffold the first slice through the standard Implement (TDD) phase** —
   no separate generator/evaluator loop. Drive it with the `tester` agent (or
   the `tdd-workflow` skill) for the test, then `backend-coder`/`frontend-coder`
   (whichever applies) for the implementation: write the test for the thin
   end-to-end path first (red), implement the minimal slice (green), refactor.
   Re-run against the spec's acceptance criteria after each step.
3. `backend-reviewer`/`frontend-reviewer` (whichever applies) (+ `security-reviewer`
   on any security-trigger slice), then stop at **Gate 1** (slice plan) and
   **Gate 2** (merge/push). Commit the scaffold and each slice as separate
   `feat:` commits.
4. Repeat phase 4 (Implement) for each subsequent slice in the plan.
5. Git choreography (B9 in `rules/common/git-workflow.md`): each slice is its
   own task branch (`feat/mvp-slice-1-<slug>` …) and its own Gate 2 merge; the
   spec ingestion may produce a user-approved `docs(plan): mvp slice map`
   commit on the base branch so the slice plan itself is versioned.

## Example

```
orch-build-mvp: civicpulse/docs/SDD-v0.6.md
→ read SDD → slice list (vertical)  [GATE 1: approve → branch feat/mvp-slice-1-…]
→ scaffold slice 1 → TDD red/green/refactor against acceptance criteria → review
→ merge slice --no-ff into base  [GATE 2: confirm] → next slice, next branch
```
