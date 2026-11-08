"""Input generator for ARC task 1198580cc354 — top-row beam fill.

Every nonzero top-row seed projects its own color downward through background
cells in its column.  A color-9 blocker stops only that column; the blocker is
preserved and cells below it remain background.

The ordinary sampler deliberately includes blocked and unblocked columns plus
color 1 in every scene.  Those facts distinguish the selected rule from three
plausible shortcuts that fit, or nearly fit, the public demonstrations.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1198580cc354"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "018c975f3e7f"

SUMMARY = (
    "Nonzero top-row seeds project downward in their own columns until an "
    "optional color-9 blocker; each blocker is column-local and preserved."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "background is color 0",
    "there are 2..4 distinct nonzero seed colors in row 0",
    "all non-background cells below row 0 are color-9 blockers",
    "every blocker lies in a seed column and each seed column has at most one",
    "ordinary draws contain at least one blocked and one unblocked seed column",
    "ordinary draws include color 1 as a genuine seed",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-profile anchors plus broad draws",
        "valid": "7..10",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-profile anchors plus broad draws",
        "valid": "7..12",
    },
    "seed_count": {
        "type": "int",
        "default": "scheduled 2..4 distinct top-row seeds",
        "valid": "2..4",
    },
}

# grid_w >= 7 is always ample for four distinct seed columns.  Blockers have
# rows 2..h-2 available for every supported height, so the full Cartesian
# override product is constructively valid in every difficulty band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_INT_RANGES = {
    "grid_h": (7, 10),
    "grid_w": (7, 12),
    "seed_count": (2, 4),
}
_BANDS = ("easy", "medium", "hard")

# First four entries exactly reproduce all public input profiles
# (height, width, number of distinct seed colors).  The final two retain broad
# supported dimensions while preserving the same semantic grammar.
_PROFILE_SPECS = (
    ("canonical_7x8_3", 7, 8, 3),
    ("canonical_8x9_3", 8, 9, 3),
    ("canonical_8x10_3", 8, 10, 3),
    ("canonical_9x7_2", 9, 7, 2),
    ("broad_10x12_4", 10, 12, 4),
    ("broad_7x12_4", 7, 12, 4),
)
SCHEDULE_PROFILES = tuple(spec[0] for spec in _PROFILE_SPECS)
_PROFILE_BY_NAME = {name: (height, width, count) for name, height, width, count in _PROFILE_SPECS}
_BAND_OFFSETS = {"easy": 0, "medium": 1, "hard": 2}


def _validate_difficulty(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in _BANDS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return difficulty


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _INT_RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Name the deterministic curriculum profile for semantic-gate auditing."""
    del seed
    band = _validate_difficulty(difficulty)
    return SCHEDULE_PROFILES[
        (int(sample_index) + _BAND_OFFSETS[band]) % len(SCHEDULE_PROFILES)
    ]


def _draw_int_axis(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    lo, hi = _INT_RANGES[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, default, default)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one lawful, shortcut-resistant input grid."""
    _validate_overrides(overrides)
    band = _validate_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    profile_name = schedule_profile(seed, sample_index, difficulty=band)
    default_h, default_w, default_seed_count = _PROFILE_BY_NAME[profile_name]
    height = _draw_int_axis(ctx, overrides, "grid_h", default_h)
    width = _draw_int_axis(ctx, overrides, "grid_w", default_w)
    seed_count = _draw_int_axis(
        ctx, overrides, "seed_count", default_seed_count
    )

    columns = ctx.draw_rng("seed_columns").sample(range(width), seed_count)

    # Color 1 is absent from all public examples, so force it into every
    # ordinary scene and vary the remaining distinct colors independently.
    other_colors = ctx.draw_rng("seed_palette").sample(
        range(2, 9), seed_count - 1
    )
    colors = [1, *other_colors]
    ctx.draw_rng("color_assignment").shuffle(colors)

    # At least one blocked and one unblocked column makes blocker stopping and
    # column locality visible in every demonstration, not only in a rare query.
    blocker_count = ctx.draw_rng("blocker_count").randint(1, seed_count - 1)
    blocker_columns = ctx.draw_rng("blocker_columns").sample(
        columns, blocker_count
    )
    blocker_rows = [
        ctx.draw_rng(f"blocker_row_{index}").randint(2, height - 2)
        for index in range(blocker_count)
    ]

    grid = full_grid(height, width, 0)
    for column, color in zip(columns, colors):
        grid[0][column] = color
    for column, row in zip(blocker_columns, blocker_rows):
        grid[row][column] = 9

    expected = {
        "grid_h": height,
        "grid_w": width,
        "seed_count": seed_count,
    }
    observed = observe_overrides(grid)
    if observed != expected:  # pragma: no cover - fail-loud generator contract
        raise RuntimeError(
            f"generated scene lost exact axes: expected {expected}, observed {observed}"
        )
    errors = self_check(grid)
    if errors:  # pragma: no cover - fail-loud generator contract
        raise RuntimeError("generated invalid beam scene: " + "; ".join(errors))
    return grid


def _basic_grid_errors(grid) -> tuple[list[str], int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected nonempty rows"], len(grid), 0
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid is ragged"], len(grid), width

    errors: list[str] = []
    height = len(grid)
    if not 7 <= height <= 10 or not 7 <= width <= 12:
        errors.append(f"grid dimensions {height}x{width} outside 7..10 by 7..12")
    bad = sorted(
        {
            repr(value)
            for row in grid
            for value in row
            if type(value) is not int or not 0 <= value <= 9
        }
    )
    if bad:
        errors.append(
            "cells must be integer ARC colors 0..9; found " + ", ".join(bad[:5])
        )
    return errors, height, width


def _analysis(grid) -> dict[str, Any]:
    errors, height, width = _basic_grid_errors(grid)
    result: dict[str, Any] = {
        "errors": errors,
        "height": height,
        "width": width,
        "seed_columns": [],
        "seed_colors": [],
        "blockers": [],
    }
    if not height or not width or errors:
        return result

    if any(value == 9 for value in grid[0]):
        errors.append("row 0 may contain only background or seed colors 1..8")
    seed_columns = [
        column for column, value in enumerate(grid[0]) if value not in (0, 9)
    ]
    seed_colors = [grid[0][column] for column in seed_columns]
    if not 2 <= len(seed_columns) <= 4:
        errors.append(f"expected 2..4 top-row seeds, found {len(seed_columns)}")
    if len(set(seed_colors)) != len(seed_colors):
        errors.append("top-row seed colors must be distinct")

    blockers: list[tuple[int, int]] = []
    blockers_by_column: dict[int, int] = {}
    seed_column_set = set(seed_columns)
    for row in range(1, height):
        for column, value in enumerate(grid[row]):
            if value == 0:
                continue
            if value != 9:
                errors.append(
                    f"cell ({row}, {column}) below row 0 must be 0 or blocker 9"
                )
                continue
            blockers.append((row, column))
            if column not in seed_column_set:
                errors.append(
                    f"blocker at ({row}, {column}) is outside every seed column"
                )
            if not 2 <= row <= height - 2:
                errors.append(
                    f"blocker at ({row}, {column}) must be in rows 2..{height - 2}"
                )
            blockers_by_column[column] = blockers_by_column.get(column, 0) + 1

    repeated = sorted(
        column for column, count in blockers_by_column.items() if count > 1
    )
    if repeated:
        errors.append(f"seed columns contain multiple blockers: {repeated}")
    if not blockers:
        errors.append("expected at least one color-9 blocker")

    result.update(
        {
            "seed_columns": seed_columns,
            "seed_colors": seed_colors,
            "blockers": blockers,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete lawful input grammar used by this task."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """All public and generated inputs share this exact structural grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "seed_count": len(analysis["seed_columns"]),
    }


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror of the selected canonical Racket rule."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid beam grid: " + "; ".join(analysis["errors"]))
    output = deepcopy(grid)
    for column in analysis["seed_columns"]:
        color = grid[0][column]
        for row in range(1, analysis["height"]):
            if grid[row][column] == 9:
                break
            output[row][column] = color
    return output


def _ignore_blockers(grid) -> list[list[int]]:
    """Wrong rule: preserve blockers but continue every beam below them."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid beam grid")
    output = deepcopy(grid)
    for column in analysis["seed_columns"]:
        color = grid[0][column]
        for row in range(1, analysis["height"]):
            if output[row][column] == 0:
                output[row][column] = color
    return output


def _global_first_blocker_row(grid) -> list[list[int]]:
    """Wrong rule: the earliest blocker globally stops every beam."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid beam grid")
    gate = min(row for row, _column in analysis["blockers"])
    output = deepcopy(grid)
    for column in analysis["seed_columns"]:
        color = grid[0][column]
        for row in range(1, gate):
            if output[row][column] == 0:
                output[row][column] = color
    return output


def _ignore_color_one(grid) -> list[list[int]]:
    """Canonical-fitting shortcut: treat color 1 as background, not a seed."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid beam grid")
    output = deepcopy(grid)
    for column in analysis["seed_columns"]:
        color = grid[0][column]
        if color == 1:
            continue
        for row in range(1, analysis["height"]):
            if grid[row][column] == 9:
                break
            output[row][column] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable] = {
    "ignore_blockers": _ignore_blockers,
    "global_first_blocker_row": _global_first_blocker_row,
    "ignore_color_1": _ignore_color_one,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"ignore_color_1": _ignore_color_one}


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness_blocker_stops_beam(grid) -> bool:
    analysis = _lawful(grid)
    return bool(
        analysis
        and any(row < analysis["height"] - 1 for row, _column in analysis["blockers"])
        and _ignore_blockers(grid) != rule_mirror(grid)
    )


def _witness_blockers_are_column_local(grid) -> bool:
    analysis = _lawful(grid)
    if not analysis:
        return False
    blocked = {column for _row, column in analysis["blockers"]}
    return bool(
        blocked
        and set(analysis["seed_columns"]) - blocked
        and _global_first_blocker_row(grid) != rule_mirror(grid)
    )


def _witness_color_one_is_seed(grid) -> bool:
    analysis = _lawful(grid)
    return bool(
        analysis
        and 1 in analysis["seed_colors"]
        and _ignore_color_one(grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "blocker_stops_beam": _witness_blocker_stops_beam,
    "blockers_are_column_local": _witness_blockers_are_column_local,
    "color_1_is_a_seed": _witness_color_one_is_seed,
}
WITNESS_RIVALS = {
    "blocker_stops_beam": ["ignore_blockers"],
    "blockers_are_column_local": ["global_first_blocker_row"],
    "color_1_is_a_seed": ["ignore_color_1"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Return reasons a labeled lesson still permits a declared rival rule."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    labelled = [*demos, query]
    for index, item in enumerate(labelled):
        role = "query" if index == len(labelled) - 1 else f"demo {index}"
        if not isinstance(item, dict) or "input" not in item or "output" not in item:
            reasons.append(f"{role} must contain input and output grids")
            continue
        try:
            expected = rule_mirror(item["input"])
        except ValueError as exc:
            reasons.append(f"{role} input is outside the teaching grammar: {exc}")
            continue
        if item["output"] != expected:
            reasons.append(f"{role} output disagrees with the beam rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(item["input"]) == item["output"] for item in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"competitor {name!r} matches every demo but changes the query"
            )
        elif survives:
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-linked malformed near misses that self_check must reject."""
    good = generate(1701, 0, grid_h=8, grid_w=9, seed_count=3)

    blank = full_grid(8, 9, 0)

    top_blocker = deepcopy(good)
    top_blocker[0][next(c for c, value in enumerate(good[0]) if value == 0)] = 9

    stray_color = deepcopy(good)
    stray_color[1][next(c for c, value in enumerate(good[0]) if value == 0)] = 4

    stray_blocker = deepcopy(good)
    empty_column = next(c for c, value in enumerate(good[0]) if value == 0)
    stray_blocker[2][empty_column] = 9

    duplicate_blocker = deepcopy(good)
    blocked_column = next(
        column
        for column in range(len(good[0]))
        if any(row[column] == 9 for row in good[1:])
    )
    free_row = next(
        row
        for row in range(2, len(good) - 1)
        if duplicate_blocker[row][blocked_column] == 0
    )
    duplicate_blocker[free_row][blocked_column] = 9

    no_blocker = deepcopy(good)
    for row in range(1, len(no_blocker)):
        for column in range(len(no_blocker[0])):
            if no_blocker[row][column] == 9:
                no_blocker[row][column] = 0

    return [
        ("blank_grid", blank),
        ("top_row_blocker", top_blocker),
        ("stray_non_blocker_color", stray_color),
        ("blocker_without_seed", stray_blocker),
        ("two_blockers_in_one_seed_column", duplicate_blocker),
        ("no_blocker", no_blocker),
        ("ragged_grid", [[1, 0, 2], [0, 0]]),
    ]
