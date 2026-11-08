"""Input generator for the cardinal-color expansion task.

Every blue (1) cell is an anchor.  The authoritative rule keeps the input and,
for each *original* blue cell in row-major order, writes red (2) above, orange
(7) to the left, magenta (6) to the right, and cyan (8) below whenever that
neighbor is in bounds.  Boundary anchors are therefore ordinary lawful cases,
not degenerates.

This module returns inputs only.  Racket remains the label authority; the
Python mirrors below are independent regression/audit helpers.
"""
from __future__ import annotations

from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c792bb147617"
TASK_ID = GENERATOR_ID
RULE_HASH = "98769b9435a0"
VERSION = "3.0.0"

SUMMARY = (
    "A 6..16 by 6..16 zero-background grid contains 2..8 blue(1) anchor "
    "cells. Anchors may be interior or lie on any outer edge. For every "
    "original blue cell, the rule paints its in-bounds cardinal neighbors: "
    "up=2, left=7, right=6, down=8, while retaining the input elsewhere."
)

INVARIANTS = [
    "rectangular 6..16 by 6..16 grid using only colors 0 and 1",
    "exactly 2..8 blue anchor cells",
    "edge_mode=none has no boundary anchor; edge_mode=some has at least one",
    "anchors are not cardinally adjacent; boundary anchors and shared-neighbor writes remain lawful",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled/weighted 6..16 with recurrent 10",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled/weighted 6..16 with recurrent 10",
        "valid": "6..16",
    },
    "n_blues": {
        "type": "int",
        "default": "scheduled/weighted 2..8 with recurrent 6 and 8",
        "valid": "2..8",
    },
    "edge_mode": {
        "type": "str",
        "default": "scheduled none/some with recurrent some",
        "valid": "none|some",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

# Any four consecutive examples (the three demonstrations plus one held-out
# query used by the lesson builder) contain two 8-anchor boundary witnesses and
# one canonical-sized 6-anchor boundary case.  Thus every rotation leaves at
# least one counterexample to the canonical "only the first seven" shortcut in
# the visible demonstrations.
SCHEDULE_PROFILES = (
    "eight_boundary_a",
    "broad",
    "eight_boundary_b",
    "canonical",
)
_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_VALID_OVERRIDES = frozenset(AXES)


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    unknown = sorted(set(overrides) - _VALID_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    for name in ("grid_h", "grid_w", "n_blues"):
        if name in overrides and overrides[name] is not None and type(overrides[name]) is not int:
            raise TypeError(f"{name} override must be an integer (not bool)")
    if (
        "edge_mode" in overrides
        and overrides["edge_mode"] is not None
        and type(overrides["edge_mode"]) is not str
    ):
        raise TypeError("edge_mode override must be a string")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the finite semantic profile used by the default stream."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    return SCHEDULE_PROFILES[sample_index % _SCHEDULE_PERIOD]


def _draw_scheduled_int(ctx, name: str, default: int | Iterable[int], lo: int, hi: int) -> int:
    """Draw an exact/weighted default while preserving full-range overrides."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    options = (default,) if type(default) is int else tuple(default)
    return ctx.draw_choice(name, options)


def _draw_scheduled_choice(ctx, name: str, default: str | Iterable[str], options: tuple[str, ...]) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        # Type validation happens before context construction; draw_choice then
        # supplies the exact advertised membership gate and provenance.
        return ctx.draw_choice(name, options)
    defaults = (default,) if isinstance(default, str) else tuple(default)
    return ctx.draw_choice(name, defaults)


def _profile_defaults(profile: str, difficulty: str | None) -> tuple[object, object, object, object]:
    if profile in ("eight_boundary_a", "eight_boundary_b"):
        return 10, 10, 8, "some"
    if profile == "canonical":
        return 10, 10, 6, "some"

    # The broad slot varies scale while keeping every advertised value reachable
    # in every difficulty through an explicit override.
    if difficulty == "easy":
        return range(6, 11), range(6, 11), range(2, 6), ("none", "some")
    if difficulty == "hard":
        return range(10, 17), range(10, 17), range(5, 9), ("none", "some")
    if difficulty == "medium":
        return range(8, 14), range(8, 14), range(4, 8), ("none", "some")
    return range(6, 17), range(6, 17), range(2, 9), ("none", "some")


def _boundary_cells(height: int, width: int) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    ]


def _spread_positions(
    height: int,
    width: int,
    count: int,
    edge_mode: str,
    rng,
) -> list[tuple[int, int]]:
    """Choose exactly ``count`` legal cells with deterministic maximin spread.

    Maximin placement keeps ordinary examples readable without imposing a
    semantic separation restriction.  It always terminates because even the
    smallest interior domain (4x4 in a 6x6 grid) has room for eight anchors.
    """
    if edge_mode == "none":
        candidates = [
            (row, col)
            for row in range(1, height - 1)
            for col in range(1, width - 1)
        ]
        first_pool = candidates[:]
    else:
        candidates = [(row, col) for row in range(height) for col in range(width)]
        first_pool = _boundary_cells(height, width)

    if count > len(candidates):
        raise ValueError(
            f"cannot place {count} blue anchors in a {height}x{width} grid with edge_mode={edge_mode!r}"
        )

    # Shuffle once to make all maximin tie breaks keyed and deterministic.
    rng.shuffle(candidates)
    rng.shuffle(first_pool)
    selected = [first_pool[0]]
    # A single checkerboard parity contains at least eight legal cells even in
    # the smallest 6x6/interior domain.  Staying on that parity makes cardinal
    # adjacency impossible while retaining the full advertised count range.
    parity = (selected[0][0] + selected[0][1]) % 2
    remaining = [
        cell
        for cell in candidates
        if cell != selected[0] and (cell[0] + cell[1]) % 2 == parity
    ]

    while len(selected) < count:
        best_distance = max(
            min(abs(row - sr) + abs(col - sc) for sr, sc in selected)
            for row, col in remaining
        )
        chosen_index = next(
            index
            for index, (row, col) in enumerate(remaining)
            if min(abs(row - sr) + abs(col - sc) for sr, sc in selected) == best_distance
        )
        selected.append(remaining.pop(chosen_index))

    return sorted(selected)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_count, default_edge = _profile_defaults(profile, difficulty)
    height = _draw_scheduled_int(ctx, "grid_h", default_h, 6, 16)
    width = _draw_scheduled_int(ctx, "grid_w", default_w, 6, 16)
    count = _draw_scheduled_int(ctx, "n_blues", default_count, 2, 8)
    edge_mode = _draw_scheduled_choice(ctx, "edge_mode", default_edge, ("none", "some"))

    grid = full_grid(height, width, 0)
    for row, col in _spread_positions(
        height,
        width,
        count,
        edge_mode,
        ctx.draw_rng("placement"),
    ):
        grid[row][col] = 1
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the complete lawful input grammar, including edge anchors."""
    del meta
    errors: list[str] = []
    if difficulty not in _VALID_DIFFICULTIES:
        errors.append("difficulty must be None, 'easy', 'medium', or 'hard'")
    if not isinstance(grid, (list, tuple)) or not grid:
        return errors + ["grid must be a non-empty list/tuple of rows"]
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        return errors + ["every row must be a non-empty list/tuple"]

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return errors + ["grid must be rectangular"]
    height = len(grid)
    if not 6 <= height <= 16:
        errors.append(f"grid height {height} outside 6..16")
    if not 6 <= width <= 16:
        errors.append(f"grid width {width} outside 6..16")

    blue_count = 0
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if type(value) is not int or value not in (0, 1):
                errors.append(
                    f"cell ({row_index},{col_index}) must be integer color 0 or 1; found {value!r}"
                )
            elif value == 1:
                blue_count += 1
    if not 2 <= blue_count <= 8:
        errors.append(f"expected 2..8 blue(1) anchors, found {blue_count}")

    blue_set = set(_blue_positions(grid))
    adjacent_pairs = []
    for row, col in sorted(blue_set):
        for neighbor in ((row + 1, col), (row, col + 1)):
            if neighbor in blue_set:
                adjacent_pairs.append(((row, col), neighbor))
    if adjacent_pairs:
        errors.append(
            "blue anchors must not be cardinally adjacent; found "
            + ", ".join(f"{left}-{right}" for left, right in adjacent_pairs)
        )
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every advertised axis exactly from the generated pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid generated grid: " + "; ".join(errors))
    height, width = len(grid), len(grid[0])
    blues = _blue_positions(grid)
    edge_mode = (
        "some"
        if any(row in (0, height - 1) or col in (0, width - 1) for row, col in blues)
        else "none"
    )
    return {
        "grid_h": height,
        "grid_w": width,
        "n_blues": len(blues),
        "edge_mode": edge_mode,
    }


def _blue_positions(grid) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]


def _apply_anchors(grid, anchors: Iterable[tuple[int, int]]) -> list[list[int]]:
    source = [list(row) for row in grid]
    output = [row[:] for row in source]
    height = len(source)
    width = len(source[0]) if height else 0
    for row, col in anchors:
        # Match the authoritative write order exactly.  The source grid, not
        # the mutating result, determines which cells are anchors.
        if row > 0:
            output[row - 1][col] = 2
        if col > 0:
            output[row][col - 1] = 7
        if col < width - 1:
            output[row][col + 1] = 6
        if row < height - 1:
            output[row + 1][col] = 8
    return output


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; never used as label authority."""
    return _apply_anchors(grid, _blue_positions(grid))


def _first_seven_blues(grid) -> list[list[int]]:
    """Canonical-fitting rival: silently ignores every blue after the seventh."""
    return _apply_anchors(grid, _blue_positions(grid)[:7])


def _skip_boundary_blues(grid) -> list[list[int]]:
    """Rival inherited from the old generator: process only interior blues."""
    height, width = len(grid), len(grid[0])
    anchors = [
        (row, col)
        for row, col in _blue_positions(grid)
        if 0 < row < height - 1 and 0 < col < width - 1
    ]
    return _apply_anchors(grid, anchors)


def _has_eight_blues(grid) -> bool:
    try:
        return len(_blue_positions(grid)) == 8 and _first_seven_blues(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


def _has_boundary_blue(grid) -> bool:
    try:
        height, width = len(grid), len(grid[0])
        return any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in _blue_positions(grid)
        ) and _skip_boundary_blues(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


def lesson_identifiable(demos, query) -> list[str]:
    """Check the concrete teaching evidence required by this task.

    This is deliberately narrower than a universal induction claim.  A lesson
    is accepted only when its labeled demonstrations expose all four directional
    color assignments, an actually clipped boundary anchor, and an eighth anchor
    whose writes rule out the strongest canonical-fitting count shortcut.
    """
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one labeled demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be a labeled input/output pair"]

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append("query input is outside the generator grammar: " + "; ".join(query_errors))
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query label does not match the declared rule")

    direction_specs = (
        ("up", -1, 0, 2),
        ("left", 0, -1, 7),
        ("right", 0, 1, 6),
        ("down", 1, 0, 8),
    )
    observed_directions: set[str] = set()
    saw_boundary = False
    saw_eighth = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demonstration {index} is not a labeled input/output pair")
            continue
        source = pair["input"]
        output = pair["output"]
        errors = self_check(source)
        if errors:
            reasons.append(f"demonstration {index} is outside the generator grammar: " + "; ".join(errors))
            continue
        if rule_mirror(source) != output:
            reasons.append(f"demonstration {index} label does not match the declared rule")
            continue

        height, width = len(source), len(source[0])
        blues = _blue_positions(source)
        if len(blues) == 8 and _first_seven_blues(source) != output:
            saw_eighth = True
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in blues
        ) and _skip_boundary_blues(source) != output:
            saw_boundary = True

        for row, col in blues:
            for name, dr, dc, color in direction_specs:
                nr, nc = row + dr, col + dc
                if (
                    0 <= nr < height
                    and 0 <= nc < width
                    and source[nr][nc] == 0
                    and output[nr][nc] == color
                ):
                    observed_directions.add(name)

    missing = [name for name, *_rest in direction_specs if name not in observed_directions]
    if missing:
        reasons.append("demonstrations do not expose directional assignment(s): " + ", ".join(missing))
    if not saw_boundary:
        reasons.append("demonstrations do not show an observable clipped boundary anchor")
    if not saw_eighth:
        reasons.append("demonstrations do not show an observable eighth anchor")
    return reasons


SEMANTIC_WITNESSES = {
    "eight_blues": _has_eight_blues,
    "boundary_blue": _has_boundary_blue,
}
SEMANTIC_RIVALS = {
    "first_seven_blues": _first_seven_blues,
    "skip_boundary_blues": _skip_boundary_blues,
}
WITNESS_RIVALS = {
    "eight_blues": ["first_seven_blues"],
    "boundary_blue": ["skip_boundary_blues"],
}
CANONICAL_SHORTCUTS = {
    "first_seven_blues": _first_seven_blues,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
