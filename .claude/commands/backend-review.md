---
description: Comprehensive backend (Python/FastAPI) code review — PEP 8, type hints, security, Pythonic idioms, async correctness, dependency injection, and Pydantic schemas. Invokes the backend-reviewer agent.
---

# Backend Code Review

This command invokes the **backend-reviewer** agent for comprehensive Python/FastAPI code review.

## What This Command Does

1. **Identify Backend Changes**: Find modified `.py` files via `git diff`
2. **Run Static Analysis**: Execute `ruff`, `mypy`, `black --check`, `bandit`
3. **Security Scan**: Check for SQL injection, command injection, unsafe deserialization, secret exposure
4. **FastAPI Review**: Async correctness, dependency injection, Pydantic request/response schemas, CORS, OpenAPI docs
5. **Type Safety Review**: Analyze type hints and mypy errors
6. **Generate Report**: Categorize issues by severity

## When to Use

Use `/backend-review` when:
- After `backend-coder` writes or modifies Python/FastAPI code
- Before committing backend changes
- Reviewing pull requests with Python code
- Onboarding to a new backend codebase

## Review Categories

### CRITICAL (Must Fix)
- SQL/command injection vulnerabilities
- Unsafe `eval`/`exec`, pickle unsafe deserialization, YAML unsafe load
- Hardcoded credentials; bare `except` clauses hiding errors
- Passwords/token hashes exposed in Pydantic response models
- Auth dependencies that can be bypassed or don't validate expiry/signature

### HIGH (Should Fix)
- Missing type hints on public functions; mutable default arguments
- Swallowed exceptions; not using context managers for resources
- Blocking database/HTTP clients inside async routes
- Database sessions created inline instead of via `Depends`
- `allow_origins=["*"]` combined with credentialed CORS
- Missing request validation for write endpoints

### MEDIUM (Consider)
- PEP 8 formatting violations; missing docstrings on public functions
- Print statements instead of logging; magic numbers without named constants
- Missing pagination on list endpoints; OpenAPI docs missing response models
- Missing timeout settings for external HTTP clients

## Automated Checks Run

```bash
mypy .
ruff check .
black --check .
isort --check-only .
bandit -r .
pip-audit
pytest --cov=app --cov-report=term-missing
```

## Approval Criteria

| Status | Condition |
|--------|-----------|
| Approve | No CRITICAL or HIGH issues |
| Warning | Only MEDIUM issues (merge with caution) |
| Block | CRITICAL or HIGH issues found |

## Integration with Other Commands

- Use the `tdd-workflow` skill (via `tester`) first to ensure tests pass
- Use `/code-review` for non-backend-specific concerns on the same PR
- Use `/backend-review` before committing
- Use `/build-fix` if static analysis tools fail

## Related

- Agent: `agents/backend-reviewer.md`
- Rules: `rules/python/coding-style.md`, `rules/python/testing.md`, `rules/python/fastapi.md`
