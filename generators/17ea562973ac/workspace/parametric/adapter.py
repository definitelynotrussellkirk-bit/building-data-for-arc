"""Native opt-in missing-box family: infer a box, optionally peel, then rebox.

The reviewed production generator and its reference remain unchanged. Labels
here are diagnostic Python claims; native qualification independently executes
the exact adjacent Racket programs. See README.md for the admitted grammar.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes

TASK_ID = "17ea562973ac"
VERSION = "peeling-v1"
_HOME = Path(__file__).resolve().parent


def _depth(settings):
    if (type(settings) is not dict or set(settings) != {"peel_depth"}
            or type(settings["peel_depth"]) is not int
            or settings["peel_depth"] not in (0, 1)):
        raise ValueError("settings must be exactly {'peel_depth': 0 or 1}; bool is forbidden")
    return settings["peel_depth"]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings):
    """Return the materialized rule, preserving the default authority bytes."""
    depth = _depth(settings)
    return (_HOME / ("canonical.rkt" if depth == 0 else "peel_once.rkt")).read_text(encoding="utf-8")


def _bbox(cells):
    if not cells:
        return None
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def _inside(cells, box):
    if box is None:
        return []
    t, l, b, r = box
    return [(y, x) for y, x in cells if t < y < b and l < x < r]


def analyze(grid):
    """Strict pixel facts; permits original canonical inputs with no inner box."""
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError("grid must be a nonempty list of rows, dimensions at most 30")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    colors = {grid[r][c] for r, c in cells}
    if len(colors) != 1 or not 2 <= next(iter(colors)) <= 9:
        raise ValueError("one nonzero marker color in 2..9 is required")
    box = _bbox(cells)
    interior = _inside(cells, box)
    return {"cells": cells, "bbox": box, "interior": interior,
            "inner_bbox": _bbox(interior), "color": next(iter(colors)),
            "height": len(grid), "width": width}


def validate_input(grid):
    """Return violations of the separate, shared two-setting sampler domain."""
    try:
        info = analyze(grid)
    except (ValueError, TypeError) as exc:
        return [str(exc)]
    errors = []
    if not 6 <= info["height"] <= 30 or not 7 <= info["width"] <= 30:
        errors.append("prototype canvas must be 6..30 rows by 7..30 columns")
    if not 4 <= len(info["cells"]) <= 160:
        errors.append("prototype needs 4..160 markers")
    t, l, b, r = info["bbox"]
    if b - t < 5 or r - l < 5:
        errors.append("outer box must span at least 6 rows and 6 columns")
    if len(info["interior"]) < 2:
        errors.append("at least two strict-interior survivors are required")
    elif (info["inner_bbox"][2] - info["inner_bbox"][0] < 3
          or info["inner_bbox"][3] - info["inner_bbox"][1] < 3):
        errors.append("survivor box must span at least 4 rows and 4 columns")
    return errors


def _render(info, box, *, fill=False):
    h, w, color = info["height"], info["width"], info["color"]
    out = [[0] * w for _ in range(h)]
    if box is not None:
        t, l, b, r = box
        for y in range(t, b + 1):
            for x in range(l, r + 1):
                if fill or y in (t, b) or x in (l, r):
                    out[y][x] = color
    return out


def mirror(grid, settings):
    """Diagnostic mirror; Racket remains the label authority."""
    depth = _depth(settings)
    info = analyze(grid)
    if depth and not info["interior"]:
        raise ValueError("peeling input has no survivors; outside the admitted grammar")
    return _render(info, info["inner_bbox"] if depth else info["bbox"])


def _rng(seed, slot):
    key = f"{TASK_ID}/{VERSION}/inputs/{seed}/{slot}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(key).digest(), "big"))


def _paint(h, w, cells, color):
    grid = [[0] * w for _ in range(h)]
    for r, c in cells:
        grid[r][c] = color
    return grid


def _teaching_input(seed, index):
    rng = _rng(seed, f"demo-{index}")
    if index == 0:
        # Noncorner extrema defeat coordinatewise rank trimming, one-axis
        # peeling, corner-only peeling and first-two-marker box inference.
        cells = [(1, 2), (2, 1), (10, 6), (6, 12),
                 (3, 4), (4, 9), (8, 7), (5, 6)]
    else:
        # Exactly two survivors defeat an otherwise invisible count gate;
        # the unequal four gaps also reject a fixed geometric inset.
        cells = [(0, 0), (11, 13), (1, 5), (8, 11)]
    if rng.randrange(2):
        cells = [(11 - r, c) for r, c in cells]
    if rng.randrange(2):
        cells = [(r, 13 - c) for r, c in cells]
    return _paint(12, 14, cells, rng.randint(2, 9))


def _nested_input(seed, slot, h, w, *, dense=False, two=False):
    rng = _rng(seed, slot)
    if dense or h == 6:
        outer = (0, 0, h - 1, w - 1)
    else:
        t, l = rng.randrange(2), rng.randrange(2)
        outer = (t, l, h - 1 - rng.randrange(2), w - 1 - rng.randrange(2))
    t, l, b, r = outer
    if dense:
        inner = (t + rng.randint(1, 3), l + rng.randint(1, 3),
                 b - rng.randint(1, 3), r - rng.randint(1, 3))
    else:
        it, il = rng.randint(t + 1, b - 4), rng.randint(l + 1, r - 4)
        inner = (it, il, rng.randint(it + 3, b - 1), rng.randint(il + 3, r - 1))
    it, il, ib, ir = inner
    if two:
        outer_cells = {(t, l), (b, r)}
        inner_cells = {(it, ir), (ib, il)}
    else:
        outer_cells = {(t, rng.randint(l + 1, r - 1)),
                       (b, rng.randint(l + 1, r - 1)),
                       (rng.randint(t + 1, b - 1), l),
                       (rng.randint(t + 1, b - 1), r)}
        inner_cells = {(it, il + 1), (it + 1, il),
                       (ib, ir - 1), (ib - 1, ir), (it + 1, il + 1)}
    if dense:
        edge = [(y, x) for y in range(t, b + 1) for x in range(l, r + 1)
                if (y in (t, b) or x in (l, r)) and (y, x) not in outer_cells]
        rng.shuffle(edge)
        outer_cells.update(edge[:rng.randint(12, 24) - len(outer_cells)])
        inside = [(y, x) for y in range(it, ib + 1) for x in range(il, ir + 1)
                  if (y, x) not in inner_cells]
        rng.shuffle(inside)
        inner_cells.update(inside[:rng.randint(48, 80) - len(inner_cells)])
    return _paint(h, w, sorted(outer_cells | inner_cells), rng.randint(2, 9))


def _rival_outputs(grid, depth):
    info = analyze(grid)
    cells, box = info["cells"], info["bbox"]
    eligible = info["interior"] if depth else cells
    target = _bbox(eligible)
    expected = _render(info, target)
    retained = deepcopy(expected)
    for r, c in cells:
        retained[r][c] = info["color"]
    dots = _paint(info["height"], info["width"], eligible, info["color"])
    outputs = {
        "opposite_setting": _render(info, box if depth else info["inner_bbox"]),
        "filled_rectangle": _render(info, target, fill=True),
        "retain_source_markers": retained,
        "first_two_eligible_markers": _render(info, _bbox(eligible[:2])),
        "keep_eligible_markers": dots,
    }
    if depth:
        t, l, b, r = box
        corners = {(t, l), (t, r), (b, l), (b, r)}
        ys, xs = sorted({y for y, x in cells}), sorted({x for y, x in cells})
        outputs.update({
            "requires_three_survivors": expected if len(eligible) >= 3 else _render(info, None),
            "fixed_inset_one": _render(info, (t + 1, l + 1, b - 1, r - 1)),
            "fixed_inset_two": _render(info, (t + 2, l + 2, b - 2, r - 2)),
            "coordinatewise_trim": _render(info, (ys[1], xs[1], ys[-2], xs[-2])),
            "remove_corners_only": _render(info, _bbox([p for p in cells if p not in corners])),
            "remove_extreme_rows_only": _render(info, _bbox([(y, x) for y, x in cells if t < y < b])),
            "remove_extreme_columns_only": _render(info, _bbox([(y, x) for y, x in cells if l < x < r])),
            "remove_canvas_boundary": _render(info, _bbox([(y, x) for y, x in cells
                if 0 < y < info["height"] - 1 and 0 < x < info["width"] - 1])),
            "peel_twice": _render(info, _bbox(_inside(eligible, target))),
        })
    return outputs


def teaching_check(episode, settings):
    """Fit finite rivals on demos only; queries only test surviving predictions.

    Private query output fields are deliberately ignored. This is a bounded
    rival analysis, never a proof of uniqueness among arbitrary programs.
    """
    depth = _depth(settings)
    train, tests = episode["train"], episode["test"]
    if not train or not tests:
        raise ValueError("at least one demo and one query are required")
    predictions = [_rival_outputs(pair["input"], depth) for pair in train]
    for pair in train:
        if pair["output"] != mirror(pair["input"], settings):
            raise ValueError("demonstration label disagrees with the diagnostic rule")
    eliminated = {name: [i for i, pair in enumerate(train)
                         if predictions[i][name] != pair["output"]]
                  for name in predictions[0]}
    survivors = [name for name, witnesses in eliminated.items() if not witnesses]
    harmful = [name for name in survivors if any(
        _rival_outputs(pair["input"], depth)[name] != mirror(pair["input"], settings)
        for pair in tests)]
    return {"survivors": survivors, "harmful_survivors": harmful,
            "eliminated": {name: rows for name, rows in eliminated.items() if rows},
            "rivals_tested": len(eliminated), "fit_uses": "demonstrations_only"}


def generate(seed, settings, demos=3, queries=4):
    """Construct an episode with independent input and rule choices.

    Slot RNGs do not depend on settings or requested query count. Different
    slot dimensions/counts guarantee within-episode uniqueness without retries.
    """
    _integer(seed, 0, 2**63 - 1, "seed")
    _depth(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")
    inputs = [_teaching_input(seed, 0), _teaching_input(seed, 1)]
    extra_sizes = [(8, 9), (10, 11), (16, 18), (20, 16)]
    for i in range(2, demos):
        h, w = extra_sizes[i - 2]
        inputs.append(_nested_input(seed, f"demo-{i}", h, w))
    query_sizes = [(6, 7), (12, 16), (22, 26), (30, 30)]
    test_inputs = [_nested_input(seed, f"query-{i}", h, w, dense=i >= 2, two=i == 0)
                   for i, (h, w) in enumerate(query_sizes[:queries])]
    for grid in inputs + test_inputs:
        errors = validate_input(grid)
        if errors:
            raise AssertionError("constructive sampler violated its domain: " + "; ".join(errors))
    result = {"train": [{"input": grid, "output": mirror(grid, settings)} for grid in inputs],
              "test": [{"input": grid, "output": mirror(grid, settings)} for grid in test_inputs],
              "program_solution": program(settings), "settings": dict(settings), "seed": seed}
    if teaching_check(result, settings)["harmful_survivors"]:
        raise AssertionError("constructed demonstrations leave a query-changing rival")
    return result


def public_view(episode, query_index=0):
    """Project one current query with its demos; the caller owns reveal timing."""
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    current = {"train": episode["train"], "test": [episode["test"][query_index]]}
    return json.loads(public_challenge_bytes(current))
