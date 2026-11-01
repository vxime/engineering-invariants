# DRAFT — NOT POSTED. Awaiting owner approval.
# Target: https://github.com/TwiN/gatus/discussions
# Category: Show and tell
# GraphQL: repositoryId=MDEwOlJlcG9zaXRvcnkyMDYyMTQ4Njc= categoryId=MDE4OkRpc2N1c3Npb25DYXRlZ29yeTMyNzY5Njg4
# Why Discussion, not Issue: every behavior observed matched expectations;
# this shares the composed verification matrix (failure -> alert -> recovery -> restart).

## Verification matrix: HTTP 503 alerting, resolution, and SQLite history persistence (v5.37.0, Docker Compose)

**Setup.** Gatus `v5.37.0` (pinned `ae605f29`) plus a synthetic HTTP fixture in one
isolated Docker Compose network. Alerting goes through `alerting.custom` into a
local webhook receiver — no real paging channels touched. Sequence driven:
`200 → 503 → 200`, plus a cold-start connection-refused case and a Gatus
container restart. Thresholds: `failure-threshold: 2`, `success-threshold: 2`,
`send-on-resolved: true`.

**Observed — all matched expectations:**

| Scenario | Expected | Observed |
|---|---|---|
| 2× consecutive 503 | TRIGGERED webhook | 2 TRIGGERED payloads received |
| Recovery to 200 | RESOLVED webhook | 1 RESOLVED payload received |
| Cold start, endpoint not listening yet | unhealthy, no alert storm | connection refused → healthy on retry |
| Gatus container restart | history retained | SQLite check history intact after restart |

**Why share this.** The docs describe each knob well; what I wanted was the
*composed* behavior across failure → alert → recovery → restart, with the exact
thresholds, in one reproducible rig. Posting the matrix here in case others are
calibrating the same thresholds — happy to answer questions about the fixture.

The one genuinely fiddly part was the first-boot connection refusal (Gatus
healthy-check page green, fixture not yet listening); the write-up documents the
startup ordering that made the rig deterministic.

Full write-up with the complete docker-compose config, fixture code, and the
troubleshooting checklist:

- https://vxi.me/en/posts/gatus-docker-compose-http-503-alert-recovery/
