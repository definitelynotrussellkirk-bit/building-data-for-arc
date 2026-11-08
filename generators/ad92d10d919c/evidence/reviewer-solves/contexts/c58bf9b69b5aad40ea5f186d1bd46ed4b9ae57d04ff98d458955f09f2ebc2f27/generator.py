"""Canonical-centred lessons for four-diagonal consensus filling.

The unchanged Racket authority fills a zero cell only when all four diagonal
neighbours are the same nonzero color.  The sampler constructs exact counts on
a separated 3x3 lattice and alternates two negative controls so ordinary
lessons refute the canonical-fitting "three corners suffice" and "any four
colored corners suffice" shortcuts.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ad92d10d919c"
TASK_ID = GENERATOR_ID
RULE_HASH = "2fadbb67030c"
VERSION = "3.0.0"
SUMMARY = (
    "Sparse 0-background grids contain 1-3 separated X motifs.  Each X has "
    "four same-color diagonal corners around a zero center, which the rule "
    "fills with that color.  Every generated input also contains exactly one "
    "scheduled near-miss: either only three matching corners or four corners "
    "split 2+2 across two colors.  These controls teach that all four corners "
    "must be present and must agree."
)

INVARIANTS = [
    "background is color 0",
    "1-3 positive motifs have four equal nonzero diagonals around a zero center",
    "ordinary generated inputs contain one partial-3 or mixed-2+2 near-miss",
    "recognized 3x3 motif neighborhoods are pairwise disjoint",
    "all nonzero cells belong to exactly one recognized motif",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical-centred, mostly 6..9", "valid": "6..16"},
    "grid_w": {"type": "int", "default": "canonical-centred, mostly 7..10", "valid": "7..18"},
    "motif_count": {"type": "int", "default": "mostly 2..3", "valid": "1..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("partial_control", "mixed_control")
MIN_STRICT_FRAC = 0.25

_BOUNDS = {
    "grid_h": (6, 16),
    "grid_w": (7, 18),
    "motif_count": (1, 3),
}
_DIFFICULTIES = (None, "easy", "medium", "hard")
_COLORS = tuple(range(1, 10))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic two-step teaching schedule."""
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_request(seed, sample_index, difficulty, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _DIFFICULTIES:
        raise ValueError(f"difficulty must be one of {_DIFFICULTIES}, got {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if type(value) is not int:  # reject bool, float, string, and explicit None
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo}, {hi}]")


def _axis_options(name: str, difficulty: str | None) -> list[int]:
    """Full legal domain plus weights; every exact override remains legal."""
    lo, hi = _BOUNDS[name]
    options = list(range(lo, hi + 1))
    if name == "grid_h":
        options += [6, 6, 7, 7, 8, 9] * 8
        options += {
            None: [7, 8],
            "easy": [6, 6, 7, 8],
            "medium": [8, 9, 10, 11],
            "hard": [9, 10, 12, 14, 16],
        }[difficulty]
    elif name == "grid_w":
        options += [7, 8, 8, 9, 9, 10] * 8
        options += {
            None: [8, 9],
            "easy": [7, 8, 8, 9],
            "medium": [9, 10, 11, 12],
            "hard": [10, 12, 14, 16, 18],
        }[difficulty]
    elif name == "motif_count":
        options += [2, 2, 2, 3, 3] * 10
        options += {
            None: [2, 3],
            "easy": [1, 2, 2],
            "medium": [2, 2, 3],
            "hard": [2, 3, 3],
        }[difficulty]
    return options


def _draw_axis(ctx, name: str, difficulty: str | None, profile: str) -> int:
    """Draw one public axis while keeping odd-index lessons canonical-profiled.

    Explicit overrides always see the full declared domain.  Without an
    override, the mixed-control half of the schedule is a stable 6x8 lesson
    with one positive motif.  That profile is present in the authority and its
    eight isolated colored cells overlap the authority's coarse object-count
    support; the partial-control half retains broad nuisance variation.
    """
    if name in ctx.overrides:
        lo, hi = _BOUNDS[name]
        options = list(range(lo, hi + 1))
    elif profile == "mixed_control":
        options = {"grid_h": [6], "grid_w": [8], "motif_count": [1]}[name]
    else:
        options = _axis_options(name, difficulty)
    return ctx.draw_choice(name, options)


def _corners(row: int, col: int) -> tuple[tuple[int, int], ...]:
    return (
        (row - 1, col - 1),
        (row - 1, col + 1),
        (row + 1, col - 1),
        (row + 1, col + 1),
    )


def _neighborhood(row: int, col: int) -> set[tuple[int, int]]:
    return {
        (rr, cc)
        for rr in range(row - 1, row + 2)
        for cc in range(col - 1, col + 2)
    }


def _center_slots(height: int, width: int) -> list[tuple[int, int]]:
    """Disjoint 3x3 slots; even the minimum 6x7 grid has four."""
    return [
        (row, col)
        for row in range(1, height - 1, 3)
        for col in range(1, width - 1, 3)
    ]


def _choose_slots(ctx, slots, motif_count: int, profile: str):
    """Choose exact-capacity slots, separating the canonical mixed anchor."""
    rng = ctx.draw_rng("motif_slots")
    if profile == "mixed_control" and motif_count == 1:
        diagonal_pairs = [
            (first, second)
            for first, second in combinations(slots, 2)
            if abs(first[0] - second[0]) >= 3
            and abs(first[1] - second[1]) >= 3
        ]
        if diagonal_pairs:
            positive, control = rng.choice(diagonal_pairs)
            if rng.randrange(2):
                positive, control = control, positive
            return [positive, control]
    return rng.sample(slots, motif_count + 1)


def _paint_positive(grid, center: tuple[int, int], color: int) -> None:
    for row, col in _corners(*center):
        grid[row][col] = color


def _paint_partial(
    grid, center: tuple[int, int], color: int, missing_index: int
) -> None:
    for index, (row, col) in enumerate(_corners(*center)):
        if index != missing_index:
            grid[row][col] = color


def _paint_mixed(
    grid,
    center: tuple[int, int],
    colors: tuple[int, int],
    orientation: int,
) -> None:
    first, second = colors
    patterns = (
        (first, second, second, first),
        (first, second, first, second),
    )
    for (row, col), color in zip(_corners(*center), patterns[orientation % 2]):
        grid[row][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    height = _draw_axis(ctx, "grid_h", difficulty, profile)
    width = _draw_axis(ctx, "grid_w", difficulty, profile)
    motif_count = _draw_axis(ctx, "motif_count", difficulty, profile)

    slots = _center_slots(height, width)
    needed = motif_count + 1  # exact positive count plus one negative control
    if len(slots) < needed:  # protected by public bounds; keep failure loud
        raise ValueError(
            f"grid {height}x{width} has {len(slots)} separated slots, needs {needed}"
        )
    chosen = _choose_slots(ctx, slots, motif_count, profile)
    palette_size = max(motif_count, 2)
    colors = ctx.draw_rng("motif_colors").sample(_COLORS, palette_size)

    grid = full_grid(height, width, 0)
    for center, color in zip(chosen[:motif_count], colors[:motif_count]):
        _paint_positive(grid, center, color)

    control_center = chosen[-1]
    control_rng = ctx.draw_rng("negative_control")
    if profile == "partial_control":
        _paint_partial(
            grid,
            control_center,
            colors[control_rng.randrange(motif_count)],
            control_rng.randrange(4),
        )
    else:
        _paint_mixed(
            grid,
            control_center,
            (colors[0], colors[1]),
            control_rng.randrange(2),
        )
    return grid


def _shape_error(grid) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "grid must be rectangular"
    return None


def _diagonal_values(grid, row: int, col: int) -> tuple[int, int, int, int]:
    return tuple(grid[rr][cc] for rr, cc in _corners(row, col))  # type: ignore[return-value]


def _motif_facts(grid):
    """Return recognized centers, nonzero-corner use counts, and errors."""
    shape_error = _shape_error(grid)
    if shape_error:
        return [], Counter(), [shape_error]
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return [], Counter(), ["cells must be integer ARC colors 0..9 (bool is not a color)"]

    height, width = len(grid), len(grid[0])
    facts = []
    usage: Counter[tuple[int, int]] = Counter()
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = _diagonal_values(grid, row, col)
            nonzero = [value for value in values if value != 0]
            counts = Counter(nonzero)
            kind = None
            if len(nonzero) == 4 and len(counts) == 1:
                kind = "positive"
            elif len(nonzero) == 3 and len(counts) == 1:
                kind = "partial"
            elif len(nonzero) == 4 and sorted(counts.values()) == [2, 2]:
                kind = "mixed"
            if kind is None:
                continue
            cells = tuple(
                (rr, cc)
                for (rr, cc), value in zip(_corners(row, col), values)
                if value != 0
            )
            usage.update(cells)
            facts.append(
                {
                    "kind": kind,
                    "row": row,
                    "col": col,
                    "values": values,
                    "cells": cells,
                }
            )

    errors: list[str] = []
    for first, second in combinations(facts, 2):
        if _neighborhood(first["row"], first["col"]) & _neighborhood(
            second["row"], second["col"]
        ):
            errors.append(
                "recognized motif neighborhoods overlap at "
                f"({first['row']},{first['col']}) and ({second['row']},{second['col']})"
            )
            break
    all_nonzero = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    unused = sorted(all_nonzero - set(usage))
    multiply_used = sorted(cell for cell, count in usage.items() if count != 1)
    if unused:
        errors.append(f"{len(unused)} nonzero cells do not belong to a recognized motif")
    if multiply_used:
        errors.append(f"{len(multiply_used)} nonzero cells belong to multiple motifs")
    return facts, usage, errors


def _facts_by_kind(grid):
    facts, _usage, errors = _motif_facts(grid)
    grouped = {"positive": [], "partial": [], "mixed": []}
    for fact in facts:
        grouped[fact["kind"]].append(fact)
    return grouped, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    grouped, errors = _facts_by_kind(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 3 <= height <= 30 or not 3 <= width <= 30:
        errors.append(f"grid dimensions {height}x{width} must be within 3..30")
    positives = len(grouped["positive"])
    negatives = len(grouped["partial"]) + len(grouped["mixed"])
    if not 1 <= positives <= 3:
        errors.append(f"expected 1-3 positive consensus motifs, got {positives}")
    if negatives > 1:
        errors.append(f"expected at most one negative control, got {negatives}")
    if grouped["partial"] and grouped["mixed"]:
        errors.append("partial and mixed controls must not coexist")
    return errors


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed lesson: " + "; ".join(errors))
    grouped, _ = _facts_by_kind(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "motif_count": len(grouped["positive"]),
    }


def strict_canonical_like(grid) -> list[str]:
    """Canonical-scale structural predicate, not literal example replay."""
    errors = self_check(grid)
    if errors:
        return errors
    grouped, _ = _facts_by_kind(grid)
    height, width = len(grid), len(grid[0])
    if not 5 <= height <= 9:
        errors.append("canonical-scale grid height is 5..9")
    if not 7 <= width <= 11:
        errors.append("canonical-scale grid width is 7..11")
    if not 1 <= len(grouped["positive"]) <= 3:
        errors.append("canonical-scale inputs contain 1..3 positive motifs")
    positive_colors = [fact["values"][0] for fact in grouped["positive"]]
    if len(positive_colors) != len(set(positive_colors)):
        errors.append("positive motif colors must be distinct")
    return errors


def rule_mirror(grid):
    """Direct Python mirror of the selected Racket authority."""
    shape_error = _shape_error(grid)
    if shape_error:
        raise ValueError(shape_error)
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = _diagonal_values(grid, row, col)
            if values[0] != 0 and all(value == values[0] for value in values[1:]):
                output[row][col] = values[0]
    return output


def _at_least_three(grid):
    """Canonical-fitting rival: three matching nonzero diagonals suffice."""
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            counts = Counter(value for value in _diagonal_values(grid, row, col) if value)
            if counts:
                color, count = counts.most_common(1)[0]
                if count >= 3:
                    output[row][col] = color
    return output


def _any_four_nonzero(grid):
    """Canonical-fitting rival: any four colored diagonals fill the center."""
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = _diagonal_values(grid, row, col)
            if all(values):
                output[row][col] = values[0]
    return output


def _has_kind(grid, kind: str) -> bool:
    grouped, errors = _facts_by_kind(grid)
    return not errors and bool(grouped[kind])


def _has_positive_consensus(grid) -> bool:
    return _has_kind(grid, "positive")


def _has_partial_near_miss(grid) -> bool:
    return _has_kind(grid, "partial")


def _has_mixed_near_miss(grid) -> bool:
    return _has_kind(grid, "mixed")


SEMANTIC_WITNESSES = {
    "positive_consensus": _has_positive_consensus,
    "three_of_four_near_miss": _has_partial_near_miss,
    "mixed_four_near_miss": _has_mixed_near_miss,
}
SEMANTIC_RIVALS = {
    "at_least_three": _at_least_three,
    "any_four_nonzero": _any_four_nonzero,
}
WITNESS_RIVALS = {
    "three_of_four_near_miss": ["at_least_three"],
    "mixed_four_near_miss": ["any_four_nonzero"],
}
BRANCH_WITNESSES = ("positive_consensus",)
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query) -> list[str]:
    """Finite, query-aware check over the declared canonical-fitting rivals."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons
