"""Synthetic Hawkes log-likelihood tie model; NOT a market-data fit.

Models the NASDAQ ITCH 5.0 same-nanosecond tie problem: 114 simultaneous
execution messages scored two ways — permutation-invariant pre-batch scoring
vs. row-by-row recursion that pretends earlier rows excite later ones.
Pure stdlib math; no ITCH data parsed, no Hawkes fitter used.
"""
import math

m, mu, alpha, tau, horizon = 114, 5.0, 0.6, 1.0, 1.0

# 同一批全部使用批次前的强度
pre_batch = m * math.log(mu)

# 错误对照：假装同一纳秒的前 i 条已激励第 i+1 条
row_ordered = math.fsum(
    math.log(mu + alpha * i / tau) for i in range(m)
)

# 完整似然还需扣除整个观测窗口的强度积分
baseline_area = mu * horizon
excitation_area = alpha * m * (-math.expm1(-horizon / tau))
compensator = baseline_area + excitation_area

print(f"prebatch_event_log_term: {pre_batch:.6f}")
print(f"row_ordered_event_log_term: {row_ordered:.6f}")
print(f"artificial_excess: {row_ordered - pre_batch:.6f}")
print(f"one_second_compensator: {compensator:.6f}")
print(f"one_second_full_LL: {pre_batch - compensator:.6f}")
