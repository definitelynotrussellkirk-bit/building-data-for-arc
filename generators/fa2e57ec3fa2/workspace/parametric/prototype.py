"""Native two-setting family for rightward rays and first-hit mirror turns.

``stop`` is the exact canonical rule. ``mirror_turn`` traces each emitter to
its first obstacle; a color-6 mirror turns the ray upward and a color-8 mirror
turns it downward.  The mirror-derived direction is an input-dependent
intermediate consumed by the second, vertical trace.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random

TASK_ID = "fa2e57ec3fa2"
HERE = Path(__file__).resolve().parent
MODES = ("stop", "mirror_turn")
_DEMO_PROFILES = ((8, 10, 2), (10, 13, 3), (12, 16, 3), (16, 20, 4), (20, 24, 5), (24, 28, 6))
_QUERY_PROFILES = ((9, 12, 3), (15, 18, 4), (22, 25, 6), (30, 30, 8))
_DISTRACTOR_COLORS = (1, 3, 4, 5, 9)


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {"ray_mode"}
            or type(settings["ray_mode"]) is not str
            or settings["ray_mode"] not in MODES):
        raise ValueError("settings must contain exactly a declared ray_mode")
    return settings["ray_mode"]


def program(settings):
    mode = _mode(settings)
    name = "canonical.rkt" if mode == "stop" else "mirror_turn.rkt"
    return (HERE / name).read_text(encoding="utf-8")


def _validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid dimensions must be 1..30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(value) is not int or not 0 <= value <= 9 for value in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors")


def analyze(grid):
    """Return row-major ray traces and the first-hit-derived turn intermediate."""
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    emitters = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not emitters:
        raise ValueError("missing color-2 emitter")
    rays = []
    for r, c in emitters:
        horizontal = []
        cc = c + 1
        while cc < w and grid[r][cc] == 0:
            horizontal.append([r, cc])
            cc += 1
        first_hit = None if cc == w else [r, cc, grid[r][cc]]
        direction = None
        vertical = []
        if first_hit is not None and first_hit[2] in (6, 8):
            dr = -1 if first_hit[2] == 6 else 1
            direction = [dr, 0]
            rr = r + dr
            while 0 <= rr < h and grid[rr][cc] == 0:
                vertical.append([rr, cc])
                rr += dr
        rays.append({
            "emitter": [r, c],
            "horizontal_path": horizontal,
            "first_hit": first_hit,
            "turn_direction": direction,
            "vertical_path": vertical,
        })
    return {"rays": rays}


def solve(grid, settings):
    mode = _mode(settings)
    facts = analyze(grid)
    out = copy.deepcopy(grid)
    for ray in facts["rays"]:
        cells = list(ray["horizontal_path"])
        if mode == "mirror_turn":
            cells.extend(ray["vertical_path"])
        for r, c in cells:
            if out[r][c] == 0:
                out[r][c] = 7
    return out


def _rng(seed, split, index):
    raw = f"fa2e-parametric-v1:{seed}:{split}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(), "big"))


def _scene_rows(height, index, count):
    up_rows = list(range(height - 2, 1, -2))
    down_rows = list(range(1, height - 2, 2))
    up_i = down_i = 0
    rows = []
    colors = []
    for i in range(count):
        color = 6 if (i + index) % 2 == 0 else 8
        if color == 6:
            if up_i >= len(up_rows):
                raise RuntimeError("insufficient upward mirror rows")
            row = up_rows[up_i]
            up_i += 1
        else:
            if down_i >= len(down_rows):
                raise RuntimeError("insufficient downward mirror rows")
            row = down_rows[down_i]
            down_i += 1
        rows.append(row)
        colors.append(color)
    return rows, colors


def _mirror_columns(width, count):
    left, right = 3, width - 2
    if count == 1:
        return [(left + right) // 2]
    columns = [left + (i * (right - left)) // (count - 1) for i in range(count)]
    if len(set(columns)) != count:
        raise RuntimeError("insufficient distinct mirror columns")
    return columns


def scene(seed, split, index):
    if split == "demo":
        _integer(index, 0, 5, "demo index")
        h, w, count = _DEMO_PROFILES[index]
        distractor_count = index + 1
    elif split == "query":
        _integer(index, 0, 3, "query index")
        h, w, count = _QUERY_PROFILES[index]
        distractor_count = (3, 5, 8, 12)[index]
    else:
        raise ValueError("split must be demo or query")
    rng = _rng(seed, split, index)
    rows, mirror_colors = _scene_rows(h, index, count)
    mirror_cols = _mirror_columns(w, count)
    grid = [[0] * w for _ in range(h)]
    protected = set()
    for i, (row, mirror_col, mirror_color) in enumerate(zip(rows, mirror_cols, mirror_colors)):
        emitter_col = i % 2
        if mirror_col <= emitter_col + 1:
            raise RuntimeError("mirror must leave a visible horizontal segment")
        grid[row][emitter_col] = 2
        grid[row][mirror_col] = mirror_color
        protected.add((row, emitter_col))
        protected.add((row, mirror_col))
        protected.update((row, col) for col in range(emitter_col + 1, mirror_col))
        dr = -1 if mirror_color == 6 else 1
        protected.update((rr, mirror_col) for rr in range(row + dr, -1 if dr < 0 else h, dr))
    candidates = [(r, c) for r in range(h) for c in range(w) if (r, c) not in protected]
    rng.shuffle(candidates)
    for n, (r, c) in enumerate(candidates[:distractor_count]):
        grid[r][c] = _DISTRACTOR_COLORS[(n + index + seed) % len(_DISTRACTOR_COLORS)]
    facts = analyze(grid)
    if len(facts["rays"]) != count:
        raise RuntimeError("scene lost an emitter")
    if any(ray["first_hit"] is None or ray["first_hit"][2] not in (6, 8)
           or not ray["vertical_path"] for ray in facts["rays"]):
        raise RuntimeError("scene does not realize every mirror turn")
    return grid


def generate(seed, settings, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    _mode(settings)
    result = {"program_solution": program(settings), "train": [], "test": []}
    for name, split, count in (("train", "demo", demos), ("test", "query", queries)):
        for index in range(count):
            grid = scene(seed, split, index)
            result[name].append({"input": grid, "output": solve(grid, settings)})
    inputs = [repr(pair["input"]) for pair in result["train"] + result["test"]]
    if len(inputs) != len(set(inputs)):
        raise RuntimeError("duplicate input within episode")
    return result
