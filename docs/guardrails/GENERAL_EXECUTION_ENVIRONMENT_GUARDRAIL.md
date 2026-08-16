# General Execution Environment Guardrail
## Permanent Agent Constraint — Decide Where Work Should Run Before Running It

Use this guardrail before every technical task in this project. Its purpose is to prevent work from being executed in the wrong environment and to avoid needless user handoffs, local dependencies, authentication dead ends, and destructive retries.

## 1. First question: where should this task run?

Classify the task before taking action:

```text
A. Agent Workspace
B. User Mac
C. GitHub Connector / App
D. GitHub Actions Runner
E. External service / authoritative web source
```

Do not assume one environment can substitute for another.

## 2. Default routing matrix

Repository/CI/release/GitHub metadata → prefer GitHub Connector/App, then GitHub Actions if execution/build/runtime is required.

Local macOS package/binary/filesystem/Keychain/device task → User Mac.

Repository-centric reproducible build/test → GitHub Actions when a suitable runner exists.

Analysis/drafting/small file transformation → Agent Workspace unless the source exists only elsewhere.

Changing external facts/releases/documentation → authoritative current source/API.

## 3. Never infer cross-environment state

These implications are invalid:

```text
gh fails in Workspace → gh fails on User Mac
Connector is authenticated → local gh is authenticated
Homebrew works on User Mac → Actions has the same packages
file exists in GitHub → file exists in Agent Workspace
workflow artifact exists → local Mac has it
```

Verify state in the environment where the action will occur.

## 4. Prefer the environment with the fewest unnecessary dependencies

Choose the execution path that requires the fewest user actions, uses native credentials for that environment, is reproducible, is least destructive, keeps secrets out of Chat, and avoids needless local setup.

A repository release should not depend on installing `gh` on the User Mac if GitHub Actions + `GITHUB_TOKEN` can do it. A local macOS binary test should not be declared verified only because a CI runner passed.

## 5. User Mac is not a generic fallback

Do not send the user to Terminal merely because an Agent-side tool is unavailable. Use the Mac only when the task is inherently local, real Mac hardware/OS state matters, local credential/Keychain interaction is required, the user explicitly requests local execution, or no GitHub/Agent-native path can satisfy the task.

## 6. GitHub is not a generic local-Mac substitute

Do not use GitHub Actions to pretend a Mac-local condition has been verified when the task depends on the user's installed binaries, network, Homebrew prefix, Keychain, device state, or local filesystem.

## 7. Authentication rule

Authentication belongs to the environment that consumes it:

```text
GitHub Connector auth → Connector only
GITHUB_TOKEN → GitHub Actions job only
local gh OAuth → User Mac only
local Keychain credential → User Mac only
```

Never copy credentials between environments as a shortcut. Never ask the user to paste long-lived secrets into Chat.

## 8. Network rule

Do not assume every environment shares the same reachability. A destination may be reachable directly from User Mac, reachable only through DevFix/Snowflake, reachable from GitHub Actions, or reachable from Agent Workspace. Test the route that matters.

## 9. Evidence before action

Before destructive or expensive changes, determine what failed, where it failed, which environment failed, whether the cause is auth/network/compatibility/source metadata/build/permissions, and what evidence supports the classification.

## 10. Retry policy

Do not repeat an expensive step without changing the hypothesis. Each retry must answer a specific question. Avoid random retry loops.

## 11. Preserve successful layers

If a lower layer has already been proven working, do not reopen it without evidence. A later formula-specific failure should not automatically trigger a Homebrew reinstall or a DevFix release when lower layers have already passed.

## 12. Source-of-truth hierarchy

For environment state: actual command output from that environment > assumption.

For repository state: GitHub API/Connector > local guess.

For package/release versions: authoritative upstream source > stale memory.

For User Mac behavior: real User Mac test > CI approximation.

## 13. Minimal user interruption

When user action is required, give one complete command block when practical, avoid repeating commands already run, state exactly when to wait, state what success looks like, and state when not to continue. Do not force one-command-at-a-time execution unless the next step truly depends on the previous result.

## 14. Safety boundaries

Do not use convenience as a reason to disable security protections, expose credentials, force-push, erase working state, delete backups before validation, or overwrite a working binary without verification. Prefer reversible actions.

## 15. Before declaring a blocker

Tie a blocker to the correct environment and report:

```text
environment
required capability
exact failed operation
exact error
alternatives attempted
why other environments cannot satisfy the task
safe next action
```

Do not call a task blocked merely because the first chosen environment lacks a tool.

## 16. Final execution report

For meaningful technical tasks, report task, selected execution environment and why, tools/connectors used, authentication mechanism, network route when relevant, what was verified, what remains unverified, cleanup, and future maintenance implications.

## Final rule

```text
Choose the execution environment before choosing the command.
Do not move a task to the User Mac just because the Agent lacks a tool.
Do not move a local Mac problem to GitHub just because CI is convenient.
Use the environment that actually owns the state, credential, network, or runtime being tested.
```
