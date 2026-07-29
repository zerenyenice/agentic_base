# Development & Testing Cycle — How This System Works

The complete reference for how a task travels through this agent system: from
the moment you describe it, through planning, test-driven implementation,
review, and the merge you approve. Companion documents: `../README.md` (quick
overview), `DEVOPS.md` (Azure DevOps, containers, releases), `../PROJECT.md`
(your project's requirements — the input to all of this).

Authoritative sources this document summarizes (agents follow those, humans
read this): `../CLAUDE.md`, `../.claude/rules`, `.claude/skills/orch-*`,
`../.claude/agents`.

---

## 1. The cast

One human, one orchestrator, six specialists:

| Actor | Role | File access | Git access |
|---|---|---|---|
| **You** (the user) | Sets tasks, approves at the gates, owns overrides | — | — |
| **Lead** (main agent) | Plans, decides architecture, dispatches all work, owns git | full | **only** actor that writes to git |
| `backend-coder` | Implements Python/FastAPI | edit | read-only |
| `frontend-coder` | Implements React/TypeScript | edit | read-only |
| `tester` | Writes AND runs unit/integration/E2E tests | edit | read-only |
| `backend-reviewer` | Reviews backend diffs, reports findings | read-only | read-only |
| `frontend-reviewer` | Reviews frontend diffs, reports findings | read-only | read-only |
| `security-reviewer` | OWASP/secret audits on sensitive diffs | read-only | read-only |

Three separations of duty hold the system together:

1. **Lead plans, specialists execute** — the Lead never implements, tests, or
   reviews work a specialist covers (exception: trivial one-line fixes).
2. **Coders never touch tests; the tester never gets reviewed by itself** —
   tests are tester-owned, findings are reviewer-owned, fixes are coder-owned.
3. **Only the Lead writes to git** — one committer keeps history linear and
   every commit attributable (`Agent:` trailer names the producing agent).

## 2. The cycle at a glance

```
you describe a task
   │
   ▼
[GATE 0] PROJECT.md feasibility check ──── out of scope? → stop, raise it with you
   │
   ▼
Intake + size classification (trivial / small / standard / large)
   │
   ▼
Research & reuse (skipped for small fixes)
   │
   ▼
Plan — the Lead writes a task_list of thin vertical slices
   │
   ▼
[GATE 1] you approve the plan
   │        → task branch <type>/<slug> created off the current branch
   │        → approved plan committed first: docs(plan):
   ▼
TDD loop (on the task branch; commits are automatic)
   │   tester writes failing test ──► committed: test: … (RED)
   │   coder implements to green  ──► committed: feat:/fix: (no test files!)
   │   refactor                   ──► committed: refactor:
   ▼
Review loop
   │   reviewers report findings ──► CRITICAL/HIGH fixed by the coder
   │                                 committed: fix: address review findings
   │   security-reviewer joins when the diff touches a security trigger
   ▼
[GATE 2] you approve the merge — diff summary + commit list + coverage (≥80%)
   │
   ▼
merge --no-ff into the base branch → suite runs on merged result → branch deleted
```

Everything between the gates flows without stopping. Everything at a gate
waits for you.

## 3. Gate 0 — the PROJECT.md check (always, first, not skippable)

Before any work — including trivial tasks — the Lead checks the request
against `/PROJECT.md`, the project team's filled-in requirements document:

- **Out of scope / conflicts with a documented constraint** (business rule,
  security/compliance, acceptance criteria) → the Lead stops and raises it
  with you. It never silently narrows or reinterprets scope to make a request
  fit.
- **Relevant section still `[FILL FREELY]`** → the Lead tells you that part
  of the project context is undefined and asks, rather than inventing it.
- Agents read PROJECT.md, never edit it (unless a human explicitly instructs).
  When the team updates it, that lands as its own `docs(project):` commit on
  the base branch — so `git log -p -- PROJECT.md` is your requirements
  changelog. After such a change, the Lead checks whether already-merged
  features are affected and proposes change tasks for the deltas.

## 4. Sizing — ceremony scales to blast radius

The Lead classifies every request and states the tier in one line (you can
override it):

| Tier | Typical shape | Phases that run |
|---|---|---|
| **trivial** | 1 file, a few lines, obvious change | TDD → review → merge |
| **small** | 1 file / 1 function, clear after reading the code | (light research) → TDD → review → merge |
| **standard** | 2–5 files, one real design choice | research → plan (GATE 1) → TDD → review → merge |
| **large** | cross-cutting, new dependency, public API, or a spec doc | full pipeline incl. scaffold |

Tie-breaker: anything touching a **security trigger** or a public
API/contract is at least `standard`, regardless of file count.

Trivial tasks may use a short-lived branch merged immediately after Gate 2 —
or, with your explicit OK, commit directly to the base branch. Commit trailers
and the coverage gate still apply; nothing is ever exempt from those.

## 5. The five operations

You don't need to name these — describe the task and the Lead picks the right
one. Each differs only in its **first move** in the TDD phase:

| Operation | When | First move (the thing that defines it) |
|---|---|---|
| `orch-add-feature` | capability doesn't exist yet | write *new* failing tests for the new behavior |
| `orch-fix-defect` | behavior is broken | reproduce the bug as a failing **regression test** — proof the bug existed, forever in history |
| `orch-change-feature` | works, but should behave differently | update the *existing* tests to the new spec first |
| `orch-refine-code` | same behavior, better structure | confirm tests are **green before touching anything**; add characterization tests if coverage is thin |
| `orch-build-mvp` | bootstrap from a spec/PRD | slice the spec into thin vertical slices; one branch + one merge per slice |

The shared engine behind all five is `../.claude/skills/orch-pipeline/SKILL.md`.

## 6. Research & planning (standard+ tiers)

- **Research before writing**: GitHub code search first, then library docs,
  then package registries — the system prefers adopting a proven
  implementation over net-new code.
- **The Lead plans directly** (there is no planning subagent): task_list
  ordered as thin vertical slices, dependencies, risks, phases. Larger work
  also produces PRD/architecture/system-design docs.
- **GATE 1** — you see the plan and approve it before any implementation code
  is written. Approval triggers two git actions: the task branch
  `<type>/<task-slug>` is created off whatever branch is checked out (a dirty
  working tree is stashed first, never carried over), and the approved plan is
  committed as the branch's **first commit** (`docs(plan):`). The plan you
  approved is frozen in history — scope drift during implementation shows up
  as a diff against it.

## 7. The testing cycle (the heart of the system)

### 7.1 TDD choreography

Mandatory for every behavior change, enforced by commit order on the branch:

1. **RED** — the `tester` writes a failing test describing the expected
   behavior, runs it, and confirms it fails *for the right reason*. It reports
   ready; the Lead commits it: `test: <desc> (RED)` with `Agent: tester`.
   **This commit must precede any implementation commit** — it is the
   tamper-proof checkpoint.
2. **GREEN** — the coder agent implements the minimal change that makes the
   test pass. Its diff **must not touch test files**. The Lead commits:
   `feat:`/`fix:` with the coder's `Agent:` trailer.
3. **Verify** — the tester re-runs the suite and confirms the test files are
   byte-identical to the committed RED version
   (`git diff <red-sha> -- <test files>`). Any difference is a test-integrity
   violation flagged to the Lead, not proceeded past.
4. **REFACTOR** — clean up with tests staying green; own `refactor:` commit.
5. **Coverage** — the tester measures (`pytest --cov` / `npm run
   test:coverage`) and reports the number to the Lead. It is a blocking input
   to Gate 2, not an FYI.

### 7.2 Test ownership and integrity

Tests are the spec. The rules that keep them honest:

- **Tests are tester-owned.** Coders never modify existing test files. If a
  test looks wrong, the coder stops and reports it; the tester fixes it.
- **Seeing the test is not cheating** — making the visible test pass is the
  point of TDD. *Editing* the test, or hard-coding the implementation to
  return the tests' literal expected values, is — reviewers treat both as
  CRITICAL/blocking.
- **Git is the proof.** The RED commit precedes implementation
  (`git log --oneline`); implementation commits show no test files
  (`git log --stat`). Reviewers verify both.

### 7.3 Test types — all three required

| Type | Covers | When |
|---|---|---|
| **Unit** | individual functions/components in isolation | always |
| **Integration** | API endpoints, database operations | always |
| **E2E** (Playwright) | critical user flows (auth, core features, CRUD, payments) | critical paths |

Edge cases the tester must cover: null/undefined, empty collections/strings,
invalid types, boundary values, error paths (network/DB failures), race
conditions, large data sets, special characters (Unicode, SQL
metacharacters).

Anti-patterns it avoids: testing implementation details instead of behavior,
shared state between tests, assertions too weak to catch a real regression,
unmocked external dependencies.

E2E discipline: Page Object Model, `data-testid` locators, real waits (never
`waitForTimeout`), new tests run 3–5× locally to prove they're not flaky;
flaky tests are quarantined with a linked issue, never silently deleted.
Targets: 100% of critical journeys passing, >95% overall pass rate, <5%
flaky, suite under 10 minutes.

### 7.4 Coverage — a merge gate, not a suggestion

- **Minimum: 80%** (branches, functions, lines, statements).
- Measured by the tester, reported to the Lead, presented to you at Gate 2.
- Below 80% **blocks the merge** unless you explicitly override with a stated
  reason — and the override is recorded in the merge commit body, not applied
  silently.
- Commits *on* the task branch are never blocked by coverage — the gate sits
  at the merge, so the RED-first choreography is never impeded.
- Infra-only tasks (no app code) replace the coverage number with
  verification evidence — see `DEVOPS.md` §7.

### 7.5 When tests fail

Order of suspicion: (1) test isolation, (2) mocks, (3) the implementation.
Fix the implementation, not the test — unless the test itself is wrong, which
is the tester's call to make, never the coder's.

## 8. The review cycle

Runs after implementation, before Gate 2, on every non-trivial diff:

- **Who**: `backend-reviewer` for Python diffs, `frontend-reviewer` for
  React/TS diffs — both when a task touches both. They are read-only: they
  report findings; they never edit.
- **What they check**: security patterns, test integrity (§7.2), error
  handling, type safety, async correctness, accessibility (frontend),
  performance smells, code-quality limits (functions <50 lines, files <800,
  nesting ≤4).
- **Severity model**:

  | Level | Meaning | Effect |
  |---|---|---|
  | CRITICAL | security vulnerability, data-loss risk, test tampering | **blocks** — must fix before merge |
  | HIGH | bug or significant quality issue | blocks (Block verdict) — fix before merge |
  | MEDIUM | maintainability concern | merge with caution; fix when possible |
  | LOW | style / minor | optional |

- **The loop**: findings go to the Lead → the Lead dispatches CRITICAL/HIGH
  fixes back to the relevant coder → fixes land as **separate**
  `fix: address review findings` commits (never folded into the original
  implementation commit, so finding→fix stays traceable) → re-review if
  needed.
- **The verdict** (Approve / Warning / Block) is recorded on the eventual
  merge commit as a `Reviewed-by:` trailer. Zero findings is a valid, expected
  outcome — reviewers don't invent issues to look busy.

### Security review

`security-reviewer` joins automatically whenever the diff touches a trigger:
authentication/authorization, user-input handling, database queries,
file-system paths, external API calls, cryptography, secrets/credentials
(plus the infra triggers in `DEVOPS.md` §6). It runs the OWASP Top 10
checklist and secret detection. Its approval also becomes a
`Reviewed-by: security-reviewer` trailer.

Independent of any review, the Lead scans the staged diff for secrets before
**every** commit. If a secret is ever found already committed: rotate first
(treat as leaked regardless of how fast the removal), remove and commit,
purge history only with your explicit direction.

## 9. Gate 2 and the merge

Gate 2 is the **merge/push gate** — the single point where task work becomes
part of the shared base branch. The Lead presents:

1. **Diff summary** — what changed, against the plan you approved at Gate 1.
2. **Commit list** — the branch's story: plan → RED → GREEN → refactor →
   review fixes.
3. **Coverage** — the tester's measured number (or infra verification
   evidence), with the 80% rule applied.
4. **Reviewer verdicts** — including security if triggered.

On your approval:

- `git merge --no-ff` into the base branch, with `Reviewed-by:` and
  `Coverage:` trailers on the merge commit (on Azure DevOps with branch
  policies, push + PR replaces the local merge — `DEVOPS.md` §4).
- **Post-merge verification**: the suite runs once on the merged result —
  two individually green branches can still merge into a broken state.
- The merged task branch is deleted (`git branch -d`).

If you reject the merge, the task branch is cheap to discard or rework —
nothing has touched the base branch.

### Base-branch drift

If the base branch moved while the task was in flight, the Lead merges the
base *into* the task branch first (never rebases), resolves conflicts there,
re-runs the full suite on the task branch, and only then brings the task to
Gate 2.

## 10. Git as the audit trail

Every commit carries trailers (`Agent:`, `Task:`, optional `Refs:` for
ticket keys); merge commits add `Reviewed-by:` and `Coverage:`. History is
append-only — no amend, rebase, or squash on protocol commits; no force-push,
ever. The payoff — anyone can reconstruct from `git log` alone:

```bash
git log --grep "Task: user-registration"   # one task's full story, in order
git log --grep "Agent: tester"             # everything the tester produced
git log --grep "Refs: PROJ-123"            # all commits for a ticket
git log --grep "Reviewed-by:"              # every reviewed merge
git log -p -- PROJECT.md                   # how requirements evolved
```

Full protocol (branching, forbidden operations, bootstrap, incident
handling): `../.claude/rules/common/git-workflow.md`.

## 11. Knowledge capture

At the end of a task, information lands where it belongs:

- **Personal** debugging notes, preferences, session context → the agent's
  auto memory (never committed).
- **Team/project** knowledge (architecture decisions, API changes, runbooks)
  → the project's docs structure, as `docs:` commits; ADRs as `docs(adr):`
  alongside the change they explain.
- No duplication: if the task's code/docs already carry the information, it
  isn't restated elsewhere. No obvious doc home → the Lead asks before
  creating a new top-level file.

## 12. Failure & edge scenarios (what the system does when things go wrong)

| Scenario | Behavior |
|---|---|
| Request out of scope per PROJECT.md | Gate 0 stop; raised with you before any work |
| PROJECT.md section unfilled | Lead tells you and asks; never invents context |
| Build breaks during implementation | `/build-fix` (generic) or `/frontend-build` (React/TS) — incremental fixes, verify after each |
| Test fails after implementation | isolation → mocks → fix the implementation, not the test (§7.5) |
| Coder believes a test is wrong | stops, reports to the Lead; tester adjudicates and fixes if warranted |
| Implementation diff touched a test file | test-integrity violation — CRITICAL finding, blocks until resolved |
| Flaky E2E test | quarantined with linked issue (`test.fixme()`), never deleted silently |
| Coverage below 80% at Gate 2 | merge blocked; proceeds only on your explicit override, reason recorded in the merge commit |
| Reviewer finds CRITICAL/HIGH | dispatched back to the coder; separate fix commit; re-review |
| Security trigger touched | security-reviewer added automatically |
| Secret found in staged diff | commit refused; secret moved to env/secret manager |
| Secret found already in history | rotate immediately → remove → purge only on your direction |
| Dirty working tree at task acceptance | stashed (`git stash -u`), restored after returning to the base branch |
| Base branch drifted mid-task | base merged into task branch, suite re-run, then Gate 2 |
| Merge makes the suite fail post-merge | task not declared done; fixed before anything else proceeds |
| Subagent invocation fails | Lead reports why — it does not silently do the work itself |
| Working directory is not a git repo | Lead stops and bootstraps (git init + .gitignore + `chore:` commit) with your confirmation — the integrity model needs git |

## 13. Parallel work

- Multiple agents on the **same task** run in parallel freely (e.g. both
  reviewers at once); their work lands as separate commits on the one task
  branch.
- Multiple **task branches** may exist, but the working tree holds one
  checked-out branch — the Lead serializes file work and never switches
  branches with uncommitted changes (finish, or stash + commit clean, first).

## 14. Commands you might type (optional — plain language works)

| Command | Use |
|---|---|
| `/plan <task>` | plan without writing code; waits for your approval |
| `/backend-review`, `/frontend-review` | on-demand review outside the cycle |
| `/security-scan` | project-wide security audit |
| `/test-coverage` | coverage analysis + generate missing tests |
| `/frontend-build`, `/build-fix` | incremental build-failure fixing |
| `/jira get <KEY>` | pull a ticket; its key flows into `Refs:` trailers |
| `/pr` | GitHub PR from the current branch (`DEVOPS.md` §4 for Azure DevOps) |

## 15. Success criteria (every task, before it's called done)

- All tests pass; coverage ≥80% (or your recorded override)
- No CRITICAL/HIGH review findings open; security review ran iff triggered
- Git story complete and ordered: plan → RED → GREEN → (refactor) → (review
  fixes) → reviewed merge; all commits carry trailers
- Suite green on the merged result; task branch deleted
- The change satisfies PROJECT.md — the requirement it started from
