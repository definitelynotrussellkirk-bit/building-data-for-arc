"""Input sampler for the vertical-7 column explosion task.

The unchanged canonical Racket authority uses the bottom-most color-7 cell as
an apex row.  For every row at or above that apex it paints the horizontally
reachable triangle, alternating 7/8 by *horizontal* distance from the source
column, and writes background everywhere else.  This module samples inputs;
Python mirrors and rivals below are review diagnostics, not label authority.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "506e262f9354"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "d19e95f77d58"
SUMMARY = (
    "A contiguous vertical color-7 source marks a column and bottom row. "
    "The output is an upward triangle clipped by the canvas: cells whose "
    "horizontal distance from the source column is at most bottom_row-row are "
    "7 at even horizontal distance and 8 at odd distance; every other output "
    "cell is 0. Controlled non-7 decoys are outside the triangle and are erased."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical_core", "teaching")

INVARIANTS = [
    "5..16 by 7..18 rectangular ARC-color grid on background 0",
    "exactly 2..7 color-7 cells form one contiguous vertical column",
    "0..4 non-{0,7,8} decoys lie strictly outside the authority triangle",
    "canonical-core inputs start the column in row 0 and contain no decoys",
    "default teaching inputs shift the column downward and contain at least one erasable decoy",
]

COLUMN_POSITIONS = ("left", "center", "right", "interior")
_DECOY_COLORS = (1, 2, 3, 4, 5, 6, 9)
_CANONICAL_PROFILES = (
    (5, 7, 4),
    (7, 8, 5),
    (9, 9, 7),
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical profiles every third sample; otherwise full difficulty-weighted support",
        "valid": "5..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical profiles every third sample; otherwise full difficulty-weighted support",
        "valid": "7..18",
    },
    "n_sevens": {
        "type": "int",
        "default": "canonical profile or full 2..7 support subject to n_sevens<=grid_h",
        "valid": "2..7",
    },
    "column_position": {
        "type": "str",
        "default": "uniform disjoint positional class",
        "valid": "left|center|right|interior",
    },
    "decoy_count": {
        "type": "int",
        "default": "0 on canonical core; 1..4 on teaching profiles",
        "valid": "0..4",
    },
}
# Conditional n_sevens > grid_h impossibilities are reported on the actual
# exception through ``incompatible_axes``; no broad wildcard hides other bugs.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


def schedule_profile(seed, sample_index, difficulty=None):
    """Three consecutive indices contain one core and two teaching inputs."""
    del seed, difficulty
    return "canonical_core" if sample_index % 3 == 0 else "teaching"


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _incompatible(message, axes):
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(axes))
    raise error


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    active = {name: value for name, value in overrides.items() if value is not None}
    for name in ("grid_h", "grid_w", "n_sevens", "decoy_count"):
        if name in active and type(active[name]) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
    if "grid_h" in active and not 5 <= active["grid_h"] <= 16:
        raise ValueError("grid_h must be in 5..16")
    if "grid_w" in active and not 7 <= active["grid_w"] <= 18:
        raise ValueError("grid_w must be in 7..18")
    if "n_sevens" in active and not 2 <= active["n_sevens"] <= 7:
        raise ValueError("n_sevens must be in 2..7")
    if "decoy_count" in active and not 0 <= active["decoy_count"] <= 4:
        raise ValueError("decoy_count must be in 0..4")
    if "column_position" in active:
        if type(active["column_position"]) is not str:
            raise TypeError("column_position must be a string")
        if active["column_position"] not in COLUMN_POSITIONS:
            raise ValueError(f"column_position must be one of {COLUMN_POSITIONS}")
    if ("grid_h" in active and "n_sevens" in active
            and active["n_sevens"] > active["grid_h"]):
        _incompatible("n_sevens cannot exceed grid_h", ("grid_h", "n_sevens"))
    return active


def _weighted(values, favored=()):
    choices = list(values)
    for value in favored:
        if value in choices:
            choices.extend([value] * 12)
    return choices


def _draw_broad_dimensions(ctx, active, band, teaching):
    if "n_sevens" in active and "grid_h" not in active:
        heights = range(max(5, active["n_sevens"] + int(teaching)), 17)
    else:
        heights = range(5, 17)
    favored_h = {
        "easy": (5, 6, 7, 8),
        "medium": (7, 8, 9, 10, 11),
        "hard": (12, 13, 14, 15, 16),
    }[band]
    h = ctx.draw_choice("grid_h", _weighted(heights, favored_h))

    favored_w = {
        "easy": (7, 8, 9, 10),
        "medium": (9, 10, 11, 12, 13),
        "hard": (14, 15, 16, 17, 18),
    }[band]
    w = ctx.draw_choice("grid_w", _weighted(range(7, 19), favored_w))

    # Default teaching draws reserve one row so the source can shift downward.
    # An exact n_sevens override may lawfully fill the full height; in that
    # constrained case the decoy still teaches overwrite semantics while the
    # source necessarily starts at row zero.
    max_n = min(7, h)
    if teaching and "n_sevens" not in active:
        max_n = min(max_n, h - 1)
    favored_n = {
        "easy": (2, 3, 4),
        "medium": (3, 4, 5),
        "hard": (5, 6, 7),
    }[band]
    n = ctx.draw_choice("n_sevens", _weighted(range(2, max_n + 1), favored_n))
    return h, w, n


def _column_for_mode(w, mode, rng):
    if mode == "left":
        return 0
    if mode == "right":
        return w - 1
    if mode == "center":
        return w // 2
    candidates = [c for c in range(1, w - 1) if c != w // 2]
    if not candidates:
        raise RuntimeError("interior positional class has no available column")
    return rng.choice(candidates)


def _inside_triangle(r, c, bottom_row, source_col):
    vertical_reach = bottom_row - r
    return vertical_reach >= 0 and abs(c - source_col) <= vertical_reach


def generate(seed, sample_index, *, difficulty=None, **overrides):
    active = _validate_overrides(overrides)
    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=active,
    )
    profile = schedule_profile(seed, sample_index, band)
    untouched_shape = not any(name in active for name in ("grid_h", "grid_w", "n_sevens"))

    if profile == "canonical_core" and untouched_shape:
        h0, w0, n0 = ctx.draw_choice("canonical_profile", _CANONICAL_PROFILES)
        h = ctx.draw_choice("grid_h", [h0])
        w = ctx.draw_choice("grid_w", [w0])
        n_sevens = ctx.draw_choice("n_sevens", [n0])
    else:
        h, w, n_sevens = _draw_broad_dimensions(
            ctx, active, band, teaching=profile == "teaching"
        )

    if n_sevens > h:
        _incompatible("n_sevens cannot exceed grid_h", ("grid_h", "n_sevens"))

    mode = ctx.draw_choice("column_position", list(COLUMN_POSITIONS))
    column = _column_for_mode(w, mode, ctx.draw_rng("column_coordinate"))

    if profile == "teaching" and h > n_sevens:
        top_row = ctx.draw_rng("vertical_shift").randint(1, h - n_sevens)
    else:
        top_row = 0
    bottom_row = top_row + n_sevens - 1

    if "decoy_count" in active:
        decoy_count = ctx.draw_choice("decoy_count", list(range(5)))
    elif profile == "canonical_core":
        decoy_count = ctx.draw_choice("decoy_count", [0])
    else:
        decoy_count = ctx.draw_choice("decoy_count", [1, 2, 3, 4])

    grid = full_grid(h, w, 0)
    for r in range(top_row, bottom_row + 1):
        grid[r][column] = 7

    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0 and not _inside_triangle(r, c, bottom_row, column)
    ]
    if len(candidates) < decoy_count:
        _incompatible(
            "requested decoys do not fit outside the triangle",
            tuple(name for name in ("grid_h", "grid_w", "n_sevens", "decoy_count")
                  if name in active),
        )
    rng = ctx.draw_rng("decoys")
    for r, c in rng.sample(candidates, decoy_count):
        grid[r][c] = rng.choice(_DECOY_COLORS)
    return grid


def _analyse(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {}, ["grid must be a nonempty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {}, ["grid rows must be nonempty"]
    h, w = len(grid), len(grid[0])
    if not 5 <= h <= 16:
        errors.append(f"height {h} outside 5..16")
    if not 7 <= w <= 18:
        errors.append(f"width {w} outside 7..18")
    rectangular = True
    for r, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != w:
            errors.append(f"row {r} has invalid width")
            rectangular = False
            continue
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color 0..9")
    if not rectangular:
        return {"grid_h": h, "grid_w": w}, errors

    sevens = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7]
    if not 2 <= len(sevens) <= 7:
        errors.append(f"expected 2..7 color-7 cells, found {len(sevens)}")
    columns = {c for _, c in sevens}
    if len(columns) != 1:
        errors.append(f"color-7 cells span {len(columns)} columns, expected 1")
        source_col = min(columns) if columns else 0
    else:
        source_col = next(iter(columns))
    rows = sorted(r for r, _ in sevens)
    if rows and rows != list(range(rows[0], rows[-1] + 1)):
        errors.append("color-7 cells must form a contiguous vertical column")
    top_row = rows[0] if rows else 0
    bottom_row = rows[-1] if rows else -1

    decoys = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 7):
                continue
            decoys.append((r, c, value))
            if value not in _DECOY_COLORS:
                errors.append(f"decoy at ({r},{c}) uses reserved/unsupported color {value}")
            if bottom_row >= 0 and _inside_triangle(r, c, bottom_row, source_col):
                errors.append(f"decoy at ({r},{c}) lies inside the authority triangle")
    if len(decoys) > 4:
        errors.append(f"expected at most 4 decoys, found {len(decoys)}")

    if source_col == 0:
        position = "left"
    elif source_col == w - 1:
        position = "right"
    elif source_col == w // 2:
        position = "center"
    else:
        position = "interior"
    info = {
        "grid_h": h,
        "grid_w": w,
        "n_sevens": len(sevens),
        "column_position": position,
        "decoy_count": len(decoys),
        "top_row": top_row,
        "bottom_row": bottom_row,
        "source_col": source_col,
        "decoys": tuple(decoys),
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _analyse(grid)[1]


def observe_overrides(grid):
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: info[name] for name in AXES}


def strict_canonical_like(grid):
    info, errors = _analyse(grid)
    if errors:
        return errors
    reasons = []
    if info["top_row"] != 0:
        reasons.append("canonical-like source column must begin in row 0")
    if info["decoy_count"] != 0:
        reasons.append("canonical-like input must contain no decoys")
    return reasons


def rule_mirror(grid):
    """Pure Python mirror used only by tests and semantic diagnostics."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    for r in range(info["grid_h"]):
        reach = info["bottom_row"] - r
        for c in range(info["grid_w"]):
            distance = abs(c - info["source_col"])
            if reach >= 0 and distance <= reach:
                out[r][c] = 7 if distance % 2 == 0 else 8
    return out


def _line_length_triangle(grid):
    """Wrong shortcut: stop expansion at the top of the source line."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = full_grid(info["grid_h"], info["grid_w"], 0)
    first_row = info["bottom_row"] - info["n_sevens"] + 1
    for r in range(first_row, info["bottom_row"] + 1):
        reach = info["bottom_row"] - r
        for c in range(info["grid_w"]):
            distance = abs(c - info["source_col"])
            if distance <= reach:
                out[r][c] = 7 if distance % 2 == 0 else 8
    return out


def _preserve_decoys(grid):
    """Wrong shortcut: transform the triangle but retain outside input cells."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = rule_mirror(grid)
    for r, c, value in info["decoys"]:
        out[r][c] = value
    return out


def _has_shifted_column(grid):
    info, errors = _analyse(grid)
    return not errors and info["top_row"] > 0


def _has_erasable_decoy(grid):
    info, errors = _analyse(grid)
    return not errors and info["decoy_count"] > 0


SEMANTIC_WITNESSES = {
    "shifted_column": _has_shifted_column,
    "erasable_decoy": _has_erasable_decoy,
}
SEMANTIC_RIVALS = {
    "line_length_triangle": _line_length_triangle,
    "preserve_decoys": _preserve_decoys,
}
WITNESS_RIVALS = {
    "shifted_column": ["line_length_triangle"],
    "erasable_decoy": ["preserve_decoys"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    reasons = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    saw_shifted = False
    saw_decoy = False
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output does not match the selected rule")
        saw_shifted |= info["top_row"] > 0
        saw_decoy |= info["decoy_count"] > 0
    if not saw_shifted:
        reasons.append("demonstrations do not refute the line-length-height shortcut")
    if not saw_decoy:
        reasons.append("demonstrations do not refute the preserve-decoys shortcut")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        _, errors = _analyse(query["input"])
        if errors:
            reasons.append(f"query malformed: {errors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the selected rule")
    return reasons
