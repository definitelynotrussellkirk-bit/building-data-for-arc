"""Constructive input sampler for recoloring three objects by size rank.

The selected canonical Racket rule is unchanged: sort the three 4-connected
objects by area, then recolor smallest/middle/largest to 2/4/8.  This module
only generates lawful inputs and exposes a task-local semantic contract.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "697e51dfedef"
TASK_ID = GENERATOR_ID
RULE_HASH = "5f4ba5cc9570"
VERSION = "2.0.0"
SUMMARY = (
    "Exactly three separated, distinct-color 4-connected objects have distinct "
    "areas.  Their spatial order varies independently of size rank."
)

INVARIANTS = [
    "background is color 0",
    "exactly three 4-connected objects use three distinct nonzero colors",
    "object areas are strictly distinct and each object fits in a 3x3 slot",
    "different objects never 4-touch",
    "smallest, middle, and largest are recolored to 2, 4, and 8 by the authority",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 8/9 anchors or keyed 7..14",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 8/9 anchors or keyed 7..14",
        "valid": "7..14",
    },
    "layout_order": {
        "type": "str",
        "default": "six-profile canonical/broad ascending/descending/scrambled schedule",
        "valid": "ascending|descending|scrambled",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (
    "canonical_8_ascending",
    "broad_descending",
    "canonical_9_scrambled",
    "canonical_9_ascending",
    "canonical_8_descending",
    "broad_scrambled",
)
MIN_STRICT_FRAC = 1.0

_LAYOUT_ORDERS = ("ascending", "descending", "scrambled")
_INPUT_COLORS = (1, 3, 5, 6, 7, 9)
_RANK_COLORS = (2, 4, 8)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive profiles retain at least two shortcut witnesses."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_request(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"difficulty must be easy/medium/hard/None, found {difficulty!r}"
        )
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if type(value) is not int:
                raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    if "layout_order" in overrides and overrides["layout_order"] is not None:
        value = overrides["layout_order"]
        if not isinstance(value, str):
            raise TypeError("layout_order must be a string")


def _profile_defaults(profile: str) -> tuple[int | None, int | None, str]:
    if profile == "canonical_8_ascending":
        return 8, 8, "ascending"
    if profile == "canonical_8_descending":
        return 8, 8, "descending"
    if profile == "canonical_9_ascending":
        return 9, 9, "ascending"
    if profile == "canonical_9_scrambled":
        return 9, 9, "scrambled"
    if profile == "broad_descending":
        return None, None, "descending"
    if profile == "broad_scrambled":
        return None, None, "scrambled"
    raise ValueError(f"unknown internal schedule profile {profile!r}")


def _draw_dimension(ctx, name: str, scheduled: int | None, overrides: dict[str, Any]) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, 7, 14)
    if scheduled is not None:
        return ctx.draw_choice(name, (scheduled,))
    return ctx.draw_choice(name, tuple(range(7, 15)))


def _connected_shape(rng, size: int) -> tuple[tuple[int, int], ...]:
    """Construct a connected size-``size`` polyomino inside a 3x3 box."""
    cells = {(rng.randrange(3), rng.randrange(3))}
    while len(cells) < size:
        frontier = {
            (row + drow, col + dcol)
            for row, col in cells
            for drow, dcol in _DIR4
            if 0 <= row + drow < 3
            and 0 <= col + dcol < 3
            and (row + drow, col + dcol) not in cells
        }
        if not frontier:
            raise RuntimeError("internal 3x3 shape frontier unexpectedly exhausted")
        cells.add(rng.choice(sorted(frontier)))
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    nxt = row + drow, col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            ordered = tuple(sorted(cells))
            result.append(
                {
                    "color": color,
                    "cells": ordered,
                    "size": len(ordered),
                    "origin": ordered[0],
                }
            )
    return result


def _ordered_sizes(ranks: list[int], layout_order: str) -> list[int]:
    if layout_order == "ascending":
        return ranks
    if layout_order == "descending":
        return list(reversed(ranks))
    if layout_order == "scrambled":
        return [ranks[1], ranks[2], ranks[0]]
    raise ValueError(f"unknown layout_order {layout_order!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_order = _profile_defaults(profile)
    height = _draw_dimension(ctx, "grid_h", scheduled_h, overrides)
    width = _draw_dimension(ctx, "grid_w", scheduled_w, overrides)
    layout_order = ctx.draw_choice(
        "layout_order",
        _LAYOUT_ORDERS if overrides.get("layout_order") is not None else (scheduled_order,),
    )

    grid = full_grid(height, width, 0)
    slots = [(0, 0), (0, width - 3), (height - 3, 0), (height - 3, width - 3)]
    selected_slots = sorted(ctx.draw_rng("slot_selection").sample(slots, 3))

    size_pool = {
        None: tuple(range(1, 6)),
        "easy": tuple(range(1, 5)),
        "medium": tuple(range(1, 6)),
        "hard": tuple(range(1, 7)),
    }[difficulty]
    ranks = sorted(ctx.draw_rng("object_sizes").sample(size_pool, 3))
    sizes = _ordered_sizes(ranks, layout_order)
    colors = ctx.draw_rng("object_colors").sample(_INPUT_COLORS, 3)

    for index, ((base_row, base_col), size, color) in enumerate(
        zip(selected_slots, sizes, colors)
    ):
        shape = _connected_shape(ctx.draw_rng(f"shape_{index}"), size)
        for local_row, local_col in shape:
            row, col = base_row + local_row, base_col + local_col
            if grid[row][col] != 0:
                raise RuntimeError("constructive placement overlapped")
            grid[row][col] = color

    findings = self_check(grid, difficulty=difficulty, meta={"profile": profile})
    if findings:
        raise RuntimeError(f"constructive generator produced invalid input: {findings}")
    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width, "layout_order": layout_order}
    if observed != expected:
        raise RuntimeError(f"constructed axes are not observable: expected {expected}, got {observed}")
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the selected sampler manifold without raising on bad inputs."""
    del difficulty, meta
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    height = len(grid)
    errors: list[str] = []
    if not (7 <= height <= 14 and 7 <= width <= 14):
        errors.append(f"grid dimensions {(height, width)} must lie in 7..14")

    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly 3 objects, found {len(components)}")
        return errors
    colors = [item["color"] for item in components]
    sizes = [item["size"] for item in components]
    if len(set(colors)) != 3:
        errors.append(f"expected 3 distinct object colors, got {colors}")
    if len(set(sizes)) != 3:
        errors.append(f"object sizes must be strictly distinct, got {sizes}")
    if any(not 1 <= size <= 6 for size in sizes):
        errors.append(f"object sizes must lie in 1..6, got {sizes}")
    for item in components:
        rows = [row for row, _ in item["cells"]]
        cols = [col for _, col in item["cells"]]
        if max(rows) - min(rows) >= 3 or max(cols) - min(cols) >= 3:
            errors.append("each object must fit inside a 3x3 box")
            break

    occupied = {
        (row, col): item["color"]
        for item in components
        for row, col in item["cells"]
    }
    for (row, col), color in occupied.items():
        for drow, dcol in ((1, 0), (0, 1)):
            neighbor = row + drow, col + dcol
            if neighbor in occupied and occupied[neighbor] != color:
                errors.append("different objects must not 4-touch")
                return errors
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The lawful three-object manifold accepted by this selected sampler."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    findings = self_check(grid)
    if findings:
        raise ValueError("cannot observe axes on invalid input: " + "; ".join(findings))
    ordered = sorted(_components(grid), key=lambda item: item["origin"])
    sizes = [item["size"] for item in ordered]
    if sizes == sorted(sizes):
        layout_order = "ascending"
    elif sizes == sorted(sizes, reverse=True):
        layout_order = "descending"
    else:
        layout_order = "scrambled"
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "layout_order": layout_order,
    }


def _recolor(grid, ordered: Iterable[dict[str, Any]]) -> list[list[int]]:
    output = [[0 for _ in row] for row in grid]
    for item, color in zip(ordered, _RANK_COLORS):
        for row, col in item["cells"]:
            output[row][col] = color
    return output


def _size_rank_output(grid) -> list[list[int]]:
    findings = self_check(grid)
    if findings:
        raise ValueError("invalid size-rank input: " + "; ".join(findings))
    return _recolor(grid, sorted(_components(grid), key=lambda item: item["size"]))


def _reading_order_output(grid) -> list[list[int]]:
    """RIVAL: incorrectly maps 2/4/8 by top-left reading order."""
    findings = self_check(grid)
    if findings:
        raise ValueError("invalid reading-order input: " + "; ".join(findings))
    return _recolor(grid, sorted(_components(grid), key=lambda item: item["origin"]))


def _size_not_reading_order(grid) -> bool:
    return _size_rank_output(grid) != _reading_order_output(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require a labeled demo that directly refutes the reading-order shortcut."""
    del query
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is missing input/output"]
        try:
            rival = _reading_order_output(pair["input"])
        except Exception as exc:
            return [f"demo {index} is not lawful: {type(exc).__name__}: {exc}"]
        if rival != pair["output"]:
            return []
    return ["reading_order fits every demonstration"]


SEMANTIC_WITNESSES = {"size_not_reading_order": _size_not_reading_order}
SEMANTIC_RIVALS = {"reading_order": _reading_order_output}
WITNESS_RIVALS = {"size_not_reading_order": ["reading_order"]}
CANONICAL_SHORTCUTS = {"reading_order": _reading_order_output}
LESSON_COMPETITORS = {"reading_order": _reading_order_output}
