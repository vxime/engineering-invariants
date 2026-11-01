"""Self-authored toy model of F_LAST event boundaries, NOT NautilusTrader runtime."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Delta:
    instrument: str
    action: str
    price: Decimal
    last: bool
    ts_init: int


def d(instrument, action, price, last, timestamp):
    return Delta(instrument, action, Decimal(price), last, timestamp)


def group_by_last(rows):
    pending = {}
    for row in rows:
        event = pending.setdefault(row.instrument, [])
        event.append(row)
        if row.last:
            yield tuple(event)
            del pending[row.instrument]
    if pending:
        detail = ", ".join(sorted(pending))
        raise ValueError(f"missing F_LAST for {detail}")


def toy_fills(rows, batch_deltas):
    """One pending BUY at 1000; match after each replay item, not each event row."""
    asks = set()
    buy_pending = True
    fills = 0
    replay_items = group_by_last(rows) if batch_deltas else ((r,) for r in rows)
    for item in replay_items:
        for row in item:
            if row.action == "ADD":
                asks.add(row.price)
            elif row.action == "DELETE":
                asks.discard(row.price)
        if buy_pending and asks and min(asks) <= Decimal("1000.00"):
            buy_pending = False
            fills += 1
    return fills


def run():
    # The same synthetic event shape as the concept behind the pinned upstream test.
    rows = [
        d("SIM", "ADD", "1000.10", True, 1),
        d("SIM", "ADD", "999.95", False, 2),
        d("SIM", "DELETE", "999.95", True, 2),
    ]
    groups = list(group_by_last(rows))
    assert [len(g) for g in groups] == [1, 2]
    print("PASS 1/5 event boundaries: 3 deltas -> groups [1, 2]")

    individual, batched = toy_fills(rows, False), toy_fills(rows, True)
    assert (individual, batched) == (1, 0)
    print(f"PASS 2/5 toy fills: individual={individual}, batched={batched}")

    try:
        list(group_by_last([d("SIM", "ADD", "1.00", False, 3)]))
    except ValueError as exc:
        assert "missing F_LAST for SIM" in str(exc)
    else:
        raise AssertionError("unterminated event did not fail")
    print("PASS 3/5 unterminated event rejected")

    interleaved = [
        d("A", "ADD", "1", False, 4),
        d("B", "ADD", "2", True, 4),
        d("A", "DELETE", "1", True, 5),
    ]
    received = list(group_by_last(interleaved))
    assert [[r.instrument for r in group] for group in received] == [["B"], ["A", "A"]]
    print("PASS 4/5 interleaved instruments remain isolated")

    same_time = [d("SIM", "ADD", "1", True, 6), d("SIM", "ADD", "2", True, 6)]
    assert [len(g) for g in group_by_last(same_time)] == [1, 1]
    print("PASS 5/5 equal-timestamp completed events stay separate")
    print("SUMMARY: 5/5 PASS, self-authored stdlib model only; no upstream engine run")


if __name__ == "__main__":
    run()
