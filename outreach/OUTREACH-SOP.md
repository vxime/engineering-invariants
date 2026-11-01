# Upstream outreach SOP — how to earn a backlink without looking like spam

The maintainer's inbox is the highest-trust surface we have. One lazy post
burns more reputation than ten good ones build. This checklist is the gate.

## The triage (do this BEFORE drafting anything)

For each candidate article, answer in order. Stop at the first "no":

1. **Is there new information for the maintainer?**
   - Unfixed edge-case bug with a runnable reproducer → yes.
   - Doc claim vs. measured behavior gap → yes.
   - Verification matrix the maintainer's own docs don't compose → yes (Discussion).
   - Already fixed upstream (release notes / merged PR) → **NO. Do not file.**
     A retrospective "I verified your fix" is not an Issue; it is noise.
   - Author already reported & fixed it themselves → **NO. Do not file.**
   - Documented behavior you are merely re-demonstrating → **NO as an Issue.**
     It may still qualify as a Discussion (Show and Tell), framed as such.
   - Your own article says "not reproduced in the real tool" → **NO.**
     At most a Discussion sharing the analysis, never a bug report.

2. **Is the claim still true at the current upstream HEAD?**
   Re-check the pinned file/line. If the code moved, update the pin or drop it.

3. **Issue or Discussion?**
   - Something is broken or the docs are wrong → Issue.
   - Sharing a verification, a checklist, a "here's how I debugged this" → Discussion.
   - When in doubt, Discussion. A misfiled Issue is the fastest way to look like spam.

## The post contract

- **95% inline, 5% link.** The full reproducer, the numbers, the code pointer
  live in the post body. The article link goes last, labeled as "full write-up".
- **Never link a 404.** `curl` every URL the day you post. (Once bitten:
  `/evidence/<slug>.json` exists for only 2 of 13 cases — link it only there.)
- **Pin everything:** version, commit hash, file path + line numbers.
- **Scope honesty:** say what you did NOT verify, in the post itself.
  ("The 401 meant the reviewer never ran, so this is an adjacent observation,
  not a proven causal chain.")
- **No cross-posting the same text** to multiple repos. Each post is written
  for that maintainer, referencing their code.
- **Rate limit yourself:** max 2–3 posts per day, hours apart. A burst of 10
  in 5 minutes trips new-account heuristics and reads as a campaign.
- **One discussion per repo per 30 days.** Even if you have two findings for the
  same repo, batch them into one post or wait. High signal-to-noise beats frequency.
- **Environment fingerprint in every technical post.** State the exact
  `OS / language version / pinned commit` you tested against (e.g.
  `Python 3.13.5 / Linux x86_64 / vectorbt @ f0d2afb`). This is the fastest way
  to disarm a maintainer's "did an LLM hallucinate this?" reflex.
- **Use an account with history.** Never post from a fresh account with no
  repos, no stars, no activity. (This account dates to 2018 — that history is
  part of why the posts land.)

## After posting

- Watch for maintainer replies for 2 weeks; answer technical follow-ups promptly.
- If a maintainer fixes it, update the article's "upstream status" note — that
  update is itself link-worthy.
- Record the post URL in the case's outreach log (below) so the next session
  doesn't double-post.

## Outreach log

| Date | Repo | Type | URL | Status |
| ---- | ---- | ---- | --- | ------ |
| 2026-11-01 | openqodex/openqodex | Issue (design question) | https://github.com/openqodex/openqodex/issues/282 | OPEN, awaiting maintainer |
| 2026-11-01 | moritzwilksch/diffle | Issue (design question; repo has no Discussions) | https://github.com/moritzwilksch/diffle/issues/422 | OPEN, awaiting maintainer |
| — | — | — | — | — |
