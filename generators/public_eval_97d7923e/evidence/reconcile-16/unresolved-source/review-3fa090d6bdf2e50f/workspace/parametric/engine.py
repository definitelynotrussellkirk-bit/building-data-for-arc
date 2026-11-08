"""Semantic engine for public_eval_97d7923e.

A top-left legend contains repeated endpoint colors.  For each color, its
legend multiplicity selects the equally colored vertical rod ranked by payload
length (longest first).  The canonical rule recolors that rod's payload to its
endpoint color.  The alternate first performs the same selection and then
highlights the complete longest selected rod.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

Grid = list[list[int]]


def _grid(grid: Any) -> Grid:
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        raise ValueError("grid must be a non-empty list of rows")
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular and non-empty")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer colors 0..9")
    return [row[:] for row in grid]


def _rod_runs(grid: Grid) -> list[dict[str, int]]:
    h, w = len(grid), len(grid[0])
    rods: list[dict[str, int]] = []
    for c in range(w):
        r = 0
        while r < h:
            if grid[r][c] == 0:
                r += 1
                continue
            top = r
            while r + 1 < h and grid[r + 1][c] != 0:
                r += 1
            bottom = r
            values = [grid[rr][c] for rr in range(top, bottom + 1)]
            if (
                len(values) >= 3
                and values[0] == values[-1]
                and values[0] != 0
                and len(set(values[1:-1])) == 1
                and values[1] != 0
                and values[1] != values[0]
            ):
                rods.append(
                    {
                        "endpoint": values[0],
                        "payload": values[1],
                        "top": top,
                        "bottom": bottom,
                        "col": c,
                        "length": bottom - top - 1,
                    }
                )
            r += 1
    return rods


def analyze(grid: Any) -> dict[str, Any]:
    g = _grid(grid)
    rods = _rod_runs(g)
    if not rods:
        raise ValueError("no vertical rods found")
    covered = {
        (r, rod["col"])
        for rod in rods
        for r in range(rod["top"], rod["bottom"] + 1)
    }
    key_counts = Counter(
        g[r][c]
        for r in range(len(g))
        for c in range(len(g[0]))
        if g[r][c] != 0 and (r, c) not in covered
    )
    if not key_counts:
        raise ValueError("no legend cells found")
    selected: list[dict[str, int]] = []
    by_color: dict[int, list[dict[str, int]]] = {}
    for color, rank in sorted(key_counts.items()):
        candidates = [rod for rod in rods if rod["endpoint"] == color]
        candidates.sort(key=lambda rod: (-rod["length"], rod["top"], rod["col"]))
        if not 1 <= rank <= len(candidates):
            raise ValueError(f"legend rank {rank} has only {len(candidates)} rods for color {color}")
        by_color[color] = [dict(rod) for rod in candidates]
        chosen = dict(candidates[rank - 1])
        chosen["rank"] = rank
        selected.append(chosen)
    if not selected:
        raise ValueError("legend selects no rods")
    return {
        "grid": g,
        "rods": [dict(rod) for rod in rods],
        "key_counts": dict(sorted(key_counts.items())),
        "by_color": by_color,
        "selected": selected,
    }


def solve(grid: Any, finish: str = "rank_only") -> Grid:
    if finish not in {"rank_only", "highlight_longest_selected"}:
        raise ValueError("finish must be rank_only or highlight_longest_selected")
    info = analyze(grid)
    out = [row[:] for row in info["grid"]]
    for rod in info["selected"]:
        for r in range(rod["top"] + 1, rod["bottom"]):
            out[r][rod["col"]] = rod["endpoint"]
    if finish == "highlight_longest_selected":
        winner = max(info["selected"], key=lambda rod: (rod["length"], -rod["top"], -rod["col"]))
        if sum(rod["length"] == winner["length"] for rod in info["selected"]) != 1:
            raise ValueError("alternate setting requires a unique longest selected rod")
        for r in range(winner["top"], winner["bottom"] + 1):
            out[r][winner["col"]] = 9
    return out
