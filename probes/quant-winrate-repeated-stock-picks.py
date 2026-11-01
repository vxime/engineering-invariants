#!/usr/bin/env python3
"""Synthetic settled T+5 selection-outcome metric comparison, no real market data."""
from collections import defaultdict
from statistics import mean

# Entirely fictional stocks and T+5 returns (decimal units).
# Every row is a distinct snapshot-date pick in the SAME market, strategy, and horizon.
ROWS = [
    ("d1", "A", 0.05), ("d1", "B", -0.03),
    ("d2", "A", 0.04), ("d2", "C", -0.02),
    ("d3", "A", 0.03), ("d3", "B", -0.01),
    ("d4", "A", 0.06),
    ("d5", "A", 0.02),
    ("d6", "A", 0.01), ("d6", "D", -0.04),
]

def calc(rows):
    assert rows and all(isinstance(r, tuple) and len(r) == 3 for r in rows)
    symbol_returns = defaultdict(list)
    date_returns = defaultdict(list)
    for day, symbol, settled_return in rows:
        symbol_returns[symbol].append(settled_return)
        date_returns[day].append(settled_return)
    symbol_means = {symbol: mean(xs) for symbol, xs in symbol_returns.items()}
    date_means = {day: mean(xs) for day, xs in date_returns.items()}
    return {
        "settled_rows": len(rows),
        "distinct_symbols": len(symbol_returns),
        "distinct_pick_dates": len(date_returns),
        "sample_win_rate": sum(ret > 0 for _, _, ret in rows) / len(rows),
        "unique_symbol_win_rate": sum(ret > 0 for ret in symbol_means.values()) / len(symbol_means),
        "daily_cohort_win_rate": sum(ret > 0 for ret in date_means.values()) / len(date_means),
        "mean_daily_cohort_return": mean(date_means.values()),
        "symbol_mean_returns": symbol_means,
        "date_cohort_returns": date_means,
    }

if __name__ == "__main__":
    import json
    result = calc(ROWS)
    assert result["settled_rows"] == 10
    assert result["distinct_symbols"] == 4
    assert result["distinct_pick_dates"] == 6
    assert result["sample_win_rate"] == 0.6
    assert result["unique_symbol_win_rate"] == 0.25
    assert abs(result["daily_cohort_win_rate"] - 5 / 6) < 1e-12
    assert abs(result["mean_daily_cohort_return"] - 0.095 / 6) < 1e-12
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    print("ASSERTIONS_PASS=7")
