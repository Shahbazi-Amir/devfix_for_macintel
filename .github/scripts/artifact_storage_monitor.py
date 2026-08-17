#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
import urllib.error
import urllib.request

TOKEN = os.environ["GH_TOKEN"]
REPO = os.environ["REPO"]
DASHBOARD_ISSUE = int(os.environ.get("DASHBOARD_ISSUE", "1"))
API_ROOT = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "devfix-artifact-storage-monitor",
}
START = "<!-- artifact-storage-monitor:start -->"
END = "<!-- artifact-storage-monitor:end -->"


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


def pct(value, total):
    return 0.0 if total <= 0 else (value / total) * 100.0


def bar(percent, width=20):
    clamped = max(0.0, min(100.0, percent))
    filled = int(round(clamped / 100.0 * width))
    return "█" * filled + "░" * (width - filled)


def load_governance():
    path = os.path.join(os.environ.get("GITHUB_WORKSPACE", "."), ".github", "artifact-governance.json")
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main():
    governance = load_governance()
    metrics = governance.get("storage_metrics", {})
    major_cleanup = governance.get("major_cleanup", {})

    artifacts = paginate(f"/repos/{REPO}/actions/artifacts?", "artifacts")
    live = [artifact for artifact in artifacts if not artifact.get("expired")]
    live_bytes = sum(artifact.get("size_in_bytes", 0) for artifact in live)
    expired = [artifact for artifact in artifacts if artifact.get("expired")]

    baseline_bytes = int(metrics.get("baseline_live_bytes") or live_bytes)
    baseline_count = int(metrics.get("baseline_artifact_count") or len(live))
    reclaimed_bytes = max(0, baseline_bytes - live_bytes)
    used_vs_baseline = pct(live_bytes, baseline_bytes)
    reclaimed_vs_baseline = pct(reclaimed_bytes, baseline_bytes)

    account_capacity_bytes = metrics.get("account_capacity_bytes")
    account_capacity_status = metrics.get("account_capacity_status", "UNKNOWN_ACCOUNT_CAPACITY")
    account_capacity_reason = metrics.get("account_capacity_reason", "Not available")
    if isinstance(account_capacity_bytes, int) and account_capacity_bytes > 0:
        account_used_pct = pct(live_bytes, account_capacity_bytes)
        account_free_bytes = max(0, account_capacity_bytes - live_bytes)
        account_capacity_line = f"**{mib(account_capacity_bytes):.2f} MiB**"
        account_free_line = f"**{mib(account_free_bytes):.2f} MiB**"
        account_used_line = f"**{account_used_pct:.2f}%**"
    else:
        account_capacity_line = "**UNKNOWN**"
        account_free_line = "**UNKNOWN**"
        account_used_line = "**UNKNOWN**"

    in_progress = request(f"/repos/{REPO}/actions/runs?status=in_progress&per_page=1").get("total_count", 0)
    queued = request(f"/repos/{REPO}/actions/runs?status=queued&per_page=1").get("total_count", 0)
    total_runs = request(f"/repos/{REPO}/actions/runs?per_page=1").get("total_count", 0)

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    monitor = "\n".join([
        START,
        "## Storage Monitor",
        "",
        f"Updated UTC: **{now}**",
        "",
        f"- Current repository Artifact storage: **{mib(live_bytes):.2f} MiB** ({live_bytes:,} bytes)",
        f"- Live artifacts: **{len(live)}**",
        f"- Expired artifacts still listed: **{len(expired)}**",
        f"- Pre-cleanup high-water mark: **{mib(baseline_bytes):.2f} MiB / {baseline_count} artifacts**",
        f"- Reclaimed since high-water mark: **{mib(reclaimed_bytes):.2f} MiB ({reclaimed_vs_baseline:.2f}%)**",
        f"- Current usage vs pre-cleanup high-water mark: **{used_vs_baseline:.2f}%**",
        f"- Relative meter: `{bar(used_vs_baseline)}` **{used_vs_baseline:.2f}% used / {reclaimed_vs_baseline:.2f}% reclaimed**",
        "",
        "### Account capacity",
        "",
        f"- GitHub Actions account capacity: {account_capacity_line}",
        f"- Account free capacity: {account_free_line}",
        f"- Account used percentage from this repository metric: {account_used_line}",
        f"- Capacity status: **{account_capacity_status}**",
        f"- Reason: {account_capacity_reason}",
        "",
        "The repository Artifact API gives exact repository-local bytes, but it does not expose the owner's total billing quota to this GitHub App. `UNKNOWN` is intentional; no quota number is guessed.",
        "",
        "### Workflow monitor",
        "",
        f"- Total workflow runs: **{total_runs}**",
        f"- In progress: **{in_progress}**",
        f"- Queued: **{queued}**",
        "",
        "### Major cleanup evidence",
        "",
        f"- Cleanup run: `{major_cleanup.get('run_id', 'unknown')}`",
        f"- Artifacts deleted: **{major_cleanup.get('artifacts_deleted', 'unknown')}**",
        f"- Bytes freed: **{mib(int(major_cleanup.get('bytes_freed', 0))):.2f} MiB**",
        f"- Errors: **{major_cleanup.get('errors', 'unknown')}**",
        END,
    ])

    issue = request(f"/repos/{REPO}/issues/{DASHBOARD_ISSUE}")
    body = issue.get("body") or ""
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pattern.search(body):
        new_body = pattern.sub(monitor, body)
    else:
        lines = body.splitlines()
        insert_at = 1 if lines and lines[0].startswith("#") else 0
        lines[insert_at:insert_at] = ["", monitor, ""]
        new_body = "\n".join(lines)

    title = f"Artifact Storage Dashboard — {mib(live_bytes):.2f} MiB / {len(live)} live artifacts"
    request(
        f"/repos/{REPO}/issues/{DASHBOARD_ISSUE}",
        method="PATCH",
        body={"title": title, "body": new_body},
    )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("\n" + monitor.replace(START, "").replace(END, "") + "\n")

    print(json.dumps({
        "live_artifacts": len(live),
        "live_bytes": live_bytes,
        "live_mib": round(mib(live_bytes), 2),
        "baseline_mib": round(mib(baseline_bytes), 2),
        "reclaimed_mib": round(mib(reclaimed_bytes), 2),
        "used_vs_baseline_percent": round(used_vs_baseline, 2),
        "reclaimed_vs_baseline_percent": round(reclaimed_vs_baseline, 2),
        "account_capacity_status": account_capacity_status,
        "in_progress_runs": in_progress,
        "queued_runs": queued,
    }, indent=2))


if __name__ == "__main__":
    main()
