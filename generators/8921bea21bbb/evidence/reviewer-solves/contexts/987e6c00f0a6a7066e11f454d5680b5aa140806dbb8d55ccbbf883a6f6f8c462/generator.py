"""Generator for 8921bea21bbb — mask the right panel with the left panel.

A full-height colour-9 column separates equal-size panels.  Every non-zero cell
in the left panel is a mask cell; the output keeps the right-panel value at the
same coordinate and writes zero elsewhere.  The teaching schedule retains the
canonical 5x5 and 6x6 profiles while varying the mask colour, density, panel
size, and right-panel holes.  In particular, non-colour-2 masks refute the
strongest canonical-only shortcut, "only colour 2 marks cells to keep".
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8921bea21bbb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "adbc411a920b"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.40

SUMMARY = (
    "Split at the full-height colour-9 separator. Treat every non-zero left-panel "
    "cell as a binary keep mask and copy the corresponding right-panel colour into "
    "the same-sized output; write zero where the left panel is zero."
)

INVARIANTS = [
    "exactly one full-height colour-9 separator splits equal-width panels",
    "the left panel is a non-empty monochrome non-zero mask",
    "the right panel contains at least two colours and overlaps the left mask",
    "right-only cells make masking observable and overlapping colours make copying observable",
]

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "panel_h": {"type": "int", "default": "scheduled by profile and difficulty", "valid": "5..8"},
    "panel_w": {"type": "int", "default": "scheduled by profile and difficulty", "valid": "5..8"},
    "mask_count": {"type": "int", "default": "scheduled 4..12", "valid": "4..12"},
    "mask_color": {"type": "int", "default": "scheduled 1..8", "valid": "1..8"},
    "right_zero_count": {"type": "int", "default": "scheduled 0..4", "valid": "0..4"},
}

_PROFILES = (
    "canonical_5",
    "non_two_sparse",
    "canonical_6",
    "non_two_dense",
)
SCHEDULE_PROFILES = _PROFILES

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_RIGHT_PALETTE = tuple(range(2, 9))
_BROAD_RIGHT_PALETTE = tuple(range(1, 9))
_ALLOWED_DIFFICULTIES = (None, "easy", "medium", "hard")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic four-slot teaching profile."""
    del seed
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    return _PROFILES[int(sample_index) % len(_PROFILES)]


def _validate_call(difficulty, overrides) -> None:
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))


def _scheduled_defaults(sample_index: int, difficulty) -> dict[str, int]:
    profile = _PROFILES[int(sample_index) % len(_PROFILES)]
    offset = {None: 1, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    if profile == "canonical_5":
        return {
            "panel_h": 5,
            "panel_w": 5,
            "mask_count": 6 + offset,
            "mask_color": 2,
            "right_zero_count": 0,
        }
    if profile == "non_two_sparse":
        return {
            "panel_h": 5 + offset,
            "panel_w": 6,
            "mask_count": 5 + 2 * offset,
            "mask_color": 3,
            "right_zero_count": 1 + offset,
        }
    if profile == "canonical_6":
        return {
            "panel_h": 6,
            "panel_w": 6,
            "mask_count": 7 + offset,
            "mask_color": 2,
            "right_zero_count": 0,
        }
    return {
        "panel_h": 6 + offset,
        "panel_w": 7,
        "mask_count": 8 + 2 * offset,
        "mask_color": 7,
        "right_zero_count": 2 + offset,
    }


def _neighbors(cell: tuple[int, int], height: int, width: int):
    row, column = cell
    for dr, dc in _CARDINAL:
        nr, nc = row + dr, column + dc
        if 0 <= nr < height and 0 <= nc < width:
            yield nr, nc


def _connected_mask(rng, height: int, width: int, count: int) -> set[tuple[int, int]]:
    """Grow an exact-size 4-connected mask from one deterministic seed cell."""
    start = (rng.randrange(height), rng.randrange(width))
    cells = {start}
    while len(cells) < count:
        frontier = sorted(
            neighbor
            for cell in cells
            for neighbor in _neighbors(cell, height, width)
            if neighbor not in cells
        )
        if not frontier:
            raise ValueError(f"cannot grow {count} mask cells in {height}x{width}")
        cells.add(rng.choice(frontier))
    return cells


def _split(grid) -> tuple[int, list[list[int]], list[list[int]]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a non-empty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    height = len(grid)
    separators = [
        column
        for column in range(width)
        if all(grid[row][column] == 9 for row in range(height))
    ]
    if len(separators) != 1:
        raise ValueError(f"expected exactly one full-height 9 separator, got {separators}")
    separator = separators[0]
    if separator * 2 + 1 != width:
        raise ValueError(f"separator at {separator} does not split width {width} equally")
    left = [list(row[:separator]) for row in grid]
    right = [list(row[separator + 1 :]) for row in grid]
    return separator, left, right


def _nonzero_cells(panel) -> set[tuple[int, int]]:
    return {
        (row, column)
        for row, values in enumerate(panel)
        for column, value in enumerate(values)
        if value != 0
    }


def _is_connected(cells: set[tuple[int, int]], height: int, width: int) -> bool:
    if not cells:
        return False
    reached = {next(iter(cells))}
    stack = list(reached)
    while stack:
        cell = stack.pop()
        for neighbor in _neighbors(cell, height, width):
            if neighbor in cells and neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    return reached == cells


def semantic_observables(grid) -> dict[str, Any]:
    separator, left, right = _split(grid)
    mask = _nonzero_cells(left)
    mask_colors = {left[row][column] for row, column in mask}
    right_nonzero = _nonzero_cells(right)
    overlap_colors = {
        right[row][column]
        for row, column in mask
        if right[row][column] != 0
    }
    return {
        "panel_h": len(grid),
        "panel_w": separator,
        "mask_count": len(mask),
        "mask_color": next(iter(mask_colors)) if len(mask_colors) == 1 else None,
        "right_zero_count": sum(value == 0 for row in right for value in row),
        "mask": mask,
        "mask_colors": mask_colors,
        "right_nonzero": right_nonzero,
        "right_colors": {right[row][column] for row, column in right_nonzero},
        "overlap_colors": overlap_colors,
        "right_only_count": len(right_nonzero - mask),
    }


def observe_overrides(grid) -> dict[str, int]:
    facts = semantic_observables(grid)
    return {name: facts[name] for name in AXES}


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror; canonical Racket remains label authority."""
    _, left, right = _split(grid)
    return [
        [right[row][column] if left[row][column] != 0 else 0 for column in range(len(left[0]))]
        for row in range(len(left))
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize this generator's lawful masking grammar and reject impostors."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a non-empty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected non-empty rows"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colours 0..9"]

    try:
        separator, left, right = _split(grid)
    except ValueError as exc:
        return [str(exc)]

    height = len(grid)
    errors: list[str] = []
    if not 5 <= height <= 8:
        errors.append(f"panel_h={height} outside 5..8")
    if not 5 <= separator <= 8:
        errors.append(f"panel_w={separator} outside 5..8")
    if any(
        grid[row][column] == 9
        for row in range(height)
        for column in range(width)
        if column != separator
    ):
        errors.append("colour 9 may appear only in the separator column")

    mask = _nonzero_cells(left)
    mask_colors = {left[row][column] for row, column in mask}
    if not 4 <= len(mask) <= 12:
        errors.append(f"mask_count={len(mask)} outside 4..12")
    if len(mask_colors) != 1 or not mask_colors <= set(range(1, 9)):
        errors.append(f"left mask must be monochrome in colours 1..8, got {sorted(mask_colors)}")
    right_zero_count = sum(value == 0 for row in right for value in row)
    right_colors = {value for row in right for value in row if value != 0}
    if not 0 <= right_zero_count <= 4:
        errors.append(f"right_zero_count={right_zero_count} outside 0..4")
    if any(value == 9 for row in right for value in row):
        errors.append("right panel may not contain separator colour 9")
    if len(right_colors) < 2 or not right_colors <= set(range(1, 9)):
        errors.append(f"right panel must use at least two colours from 1..8, got {sorted(right_colors)}")

    overlap_colors = {
        right[row][column]
        for row, column in mask
        if right[row][column] != 0
    }
    if len(overlap_colors) < 2:
        errors.append("mask/right overlap must expose at least two copied colours")
    if not any(
        left[row][column] == 0 and right[row][column] != 0
        for row in range(height)
        for column in range(separator)
    ):
        errors.append("right panel needs at least one non-zero cell outside the mask")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the dimensions and palette shared by the canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if facts["panel_h"] != facts["panel_w"] or facts["panel_h"] not in (5, 6):
        reasons.append("canonical panels are square with side 5 or 6")
    if facts["mask_color"] != 2:
        reasons.append("canonical left masks use colour 2")
    if facts["right_zero_count"] != 0:
        reasons.append("canonical right panels are fully non-zero")
    if facts["right_colors"] != set(range(2, 9)):
        reasons.append("canonical right panels use every colour 2..8 and no colour 1")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled = _scheduled_defaults(sample_index, difficulty)
    effective = dict(scheduled)
    effective.update({name: value for name, value in overrides.items() if value is not None})

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    panel_h = ctx.draw_int_strict("panel_h", 5, 8)
    panel_w = ctx.draw_int_strict("panel_w", 5, 8)
    mask_count = ctx.draw_int_strict("mask_count", 4, 12)
    mask_color = ctx.draw_int_strict("mask_color", 1, 8)
    right_zero_count = ctx.draw_int_strict("right_zero_count", 0, 4)
    rng = ctx.draw_rng("layout")

    mask = _connected_mask(rng, panel_h, panel_w, mask_count)
    outside_mask = sorted(
        (row, column)
        for row in range(panel_h)
        for column in range(panel_w)
        if (row, column) not in mask
    )
    zero_cells = set(rng.sample(outside_mask, right_zero_count))

    grid = full_grid(panel_h, panel_w * 2 + 1, 0)
    for row in range(panel_h):
        grid[row][panel_w] = 9
    for row, column in mask:
        grid[row][column] = mask_color

    palette = (
        _CANONICAL_RIGHT_PALETTE
        if profile in ("canonical_5", "canonical_6")
        else _BROAD_RIGHT_PALETTE
    )
    nonzero_right = [
        (row, column)
        for row in range(panel_h)
        for column in range(panel_w)
        if (row, column) not in zero_cells
    ]
    shift = rng.randrange(len(palette))
    for index, (row, column) in enumerate(nonzero_right):
        grid[row][panel_w + 1 + column] = palette[(index + shift) % len(palette)]

    # Make colour preservation explicit at the mask, independent of chance.
    first, second = sorted(mask)[:2]
    grid[first[0]][panel_w + 1 + first[1]] = palette[0]
    grid[second[0]][panel_w + 1 + second[1]] = palette[1]

    observed = observe_overrides(grid)
    expected = {
        "panel_h": panel_h,
        "panel_w": panel_w,
        "mask_count": mask_count,
        "mask_color": mask_color,
        "right_zero_count": right_zero_count,
    }
    if observed != expected:
        raise AssertionError(f"axis realization drift: expected {expected}, observed {observed}")
    findings = self_check(grid)
    if findings:
        raise AssertionError(f"generated grid violates declared grammar: {findings}")
    return grid


# ---------------------------------------------------------------------------
# Plausible wrong rules and task-linked semantic witnesses.
# ---------------------------------------------------------------------------


def _rival_color2_only(grid):
    _, left, right = _split(grid)
    return [
        [right[row][column] if left[row][column] == 2 else 0 for column in range(len(left[0]))]
        for row in range(len(left))
    ]


def _rival_copy_right(grid):
    _, _, right = _split(grid)
    return [list(row) for row in right]


def _modal_nonzero(panel) -> int:
    counts = Counter(value for row in panel for value in row if value != 0)
    if not counts:
        return 0
    largest = max(counts.values())
    return min(color for color, count in counts.items() if count == largest)


def _rival_modal_mask(grid):
    _, left, right = _split(grid)
    color = _modal_nonzero(right)
    return [[color if value != 0 else 0 for value in row] for row in left]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "color2_only": _rival_color2_only,
    "copy_right": _rival_copy_right,
    "modal_mask": _rival_modal_mask,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"color2_only": _rival_color2_only}


def _lawful_difference(rival):
    def witness(grid):
        return not self_check(grid) and rule_mirror(grid) != rival(grid)

    return witness


def _non_two_mask(grid):
    if self_check(grid):
        return False
    return semantic_observables(grid)["mask_color"] != 2 and rule_mirror(grid) != _rival_color2_only(grid)


SEMANTIC_WITNESSES = {
    "non_two_mask": _non_two_mask,
    "right_only_cells": _lawful_difference(_rival_copy_right),
    "multicolour_overlap": _lawful_difference(_rival_modal_mask),
}
WITNESS_RIVALS = {
    "non_two_mask": ["color2_only"],
    "right_only_cells": ["copy_right"],
    "multicolour_overlap": ["modal_mask"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demonstrations to eliminate every declared plausible rival."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(pair["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the mask rule")
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the mask rule")
    if reasons:
        return reasons

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            relation = (
                "same query answer"
                if rival(query["input"]) == query["output"]
                else "different query answer"
            )
            reasons.append(f"competing rule {name!r} survives every demonstration ({relation})")
    return reasons
