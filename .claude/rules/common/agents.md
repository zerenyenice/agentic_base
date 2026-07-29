# Agent Orchestration

## Available Agents

Located in `~/.claude/agents/`:

| Agent | Purpose | When to Use |
|-------|---------|-------------|
| backend-coder | Implements Python/FastAPI code (has edit access) | Any backend implementation task |
| frontend-coder | Implements React/TypeScript code (has edit access) | Any frontend implementation task |
| backend-reviewer | Python/FastAPI code review (read-only) | After backend-coder writes/modifies code |
| frontend-reviewer | React/TypeScript code review (read-only) | After frontend-coder writes/modifies code |
| tester | Creates and runs unit/integration/E2E tests (has edit access) | New features, bug fixes, before merge |
| security-reviewer | Security analysis (read-only) | Before commits, sensitive code |

Planning and architecture stay with the Lead (the main agent) — there is no
dedicated planning/architecture subagent. Build fixes and dead-code sweeps are
self-contained commands (`/build-fix`, `/frontend-build`, `/refactor-clean`)
rather than dedicated agents.

## Immediate Agent Usage

No user prompt needed:
1. Complex feature requests - the Lead plans it, then dispatches implementation
2. Code just written/modified - Use **backend-reviewer** / **frontend-reviewer**
3. Bug fix or new feature - Use **tester** to write the failing test first
4. Architectural decision - the Lead decides directly

## Parallel Task Execution

ALWAYS use parallel Task execution for independent operations:

```markdown
# GOOD: Parallel execution
Launch 3 agents in parallel:
1. Agent 1: Security analysis of auth module
2. Agent 2: Performance review of cache system
3. Agent 3: Type checking of utilities

# BAD: Sequential when unnecessary
First agent 1, then agent 2, then agent 3
```

## Delegation Completion Contract

Applies to every agent at every depth (parent, child, grandchild):

1. **Your final message IS the deliverable.** Never end your turn with "waiting for background agents" — a spawned task is not a completed task. Ending your turn while children are running orphans their results (completed children cannot notify a parent whose turn has ended).
2. **If you delegate, you own collection.** Wait for results, integrate them, then return. Fire-and-forget delegation is forbidden.
3. **Decompose only when the work cannot fit in one context.** Do not re-delegate a task already sized for a single agent — depth is an outcome, not a plan.

> Rationale: observed failure mode — research agents followed "Parallel Task Execution" above, spawned children, and returned "waiting" as their final answer. All children completed successfully but their results were orphaned. The parallel rule without a completion contract produces zombie tasks.

## Multi-Perspective Analysis

For complex problems, use split role sub-agents:
- Factual reviewer
- Senior engineer
- Security expert
- Consistency reviewer
- Redundancy checker
