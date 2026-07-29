---
description: Guided feature development with codebase understanding and architecture focus
---

A structured feature-development workflow that emphasizes understanding existing code before writing new code.

## Phases

### 1. Discovery

- read the feature request carefully
- identify requirements, constraints, and acceptance criteria
- ask clarifying questions if the request is ambiguous

### 2. Codebase Exploration

- use the Explore agent (or Grep/Glob) to analyze the relevant existing code
- trace execution paths and architecture layers
- understand integration points and conventions

### 3. Clarifying Questions

- present findings from exploration
- ask targeted design and edge-case questions
- wait for user response before proceeding

### 4. Architecture Design

- the Lead designs the feature directly (no dedicated architecture agent —
  this stays with the orchestrator)
- provide the implementation blueprint
- wait for approval before implementing

### 5. Implementation

- dispatch to `backend-coder` and/or `frontend-coder` depending on what the
  feature touches; coordinate with `tester` for the red→green→refactor loop
- keep commits small and focused

### 6. Quality Review

- use `backend-reviewer` and/or `frontend-reviewer` (whichever applies) to
  review the implementation; add `security-reviewer` if a security trigger
  was touched
- address critical and important issues
- verify test coverage

### 7. Summary

- summarize what was built
- list follow-up items or limitations
- provide testing instructions
