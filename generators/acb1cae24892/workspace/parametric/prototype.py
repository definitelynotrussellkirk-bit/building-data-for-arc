"""Matched-input outline construction and enclosed-region finishing family."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import hashlib
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ("outline_only", "fill_largest_hole")
_DEMOS = ((8, 10), (9, 12), (12, 14), (14, 16), (18, 20), (20, 22))
_QUERIES = ((10, 12), (16, 18), (24, 26), (30, 30))


def _read(name):
    return (HOME / name).read_text(encoding="utf-8")


def program_for(mode):
    if type(mode) is not str or mode not in MODES:
        raise ValueError("finish_mode is not declared")
    return _read("canonical.rkt" if mode == "outline_only" else "fill_largest_hole.rkt")


def validate_settings(settings):
    if type(settings) is not dict or set(settings) != {"finish_mode"}:
        raise ValueError("settings must contain exactly finish_mode")
    mode = settings["finish_mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("finish_mode is not declared")
    return {"finish_mode": mode}


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}")
    return value


def _rng(seed, split, slot):
    raw = hashlib.sha256(f"acb-parametric-v1:{seed}:{split}:{slot}".encode()).digest()
    return random.Random(int.from_bytes(raw[:8], "big"))


def _outline(grid):
    h, w = len(grid), len(grid[0])
    out = [[0] * w for _ in range(h)]
    colors = []
    for row in grid:
        for value in row:
            if value and value not in colors:
                colors.append(value)
    for color in colors:
        pts = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        if len(pts) != 2:
            continue
        (r0, c0), (r1, c1) = pts
        lo_r, hi_r = sorted((r0, r1)); lo_c, hi_c = sorted((c0, c1))
        for r in range(lo_r, hi_r + 1):
            for c in range(lo_c, hi_c + 1):
                if r in (lo_r, hi_r) or c in (lo_c, hi_c):
                    out[r][c] = color
    return out


def _zero_regions(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 0}
    regions = []
    while remaining:
        start = min(remaining); remaining.remove(start)
        region = {start}; todo = deque([start])
        while todo:
            r, c = todo.popleft()
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in remaining:
                    remaining.remove(q); region.add(q); todo.append(q)
        regions.append(region)
    return regions


def _holes(outlined):
    h, w = len(outlined), len(outlined[0])
    result = []
    for cells in _zero_regions(outlined):
        if any(r in (0, h - 1) or c in (0, w - 1) for r, c in cells):
            continue
        neighbors = set()
        for r, c in cells:
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= rr < h and 0 <= cc < w and outlined[rr][cc] != 0:
                    neighbors.add(outlined[rr][cc])
        if len(neighbors) != 1:
            raise ValueError(f"hole must have one border color, got {neighbors}")
        result.append((cells, next(iter(neighbors))))
    if len(result) < 2:
        raise ValueError(f"expected at least two enclosed regions, found {len(result)}")
    return result


def _fill_selected(grid, *, largest):
    outlined = _outline(grid)
    holes = _holes(outlined)
    cells, color = (max if largest else min)(holes, key=lambda item: len(item[0]))
    out = deepcopy(outlined)
    for r, c in cells:
        out[r][c] = color
    return out


def output_for(grid, mode):
    if mode == "outline_only":
        return _outline(grid)
    if mode == "fill_largest_hole":
        return _fill_selected(grid, largest=True)
    raise ValueError("unknown finish_mode")


def _build(seed, slot, dims, *, split):
    h, w = dims
    rng = _rng(seed, split, slot)
    grid = [[0] * w for _ in range(h)]
    colors = rng.sample(range(1, 10), 2)
    gap = 2 if w < 16 else 3
    left_c1 = max(3, w // 2 - gap)
    right_c0 = min(w - 4, w // 2 + gap - 1)
    small_margin = 2 if h < 16 else 4
    full_rows = (0, h - 1)
    small_rows = (small_margin, h - 1 - small_margin)
    if small_rows[1] - small_rows[0] < 3:
        small_rows = (2, h - 3)
    large_left = slot % 2 == 0
    rects = [
        (full_rows if large_left else small_rows, (0, left_c1), colors[0]),
        (small_rows if large_left else full_rows, (right_c0, w - 1), colors[1]),
    ]
    for (r0, r1), (c0, c1), color in rects:
        if r1 - r0 < 2 or c1 - c0 < 2:
            raise RuntimeError("rectangle cannot enclose a region")
        grid[r0][c0] = color
        grid[r1][c1] = color
    info = analyze_input(grid)
    if info["largest_hole_size"] == info["smallest_hole_size"]:
        raise RuntimeError("hole sizes must distinguish the finish rule")
    if output_for(grid, "outline_only") == output_for(grid, "fill_largest_hole"):
        raise RuntimeError("settings must disagree")
    return grid


def select_inputs(seed, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    return {
        "train": [{"input": _build(seed, i, _DEMOS[i], split="demo")} for i in range(demos)],
        "test": [{"input": _build(seed, i, _QUERIES[i], split="query")} for i in range(queries)],
    }


def analyze_input(grid):
    holes = _holes(_outline(grid))
    sizes = sorted(len(cells) for cells, _ in holes)
    return {"hole_count": len(holes), "smallest_hole_size": sizes[0],
            "largest_hole_size": sizes[-1]}


def _fill_side(grid, side):
    outlined = _outline(grid)
    holes = _holes(outlined)
    chosen = min(holes, key=lambda item: min(c for _, c in item[0])) if side == "left" else max(holes, key=lambda item: max(c for _, c in item[0]))
    out = deepcopy(outlined)
    for r, c in chosen[0]:
        out[r][c] = chosen[1]
    return out


def _fill_all(grid):
    outlined = _outline(grid); out = deepcopy(outlined)
    for cells, color in _holes(outlined):
        for r, c in cells: out[r][c] = color
    return out


def _wrong_outputs(grid, chosen):
    canonical = output_for(grid, "outline_only")
    alternate = output_for(grid, "fill_largest_hole")
    return {
        "opposite_setting": alternate if chosen == "outline_only" else canonical,
        "fill_smallest_hole": _fill_selected(grid, largest=False),
        "fill_all_holes": _fill_all(grid),
        "fill_fixed_left": _fill_side(grid, "left"),
        "fill_fixed_right": _fill_side(grid, "right"),
    }


def assess_demos(demos, chosen):
    if chosen not in MODES:
        raise ValueError("unknown finish_mode")
    settings = [m for m in MODES if all(output_for(p["input"], m) == p["output"] for p in demos)]
    names = list(_wrong_outputs(demos[0]["input"], chosen))
    survivors = [n for n in names if all(_wrong_outputs(p["input"], chosen)[n] == p["output"] for p in demos)]
    return {"demonstrations": len(demos), "setting_survivors": settings,
            "harmful_shortcut_survivors": survivors, "rivals_tested": len(names)}


def generate_episode(seed, mode, demos=2, queries=4):
    if mode not in MODES:
        raise ValueError("unknown finish_mode")
    selected = select_inputs(seed, demos, queries)
    return {"program_solution": program_for(mode),
            "train": [{"input": deepcopy(p["input"]), "output": output_for(p["input"], mode)} for p in selected["train"]],
            "test": [{"input": deepcopy(p["input"]), "output": output_for(p["input"], mode)} for p in selected["test"]]}


def public_turn(episode, query_index):
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {"train": deepcopy(episode["train"]),
            "test": [{"input": deepcopy(episode["test"][query_index]["input"])}]}


def causal_case(grid):
    info = analyze_input(grid)
    return {"input": deepcopy(grid),
            "settings": {"finish_mode": "fill_largest_hole"},
            "intermediate_value": info,
            "program": program_for("fill_largest_hole"),
            "output": output_for(grid, "fill_largest_hole"),
            "counterfactual_program": _read("fill_smallest_hole_counterfactual.rkt"),
            "counterfactual_output": _fill_selected(grid, largest=False),
            "ablation": "wrong_intermediate"}
