"""Generator for ARC task 329d82eaaa63.

A lawful input is a 0-background grid whose only nonzero cells are one to eight
pairwise-distinct seed colours on the top row.  Seeds are interior and at least
three columns apart.  The authoritative Racket rule repeats each seed straight
down on even rows and branches it one cell left and right on odd rows.

The four-profile default schedule is a teaching contract, not an extra input
axis: it always contains two single-seed cases, two multi-seed cases, two
canonical-height cases, and two taller cases.  Therefore any three-of-four
query rotation still refutes the main single-only, multi-only, branch-dropping,
and fixed-six-row shortcuts.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "329d82eaaa63"
TASK_ID = "329d82eaaa63"
VERSION = "3.0.0"
RULE_HASH = "c3b26f3f0fc8"

SUMMARY = (
    "Place 1..8 distinct nonzero seed colours only on row 0 of a 0-background "
    "grid. Seeds are interior and separated by at least three columns. For "
    "every seed at column c, paint its colour at c on every even row and at "
    "c-1 and c+1 on every odd row. The four-profile lesson schedule preserves "
    "single/multi-seed and height-6/taller counterexamples under query rotation."
)

INVARIANTS = [
    "grid size is 3..18 rows by 4..24 columns",
    "only row 0 contains nonzero input cells",
    "there are 1..8 top-row seeds with pairwise-distinct colours",
    "each seed is interior and adjacent seed columns differ by at least 3",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile schedule; 6 or keyed 7..18",
        "valid": "3..18",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile schedule; canonical 7/12 or keyed feasible 4..24",
        "valid": "4..24",
    },
    "n_seeds": {
        "type": "int",
        "default": "four-profile schedule; single or keyed feasible multi-seed",
        "valid": "1..8",
    },
}

# Feasibility depends on the numeric relation n_seeds <= _max_seeds(grid_w).
# The override checker recognizes the structured exception emitted below.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

SCHEDULE_PROFILES = (
    "canonical_single",
    "canonical_multi",
    "broad_single",
    "broad_multi",
)

_DIFFICULTIES = (None, "easy", "medium", "hard")


def schedule_profile(seed, sample_index, difficulty=None):
    """Name the deterministic lesson slot used by this draw."""
    del seed
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")


def _max_seeds(width: int) -> int:
    """Maximum interior columns with pairwise gap >=3 for this width."""
    if type(width) is not int or width < 4:
        return 0
    return 1 + (width - 3) // 3


@lru_cache(maxsize=None)
def _valid_column_sets(width: int, count: int) -> tuple[tuple[int, ...], ...]:
    """All sorted lawful seed-column tuples for a requested shape."""
    if type(width) is not int or type(count) is not int:
        return ()
    if not 4 <= width <= 24 or not 1 <= count <= 8:
        return ()
    return tuple(
        columns
        for columns in combinations(range(1, width - 1), count)
        if all(right - left >= 3 for left, right in zip(columns, columns[1:]))
    )


def _profile_defaults(
    seed: int, sample_index: int, difficulty: str | None
) -> dict[str, int]:
    """Choose a feasible default triple before any exact axis is drawn."""
    profile = schedule_profile(seed, sample_index, difficulty)
    rng = stable_rng(
        seed,
        f"{TASK_ID}|{sample_index}|profile-defaults|{difficulty}",
        VERSION,
    )
    if profile == "canonical_single":
        return {"grid_h": 6, "grid_w": 7, "n_seeds": 1}
    if profile == "canonical_multi":
        return {"grid_h": 6, "grid_w": 12, "n_seeds": 3}
    if profile == "broad_single":
        return {
            "grid_h": rng.randint(7, 18),
            "grid_w": rng.randint(4, 24),
            "n_seeds": 1,
        }

    count = rng.randint(2, 8)
    return {
        "grid_h": rng.randint(7, 18),
        "grid_w": rng.randint(3 * count, 24),
        "n_seeds": count,
    }


def _effective_axis_values(
    seed: int,
    sample_index: int,
    difficulty: str | None,
    overrides: dict[str, Any],
) -> dict[str, int]:
    """Resolve dependent defaults without mutating any explicitly drawn axis."""
    effective = _profile_defaults(seed, sample_index, difficulty)
    effective.update({name: value for name, value in overrides.items() if value is not None})

    explicit_width = overrides.get("grid_w") is not None
    explicit_count = overrides.get("n_seeds") is not None
    if explicit_width and not explicit_count:
        effective["n_seeds"] = min(effective["n_seeds"], _max_seeds(effective["grid_w"]))
    elif explicit_count and not explicit_width:
        effective["grid_w"] = max(effective["grid_w"], 4 if effective["n_seeds"] == 1 else 3 * effective["n_seeds"])
    return effective


def _incompatible_axes(message: str, *axes: str) -> ValueError:
    error = ValueError(message)
    error.incompatible_axes = tuple(axes)
    return error


def _grid_errors(grid) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"], {}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"], {}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], {}

    height = len(grid)
    if not 3 <= height <= 18:
        errors.append(f"grid height {height} outside 3..18")
    if not 4 <= width <= 24:
        errors.append(f"grid width {width} outside 4..24")

    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                errors.append("cells must be literal ARC integers 0..9")
                return errors, {"grid_h": height, "grid_w": width}

    if any(value != 0 for row in grid[1:] for value in row):
        errors.append("rows 1+ must contain only background 0")

    columns = tuple(index for index, value in enumerate(grid[0]) if value != 0)
    colors = tuple(grid[0][column] for column in columns)
    if not 1 <= len(columns) <= 8:
        errors.append(f"expected 1..8 top-row seeds, found {len(columns)}")
    if any(column in (0, width - 1) for column in columns):
        errors.append("seed columns must be interior so both odd-row branches fit")
    if len(colors) != len(set(colors)):
        errors.append("seed colours must be pairwise distinct")
    if any(right - left < 3 for left, right in zip(columns, columns[1:])):
        errors.append("adjacent seed columns must differ by at least 3")

    return errors, {
        "grid_h": height,
        "grid_w": width,
        "n_seeds": len(columns),
        "seed_columns": columns,
        "seed_colors": colors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete authority-safe input grammar."""
    del meta
    if difficulty not in _DIFFICULTIES:
        return [f"unknown difficulty: {difficulty!r}"]
    return _grid_errors(grid)[0]


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned grid."""
    errors, facts = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_seeds": facts["n_seeds"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    errors, facts = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    return {
        **observe_overrides(grid),
        "single_seed": facts["n_seeds"] == 1,
        "multiple_seeds": facts["n_seeds"] >= 2,
        "height_over_six": facts["grid_h"] > 6,
        "odd_row_branching_visible": facts["grid_h"] >= 2,
        "seed_columns": facts["seed_columns"],
    }


def strict_canonical_like(grid) -> list[str]:
    """The generator's lawful grammar is the intended canonical extension."""
    return self_check(grid)


def _paint(grid, selected_columns: tuple[int, ...] | None = None) -> list[list[int]]:
    errors, facts = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    selected = set(facts["seed_columns"] if selected_columns is None else selected_columns)
    height, width = facts["grid_h"], facts["grid_w"]
    output = full_grid(height, width, 0)
    for column in facts["seed_columns"]:
        if column not in selected:
            continue
        color = grid[0][column]
        for row in range(height):
            if row % 2 == 0:
                output[row][column] = color
            else:
                output[row][column - 1] = color
                output[row][column + 1] = color
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Pure test/diagnostic mirror; the retained Racket program owns labels."""
    return _paint(grid)


def _identity(grid):
    return [list(row) for row in grid]


def _straight_columns(grid):
    errors, facts = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    for column in facts["seed_columns"]:
        color = grid[0][column]
        for row in range(facts["grid_h"]):
            output[row][column] = color
    return output


def _one_branch(grid, delta: int):
    errors, facts = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    for column in facts["seed_columns"]:
        color = grid[0][column]
        for row in range(facts["grid_h"]):
            output[row][column if row % 2 == 0 else column + delta] = color
    return output


def _left_branch_only(grid):
    return _one_branch(grid, -1)


def _right_branch_only(grid):
    return _one_branch(grid, 1)


def _skip_single_seed(grid):
    facts = semantic_observables(grid)
    return _identity(grid) if facts.get("n_seeds") == 1 else rule_mirror(grid)


def _first_seed_only(grid):
    errors, facts = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _paint(grid, facts["seed_columns"][:1])


def _six_rows_only(grid):
    output = rule_mirror(grid)
    for row in range(6, len(output)):
        output[row] = [0] * len(output[row])
    return output


def _witness(**expected):
    def check(grid):
        observed = semantic_observables(grid)
        return not observed.get("errors") and all(
            observed.get(name) == value for name, value in expected.items()
        )

    return check


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "single_seed": _witness(single_seed=True),
    "multiple_seeds": _witness(multiple_seeds=True),
    "height_over_six": _witness(height_over_six=True),
    "odd_row_branching": _witness(odd_row_branching_visible=True),
}

LESSON_COMPETITORS: dict[str, Callable[[Any], list[list[int]]]] = {
    "identity": _identity,
    "straight_columns": _straight_columns,
    "left_branch_only": _left_branch_only,
    "right_branch_only": _right_branch_only,
    "skip_single_seed": _skip_single_seed,
    "first_seed_only": _first_seed_only,
    "six_rows_only": _six_rows_only,
}
SEMANTIC_RIVALS = dict(LESSON_COMPETITORS)
WITNESS_RIVALS = {
    "single_seed": ["skip_single_seed"],
    "multiple_seeds": ["first_seed_only"],
    "height_over_six": ["six_rows_only"],
    "odd_row_branching": [
        "identity",
        "straight_columns",
        "left_branch_only",
        "right_branch_only",
    ],
}
CANONICAL_SHORTCUTS = {"six_rows_only": _six_rows_only}


def lesson_identifiable(demos, query) -> list[str]:
    """Report competitors that fit every demo but change the query answer."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)):
        return ["demos must be a sequence"]
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the task grammar: {errors}")
            continue
        if rule_mirror(demo["input"]) != demo["output"]:
            reasons.append(f"demo {index} output does not match the branching rule")
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain input")
        return reasons
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is outside the task grammar: {query_errors}")
        return reasons
    if reasons:
        return reasons

    query_answer = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_answer:
                reasons.append(
                    f"competing rule {name!r} fits every demo but changes the query answer"
                )
    return reasons


def semantic_signature(grid) -> dict[str, Any]:
    observed = semantic_observables(grid)
    if observed.get("errors"):
        raise ValueError("; ".join(observed["errors"]))
    output = rule_mirror(grid)
    return {
        **observed,
        "output_nonzero": sum(value != 0 for row in output for value in row),
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Build one deterministic lawful input; Racket remains label authority."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    _validate_override_keys(overrides)

    effective = _effective_axis_values(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    height = ctx.draw_int_strict("grid_h", 3, 18)
    width = ctx.draw_int_strict("grid_w", 4, 24)
    count = ctx.draw_int_strict("n_seeds", 1, 8)

    column_sets = _valid_column_sets(width, count)
    if not column_sets:
        raise _incompatible_axes(
            f"grid_w={width} cannot realize n_seeds={count} with interior gap >=3",
            "grid_w",
            "n_seeds",
        )
    columns = ctx.draw_choice("seed_columns", column_sets)
    colors = ctx.draw_distinct_colors("seed_colors", n=count, exclude={0})

    grid = full_grid(height, width, 0)
    for column, color in zip(columns, colors):
        grid[0][column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]
