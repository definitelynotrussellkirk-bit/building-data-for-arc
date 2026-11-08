"""Arithmetic blue-line inputs; labels remain the unchanged canonical Racket rule.

Exact controls are resolved constructively before placement. Production uses a
six-profile curriculum; any five consecutive examples refute the declared
rivals, including every canonical-fitting count-to-column-sign lookup. Explicit
overrides select an unscheduled authoring distribution and make no lesson promise.
"""
from __future__ import annotations

from functools import lru_cache, partial
from math import gcd

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2d2b102b7740"
TASK_ID = GENERATOR_ID
RULE_HASH = "8db0d36e6e45"
VERSION = "2.0.0"
SUMMARY = "2-5 equally spaced blue cells; continue their row-major step with red cells."
EXAMPLES_NEEDED = 5
LESSON_SCHEDULE_PERIOD = 6
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "rectangular 6..18 by 8..20 integer grid containing only background 0 and blue 1",
    "2..5 blue cells form one constant row-major step: dr>0 or dr=0,dc>0",
    "0<=dr<=4, -4<=dc<=4, and at least one continuation cell fits",
    "exact overrides are honored or rejected; never clipped, dropped, or replaced",
]
LINE_ORIENTS = ("horizontal", "vertical", "diagonal_dr", "diagonal_dl",
                "knight", "steep_diag", "oblique")
HELPFUL_TEXTURES = LINE_ORIENTS + ("two_blues_only", "line_at_edge")
DEGENERATE_TEXTURES = ()
AXES = {
    "grid_h": {"type": "int", "default": "feasible 6..18; canonical profile 15", "valid": "6..18"},
    "grid_w": {"type": "int", "default": "feasible 8..20; canonical profile 15", "valid": "8..20"},
    "n_blues": {"type": "int", "default": "curriculum 2..5", "valid": "2..5"},
    "line_orientation": {"type": "str", "default": "feasible curriculum direction", "valid": "|".join(LINE_ORIENTS)},
    "step_dr": {"type": "int", "default": "feasible 0..4", "valid": "0..4"},
    "step_dc": {"type": "int", "default": "feasible -4..4", "valid": "-4..4"},
    "position_bias": {"type": "str", "default": "spread|corner|center", "valid": "spread|corner|center"},
    "anchor_corner": {"type": "bool", "default": "feasible true|false", "valid": "true|false"},
    "texture": {"type": "str", "default": "actual orientation", "valid": "|".join(HELPFUL_TEXTURES)},
}
# Strict classification: each refused feasible-domain tuple carries its axes.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_INT_RANGES = {"grid_h": (6, 18), "grid_w": (8, 20), "n_blues": (2, 5),
               "step_dr": (0, 4), "step_dc": (-4, 4)}


class IncompatibleOverrides(ValueError):
    def __init__(self, message, axes):
        super().__init__(message)
        self.incompatible_axes = tuple(sorted(axes))


def _validate_call(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")


def _validated(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override keys: {sorted(unknown)}")
    pins = {key: value for key, value in overrides.items() if value is not None}
    for key, value in pins.items():
        if key in _INT_RANGES:
            lo, hi = _INT_RANGES[key]
            if type(value) is not int or not lo <= value <= hi:
                raise ValueError(f"{key} must be an integer in {lo}..{hi}, not {value!r}")
        elif key == "anchor_corner":
            if type(value) is not bool:
                raise ValueError("anchor_corner must be a bool")
        elif not isinstance(value, str) or value not in AXES[key]["valid"].split("|"):
            raise ValueError(f"invalid {key}: {value!r}")
    return pins


def _orientation(dr, dc):
    if dr == 0:
        return "horizontal"
    if dc == 0:
        return "vertical"
    if dr == dc:
        return "diagonal_dr"
    if dr == -dc:
        return "diagonal_dl"
    if (dr, abs(dc)) in ((1, 2), (2, 1)):
        return "knight"
    if dr in (3, 4) and abs(dc) == 1:
        return "steep_diag"
    return "oblique"


def _origin_bounds(h, w, n, dr, dc, before, after, edge=False):
    last = n - 1 + after
    low_r, high_r = before * dr, h - 1 - last * dr
    if dc >= 0:
        low_c, high_c = before * dc, w - 1 - last * dc
    else:
        low_c, high_c = last * -dc, w - 1 - before * -dc
    if edge:
        low_r = high_r = 0
    return low_r, high_r, low_c, high_c


@lru_cache(maxsize=4096)
def _configs(profile, count, items):
    """Cache immutable feasible geometry, never grids or RNG state."""
    pins = dict(items)
    texture = pins.get("texture")
    orientation = pins.get("line_orientation")
    if texture in LINE_ORIENTS:
        if orientation is not None and orientation != texture:
            return ()
        orientation = texture
    if texture == "line_at_edge":
        if orientation is not None and orientation != "horizontal":
            return ()
        orientation = "horizontal"
    before, after = (1, 2) if profile in (0, 1, 2) else (0, 1)
    h_cap = 15 if profile == 3 else pins.get("grid_h", 18)
    w_cap = 15 if profile == 3 else pins.get("grid_w", 20)
    found = []
    for n in range(2, 6):
        if count is not None and n != count:
            continue
        if pins.get("n_blues", n) != n or (texture == "two_blues_only" and n != 2):
            continue
        for dr in range(5):
            for dc in range(-4, 5):
                if dr == 0 and dc <= 0:
                    continue
                if pins.get("step_dr", dr) != dr or pins.get("step_dc", dc) != dc:
                    continue
                if orientation is not None and _orientation(dr, dc) != orientation:
                    continue
                if profile in (0, 1) and (dr, dc) not in ((2, -2), (2, -4), (4, -2)):
                    continue
                if profile == 2 and (dr, dc) not in ((2, 2), (2, 4), (4, 2)):
                    continue
                if profile == 3 and not (2 <= dr == dc <= 4):
                    continue
                bounds = _origin_bounds(h_cap, w_cap, n, dr, dc, before, after,
                                        texture == "line_at_edge")
                lr, hr, lc, hc = bounds
                if lr > hr or lc > hc:
                    continue
                corner = (0, 0 if dc >= 0 else w_cap - 1)
                if pins.get("anchor_corner") is False and (lr, lc) == (hr, hc) == corner:
                    continue
                found.append((n, dr, dc))
    return tuple(found)


def _dimension(ctx, name, choices, band, profile):
    values = list(choices)
    if profile == 3:
        return ctx.draw_choice(name, [15])
    # Difficulty weights preferred sizes; it never narrows override validity.
    favorite = {"easy": (6, 10), "medium": (10, 15), "hard": (14, 20)}.get(band, (8, 16))
    weighted = values + [v for v in values if favorite[0] <= v <= favorite[1]] * 2
    if 15 in values:
        weighted += [15] * (12 if profile is not None else 2)
    return ctx.draw_choice(name, weighted)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty)
    pins = _validated(overrides)
    if pins.get("anchor_corner") is True and "position_bias" in pins:
        raise IncompatibleOverrides("position_bias cannot move an exact anchor_corner", ("anchor_corner", "position_bias"))
    profile = sample_index % LESSON_SCHEDULE_PERIOD if not pins else None
    family_counts = [2, 4, 5]
    stable_rng(seed, TASK_ID + ":curriculum-counts", VERSION).shuffle(family_counts)
    x, y, z = family_counts
    count = (x, 3, x, 3, y, z)[profile] if profile is not None else None
    configs = list(_configs(profile, count, tuple(sorted(pins.items()))))
    if not configs:
        raise IncompatibleOverrides("no constant-step line fits the requested exact controls", pins)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=pins)
    orient = ctx.draw_choice("line_orientation", sorted({_orientation(dr, dc) for _, dr, dc in configs}))
    configs = [item for item in configs if _orientation(item[1], item[2]) == orient]
    n = ctx.draw_choice("n_blues", sorted({item[0] for item in configs}))
    configs = [item for item in configs if item[0] == n]
    dr = ctx.draw_choice("step_dr", sorted({item[1] for item in configs}))
    dc = ctx.draw_choice("step_dc", sorted({item[2] for item in configs if item[1] == dr}))
    texture = ctx.draw_choice("texture", [pins.get("texture", orient)])
    before, after = (1, 2) if profile in (0, 1, 2) else (0, 1)
    span = n - 1 + before + after
    min_h, min_w = max(6, span * dr + 1), max(8, span * abs(dc) + 1)
    possible_h = [pins["grid_h"]] if "grid_h" in pins else list(range(min_h, 19))
    possible_w = [pins["grid_w"]] if "grid_w" in pins else list(range(min_w, 21))
    edge = texture == "line_at_edge"
    # A false corner pin needs a real non-corner start, even at tight bounds.
    def positions(h, w):
        lr, hr, lc, hc = _origin_bounds(h, w, n, dr, dc, before, after, edge)
        if profile == 3:
            return [(t, t) for t in range(lr, min(hr, hc) + 1)]
        return [(r, c) for r in range(lr, hr + 1) for c in range(lc, hc + 1)]
    def admits(h, w):
        lr, hr, lc, hc = _origin_bounds(h, w, n, dr, dc, before, after, edge)
        if profile == 3:
            hr = min(hr, hc)
            lc, hc = lr, hr
        if lr > hr or lc > hc:
            return False
        corner = (0, 0 if dc >= 0 else w - 1)
        return not ((lr, lc) == (hr, hc) == corner) if pins.get("anchor_corner") is False else True
    possible_h = [h for h in possible_h if any(admits(h, w) for w in possible_w)]
    if not possible_h:
        raise IncompatibleOverrides("no placement fits anchor_corner and the exact geometry", pins)
    h = _dimension(ctx, "grid_h", possible_h, difficulty, profile)
    possible_w = [w for w in possible_w if admits(h, w)]
    w = _dimension(ctx, "grid_w", possible_w, difficulty, profile)
    points = positions(h, w)
    corner = (0, 0 if dc >= 0 else w - 1)
    anchors = sorted({point == corner for point in points})
    anchor = ctx.draw_choice("anchor_corner", anchors)
    points = [point for point in points if (point == corner) == anchor]
    bias = ctx.draw_choice("position_bias", ["spread", "corner", "center"])
    if bias == "corner":
        origin = min(points, key=lambda p: (p[0] + abs(p[1] - corner[1]), p))
    elif bias == "center":
        lr, hr, lc, hc = _origin_bounds(h, w, n, dr, dc, before, after, edge)
        origin = min(points, key=lambda p: (abs(2*p[0]-lr-hr) + abs(2*p[1]-lc-hc), p))
    else:
        origin = ctx.draw_rng("origin").choice(points)
    grid = full_grid(h, w, 0)
    for i in range(n):
        grid[origin[0] + i*dr][origin[1] + i*dc] = 1
    return grid


def _blue_cells(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) or not row for row in grid):
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if not (6 <= h <= 18 and 8 <= w <= 20):
        return ["grid outside the declared 6..18 by 8..20 sampler domain"]
    if any(type(value) is not int or value not in (0, 1) for row in grid for value in row):
        return ["input must contain integer background 0 and blue 1 only"]
    blues = _blue_cells(grid)
    if not 2 <= len(blues) <= 5:
        return [f"need 2..5 blue cells, got {len(blues)}"]
    dr, dc = blues[1][0]-blues[0][0], blues[1][1]-blues[0][1]
    if not (0 <= dr <= 4 and -4 <= dc <= 4 and (dr > 0 or dc > 0)):
        return ["step outside the declared row-major domain"]
    if any((b[0]-a[0], b[1]-a[1]) != (dr, dc) for a, b in zip(blues, blues[1:])):
        return ["blue cells must be equally spaced on one line"]
    nr, nc = blues[-1][0]+dr, blues[-1][1]+dc
    if not (0 <= nr < h and 0 <= nc < w):
        return ["at least one red continuation must fit"]
    return []


def strict_canonical_like(grid):
    """Lawful arithmetic lines in this explicit broader-than-canonical domain."""
    return self_check(grid)


def observe_overrides(grid):
    blues = _blue_cells(grid)
    dr, dc = blues[1][0]-blues[0][0], blues[1][1]-blues[0][1]
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_blues": len(blues),
            "step_dr": dr, "step_dc": dc, "line_orientation": _orientation(dr, dc),
            "anchor_corner": blues[0] == (0, 0 if dc >= 0 else len(grid[0])-1)}


def _rival(grid, mode, sign_mask=None):
    """Deliberately wrong continuations for authoring checks; never label authority."""
    out = [row[:] for row in grid]
    cells = _blue_cells(grid)
    if len(cells) < 2:
        return out
    dr, dc = cells[1][0]-cells[0][0], cells[1][1]-cells[0][1]
    end = cells[-1]
    if mode == "equal_row_column_step":
        dc = dr
    elif mode == "absolute_column_step":
        dc = abs(dc)
    elif mode == "unit_lattice_step":
        divisor = gcd(dr, abs(dc))
        dr, dc = dr // divisor, dc // divisor
    elif mode == "three_blue_prefix":
        end = (cells[0][0] + 2*dr, cells[0][1] + 2*dc)
    elif mode == "count_sign":
        dc = abs(dc) * (-1 if len(cells) in sign_mask else 1)
    steps = 1 if mode == "one_red_only" else 20
    for i in range(1, steps+1):
        r, c = end[0]+i*dr, end[1]+i*dc
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
            out[r][c] = 2
    if mode == "extend_both_directions":
        for i in range(1, 21):
            r, c = cells[0][0]-i*dr, cells[0][1]-i*dc
            if 0 <= r < len(grid) and 0 <= c < len(grid[0]):
                out[r][c] = 2
    return out


def _witness(grid, name):
    cells = _blue_cells(grid)
    dr, dc = cells[1][0]-cells[0][0], cells[1][1]-cells[0][1]
    inside = lambda r, c: 0 <= r < len(grid) and 0 <= c < len(grid[0])
    return {
        "negative_column": dc < 0,
        "negative_three_blues": dc < 0 and len(cells) == 3,
        "multiple_red_cells": inside(cells[-1][0]+2*dr, cells[-1][1]+2*dc),
        "backward_room": inside(cells[0][0]-dr, cells[0][1]-dc),
        "nonunit_spacing": gcd(dr, abs(dc)) > 1,
        "non_three_blue_count": len(cells) != 3,
    }[name]


SEMANTIC_RIVALS = {name: partial(_rival, mode=name) for name in (
    "equal_row_column_step", "absolute_column_step", "extend_both_directions",
    "three_blue_prefix", "unit_lattice_step", "one_red_only")}
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in (
    "equal_row_column_step", "absolute_column_step", "extend_both_directions", "three_blue_prefix")}
# All eight sign lookups that agree on canonical three-blue positive directions.
for _mask in range(8):
    _negative_counts = tuple(n for bit, n in enumerate((2, 4, 5)) if _mask & (1 << bit))
    CANONICAL_SHORTCUTS[f"count_sign_{_mask:03b}"] = partial(_rival, mode="count_sign", sign_mask=_negative_counts)
SEMANTIC_RIVALS.update(CANONICAL_SHORTCUTS)
LESSON_COMPETITORS = {**SEMANTIC_RIVALS, **CANONICAL_SHORTCUTS}
SEMANTIC_WITNESSES = {name: partial(_witness, name=name) for name in (
    "negative_column", "negative_three_blues", "multiple_red_cells", "backward_room", "nonunit_spacing", "non_three_blue_count")}
WITNESS_RIVALS = {
    "negative_column": ["absolute_column_step", "equal_row_column_step"],
    "negative_three_blues": [f"count_sign_{mask:03b}" for mask in range(8)],
    "multiple_red_cells": ["one_red_only"],
    "backward_room": ["extend_both_directions"],
    "nonunit_spacing": ["unit_lattice_step"],
    "non_three_blue_count": ["three_blue_prefix"],
}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; no assertion about undeclared hypotheses."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair['input']) == pair['output'] for pair in demos):
            if rival(query['input']) != query['output']:
                reasons.append(f"{name} fits demonstrations but disagrees on query")
    return reasons


def mutation_fixtures():
    blank = full_grid(8, 10, 0)
    singleton = full_grid(8, 10, 0)
    singleton[2][2] = 1
    block = full_grid(8, 10, 0)
    for r, c in ((0, 0), (0, 1), (1, 0), (1, 1)):
        block[r][c] = 1
    edge_identity = full_grid(8, 10, 0)
    edge_identity[0][8] = edge_identity[0][9] = 1
    return [('all_background', blank), ('same_position', singleton),
            ('solid_2x2', block), ('edge_identity', edge_identity)]
