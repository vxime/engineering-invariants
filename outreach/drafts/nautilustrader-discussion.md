# DRAFT — NOT POSTED. Awaiting owner approval.
# Target: https://github.com/nautechsystems/nautilus_trader/discussions
# Category: Show and tell
# Why Discussion, not Issue: the head-truncation behavior is documented in the
# official docs at the pinned commit; this shares a runnable demonstration + checklist.

## F_LAST head-truncation: a runnable toy model + checklist for backtest fill mismatches

**Context.** While debugging backtest fill mismatches on NautilusTrader `2.0.0rc7`
(pinned at commit `55c0e820`), I worked through how `batch_deltas` interacts with
`F_LAST` grouping in `BookDeltasBatcher` (`crates/backtest/src/node.rs`, L744–L829).
The [official docs at that commit](https://github.com/nautechsystems/nautilus_trader/blob/55c0e82053142bce3a5cba4de4221d3929c2d3bc/docs/concepts/backtesting/apis-and-runs.md#L176-L187)
already note that head truncation may go undetected — this post is a runnable
demonstration of *why*, plus the checklist I now run before touching strategy params.

**The mechanism, in one table.**

| Window cut | Rows seen by the batcher | `F_LAST` present? | Batcher behavior |
|---|---|---|---|
| complete | ADD 999.95 → DELETE 999.95 | yes | closes normally |
| tail cut | ADD 999.95 | no | unterminated → error at end of input |
| **head cut** | DELETE 999.95 | **yes** | **closes, silently missing the head** |

The batcher raises on a missing *tail*, but a batch that starts mid-event and still
carries `F_LAST` closes without complaint. `F_LAST` proves where a batch *ends*,
never where it *began*.

**Minimal model (stdlib only).** Self-authored toy of the grouping rule —
*not* the NautilusTrader runtime:

```python
def group_by_last(rows):
    pending = {}
    for row in rows:
        event = pending.setdefault(row.instrument, [])
        event.append(row)
        if row.last:                      # F_LAST
            yield tuple(event)
            del pending[row.instrument]
    if pending:
        raise ValueError(f"missing F_LAST for {sorted(pending)}")

# head-truncated input: only the DELETE survives, still carrying F_LAST
rows = [("SIM", "DELETE", "999.95", True)]
print(list(group_by_last(rows)))   # closes silently — the missing head is invisible
```

And the fill consequence: with one pending BUY at 1000.00, replaying an event
row-by-row fills once (`individual=1`); replaying the whole event as one batch
fills zero times (`batched=0`) — the intermediate 999.95 ask is added and removed
inside the same batch, so the matcher never sees it. Same data, different fills,
from `batch_deltas=True` vs `False` alone. (Full 5/5 + 10/10 synthetic checks in
the write-up; the 10 include the head-truncation counter-example above.)

**Checklist I use now:**
1. Pin the baseline first: version, catalog content, query window, instrument
   precision — archive before re-running anything.
2. Verify window completeness per instrument: count `F_LAST`, then check the
   *first* event's start boundary. A closed tail does not prove an intact head.
3. Flip only `batch_deltas` (True → False) on identical data and config; find
   the first divergent fill, then trace back to its book events.

Full write-up with config snippets (`BacktestDataConfig`), the v2.0.0rc6
comparison, and scope notes:

- https://vxi.me/en/posts/nautilustrader-orderbook-batch-deltas-f-last/
