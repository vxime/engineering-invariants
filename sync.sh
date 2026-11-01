#!/usr/bin/env bash
# Sync engineering-invariants with the canonical vxi.me invariants index.
# - Downloads the latest index.json
# - Downloads every evidence/*.json the index references (only those that exist upstream)
# - Regenerates README.md
# Safe to run repeatedly; commits only when something changed.
set -euo pipefail
cd "$(dirname "$0")"

echo "== fetch index =="
curl -fsSL --max-time 30 "https://vxi.me/invariants/index.json" -o /tmp/ei-index.json

echo "== fetch evidence =="
mkdir -p evidence
python3 - <<'EOF'
import json, urllib.request, os
d = json.load(open('/tmp/ei-index.json'))
for c in d['cases']:
    u = c.get('evidence_url')
    if not u:
        continue
    name = u.rsplit('/', 1)[-1]
    dest = os.path.join('evidence', name)
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'engineering-invariants-sync/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        open(dest, 'wb').write(data)
        print(f"OK {name} ({len(data)} bytes)")
    except Exception as e:
        print(f"SKIP {name}: {e}")
EOF

echo "== regenerate README =="
python3 generate_readme.py --index /tmp/ei-index.json

echo "== verify probes still run =="
for p in probes/*.py; do
  python3 "$p" >/dev/null || { echo "PROBE FAILED: $p"; exit 1; }
done
echo "all probes pass"

if git diff --quiet && git status --porcelain | grep -q . ; then
  echo "untracked files only, nothing to commit"
elif git diff --quiet; then
  echo "no changes"
else
  git add -A
  git commit -m "chore(sync): refresh from vxi.me invariants index" \
    -m "Auto-sync: index.json, evidence/*.json, regenerated README.md."
  echo "committed"
fi
