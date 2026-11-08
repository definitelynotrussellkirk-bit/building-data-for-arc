"""Generator for ARC task ffd3a33c5687.

Rule
====
Each row is partitioned into left/right mirror orbits.  For each orbit, use the
left member when it is nonzero; otherwise use the right member.  Paint that
chosen color into both members.  A nonzero center-axis cell is unchanged.

The canonical examples contain only empty/singleton/same-color mirror orbits,
so two especially plausible shortcuts fit every demonstration: merely filling
blank mates while preserving occupied conflicts, and giving the right member
priority.  Ordinary generated scenes therefore contain an occupied pair with
different colors, which makes the authority's left-priority choice observable.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ffd3a33c5687"
TASK_ID = "ffd3a33c5687"
VERSION = "2.0.0"
RULE_HASH = "4276b16a10bb"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Sparse multicolor mirror orbits.  Complete each left/right pair using "
    "the nonzero member, with the left color winning occupied conflicts."
)

INVARIANTS = [
    "background is color 0; every foreground value is an ARC color 1..9",
    "2..5 one-sided mirror orbits make every accepted input non-identity",
    "0..3 same-color occupied mirror pairs are allowed",
    "0..2 different-color occupied conflicts are allowed",
    "ordinary defaults include at least one conflict that exposes left priority",
    "all declared axes are exact and recoverable from the returned grid",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "5..12",
        "doc": "Exact grid height; explicit overrides use the full domain in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical profile",
        "valid": "5..16",
        "doc": "Exact grid width; explicit overrides use the full domain in every band.",
    },
    "n_singletons": {
        "type": "int",
        "default": "scheduled 2..5",
        "valid": "2..5",
        "doc": "Exact count of mirror orbits with exactly one occupied member.",
    },
    "n_pairs": {
        "type": "int",
        "default": "scheduled 0..1",
        "valid": "0..3",
        "doc": "Exact count of mirror orbits occupied by the same color on both sides.",
    },
    "n_conflicts": {
        "type": "int",
        "default": "1",
        "valid": "0..2",
        "doc": "Exact count of mirror orbits occupied by two different nonzero colors.",
    },
}

# (height, width, palette-size including background, singletons, same pairs,
# conflicts).  Every default draw is an exact canonical (h, w, palette) profile,
# while placements and color identities remain generated.
SCHEDULE_PROFILES = (0, 1, 2, 3, 4)
_PROFILE_SPECS = (
    (5, 5, 4, 2, 1, 1),
    (5, 7, 3, 4, 1, 1),
    (6, 9, 4, 4, 1, 1),
    (7, 7, 6, 4, 0, 1),
    (7, 9, 6, 5, 0, 1),
)

_BAND_OFFSET = {None: 1, "easy": 0, "medium": 1, "hard": 2}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Five-profile cycle; difficulty rotates, rather than narrows, support."""
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    return (int(seed) + int(sample_index) + _BAND_OFFSET[difficulty]) % len(
        SCHEDULE_PROFILES
    )


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) for row in grid):
        return "every row must be a list"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return "grid values must be integer ARC colors in 0..9"
    return None


def _orbit_counts(grid: list[list[int]]) -> dict[str, int]:
    width = len(grid[0])
    counts = {"n_singletons": 0, "n_pairs": 0, "n_conflicts": 0}
    for row in grid:
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            if (left == 0) != (right == 0):
                counts["n_singletons"] += 1
            elif left != 0 and left == right:
                counts["n_pairs"] += 1
            elif left != 0 and right != 0 and left != right:
                counts["n_conflicts"] += 1
    return counts


def _left_priority_output(grid: list[list[int]]) -> list[list[int]]:
    output = copy.deepcopy(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            color = row[left_col] if row[left_col] != 0 else row[right_col]
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output


def _analyze(grid: Any) -> dict[str, Any]:
    error = _shape_error(grid)
    if error:
        return {"errors": [error]}

    height, width = len(grid), len(grid[0])
    counts = _orbit_counts(grid)
    foreground = {value for row in grid for value in row if value != 0}
    center_marks = (
        sum(row[width // 2] != 0 for row in grid) if width % 2 else 0
    )
    errors: list[str] = []

    if not 5 <= height <= 12:
        errors.append(f"grid height must be in 5..12, got {height}")
    if not 5 <= width <= 16:
        errors.append(f"grid width must be in 5..16, got {width}")
    if not 2 <= counts["n_singletons"] <= 5:
        errors.append(
            "expected 2..5 one-sided mirror orbits, found "
            f"{counts['n_singletons']}"
        )
    if not 0 <= counts["n_pairs"] <= 3:
        errors.append(
            f"expected 0..3 same-color occupied mirror pairs, found {counts['n_pairs']}"
        )
    if not 0 <= counts["n_conflicts"] <= 2:
        errors.append(
            "expected 0..2 different-color occupied conflicts, found "
            f"{counts['n_conflicts']}"
        )
    if not 2 <= len(foreground) <= 5:
        errors.append(
            f"expected 2..5 foreground colors, found {len(foreground)}"
        )
    if center_marks > 1:
        errors.append(f"expected at most one occupied center-axis cell, found {center_marks}")

    output = _left_priority_output(grid)
    if output == grid:
        errors.append("left-priority mirror rule would leave the input unchanged")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        **counts,
        "foreground_colors": foreground,
        "center_marks": center_marks,
        "output": output,
    }


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    bounds = {
        "grid_h": (5, 12),
        "grid_w": (5, 16),
        "n_singletons": (2, 5),
        "n_pairs": (0, 3),
        "n_conflicts": (0, 2),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} override must be an integer")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")


def _draw_exact_int(ctx, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _assignment_colors(
    palette: list[int], assignment_count: int
) -> list[int]:
    """Cycle through a shuffled palette, preserving exact palette cardinality."""
    if assignment_count < len(palette):
        raise ValueError("not enough occupied color slots for requested palette")
    return [palette[index % len(palette)] for index in range(assignment_count)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile_index = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, palette_size, scheduled_singletons, scheduled_pairs, scheduled_conflicts = (
        _PROFILE_SPECS[profile_index]
    )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = _draw_exact_int(ctx, "grid_h", scheduled_h, 5, 12)
    width = _draw_exact_int(ctx, "grid_w", scheduled_w, 5, 16)
    n_singletons = _draw_exact_int(
        ctx, "n_singletons", scheduled_singletons, 2, 5
    )
    n_pairs = _draw_exact_int(ctx, "n_pairs", scheduled_pairs, 0, 3)
    n_conflicts = _draw_exact_int(
        ctx, "n_conflicts", scheduled_conflicts, 0, 2
    )

    orbit_slots = [
        (row, left_col, width - 1 - left_col)
        for row in range(height)
        for left_col in range(width // 2)
    ]
    needed_orbits = n_singletons + n_pairs + n_conflicts
    if needed_orbits > len(orbit_slots):
        # The declared product is constructed so this cannot happen, but this
        # guard keeps future range edits loud rather than silently truncating.
        raise ValueError(
            f"requested {needed_orbits} mirror orbits but {height}x{width} has "
            f"only {len(orbit_slots)} off-axis slots"
        )

    layout_rng = ctx.draw_rng("layout")
    layout_rng.shuffle(orbit_slots)
    selected = orbit_slots[:needed_orbits]
    assignment_count = n_singletons + n_pairs + 2 * n_conflicts
    nonzero_palette_size = min(palette_size - 1, assignment_count)
    if n_conflicts:
        nonzero_palette_size = max(2, nonzero_palette_size)
    nonzero_palette_size = max(2, nonzero_palette_size)
    palette = list(range(1, 10))
    color_rng = ctx.draw_rng("colors")
    color_rng.shuffle(palette)
    palette = palette[:nonzero_palette_size]
    colors = _assignment_colors(palette, assignment_count)

    grid = full_grid(height, width, 0)
    color_index = 0
    slot_index = 0
    start_on_left = bool(layout_rng.randrange(2))

    for singleton_index in range(n_singletons):
        row, left_col, right_col = selected[slot_index]
        slot_index += 1
        color = colors[color_index]
        color_index += 1
        if (singleton_index + int(start_on_left)) % 2 == 0:
            grid[row][left_col] = color
        else:
            grid[row][right_col] = color

    for _ in range(n_pairs):
        row, left_col, right_col = selected[slot_index]
        slot_index += 1
        color = colors[color_index]
        color_index += 1
        grid[row][left_col] = color
        grid[row][right_col] = color

    for _ in range(n_conflicts):
        row, left_col, right_col = selected[slot_index]
        slot_index += 1
        left_color = colors[color_index]
        right_color = colors[color_index + 1]
        color_index += 2
        if left_color == right_color:
            raise AssertionError("constructed conflict colors must differ")
        grid[row][left_col] = left_color
        grid[row][right_col] = right_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_singletons": n_singletons,
        "n_pairs": n_pairs,
        "n_conflicts": n_conflicts,
    }
    if observed != expected:
        raise AssertionError(
            f"axis realization mismatch: expected {expected}, observed {observed}"
        )
    return grid


# ---------------------------------------------------------------------------
# Public structural and semantic contracts
# ---------------------------------------------------------------------------


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    error = _shape_error(grid)
    if error:
        raise ValueError(error)
    return _left_priority_output(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_singletons": analysis["n_singletons"],
        "n_pairs": analysis["n_pairs"],
        "n_conflicts": analysis["n_conflicts"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        **observe_overrides(grid),
        "palette_size": len(analysis["foreground_colors"]) + 1,
        "center_marks": analysis["center_marks"],
        "rule_changes_input": analysis["output"] != grid,
    }


def _lawful(grid) -> bool:
    return not _analyze(grid)["errors"]


def _has_occupied_color_conflict(grid) -> bool:
    return _lawful(grid) and _orbit_counts(grid)["n_conflicts"] > 0


def _preserve_occupied_conflicts(grid):
    error = _shape_error(grid)
    if error:
        return None
    output = copy.deepcopy(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            left, right = row[left_col], row[right_col]
            if left == 0 and right != 0:
                output[row_index][left_col] = right
            elif right == 0 and left != 0:
                output[row_index][right_col] = left
    return output


def _right_priority(grid):
    error = _shape_error(grid)
    if error:
        return None
    output = copy.deepcopy(grid)
    width = len(grid[0])
    for row_index, row in enumerate(grid):
        for left_col in range(width // 2):
            right_col = width - 1 - left_col
            color = row[right_col] if row[right_col] != 0 else row[left_col]
            output[row_index][left_col] = color
            output[row_index][right_col] = color
    return output


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "occupied_color_conflict": _has_occupied_color_conflict,
}

SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]] | None]] = {
    "preserve_occupied_conflicts": _preserve_occupied_conflicts,
    "right_priority": _right_priority,
}

WITNESS_RIVALS = {
    "occupied_color_conflict": [
        "preserve_occupied_conflicts",
        "right_priority",
    ]
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the mirror grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(
                f"demo {index} output disagrees with left-priority mirror completion"
            )

    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the mirror grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with left-priority mirror completion")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Small task-local impostors that the structural contract must reject."""
    blank = full_grid(5, 5, 0)

    identity = full_grid(5, 5, 0)
    identity[1][0] = identity[1][4] = 2
    identity[2][1] = identity[2][3] = 3

    one_color_block = full_grid(5, 5, 0)
    one_color_block[0][0] = one_color_block[0][1] = 2
    one_color_block[1][0] = one_color_block[1][1] = 2

    too_many_center_marks = generate(7001, 2, difficulty="medium")
    center = len(too_many_center_marks[0]) // 2
    if len(too_many_center_marks[0]) % 2:
        too_many_center_marks = copy.deepcopy(too_many_center_marks)
        too_many_center_marks[0][center] = 8
        too_many_center_marks[1][center] = 9
    else:
        # Use an odd-width exact draw so the fixture always exercises the axis.
        too_many_center_marks = generate(7001, 2, difficulty="medium", grid_w=9)
        too_many_center_marks = copy.deepcopy(too_many_center_marks)
        center = 4
        too_many_center_marks[0][center] = 8
        too_many_center_marks[1][center] = 9

    return [
        ("blank_grid", blank),
        ("already_symmetric_identity", identity),
        ("single_color_2x2_impostor", one_color_block),
        ("multiple_center_axis_marks", too_many_center_marks),
    ]
