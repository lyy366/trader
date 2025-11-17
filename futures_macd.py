import sys
import argparse
import pandas as pd
import akshare as ak

# 计算双通道
def compute_dual_channel(df, lt=90, st=25) -> pd.DataFrame:
    df = df.copy()
    lt_upper = df["high"].ewm(span=lt, adjust=False).mean()
    lt_lower = df["low"].ewm(span=lt, adjust=False).mean()
    st_upper = df["high"].ewm(span=st, adjust=False).mean()
    st_lower = df["low"].ewm(span=st, adjust=False).mean()
    df.loc[:, "lt_upper"] = lt_upper
    df.loc[:, "lt_lower"] = lt_lower
    df.loc[:, "st_upper"] = st_upper
    df.loc[:, "st_lower"] = st_lower
    cols = ["date", "open", "high", "low", "close", "dif", "dea", "macd"]
    if "macd_cross" in df.columns:
        cols.append("macd_cross")
    cols += ["lt_upper", "lt_lower", "st_upper", "st_lower"]
    if "macd_purify" in df.columns:
        cols.append("macd_purify")
    if "macd_structure" in df.columns:
        cols.append("macd_structure")
    return df[cols]


# 纯化结构算法
# 定义：基于死叉/金叉分段，比较相邻段的价格与DIF极值，判断“直接/隔峰”的纯化与结构确认
# 输出：macd_structure 列，取值说明：
#  1  底部纯化（直接或隔峰底纯化成立）
#  2  底部结构（底部纯化后下一步动能确认：MACD>0 或 DIF上行）
# -1  顶部纯化（直接或隔峰顶纯化成立）
# -2  顶部结构（顶部纯化后下一步动能确认：MACD<0 或 DIF下行）
#  0  无结构形成
def compute_macd_structure(df) -> pd.DataFrame:
    df = df.copy()
    dif = df["dif"]
    dea = df["dea"]
    close = df["close"].astype(float)

    prev_dif = dif.shift(1)
    prev_dea = dea.shift(1)
    golden = (prev_dif < prev_dea) & (dif >= dea)
    dead = (prev_dif > prev_dea) & (dif <= dea)

    # 分段：以死叉/金叉为边界（累积段号）
    seg_down = dead.cumsum()
    seg_up = golden.cumsum()

    # 段内价格/DIF极值（滚动到当前行，避免前视偏差）
    seg_low_close_cum = close.groupby(seg_down).cummin()
    seg_low_dif_cum = dif.groupby(seg_down).cummin()
    seg_high_close_cum = close.groupby(seg_up).cummax()
    seg_high_dif_cum = dif.groupby(seg_up).cummax()

    # 完整段的极值（用于比较上一段/前两段）
    down_seg_low_close = close.groupby(seg_down).min()
    down_seg_low_dif = dif.groupby(seg_down).min()
    up_seg_high_close = close.groupby(seg_up).max()
    up_seg_high_dif = dif.groupby(seg_up).max()

    # 辅助：取当前段之前最近两个段id
    def prev_segments(series, cur_id):
        ids = series.iloc[:].unique()
        ids = [i for i in ids if i < cur_id]
        if len(ids) >= 2:
            return ids[-2], ids[-1]
        elif len(ids) == 1:
            return None, ids[-1]
        else:
            return None, None

    def row_prev_segments(group_ids, cur_id, upto_pos):
        ids = group_ids.iloc[:upto_pos].unique()
        ids = [i for i in ids if i < cur_id]
        ids.sort()
        if len(ids) >= 2:
            return ids[-2], ids[-1]
        elif len(ids) == 1:
            return None, ids[-1]
        else:
            return None, None

    df["macd_structure"] = 0
    prev_bottom_purify = False
    prev_top_purify = False

    for i in range(len(df)):
        state = 0
        # 底部：直接/隔峰纯化（使用当前段滚动极值；上一段用完整段极值）
        sd = seg_down.iloc[i]
        p1_id, p2_id = row_prev_segments(seg_down, sd, i)
        cur_low_c = seg_low_close_cum.iloc[i]
        cur_low_d = seg_low_dif_cum.iloc[i]
        if p2_id is not None:
            prev_low_c = float(down_seg_low_close.loc[p2_id])
            prev_low_d = float(down_seg_low_dif.loc[p2_id])
            cond_direct_bottom = (cur_low_c < prev_low_c) and (cur_low_d > prev_low_d) and (df["macd"].iloc[i] < 0) and (df["macd"].iloc[i-1] < 0 if i > 0 else False)
        else:
            cond_direct_bottom = False
        if p1_id is not None and p2_id is not None:
            low1_c = float(down_seg_low_close.loc[p1_id])
            low2_c = float(down_seg_low_close.loc[p2_id])
            low1_d = float(down_seg_low_dif.loc[p1_id])
            low2_d = float(down_seg_low_dif.loc[p2_id])
            cond_separated_bottom = (cur_low_c < low1_c) and (low1_c < low2_c) and (cur_low_d > low1_d) and (df["macd"].iloc[i] < 0) and (df["macd"].iloc[i-1] < 0 if i > 0 else False)
        else:
            cond_separated_bottom = False
        bottom_purify = bool(cond_direct_bottom or cond_separated_bottom)
        bottom_structure = bool(prev_bottom_purify and ((df["macd"].iloc[i] > 0) or (dif.iloc[i] > dif.iloc[i-1] if i > 0 else False)))
        if bottom_structure:
            state = 2
        elif bottom_purify:
            state = 1

        # 顶部：直接/隔峰纯化（使用当前段滚动极值；上一段用完整段极值）
        su = seg_up.iloc[i]
        t1_id, t2_id = row_prev_segments(seg_up, su, i)
        cur_high_c = seg_high_close_cum.iloc[i]
        cur_high_d = seg_high_dif_cum.iloc[i]
        if t2_id is not None and state == 0:
            prev_high_c = float(up_seg_high_close.loc[t2_id])
            prev_high_d = float(up_seg_high_dif.loc[t2_id])
            cond_direct_top = (cur_high_c > prev_high_c) and (cur_high_d < prev_high_d) and (df["macd"].iloc[i] > 0) and (df["macd"].iloc[i-1] > 0 if i > 0 else False)
        else:
            cond_direct_top = False
        if t1_id is not None and t2_id is not None and state == 0:
            high1_c = float(up_seg_high_close.loc[t1_id])
            high2_c = float(up_seg_high_close.loc[t2_id])
            high1_d = float(up_seg_high_dif.loc[t1_id])
            high2_d = float(up_seg_high_dif.loc[t2_id])
            cond_separated_top = (cur_high_c > high1_c) and (high1_c > high2_c) and (cur_high_d < high1_d) and (df["macd"].iloc[i] > 0) and (df["macd"].iloc[i-1] > 0 if i > 0 else False)
        else:
            cond_separated_top = False
        top_purify = bool(cond_direct_top or cond_separated_top)
        top_structure = bool(prev_top_purify and ((df["macd"].iloc[i] < 0) or (dif.iloc[i] < dif.iloc[i-1] if i > 0 else False)))
        if state == 0:
            if top_structure:
                state = -2
            elif top_purify:
                state = -1

        df.iloc[i, df.columns.get_loc("macd_structure")] = state
        prev_bottom_purify = bottom_purify
        prev_top_purify = top_purify

    return df

# 计算MACD
def compute_futures_macd(df, fe=12, le=26, sp=9) -> pd.DataFrame:  
    ema12 = df["close"].ewm(span=fe, adjust=False).mean()
    ema26 = df["close"].ewm(span=le, adjust=False).mean()
    df["dif"] = ema12 - ema26
    df["dea"] = df["dif"].ewm(span=sp, adjust=False).mean()
    df["macd"] = 2 * (df["dif"] - df["dea"])
    return df[["date", "open", "high", "low", "close", "dif", "dea", "macd"]]

def compute_macd_cross(df) -> pd.DataFrame:
    prev_dif = df["dif"].shift(1)
    prev_dea = df["dea"].shift(1)
    golden = (prev_dif < prev_dea) & (df["dif"] >= df["dea"]) 
    dead = (prev_dif > prev_dea) & (df["dif"] <= df["dea"]) 
    df = df.copy()
    df["macd_cross"] = 0
    df.loc[golden, "macd_cross"] = 1
    df.loc[dead, "macd_cross"] = -1
    return df

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--period", type=int, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--analyze", action="store_true")
    args = parser.parse_args(argv)
    if args.period not in {1, 5, 15, 30, 60}:
        raise ValueError("period must be one of 1, 5, 15, 30, 60")
    df = ak.futures_zh_minute_sina(symbol=args.symbol, period=str(args.period))
    if "datetime" in df.columns and "date" not in df.columns:
        df["date"] = df["datetime"]
    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = df[col].astype(float)
    out = compute_futures_macd(df)
    out = compute_macd_cross(out)

    out = compute_dual_channel(out)

    out = compute_macd_structure(out)

    if args.limit and args.limit > 0:
        out = out.tail(args.limit)
    if not args.analyze:
        print(out.to_csv(index=False))
        return

if __name__ == "__main__":
    main(sys.argv[1:])