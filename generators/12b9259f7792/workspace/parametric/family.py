"""Native two-setting family for 12b9259f7792.

``all_nearest`` is the byte-exact canonical rule. ``dominant_assignment``
first performs the canonical nearest-marker recoloring, then aggregates the
assigned blob area by marker color and retains only the uniquely largest group.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import math
from pathlib import Path
import random
from typing import Any, Callable

TASK_ID = "12b9259f7792"
MODES = ("all_nearest", "dominant_assignment")
DEFAULT_MODE = "all_nearest"
HERE = Path(__file__).resolve().parent


def _strict_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: Any) -> str:
    mode = _strict_settings(settings)
    name = "canonical.rkt" if mode == "all_nearest" else "dominant_assignment.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}|nearest-family-v1".encode()).digest()
    return random.Random(int.from_bytes(raw[:16], "big"))


def _components(grid: list[list[int]], color: int = 5) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            for rr, cc in queue:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = rr + dr, cc + dc
                    if 0 <= nxt[0] < h and 0 <= nxt[1] < w and nxt not in seen and grid[nxt[0]][nxt[1]] == color:
                        seen.add(nxt)
                        queue.append(nxt)
            result.append(sorted(cells))
    return sorted(result, key=lambda cells: cells[0])


def _shape(rng: random.Random, size: int) -> list[tuple[int, int]]:
    cells = {(0, 0)}
    while len(cells) < size:
        r, c = rng.choice(sorted(cells))
        dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
        cells.add((r + dr, c + dc))
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _nearest(markers: list[tuple[int, int, int]], cells: list[tuple[int, int]], *, euclidean=False):
    ranked = []
    for mr, mc, color in markers:
        if euclidean:
            distance = min(math.hypot(r - mr, c - mc) for r, c in cells)
        else:
            distance = min(abs(r - mr) + abs(c - mc) for r, c in cells)
        ranked.append((distance, color))
    ranked.sort()
    if len(ranked) > 1 and abs(ranked[0][0] - ranked[1][0]) < 1e-9:
        raise ValueError("nearest-marker tie")
    return ranked[0]


def _place_blob(grid, markers, occupied, size, target_color, rng, *, boundary=False):
    h, w = len(grid), len(grid[0])
    target = next((r, c) for r, c, color in markers if color == target_color)
    candidates = []
    for _ in range(1200):
        shape = _shape(rng, size)
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        if boundary:
            side = rng.randrange(4)
            if side == 0:
                top, left = 0, rng.randrange(max(1, w - sw + 1))
            elif side == 1:
                top, left = h - sh, rng.randrange(max(1, w - sw + 1))
            elif side == 2:
                top, left = rng.randrange(max(1, h - sh + 1)), 0
            else:
                top, left = rng.randrange(max(1, h - sh + 1)), w - sw
        else:
            top = rng.randrange(max(1, h - sh + 1))
            left = rng.randrange(max(1, w - sw + 1))
        cells = [(top + r, left + c) for r, c in shape]
        if any(cell in occupied for cell in cells):
            continue
        if any(abs(r - mr) + abs(c - mc) <= 1 for r, c in cells for mr, mc, _ in markers):
            continue
        if any((r + dr, c + dc) in occupied and grid[r + dr][c + dc] == 5
               for r, c in cells for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if 0 <= r + dr < h and 0 <= c + dc < w):
            continue
        try:
            distance, color = _nearest(markers, cells)
        except ValueError:
            continue
        if color != target_color:
            continue
        score = distance + abs(sum(r for r, _ in cells) / len(cells) - target[0]) * 0.01
        candidates.append((score, cells))
    if not candidates:
        raise ValueError(f"could not place size-{size} blob for marker {target_color}")
    candidates.sort(key=lambda item: item[0])
    cells = rng.choice(candidates[: min(25, len(candidates))])[1]
    for r, c in cells:
        grid[r][c] = 5
        occupied.add((r, c))
    return cells


def _special_scene(seed: int, split: str) -> list[list[int]]:
    rng = _rng(seed, split, 0)
    h, w = 15, 17
    colors = rng.sample([1, 2, 3, 4], 3)
    markers = [(8, 0, colors[0]), (5, 2, colors[1]), (0, 16, colors[2])]
    grid = [[0] * w for _ in range(h)]
    occupied = set()
    for r, c, color in markers:
        grid[r][c] = color
        occupied.add((r, c))
    # L1 chooses colors[0], while L2 chooses colors[1].
    special = [(8, 5), (8, 6)]
    assert _nearest(markers, special)[1] == colors[0]
    assert _nearest(markers, special, euclidean=True)[1] == colors[1]
    for r, c in special:
        grid[r][c] = 5
        occupied.add((r, c))
    plans = {
        colors[0]: [5],       # total 7; largest individual blob is here
        colors[1]: [4, 4],    # total 8; dominant total winner
        colors[2]: [2, 2],    # total 4
    }
    for color in colors:
        for size in plans[color]:
            _place_blob(grid, markers, occupied, size, color, rng)
    info = analyze(grid)
    if info["winner_color"] != colors[1]:
        raise AssertionError(info)
    return grid


def _ordinary_scene(seed: int, split: str, index: int) -> list[list[int]]:
    rng = _rng(seed, split, index)
    h = 14 + rng.randrange(3)
    w = 16 + rng.randrange(3)
    colors = rng.sample([1, 2, 3, 4], 3)
    jitter = rng.randrange(2)
    markers = [(1 + jitter, 1, colors[0]), (1, w - 2 - jitter, colors[1]), (h - 2, w // 2, colors[2])]
    winner_index = (index + (0 if split == "train" else 1)) % 3
    decoy_index = (winner_index + 1) % 3
    other_index = (winner_index + 2) % 3
    plans = {
        colors[winner_index]: [4, 4],
        colors[decoy_index]: [5, 2],
        colors[other_index]: [2, 2],
    }
    grid = [[0] * w for _ in range(h)]
    occupied = set()
    for r, c, color in markers:
        grid[r][c] = color
        occupied.add((r, c))
    for color in colors:
        for size in plans[color]:
            _place_blob(grid, markers, occupied, size, color, rng, boundary=False)
    return grid


def _stress_scene(seed: int) -> list[list[int]]:
    rng = _rng(seed, "test", 3)
    h = w = 30
    colors = rng.sample([1, 2, 3, 4], 4)
    markers = [(1, 1, colors[0]), (1, 28, colors[1]), (28, 1, colors[2]), (28, 28, colors[3])]
    winner_index = seed % 4
    plans_by_role = ([6, 5, 5], [8, 7], [5, 4, 3], [4, 3, 2])
    roles = [None] * 4
    roles[winner_index] = plans_by_role[0]
    roles[(winner_index + 1) % 4] = plans_by_role[1]
    roles[(winner_index + 2) % 4] = plans_by_role[2]
    roles[(winner_index + 3) % 4] = plans_by_role[3]
    grid = [[0] * w for _ in range(h)]
    occupied = set()
    for r, c, color in markers:
        grid[r][c] = color
        occupied.add((r, c))
    first = True
    for color, sizes in zip(colors, roles):
        for size in sizes:
            _place_blob(grid, markers, occupied, size, color, rng, boundary=first)
            first = False
    return grid


@lru_cache(maxsize=512)
def _scene_cached(seed: int, split: str, index: int) -> tuple[tuple[int, ...], ...]:
    if split == "test" and index == 3:
        grid = _stress_scene(seed)
    elif index == 0:
        grid = _special_scene(seed, split)
    else:
        grid = _ordinary_scene(seed, split, index)
    analyze(grid)  # full construction validation before a scene enters the cache
    return tuple(tuple(row) for row in grid)


def scene(seed: int, split: str, index: int) -> list[list[int]]:
    _strict_int("seed", seed, 0, 2**63 - 1)
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    limit = 6 if split == "train" else 4
    _strict_int("index", index, 0, limit - 1)
    return [list(row) for row in _scene_cached(seed, split, index)]


def analyze(grid: Any) -> dict[str, Any]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be nonempty")
    w = len(grid[0])
    if any(type(row) is not list or len(row) != w or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact ARC colors")
    markers = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v in (1, 2, 3, 4)]
    if not 2 <= len(markers) <= 4 or len({v for _, _, v in markers}) != len(markers):
        raise ValueError("need 2..4 distinct marker colors")
    blobs = []
    totals = {color: 0 for _, _, color in markers}
    for cells in _components(grid):
        distance, color = _nearest(markers, cells)
        euclidean_color = _nearest(markers, cells, euclidean=True)[1]
        blobs.append({"cells": cells, "area": len(cells), "assigned_color": color,
                      "manhattan_distance": distance, "euclidean_color": euclidean_color})
        totals[color] += len(cells)
    if len(blobs) < 3 or any(total <= 0 for total in totals.values()):
        raise ValueError("each marker needs assigned blobs")
    ordered = sorted(totals, key=lambda color: (-totals[color], color))
    if len(ordered) > 1 and totals[ordered[0]] == totals[ordered[1]]:
        raise ValueError("dominant assignment total must be unique")
    return {
        "markers": [{"row": r, "col": c, "color": color} for r, c, color in markers],
        "blobs": blobs,
        "assigned_area_by_color": totals,
        "winner_color": ordered[0],
    }


def solve_all_nearest(grid: Any, *, euclidean=False) -> list[list[int]]:
    source = deepcopy(grid)
    info = analyze(source)
    markers = [(m["row"], m["col"], m["color"]) for m in info["markers"]]
    output = deepcopy(source)
    for blob in info["blobs"]:
        color = _nearest(markers, blob["cells"], euclidean=euclidean)[1]
        for r, c in blob["cells"]:
            output[r][c] = color
    return output


def _filter_to_color(grid: Any, winner: int) -> list[list[int]]:
    info = analyze(grid)
    marker_positions = {(m["row"], m["col"]) for m in info["markers"]}
    assigned = solve_all_nearest(grid)
    output = deepcopy(assigned)
    for r, row in enumerate(output):
        for c, value in enumerate(row):
            if (r, c) not in marker_positions and value in (1, 2, 3, 4) and value != winner:
                output[r][c] = 0
    return output


def solve(grid: Any, mode: str) -> list[list[int]]:
    if mode == "all_nearest":
        return solve_all_nearest(grid)
    if mode == "dominant_assignment":
        info = analyze(grid)
        return _filter_to_color(grid, info["winner_color"])
    raise ValueError(f"unknown mode: {mode}")


def solve_skip_assignment(grid: Any) -> list[list[int]]:
    """Counterfactual B(g): without A, no assigned colored blob area exists."""
    return deepcopy(grid)


def _first_two_only(grid):
    info = analyze(grid)
    output = deepcopy(grid)
    markers = [(m["row"], m["col"], m["color"]) for m in info["markers"]]
    for blob in info["blobs"][:2]:
        color = _nearest(markers, blob["cells"])[1]
        for r, c in blob["cells"]:
            output[r][c] = color
    return output


def _all_first_marker(grid):
    info = analyze(grid)
    winner = info["markers"][0]["color"]
    output = deepcopy(grid)
    for blob in info["blobs"]:
        for r, c in blob["cells"]:
            output[r][c] = winner
    return output


def _largest_single_group(grid):
    info = analyze(grid)
    largest = max(info["blobs"], key=lambda blob: (blob["area"], -blob["assigned_color"]))
    return _filter_to_color(grid, largest["assigned_color"])


def _smallest_total_group(grid):
    info = analyze(grid)
    color = min(info["assigned_area_by_color"], key=lambda c: (info["assigned_area_by_color"][c], c))
    return _filter_to_color(grid, color)


def audit_rivals(mode: str) -> dict[str, Callable[[Any], list[list[int]]]]:
    if mode == "all_nearest":
        return {
            "euclidean_distance": lambda grid: solve_all_nearest(grid, euclidean=True),
            "first_two_components_only": _first_two_only,
            "all_blobs_use_first_marker": _all_first_marker,
        }
    if mode == "dominant_assignment":
        return {
            "keep_all_assigned_blobs": solve_all_nearest,
            "winner_by_largest_single_blob": _largest_single_group,
            "winner_by_smallest_total": _smallest_total_group,
        }
    raise ValueError(mode)


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _strict_int("seed", seed, 0, 2**63 - 1)
    demos = _strict_int("demos", demos, 2, 6)
    queries = _strict_int("queries", queries, 1, 4)
    mode = _strict_settings(settings)
    train = []
    for i in range(demos):
        grid = scene(seed, "train", i)
        train.append({"input": grid, "output": solve(grid, mode)})
    test = []
    for i in range(queries):
        grid = scene(seed, "test", i)
        test.append({"input": grid, "output": solve(grid, mode)})
    return {"train": train, "test": test, "program_solution": program({"mode": mode})}
