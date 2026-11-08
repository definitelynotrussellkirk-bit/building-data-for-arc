"""Native two-setting guarded-diagonal episodes for 7195f447bb20."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

TASK_ID = "7195f447bb20"
HOME = Path(__file__).resolve().parent
MODES = ("canonical", "cascade")
DEMO_PROFILES = ((12, 13), (16, 17), (20, 21), (14, 19), (23, 24), (18, 22))
QUERY_PROFILES = ((15, 16), (21, 24), (27, 29), (30, 30))


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def settings_value(settings):
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly mode")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("mode must be canonical or cascade")
    return {"mode": mode}


def program(settings):
    mode = settings_value(settings)["mode"]
    return (HOME / "rules" / ("canonical.rkt" if mode == "canonical" else "cascade.rkt")).read_text(
        encoding="utf-8"
    )


def strict_grid(grid):
    if (type(grid) is not list or not grid or len(grid) > 30
            or type(grid[0]) is not list or not grid[0] or len(grid[0]) > 30):
        raise ValueError("grid must be a nonempty 1..30 rectangle")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or cell not in (0, 4) for cell in row)
           for row in grid):
        raise ValueError("grid cells must be exact 0 or 4 integers")
    return grid


def _eligible_centers(grid):
    strict_grid(grid)
    h, w = len(grid), len(grid[0])
    centers = []
    for r in range(h - 2):
        for c in range(w - 2):
            predecessor = r > 0 and c > 0 and grid[r - 1][c - 1] == 4
            successor = r + 3 < h and c + 3 < w and grid[r + 3][c + 3] == 4
            if (grid[r][c] == 4 and grid[r + 1][c + 1] == 0
                    and grid[r + 2][c + 2] == 4 and not predecessor and not successor):
                centers.append((r + 1, c + 1))
    return centers


def guard_witness(grid):
    strict_grid(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h - 2):
        for c in range(w - 2):
            if not (grid[r][c] == 4 and grid[r + 1][c + 1] == 0
                    and grid[r + 2][c + 2] == 4):
                continue
            predecessor = r > 0 and c > 0 and grid[r - 1][c - 1] == 4
            successor = r + 3 < h and c + 3 < w and grid[r + 3][c + 3] == 4
            if predecessor or successor:
                return True
    return False


def python_oracle(grid, settings):
    mode = settings_value(settings)["mode"]
    strict_grid(grid)
    source = deepcopy(grid)
    after_a = deepcopy(source)
    centers = _eligible_centers(source)
    for r, c in centers:
        after_a[r][c] = 4
    if mode == "canonical":
        return after_a
    result = deepcopy(after_a)
    width = len(source[0])
    for r, c in centers:
        if c + 2 < width and after_a[r][c + 1] == 0 and after_a[r][c + 2] == 4:
            result[r][c + 1] = 4
    return result


def _rng(seed, split, index):
    key = json.dumps([TASK_ID, seed, split, index], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(key.encode()).digest(), "big"))


def _tile_anchors(h, w):
    return [(r, c) for r in range(1, h - 3, 5) for c in range(1, w - 4, 6)]


def _build_scene(h, w, rng):
    grid = [[0] * w for _ in range(h)]
    candidates = _tile_anchors(h, w)
    rng.shuffle(candidates)
    target = max(2, min(10, (h * w) // 75))
    selected = []
    used_diagonals = set()
    for r, c in candidates:
        diagonals = {c - r, c - r + 2}
        if used_diagonals & diagonals:
            continue
        selected.append((r, c))
        used_diagonals.update(diagonals)
        if len(selected) == target:
            break
    if len(selected) < 2:
        raise ValueError("profile cannot place enough cascade motifs")
    for r, c in selected:
        grid[r][c] = 4
        grid[r + 2][c + 2] = 4
        grid[r + 1][c + 3] = 4

    guard = next(((r, c) for r, c in candidates
                  if (r, c) not in selected and (c - r) not in used_diagonals), None)
    if guard is None:
        raise ValueError("profile cannot place a guarded near-miss")
    r, c = guard
    grid[r - 1][c - 1] = 4
    grid[r][c] = 4
    grid[r + 2][c + 2] = 4

    centers = _eligible_centers(grid)
    if len(centers) != len(selected) or not guard_witness(grid):
        raise AssertionError("constructed scene lost its intended motif census")
    canonical = python_oracle(grid, {"mode": "canonical"})
    cascade = python_oracle(grid, {"mode": "cascade"})
    if canonical == cascade:
        raise AssertionError("constructed scene failed to distinguish settings")
    return grid


def sample_input(seed, split, index):
    _integer(seed, 0, 2**63 - 1, "seed")
    profiles = DEMO_PROFILES if split == "demo" else QUERY_PROFILES if split == "query" else None
    if profiles is None:
        raise ValueError("split must be demo or query")
    _integer(index, 0, len(profiles) - 1, "index")
    h, w = profiles[index]
    return _build_scene(h, w, _rng(seed, split, index))


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63 - 1, "seed")
    settings = settings_value(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    train = []
    for index in range(demos):
        grid = sample_input(seed, "demo", index)
        train.append({"input": grid, "output": python_oracle(grid, settings)})
    test = []
    for index in range(queries):
        grid = sample_input(seed, "query", index)
        test.append({"input": grid, "output": python_oracle(grid, settings)})
    return {"train": train, "test": test, "program_solution": program(settings)}
