"""Generator for training task 7ddcd7ec / e0ef0cfeaf88.

A monochrome 2x2 body has one to four isolated pixels immediately beyond its
diagonal corners.  Each such tail extends a diagonal ray away from the body
until the grid edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "e0ef0cfeaf88"
VERSION = "4.1.0"
TASK_ID = "e0ef0cfeaf88"
RULE_HASH = "44a4f74471b9"

SUMMARY = (
    "Place a monochrome 2x2 body on background 0 with one to four diagonal "
    "corner tails; the rule extends every tail diagonally away from the body "
    "through the grid edge."
)

INVARIANTS = [
    "the background is color 0 and all foreground cells share one color",
    "there is exactly one solid 2x2 body",
    "one to four tails occupy distinct diagonal corner positions",
    "the body leaves room for every possible tail ray to add a cell",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 10..20",
        "valid": "10..20",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 10..20",
        "valid": "10..20",
    },
    "tail_count": {
        "type": "int",
        "default": "rng 1..4",
        "valid": "1..4",
    },
    "color": {
        "type": "color",
        "default": "rng 1..9",
        "valid": "1..9",
    },
}

_VALID_H = (10, 20)
_VALID_W = (10, 20)
_VALID_TAILS = (1, 4)
_PROFILE_PERIOD = 12
_PROFILE_RESIDUE = 0
_PROFILE_BAND_OFFSETS = {"easy": 0, "medium": 1, "hard": 2}

# Tail order: upper-left, upper-right, lower-left, lower-right.
_TAIL_OFFSETS = ((-1, -1), (-1, 2), (2, -1), (2, 2))

# Grid height, width, color, body row, body column, tail-index tuple.
_PROFILE_SPECS = (
    (10, 10, 4, 2, 4, (1, 3)),
    (10, 10, 3, 2, 2, (3,)),
    (10, 10, 7, 3, 4, (1, 2)),
    (10, 10, 8, 4, 3, (1, 2, 3)),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in AXES:
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _body_candidates(cells):
    return [
        (r, c)
        for r, c in sorted(cells)
        if {
            (r, c),
            (r + 1, c),
            (r, c + 1),
            (r + 1, c + 1),
        }
        <= cells
    ]


def _analyze_scene(grid):
    grid = _coerce_grid(grid)
    h = len(grid)
    w = len(grid[0]) if grid else 0
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }
    colors = {
        grid[r][c]
        for r, c in cells
        if type(grid[r][c]) is int
    }
    candidates = _body_candidates(cells)
    body = candidates[0] if len(candidates) == 1 else None
    body_cells = set()
    tails = set()
    tail_indices = []
    if body is not None:
        r0, c0 = body
        body_cells = {
            (r0, c0),
            (r0 + 1, c0),
            (r0, c0 + 1),
            (r0 + 1, c0 + 1),
        }
        tails = cells - body_cells
        expected = {
            (r0 + dr, c0 + dc): index
            for index, (dr, dc) in enumerate(_TAIL_OFFSETS)
        }
        tail_indices = sorted(
            expected[cell]
            for cell in tails
            if cell in expected
        )
    return {
        "grid": grid,
        "h": h,
        "w": w,
        "cells": frozenset(cells),
        "colors": frozenset(colors),
        "body_candidates": tuple(candidates),
        "body": body,
        "body_cells": frozenset(body_cells),
        "tails": frozenset(tails),
        "tail_indices": tuple(tail_indices),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return ["grid rows must be non-empty lists or digit strings"]
    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return ["grid must be rectangular"]

    errors = []
    h = len(coerced)
    w = width
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append("grid height must be in 10..20")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append("grid width must be in 10..20")
    if any(
        type(value) is not int or not (0 <= value <= 9)
        for row in coerced
        for value in row
    ):
        errors.append("grid values must be integer ARC colors 0..9")

    scene = _analyze_scene(coerced)
    if len(scene["colors"]) != 1:
        errors.append("all foreground cells must share one nonzero color")
    if len(scene["body_candidates"]) != 1:
        errors.append("scene must contain exactly one solid 2x2 body")
        return errors

    r0, c0 = scene["body"]
    if not (2 <= r0 <= h - 4 and 2 <= c0 <= w - 4):
        errors.append(
            "body must leave one output cell beyond every possible tail"
        )
    if not (_VALID_TAILS[0] <= len(scene["tails"]) <= _VALID_TAILS[1]):
        errors.append("scene must contain exactly 1..4 tails")
    expected_tails = {
        (r0 + dr, c0 + dc)
        for dr, dc in _TAIL_OFFSETS
    }
    if not scene["tails"] <= expected_tails:
        errors.append(
            "tails must occupy distinct diagonal positions around the body"
        )
    return errors


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    color = next(iter(scene["colors"]))
    return {
        "grid_h": scene["h"],
        "grid_w": scene["w"],
        "tail_count": len(scene["tails"]),
        "color": color,
    }


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))
    scene = _analyze_scene(grid)
    output = [row[:] for row in scene["grid"]]
    r0, c0 = scene["body"]
    center_r2 = 2 * r0 + 1
    center_c2 = 2 * c0 + 1
    color = next(iter(scene["colors"]))
    for tail_r, tail_c in scene["tails"]:
        dr = -1 if 2 * tail_r < center_r2 else 1
        dc = -1 if 2 * tail_c < center_c2 else 1
        r = tail_r + dr
        c = tail_c + dc
        while 0 <= r < scene["h"] and 0 <= c < scene["w"]:
            output[r][c] = color
            r += dr
            c += dc
    return output


def canonical_profile_signature(grid):
    if self_check(grid):
        return None
    scene = _analyze_scene(grid)
    color = next(iter(scene["colors"]))
    return (
        scene["h"],
        scene["w"],
        color,
        scene["tail_indices"],
    )


def _profile_signature(profile):
    h, w, color, _r0, _c0, tail_indices = profile
    return h, w, color, tuple(tail_indices)


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _profile_signature(profile) for profile in _PROFILE_SPECS
)


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) in _CANONICAL_PROFILE_SIGNATURES


def _paint_scene(h, w, color, r0, c0, tail_indices):
    grid = full_grid(h, w, 0)
    for dr in (0, 1):
        for dc in (0, 1):
            grid[r0 + dr][c0 + dc] = color
    for index in tail_indices:
        dr, dc = _TAIL_OFFSETS[index]
        grid[r0 + dr][c0 + dc] = color
    return grid


def _profile_positions(profile):
    h, w, _color, _r0, _c0, _tail_indices = profile
    return tuple(
        (r0, c0)
        for r0 in range(2, h - 3)
        for c0 in range(2, w - 3)
    )


def _draw_profile(profile, rng):
    h, w, color, _r0, _c0, tail_indices = profile
    r0, c0 = rng.choice(_profile_positions(profile))
    return _paint_scene(h, w, color, r0, c0, tail_indices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    has_override = any(overrides.get(label) is not None for label in AXES)
    profile = None
    if not has_override and sample_index % _PROFILE_PERIOD == _PROFILE_RESIDUE:
        # A deterministic 1-in-12 schedule preserves the intended ~8% prior
        # while guaranteeing support in the pinned per-band census.  The
        # quotient and band offset rotate through every canonical profile.
        profile_index = (
            sample_index // _PROFILE_PERIOD + _PROFILE_BAND_OFFSETS[band]
        ) % len(_PROFILE_SPECS)
        profile = _PROFILE_SPECS[profile_index]

    if profile is not None:
        h, w, color, _r0, _c0, tail_indices = profile
        ctx.draw_int("grid_h", h, h)
        ctx.draw_int("grid_w", w, w)
        ctx.draw_int("tail_count", len(tail_indices), len(tail_indices))
        ctx.draw_int("color", color, color)
        grid = _draw_profile(profile, ctx.draw_rng("layout"))
    else:
        if overrides.get("grid_h") is not None:
            h = ctx.draw_int("grid_h", *_VALID_H)
        else:
            h = ctx.draw_int(
                "grid_h",
                *{
                    "easy": (10, 13),
                    "medium": (10, 16),
                    "hard": (14, 20),
                }[band],
            )
        if overrides.get("grid_w") is not None:
            w = ctx.draw_int("grid_w", *_VALID_W)
        else:
            w = ctx.draw_int(
                "grid_w",
                *{
                    "easy": (10, 13),
                    "medium": (10, 16),
                    "hard": (14, 20),
                }[band],
            )
        tail_count = ctx.draw_int("tail_count", *_VALID_TAILS)
        color = ctx.draw_color("color", exclude={0})
        layout_rng = ctx.draw_rng("layout")
        r0 = layout_rng.randint(2, h - 4)
        c0 = layout_rng.randint(2, w - 4)
        tail_indices = tuple(
            sorted(layout_rng.sample(range(4), tail_count))
        )
        grid = _paint_scene(
            h,
            w,
            color,
            r0,
            c0,
            tail_indices,
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
