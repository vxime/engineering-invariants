# DRAFT — NOT POSTED. Awaiting owner approval.
# Target: https://github.com/moritzwilksch/diffle/discussions
# Category: Q&A (or Show and tell)
# Why Discussion, not a bug Issue: the article explicitly states the ambiguity
# was demonstrated in a synthetic model, NOT reproduced as a UI bug in Diffle.

## Question: when two identical text candidates exist, nearest-match anchoring may pick the wrong one

**Context.** While studying how Diffle re-anchors line comments after an Agent
rewrite (pinned at commit `a69274d`), I built a synthetic model of the
relocation rule in
[`CommentStore.relocateAll()`](https://github.com/moritzwilksch/diffle/blob/a69274d512a588dd86714bef103c8dbc2cadb2cf/src/server/comments/CommentStore.ts)
to understand one specific case: what happens when the quoted text appears
*twice* in the new file.

**The synthetic test** (Node built-in `node:test`, 4/4 passing — a model of the
rule, not the Diffle UI):

```js
const contents = [
  'header();',   // line 1
  'repeat();',   // line 2: 1 line away from the old comment
  'other();',    // line 3: the old comment's position
  'new();',
  'changed();',
  'gap();',
  'repeat();',   // line 7: the assumed semantic target
].join('\n') + '\n';

// old comment at line 3 quoted 'repeat();' — after the rewrite there are
// two identical candidates. The rule picks line 2 (nearest), not line 7.
```

**The observation.** Nearest wins the tiebreak (`dist < bestDist` keeps the
first-found candidate), so "closest" is treated as "same". But distance is not
semantic identity: the line the reviewer actually meant can easily be the
farther one. I want to stress what this *doesn't* prove — I did not reproduce
a mis-anchored comment in the Diffle UI, and the existing guards are genuinely
good (comparison-side checks, hunk visibility, `stale` marking, and the refusal
to anchor worktree-only lines for GitHub in `review.ts` — all solid design).

**The question.** Is nearest-match the intended tiebreak when candidates tie on
text? If so, would you consider documenting it as a known limitation — or is
there appetite for a tiebreak that weighs surrounding context (with the honest
caveat that refactors scatter those clues too, so it's a tradeoff, not a fix)?

Full write-up with the 4-scenario test matrix, TAP output, and scope notes:

- https://vxi.me/en/posts/diffle-git-diff-comment-anchoring/
