"""Finite demonstration-only shortcut bank for be6269bef667."""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
_path = HERE / "adapter.py"
_name = "_be6269bef667_parametric_adapter_" + hashlib.sha256(str(_path).encode()).hexdigest()
if _name in sys.modules:
    adapter = sys.modules[_name]
else:
    _spec = importlib.util.spec_from_file_location(_name, _path)
    if _spec is None or _spec.loader is None:
        raise ImportError(_path)
    adapter = importlib.util.module_from_spec(_spec)
    sys.modules[_name] = adapter
    _spec.loader.exec_module(adapter)


RIVAL_NAMES = (
    "unit",
    "plurality_double",
    "fixed_double_1",
    "fixed_double_2",
    "fixed_double_3",
    "fixed_double_4",
    "least_direction_double",
    "plurality_only",
    "nonplurality_double",
    "direction_count_weight",
)


def predict(grid, name):
    if name in adapter.WEIGHTINGS:
        return adapter.solve(grid, name)
    facts = adapter.analyze(grid)
    plurality = facts["plurality_direction"]
    counts = facts["direction_counts"]
    if name.startswith("fixed_double_"):
        chosen = int(name.rsplit("_", 1)[1])
        weights = {direction: 2 if direction == chosen else 1 for direction in adapter.DIRECTIONS}
    elif name == "least_direction_double":
        minimum = min(counts.values())
        chosen = min(direction for direction, count in counts.items() if count == minimum)
        weights = {direction: 2 if direction == chosen else 1 for direction in adapter.DIRECTIONS}
    elif name == "plurality_only":
        weights = {direction: 1 if direction == plurality else 0 for direction in adapter.DIRECTIONS}
        # solve_weighted intentionally requires positive weights, so implement
        # this rival by subtracting the nonplurality unit maps from the full map.
        out = [[0] * len(grid[0]) for _ in grid]
        selected = {direction: (1 if direction == plurality else 0) for direction in adapter.DIRECTIONS}
        height, width = len(grid), len(grid[0])
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value != plurality:
                    continue
                dr, dc = adapter.DIRECTIONS[value]
                rr, cc = r, c
                while 0 <= rr < height and 0 <= cc < width and grid[rr][cc] != 5:
                    out[rr][cc] += selected[value]
                    rr += dr
                    cc += dc
        return out
    elif name == "nonplurality_double":
        weights = {direction: 1 if direction == plurality else 2 for direction in adapter.DIRECTIONS}
    elif name == "direction_count_weight":
        weights = dict(counts)
    else:
        raise ValueError("unknown rival")
    return adapter.solve_weighted(grid, weights)
