---
applyTo: "**/*.py,**/*.pyi"
---

> Generated from `.claude/rules/python/hooks.md` by setup-harness.py — do not edit by hand.

# Python Hooks

> This file extends [common/hooks.md](../common/hooks.md) with Python specific content.

## PostToolUse Hooks

Configure in `~/.claude/settings.json`:

- **black/ruff**: Auto-format `.py` files after edit
- **mypy/pyright**: Run type checking after editing `.py` files

## Warnings

- Warn about `print()` statements in edited files (use `logging` module instead)
