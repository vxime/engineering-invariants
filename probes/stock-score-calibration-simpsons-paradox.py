#!/usr/bin/env python3
"""Deterministic synthetic check of group-conditional scoring; NOT a market backtest.

All labels below are intentionally constructed. There are no real stock prices,
no actual trading outcomes, and no production scoring-engine output.
"""
import json
import math
from collections import defaultdict

# Fixed illustrative counts: (source, hypothetical regime, observations, positive outcomes)
SPEC = [
    ("technical_signal", "trend", 30, 21),
    ("technical_signal", "range", 10, 3),
    ("screener_preset", "trend", 10, 8),
    ("screener_preset", "range", 30, 15),
]


def wilson_interval(positive, total, z=1.959963984540054):
    if total < 1:
        raise ValueError("empty group")
    p = positive / total
    denom = 1 + z*z/total
    center = (p + z*z/(2*total)) / denom
    half = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / denom
    return [round(center-half, 4), round(center+half, 4)]


def make_group(total, positive):
    return {"n": total, "positive": positive, "rate": round(positive / total, 4),
            "wilson_95": wilson_interval(positive, total)}


def main():
    rows = []
    for source, regime, total, positive in SPEC:
        rows.extend({"source": source, "regime": regime, "raw_score": 80,
                     "positive_event_5d": int(i < positive)} for i in range(total))
    summaries = defaultdict(dict)
    pooled = defaultdict(lambda: [0, 0])
    for source, regime, n, yes in SPEC:
        summaries[source][regime] = make_group(n, yes)
        pooled[source][0] += n
        pooled[source][1] += yes
    result = {"scope": "CONSTRUCTED_SYNTHETIC_EXAMPLE_NOT_MARKET_DATA",
              "event_definition": "binary illustrative positive_event_5d, not executed trade PnL",
              "raw_score": 80, "total_rows": len(rows), "sources": {}}
    for source in sorted(summaries):
        trend = summaries[source]["trend"]["rate"]
        range_ = summaries[source]["range"]["rate"]
        n, yes = pooled[source]
        result["sources"][source] = {
            "by_regime": summaries[source], "pooled": make_group(n, yes),
            "equal_regime_mix_rate": round((trend + range_) / 2, 4)
        }
    a = result["sources"]["technical_signal"]
    b = result["sources"]["screener_preset"]
    assert len(rows) == 80
    assert a["pooled"]["rate"] == 0.6 and b["pooled"]["rate"] == 0.575
    assert a["equal_regime_mix_rate"] == 0.5 and b["equal_regime_mix_rate"] == 0.65
    assert all(b["by_regime"][r]["rate"] > a["by_regime"][r]["rate"] for r in ("trend", "range"))
    result["test_assertions"] = {
        "fixed_80_records": "PASS", "pooled_order_a_above_b": "PASS",
        "within_each_regime_b_above_a": "PASS", "fixed_equal_mix_order_b_above_a": "PASS"
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
