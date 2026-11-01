#!/usr/bin/env bash
# Model of the OpenQodex pre-push hook decision on `incomplete` reviews.
# NOT the real OpenQodex code: a mock hook implementing the documented semantic
# "an incomplete review never blocks" (packages/cli/src/commands/hook.ts L299
# @ 2f2fa9e). Runs fully offline in a temp git repo + local bare remote.
# Asserts: incomplete -> push allowed (exit 0); blocked -> push denied (exit 1).
set -euo pipefail

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
git init -q --bare "$work/remote.git"
git init -q "$work/local"
cd "$work/local"
git config user.email probe@test
git config user.name probe
git remote add origin "$work/remote.git"

# Mock hook: models checkPush() — incomplete/missing abstains (allow),
# blocked denies. Mirrors the pinned source's stated intent, not its code.
mkdir -p .git/hooks
cat > .git/hooks/pre-push <<'HOOK'
#!/usr/bin/env bash
if [ "${REVIEW_STATUS:-missing}" = "blocked" ]; then
  echo "hook: deny (review blocked)"; exit 1
fi
echo "hook: abstain (status=${REVIEW_STATUS:-missing}) -> allow"; exit 0
HOOK
chmod +x .git/hooks/pre-push

echo x > f && git add f && git commit -qm init
if REVIEW_STATUS=incomplete git push -q origin HEAD:refs/heads/main; then
  echo "PASS 1/2: incomplete review -> push allowed (fail-open)"
else
  echo "FAIL 1/2: incomplete review blocked the push"; exit 1
fi

echo y > g && git add g && git commit -qm second
if REVIEW_STATUS=blocked git push -q origin HEAD:refs/heads/main 2>/dev/null; then
  echo "FAIL 2/2: blocked review was allowed through"; exit 1
else
  echo "PASS 2/2: blocked review -> push denied"
fi
echo "SUMMARY: 2/2 PASS — mock hook reproduces the incomplete fail-open semantic"
