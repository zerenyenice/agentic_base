#!/usr/bin/env bash
# First-time GitHub access setup for the agent harness.
#
# Installs the GitHub CLI (gh) if missing and authenticates it via the OAuth
# device flow. gh is the channel the devops agent (and the /pr workflow) uses
# to reach GitHub's API — CI runs, PR checks, logs. Auth is stored once per
# machine (keyring) and shared by every session and subagent.
#
# Idempotent — safe to re-run; exits 0 immediately if already set up.
# Works both for a human in a terminal and agent-driven without a TTY
# (see .claude/skills/github-setup/SKILL.md for the agent flow).
set -euo pipefail

GH_HOSTNAME="${GH_HOST:-github.com}"

log() { printf '%s\n' "$*"; }
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# --- 1. Install gh if missing ------------------------------------------------
if ! command -v gh >/dev/null 2>&1; then
  log "GitHub CLI (gh) not found — installing..."
  if command -v brew >/dev/null 2>&1; then
    brew install gh
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y gh
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y gh
  else
    fail "No supported package manager (brew/apt/dnf). Install manually: https://cli.github.com"
  fi
fi
log "gh installed: $(gh --version | head -1)"

# --- 2. Skip if already authenticated (covers GH_TOKEN env auth too) ---------
if gh auth status --hostname "$GH_HOSTNAME" >/dev/null 2>&1; then
  log "Already authenticated with $GH_HOSTNAME:"
  gh auth status --hostname "$GH_HOSTNAME"
  exit 0
fi

# --- 3. Authenticate via OAuth device flow -----------------------------------
# --git-protocol ssh: existing SSH keys stay the push mechanism (gh won't
#   switch git to HTTPS tokens).
# --skip-ssh-key: avoids the interactive key-upload picker.
if [ -t 0 ]; then
  # Human in a terminal — gh drives its own prompts.
  gh auth login --hostname "$GH_HOSTNAME" --git-protocol ssh --skip-ssh-key --web
else
  # No TTY (agent-driven): expect supplies the Enter keypress gh waits for.
  # The one-time code prints below; a human enters it in the browser at
  # https://github.com/login/device within 15 minutes.
  command -v expect >/dev/null 2>&1 \
    || fail "expect not found and no TTY — run this script from a terminal instead."
  expect -c "
    set timeout 900
    spawn gh auth login --hostname $GH_HOSTNAME --git-protocol ssh --skip-ssh-key --web
    expect \"Press Enter\"
    send \"\r\"
    expect {
      \"Authentication complete\" { catch { expect eof }; exit 0 }
      eof { exit 0 }
      timeout { puts stderr \"Timed out waiting for browser approval.\"; exit 1 }
    }"
fi

# --- 4. Verify ---------------------------------------------------------------
gh auth status --hostname "$GH_HOSTNAME"
log ""
log "GitHub access ready — devops agent can now use: gh run list / gh run view / gh pr checks"
