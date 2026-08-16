# GitHub / CI / Repository Guardrail
## Permanent Agent Constraint — Prevent `gh`, Token, Workspace, and GitHub Environment Dead-Ends

Use this guardrail before every GitHub, repository, CI, release, artifact, workflow, commit, push, PR, or GitHub Actions task in this project.

## 1. Treat execution environments as independent

Never assume these environments share tools, credentials, files, caches, or authentication:

```text
Agent Workspace
User Mac
GitHub Actions Runner
GitHub Connector / App
```

A fact about one environment proves nothing about another. Local `gh auth status` failure does not mean the GitHub Connector lacks write access; missing `gh` in an Agent Workspace does not mean GitHub Actions cannot do the task.

## 2. Default environment for repository work

For repository changes, GitHub Actions, CI, releases, artifacts, workflows and repository metadata, prefer:

```text
GitHub Connector / App
or
GitHub Actions
```

Do not send the user to the Mac for work that can be completed GitHub-native.

## 3. Local `gh` is optional, not architectural

The following are not blockers by themselves:

```text
gh is not installed
gh auth status fails
gh has no local credential
PAT is not present in Agent Workspace
User Mac is not logged into gh
```

For repository work, use this order:

```text
GitHub Connector / App
→ Repository write
→ GitHub Actions
→ GITHUB_TOKEN
→ GitHub REST API
```

Only use local `gh` when the task is genuinely local-only or the user explicitly wants a local GitHub CLI workflow.

## 4. Local `gh` authentication is separate

GitHub Connector authentication and local `gh` authentication are independent. If local `gh` needs authentication, use OAuth/device login on the User Mac and the local secure credential store. Do not extract Connector credentials and do not ask the user to paste a PAT into Chat.

If `gh` is installed directly rather than by Homebrew, do not reinstall it merely to authenticate it.

## 5. Required resolution order

### A. GitHub Connector / App
Use the Connector first for supported repository read/write operations.

### B. Repository write capability
Check actual repository permissions rather than local CLI authentication.

### C. GitHub Actions
If execution is better done inside GitHub infrastructure, create/update a workflow on the allowed branch. Respect branch constraints exactly, including `main only`, `no PR`, `no force-push`, or equivalent project rules.

### D. Controlled self-trigger
If workflow dispatch cannot be invoked from the available tool, a controlled one-time trigger is allowed:

```yaml
on:
  workflow_dispatch:
  push:
    branches:
      - main
    paths:
      - ".github/bootstrap/<task>.trigger"
```

Then commit workflow + marker, let the workflow run, verify it, remove the marker, and remove the temporary push trigger or make the workflow manual-only. Prevent loops.

### E. `GITHUB_TOKEN`
Inside GitHub Actions, prefer `GITHUB_TOKEN` with the minimum explicit permissions required, for example:

```yaml
permissions:
  contents: write
  actions: read
```

Never log the token.

### F. REST API without `gh`
`gh` is not mandatory inside a runner. GitHub REST API with `curl`, Python `urllib`, or standard-library HTTP may be used for release, asset, workflow, or metadata operations.

### G. Artifact/release fallbacks
If the Connector lacks a specific operation, move it into GitHub Actions rather than declaring the task blocked when GitHub-native alternatives remain.

## 6. Release assets

For release/asset operations: resolve or create the release, use GitHub APIs with `GITHUB_TOKEN`, record actual size and SHA-256, make the process idempotent, reuse an existing asset only when name/checksum match, fail clearly on same-name/different-content conflicts, and never expose credentials.

## 7. Large artifacts

A large file missing from Agent Workspace is not automatically a blocker. When appropriate, build/download/package/hash/upload it inside GitHub Actions. If a platform size limit is hit, record the exact error and use deterministic splitting + hashes + manifest only when suitable.

## 8. Secret policy

Never ask the user to paste these into Chat:

```text
PAT
GITHUB_TOKEN
HF_TOKEN
password
private credential
```

Never hard-code secrets or write them into logs, artifacts, manifests, workflow outputs, or repository files.

## 9. `gh` on the User Mac

For genuinely local `gh` use, check:

```bash
which gh
gh --version
gh auth status
```

If authentication is missing, use GitHub OAuth/device login. If a local network wrapper such as DevFix is needed, run the local GitHub network operation through the approved route. Local `gh` auth failure does not invalidate Connector or Actions access.

## 10. Before declaring BLOCKED

Verify and report the status of:

```text
A. GitHub Connector/App
B. Repository permission
C. Repository write
D. Workflow update capability
E. Controlled self-trigger
F. GitHub Actions
G. GITHUB_TOKEN
H. GitHub REST API
I. Release/artifact alternative
```

If a valid path remains, the task is not blocked.

## 11. Real blockers

Legitimate blockers include explicit rejection of required write permission, repository settings/branch protection that prohibit the required action with no allowed path, legal/license restrictions, hard platform limits after supported alternatives, or a genuinely unavailable required external source.

When blocked, report the failed step, exact error, HTTP status when applicable, permission involved, alternatives attempted, why each failed, and the safe next action.

## 12. Cleanup

Temporary automation infrastructure must be cleaned up after success: remove one-time marker files, temporary push triggers, and temporary workflows that are no longer useful.

## 13. Final report for GitHub tasks

Report at minimum:

```text
Repository
Branch
Final SHA
Execution environment used
Connector operations used
GitHub Actions run IDs when applicable
Whether local gh was needed
GITHUB_TOKEN permissions actually used
Temporary workflow/marker cleanup status
HEAD == origin/<branch> when relevant
Local worktree state when a local checkout was actually used
```

## Final rule

```text
Missing local `gh` is not an architectural blocker.
Local `gh` authentication and GitHub Connector authentication are independent.
As long as repository write and GitHub-native execution paths are available,
do not block a repository task because a local CLI or local credential is missing.
```
