"""Native matched-input family for direct or 180-degree edit-delta transfer.

The default returns the selected canonical Racket source byte-for-byte.  Both
settings first infer the bbox-aligned cells added from panel A to panel B.  The
canonical setting stamps those relative cells onto panel C; the alternative
rotates that inferred edit frame by 180 degrees before stamping it.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random
from typing import Callable

from reviewer_support import public_challenge_id


TASK_ID = "a80c6418f6bc"
ORIENTATIONS = ("direct", "rotate_180")
_HOME = Path(__file__).resolve().parent
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLORS = tuple(range(1, 9))

# The first two demonstrations are intentionally sufficient: an in-bbox edit
# followed by a two-axis expansion.  Later profiles broaden geometry without
# changing the visible prefix for smaller requested demo counts.
_DEMO_PROFILES = (
    dict(name="demo_within", size=(15, 15), separator=(7, 7), shape=(5, 5),
         delta=((1, 3),), positions=((0, 0), (2, 2), (1, 1))),
    dict(name="demo_expand_both", size=(17, 17), separator=(8, 8), shape=(4, 5),
         delta=((4, 5), (1, 5)), positions=((1, 0), (3, 2), (0, 2))),
    dict(name="demo_expand_right", size=(19, 19), separator=(9, 9), shape=(5, 4),
         delta=((1, 4), (4, 4)), positions=((4, 0), (0, 4), (2, 2))),
    dict(name="demo_expand_down", size=(21, 21), separator=(10, 10), shape=(4, 6),
         delta=((4, 1), (4, 5)), positions=((0, 4), (5, 0), (3, 2))),
    dict(name="demo_within_dense", size=(23, 23), separator=(11, 11), shape=(6, 7),
         delta=((1, 5), (4, 2)), positions=((5, 0), (0, 4), (2, 2))),
    dict(name="demo_expand_both_dense", size=(25, 25), separator=(12, 12), shape=(7, 6),
         delta=((7, 6), (7, 2), (2, 6)), positions=((0, 6), (4, 0), (2, 3))),
)

_QUERY_PROFILES = (
    dict(name="query_within", size=(17, 17), separator=(8, 8), shape=(5, 6),
         delta=((1, 4), (3, 2)), positions=((3, 0), (0, 2), (2, 1))),
    dict(name="query_expand_right", size=(21, 21), separator=(10, 10), shape=(6, 5),
         delta=((0, 5), (4, 5), (5, 5)), positions=((0, 5), (4, 0), (2, 3))),
    dict(name="query_expand_down", size=(25, 25), separator=(12, 12), shape=(7, 6),
         delta=((7, 1), (7, 4)), positions=((5, 0), (0, 6), (3, 2))),
    # A 30x30 cross cannot make four equal quadrants.  The rule itself supports
    # rectangular panels, so this uses a 14/15 split while retaining the same
    # A->B edit inference and C transfer semantics.
    dict(name="query_30x30", size=(30, 30), separator=(14, 14), shape=(10, 11),
         delta=((1, 11), (5, 11), (9, 11)), positions=((0, 0), (4, 3), (5, 2)),
         source_density=0.55, query_density=0.72),
)


def _orientation(settings) -> str:
    if type(settings) is not dict or set(settings) != {"orientation"}:
        raise ValueError("settings must contain exactly orientation")
    value = settings["orientation"]
    if type(value) is not str or value not in ORIENTATIONS:
        raise ValueError("orientation must be direct or rotate_180")
    return value


def _count(name: str, value, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be a literal integer in {low}..{high}")
    return value


def program(settings) -> str:
    orientation = _orientation(settings)
    filename = "canonical.rkt" if orientation == "direct" else "rotate_180.rkt"
    return (_HOME / filename).read_text(encoding="utf-8")


def program_hash(orientation: str) -> str:
    return hashlib.sha256(program({"orientation": orientation}).encode()).hexdigest()


def grid_hash(grid) -> str:
    raw = json.dumps(grid, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _rng(seed: int, split: str, index: int, stream: str) -> random.Random:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    digest = hashlib.sha256(
        f"{TASK_ID}:transfer-orientation:v1:{seed}:{split}:{index}:{stream}".encode()
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def _neighbors(cell, h: int, w: int):
    row, col = cell
    for dr, dc in _DIR4:
        nxt = row + dr, col + dc
        if 0 <= nxt[0] < h and 0 <= nxt[1] < w:
            yield nxt


def _path_to_target(cells, target, allowed, rng):
    queue = list(sorted(cells))
    rng.shuffle(queue)
    parent = {cell: None for cell in queue}
    cursor = 0
    while cursor < len(queue):
        current = queue[cursor]
        cursor += 1
        if current == target:
            path = []
            while current is not None:
                path.append(current)
                current = parent[current]
            return path
        neighbors = [n for n in _neighbors(current, max(r for r, _ in allowed) + 1,
                                            max(c for _, c in allowed) + 1)
                     if n in allowed and n not in parent]
        rng.shuffle(neighbors)
        for nxt in neighbors:
            parent[nxt] = current
            queue.append(nxt)
    raise ValueError("forbidden cells disconnected the profile canvas")


def _shape(h: int, w: int, forbidden, rng: random.Random, density: float):
    forbidden = set(forbidden)
    allowed = {(r, c) for r in range(h) for c in range(w)} - forbidden
    if not allowed:
        raise ValueError("profile has no allowed cells")
    interior = sorted(cell for cell in allowed if 0 < cell[0] < h - 1 and 0 < cell[1] < w - 1)
    cells = {rng.choice(interior or sorted(allowed))}
    boundaries = (
        sorted(cell for cell in allowed if cell[0] == 0),
        sorted(cell for cell in allowed if cell[0] == h - 1),
        sorted(cell for cell in allowed if cell[1] == 0),
        sorted(cell for cell in allowed if cell[1] == w - 1),
    )
    for candidates in boundaries:
        if not candidates:
            raise ValueError("profile forbids an entire bbox side")
        target = rng.choice(candidates)
        cells.update(_path_to_target(cells, target, allowed, rng))
    target_size = max(len(cells), min(len(allowed), round(density * len(allowed))))
    while len(cells) < target_size:
        frontier = sorted({n for cell in cells for n in _neighbors(cell, h, w)
                           if n in allowed and n not in cells})
        if not frontier:
            break
        cells.add(rng.choice(frontier))
    return frozenset(cells)


def _rotate_delta(delta, edit_h: int, edit_w: int):
    return frozenset((edit_h - 1 - row, edit_w - 1 - col) for row, col in delta)


def _panel_info(panel):
    cells = {(r, c) for r, row in enumerate(panel) for c, value in enumerate(row) if value != 0}
    if not cells:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, c0, r1, c1 = min(rows), min(cols), max(rows), max(cols)
    return {
        "origin": (r0, c0),
        "height": r1 - r0 + 1,
        "width": c1 - c0 + 1,
        "cells": cells,
        "relative": frozenset((r - r0, c - c0) for r, c in cells),
        "colors": frozenset(panel[r][c] for r, c in cells),
    }


def _grid_shape(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or not grid
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact ARC integer colors")
    return len(grid), width


def analyze(grid) -> dict:
    h, w = _grid_shape(grid)
    sep_rows = [r for r in range(h) if all(grid[r][c] == 9 for c in range(w))]
    sep_cols = [c for c in range(w) if all(grid[r][c] == 9 for r in range(h))]
    if len(sep_rows) != 1 or len(sep_cols) != 1:
        raise ValueError("expected exactly one full color-9 separator row and column")
    sr, sc = sep_rows[0], sep_cols[0]
    panels = {
        "a": [row[:sc] for row in grid[:sr]],
        "b": [row[sc + 1:] for row in grid[:sr]],
        "c": [row[:sc] for row in grid[sr + 1:]],
        "answer": [row[sc + 1:] for row in grid[sr + 1:]],
    }
    a_info, b_info, c_info = (_panel_info(panels[key]) for key in ("a", "b", "c"))
    if any(value is None for value in (a_info, b_info, c_info)):
        raise ValueError("A, B, and C must be nonempty")
    delta = frozenset(b_info["relative"] - a_info["relative"])
    edit_h = max(a_info["height"], b_info["height"])
    edit_w = max(a_info["width"], b_info["width"])
    rotated = _rotate_delta(delta, edit_h, edit_w)
    if b_info["height"] == a_info["height"] and b_info["width"] == a_info["width"]:
        mode = "within_bbox"
    elif b_info["height"] == a_info["height"] and b_info["width"] == a_info["width"] + 1:
        mode = "expand_right"
    elif b_info["height"] == a_info["height"] + 1 and b_info["width"] == a_info["width"]:
        mode = "expand_down"
    elif b_info["height"] == a_info["height"] + 1 and b_info["width"] == a_info["width"] + 1:
        mode = "expand_both"
    else:
        mode = "other"
    errors = []
    if any(cell != 0 for row in panels["answer"] for cell in row):
        errors.append("answer panel must be empty")
    for name, info in (("A", a_info), ("B", b_info), ("C", c_info)):
        if len(info["colors"]) != 1:
            errors.append(f"{name} must be monochrome")
        if 9 in info["colors"]:
            errors.append(f"{name} uses separator color")
    if a_info["colors"] != b_info["colors"]:
        errors.append("A and B must use the same color")
    if c_info["colors"] == a_info["colors"]:
        errors.append("C must use a different color")
    if (a_info["height"], a_info["width"]) != (c_info["height"], c_info["width"]):
        errors.append("A and C bbox dimensions differ")
    if not a_info["relative"] <= b_info["relative"]:
        errors.append("B must be a bbox-aligned superset of A")
    if not delta:
        errors.append("B has no inferred added cells")
    if mode == "other":
        errors.append("B may expand A by at most one row and/or column")
    if delta == rotated:
        errors.append("direct and rotated edits are indistinguishable")
    if delta & c_info["relative"]:
        errors.append("C hides the direct delta")
    if rotated & c_info["relative"]:
        errors.append("C hides the rotated delta")
    cr0, cc0 = c_info["origin"]
    for name, cells in (("direct", delta), ("rotate_180", rotated)):
        if any(not (0 <= cr0 + r < len(panels["c"]) and 0 <= cc0 + c < len(panels["c"][0]))
               for r, c in cells):
            errors.append(f"{name} delta would be clipped")
    if len(panels["answer"]) < len(panels["c"]) or len(panels["answer"][0]) < len(panels["c"][0]):
        errors.append("answer panel is smaller than C")
    return {
        "shape": (h, w), "separator": (sr, sc), **panels,
        "a_info": a_info, "b_info": b_info, "c_info": c_info,
        "delta": delta, "rotated_delta": rotated, "edit_h": edit_h,
        "edit_w": edit_w, "delta_mode": mode, "errors": errors,
    }


def _copy_c(grid, facts):
    out = [row[:] for row in grid]
    sr, sc = facts["separator"]
    for r, row in enumerate(facts["c"]):
        for c, value in enumerate(row):
            rr, cc = sr + 1 + r, sc + 1 + c
            if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
                out[rr][cc] = value
    return out


def _stamp_relative(grid, facts, cells):
    out = _copy_c(grid, facts)
    sr, sc = facts["separator"]
    cr0, cc0 = facts["c_info"]["origin"]
    color = next(iter(facts["c_info"]["colors"]))
    for row, col in cells:
        rr, cc = cr0 + row, cc0 + col
        if 0 <= rr < len(facts["c"]) and 0 <= cc < len(facts["c"][0]):
            out[sr + 1 + rr][sc + 1 + cc] = color
    return out


def solve_with_delta(grid, orientation: str, inferred_delta):
    if orientation not in ORIENTATIONS:
        raise ValueError("invalid orientation")
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    delta = frozenset(tuple(cell) for cell in inferred_delta)
    if orientation == "rotate_180":
        delta = _rotate_delta(delta, facts["edit_h"], facts["edit_w"])
    return _stamp_relative(grid, facts, delta)


def solve_python(grid, orientation: str):
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return solve_with_delta(grid, orientation, facts["delta"])


def _transform_solver(transform: Callable[[dict], frozenset]):
    def solve(grid):
        facts = analyze(grid)
        if facts["errors"]:
            raise ValueError("; ".join(facts["errors"]))
        return _stamp_relative(grid, facts, transform(facts))
    return solve


def _copy_b(grid):
    facts = analyze(grid)
    return _stamp_relative(grid, facts, facts["b_info"]["relative"])


def _fill_bbox(grid):
    facts = analyze(grid)
    cells = frozenset((r, c) for r in range(facts["edit_h"]) for c in range(facts["edit_w"]))
    return _stamp_relative(grid, facts, cells)


def _absolute_delta(grid):
    facts = analyze(grid)
    cells = facts["b_info"]["cells"] - facts["a_info"]["cells"]
    out = _copy_c(grid, facts)
    sr, sc = facts["separator"]
    color = next(iter(facts["c_info"]["colors"]))
    for row, col in cells:
        if 0 <= row < len(facts["answer"]) and 0 <= col < len(facts["answer"][0]):
            out[sr + 1 + row][sc + 1 + col] = color
    return out


def declared_rivals(orientation: str):
    if orientation not in ORIENTATIONS:
        raise ValueError("invalid orientation")
    other = "rotate_180" if orientation == "direct" else "direct"
    return {
        f"other_setting_{other}": lambda grid, other=other: solve_python(grid, other),
        "copy_c_only": _transform_solver(lambda _facts: frozenset()),
        "copy_b_silhouette": _copy_b,
        "fill_edit_bbox": _fill_bbox,
        "absolute_panel_delta": _absolute_delta,
        "mirror_left_right": _transform_solver(
            lambda facts: frozenset((r, facts["edit_w"] - 1 - c) for r, c in facts["delta"])
        ),
        "mirror_up_down": _transform_solver(
            lambda facts: frozenset((facts["edit_h"] - 1 - r, c) for r, c in facts["delta"])
        ),
        "first_delta_only": _transform_solver(
            lambda facts: frozenset((sorted(facts["delta"])[0],))
        ),
    }


def _profile_pair(seed: int, split: str, index: int, profile: dict):
    height, width = profile["size"]
    sr, sc = profile["separator"]
    shape_h, shape_w = profile["shape"]
    delta = frozenset(tuple(cell) for cell in profile["delta"])
    edit_h = max(shape_h, max(row for row, _ in delta) + 1)
    edit_w = max(shape_w, max(col for _, col in delta) + 1)
    rotated = _rotate_delta(delta, edit_h, edit_w)
    source_forbidden = {cell for cell in delta if cell[0] < shape_h and cell[1] < shape_w}
    query_forbidden = {
        cell for cell in delta | rotated if cell[0] < shape_h and cell[1] < shape_w
    }
    source = _shape(shape_h, shape_w, source_forbidden,
                    _rng(seed, split, index, "source"), profile.get("source_density", 0.40))
    query = _shape(shape_h, shape_w, query_forbidden,
                   _rng(seed, split, index, "query"), profile.get("query_density", 0.58))
    if source == query:
        raise ValueError("profile produced identical A and C shapes")
    target = source | delta
    a_pos, b_pos, c_pos = profile["positions"]
    top_h, left_w = sr, sc
    right_w, bottom_h = width - sc - 1, height - sr - 1
    ar, ac = a_pos; br, bc = b_pos; cr, cc = c_pos
    if not (0 <= ar <= top_h - shape_h and 0 <= ac <= left_w - shape_w):
        raise ValueError("A placement does not fit")
    if not (0 <= br <= top_h - edit_h and 0 <= bc <= right_w - edit_w):
        raise ValueError("B placement does not fit")
    if not (0 <= cr <= bottom_h - edit_h and 0 <= cc <= left_w - edit_w):
        raise ValueError("C/edit placement does not fit")
    colors = _rng(seed, split, index, "colors").sample(_COLORS, 2)
    demo_color, query_color = colors
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for col in range(width):
        grid[sr][col] = 9
    for row in range(height):
        grid[row][sc] = 9
    for row, col in source:
        grid[ar + row][ac + col] = demo_color
    for row, col in target:
        grid[br + row][sc + 1 + bc + col] = demo_color
    for row, col in query:
        grid[sr + 1 + cr + row][cc + col] = query_color
    facts = analyze(grid)
    if facts["errors"]:
        raise ValueError(f"invalid authored profile {profile['name']}: {facts['errors']}")
    return grid


def generate(seed, settings, demos, queries) -> dict:
    orientation = _orientation(settings)
    demos = _count("demos", demos, 2, 6)
    queries = _count("queries", queries, 1, 4)
    train = []
    test = []
    for index, profile in enumerate(_DEMO_PROFILES[:demos]):
        grid = _profile_pair(seed, "train", index, profile)
        train.append({"input": grid, "output": solve_python(grid, orientation)})
    for index, profile in enumerate(_QUERY_PROFILES[:queries]):
        grid = _profile_pair(seed, "test", index, profile)
        test.append({"input": grid, "output": solve_python(grid, orientation)})
    return {"train": train, "test": test, "program_solution": program(settings)}


def public_id(episode: dict, *, query_count: int = 1) -> str:
    query_count = _count("query_count", query_count, 1, len(episode["test"]))
    return public_challenge_id({"train": episode["train"], "test": episode["test"][:query_count]})


def non_separator_nonzero_cells(grid):
    _grid_shape(grid)
    return {
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row)
        if value != 0 and value != 9
    }
