from dataclasses import dataclass
from typing import Dict, Any, List
import pandas as pd

@dataclass
class EngineConfig:
    initial_cash: float = 100000.0
    commission_rate: float = 0.0005
    slippage: float = 0.0
    position_pct: float = 1.0
    order_type: str = "market"
    stop_loss: float | None = None
    take_profit: float | None = None
    freq: str = "daily"

class BacktestResult:
    def __init__(self, equity: pd.Series, trades: pd.DataFrame, positions: pd.Series, returns: pd.Series):
        self.equity = equity
        self.trades = trades
        self.positions = positions
        self.returns = returns

class Backtester:
    def __init__(self, config: EngineConfig):
        self.config = config

    def run(self, df: pd.DataFrame, signals: pd.Series) -> BacktestResult:
        df = df.copy()
        df["signal"] = signals.fillna(0)
        cash = self.config.initial_cash
        shares = 0.0
        entry_price = None
        equity = []
        pos_series = []
        trades: List[Dict[str, Any]] = []
        for i in range(len(df)):
            price = float(df["close"].iloc[i])
            sig = int(df["signal"].iloc[i])
            side = None
            exec_price = price
            if self.config.slippage and self.config.order_type == "market":
                if sig == 1:
                    exec_price = price * (1 + self.config.slippage)
                elif sig == -1:
                    exec_price = price * (1 - self.config.slippage)
            if sig == 1 and shares == 0.0:
                alloc_cash = cash * self.config.position_pct
                qty = alloc_cash / exec_price
                cost = qty * exec_price
                fee = cost * self.config.commission_rate
                cash -= cost + fee
                shares += qty
                entry_price = exec_price
                side = "buy"
                trades.append({"date": df["date"].iloc[i], "side": side, "price": exec_price, "shares": qty, "fee": fee})
            elif sig == -1 and shares > 0.0:
                revenue = shares * exec_price
                fee = revenue * self.config.commission_rate
                cash += revenue - fee
                side = "sell"
                trades.append({"date": df["date"].iloc[i], "side": side, "price": exec_price, "shares": shares, "fee": fee})
                shares = 0.0
                entry_price = None
            if shares > 0.0 and entry_price is not None:
                if self.config.stop_loss is not None:
                    if exec_price <= entry_price * (1 - self.config.stop_loss):
                        revenue = shares * exec_price
                        fee = revenue * self.config.commission_rate
                        cash += revenue - fee
                        trades.append({"date": df["date"].iloc[i], "side": "stop_loss", "price": exec_price, "shares": shares, "fee": fee})
                        shares = 0.0
                        entry_price = None
                if shares > 0.0 and self.config.take_profit is not None:
                    if exec_price >= entry_price * (1 + self.config.take_profit):
                        revenue = shares * exec_price
                        fee = revenue * self.config.commission_rate
                        cash += revenue - fee
                        trades.append({"date": df["date"].iloc[i], "side": "take_profit", "price": exec_price, "shares": shares, "fee": fee})
                        shares = 0.0
                        entry_price = None
            eq = cash + shares * price
            equity.append(eq)
            pos_series.append(shares)
        equity = pd.Series(equity, index=df.index)
        positions = pd.Series(pos_series, index=df.index)
        returns = equity.pct_change().fillna(0)
        trades_df = pd.DataFrame(trades)
        return BacktestResult(equity, trades_df, positions, returns)