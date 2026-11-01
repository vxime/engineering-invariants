"""Offline model of the Polymarket volume double-counting trap.

Uses the article's own numbers — no network, no live API calls:
- Constructed example: 10 shares @ $0.60 filled by two makers ($2.40 + $3.60
  maker fills) plus the $6.00 taker summary. Naively summing all three records
  as independent trades gives $12.00, double the $6.00 economic volume.
- Observed shape: a 100-row taker_only=false page collapsed to 49 distinct
  transaction hashes (48 hashes repeated, up to 3 rows each).

Models the CTF Exchange V2 event hierarchy (one taker order + N maker orders
-> N maker OrderFilled + 1 taker-summary OrderFilled) and asserts the naive
row-sum overcounts the economic volume.
"""
from decimal import Decimal

# One economic trade, three on-chain records sharing one tx hash.
RECORDS = [
    {"tx": "0xAAA", "kind": "maker_fill", "amount": Decimal("2.40")},
    {"tx": "0xAAA", "kind": "maker_fill", "amount": Decimal("3.60")},
    {"tx": "0xAAA", "kind": "taker_summary", "amount": Decimal("6.00")},
    # Second trade, single maker: 2 records, 1 hash.
    {"tx": "0xBBB", "kind": "maker_fill", "amount": Decimal("1.00")},
    {"tx": "0xBBB", "kind": "taker_summary", "amount": Decimal("1.00")},
]


def naive_volume(records):
    """Sum every record as if each were an independent trade."""
    return sum(r["amount"] for r in records)


def economic_volume(records):
    """Count each transaction hash once, using its taker summary."""
    seen = {}
    for r in records:
        if r["kind"] == "taker_summary":
            seen[r["tx"]] = r["amount"]
    return sum(seen.values())


naive = naive_volume(RECORDS)
economic = economic_volume(RECORDS)
distinct_hashes = len({r["tx"] for r in RECORDS})
print(f"records={len(RECORDS)}, distinct_hashes={distinct_hashes}")
print(f"naive_row_sum={naive}, economic_volume={economic}")

assert naive == Decimal("14.00"), f"unexpected naive sum {naive}"
assert economic == Decimal("7.00"), f"unexpected economic sum {economic}"
assert naive == 2 * economic, "naive counting double-counts maker+taker legs"
assert distinct_hashes < len(RECORDS), "hash dedup must shrink the row count"
print("PASS: naive row-sum double-counts; per-hash taker-summary gives economic volume")
