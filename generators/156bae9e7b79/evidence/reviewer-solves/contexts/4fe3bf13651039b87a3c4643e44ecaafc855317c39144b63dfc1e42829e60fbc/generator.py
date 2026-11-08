"""Generator for ARC task 156bae9e7b79 — keyed triangular projection.

The input has a dense key row at row 0, gray background (5), and one vertical
cyan line (8).  Between the observed top and bottom of that line, row ``r``
reveals key-row cells within a radius ``min((width - 1) // 2, r - line_top)``
of the line.  The line itself remains cyan; everything outside the active
interval/radius is gray.

All canonical demonstrations put the line in the geometric center and extend it
to the bottom edge.  The ordinary three-role curriculum therefore includes a
canonical-scale centered/bottom-reaching draw plus left- and right-shifted lines
that stop one row early.  Either contrast draw refutes both strongest shortcuts:
using the fixed grid center and extending every line to the bottom.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "156bae9e7b79"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "01a0d2007d61"

SUMMARY = (
    "Row 0 is a dense color key with gray (5) at the column of one vertical "
    "cyan (8) line. From the observed line top through its observed bottom, "
    "copy key-row colors into an expanding triangle centered on that line; "
    "keep the line cyan and all cells outside the active triangle gray."
)

INVARIANTS = [
    "rectangular 9..15 by 9..15 ARC grid",
    "row 0 is dense and has gray only at the vertical-line column",
    "below row 0 only gray 5 and one contiguous vertical cyan 8 line occur",
    "the line column is one of the declared left, center, or right positions",
    "the line ends at the bottom row or exactly one row above it",
    "the complete input uses exactly 6..9 colors",
]

LINE_POSITIONS = ("center", "left", "right")
LINE_ENDS = ("bottom", "truncated")
SCHEDULE_PROFILES = ("canonical_core", "left_truncated", "right_truncated")
CANONICAL_PROFILES = {(9, 9, 6), (11, 11, 8), (13, 13, 9)}
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

AXES = {
    "grid_h": {"type": "int", "default": "scheduled by curriculum", "valid": "9..15"},
    "grid_w": {"type": "int", "default": "scheduled by curriculum", "valid": "9..15"},
    "n_colors": {"type": "int", "default": "scheduled by curriculum", "valid": "6..9"},
    "line_position": {
        "type": "str",
        "default": "scheduled modulo 3",
        "valid": "|".join(LINE_POSITIONS),
    },
    "line_end": {
        "type": "str",
        "default": "canonical core reaches bottom; contrasts are truncated",
        "valid": "|".join(LINE_ENDS),
    },
}

# Every Cartesian combination of the five declared axes is constructive.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_AVAILABLE_KEY_COLORS = (0, 1, 2, 3, 4, 6, 7, 9)
_CANONICAL_EXTRAS = {
    (9, 9, 6): (0, 1, 6, 9),
    (11, 11, 8): (2, 3, 4, 6, 7, 9),
    (13, 13, 9): (0, 1, 2, 3, 6, 7, 9),
}
_CANONICAL_LINE_TOP = {9: 3, 11: 5, 13: 5}
_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_schedule_arguments(sample_index: Any, difficulty: Any) -> None:
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer, not bool/float/string")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call_arguments(seed: Any, sample_index: Any, difficulty: Any) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer, not bool/float/string")
    _validate_schedule_arguments(sample_index, difficulty)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the exact semantic role used by the default curriculum."""
    del seed
    _validate_schedule_arguments(sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _line_col_for(width: int, position: str) -> int:
    if position == "center":
        return width // 2
    if position == "left":
        return width // 3
    if position == "right":
        return width - 1 - width // 3
    raise ValueError(f"unknown line position {position!r}")


def _position_for_line_col(width: int, line_col: int) -> str | None:
    for position in LINE_POSITIONS:
        if _line_col_for(width, position) == line_col:
            return position
    return None


def _default_axes(sample_index: int, difficulty: Any) -> dict[str, Any]:
    profile = schedule_profile(0, sample_index, difficulty)
    canonical_by_band = {
        "easy": (9, 9, 6),
        "medium": (11, 11, 8),
        "hard": (13, 13, 9),
    }
    contrast_by_band = {
        "easy": (10, 11, 7),
        "medium": (12, 13, 8),
        "hard": (14, 15, 9),
    }
    if profile == "canonical_core":
        dims = canonical_by_band.get(difficulty)
        if dims is None:
            dims = tuple(sorted(CANONICAL_PROFILES))[((int(sample_index) // 3) % 3)]
        grid_h, grid_w, n_colors = dims
        return {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "n_colors": n_colors,
            "line_position": "center",
            "line_end": "bottom",
        }

    grid_h, grid_w, n_colors = contrast_by_band.get(difficulty, (12, 14, 8))
    return {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_colors": n_colors,
        "line_position": "left" if profile == "left_truncated" else "right",
        "line_end": "truncated",
    }


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise KeyError(f"unknown override axis/axes: {unknown}")

    for name, lo, hi in (("grid_h", 9, 15), ("grid_w", 9, 15), ("n_colors", 6, 9)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer, not bool/float/string")
        if not lo <= value <= hi:
            raise ValueError(f"{name} override must be in {lo}..{hi}")

    for name, options in (("line_position", LINE_POSITIONS), ("line_end", LINE_ENDS)):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if not isinstance(value, str) or value not in options:
            raise ValueError(f"{name} override must be one of {options}, got {value!r}")


def _scheduled_int(ctx, overrides: dict[str, Any], name: str, default: int, lo: int, hi: int) -> int:
    bounds = (lo, hi) if overrides.get(name) is not None else (default, default)
    return ctx.draw_int_strict(name, *bounds)


def _scheduled_choice(
    ctx,
    overrides: dict[str, Any],
    name: str,
    default: str,
    options: Sequence[str],
) -> str:
    choices: Sequence[str] = options if overrides.get(name) is not None else (default,)
    return str(ctx.draw_choice(name, choices))


def _key_extras(height: int, width: int, n_colors: int, rng) -> list[int]:
    profile = (height, width, n_colors)
    if profile in _CANONICAL_EXTRAS:
        extras = list(_CANONICAL_EXTRAS[profile])
    else:
        pool = list(_AVAILABLE_KEY_COLORS)
        rng.shuffle(pool)
        extras = pool[: n_colors - 2]
    # Even canonical-scale draws vary their concrete key-row arrangement.
    rng.shuffle(extras)
    return extras


def _paint_key_row(
    grid: list[list[int]],
    *,
    line_col: int,
    extras: list[int],
    rng,
) -> None:
    slots = [col for col in range(len(grid[0])) if col != line_col]
    rng.shuffle(slots)

    values = list(extras)
    # Color 8 is itself a lawful key value.  Include it only when there is room
    # after exposing every palette color, so total palette cardinality is exact.
    if len(slots) > len(extras) and rng.random() < 0.5:
        values.append(8)
    while len(values) < len(slots):
        values.append(rng.choice(extras))
    rng.shuffle(values)

    grid[0][line_col] = 5
    for col, value in zip(slots, values, strict=True):
        grid[0][col] = value


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["grid must be a nonempty sequence of rows"]}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["grid rows must be nonempty sequences"]}

    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid must be rectangular"]}
    height = len(grid)
    if not 9 <= height <= 15:
        errors.append(f"grid height must be in 9..15, got {height}")
    if not 9 <= width <= 15:
        errors.append(f"grid width must be in 9..15, got {width}")

    bad_cells = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if type(value) is not int or not 0 <= value <= 9
    ]
    if bad_cells:
        row, col, value = bad_cells[0]
        errors.append(f"cell ({row},{col}) must be an integer ARC color 0..9, got {value!r}")
        return {"errors": errors}

    below_values = {grid[row][col] for row in range(1, height) for col in range(width)}
    illegal_below = sorted(below_values - {5, 8})
    if illegal_below:
        errors.append(f"below row 0 only colors 5 and 8 are allowed, got {illegal_below}")

    eights_by_col = {
        col: [row for row in range(1, height) if grid[row][col] == 8]
        for col in range(width)
    }
    eights_by_col = {col: rows for col, rows in eights_by_col.items() if rows}
    if len(eights_by_col) != 1:
        errors.append(f"expected one cyan column below row 0, got {sorted(eights_by_col)}")
        return {"errors": errors}

    line_col, line_rows = next(iter(eights_by_col.items()))
    if len(line_rows) < 2:
        errors.append("vertical cyan line must contain at least two cells")
    expected_rows = list(range(line_rows[0], line_rows[-1] + 1))
    if line_rows != expected_rows:
        errors.append("vertical cyan line must be contiguous")
    line_top, line_bottom = line_rows[0], line_rows[-1]

    position = _position_for_line_col(width, line_col)
    if position is None:
        legal = {name: _line_col_for(width, name) for name in LINE_POSITIONS}
        errors.append(f"line column {line_col} is not a declared position {legal}")

    if line_bottom not in (height - 1, height - 2):
        errors.append(
            f"line must end at bottom row {height - 1} or truncated row {height - 2}, got {line_bottom}"
        )
    line_end = "bottom" if line_bottom == height - 1 else "truncated"

    if grid[0][line_col] != 5:
        errors.append("row 0 at the vertical-line column must be gray 5")
    other_gray = [col for col in range(width) if col != line_col and grid[0][col] == 5]
    if other_gray:
        errors.append(f"row 0 must be dense; gray appears outside line column at {other_gray}")

    n_colors = len({value for row in grid for value in row})
    if not 6 <= n_colors <= 9:
        errors.append(f"input must use exactly 6..9 colors, got {n_colors}")

    return {
        "errors": errors,
        "facts": {
            "grid_h": height,
            "grid_w": width,
            "n_colors": n_colors,
            "line_position": position,
            "line_end": line_end,
            "line_col": line_col,
            "line_top": line_top,
            "line_bottom": line_bottom,
        },
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete generated-input grammar and requested controls."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact semantic axis directly from input pixels."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    facts = analysis["facts"]
    return {name: facts[name] for name in AXES}


def strict_canonical_like(grid) -> list[str]:
    """Accept the centered, bottom-reaching canonical-scale manifold."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    observed = observe_overrides(grid)
    profile = (observed["grid_h"], observed["grid_w"], observed["n_colors"])
    if profile not in CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is not one of {sorted(CANONICAL_PROFILES)}")
    if observed["line_position"] != "center":
        reasons.append("canonical line must be centered")
    if observed["line_end"] != "bottom":
        reasons.append("canonical line must reach the bottom")
    expected_top = _CANONICAL_LINE_TOP.get(observed["grid_h"])
    actual_top = _analyze(grid)["facts"]["line_top"]
    if expected_top is not None and actual_top != expected_top:
        reasons.append(f"canonical line top for height {observed['grid_h']} is {expected_top}, got {actual_top}")
    return reasons


def _render(
    grid: Sequence[Sequence[int]],
    *,
    projection_col: int,
    cyan_col: int,
    line_top: int,
    line_bottom: int,
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    key = list(grid[0])
    output = full_grid(height, width, 5)
    max_radius = (width - 1) // 2
    for row in range(line_top, line_bottom + 1):
        radius = min(max_radius, row - line_top)
        for col in range(width):
            if col == cyan_col:
                output[row][col] = 8
            elif projection_col - radius <= col <= projection_col + radius:
                output[row][col] = key[col]
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; the pinned canonical Racket rule is authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return _render(
        grid,
        projection_col=facts["line_col"],
        cyan_col=facts["line_col"],
        line_top=facts["line_top"],
        line_bottom=facts["line_bottom"],
    )


def _fixed_grid_center(grid) -> list[list[int]]:
    """Wrong shortcut: always project around the geometric grid center."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    facts = analysis["facts"]
    center = facts["grid_w"] // 2
    return _render(
        grid,
        projection_col=center,
        cyan_col=center,
        line_top=facts["line_top"],
        line_bottom=facts["line_bottom"],
    )


def _extends_to_bottom(grid) -> list[list[int]]:
    """Wrong shortcut: ignore the observed line bottom and continue to the edge."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    facts = analysis["facts"]
    return _render(
        grid,
        projection_col=facts["line_col"],
        cyan_col=facts["line_col"],
        line_top=facts["line_top"],
        line_bottom=facts["grid_h"] - 1,
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "fixed_grid_center": _fixed_grid_center,
    "extends_to_bottom": _extends_to_bottom,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_off_center(grid) -> bool:
    observed = observe_overrides(grid)
    return bool(observed) and observed["line_position"] != "center"


def _witness_truncated(grid) -> bool:
    observed = observe_overrides(grid)
    return bool(observed) and observed["line_end"] == "truncated"


SEMANTIC_WITNESSES = {
    "off_center_line": _witness_off_center,
    "truncated_line": _witness_truncated,
}
WITNESS_RIVALS = {
    "off_center_line": ["fixed_grid_center"],
    "truncated_line": ["extends_to_bottom"],
}


def _pair_errors(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label}: pair must contain input and output"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label}: invalid input: {errors[0]}"]
    try:
        expected = rule_mirror(pair["input"])
    except Exception as exc:
        return [f"{label}: rule mirror failed: {type(exc).__name__}: {exc}"]
    if pair["output"] != expected:
        return [f"{label}: output does not match the keyed triangular projection"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson only when a named canonical-fitting rival is ambiguous."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query"))
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(
            competitor(deepcopy(pair["input"])) == pair["output"] for pair in demos
        )
        if fits_demos and competitor(deepcopy(query["input"])) != query["output"]:
            reasons.append(f"named competitor {name!r} fits every demo but changes the query")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic, rejection-free keyed projection input."""
    _validate_call_arguments(seed, sample_index, difficulty)
    _validate_overrides(overrides)
    defaults = _default_axes(sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    grid_h = _scheduled_int(ctx, overrides, "grid_h", defaults["grid_h"], 9, 15)
    grid_w = _scheduled_int(ctx, overrides, "grid_w", defaults["grid_w"], 9, 15)
    n_colors = _scheduled_int(ctx, overrides, "n_colors", defaults["n_colors"], 6, 9)
    line_position = _scheduled_choice(
        ctx, overrides, "line_position", defaults["line_position"], LINE_POSITIONS
    )
    line_end = _scheduled_choice(ctx, overrides, "line_end", defaults["line_end"], LINE_ENDS)

    line_col = _line_col_for(grid_w, line_position)
    profile = (grid_h, grid_w, n_colors)
    if profile in CANONICAL_PROFILES and line_position == "center" and line_end == "bottom":
        line_top = _CANONICAL_LINE_TOP[grid_h]
    else:
        line_top_rng = ctx.draw_rng("line_top")
        line_top = line_top_rng.randint(2, min(5, grid_h - 3))
    line_bottom = grid_h - 1 if line_end == "bottom" else grid_h - 2

    grid = full_grid(grid_h, grid_w, 5)
    key_rng = ctx.draw_rng("key_row")
    extras = _key_extras(grid_h, grid_w, n_colors, key_rng)
    _paint_key_row(grid, line_col=line_col, extras=extras, rng=key_rng)
    for row in range(line_top, line_bottom + 1):
        grid[row][line_col] = 8

    errors = self_check(grid, meta={"overrides": overrides})
    if errors:
        raise RuntimeError("constructed invalid keyed-projection input: " + "; ".join(errors))
    expected = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_colors": n_colors,
        "line_position": line_position,
        "line_end": line_end,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid
