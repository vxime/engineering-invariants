# DRAFT — NOT POSTED. Awaiting owner approval.
# Target: https://github.com/openqodex/openqodex/issues
# Why an Issue: this is a product-semantics question about a real code path
# (checkPush() -> abstain on incomplete), with pinned source references.
# Framed as a question, not a vulnerability claim — see scope note at the end.

## Question: pre-push hook fail-open when the review record is `incomplete`

**Version:** OpenQodex `0.11.0`, pinned at commit `2f2fa9e`.

**What I observed** (isolated repo, the real installed Git pre-push hook, synthetic shell change):

1. Unreviewed change + default config → hook prints the unreviewed warning, push
   succeeds. (Understood: documented default.)
2. After enabling blocking: unreviewed change → push rejected, and the local bare
   remote's `main` stayed at the pre-push commit. ✓
3. Started the independent reviewer; the subprocess got HTTP 401 → OpenQodex
   recorded the review as `incomplete`. A subsequent push **succeeded** (exit 0)
   and created the remote branch.

**Code pointer.** In
[`packages/core/src/push-gate.ts`](https://github.com/openqodex/openqodex/blob/2f2fa9e48c1f62a6123997eb14111140d8e22a74/packages/core/src/push-gate.ts),
`checkPush()` returns `abstain` when the matching record is `incomplete` — and
configuring `block_on_severity: major` does not flip this branch to reject.
The hook itself states the intent plainly
([`packages/cli/src/commands/hook.ts` L297–299](https://github.com/openqodex/openqodex/blob/2f2fa9e48c1f62a6123997eb14111140d8e22a74/packages/cli/src/commands/hook.ts#L297-L299),
same wording on current main):

```
// Exit 1 only when the lookup denies (block_on_severity is set and
// the review is missing or blocked); an incomplete review never blocks.
```

The hook (`packages/cli/src/commands/hook.ts`) reads the review record for the
push range; it does not re-run the reviewer.

**The question, not an accusation.** Fail-open on reviewer outage may be an
intentional product choice — never block a developer because the reviewer is
down. But a team reading "pre-push review gate" as "incomplete review ⇒
blocked" will build the wrong safety expectation. Would you consider either:

- documenting the `incomplete → abstain → allow` path explicitly, or
- a `fail_closed_on_incomplete`-style option for teams that want the strict semantic?

**Scope honesty.** The 401 meant the independent reviewer never actually ran, so
step 3's push and the `incomplete` record are adjacent observations, not a proven
causal chain — I did not have a verifiable evidence pack for that leg. The
`abstain` branch itself is read straight from the pinned source. This is a
semantics question about intended behavior, not a demonstrated bypass.

Full notes:

- https://vxi.me/en/posts/openqodex-prepush-review-fail-open/
