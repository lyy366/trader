# Trader 期货 MACD 与双通道分析

使用 AkShare 拉取期货分钟数据，计算 MACD、标记金叉/死叉、生成长短期双通道，并识别“MACD 纯化结构”。脚本位于 `futures_macd.py`，输出为 CSV。

## 算法概要
- MACD（`futures_macd.py:197`）：`DIF = EMA(close,12) - EMA(close,26)`；`DEA = EMA(DIF,9)`；`MACD = 2*(DIF-DEA)`。
- 金叉/死叉（`futures_macd.py:205`）：比较上一时刻与当前 `DIF/DEA` 关系，得到 `macd_cross`（金叉=1，死叉=-1，其他=0）。
- 双通道（`futures_macd.py:7`）：对 `high/low` 做指数加权均值（EWM），生成长/短期上下轨：`lt_upper/lt_lower/st_upper/st_lower`（默认 `lt=90, st=25`）。
- 纯化结构（`futures_macd.py:82`）：以 `DIF/DEA` 的金叉/死叉分段，比较当前段滚动极值与上一完整段极值：
  - 底部纯化 `1`：价格创新低且 `DIF` 低点抬高，且 `MACD<0`。
  - 底部结构 `2`：在底部纯化后，`MACD>0` 或 `DIF` 上行。
  - 顶部纯化 `-1`：价格创新高且 `DIF` 高点降低，且 `MACD>0`。
  - 顶部结构 `-2`：在顶部纯化后，`MACD<0` 或 `DIF` 下行。
  - 其他为 `0`。

## 输出列
- `date, open, high, low, close, dif, dea, macd`
- `macd_cross`
- `lt_upper, lt_lower, st_upper, st_lower`
- `macd_structure`

## 环境与安装
- Python 3.9+；建议虚拟环境
- 创建并激活：`python3 -m venv .venv && source .venv/bin/activate`
- 安装依赖：`pip install -r requirements.txt`

## 使用示例
- `python futures_macd.py --symbol RB2310 --period 5 --limit 120`
- `python futures_macd.py --symbol RB2310 --period 1`

## 提示
- 数据源为新浪；需可访问外网
- 支持分钟周期：`1, 5, 15, 30, 60`
- 可选 `--limit` 控制输出行数；不加参数默认打印全部 CSV