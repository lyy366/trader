import numpy as np
import pandas as pd

def periods_per_year(freq: str) -> int:
    if freq == "daily":
        return 252
    if freq == "weekly":
        return 52
    if freq == "monthly":
        return 12
    return 252

def cumulative_return(equity: pd.Series) -> float:
    if len(equity) == 0:
        return 0.0
    return float(equity.iloc[-1] / equity.iloc[0] - 1.0)

def annualized_return(equity: pd.Series, freq: str) -> float:
    n = len(equity)
    if n <= 1:
        return 0.0
    ppy = periods_per_year(freq)
    cr = equity.iloc[-1] / equity.iloc[0]
    return float(cr ** (ppy / n) - 1.0)

def max_drawdown(equity: pd.Series) -> float:
    if len(equity) == 0:
        return 0.0
    roll_max = equity.cummax()
    drawdown = equity / roll_max - 1.0
    return float(drawdown.min())

def sharpe_ratio(returns: pd.Series, freq: str, rf: float = 0.0) -> float:
    if returns.std() == 0:
        return 0.0
    ppy = periods_per_year(freq)
    return float((returns.mean() - rf / ppy) / returns.std() * np.sqrt(ppy))

def win_rate(trades: pd.DataFrame) -> float:
    if trades.empty:
        return 0.0
    pnl = []
    for i in range(1, len(trades)):
        prev = trades.iloc[i - 1]
        cur = trades.iloc[i]
        if prev["side"] in {"buy"} and cur["side"] in {"sell", "stop_loss", "take_profit"}:
            pnl.append(cur["price"] - prev["price"])
    if len(pnl) == 0:
        return 0.0
    wins = [x for x in pnl if x > 0]
    return float(len(wins) / len(pnl))

def profit_factor(trades: pd.DataFrame) -> float:
    pnl = []
    for i in range(1, len(trades)):
        prev = trades.iloc[i - 1]
        cur = trades.iloc[i]
        if prev["side"] in {"buy"} and cur["side"] in {"sell", "stop_loss", "take_profit"}:
            pnl.append(cur["price"] - prev["price"])
    if len(pnl) == 0:
        return 0.0
    gains = sum([x for x in pnl if x > 0])
    losses = sum([x for x in pnl if x < 0])
    if losses == 0:
        return float("inf")
    return float(gains / abs(losses))

def summarize(equity: pd.Series, returns: pd.Series, trades: pd.DataFrame, freq: str) -> pd.Series:
    return pd.Series({
        "cumulative_return": cumulative_return(equity),
        "annualized_return": annualized_return(equity, freq),
        "max_drawdown": max_drawdown(equity),
        "sharpe_ratio": sharpe_ratio(returns, freq),
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
    })