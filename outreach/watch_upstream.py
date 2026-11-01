#!/usr/bin/env python3
"""Watch upstream repos for new releases.

Read-only. Compares each watched repo's latest release against
outreach/upstream_state.json and prints a machine-readable report.
Designed to run from a cron; the cron's handoff decides whether to notify
the user. NEVER posts anything upstream — drafting and posting stay
human-approved (see OUTREACH-SOP.md).

Usage: python3 watch_upstream.py [--state outreach/upstream_state.json]
Output: JSON to stdout: {"changes": [...], "checked": N}
"""
import argparse
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

WATCHED = [
    # repo, why we watch it
    ("nautechsystems/nautilus_trader", "F_LAST/batch_deltas behavior may change across releases"),
    ("polakowo/vectorbt", "verify the v1.1.2 NaN/isclose fixes stay fixed"),
    ("TwiN/gatus", "503 alerting / SQLite persistence boundaries may change"),
    ("scs0209/laya-guard", "ReDoS status still unknown; re-test if new release"),
    ("openqodex/openqodex", "fail-open design may evolve; see issue #282"),
    ("moritzwilksch/diffle", "anchoring logic may evolve; see issue #422"),
    ("drkokorev/context-diet", "dormant; note if it revives"),
]


def latest_release(repo):
    try:
        out = subprocess.run(
            ["gh", "release", "view", "--repo", repo, "--json", "tagName,name,publishedAt,url"],
            capture_output=True, text=True, timeout=30,
        )
        if out.returncode != 0:
            return {"error": (out.stderr or "unknown").strip()[:120]}
        return json.loads(out.stdout)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:120]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=os.path.join(BASE, "outreach", "upstream_state.json"))
    ap.add_argument("--update", action="store_true",
                    help="write the new state file (use after the report was reviewed)")
    args = ap.parse_args()

    try:
        with open(args.state, encoding="utf-8") as f:
            old = json.load(f)
    except FileNotFoundError:
        old = {}

    changes = []
    new_state = {}
    for repo, reason in WATCHED:
        cur = latest_release(repo)
        new_state[repo] = {"release": cur, "reason": reason}
        prev = (old.get(repo) or {}).get("release") or {}
        if cur.get("tagName") and cur.get("tagName") != prev.get("tagName"):
            changes.append({
                "repo": repo,
                "old": prev.get("tagName"),
                "new": cur.get("tagName"),
                "url": cur.get("url"),
                "published_at": cur.get("publishedAt"),
                "reason": reason,
            })

    if args.update:
        with open(args.state, "w", encoding="utf-8") as f:
            json.dump(new_state, f, indent=2, ensure_ascii=False)

    print(json.dumps({"changes": changes, "checked": len(WATCHED)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
