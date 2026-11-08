"""Semantic generator for ARC task e0fb7511 / 57bafcdde8c3.

The canonical inputs are dense 13x13 binary fields.  The modal color is the
background.  Every 4-connected, non-background component with more than one
cell is recolored cyan (8); isolated singletons retain their original color.

Version 3 replaces the old planted-shape distribution with exact-count random
fields constrained to the canonical topology envelope.  A four-slot schedule
anchors both the published binary palette and generalized non-zero foregrounds,
so lessons refute color-specific and 8-connectivity shortcuts.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "57bafcdde8c3"
TASK_ID = "57bafcdde8c3"
VERSION = "3.0.0"
RULE_HASH = "e47ef90b42c0"
SUMMARY = (
    "Use the unique modal color as background. Recolor every non-background "
    "4-connected component of size greater than one to cyan (8), while "
    "leaving isolated singleton cells unchanged."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

INVARIANTS = [
    "the input is a 13x13 two-color field and cyan (8) is absent",
    "the unique modal background is color 1 or 7 and the foreground is color 0 or 3",
    "the foreground count lies in the canonical 27..52 range",
    "both isolated foreground cells and multi-cell 4-connected components occur",
    "a diagonal-only singleton pair distinguishes 4-connectivity from 8-connectivity",
    "multi-cell components occur both at the border and in the interior",
]

FOREGROUND_COUNTS = (27, 33, 45, 52)
BACKGROUND_COLORS = (1, 7)
FOREGROUND_COLORS = (0, 3)
SCHEDULE_PROFILES = (0, 1, 2, 3)

AXES = {
    "foreground_count": {
        "type": "int",
        "default": "four-slot canonical schedule 27|33|45|52",
        "valid": "27..52",
    },
    "background_color": {
        "type": "color",
        "default": "canonical 1 on three slots and generalized 7 on one slot",
        "valid": "1|7",
    },
    "foreground_color": {
        "type": "color",
        "default": "canonical 0 on two slots and generalized 3 on two slots",
        "valid": "0|3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_KING = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0), (1, 1),
)


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    errors: list[str] = []
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) != 13 or width != 13:
        errors.append(f"grid must be 13x13, got {len(grid)}x{width}")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
    return errors


def _background(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> int:
    counts = Counter(value for row in grid for value in row)
    return counts.most_common(1)[0][0]


def _components(
    grid: list[list[int]] | tuple[tuple[int, ...], ...],
    *,
    background: int | None = None,
    diagonal: bool = False,
) -> list[dict[str, Any]]:
    """Return color-preserving non-background connected components."""
    bg = _background(grid) if background is None else background
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != bg
    }
    offsets = _KING if diagonal else _CARDINAL
    components: list[dict[str, Any]] = []
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        stack = [start]
        cells = {start}
        while stack:
            row, col = stack.pop()
            for dr, dc in offsets:
                neighbor = row + dr, col + dc
                if (
                    neighbor in unseen
                    and grid[neighbor[0]][neighbor[1]] == color
                ):
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        components.append(
            {
                "color": color,
                "cells": cells,
                "size": len(cells),
                "touches_edge": any(
                    row in (0, height - 1) or col in (0, width - 1)
                    for row, col in cells
                ),
            }
        )
    return components


def _facts(grid: list[list[int]] | tuple[tuple[int, ...], ...]) -> dict[str, Any]:
    counts = Counter(value for row in grid for value in row)
    ordered = counts.most_common()
    background = ordered[0][0]
    components = _components(grid, background=background)
    singletons = [component for component in components if component["size"] == 1]
    multi = [component for component in components if component["size"] > 1]
    singleton_at = {
        next(iter(component["cells"])): component["color"]
        for component in singletons
    }
    diagonal_singletons = False
    for (row, col), color in singleton_at.items():
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            if singleton_at.get((row + dr, col + dc)) == color:
                diagonal_singletons = True
                break
        if diagonal_singletons:
            break
    foreground_colors = [color for color in counts if color != background]
    return {
        "counts": counts,
        "background": background,
        "foreground_colors": foreground_colors,
        "foreground_count": sum(counts[color] for color in foreground_colors),
        "components": components,
        "singletons": singletons,
        "multi": multi,
        "largest": max((component["size"] for component in components), default=0),
        "edge_multi": sum(component["touches_edge"] for component in multi),
        "interior_multi": sum(not component["touches_edge"] for component in multi),
        "diagonal_singletons": diagonal_singletons,
        "mode_tied": len(ordered) > 1 and ordered[0][1] == ordered[1][1],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-local canonical/generalized input grammar."""
    del difficulty, meta
    errors = _validate_grid(grid)
    if errors:
        return errors
    facts = _facts(grid)
    palette = set(facts["counts"])
    if len(palette) != 2:
        errors.append(f"expected exactly two input colors, got {sorted(palette)}")
    if 8 in palette:
        errors.append("cyan 8 must be absent from the input")
    if facts["mode_tied"]:
        errors.append("background mode must be unique")
    if facts["background"] not in BACKGROUND_COLORS:
        errors.append(
            f"background must be one of {BACKGROUND_COLORS}, got {facts['background']}"
        )
    if len(facts["foreground_colors"]) != 1:
        errors.append("expected exactly one foreground color")
    elif facts["foreground_colors"][0] not in FOREGROUND_COLORS:
        errors.append(
            f"foreground must be one of {FOREGROUND_COLORS}, "
            f"got {facts['foreground_colors'][0]}"
        )
    if not 27 <= facts["foreground_count"] <= 52:
        errors.append(
            f"foreground count must be in 27..52, got {facts['foreground_count']}"
        )
    object_count = len(facts["components"])
    if not 18 <= object_count <= 30:
        errors.append(f"4-connected foreground object count must be 18..30, got {object_count}")
    if len(facts["singletons"]) < 8:
        errors.append(f"need at least 8 singleton objects, got {len(facts['singletons'])}")
    if len(facts["multi"]) < 4:
        errors.append(f"need at least 4 multi-cell objects, got {len(facts['multi'])}")
    if not 3 <= facts["largest"] <= 12:
        errors.append(f"largest object must have size 3..12, got {facts['largest']}")
    if facts["edge_multi"] < 1:
        errors.append("need a multi-cell object touching the border")
    if facts["interior_multi"] < 1:
        errors.append("need an interior multi-cell object")
    if not facts["diagonal_singletons"]:
        errors.append("need a diagonal-only same-color singleton pair")
    return errors


def strict_canonical_like(grid) -> list[str]:
    errors = list(self_check(grid))
    if errors:
        return errors
    facts = _facts(grid)
    if facts["background"] != 1 or facts["foreground_colors"] != [0]:
        errors.append("strict canonical palette is background 1 and foreground 0")
    return errors


def _paint_by_size(grid, *, diagonal: bool, predicate: Callable[[dict[str, Any]], bool]):
    background = _background(grid)
    output = [list(row) for row in grid]
    for component in _components(grid, background=background, diagonal=diagonal):
        if predicate(component):
            for row, col in component["cells"]:
                output[row][col] = 8
    return output


def rule_mirror(grid):
    """Pure-Python mirror used only by tests and semantic rival checks."""
    return _paint_by_size(
        grid,
        diagonal=False,
        predicate=lambda component: component["size"] > 1,
    )


def _rival_identity(grid):
    return [list(row) for row in grid]


def _rival_recolor_all_nonbackground(grid):
    background = _background(grid)
    return [
        [background if value == background else 8 for value in row]
        for row in grid
    ]


def _rival_eight_connected(grid):
    return _paint_by_size(
        grid,
        diagonal=True,
        predicate=lambda component: component["size"] > 1,
    )


def _rival_zero_only(grid):
    return _paint_by_size(
        grid,
        diagonal=False,
        predicate=lambda component: component["color"] == 0 and component["size"] > 1,
    )


def _rival_size_two_only(grid):
    return _paint_by_size(
        grid,
        diagonal=False,
        predicate=lambda component: component["size"] == 2,
    )


def _rival_interior_only(grid):
    return _paint_by_size(
        grid,
        diagonal=False,
        predicate=lambda component: component["size"] > 1 and not component["touches_edge"],
    )


def _witness_singleton_and_cluster(grid) -> bool:
    facts = _facts(grid)
    return bool(facts["singletons"] and facts["multi"])


def _witness_diagonal_singletons(grid) -> bool:
    return bool(_facts(grid)["diagonal_singletons"])


def _witness_component_larger_than_two(grid) -> bool:
    return _facts(grid)["largest"] >= 3


def _witness_nonzero_foreground(grid) -> bool:
    facts = _facts(grid)
    return bool(facts["foreground_colors"] and facts["foreground_colors"][0] != 0)


def _witness_edge_and_interior(grid) -> bool:
    facts = _facts(grid)
    return facts["edge_multi"] > 0 and facts["interior_multi"] > 0


SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "recolor_all_nonbackground": _rival_recolor_all_nonbackground,
    "eight_connected": _rival_eight_connected,
    "zero_only": _rival_zero_only,
    "size_two_only": _rival_size_two_only,
    "interior_only": _rival_interior_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"zero_only": _rival_zero_only}
SEMANTIC_WITNESSES = {
    "singleton_and_cluster": _witness_singleton_and_cluster,
    "diagonal_singletons": _witness_diagonal_singletons,
    "component_larger_than_two": _witness_component_larger_than_two,
    "nonzero_foreground": _witness_nonzero_foreground,
    "edge_and_interior": _witness_edge_and_interior,
}
WITNESS_RIVALS = {
    "singleton_and_cluster": ("identity", "recolor_all_nonbackground"),
    "diagonal_singletons": ("eight_connected",),
    "component_larger_than_two": ("size_two_only",),
    "nonzero_foreground": ("zero_only",),
    "edge_and_interior": ("interior_only",),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require the selected rule to fit and every declared rival to be refuted."""
    errors: list[str] = []
    for index, pair in enumerate(list(demos) + [query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output grids")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} output does not match the selected rule")
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} survives every demonstration")
    return errors


def _difficulty_offset(difficulty) -> int:
    return {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    return (int(sample_index) + _difficulty_offset(difficulty)) % len(SCHEDULE_PROFILES)


def _draw_int_axis(ctx, overrides, label: str, scheduled: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return int(ctx.draw_choice(label, (scheduled,)))


def _draw_choice_axis(ctx, overrides, label: str, scheduled: int, legal: tuple[int, ...]) -> int:
    if label in overrides and overrides[label] is not None:
        return int(ctx.draw_choice(label, legal))
    return int(ctx.draw_choice(label, (scheduled,)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    foreground_count = _draw_int_axis(
        ctx, overrides, "foreground_count", FOREGROUND_COUNTS[slot], 27, 52
    )
    background_schedule = (1, 1, 1, 7)
    foreground_schedule = (0, 0, 3, 3)
    background = _draw_choice_axis(
        ctx, overrides, "background_color", background_schedule[slot], BACKGROUND_COLORS
    )
    foreground = _draw_choice_axis(
        ctx, overrides, "foreground_color", foreground_schedule[slot], FOREGROUND_COLORS
    )
    if background == foreground:
        raise ValueError("background_color and foreground_color must be distinct")

    rng = ctx.draw_rng("layout")
    population = list(range(13 * 13))
    for _attempt in range(1024):
        selected = set(rng.sample(population, foreground_count))
        grid = [
            [foreground if row * 13 + col in selected else background for col in range(13)]
            for row in range(13)
        ]
        if not self_check(grid):
            return grid
    raise RuntimeError(
        "could not draw a canonical-topology field after 1024 deterministic attempts"
    )


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    facts = _facts(grid)
    return {
        "foreground_count": facts["foreground_count"],
        "background_color": facts["background"],
        "foreground_color": facts["foreground_colors"][0],
    }


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Small deterministic malformed fixtures for future regression agents."""
    grid = generate(57, 0, difficulty="medium", foreground_count=27)
    facts = _facts(grid)
    background = facts["background"]
    foreground = facts["foreground_colors"][0]
    third = next(color for color in range(10) if color not in {background, foreground, 8})
    third_color = [list(row) for row in grid]
    third_color[0][0] = third
    missing = [list(row) for row in grid]
    row, col = next(
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == foreground
    )
    missing[row][col] = background
    inverted = [
        [foreground if value == background else background for value in row]
        for row in grid
    ]
    return [
        ("blank", [[0] * 13 for _ in range(13)]),
        ("third_color", third_color),
        ("missing_foreground", missing),
        ("inverted_roles", inverted),
    ]
