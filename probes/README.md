# Probe contract

Every file in this directory is a **standalone counter-example reproducer**:

1. **stdlib-only** (Python: no pip installs; shell: no downloads) — a maintainer
   must be able to copy-paste and run it with zero setup.
2. **One-command runnable** — `python3 probes/<name>.py` (or `bash`/`node` for
   `.sh`/`.mjs`) exits 0 on success, non-zero on failure. No arguments, no env
   vars, no network.
3. **Honest docstring, first thing in the file** — state the pinned upstream
   version/commit, what the probe models, and explicitly what it does NOT do
   (e.g. "models the grouping mechanism, does NOT run the NautilusTrader engine").
4. **Deterministic** — same output on every run. Synthetic inputs only; never
   real market data, never credentials.
5. **Named by article slug** — `probes/<slug>.py`, matching the case slug in
   `https://vxi.me/invariants/index.json` so `generate_readme.py` can link it
   automatically. A case without a probe yet simply shows "—" in the README.

Verified before commit: run the probe and paste the actual output into the
commit message or PR description. A probe that doesn't run doesn't ship.
