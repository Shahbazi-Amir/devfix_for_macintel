#!/usr/bin/env python3
import collections
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request

TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ["REPO"]
DASHBOARD_ISSUE = int(os.environ.get("DASHBOARD_ISSUE", "1"))
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() in ("1", "true", "yes")
EXPLICIT_PROTECTED = {
    int(x)
    for x in os.environ.get("PROTECTED_ARTIFACT_IDS", "").split(",")
    if x.strip()
}
API_ROOT = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "devfix-artifact-retention",
}


def request(path, method="GET", body=None):
    url = path if path.startswith("http") else API_ROOT + path
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read()
            return None if not raw else json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {detail}") from exc


def paginate(path, key):
    items = []
    page = 1
    sep = "&" if "?" in path else "?"
    while True:
        payload = request(f"{path}{sep}per_page=100&page={page}")
        batch = payload.get(key, [])
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1


def mib(value):
    return value / 1024 / 1024


def family(name):
    if name == "DevFixTunnel-0.3.0-rc3-safari-preview-macos-x86_64":
        return "tunnel-ui-safari"
    if name == "DevFixTunnel-0.3.0-rc3-ui-preview-macos-x86_64":
        return "tunnel-ui-legacy"
    match = re.fullmatch(r"DevFixTunnel-(\d+\.\d+\.\d+-rc\d+)-macos-x86_64", name)
    if match:
        return f"tunnel-package:{match.group(1)}"
    if re.fullmatch(r"DevFix-[0-9a-f]{40}", name):
        return "devfix-main-package"
    return None


RUN_CACHE = {}


def get_run(run_id):
    if run_id not in RUN_CACHE:
        RUN_CACHE[run_id] = request(f"/repos/{REPO}/actions/runs/{run_id}")
    return RUN_CACHE[run_id]


def inventory():
    return paginate(f"/repos/{REPO}/actions/artifacts?", "artifacts")


def family_stats(artifacts):
    stats = collections.defaultdict(
        lambda: {"count": 0, "bytes": 0, "oldest": None, "latest": None}
    )
    for artifact in artifacts:
        fam = family(artifact["name"]) or f"unknown:{artifact['name']}"
        current = stats[fam]
        current["count"] += 1
        current["bytes"] += artifact.get("size_in_bytes", 0)
        created = artifact.get("created_at")
        if created:
            current["oldest"] = (
                created
                if current["oldest"] is None or created < current["oldest"]
                else current["oldest"]
            )
            current["latest"] = (
                created
                if current["latest"] is None or created > current["latest"]
                else current["latest"]
            )
    return stats


def main():
    before = inventory()
    before_live = [a for a in before if not a.get("expired")]
    before_expired = [a for a in before if a.get("expired")]
    bytes_before = sum(a.get("size_in_bytes", 0) for a in before_live)

    active_runs = []
    for status in ("in_progress", "queued"):
        active_runs += paginate(
            f"/repos/{REPO}/actions/runs?status={status}", "workflow_runs"
        )
    active_run_ids = {run["id"] for run in active_runs}

    groups = collections.defaultdict(list)
    unknown = []
    for artifact in before_live:
        fam = family(artifact["name"])
        if fam is None:
            unknown.append(artifact)
        else:
            groups[fam].append(artifact)

    protected_ids = set(EXPLICIT_PROTECTED)
    protected_reason = {
        artifact_id: "explicit project evidence protection"
        for artifact_id in EXPLICIT_PROTECTED
    }

    for artifact in unknown:
        protected_ids.add(artifact["id"])
        protected_reason[artifact["id"]] = "unknown artifact family; fail-safe preserve"

    for artifact in before_live:
        if artifact["workflow_run"]["id"] in active_run_ids:
            protected_ids.add(artifact["id"])
            protected_reason[artifact["id"]] = "active or queued workflow run"

    for fam, artifacts in groups.items():
        successful = []
        for artifact in artifacts:
            run = get_run(artifact["workflow_run"]["id"])
            run_name = (run.get("name") or "").lower()
            if any(
                word in run_name
                for word in ("release", "deploy", "audit", "governance")
            ):
                protected_ids.add(artifact["id"])
                protected_reason[artifact["id"]] = (
                    f"protected workflow provenance: {run.get('name')}"
                )
            if run.get("status") == "completed" and run.get("conclusion") == "success":
                successful.append(artifact)
        if successful:
            latest = max(successful, key=lambda item: item.get("created_at") or "")
            protected_ids.add(latest["id"])
            protected_reason[latest["id"]] = f"latest successful artifact for {fam}"
        else:
            for artifact in artifacts:
                protected_ids.add(artifact["id"])
                protected_reason[artifact["id"]] = (
                    f"no verified successful survivor for {fam}"
                )

    candidates = []
    for fam, artifacts in groups.items():
        for artifact in artifacts:
            if artifact["id"] in protected_ids:
                continue
            run = get_run(artifact["workflow_run"]["id"])
            if run.get("status") != "completed":
                protected_ids.add(artifact["id"])
                protected_reason[artifact["id"]] = "run not completed; preserve"
                continue
            conclusion = run.get("conclusion") or "unknown"
            if conclusion == "success":
                reason = "superseded successful artifact; newer successful survivor preserved"
            else:
                reason = (
                    f"obsolete artifact from completed {conclusion} run; "
                    "successful survivor preserved"
                )
            candidates.append((artifact, fam, reason))

    deleted = []
    errors = []
    for artifact, fam, reason in sorted(
        candidates, key=lambda item: item[0].get("created_at") or ""
    ):
        if DRY_RUN:
            continue
        try:
            request(f"/repos/{REPO}/actions/artifacts/{artifact['id']}", method="DELETE")
            deleted.append((artifact, fam, reason))
        except Exception as exc:  # fail open per item, fail workflow after dashboard update
            errors.append((artifact, str(exc)))

    after = inventory()
    after_live = [a for a in after if not a.get("expired")]
    after_expired = [a for a in after if a.get("expired")]
    bytes_after = sum(a.get("size_in_bytes", 0) for a in after_live)
    bytes_freed = max(0, bytes_before - bytes_after)

    total_runs = request(f"/repos/{REPO}/actions/runs?per_page=1").get("total_count", 0)
    completed_runs = request(
        f"/repos/{REPO}/actions/runs?status=completed&per_page=1"
    ).get("total_count", 0)
    in_progress_runs = request(
        f"/repos/{REPO}/actions/runs?status=in_progress&per_page=1"
    ).get("total_count", 0)
    queued_runs = request(f"/repos/{REPO}/actions/runs?status=queued&per_page=1").get(
        "total_count", 0
    )
    workflows = request(f"/repos/{REPO}/actions/workflows?per_page=100")
    active_workflows = sum(
        1 for workflow in workflows.get("workflows", []) if workflow.get("state") == "active"
    )
    latest_completed = request(
        f"/repos/{REPO}/actions/runs?status=completed&per_page=5"
    ).get("workflow_runs", [])

    repo_meta = request(f"/repos/{REPO}")
    default_branch = repo_meta.get("default_branch", "unknown")
    default_ref = request(
        f"/repos/{REPO}/branches/{urllib.parse.quote(default_branch, safe='')}"
    )
    default_sha = default_ref.get("commit", {}).get("sha", "unknown")

    active_lines = []
    for run in active_runs:
        jobs = request(f"/repos/{REPO}/actions/runs/{run['id']}/jobs?per_page=100").get(
            "jobs", []
        )
        if not jobs:
            active_lines.append(
                f"- `{run.get('name')}` | `{run.get('head_branch')}` | "
                f"`{run.get('head_sha', '')[:12]}` | run `{run['id']}` | no job started"
            )
            continue
        for job in jobs:
            steps = job.get("steps") or []
            completed_steps = sum(1 for step in steps if step.get("status") == "completed")
            current_step = next(
                (step.get("name") for step in steps if step.get("status") == "in_progress"),
                "waiting",
            )
            active_lines.append(
                f"- `{run.get('name')}` | `{run.get('head_branch')}` | "
                f"`{run.get('head_sha', '')[:12]}` | run `{run['id']}` | "
                f"job `{job.get('name')}` | step `{current_step}` | "
                f"{completed_steps}/{len(steps)} steps"
            )

    stats_after = family_stats(after_live)
    family_rows = sorted(stats_after.items(), key=lambda item: item[1]["bytes"], reverse=True)

    preserved_lines = []
    for artifact in sorted(
        after_live, key=lambda item: item.get("size_in_bytes", 0), reverse=True
    ):
        reason = protected_reason.get(
            artifact["id"], "preserved after independently verified cleanup"
        )
        preserved_lines.append(
            f"- `{artifact['id']}` `{artifact['name']}` — "
            f"{artifact.get('size_in_bytes', 0)} bytes — {reason}"
        )

    deleted_lines = [
        f"- `{artifact['id']}` `{artifact['name']}` — "
        f"{artifact.get('size_in_bytes', 0)} bytes — {reason}"
        for artifact, fam, reason in deleted
    ]
    error_lines = [
        f"- `{artifact['id']}` `{artifact['name']}` — {error}"
        for artifact, error in errors
    ]

    quota_state = (
        "CLEANUP_RECOMMENDED"
        if DRY_RUN or errors or (candidates and not deleted)
        else "NORMAL"
    )
    account_quota = "UNKNOWN_ACCOUNT_CAPACITY"
    now = (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    run_id = os.environ.get("GITHUB_RUN_ID", "unknown")
    run_url = f"https://github.com/{REPO}/actions/runs/{run_id}"
    actions_url = f"https://github.com/{REPO}/actions"
    issue_url = f"https://github.com/{REPO}/issues/{DASHBOARD_ISSUE}"

    lines = [
        "# Artifact Storage Dashboard",
        "",
        f"Updated UTC: {now}",
        "",
        "## Storage",
        "",
        f"- Repository: `{REPO}`",
        f"- Default branch: `{default_branch}`",
        f"- Default branch HEAD: `{default_sha}`",
        f"- Total artifact records: **{len(after)}**",
        f"- Live artifact count: **{len(after_live)}**",
        f"- Live artifact bytes: **{bytes_after}**",
        f"- Live artifact MiB: **{mib(bytes_after):.2f} MiB**",
        f"- Expired artifacts: **{len(after_expired)}**",
        f"- Expired artifact bytes: **{sum(a.get('size_in_bytes', 0) for a in after_expired)}**",
        f"- Storage freed by last cleanup: **{bytes_freed} bytes ({mib(bytes_freed):.2f} MiB)**",
        "",
        "| Artifact family | Count | Live MiB | Oldest | Latest |",
        "|---|---:|---:|---|---|",
    ]
    if family_rows:
        for fam, stat in family_rows:
            lines.append(
                f"| `{fam}` | {stat['count']} | {mib(stat['bytes']):.2f} | "
                f"{stat['oldest'] or '—'} | {stat['latest'] or '—'} |"
            )
    else:
        lines.append("| — | 0 | 0.00 | — | — |")

    lines += [
        "",
        "## Workflow activity",
        "",
        f"- Active workflows: **{active_workflows}**",
        f"- Total workflow runs: **{total_runs}**",
        f"- In progress: **{in_progress_runs}**",
        f"- Queued: **{queued_runs}**",
        f"- Completed: **{completed_runs}**",
        "",
        "Latest completed runs:",
    ]
    for run in latest_completed:
        lines.append(
            f"- `{run.get('name')}` run `{run['id']}` — `{run.get('conclusion')}` — "
            f"`{run.get('head_branch')}` — `{run.get('head_sha', '')[:12]}`"
        )

    lines += [
        "",
        "## Current active runs",
        "",
    ]
    lines += active_lines or ["None."]
    lines += [
        "",
        "`completed steps / total steps` is Workflow execution progress only; it is not overall project completion percentage.",
        "",
        "## Cleanup",
        "",
        f"- Last cleanup date: **{now}**",
        f"- Cleanup run: [{run_id}]({run_url})",
        f"- Dry run: **{DRY_RUN}**",
        f"- Artifacts before: **{len(before_live)}**",
        f"- Bytes before: **{bytes_before} ({mib(bytes_before):.2f} MiB)**",
        f"- Artifacts deleted: **{len(deleted)}**",
        f"- Bytes freed (independently verified): **{bytes_freed} ({mib(bytes_freed):.2f} MiB)**",
        f"- Artifacts after: **{len(after_live)}**",
        f"- Bytes after: **{bytes_after} ({mib(bytes_after):.2f} MiB)**",
        f"- Cleanup errors: **{len(errors)}**",
        "",
        "### Preserved artifacts",
        "",
    ]
    lines += preserved_lines or ["- None"]
    lines += ["", "### Deleted artifacts", ""]
    lines += deleted_lines or ["- None"]
    lines += ["", "### Cleanup errors", ""]
    lines += error_lines or ["- None"]
    lines += [
        "",
        "## Quota state",
        "",
        f"- Repository-local state: **{quota_state}**",
        f"- `REPOSITORY_LIVE_ARTIFACT_STORAGE`: **{mib(bytes_after):.2f} MiB**",
        f"- `ACCOUNT_QUOTA_STATUS`: **{account_quota}**",
        "",
        "Repository-local Artifact API storage is not the same as owner/account billing quota accounting. No account capacity is guessed. If the GitHub billing UI remains quota-blocked after repository bytes fall substantially, classify it separately as `WAITING_FOR_GITHUB_RECALCULATION` until billing accounting refreshes.",
        "",
        "## Retention policy",
        "",
        "- routine `DevFix-<SHA>` package builds: keep latest successful via cleanup; recommended upload retention 14 days",
        "- Tunnel RC package builds: 14 days plus latest-successful preservation",
        "- UI previews: 14 days plus latest-successful preservation",
        "- release/deployment/audit/governance evidence: protected / project-specific",
        "- unknown artifact families: fail-safe preserve",
        "",
        "## Central dashboard integration",
        "",
        f"- Local dashboard: {issue_url}",
        f"- Actions page: {actions_url}",
        "- Cleanup workflow: `.github/workflows/actions-artifact-retention.yml`",
        f"- Latest cleanup run: {run_url}",
        "- Central dashboard: **not configured**",
        "- Cross-repository updater requirement: fine-grained PAT or GitHub App token with Actions read, Metadata read, and Issues read/write only where dashboard updates are required. No token is stored in the repository.",
        "",
        "<!-- devfix-artifact-dashboard -->",
    ]

    title = (
        f"Artifact Storage Dashboard — {mib(bytes_after):.2f} MiB live / "
        f"{len(after_live)} artifacts"
    )
    request(
        f"/repos/{REPO}/issues/{DASHBOARD_ISSUE}",
        method="PATCH",
        body={"title": title, "body": "\n".join(lines)},
    )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("# Actions Artifact Retention\n\n")
            summary.write(f"- ARTIFACTS_BEFORE: {len(before_live)}\n")
            summary.write(f"- BYTES_BEFORE: {bytes_before} ({mib(bytes_before):.2f} MiB)\n")
            summary.write(f"- ARTIFACTS_DELETED: {len(deleted)}\n")
            summary.write(f"- BYTES_FREED: {bytes_freed} ({mib(bytes_freed):.2f} MiB)\n")
            summary.write(f"- ARTIFACTS_AFTER: {len(after_live)}\n")
            summary.write(f"- BYTES_AFTER: {bytes_after} ({mib(bytes_after):.2f} MiB)\n")
            summary.write(f"- PRESERVED: {len(after_live)}\n")
            summary.write(f"- CLEANUP_ERRORS: {len(errors)}\n")
            summary.write(f"- ACCOUNT_QUOTA_STATUS: {account_quota}\n")
            summary.write(f"- Dashboard: {issue_url}\n")

    print(
        json.dumps(
            {
                "artifacts_before": len(before_live),
                "bytes_before": bytes_before,
                "artifacts_deleted": len(deleted),
                "bytes_freed": bytes_freed,
                "artifacts_after": len(after_live),
                "bytes_after": bytes_after,
                "errors": len(errors),
                "dry_run": DRY_RUN,
            },
            indent=2,
        )
    )

    if errors:
        raise SystemExit("Cleanup completed with deletion errors; dashboard contains details.")


if __name__ == "__main__":
    main()
