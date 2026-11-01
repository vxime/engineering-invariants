"""Synthetic CVaR tail-mean demo; source-inspection model, not vectorbt runtime."""
import math
import sys
import unittest

# All 20 returns below are fictional decimal returns. NaN is NOT zero.
CLEAN = [
    -0.07, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, 0.03, 0.0,
    -0.02, 0.01, 0.02, 0.03, 0.01, 0.0, 0.02, 0.01, 0.0, 0.04,
]
DIRTY = CLEAN[:8] + [float('nan')] + CLEAN[8:]
ALPHA = 0.10  # Deliberate teaching cutoff; upstream default is 0.05.


def tail_mean(data, alpha=ALPHA, *, drop_nan):
    """Model v1.1.1 raw-count vs v1.1.2 valid-count tail selection.

    Returns (signed tail mean, cutoff_index, selected tail values).
    The original Rust comparison puts NaN last; this is a stdlib model.
    """
    values = [v for v in data if not math.isnan(v)] if drop_nan else list(data)
    if not values:
        return float('nan'), None, []
    ordered = sorted(values, key=lambda v: (math.isnan(v), 0 if math.isnan(v) else v))
    k = int((len(values) - 1) * alpha)
    selected = ordered[:k + 1]
    return sum(selected) / len(selected), k, selected


def old_isclose(a, b):
    # Models the v1.1.1 tests/utils.py early-return bug only.
    if math.isnan(a) == math.isnan(b):
        return True
    return math.isclose(a, b, rel_tol=1e-6)


class SyntheticChecks(unittest.TestCase):
    def test_old_new_tail_count(self):
        self.assertAlmostEqual(tail_mean(DIRTY, drop_nan=False)[0], -0.04666666666666667)
        self.assertAlmostEqual(tail_mean(DIRTY, drop_nan=True)[0], -0.055)
        self.assertEqual(tail_mean(DIRTY, drop_nan=False)[1], 2)
        self.assertEqual(tail_mean(DIRTY, drop_nan=True)[1], 1)

    def test_no_nan_control(self):
        self.assertAlmostEqual(tail_mean(CLEAN, drop_nan=False)[0], -0.055)
        self.assertAlmostEqual(tail_mean(CLEAN, drop_nan=True)[0], -0.055)

    def test_nan_position_invariance(self):
        for i in (0, 8, 20):
            values = CLEAN[:i] + [float('nan')] + CLEAN[i:]
            self.assertAlmostEqual(tail_mean(values, drop_nan=True)[0], -0.055)

    def test_empty_and_all_nan(self):
        self.assertTrue(math.isnan(tail_mean([], drop_nan=True)[0]))
        self.assertTrue(math.isnan(tail_mean([float('nan')] * 3, drop_nan=True)[0]))

    def test_test_helper_false_positive(self):
        self.assertTrue(old_isclose(1.0, 2.0))
        self.assertFalse(math.isclose(1.0, 2.0, rel_tol=1e-6))


if __name__ == '__main__':
    old, old_k, old_tail = tail_mean(DIRTY, drop_nan=False)
    new, new_k, new_tail = tail_mean(DIRTY, drop_nan=True)
    print('SYNTHETIC_INPUT: 20 valid returns + one NaN; alpha=0.10')
    print(f'RAW_COUNT: n={len(DIRTY)}, k={old_k}, tail={old_tail}, signed_mean={old:.8f}')
    print(f'VALID_COUNT: n={len(CLEAN)}, k={new_k}, tail={new_tail}, signed_mean={new:.8f}')
    print(f'NO_NAN_CONTROL: raw={tail_mean(CLEAN, drop_nan=False)[0]:.8f}, '
          f'valid={tail_mean(CLEAN, drop_nan=True)[0]:.8f}')
    print(f'OLD_ISCLOSE_FALSE_POSITIVE: isclose(1.0,2.0)={old_isclose(1.0, 2.0)}')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticChecks)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=1).run(suite)
    print(f'CHECKS_PASS={result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun}')
    sys.exit(0 if result.wasSuccessful() else 1)
