from typing import Dict, Any
import pandas as pd

class Strategy:
    def __init__(self, params: Dict[str, Any] | None = None):
        self.params = params or {}

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

class MACDCrossStrategy(Strategy):
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ema12 = df["close"].ewm(span=int(self.params.get("fe", 12)), adjust=False).mean()
        ema26 = df["close"].ewm(span=int(self.params.get("le", 26)), adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=int(self.params.get("sp", 9)), adjust=False).mean()
        prev_dif = dif.shift(1)
        prev_dea = dea.shift(1)
        buy = (prev_dif < prev_dea) & (dif >= dea)
        sell = (prev_dif > prev_dea) & (dif <= dea)
        sig = pd.Series(0, index=df.index)
        sig[buy] = 1
        sig[sell] = -1
        return sig