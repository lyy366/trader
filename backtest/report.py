import pandas as pd

def equity_curve_df(equity: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({"equity": equity})

def returns_hist_df(returns: pd.Series, bins: int = 50) -> pd.DataFrame:
    s = returns.dropna()
    hist = pd.cut(s, bins=bins).value_counts().sort_index()
    return hist.to_frame(name="count")

def drawdown_df(equity: pd.Series) -> pd.DataFrame:
    roll_max = equity.cummax()
    dd = equity / roll_max - 1.0
    return pd.DataFrame({"drawdown": dd})

def save_plots(equity: pd.Series, returns: pd.Series, out_dir: str) -> dict:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return {}
    paths = {}
    fig1 = plt.figure()
    plt.plot(equity.values)
    p1 = f"{out_dir}/equity_curve.png"
    fig1.savefig(p1)
    plt.close(fig1)
    fig2 = plt.figure()
    plt.hist(returns.values, bins=50)
    p2 = f"{out_dir}/returns_hist.png"
    fig2.savefig(p2)
    plt.close(fig2)
    roll_max = equity.cummax()
    dd = equity / roll_max - 1.0
    fig3 = plt.figure()
    plt.plot(dd.values)
    p3 = f"{out_dir}/drawdown.png"
    fig3.savefig(p3)
    plt.close(fig3)
    paths["equity_curve"] = p1
    paths["returns_hist"] = p2
    paths["drawdown"] = p3
    return paths