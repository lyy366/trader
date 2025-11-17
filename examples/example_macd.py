import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import pandas as pd
from backtest.strategy import MACDCrossStrategy
from backtest.engine import Backtester, EngineConfig
from backtest.metrics import summarize

def run_example(df: pd.DataFrame) -> pd.Series:
    strat = MACDCrossStrategy({"fe": 12, "le": 26, "sp": 9})
    signals = strat.generate_signals(df)
    engine = Backtester(EngineConfig(initial_cash=100000, commission_rate=0.0005, slippage=0.0005, position_pct=1.0, freq="daily"))
    res = engine.run(df, signals)
    return summarize(res.equity, res.returns, res.trades, "daily")

if __name__ == "__main__":
    idx = pd.date_range("2024-01-01", periods=300, freq="D")
    prices = pd.Series(pd.Series(range(300)).rolling(10, min_periods=1).mean() + 100).astype(float)
    df = pd.DataFrame({"date": idx.astype(str), "open": prices.values, "high": prices.values * 1.01, "low": prices.values * 0.99, "close": prices.values})
    s = run_example(df)
    print(s.to_string())