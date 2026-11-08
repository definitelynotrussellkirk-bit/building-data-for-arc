"""Continue a nozzle's stepped walls and fill its band with parallel shadows."""
from __future__ import annotations
from collections import Counter
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path
import random

TASK_ID = "public_eval_b9e38dc0"
CANONICAL = Path(__file__).with_name("canonical.rkt").read_text()
PARAMETERS = {"obstacle_mode": ["opaque", "transparent"]}
DEFAULT = {"obstacle_mode": "opaque"}
LIMITS = {"demos": [2, 6], "queries": [1, 4]}
assert CANONICAL.count("(opaque #t)") == 1
ALTERNATIVE = CANONICAL.replace("(opaque #t)", "(opaque #f)", 1)
EIGHT = tuple((dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if dr or dc)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {"obstacle_mode"}
            or type(settings["obstacle_mode"]) is not str
            or settings["obstacle_mode"] not in PARAMETERS["obstacle_mode"]):
        raise ValueError("settings must be exactly obstacle_mode=opaque or transparent")
    return settings["obstacle_mode"]


def program(settings):
    return CANONICAL if _setting(settings) == "opaque" else ALTERNATIVE


def _grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0]) for row in grid)
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
        raise ValueError("need an exact-integer rectangular ARC grid with axes 1..30")
    return [row[:] for row in grid]


def _rotate(grid, turns=1):
    for _ in range(turns % 4):
        grid = [list(row) for row in zip(*grid[::-1])]
    return grid


def _wall(grid, wall):
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == wall}
    adjacency = {p: {(p[0] + dr, p[1] + dc) for dr, dc in EIGHT} & cells for p in cells}
    ends = sorted(p for p in cells if len(adjacency[p]) == 1)
    if len(ends) != 2:
        raise ValueError("the wall needs exactly two eight-neighbor endpoints")
    reached, pending = {ends[0]}, [ends[0]]
    while pending:
        for p in adjacency[pending.pop()] - reached:
            reached.add(p); pending.append(p)
    if reached != cells:
        raise ValueError("the wall must be one eight-connected component")
    tangent = [tuple(a - b for a, b in zip(p, next(iter(adjacency[p])))) for p in ends]
    dy, dx = (sum(t[i] for t in tangent) for i in (0, 1))
    if abs(dy) == abs(dx):
        raise ValueError("endpoint tangents must identify one cardinal flow axis")
    flow = ((1 if dy > 0 else -1), 0) if abs(dy) > abs(dx) else (0, (1 if dx > 0 else -1))
    return cells, ends, flow


def plan(grid, obstacle_mode="opaque"):
    _setting({"obstacle_mode": obstacle_mode})
    grid = _grid(grid)
    ranked = Counter(v for row in grid for v in row).most_common()
    if len(ranked) < 3 or not ranked[0][1] > ranked[1][1] > ranked[2][1]:
        raise ValueError("need unique modal background and unique next-most-frequent wall color")
    background, wall_color = ranked[0][0], ranked[1][0]
    _, _, flow = _wall(grid, wall_color)
    turns = {(1, 0): 0, (0, 1): 1, (-1, 0): 2, (0, -1): 3}[flow]
    base = _rotate(grid, turns)
    cells, ends, normalized_flow = _wall(base, wall_color)
    if normalized_flow != (1, 0):
        raise ValueError("normalization did not preserve the inferred flow")
    ends.sort(key=lambda p: p[1])
    if ends[0][1] >= ends[1][1]:
        raise ValueError("mouth tips must identify separate left and right walls")
    height, width = len(base), len(base[0])
    by_row = {r: sorted(c for y, c in cells if y == r) for r in range(height)}
    cap_row = min(r for r, c in cells)
    cap = by_row[cap_row]
    if len(cap) < 3 or cap != list(range(cap[0], cap[-1] + 1)):
        raise ValueError("the rear cap must be one contiguous run of at least three cells")
    records = []
    for side, (row, col) in zip((-1, 1), ends):
        start = row
        while (start - 1, col) in cells:
            start -= 1
        stride = row - start + 1
        inner_end = start - 1
        if (inner_end, col - side) not in cells:
            raise ValueError("the terminal run needs an adjacent inward predecessor")
        inner_start = inner_end
        while (inner_start - 1, col - side) in cells:
            inner_start -= 1
        if inner_end - inner_start + 1 != stride:
            raise ValueError("partial terminal runs or unequal consecutive run lengths are outside this grammar")
        records.append({"endpoint": (row, col), "side": side, "stride": stride, "run_start": start})
    if records[0]["stride"] != records[1]["stride"]:
        raise ValueError("both flaring walls must share their forward stride")

    def edge_at(row, record):
        end_row, end_col = record["endpoint"]
        if row > end_row:
            return end_col + record["side"] * ((row - end_row + record["stride"] - 1) // record["stride"])
        columns = by_row[row]
        if not columns:
            raise ValueError("wall rows before the tips may not be absent")
        return columns[0] if record["side"] == -1 else columns[-1]

    interior, virtual, bounds = set(), set(), []
    previous = None
    for row in range(cap_row + 1, height):
        left, right = (edge_at(row, record) for record in records)
        if left >= right:
            raise ValueError("wall boundaries may not cross")
        columns = by_row[row]
        runs = sum(index == 0 or col != columns[index - 1] + 1 for index, col in enumerate(columns))
        expected_runs = sum(row <= record["endpoint"][0] for record in records)
        if runs != expected_runs:
            raise ValueError("each row needs its two side-wall runs, except after a clipped or completed tip")
        for record, col in zip(records, (left, right)):
            if row > record["endpoint"][0] and 0 <= col < width:
                virtual.add((row, col))
        current = {col for col in range(max(0, left + 1), min(width, right)) if (row, col) not in cells}
        if not current or (previous is not None and not current & previous):
            raise ValueError("the interior must remain nonempty and four-connected between rows")
        interior.update((row, col) for col in current)
        previous = current
        bounds.append((row, left, right))
    if not interior:
        raise ValueError("a nonempty interior must lie ahead of the rear cap")
    markers = sorted((r, c, base[r][c]) for r, c in interior if base[r][c] not in (background, wall_color))
    if not markers:
        raise ValueError("the interior needs a dye marker")
    first_row = markers[0][0]
    dyes = {color for r, c, color in markers if r == first_row}
    if len(dyes) != 1:
        raise ValueError("the earliest interior marker row must identify exactly one dye color")
    fill_color = dyes.pop()
    blockers = {(r, c) for r, c, color in markers if color != fill_color}
    frontiers = [min((r for r, x in blockers if x == c), default=height) for c in range(width)]
    shadow = {(r, c) for r, c in interior if r > frontiers[c]} if obstacle_mode == "opaque" else set()
    return {"grid": base, "turns": turns, "flow": flow, "background": background,
            "wall_color": wall_color, "fill_color": fill_color, "wall_cells": cells,
            "endpoints": records, "cap_row": cap_row, "bounds": bounds,
            "interior": interior, "virtual_walls": virtual, "blockers": blockers,
            "frontiers": frontiers, "shadow": shadow}


def solve(grid, obstacle_mode="opaque"):
    state = plan(grid, obstacle_mode)
    out = [row[:] for row in state["grid"]]
    for r, c in state["interior"] - state["shadow"]:
        if out[r][c] == state["background"]:
            out[r][c] = state["fill_color"]
    return _rotate(out, -state["turns"])


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _rng(seed, stream):
    digest = hashlib.sha256(f"{TASK_ID}:{seed}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest, "big"))


@lru_cache(maxsize=1)
def _templates():
    path = Path(__file__).with_name("scene_templates.py")
    spec = importlib.util.spec_from_file_location("nozzle_scene_templates", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _palette(rng, avoid_roles=None):
    if avoid_roles is None:
        return rng.sample(range(10), 10)
    choices = [(b, w, d) for b in range(10) for w in range(10) for d in range(10)
               if len({b, w, d}) == 3 and all(a != old for a, old in zip((b, w, d), avoid_roles))]
    chosen = list(rng.choice(choices))
    return chosen + rng.sample([v for v in range(10) if v not in chosen], 7)


def _augment(grid, rng, palette, avoid_turn=None):
    grid = [[palette[v] for v in row] for row in grid]
    if rng.randrange(2):
        grid = [row[::-1] for row in grid]
    turns = rng.randrange(4) if avoid_turn is None else rng.choice([turn for turn in range(4) if turn != avoid_turn])
    return _rotate(grid, turns), turns


def input_bank(seed):
    _integer(seed, 0, 2**63 - 1, "seed")
    demos, queries = _templates().input_templates(seed)
    d, q = _rng(seed, "demonstrations"), _rng(seed, "queries")
    output, first_palette, first_turn = [], None, None
    for index, grid in enumerate(demos):
        palette = _palette(d, first_palette[:3] if index == 1 else None)
        if index == 0:
            first_palette = palette
        augmented, turn = _augment(grid, d, palette, first_turn if index == 1 else None)
        if index == 0:
            first_turn = turn
        output.append(augmented)
    queries = [_augment(grid, q, _palette(q))[0] for grid in queries]
    q.shuffle(queries)
    return output, queries


def generate(seed, settings=None, demos=3, queries=4):
    _integer(seed, 0, 2**63 - 1, "seed")
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    if settings is None:
        settings = {"obstacle_mode": _rng(seed, "settings").choice(PARAMETERS["obstacle_mode"])}
    mode = _setting(settings)
    train, test = input_bank(seed)
    def pairs(grids):
        return [{"input": grid, "output": solve(grid, mode)} for grid in grids]
    return {"train": pairs(train[:demos]), "test": pairs(test[:queries]), "program_solution": program(settings)}
