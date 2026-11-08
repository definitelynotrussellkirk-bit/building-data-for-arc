"""Generator for separator-count compression puzzle 1190e5a7.

The input contains exactly two nonzero colours.  One is a strict-majority
background.  The other paints complete separator rows and columns.  The answer
is a fresh ``(separator_rows + 1) x (separator_cols + 1)`` grid filled with the
background colour.
"""
from __future__ import annotations

from collections import Counter
from itertools import product
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1c1ef857c9e2"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "13aa128bacd8"
SUMMARY = (
    "Count the complete rows and columns painted in the separator colour. "
    "Return a (row-count + 1) by (column-count + 1) grid filled with the "
    "strict-majority background colour."
)
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 20
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "rectangular 7..27 by 7..27 input with literal ARC colours",
    "exactly two distinct nonzero colours",
    "one strict-majority background colour",
    "1..5 complete interior separator rows and 1..5 complete interior separator columns",
    "every separator-colour cell belongs to one of those complete rows or columns",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical profile schedule", "valid": "7..27"},
    "grid_w": {"type": "int", "default": "canonical profile schedule", "valid": "7..27"},
    "n_sep_rows": {"type": "int", "default": "canonical profile schedule", "valid": "1..5"},
    "n_sep_cols": {"type": "int", "default": "canonical profile schedule", "valid": "1..5"},
    "bg_color": {"type": "color", "default": "rng nonzero", "valid": "1..9"},
    "sep_color": {"type": "color", "default": "rng nonzero distinct from bg_color", "valid": "1..9"},
}

# Feasibility depends on numeric values rather than a short finite list.  Joint
# failures are reported dynamically with ``ValueError.incompatible_axes``.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Canonical dimensions are retained on the default path, while all twenty
# asymmetric 1..5 row/column count pairs are scheduled.  This removes a
# row-count -> column-count shortcut and widens the intrinsically small output
# alphabet without leaving the canonical size/palette family.
_CANONICAL_EXACT_PROFILES = (
    (11, 11, 2, 1),
    (15, 15, 1, 3),
    (27, 27, 5, 4),
    (22, 22, 4, 2),
)
_CANONICAL_DIMENSIONS = (11, 15, 22, 27)
_COUNT_PAIRS = tuple(
    (n_rows, n_cols)
    for n_rows in range(1, 6)
    for n_cols in range(1, 6)
    if n_rows != n_cols
)


def _default_dimension(index: int, n_rows: int, n_cols: int) -> int:
    preferred = _CANONICAL_DIMENSIONS[index % len(_CANONICAL_DIMENSIONS)]
    ordered = tuple(
        dimension for dimension in _CANONICAL_DIMENSIONS if dimension >= preferred
    ) + tuple(
        dimension for dimension in _CANONICAL_DIMENSIONS if dimension < preferred
    )
    for dimension in ordered:
        if 2 * (dimension - n_rows) * (dimension - n_cols) > dimension * dimension:
            return dimension
    raise AssertionError("27x27 must realize every 1..5 asymmetric count pair")


_DEFAULT_PROFILES = tuple(
    (dimension, dimension, n_rows, n_cols)
    for index, (n_rows, n_cols) in enumerate(_COUNT_PAIRS)
    for dimension in (_default_dimension(index, n_rows, n_cols),)
)
SCHEDULE_PROFILES = tuple(
    f"rows_{n_rows}_cols_{n_cols}_size_{height}"
    for height, _width, n_rows, n_cols in _DEFAULT_PROFILES
)
_DIFFICULTIES = {None, "easy", "medium", "hard"}
_NUMERIC_AXES = ("grid_h", "grid_w", "n_sep_rows", "n_sep_cols")
_COLOR_AXES = ("bg_color", "sep_color")
_AXIS_BOUNDS = {
    "grid_h": (7, 27),
    "grid_w": (7, 27),
    "n_sep_rows": (1, 5),
    "n_sep_cols": (1, 5),
    "bg_color": (1, 9),
    "sep_color": (1, 9),
}


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the finite semantic profile selected by the keyed seed/index lane."""
    _validate_call(seed, sample_index, difficulty, {})
    slot = (2 * seed + sample_index) % LESSON_SCHEDULE_PERIOD
    return SCHEDULE_PROFILES[slot]


def _incompatible(message: str, *axes: str) -> ValueError:
    error = ValueError(message)
    error.incompatible_axes = tuple(sorted(set(axes)))  # type: ignore[attr-defined]
    return error


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")

    for axis, value in overrides.items():
        if value is None:
            continue
        lo, hi = _AXIS_BOUNDS[axis]
        if type(value) is not int:
            raise TypeError(f"{axis} must be an integer in [{lo}, {hi}] (not bool)")
        if not lo <= value <= hi:
            raise ValueError(f"{axis}={value} outside [{lo}, {hi}]")

    bg = overrides.get("bg_color")
    sep = overrides.get("sep_color")
    if bg is not None and sep is not None and bg == sep:
        raise _incompatible(
            "bg_color and sep_color must be distinct",
            "bg_color",
            "sep_color",
        )


def _candidate_values(default: int, explicit: int | None, fallback: int) -> tuple[int, ...]:
    if explicit is not None:
        return (explicit,)
    return tuple(dict.fromkeys((default, fallback)))


def _numeric_completion(seed: int, sample_index: int, overrides: dict[str, Any]) -> dict[str, int]:
    """Complete dependent exact axes without changing an explicit request.

    A larger unpinned dimension and a smaller unpinned line count are the
    monotone feasibility extrema.  Trying ``default`` then that extremum for
    each axis is therefore complete for this grammar while requiring at most
    sixteen candidates.
    """
    slot = (2 * seed + sample_index) % LESSON_SCHEDULE_PERIOD
    default_h, default_w, default_rows, default_cols = _DEFAULT_PROFILES[slot]
    candidates = {
        "grid_h": _candidate_values(default_h, overrides.get("grid_h"), 27),
        "grid_w": _candidate_values(default_w, overrides.get("grid_w"), 27),
        "n_sep_rows": _candidate_values(default_rows, overrides.get("n_sep_rows"), 1),
        "n_sep_cols": _candidate_values(default_cols, overrides.get("n_sep_cols"), 1),
    }

    for h, w, n_rows, n_cols in product(
        candidates["grid_h"],
        candidates["grid_w"],
        candidates["n_sep_rows"],
        candidates["n_sep_cols"],
    ):
        if n_rows > h - 2 or n_cols > w - 2:
            continue
        background_cells = (h - n_rows) * (w - n_cols)
        if 2 * background_cells <= h * w:
            continue
        return {
            "grid_h": h,
            "grid_w": w,
            "n_sep_rows": n_rows,
            "n_sep_cols": n_cols,
        }

    explicit_axes = tuple(
        axis for axis in _NUMERIC_AXES if overrides.get(axis) is not None
    )
    raise _incompatible(
        "requested dimensions and separator counts cannot preserve interior "
        "lines with a strict-majority background",
        *explicit_axes,
    )


def _analyse(grid: Any) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"], {}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], {}

    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], {}
    height = len(grid)

    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal integer ARC colours 0..9, not booleans"], {
            "grid_h": height,
            "grid_w": width,
        }
    if not 7 <= height <= 27 or not 7 <= width <= 27:
        errors.append("grid dimensions must each lie in 7..27")

    counts = Counter(value for row in grid for value in row)
    colors = set(counts)
    if 0 in colors:
        errors.append("background and separator colours must both be nonzero")
    if len(colors) != 2:
        errors.append(f"expected exactly two colours, found {len(colors)}")
    if errors:
        return errors, {"grid_h": height, "grid_w": width}

    ordered = counts.most_common()
    if len(ordered) != 2 or ordered[0][1] == ordered[1][1]:
        return ["background colour must be uniquely most common"], {
            "grid_h": height,
            "grid_w": width,
        }
    bg, bg_count = ordered[0]
    sep = ordered[1][0]
    if 2 * bg_count <= height * width:
        errors.append("background colour must be a strict majority")

    sep_rows = tuple(
        r for r, row in enumerate(grid) if all(value == sep for value in row)
    )
    sep_cols = tuple(
        c
        for c in range(width)
        if all(grid[r][c] == sep for r in range(height))
    )
    if not 1 <= len(sep_rows) <= 5:
        errors.append(f"expected 1..5 complete separator rows, found {len(sep_rows)}")
    if not 1 <= len(sep_cols) <= 5:
        errors.append(f"expected 1..5 complete separator columns, found {len(sep_cols)}")
    if any(row in (0, height - 1) for row in sep_rows):
        errors.append("separator rows must be interior")
    if any(col in (0, width - 1) for col in sep_cols):
        errors.append("separator columns must be interior")

    row_set, col_set = set(sep_rows), set(sep_cols)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            expected = sep if r in row_set or c in col_set else bg
            if value != expected:
                errors.append(
                    f"cell ({r},{c}) breaks the complete row/column separator pattern"
                )
                return errors, {
                    "grid_h": height,
                    "grid_w": width,
                    "bg_color": bg,
                    "sep_color": sep,
                    "n_sep_rows": len(sep_rows),
                    "n_sep_cols": len(sep_cols),
                    "sep_rows": sep_rows,
                    "sep_cols": sep_cols,
                }

    return errors, {
        "grid_h": height,
        "grid_w": width,
        "n_sep_rows": len(sep_rows),
        "n_sep_cols": len(sep_cols),
        "bg_color": bg,
        "sep_color": sep,
        "sep_rows": sep_rows,
        "sep_cols": sep_cols,
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    """Validate the complete authority-safe input grammar."""
    del difficulty, meta
    return _analyse(grid)[0]


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every declared exact axis from the returned grid."""
    errors, facts = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {axis: int(facts[axis]) for axis in AXES}


def strict_canonical_like(grid: Any) -> list[str]:
    errors, facts = _analyse(grid)
    if errors:
        return errors
    if (facts["grid_h"], facts["grid_w"]) not in {
        (dimension, dimension) for dimension in _CANONICAL_DIMENSIONS
    }:
        return ["input does not match a canonical input-size profile"]
    return []


def rule_mirror(grid: Any) -> list[list[int]]:
    """Independent Python mirror of the pinned Racket rule."""
    errors, facts = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return full_grid(
        facts["n_sep_rows"] + 1,
        facts["n_sep_cols"] + 1,
        facts["bg_color"],
    )


def _rival_omit_plus_one(grid: Any) -> list[list[int]]:
    facts = observe_overrides(grid)
    return full_grid(facts["n_sep_rows"], facts["n_sep_cols"], facts["bg_color"])


def _rival_transpose_counts(grid: Any) -> list[list[int]]:
    facts = observe_overrides(grid)
    return full_grid(
        facts["n_sep_cols"] + 1,
        facts["n_sep_rows"] + 1,
        facts["bg_color"],
    )


def _rival_separator_color(grid: Any) -> list[list[int]]:
    facts = observe_overrides(grid)
    return full_grid(
        facts["n_sep_rows"] + 1,
        facts["n_sep_cols"] + 1,
        facts["sep_color"],
    )


def _rival_rows_control_both_dimensions(grid: Any) -> list[list[int]]:
    facts = observe_overrides(grid)
    size = facts["n_sep_rows"] + 1
    return full_grid(size, size, facts["bg_color"])


def _valid_facts(grid: Any) -> dict[str, int] | None:
    errors, facts = _analyse(grid)
    if errors:
        return None
    return {axis: int(facts[axis]) for axis in AXES}


def _witness_plus_one(grid: Any) -> bool:
    return _valid_facts(grid) is not None


def _witness_asymmetric_counts(grid: Any) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["n_sep_rows"] != facts["n_sep_cols"])


def _witness_distinct_roles(grid: Any) -> bool:
    facts = _valid_facts(grid)
    return bool(facts and facts["bg_color"] != facts["sep_color"])


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "omit_plus_one": _rival_omit_plus_one,
    "transpose_row_column_counts": _rival_transpose_counts,
    "fill_with_separator_color": _rival_separator_color,
    "rows_control_both_dimensions": _rival_rows_control_both_dimensions,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Any], list[list[int]]]] = {}
SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "plus_one_changes_shape": _witness_plus_one,
    "row_and_column_counts_are_asymmetric": _witness_asymmetric_counts,
    "background_and_separator_roles_are_distinct": _witness_distinct_roles,
    "both_axes_control_output_shape": _witness_asymmetric_counts,
}
WITNESS_RIVALS = {
    "plus_one_changes_shape": ["omit_plus_one"],
    "row_and_column_counts_are_asymmetric": ["transpose_row_column_counts"],
    "background_and_separator_roles_are_distinct": ["fill_with_separator_color"],
    "both_axes_control_output_shape": ["rows_control_both_dimensions"],
}


def lesson_identifiable(demos: Any, query: Any) -> list[str]:
    """Return concrete reasons a declared competitor remains ambiguous."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    reasons: list[str] = []
    checked: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match the canonical rule")
            continue
        checked.append(pair)

    query_grid = query.get("input") if isinstance(query, dict) else query
    query_errors = self_check(query_grid)
    if query_errors:
        reasons.append(f"query input is unlawful: {query_errors[0]}")
        return reasons
    query_answer = rule_mirror(query_grid)

    if len(checked) == len(demos):
        for name, rival in LESSON_COMPETITORS.items():
            if all(rival(pair["input"]) == pair["output"] for pair in checked):
                if rival(query_grid) != query_answer:
                    reasons.append(
                        f"declared competitor {name!r} fits every demonstration "
                        "but changes the query answer"
                    )
    return reasons


def generate(seed: int, sample_index: int, *, difficulty: str | None = None, **overrides: Any) -> list[list[int]]:
    """Build one deterministic lawful input while honoring every exact axis."""
    _validate_call(seed, sample_index, difficulty, overrides)
    effective_numeric = _numeric_completion(seed, sample_index, overrides)

    # Pass resolved defaults through the public draw API so every exact axis has
    # keyed provenance while all caller-provided values remain unchanged.
    ctx_overrides = dict(effective_numeric)
    for axis in _COLOR_AXES:
        if overrides.get(axis) is not None:
            ctx_overrides[axis] = overrides[axis]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=ctx_overrides,
    )

    height = ctx.draw_int_strict("grid_h", 7, 27)
    width = ctx.draw_int_strict("grid_w", 7, 27)
    n_rows = ctx.draw_int_strict("n_sep_rows", 1, 5)
    n_cols = ctx.draw_int_strict("n_sep_cols", 1, 5)

    explicit_bg = overrides.get("bg_color")
    explicit_sep = overrides.get("sep_color")
    bg_exclude = {0}
    if explicit_sep is not None and explicit_bg is None:
        bg_exclude.add(explicit_sep)
    bg = ctx.draw_color("bg_color", exclude=bg_exclude)
    sep = ctx.draw_color("sep_color", exclude={0, bg})

    row_rng = ctx.draw_rng(f"separator_rows:{difficulty or 'all'}")
    col_rng = ctx.draw_rng(f"separator_cols:{difficulty or 'all'}")
    sep_rows = sorted(row_rng.sample(range(1, height - 1), n_rows))
    sep_cols = sorted(col_rng.sample(range(1, width - 1), n_cols))

    grid = full_grid(height, width, bg)
    for r in sep_rows:
        grid[r] = [sep] * width
    for c in sep_cols:
        for r in range(height):
            grid[r][c] = sep

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]
