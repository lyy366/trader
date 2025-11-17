import pandas as pd
import akshare as ak

def load_stock(symbol: str, start: str = None, end: str = None, period: str = "daily") -> pd.DataFrame:
    df = ak.stock_zh_a_hist(symbol=symbol, period=period, adjust="")
    if start is not None:
        df = df[df["日期"] >= start]
    if end is not None:
        df = df[df["日期"] <= end]
    df = df.rename(columns={"日期": "date", "开盘": "open", "最高": "high", "最低": "low", "收盘": "close", "成交量": "volume"})
    df = df[["date", "open", "high", "low", "close", "volume"]]
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    return df

def load_futures_minute(symbol: str, period: int = 1) -> pd.DataFrame:
    df = ak.futures_zh_minute_sina(symbol=symbol, period=str(period))
    if "datetime" in df.columns and "date" not in df.columns:
        df["date"] = df["datetime"]
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = df[col].astype(float)
    return df[["date", "open", "high", "low", "close"]]

def select_fields(df: pd.DataFrame, fields: list) -> pd.DataFrame:
    return df[fields]