---
name: orch-pipeline
description: Shared orchestration engine for the orch-* skill family. Defines the gated Research-Plan-TDD-Review-Merge pipeline, the size classifier, the agent map, and the two human gates that the orch-* operation skills delegate to. Not usually invoked directly.
metadata:
  origin: ECC
---

# Orchestrator Pipeline (shared engine)

The `orch-*` skills are thin wrappers. They do not re-implement any work — they
classify the request, choose which phases of *this* pipeline run, and delegate
each phase to an existing ECC agent or command. This file is that pipeline.

> Invoke an operation skill (`orch-add-feature`, `orch-fix-defect`, …) rather
> than this engine directly. This file is the reference they point at.

## When to Use

- Loaded indirectly whenever an `orch-*` operation skill runs.
- Read directly only when adding a new operation to the family or tuning the
  shared phases, gates, or agent map.

## The operation family

| Skill | Operation | Trigger | First move |
|-------|-----------|---------|------------|
| `orch-add-feature` | feature | capability does not exist yet | research + plan a new slice |
| `orch-change-feature` | tweak | works, but desired behavior differs | amend existing behavior *and its tests* |
| `orch-fix-defect` | fix | broken; behavior is wrong | reproduce as a failing test, then fix |
| `orch-refine-code` | refactor | behavior stays, structure improves | restructure while keeping tests green |
| `orch-build-mvp` | mvp | bootstrap from a design/spec doc | ingest doc → vertical slices |

> These wrappers **compose** existing commands rather than replace them:
> `/feature-dev`, `/plan`, `/code-review`, `/build-fix`, `/frontend-build`,
> `/refactor-clean`, plus the `tdd-workflow` skill. The orch-* family adds the
> shared size classifier and the two gates on top of them, so one umbrella
> covers all five operations consistently.

## Step 0 — Classify size (right-sizing)

Ceremony scales to blast radius. Score the request on three signals, take the
**highest** tier any signal reaches, and state the result in one line so the user
can override:

| Tier | Files touched | New dependency / contract | Design ambiguity | Phases that run |
|------|---------------|---------------------------|------------------|-----------------|
| trivial | 1, a few lines | none | none — the change is obvious | 4 → 5 → 6 |
| small | 1 file / 1 function | none | clear once you read the code | (1 light) → 4 → 5 → 6 |
| standard | 2–5 files | maybe a new internal module | one real choice to make | 1 → 2 → 4 → 5 → 6 |
| large | many / cross-cutting | new external dep, public API, or a spec doc | multiple open questions | 1 → 2 → (3) → 4 → 5 → 6 |

Phase 0 (Intake) always runs and is omitted from the mask column above. The
tie-breaker: anything touching a security trigger (below) or a public API /
contract is **at least** standard, regardless of file count.

## Phase -1 — Project alignment check (always runs, before Intake)

Before any other phase, check the request against `/PROJECT.md` — the project
team's filled-in customer/business context (scope, constraints, acceptance
criteria). If the request is out of scope, conflicts with a documented
constraint, or the relevant section is still an unfilled `[FILL FREELY]`
placeholder, **stop here** and raise it with the user. → **GATE 0.** This is
not skippable at any size tier, including `trivial`.

## The phases

Each phase delegates — it does not do the work inline.

- **0. Intake** — restate the request. For `orch-build-mvp`, read the spec/design
  doc and extract scope, locked decisions, and a feature list.
- **1. Research & Reuse** — per `rules/common/development-workflow.md`: `gh search repos` /
  `gh search code`, then Context7 / vendor docs, then package registries, then
  Exa. Prefer adopting a proven implementation over net-new code.
- **2. Plan** — the Lead plans directly (no dedicated planning/architecture
  subagent in this setup). Output a `task_list` ordered as thin vertical
  slices. → **GATE 1.** On approval, the Lead creates the task branch
  `<type>/<task-slug>` off the currently checked-out base branch (stashing any
  dirty tree first — `git stash -u`) and commits the approved plan as the
  branch's first commit (`docs(plan): <task> implementation plan`,
  `Agent: lead`).
- **3. Scaffold** — `orch-build-mvp` only: stand up the first end-to-end slice.
- **4. Implement (TDD)** — drive each task through the `tester` agent (or the
  `tdd-workflow` skill) for the test, then `backend-coder`/`frontend-coder`
  (whichever applies) for the implementation: red → green → refactor. Honor
  the operation's first-move rule. **The Lead commits the RED test on the task
  branch (`test: <desc> (RED)`, `Agent: tester` trailer) before the coder
  starts** — the implementation commits must not touch test files (per
  `rules/common/testing.md` Test Integrity), and each carries the coder
  agent's `Agent:` trailer. Task-branch commits are protocol-internal: the
  Lead makes them at these choreography points without asking.
- **5. Review** — `backend-reviewer`/`frontend-reviewer` (whichever applies) /
  `/code-review`. Add `security-reviewer` whenever the diff touches a security
  trigger (below). Fixes for CRITICAL/HIGH findings land as separate
  `fix: address review findings` commits — never folded into the original
  implementation commit.
- **6. Merge** — → **GATE 2** (the merge/push gate): present the diff summary,
  the commit list, and the tester's measured coverage; wait for user
  confirmation. On approval, `git merge --no-ff` the task branch back into its
  base branch with `Reviewed-by:` and `Coverage:` trailers on the merge
  commit, run the suite on the merged result, and delete the merged branch
  (`git branch -d`).

## The gates

This family is **gated, not autonomous**:

0. **GATE 0 — before Intake.** Confirm the request is feasible and acceptable
   per `/PROJECT.md`; do not proceed to Intake until it clears. See Phase -1
   above.
1. **GATE 1 — after Plan.** Present the `task_list`; do not write implementation
   code until the user approves.
2. **GATE 2 — before Merge/Push.** Task-branch commits are protocol-internal
   and happen automatically at the choreography points; the gate guards the
   merge back into the base branch (and any push / PR). Present the diff
   summary, the commit list, and the tester's measured coverage number; do not
   merge or push until the user confirms. Coverage below 80% blocks the gate
   unless the user explicitly overrides with a stated reason (recorded in the
   merge commit body).

Everything between the gates flows without stopping.

## Agent / command map

| Phase | Primary | Fallback / escalation |
|-------|---------|----------------------|
| Intake / understand | Explore (built-in) / Grep | trace existing paths before a tweak, fix, or refactor |
| Plan | The Lead, directly | — (no dedicated planning/architecture subagent) |
| Implement (tests) | `tester` (or `tdd-workflow` skill) | — |
| Implement (code) | `backend-coder` (Python/FastAPI) / `frontend-coder` (React/TS) | `/build-fix` (generic) or `/frontend-build` (frontend) on build breaks |
| Review | `backend-reviewer` / `frontend-reviewer` / `/code-review` | whichever stack the diff touches; both if it touches both |
| Security | `security-reviewer` | — |
| MVP inner loop | phase 4 (Implement/TDD) applied to the first slice | no separate generator/evaluator loop — the scaffold slice follows the same TDD cycle as any other task |

Match the reviewer agent to the stack the diff touches.

## Security-review trigger

Pull in `security-reviewer` when the diff touches any of: authentication or
authorization, user-input handling, database queries, file-system paths,
external API calls, cryptography, or secrets / credentials. (Per `rules/common/security.md`.)

## Handoff artifacts

The pipeline carries no hidden state — the planning docs *are* the handoff:

- `task_list` (from Plan) drives the Implement loop.
- Larger work may also emit PRD / architecture / system_design under the repo's
  `docs/` per `rules/common/development-workflow.md`.
- Review findings (CRITICAL / HIGH) must be resolved before Gate 2.

## Verification

- Gate 0 (project alignment against `/PROJECT.md`) was checked before Intake
- size tier was stated and matched the work
- Gate 1 (plan) and Gate 2 (merge/push) were both honored
- the task branch is named `<type>/<task-slug>` and the plan commit
  (`docs(plan):`) is its first commit
- the RED test commit precedes any implementation commit
  (`git log --oneline` order), and implementation commits show no test files
  (`git log --stat`) — test integrity per `rules/common/testing.md`
- all commits carry `Agent:` and `Task:` trailers
- `security-reviewer` ran iff a security trigger was touched
- commits are conventional and scoped to one logical change
- new / changed behavior has tests; measured coverage ≥ 80% was reported at
  Gate 2 (or an explicit user override was recorded)
- the merge was `--no-ff` after Gate 2 with `Reviewed-by:`/`Coverage:`
  recorded on the merge commit, and the merged task branch was deleted
