#!/usr/bin/env python3
"""
setup-harness.py — configure this template for your editor / AI harness.

The source-of-truth files are:

    CLAUDE.md            master instructions
    .agents_base/        the 7 specialist agents (canonical, Claude-native form)
    .claude/commands/    slash commands
    .claude/rules/       coding/testing/security standards

This script GENERATES the editor-specific surfaces from them.

Surface model (verified against current editor behavior, 2026-07):

    .claude/agents/*.md            ALWAYS Claude-native frontmatter
                                   (model: sonnet; tools: Read, Write, Edit,
                                   Bash, Grep, Glob — comma-separated string).
                                   Read natively by BOTH Claude Code and
                                   VS Code Copilot (Claude sub-agent compat).
                                   Never generated with Copilot tool names —
                                   that breaks both readers.
    .github/agents/*.agent.md      Copilot custom agents for VS Code AND
                                   JetBrains (PyCharm). This replaced the
                                   legacy .github/chatmodes/ surface; JetBrains
                                   Copilot reads ONLY this location (GA since
                                   2026-03), not .claude/agents/.
    .github/copilot-instructions.md  exact copy of CLAUDE.md (all Copilot IDEs)
    AGENTS.md                      exact copy of CLAUDE.md (VS Code
                                   chat.useAgentsMdFile)
    .github/prompts/*.prompt.md    from .claude/commands/ (VS Code only)
    .github/instructions/*.instructions.md  from .claude/rules/ (VS Code only)

Targets:

    claude   -> .claude/agents only; prunes every generated Copilot surface
    vscode   -> .claude/agents + copilot-instructions + AGENTS.md +
                .github/agents + prompts + instructions
    pycharm  -> .claude/agents + copilot-instructions + .github/agents
                (JetBrains reads no AGENTS.md, prompts, or scoped instructions)
    all      -> the union (recommended when the team mixes editors)

The instruction docs are EXACT COPIES of CLAUDE.md — one set of instructions
for every editor, verifiable with a plain `diff`. Only the generated
.github/agents frontmatter (model/tool names) differs from the Claude form.

The script PRUNES generated surfaces the selected target does not read (the
legacy .github/chatmodes/ dir is always pruned). Only generated surfaces are
pruned — nothing else under .github/ is touched. CLAUDE.md, .agents_base/, and
.claude/{commands,rules,skills} are NEVER pruned or rewritten: they are the
build sources. To change an agent, edit .agents_base/<name>.md and re-run this
script — never edit .claude/agents/ or .github/agents/ directly.

Never hand-edit generated files — edit the source and re-run this script with
your target (it is idempotent), then commit sources and generated files
together.

Usage:
    python3 setup-harness.py                   # interactive
    python3 setup-harness.py --target all      # claude | vscode | pycharm | all
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

COPILOT_MODEL = "Claude Sonnet 4.5"
CLAUDE_MODEL_ALIASES = {"sonnet", "opus", "haiku", "inherit"}
CLAUDE_TOOLS = {"Read", "Write", "Edit", "Bash", "Grep", "Glob",
                "WebFetch", "WebSearch", "Task", "NotebookEdit"}

# Copilot (.github/agents/*.agent.md) tool sets, by capability tier.
# Unknown tool ids are ignored by Copilot, so this list errs on the side of
# covering both current and older id spellings.
COPILOT_READ_TOOLS = [
    "search", "codebase", "usages", "problems", "changes",
    "runCommands", "terminalLastCommand",
]
COPILOT_EDIT_TOOLS = COPILOT_READ_TOOLS + ["edit", "new", "todos"]

# applyTo globs per rules directory (fallback when a rule file has no paths:)
RULE_DIR_GLOBS = {
    "common": "**",
    "python": "**/*.py",
    "typescript": "**/*.ts,**/*.tsx,**/*.js,**/*.jsx",
    "react": "**/*.tsx,**/*.jsx",
    "web": "**/*.html,**/*.css,**/*.scss,**/*.ts,**/*.tsx,**/*.js,**/*.jsx",
    "devops": ".github/workflows/**,**/Dockerfile*,**/docker-compose*.yml,**/docker-compose*.yaml",
}

FRONT_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)


def split_frontmatter(text: str):
    m = FRONT_RE.match(text)
    if m:
        return m.group(1), text[m.end():]
    return None, text


def get_field(front: str, key: str) -> str:
    if not front:
        return ""
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", front, re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def parse_claude_tools(tools_line: str) -> list:
    """Accept both the canonical comma-separated form and a quoted list."""
    quoted = re.findall(r"['\"]([^'\"]+)['\"]", tools_line)
    if quoted:
        return quoted
    return [t.strip() for t in tools_line.strip("[]").split(",") if t.strip()]


def fmt_tools(tools) -> str:
    return "[" + ", ".join(f"'{t}'" for t in tools) + "]"


def write(path: Path, content: str, written: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    written.append(str(path.relative_to(ROOT)))


# ------------------------------------------------------------ instruction docs

def generate_instruction_docs(target: str, written: list):
    """Exact copies of CLAUDE.md — one set of instructions for every editor,
    verifiable with a plain `diff CLAUDE.md .github/copilot-instructions.md`."""
    claude_md = ROOT / "CLAUDE.md"
    if not claude_md.exists():
        sys.exit("ERROR: CLAUDE.md not found — it is the master instructions file.")
    content = claude_md.read_text(encoding="utf-8")
    write(ROOT / ".github" / "copilot-instructions.md", content, written)
    if target in ("vscode", "all"):  # VS Code reads AGENTS.md; PyCharm doesn't
        write(ROOT / "AGENTS.md", content, written)


# --------------------------------------------------------------------- agents

BASE_AGENTS = ROOT / ".agents_base"


def base_agent_files():
    if not BASE_AGENTS.is_dir():
        sys.exit("ERROR: .agents_base/ not found — it holds the canonical "
                 "agent definitions that all agent surfaces are generated from.")
    return sorted(BASE_AGENTS.glob("*.md"))


def copilot_tools_for(front: str) -> list:
    claude_tools = parse_claude_tools(get_field(front, "tools"))
    can_edit = "Edit" in claude_tools or "Write" in claude_tools
    return COPILOT_EDIT_TOOLS if can_edit else COPILOT_READ_TOOLS


def generate_claude_agents(written: list):
    """.claude/agents/ in Claude-native form — a verbatim copy of the base.
    This one form is read by both Claude Code and VS Code Copilot."""
    for src in base_agent_files():
        write(ROOT / ".claude" / "agents" / src.name,
              src.read_text(encoding="utf-8"), written)


def generate_github_agents(written: list):
    """.github/agents/*.agent.md — Copilot custom agents for VS Code and
    JetBrains IDEs (the surface that replaced legacy chatmodes)."""
    for src in base_agent_files():
        front, body = split_frontmatter(src.read_text(encoding="utf-8"))
        name = get_field(front, "name") or src.stem
        desc = get_field(front, "description")
        model = get_field(front, "model")
        lines = [
            "---",
            f"name: {name}",
            f"description: {desc}",
            f"tools: {fmt_tools(copilot_tools_for(front))}",
        ]
        if model != "inherit":
            lines.append(f"model: {COPILOT_MODEL}")
        lines += [
            "---",
            "",
            f"> Generated from `.agents_base/{src.name}` by setup-harness.py "
            "— do not edit by hand.",
            body,
        ]
        write(ROOT / ".github" / "agents" / f"{src.stem}.agent.md",
              "\n".join(lines), written)


# -------------------------------------------------------------------- prompts

def generate_prompts(written: list):
    commands_dir = ROOT / ".claude" / "commands"
    for src in sorted(commands_dir.glob("*.md")):
        front, body = split_frontmatter(src.read_text(encoding="utf-8"))
        desc = get_field(front, "description")
        body = body.replace("$ARGUMENTS", "the user input provided after the prompt name")
        out = (
            "---\n"
            "mode: agent\n"
            f"description: {desc}\n"
            "---\n\n"
            f"> Generated from `.claude/commands/{src.name}` by setup-harness.py — do not edit by hand.\n"
            f"{body}"
        )
        write(ROOT / ".github" / "prompts" / f"{src.stem}.prompt.md", out, written)


# --------------------------------------------------------------- instructions

def generate_instructions(written: list):
    rules_dir = ROOT / ".claude" / "rules"
    for sub, default_glob in RULE_DIR_GLOBS.items():
        subdir = rules_dir / sub
        if not subdir.is_dir():
            continue
        for src in sorted(subdir.glob("*.md")):
            if src.name.upper() == "README.MD":
                continue
            front, body = split_frontmatter(src.read_text(encoding="utf-8"))
            globs = re.findall(r'-\s*"([^"]+)"', front) if front else []
            apply_to = ",".join(globs) if globs else default_glob
            out = (
                "---\n"
                f'applyTo: "{apply_to}"\n'
                "---\n\n"
                f"> Generated from `.claude/rules/{sub}/{src.name}` by setup-harness.py — do not edit by hand.\n\n"
                f"{body}"
            )
            write(ROOT / ".github" / "instructions" / f"{sub}-{src.stem}.instructions.md",
                  out, written)


# ---------------------------------------------------------------------- prune

# Every file/dir this script can generate. Pruning never touches anything else
# under .github/ (CI workflows etc. are safe).
LEGACY_SURFACES = [".github/chatmodes"]  # pre-.agent.md format; always pruned
VSCODE_ONLY_SURFACES = LEGACY_SURFACES + [
    ".github/prompts", ".github/instructions", "AGENTS.md",
]
ALL_GENERATED_SURFACES = VSCODE_ONLY_SURFACES + [
    ".github/agents", ".github/copilot-instructions.md",
]

PRUNE_BY_TARGET = {
    "claude": ALL_GENERATED_SURFACES,
    "vscode": LEGACY_SURFACES,
    "pycharm": VSCODE_ONLY_SURFACES,
    "all": LEGACY_SURFACES,
}


def prune(paths: list, removed: list):
    for rel in paths:
        p = ROOT / rel
        if p.is_dir():
            shutil.rmtree(p)
            removed.append(rel + "/")
        elif p.exists():
            p.unlink()
            removed.append(rel)


# ----------------------------------------------------------- claude validation

def validate_claude_agents() -> bool:
    ok = True
    agents_dir = ROOT / ".claude" / "agents"
    for src in sorted(agents_dir.glob("*.md")):
        front, _ = split_frontmatter(src.read_text(encoding="utf-8"))
        model = get_field(front, "model")
        tools_line = get_field(front, "tools")
        problems = []
        if not (model in CLAUDE_MODEL_ALIASES or model.startswith("claude-")):
            problems.append(f"model '{model}' is not a claude CLI alias "
                            f"({'/'.join(sorted(CLAUDE_MODEL_ALIASES))}) or claude-* id")
        if "[" in tools_line or "'" in tools_line or '"' in tools_line:
            problems.append("tools must be a comma-separated string "
                            "(Read, Grep, ...) — lists/quotes break VS Code's "
                            "Claude sub-agent parser")
        for tool in parse_claude_tools(tools_line):
            if tool not in CLAUDE_TOOLS:
                problems.append(f"tool '{tool}' is not a claude CLI tool name")
        if problems:
            ok = False
            print(f"  FAIL {src.relative_to(ROOT)}")
            for p in problems:
                print(f"       - {p}")
        else:
            print(f"  OK   {src.relative_to(ROOT)}")
    return ok


def check_github_access():
    """Non-fatal first-time check: the devops agent, /pr workflow, and
    Research-phase `gh search` all need an authenticated GitHub CLI.
    One-time per machine — see .claude/skills/github-setup/SKILL.md."""
    if shutil.which("gh") is None:
        print("\nGitHub access: gh CLI NOT installed — required by the devops "
              "agent and the /pr workflow.\n"
              "  One-time setup: bash .claude/scripts/setup-gh.sh")
        return
    status = subprocess.run(["gh", "auth", "status"],
                            capture_output=True, text=True)
    if status.returncode != 0:
        print("\nGitHub access: gh is installed but NOT authenticated.\n"
              "  One-time setup: bash .claude/scripts/setup-gh.sh")
    else:
        print("\nGitHub access: gh authenticated — devops agent and /pr ready.")


# ----------------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--target", choices=["claude", "vscode", "pycharm", "all"])
    target = parser.parse_args().target

    if not target:
        print("Which editor is your team using?\n"
              "  1) claude   — Claude Code CLI only\n"
              "  2) vscode   — GitHub Copilot in VS Code (+ Claude Code)\n"
              "  3) pycharm  — GitHub Copilot in PyCharm/JetBrains (+ Claude Code)\n"
              "  4) all      — mixed team: every surface (recommended)")
        choice = input("Select [1-4]: ").strip()
        target = {"1": "claude", "2": "vscode", "3": "pycharm", "4": "all"}.get(choice)
        if not target:
            sys.exit("Invalid selection.")

    written: list = []
    removed: list = []

    # .claude/agents is ALWAYS Claude-native — every target regenerates it
    # from .agents_base so a stale Copilot-frontmatter copy can't linger.
    generate_claude_agents(written)

    if target in ("vscode", "pycharm", "all"):
        generate_instruction_docs(target, written)
        generate_github_agents(written)
    if target in ("vscode", "all"):
        generate_prompts(written)
        generate_instructions(written)

    prune(PRUNE_BY_TARGET[target], removed)

    if written:
        print(f"Generated/updated {len(written)} file(s):")
        for path in written:
            print(f"  {path}")
    if removed:
        print(f"Removed {len(removed)} generated surface(s) not read by "
              f"'{target}':")
        for path in removed:
            print(f"  {path}")

    print("Validating .claude/agents (read by Claude Code AND VS Code Copilot):")
    if not validate_claude_agents():
        sys.exit(1)

    if target in ("vscode", "all"):
        print("\nVS Code notes:\n"
              "  - Custom agents appear in the Copilot Chat agents dropdown\n"
              "    (from .github/agents/ and .claude/agents/; use 'Configure\n"
              "    Custom Agents' in the dropdown to check detection).\n"
              "  - Prompts are invoked as /name in Copilot Chat.\n"
              "  - If prompt/instruction files don't load, enable the\n"
              "    'chat.promptFiles' and instruction-files settings.")
    if target in ("pycharm", "all"):
        print("\nPyCharm/JetBrains notes:\n"
              "  - Copilot custom agents load from .github/agents/*.agent.md\n"
              "    (agents dropdown in Copilot Chat; GA since 2026-03).\n"
              "  - Instructions load from .github/copilot-instructions.md.")

    check_github_access()

    print("\nDone. Re-run this script with the same target after editing "
          "CLAUDE.md, .agents_base/, or .claude/{commands,rules}; commit "
          "sources and generated files together. Never edit .claude/agents/ "
          "or .github/agents/ directly — edit .agents_base/ instead.")


if __name__ == "__main__":
    main()
