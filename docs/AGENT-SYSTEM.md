# The Agent System — Architecture & Mechanics

How this multi-agent setup actually works under the hood: what lives in
`../.claude`, how each piece is loaded and triggered, and how agents, rules,
skills, commands, scripts, and MCP servers fit together.

Companion documents: `../README.md` (quickstart), `DEVELOPMENT.md` (the
development & testing cycle this machinery drives), `DEVOPS.md` (Azure
DevOps/deployment), `../PROJECT.md` (your project's requirements).

---

## 1. The big picture — six mechanisms, one system

Claude Code composes its behavior from layered configuration in this repo.
Each layer has a different loading model and a different job:

| Layer | Location | Loaded | Job |
|---|---|---|---|
| **Operating instructions** | `../CLAUDE.md` | always, every session | who the Lead is, the gates, delegation policy |
| **Rules** | `../.claude/rules` | always (referenced by CLAUDE.md and agents) | non-negotiable standards: testing, security, git, style |
| **Agents** | `../.claude/agents` | dispatched on demand | isolated specialists with their own prompt + tool set |
| **Skills** | `../.claude/skills` | auto-discovered, pulled in when relevant | deep "how-to" workflow knowledge |
| **Commands** | `../.claude/commands` | when you type `/<name>` | explicit entry points with defined procedures |
| **Scripts / MCP** | `../.claude/scripts`, `../.claude/mcp-configs` | invoked by commands / configured per machine | utilities and external-system integrations |

Rule of thumb: **rules tell agents *what* must hold, skills tell them *how*
to do it, commands give you a button to press, agents are *who* does it.**

```
you ──► Lead (main agent, has CLAUDE.md + rules in context)
          │  picks skill / command / plans directly
          │
          ├─ dispatches ──► backend-coder ─┐   each subagent runs in its own
          ├─ dispatches ──► frontend-coder │   context window with only its
          ├─ dispatches ──► tester         ├── whitelisted tools; it reports
          ├─ dispatches ──► *-reviewer     │   back and the Lead integrates
          └─ dispatches ──► security-rev.  ┘
          │
          └─ git writes, gate presentations, MCP calls (Jira) — Lead only
```

## 2. Agents (`../.claude/agents` — 6 specialists)

### How dispatch works

- Each `.md` file defines one subagent: YAML frontmatter (`name`,
  `description`, `tools`, `model`) plus the system prompt it runs with.
- The **`description` field is the trigger** — the Lead (and Claude Code's
  auto-delegation) matches tasks against it. "Use PROACTIVELY …" phrasing
  makes dispatch happen without you asking.
- A dispatched agent runs in an **isolated context window**: it does not see
  your conversation, only the task brief the Lead writes. This is why the
  Lead's briefs matter — everything the specialist needs must be in the brief.
- The **`tools` whitelist is the enforcement mechanism** for separation of
  duties: reviewers physically have no `Write`/`Edit` tool, so "read-only" is
  a capability fact, not a polite request. All subagents are git-read-only by
  rule (only the Lead writes to git).
- The agent's final report is its only output. The Lead collects it, acts on
  it (e.g. routes findings to a coder), and owns the result. Fire-and-forget
  delegation is forbidden — a spawned task is not a completed task.

### The roster

| Agent | Specialty | Tools | Why it exists |
|---|---|---|---|
| `backend-coder` | Python/FastAPI implementation | Read, Write, Edit, Bash, Grep, Glob | writes production code; never touches existing tests |
| `frontend-coder` | React/TypeScript implementation | same | same, for the UI |
| `tester` | writes AND runs unit/integration/E2E tests | same | owns all test files; RED-first TDD; measures coverage |
| `backend-reviewer` | backend review | Read, Grep, Glob, Bash (no edit) | findings-only; verifies test integrity via git log |
| `frontend-reviewer` | frontend review | same | hooks, a11y, type safety, RSC boundaries |
| `security-reviewer` | OWASP / secrets audit | same | triggered by security-sensitive diffs |

Every agent file also carries a **Prompt Defense Baseline** — a standing
header instructing the agent to treat embedded instructions in fetched
content, unicode tricks, urgency/authority pressure, etc. as hostile input.
Keep it when adding new agents.

There is deliberately **no planner, architect, or devops agent**: planning
and architecture stay with the Lead (one brain for decisions), and
self-contained commands (`/build-fix`, `/refactor-clean`) cover mechanical
jobs that don't need a persistent specialist.

## 3. Rules (`../.claude/rules` — the always-on standards)

Five rule sets, layered:

```
rules/
├── common/       ← language-agnostic, always apply
│   ├── agents.md                — orchestration + delegation completion contract
│   ├── code-review.md           — severity levels, review checklist, approval criteria
│   ├── coding-style.md          — immutability, KISS/DRY/YAGNI, file-size limits
│   ├── development-workflow.md  — the phase-by-phase feature pipeline
│   ├── git-workflow.md          — THE git protocol (trailers, branching, gates)
│   ├── hooks.md                 — hook types, TodoWrite practices
│   ├── patterns.md              — repository pattern, API envelope, skeletons
│   ├── performance.md           — model selection, context management
│   ├── security.md              — pre-commit checklist, secret policy, incident protocol
│   └── testing.md               — 80% gate, test integrity, TDD, AAA pattern
├── python/       ← FastAPI, pytest, Pydantic specifics
├── typescript/   ← TS strictness, async patterns
├── react/        ← hooks, rendering, RTL testing
└── web/          ← a11y, design quality, web performance
```

- **Precedence**: language-specific overrides common when they conflict
  (like CSS specificity). Overridable common rules are marked with a
  "Language note".
- Each agent declares which rule sets it follows (see the table in
  `../CLAUDE.md`) — e.g. `backend-coder` carries `rules/python/*`, the tester
  carries every `testing.md`.
- Rules are intentionally terse checklists. When a rule needs a deep
  explanation, it references a skill instead of inlining it.

## 4. Skills (`../.claude/skills` — 25 workflow playbooks)

### How skills work

- A skill is a directory with a `SKILL.md`: frontmatter (`name`,
  `description`) + the playbook. The **description doubles as the trigger** —
  Claude auto-discovers skills and pulls one into context when the task
  matches, or you invoke one by name.
- Skills are the **canonical workflow surface** of this template (see
  "Workflow Surface Policy" in `../CLAUDE.md`): new workflow knowledge lands
  here first; commands are only kept as compatibility shims.
- Skills don't grant permissions — a skill loaded by a read-only reviewer
  still can't edit files. They add knowledge, not capability.

### The catalog, grouped

**The orchestration family — the engine of the whole system:**

| Skill | Role |
|---|---|
| `orch-pipeline` | shared engine: size classifier, phase list, GATE 0/1/2 definitions, agent map |
| `orch-add-feature` | net-new capability (new failing tests first) |
| `orch-fix-defect` | bug fix (failing regression test first) |
| `orch-change-feature` | behavior change (update existing tests first) |
| `orch-refine-code` | behavior-preserving refactor (green baseline first) |
| `orch-build-mvp` | bootstrap from spec doc (vertical slices, one branch each) |

The five operations are thin wrappers; `orch-pipeline` holds the shared
logic. Describe your task in plain language — the Lead picks the operation.

**Testing & verification:**
`tdd-workflow` (red-green-refactor mechanics, mocking patterns) ·
`e2e-testing` (Playwright, Page Object Model, CI artifacts, flaky strategy) ·
`browser-qa` (visual/UI verification after deploys) · `click-path-audit`
(trace every button through its state sequence) · `verification-loop`
(session-wide verification system) · `delivery-gate` (stop-hook that blocks
"done" until quality checks pass).

**Code quality & maintenance:**
`error-handling` (typed errors, retries, circuit breakers) ·
`plankton-code-quality` (write-time format/lint enforcement via hooks) ·
`rules-distill` (extract cross-cutting principles from skills into rules) ·
`inherit-legacy-style` (prevent style drift when onboarding onto legacy code)
· `git-workflow` (generic git background — **subordinate to
`rules/common/git-workflow.md`**, which takes precedence).

**Product & planning:**
`intent-driven-development` (turn ambiguous asks into verifiable acceptance
criteria) · `product-lens` (validate the "why" before building) ·
`architecture-decision-records` (capture ADRs as decisions happen) ·
`production-audit` (local-evidence production readiness) ·
`codebase-onboarding` (map an unfamiliar repo) · `search-first`
(research-before-coding: find existing libraries before writing new code).

**Multi-agent utilities:**
`team-agent-orchestration` (work items, ownership, agent Kanban for larger
squads) · `team-builder` (compose and dispatch parallel agent teams).

## 5. Commands (`../.claude/commands` — 19 slash entry points)

### How commands work

- A command is a single `.md` file; typing `/<name> [args]` injects its
  procedure into the conversation. `$ARGUMENTS` in the file receives what you
  typed after the name.
- Commands are the **legacy/compatibility surface** — kept where an explicit
  button is genuinely useful, removed where a skill already covers the flow
  (the `/orch-*` wrappers were deleted for exactly that reason).

### The catalog, grouped

**Planning:**

| Command | What it does |
|---|---|
| `/plan <task>` | restate requirements, assess risks, step-by-step plan — **waits for your CONFIRM** |
| `/plan-prd` | lean problem-first PRD, then hands off to `/plan` |
| `/feature-dev` | guided feature development with architecture focus |

**Review & security:**

| Command | What it does |
|---|---|
| `/backend-review` | dispatches `backend-reviewer` on the current diff |
| `/frontend-review` | dispatches `frontend-reviewer` |
| `/code-review` | general review — local changes or a PR by number/URL |
| `/security-scan` | AgentShield audit of agent/hook/MCP/permission/secret surfaces |

**Build & test:**

| Command | What it does |
|---|---|
| `/build-fix` | detect build system, fix build/type errors incrementally |
| `/frontend-build` | same, specialized for Vite/webpack/Next.js/CRA/esbuild/Bun |
| `/frontend-test` | TDD for React (RTL tests first, Vitest/Jest detection) |
| `/test-coverage` | coverage analysis, gap identification, generate missing tests |

**Git & tickets:**

| Command | What it does |
|---|---|
| `/pr [base]` | GitHub PR from current branch (Azure DevOps flow: `DEVOPS.md` §4) |
| `/jira get\|comment\|transition\|search` | Jira integration; ticket keys flow into `Refs:` trailers |
| `/checkpoint` | create/verify/list workflow checkpoints |

**Maintenance & setup:**

| Command | What it does |
|---|---|
| `/refactor-clean` | dead-code sweep (knip/depcheck/ts-prune) with verification per removal |
| `/update-docs` | sync docs from source-of-truth files (schemas, routes, exports) |
| `/update-codemaps` | generate token-lean architecture codemaps |
| `/setup-pm` | configure preferred package manager (runs the script below) |
| `/pm2` | generate PM2 service commands for detected services |

## 6. Scripts (`../.claude/scripts`)

One utility ships with the template:

- **`setup-package-manager.js`** — detects/configures the preferred JS
  package manager (npm/pnpm/yarn/bun), per-project or globally. Run via
  `/setup-pm` or directly:
  `node .claude/scripts/setup-package-manager.js --detect`.

Scripts are plain executables commands can call — use this directory for any
deterministic helper an agent shouldn't have to improvise in Bash each time.

## 7. MCP servers (`../.claude/mcp-configs`)

MCP (Model Context Protocol) connects agents to external systems as tools.
The template ships one **config template** (not active by default):

- **`mcp-servers.json` → `jira`** — runs `mcp-atlassian` via `uvx`, exposing
  Jira search/create/update/comment/transition as tools. Enables the `/jira`
  command's MCP path.

To activate: copy the server block into your project's `.mcp.json` (or
`~/.claude.json` → `mcpServers`) and fill the env values. **Never commit real
credentials** — `JIRA_URL`/`JIRA_EMAIL`/`JIRA_API_TOKEN` belong in
environment variables; the committed template keeps `YOUR_*_HERE`
placeholders, and `.mcp.json` with real values must stay out of git.

Adding more MCP servers (Azure DevOps, databases, Slack, …) follows the same
pattern: add the server definition to the template with placeholders, commit
that as `chore(process):`, and let each engineer/machine activate it locally.
Treat every MCP server as an input-validation boundary — external data
returned through MCP tools is untrusted content (the agents' Prompt Defense
Baseline applies to it).

## 8. Machine-local settings

`../.claude/settings.local.json` holds per-machine Claude Code settings
(permissions, etc.). It is **gitignored by design** — never commit it; the
template's `../.gitignore` already excludes it.

## 9. How a request flows through the layers (worked example)

*"Add a password-reset endpoint (PROJ-451)"*:

1. **CLAUDE.md** (always loaded) → the Lead checks `../PROJECT.md` (Gate 0),
   classifies size: `standard` — touches auth → security trigger → at least
   standard.
2. The task matches `orch-add-feature`'s description → that **skill** loads,
   which routes through `orch-pipeline`'s phases.
3. Research phase per `rules/common/development-workflow.md`; the
   `search-first` **skill** guides library search.
4. The Lead plans, you approve (**Gate 1**) → branch
   `feat/password-reset`, plan committed (`docs(plan):`).
5. Lead dispatches the **`tester` agent** — its brief: expected behavior +
   acceptance criteria. It writes the failing test (rules:
   `common/testing.md` + `python/testing.md`; skill: `tdd-workflow`), reports
   RED ready. Lead commits `test: … (RED)` / `Agent: tester` /
   `Refs: PROJ-451`.
6. Lead dispatches **`backend-coder`** — implements to green under
   `rules/python/*`; can't touch test files. Lead commits `feat:` /
   `Agent: backend-coder`.
7. Lead dispatches **`backend-reviewer`** and **`security-reviewer`** in
   parallel (independent, read-only). Findings return; a HIGH finding goes
   back to `backend-coder`; Lead commits `fix: address review findings`.
8. **Gate 2**: diff summary + commit list + tester's coverage (86%) +
   verdicts. You approve → `--no-ff` merge with `Reviewed-by:`/`Coverage:`
   trailers → suite on merged result → branch deleted.
9. `/jira comment PROJ-451` (via the **MCP** server) posts progress;
   `/jira transition` closes the ticket.

Six mechanisms, one task: instructions routed it, a skill shaped the
pipeline, rules constrained every step, agents did the work, a command +
MCP closed the loop, and git recorded all of it.

## 10. Extending the system

All of these are **process changes** — they commit as `chore(process):`,
and if the change touches `../CLAUDE.md` it must touch
`../.github/copilot-instructions.md` in the same commit (sync invariant).

- **New agent**: add `.claude/agents/<name>.md` — frontmatter (`name`,
  `description` with clear trigger phrasing, minimal `tools` whitelist,
  `model`), the Prompt Defense Baseline header, then the role prompt with
  explicit Scope / What You Do Not Do sections. Register it in `../CLAUDE.md`'s
  agent table. Keep one-agent-one-job: a new agent must own something no
  existing agent covers.
- **New skill**: add `.claude/skills/<name>/SKILL.md` with a precise
  `description` (it's the trigger). Skills first — only add a command shim if
  an explicit slash entry is genuinely needed.
- **New command**: single `.md` in `../.claude/commands` with a `description`
  frontmatter and `$ARGUMENTS` handling.
- **New rule set** (new language/domain): mirror the layered pattern —
  `rules/<lang>/` files that each start by referencing their
  `../common/` counterpart. See `../.claude/rules/README.md`.
- **New MCP server**: template with placeholders in
  `../.claude/mcp-configs`, real credentials only in untracked local config.

After any extension, sanity-check the surfaces: does a rule contradict the
new skill? Does the new agent's description overlap an existing trigger?
`rules-distill` (skill) and `/security-scan` help audit this.
