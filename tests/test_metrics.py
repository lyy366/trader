import unittest
import pandas as pd
from backtest.metrics import cumulative_return, annualized_return, max_drawdown, sharpe_ratio

class TestMetrics(unittest.TestCase):
    def test_metrics_basic(self):
        idx = pd.date_range("2024-01-01", periods=10, freq="D")
        eq = pd.Series([100, 101, 102, 103, 104, 105, 106, 105, 106, 107], index=idx)
        ret = eq.pct_change().fillna(0)
        self.assertAlmostEqual(cumulative_return(eq), 107/100 - 1, places=6)
        self.assertGreater(annualized_return(eq, "daily"), 0)
        self.assertLessEqual(max_drawdown(eq), 0)
        self.assertGreater(sharpe_ratio(ret, "daily"), 0)