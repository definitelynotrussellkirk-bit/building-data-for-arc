"""Generator for ARC task 673ef223 / ec1260207f71.

Two equal vertical red bars sit on opposite side edges in separate row
bands. Cyan dots beside one bar select row offsets. The rule joins each dot
to its bar, changes the dot to magenta, and fills the corresponding rows
beside the other bar.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ec1260207f71"
VERSION = "3.0.0"
TASK_ID = "ec1260207f71"
RULE_HASH = "8b7e24f62fab"

SUMMARY = (
    "Place equal red bars on the left and right edges in separated row "
    "bands. Put one to five cyan dots on distinct rows beside exactly one "
    "bar. Each dot selects a bar-relative row offset: join that dot inward "
    "to its red bar and paint the matching row beside the plain bar."
)

INVARIANTS = [
    "the input is a 14..28 by 7..16 zero-background grid",
    "equal contiguous red bars of length 4..8 occupy the two side edges",
    "the bars are in disjoint row bands separated by at least two blank rows",
    "one to five cyan dots occupy distinct rows of exactly one bar",
    "every cyan dot is strictly inside the canvas and inward of its bar",
    "the output has the same dimensions as the input",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 14..28",
        "valid": "14..28",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 7..16",
        "valid": "7..16",
    },
    "dot_side": {
        "type": "str",
        "default": "rng left|right",
        "valid": "left|right",
    },
    "dot_band": {
        "type": "str",
        "default": "rng upper|lower",
        "valid": "upper|lower",
    },
}

_VALID_H = (14, 28)
_VALID_W = (7, 16)
_PROFILE_PRIOR = 0.07
_BAND_BOUNDS = {
    "easy": ((16, 20), (8, 10), (4, 5), (1, 2)),
    "medium": ((19, 23), (9, 13), (5, 7), (2, 4)),
    "hard": ((22, 28), (12, 16), (6, 8), (3, 5)),
}

# These are the four public input profiles. Dot columns are stored in the
# physical orientation named by dot_side.
_PROFILE_SPECS = (
    {
        "height": 20,
        "width": 10,
        "length": 5,
        "dot_start": 1,
        "plain_start": 11,
        "dot_side": "left",
        "dots": ((1, 7), (3, 5)),
    },
    {
        "height": 19,
        "width": 8,
        "length": 4,
        "dot_start": 1,
        "plain_start": 11,
        "dot_side": "left",
        "dots": ((2, 4),),
    },
    {
        "height": 20,
        "width": 10,
        "length": 6,
        "dot_start": 3,
        "plain_start": 13,
        "dot_side": "right",
        "dots": ((1, 6), (2, 2), (4, 4)),
    },
    {
        "height": 21,
        "width": 12,
        "length": 6,
        "dot_start": 1,
        "plain_start": 14,
        "dot_side": "left",
        "dots": ((1, 8), (2, 7), (4, 4)),
    },
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    for label, bounds in (("grid_h", _VALID_H), ("grid_w", _VALID_W)):
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{label} must be an integer")
        if not bounds[0] <= value <= bounds[1]:
            raise ValueError(
                f"{label} must be in {bounds[0]}..{bounds[1]}"
            )

    for label, options in (
        ("dot_side", ("left", "right")),
        ("dot_band", ("upper", "lower")),
    ):
        value = overrides.get(label)
        if value is None:
            continue
        if type(value) is not str or value not in options:
            rendered = "|".join(options)
            raise ValueError(f"{label} must be {rendered}")


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


def _scene_analysis(grid):
    """Return ``(coerced_grid, features, errors)`` for a proposed input."""
    if not isinstance(grid, list) or not grid:
        return None, None, ["grid must be a non-empty list"]
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return None, None, [
            "grid rows must be non-empty lists or digit strings"
        ]

    coerced = _coerce_grid(grid)
    width = len(coerced[0])
    if any(len(row) != width for row in coerced):
        return coerced, None, ["grid must be rectangular"]

    height = len(coerced)
    errors = []
    if not _VALID_H[0] <= height <= _VALID_H[1]:
        errors.append("grid height must be in 14..28")
    if not _VALID_W[0] <= width <= _VALID_W[1]:
        errors.append("grid width must be in 7..16")
    if any(
        type(value) is not int or value not in (0, 2, 8)
        for row in coerced
        for value in row
    ):
        errors.append("input cells must use only integer colors 0, 2, and 8")
        return coerced, None, errors

    interior_red = [
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == 2 and col not in (0, width - 1)
    ]
    if interior_red:
        errors.append("red cells may occur only on the two side edges")

    left_rows = [
        row for row, values in enumerate(coerced) if values[0] == 2
    ]
    right_rows = [
        row for row, values in enumerate(coerced) if values[-1] == 2
    ]
    if not left_rows or not right_rows:
        errors.append("both side edges must contain a red bar")
        return coerced, None, errors

    for label, rows in (("left", left_rows), ("right", right_rows)):
        expected = list(range(rows[0], rows[-1] + 1))
        if rows != expected:
            errors.append(f"the {label} red bar must be contiguous")
    if len(left_rows) != len(right_rows):
        errors.append("the two red bars must have equal length")
    length = len(left_rows)
    if not 4 <= length <= 8 or not 4 <= len(right_rows) <= 8:
        errors.append("each red bar must have length 4..8")
    if errors:
        return coerced, None, errors

    left_start = left_rows[0]
    right_start = right_rows[0]
    if left_start < right_start:
        upper_start, lower_start = left_start, right_start
    else:
        upper_start, lower_start = right_start, left_start
    if lower_start < upper_start + length + 2:
        errors.append(
            "red bars must be separated by at least two blank rows"
        )

    cyan = [
        (row, col)
        for row, values in enumerate(coerced)
        for col, value in enumerate(values)
        if value == 8
    ]
    if not 1 <= len(cyan) <= 5:
        errors.append("the input must contain 1..5 cyan dots")
    if any(col in (0, width - 1) for _row, col in cyan):
        errors.append("cyan dots must be strictly inside the side edges")
    if len({row for row, _col in cyan}) != len(cyan):
        errors.append("cyan dots must occupy distinct rows")
    if errors:
        return coerced, None, errors

    dot_rows = {row for row, _col in cyan}
    candidates = []
    if dot_rows.issubset(set(left_rows)):
        candidates.append(("left", left_start))
    if dot_rows.issubset(set(right_rows)):
        candidates.append(("right", right_start))
    if len(candidates) != 1:
        errors.append("all cyan dots must belong to exactly one red bar")
        return coerced, None, errors

    dot_side, dot_start = candidates[0]
    plain_start = right_start if dot_side == "left" else left_start
    dot_band = "upper" if dot_start < plain_start else "lower"
    dots = tuple(sorted(
        (row - dot_start, col) for row, col in cyan
    ))
    features = {
        "grid_h": height,
        "grid_w": width,
        "length": length,
        "left_start": left_start,
        "right_start": right_start,
        "dot_start": dot_start,
        "plain_start": plain_start,
        "dot_side": dot_side,
        "dot_band": dot_band,
        "dots": dots,
    }
    return coerced, features, errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    _coerced, _features, errors = _scene_analysis(grid)
    return errors


def observe_overrides(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": features["grid_h"],
        "grid_w": features["grid_w"],
        "dot_side": features["dot_side"],
        "dot_band": features["dot_band"],
    }


def rule_mirror(grid):
    coerced, features, errors = _scene_analysis(grid)
    if errors:
        raise ValueError("invalid scene: " + "; ".join(errors))

    output = [row[:] for row in coerced]
    width = features["grid_w"]
    dot_side = features["dot_side"]
    dot_col = 0 if dot_side == "left" else width - 1
    plain_col = width - 1 if dot_side == "left" else 0

    for offset, marker_col in features["dots"]:
        dot_row = features["dot_start"] + offset
        plain_row = features["plain_start"] + offset
        lo, hi = sorted((dot_col, marker_col))
        for col in range(lo + 1, hi):
            output[dot_row][col] = 8
        output[dot_row][marker_col] = 4
        for col in range(width):
            if col != plain_col:
                output[plain_row][col] = 8
    return output


def _profile_signature_from_features(features):
    width = features["grid_w"]
    if features["dot_side"] == "left":
        normalized_dots = features["dots"]
    else:
        normalized_dots = tuple(sorted(
            (offset, width - 1 - col)
            for offset, col in features["dots"]
        ))
    return (
        features["grid_h"],
        width,
        features["length"],
        features["dot_start"],
        features["plain_start"],
        features["dot_band"],
        normalized_dots,
    )


def _spec_signature(spec):
    dots = spec["dots"]
    if spec["dot_side"] == "right":
        dots = tuple(sorted(
            (offset, spec["width"] - 1 - col)
            for offset, col in dots
        ))
    return (
        spec["height"],
        spec["width"],
        spec["length"],
        spec["dot_start"],
        spec["plain_start"],
        "upper",
        dots,
    )


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    _spec_signature(spec) for spec in _PROFILE_SPECS
)


def canonical_profile_signature(grid):
    _coerced, features, errors = _scene_analysis(grid)
    if errors:
        return None
    signature = _profile_signature_from_features(features)
    return (
        signature
        if signature in _CANONICAL_PROFILE_SIGNATURES
        else None
    )


def is_canonical_profile(grid):
    return canonical_profile_signature(grid) is not None


def _draw_scene(
    height,
    width,
    length,
    upper_start,
    lower_start,
    dot_side,
    dot_band,
    dots,
):
    dot_start = upper_start if dot_band == "upper" else lower_start
    plain_start = lower_start if dot_band == "upper" else upper_start
    left_start = dot_start if dot_side == "left" else plain_start
    right_start = plain_start if dot_side == "left" else dot_start

    grid = full_grid(height, width, 0)
    for offset in range(length):
        grid[left_start + offset][0] = 2
        grid[right_start + offset][width - 1] = 2
    for offset, col in dots:
        grid[dot_start + offset][col] = 8
    return grid


def _draw_profile(spec, desired_side):
    dots = spec["dots"]
    if desired_side != spec["dot_side"]:
        dots = tuple(
            (offset, spec["width"] - 1 - col)
            for offset, col in dots
        )
    grid = _draw_scene(
        spec["height"],
        spec["width"],
        spec["length"],
        spec["dot_start"],
        spec["plain_start"],
        desired_side,
        "upper",
        dots,
    )
    if canonical_profile_signature(grid) != _spec_signature(spec):
        raise AssertionError("constructed public profile drifted")
    return grid


def _draw_general(
    height,
    width,
    band,
    dot_side,
    dot_band,
    rng,
):
    _height_bounds, _width_bounds, length_bounds, dot_bounds = (
        _BAND_BOUNDS[band]
    )
    maximum_length = min(8, (height - 2) // 2)
    length_lo = min(length_bounds[0], maximum_length)
    length_hi = min(length_bounds[1], maximum_length)
    length = rng.randint(length_lo, length_hi)

    start_pairs = [
        (upper, lower)
        for upper in range(height - length + 1)
        for lower in range(upper + length + 2, height - length + 1)
    ]
    upper_start, lower_start = rng.choice(start_pairs)

    dot_hi = min(dot_bounds[1], length, 5)
    dot_lo = min(dot_bounds[0], dot_hi)
    dot_count = rng.randint(dot_lo, dot_hi)
    offsets = sorted(rng.sample(range(length), dot_count))
    dots = tuple(
        (offset, rng.randint(1, width - 2))
        for offset in offsets
    )
    return _draw_scene(
        height,
        width,
        length,
        upper_start,
        lower_start,
        dot_side,
        dot_band,
        dots,
    )


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
    has_override = any(
        overrides.get(label) is not None for label in AXES
    )

    profile_index = None
    if not has_override:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )

    if profile_index is not None:
        spec = _PROFILE_SPECS[profile_index]
        ctx.draw_int("grid_h", spec["height"], spec["height"])
        ctx.draw_int("grid_w", spec["width"], spec["width"])
        dot_side = ctx.draw_choice("dot_side", ("left", "right"))
        ctx.draw_choice("dot_band", ("upper",))
        grid = _draw_profile(spec, dot_side)
    else:
        height_bounds, width_bounds, _length_bounds, _dot_bounds = (
            _BAND_BOUNDS[band]
        )
        if overrides.get("grid_h") is not None:
            height = ctx.draw_int("grid_h", *_VALID_H)
        else:
            height = ctx.draw_int("grid_h", *height_bounds)
        if overrides.get("grid_w") is not None:
            width = ctx.draw_int("grid_w", *_VALID_W)
        else:
            width = ctx.draw_int("grid_w", *width_bounds)
        dot_side = ctx.draw_choice("dot_side", ("left", "right"))
        dot_band = ctx.draw_choice("dot_band", ("upper", "lower"))
        grid = _draw_general(
            height,
            width,
            band,
            dot_side,
            dot_band,
            ctx.draw_rng("layout"),
        )

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
