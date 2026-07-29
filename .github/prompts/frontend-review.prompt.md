---
mode: agent
description: Comprehensive frontend (React/TypeScript) code review for hook correctness, render performance, accessibility, server/client component boundaries, type safety, and frontend security. Invokes the frontend-reviewer agent.
---

> Generated from `.claude/commands/frontend-review.md` by setup-harness.py — do not edit by hand.

# Frontend Code Review

This command invokes the **frontend-reviewer** agent for React/TypeScript code review — one agent covers both React-specific and general TS/JS concerns.

## What This Command Does

1. **Identify Frontend Changes**: Find modified `.tsx`/`.jsx`/`.ts`/`.js` files via `git diff`
2. **Run Lint**: Execute `eslint` with `eslint-plugin-react-hooks` and `eslint-plugin-jsx-a11y`
3. **Typecheck**: Run `tsc --noEmit` or the project's canonical typecheck command
4. **Review**: Hook rules, RSC boundaries, accessibility, render performance, type safety, async correctness, frontend security
5. **Generate Report**: Categorize issues by severity (CRITICAL / HIGH / MEDIUM)

## When to Use

Use `/frontend-review` when:

- After `frontend-coder` writes or modifies components, hooks, or pages
- A PR or commit touches `.tsx`/`.jsx`/`.ts`/`.js` files
- Before merging frontend code
- Auditing accessibility on UI components
- Auditing a Next.js App Router server/client component boundary

For non-frontend-specific concerns on the same PR, use `/code-review` (general).

## Review Categories

### CRITICAL (Must Fix)

- `dangerouslySetInnerHTML`/`innerHTML` with unsanitized input
- `href`/`src` with unvalidated user URLs (`javascript:`, `data:`)
- Server Action without input validation
- Secret in client bundle (`NEXT_PUBLIC_*`, `VITE_*`, `REACT_APP_*`)
- `localStorage`/`sessionStorage` for session tokens
- Conditional hook calls (violates Rules of Hooks); direct state mutation
- Hook called outside a component or custom hook

### HIGH (Should Fix)

- Missing `useEffect`/`useMemo`/`useCallback` deps (disabled `exhaustive-deps` without justification)
- Effect for derived state; effect missing cleanup; stale closures
- Server-only imports in Client Components; sensitive data leaked via props
- Server Actions without auth checks
- Accessibility violations (missing labels, non-semantic interactive elements, ARIA misuse)
- `key={index}` in dynamic lists; duplicated state; `useEffect` chains
- `any` without justification; unhandled promise rejections; swallowed errors

### MEDIUM (Consider)

- Over-memoization without measured win; inline object/function prop to memoized child
- Suspense at route root only; long lists without virtualization
- Roll-your-own validation in non-trivial forms; prop drilling beyond 3 levels
- Component over 200 lines; `console.log` in production code

## Automated Checks Run

```bash
npx eslint . --ext .tsx,.jsx,.ts,.js
npm run typecheck --if-present
[ -f tsconfig.json ] && tsc --noEmit -p tsconfig.json
npx eslint . --rule 'jsx-a11y/alt-text: error' --rule 'jsx-a11y/anchor-is-valid: error'
npm audit
```

If `eslint-plugin-react-hooks` or `eslint-plugin-jsx-a11y` is not configured, the review will flag the gap as a HIGH config issue and continue.

## Approval Criteria

| Status | Condition |
|---|---|
| Approve | No CRITICAL or HIGH issues |
| Warning | Only MEDIUM issues (merge with caution) |
| Block | CRITICAL or HIGH issues found |

## Integration with Other Commands

- Run `/frontend-build` first if the build is broken
- Run `/frontend-test` to ensure component tests pass
- Run `/frontend-review` before merging
- Use `/code-review` for non-frontend-specific concerns on the same PR

## Related

- Agent: `agents/frontend-reviewer.md`
- Rules: `rules/react/`, `rules/typescript/`, `rules/web/`
