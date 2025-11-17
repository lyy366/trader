from concurrent.futures import ThreadPoolExecutor
from itertools import product
from typing import Dict, Any, List, Tuple, Callable
import pandas as pd

def grid_params(grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    keys = list(grid.keys())
    vals = [grid[k] for k in keys]
    combos = product(*vals)
    return [dict(zip(keys, c)) for c in combos]

def optimize(df: pd.DataFrame, strategy_factory: Callable[[Dict[str, Any]], Any], run_fn: Callable[[pd.DataFrame, Any], Dict[str, Any]], grid: Dict[str, List[Any]], max_workers: int = 4) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    params_list = grid_params(grid)
    results: List[Tuple[Dict[str, Any], Dict[str, Any]]] = []
    def task(p: Dict[str, Any]):
        strat = strategy_factory(p)
        return p, run_fn(df, strat)
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for p, r in ex.map(task, params_list):
            results.append((p, r))
    return results