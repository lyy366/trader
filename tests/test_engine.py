import unittest
import pandas as pd
from backtest.strategy import MACDCrossStrategy
from backtest.engine import Backtester, EngineConfig

class TestEngine(unittest.TestCase):
    def test_engine_runs(self):
        idx = pd.date_range("2024-01-01", periods=100, freq="D")
        close = pd.Series(range(100)).astype(float) + 100
        df = pd.DataFrame({"date": idx.astype(str), "open": close.values, "high": close.values * 1.01, "low": close.values * 0.99, "close": close.values})
        strat = MACDCrossStrategy({"fe": 12, "le": 26, "sp": 9})
        signals = strat.generate_signals(df)
        engine = Backtester(EngineConfig(initial_cash=100000, commission_rate=0.0005, slippage=0.0005, position_pct=1.0, freq="daily"))
        res = engine.run(df, signals)
        self.assertEqual(len(res.equity), len(df))
        self.assertIsNotNone(res.trades)