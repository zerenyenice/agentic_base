# DevOps Integration Guide — Azure DevOps, Containers, Helm, Releases

How to run your DevOps processes through this agent system: Azure DevOps
(Repos, Boards, Pipelines), Docker/Compose, Helm charts, image versioning, and
releases. This extends — never replaces — the git protocol in
`../.claude/rules/common/git-workflow.md`; everything below maps onto the same
gates, trailers, and choreography.

> **Audience:** project teams adopting this template inside the company.
> **Status:** company convention. If your project deviates (different branch
> model, different registry), record the deviation in `../PROJECT.md` §
> technical constraints so agents pick it up.

---

## 1. The division of labor stays the same

The agent model does not change for DevOps work:

| Concern | Who handles it |
|---|---|
| Planning a deploy/infra change, deciding versioning | **Lead** (main agent) |
| Dockerfile / compose / Helm edits tied to app code | **backend-coder** / **frontend-coder** (same task branch as the code) |
| Standalone infra edits (chart values, compose services, pipeline YAML) | **Lead** directly for small edits; dispatch a coder agent when substantial |
| Reviewing base images, exposed ports, secrets in values, pipeline permissions | **security-reviewer** (mandatory — see §6) |
| Running lint/template/build verification for infra changes | **tester** (it runs commands, not just unit tests) or the Lead |
| All git writes, pushes, PR creation, tags | **Lead only** — unchanged |

Subagents remain git-read-only. The Lead remains the single committer and is
also the single PR-creator and tag-creator.

## 2. Azure DevOps setup (one-time per project)

The template's `/pr` command targets GitHub (`gh`). For Azure DevOps, the Lead
uses the `az` CLI instead:

```bash
# prerequisites (each engineer's machine / agent environment)
az extension add --name azure-devops
az devops configure --defaults \
  organization=https://dev.azure.com/<your-org> \
  project=<your-project>
az login   # or: export AZURE_DEVOPS_EXT_PAT=<pat with Code read/write>
```

Point the repo at Azure Repos and set the integration branch:

```bash
git remote add origin https://dev.azure.com/<org>/<project>/_git/<repo>
git push -u origin dev        # dev is the integration branch (see §3)
```

Recommended **branch policies on `dev`** (set once in ADO → Repos → Branches):

- Minimum 1 reviewer (a human — the agent reviewers are advisory input, not a
  substitute for the human gate on shared branches)
- Build validation: the CI pipeline must pass
- "Check for linked work items" — pairs with the `Refs:` trailer (§4)
- Merge strategy: **merge (no fast-forward)** preferred — it preserves the
  task branch's internal commit story (plan → RED → GREEN → review fixes),
  which is the protocol's audit trail. If your org standardizes on squash,
  that is an accepted deviation: the story remains verifiable in the PR's
  branch history, so keep task branches on the remote until the PR is closed.

## 3. Branch model: `dev` as the base branch

The git protocol says the base branch is *whatever is checked out when a task
is accepted*. For teams on Azure DevOps the standing convention is:

```
main   ← production releases only (PR from dev; tagged)
dev    ← integration branch; ALL task branches fork from and return to dev
  ├── feat/user-registration
  ├── fix/empty-poller-crash
  └── chore/helm-hpa-tuning
```

Practically: **keep `dev` checked out** in the working tree between tasks.
Task branches then automatically fork from `dev` at Gate 1 and target `dev`
at Gate 2 — no configuration needed, the protocol's "current branch = base
branch" rule does the right thing.

## 4. Gate 2 with a protected remote: PR instead of local merge

The protocol defines Gate 2 as the **merge/push gate**. With ADO branch
policies on `dev`, the local `--no-ff` merge is replaced by a pushed branch +
PR — this is the anticipated deviation in `git-workflow.md`:

**Choreography (per task):**

1. Task branch completes its internal choreography as usual (plan commit →
   RED → GREEN → review-fix commits, all with `Agent:`/`Task:` trailers).
2. **GATE 2** — the Lead presents: diff summary, commit list, tester's
   measured coverage (or infra verification evidence, §7), and reviewer
   verdicts. The user confirms.
3. On approval the Lead pushes and opens the PR:

   ```bash
   git push -u origin feat/user-registration
   az repos pr create \
     --source-branch feat/user-registration \
     --target-branch dev \
     --title "feat: add user registration endpoint" \
     --description "$(cat <<'EOF'
   ## Summary
   <what and why>

   Task: user-registration
   Reviewed-by: backend-reviewer
   Reviewed-by: security-reviewer
   Coverage: 87%
   Refs: #123
   EOF
   )" \
     --work-items 123
   ```

   The `Reviewed-by:`/`Coverage:` trailers that would have gone on the local
   merge commit go in the **PR description** instead (and on the merge commit
   too, if ADO's merge-commit message is editable in your policy).
4. The PR merges in ADO once policies pass (human reviewer + build
   validation). Optionally: `az repos pr update --id <id> --auto-complete true`
   with user approval — auto-complete counts as the merge decision, so it sits
   *behind* Gate 2, never before.
5. After the PR completes: `git checkout dev && git pull`, run the suite once
   on the merged result (post-merge verification rule), then delete the local
   task branch (`git branch -d …`) and the remote one if policy allows.

**Work-item traceability:** the commit trailer `Refs: #123` (Azure Boards
work-item ID) plus `--work-items 123` on the PR closes the Boards↔git loop —
the same role Jira keys play in `/jira`. If your team uses Jira with ADO
Repos, keep the Jira key in `Refs:` and link manually.

**Do the same for `dev → main` promotion:** a release PR from `dev` to `main`
is itself a Gate 2 event — the Lead opens it only with user approval, and it
carries the release summary (§8).

## 5. Docker, Compose, and Helm changes

Infrastructure-as-code **is code** — it goes through the same pipeline:
task branch, choreography commits, review, Gate 2. What differs is the commit
type, the verification commands, and the mandatory security review.

### Commit conventions

| Artifact | Change | Commit type |
|---|---|---|
| `Dockerfile` | behavior/runtime change (new dep, base image bump) | `feat(docker):` / `fix(docker):` |
| `docker-compose*.yml` | service added/changed | `feat(compose):` / `fix(compose):` |
| Helm chart templates | new resource, probe, HPA, ingress rule | `feat(helm):` / `fix(helm):` |
| Helm `values*.yaml` | environment tuning (replicas, resources) | `chore(deploy):` |
| `azure-pipelines.yml` / `.azuredevops/` | pipeline change | `ci:` |
| Chart/app version bumps for a release | | `chore(release):` |

Trailers apply exactly as for app code: `Agent:` (whoever produced it — often
`lead`), `Task:`, `Refs:`.

### Verification = the "tests" of infra changes

There is no unit-test RED/GREEN for YAML, so the choreography adapts (same
spirit as the refactor lifecycle B6 — evidence first, then change):

1. **Baseline** — before editing, capture that current state is valid:
   `helm lint` + `helm template` render clean, `docker compose config -q`
   passes. Note it in the plan commit.
2. **Change** — one logical change per commit.
3. **Verify after each commit** — run the relevant commands and paste results
   into the Gate 2 summary:

   ```bash
   # Docker
   hadolint Dockerfile                      # Dockerfile lint
   docker build -t <app>:check .            # it must build
   trivy image <app>:check                  # vulnerability scan (or ADO Defender)

   # Compose
   docker compose config -q                 # syntax + interpolation check
   docker compose up -d && <smoke check> && docker compose down

   # Helm
   helm lint charts/<app>
   helm template charts/<app> -f values-dev.yaml | kubeconform -strict -
   helm diff upgrade <release> charts/<app> -f values-dev.yaml   # if plugin available
   ```

4. **E2E where it matters** — for compose changes the `tester` agent can run
   the stack and execute the existing E2E suite against it; that is the
   strongest green signal an infra change can produce.

### Environment values

- One chart, per-environment values files (`values-dev.yaml`,
  `values-staging.yaml`, `values-prod.yaml`) — all committed, all
  placeholder-safe (no secrets, see §6).
- `values-prod.yaml` changes are always at least **standard** tier (never
  trivial): they get a plan, a review, and an explicit Gate 2 — a wrong
  resource limit in prod is an outage, not a tweak.

## 6. Security review is mandatory for infra diffs

Add these to the security triggers your team already uses (auth, input
handling, DB, crypto, secrets). Dispatch `security-reviewer` whenever a diff
touches:

- `Dockerfile` — base image provenance/pinning, `USER` (no root),
  no secrets in layers or build args, minimal exposed ports
- `docker-compose*.yml` — no plaintext credentials in `environment:`, no
  unneeded host mounts, no `privileged: true`
- Helm templates/values — no secrets in `values*.yaml` (use Azure Key Vault +
  CSI driver or ADO variable groups), `securityContext` set, no wildcard RBAC
- `azure-pipelines.yml` — no inline secrets, restricted service-connection
  scopes, no `system.accessToken` leakage into scripts

Secrets policy is unchanged from the protocol: `.env` gitignored,
`.env.example` with placeholders committed, staged-diff secret scan before
every commit, incident protocol (rotate first) if one ever lands in history.
**Helm values and pipeline YAML are in scope of that pre-commit scan.**

## 7. The coverage gate for infra-only tasks

The 80% coverage gate applies to **application code**. An infra-only task
(chart tuning, compose change, pipeline edit) has no meaningful coverage
number — so at Gate 2 the Lead presents, instead:

- the verification evidence from §5 (lint/template/build/scan outputs), and
- confirmation that the *existing* app test suite still passes where the
  change could affect runtime behavior (e.g. compose changes → run the suite
  against the stack).

State explicitly in the Gate 2 summary: *"infra-only change — coverage gate
replaced by verification evidence."* Mixed tasks (code + chart in one task)
still owe the coverage number for the code part.

## 8. Versioning and releases

The protocol's B12 stays lightweight: tags are Lead-created, annotated, and
made only when the user declares a release. The company convention on top:

**One version string, three places, one commit:**

| Place | Example |
|---|---|
| Git tag (annotated, on `main` after the release PR merges) | `v1.4.0` |
| Container image tag (built by the pipeline **from the git tag**) | `<acr>.azurecr.io/<app>:1.4.0` |
| Helm chart `appVersion` (+ chart `version` bump) | `appVersion: 1.4.0` |

**Release choreography:**

1. User declares the release → Lead opens a task branch
   `chore/release-1.4.0` off `dev`.
2. Single `chore(release): 1.4.0` commit: bump `Chart.yaml` `version`
   and `appVersion`, changelog update if the project keeps one.
3. Gate 2 → PR `chore/release-1.4.0 → dev` → then release PR `dev → main`
   (each PR is its own user approval).
4. After the `main` merge, the Lead tags: `git tag -a v1.4.0 -m "<summary of
   what shipped, from the task-level git history>" && git push origin v1.4.0`.
5. The **pipeline** — not an agent — builds and pushes the image on the tag
   trigger and deploys the chart. Agents never run `docker push`, `helm
   upgrade` against clusters, or `az pipelines run` for deployment stages
   without explicit user direction; deployment execution belongs to Azure
   Pipelines with its approvals and service connections.

Image tags in values files: `values-dev.yaml` may float (`dev-latest` or the
short SHA the pipeline stamps); `values-prod.yaml` pins the released version
and only changes via the release choreography above. `latest` is never
deployed to prod.

**Hotfixes:** branch `fix/<slug>` from `main`, same choreography (regression
test first), PR back to `main`, tag `v1.4.1`, then merge `main` back into
`dev` so the fix isn't lost — the Lead proposes that back-merge as part of
the hotfix task, not as an afterthought.

## 9. What agents never do (DevOps edition)

Extending the protocol's forbidden list:

- No `docker push` to shared registries, no `helm upgrade`/`kubectl apply`
  against shared clusters, no `az pipelines run` on deploy stages — pipelines
  deploy; agents prepare and verify. (Local `docker build`/`compose up` for
  verification is fine.)
- No editing ADO branch policies, service connections, variable groups, or
  pipeline permissions — humans own the control plane.
- No PR creation, auto-complete, or tagging before Gate 2 approval.
- No secrets in any committed file — including Helm values, compose
  `environment:` blocks, and pipeline YAML.

## 10. Adopting this in your project

1. Fill `../PROJECT.md` § technical/security constraints with your specifics:
   ACR name, cluster names, environments, who approves prod deploys.
2. Set up the ADO remote + branch policies (§2) and create `dev`.
3. Tell the Lead your conventions once per repo — or better, record them in
   `../PROJECT.md` — e.g. *"base branch is dev; Gate 2 = push + PR per
   DEVOPS.md §4."* Agents read this file; it is part of the template.
4. Optional hardening as your usage grows (not shipped by default, keep to
   the one-agent-one-job principle):
   - a `devops-coder` agent (edit access scoped to `Dockerfile*`,
     `docker-compose*`, `charts/**`, `azure-pipelines.yml`) if infra work
     volume justifies it,
   - an `/ado-pr` command mirroring `/pr` with `az repos pr create`,
   - a pipeline step that validates commit trailers (`Agent:`/`Task:`) so the
     audit trail is machine-enforced server-side.
