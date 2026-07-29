---
name: github-setup
description: One-time GitHub access setup for the agent harness — install the gh CLI and authenticate it via the OAuth device flow (browser approval). Use on first use of the template on a new machine, when gh is missing or unauthenticated, when the devops agent can't reach GitHub (CI runs, PR checks), or before /pr can push and open pull requests.
---

# GitHub Access Setup (first-time, per machine)

The devops agent, the `/pr` workflow, and Research-phase `gh search` all talk
to GitHub's API through the **`gh` CLI**. Its auth is machine-level: one
device-flow login, stored in the OS keyring, shared by every session and
every subagent. No per-agent configuration exists — if `gh auth status`
passes, every agent has access.

**Everything below is wrapped in one idempotent script:**

```bash
bash .claude/scripts/setup-gh.sh
```

It installs `gh` if missing (brew/apt/dnf), skips cleanly if already
authenticated, and otherwise starts the OAuth device flow. Re-running it is
always safe.

## Flow A — human at a terminal

Run the script in a terminal. `gh` prints a one-time code, opens
`https://github.com/login/device`, you paste the code and approve. Done.

## Flow B — agent-driven (no TTY)

When an agent runs the setup, `gh`'s interactive prompt needs a pseudo-TTY.
The script handles this with `expect` automatically, but the agent must
orchestrate around it:

1. Run the script **in the background** (it blocks up to 15 minutes waiting
   for browser approval):
   ```
   Bash(command: "bash .claude/scripts/setup-gh.sh", run_in_background: true)
   ```
2. After a few seconds, **read the task output file** and extract the
   one-time code line: `! First copy your one-time code: XXXX-XXXX`.
3. **Surface the code to the user immediately** and tell them to enter it at
   https://github.com/login/device (the script also tries to open the
   browser). End the turn — the approval is theirs to give.
4. When the background task completes, **verify** with `gh auth status`, then
   continue the original task (e.g. create the PR, dispatch devops).

Known pitfalls (learned the hard way — don't rediscover them):

- **Don't pipe a newline via `printf '\n' | script -q ...`** — the keypress
  is consumed before the prompt appears and `gh` hangs forever. `expect` is
  the reliable mechanism; the script already uses it.
- **Each restart mints a new device code** — a code shown from a killed
  attempt is dead; always surface the code from the *current* run.
- Without `--skip-ssh-key`, `gh` blocks on an interactive SSH-key-upload
  picker that no piped input reaches.

## Variants

- **Headless / CI / containers** (no browser at all): skip the login and set
  a fine-grained PAT as an env var — `gh` picks it up automatically:
  ```bash
  export GH_TOKEN=<fine-grained-PAT>   # repo read + actions read is enough for diagnosis
  ```
- **GitHub Enterprise**: `export GH_HOST=github.yourcompany.com` before
  running the script (it honors `GH_HOST`).

## Verification

```bash
gh auth status            # logged in, scopes listed (repo, read:org)
gh run list --limit 5     # devops agent smoke test (empty until CI exists — that's fine)
gh pr list                # PR workflow smoke test
```

Scopes note: the web login grants `repo` + `read:org` — enough for everything
the agents do. Pushing `.github/workflows/` changes needs the extra
`workflow` scope only over HTTPS; teams pushing over SSH (the default here)
are unaffected.

## Related, but separate

The **`github` MCP server** in `.mcp.json` authenticates independently
(one-time OAuth via `/mcp` inside Claude Code). Setting up `gh` does not set
up the MCP server, or vice versa — `gh` is the one the devops agent requires.

## Related

- Script: `.claude/scripts/setup-gh.sh` (the wrapper — keep fixes there, not in ad-hoc commands)
- Skills: `ci-triage`, `github-actions` (both assume this setup is done)
- Rules: `rules/devops/ci-cd.md` (names `gh` as the CI interaction channel)
