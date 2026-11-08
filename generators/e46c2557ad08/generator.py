"""Generator for task e46c2557ad08: recolor exact horizontal gray dominoes.

The supported input manifold is intentionally all-gray: every foreground
component uses color 5 on a black background.  Exact 1x2 horizontal components
are the targets.  A vertical domino and one horizontally-adjacent non-domino
near miss are present in every ordinary scene, so orientation and exact-object
size are both answer-bearing.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e46c2557ad08"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "bba257d19e2b"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Separated gray objects on black.  Recolor exactly the 1x2 horizontal "
    "components cyan; leave a vertical domino and a horizontal-adjacency "
    "near miss gray.  Four scheduled profiles retain every canonical shape."
)

INVARIANTS = [
    "background is 0 and every foreground cell is gray 5",
    "1..6 exact horizontal gray domino components are present",
    "exactly one vertical gray domino is present and remains gray",
    "exactly one non-domino object with a horizontal adjacent pair is present",
    "all foreground components are separated by a one-cell halo",
    "every declared override is exactly recoverable from returned pixels",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "strongly weighted canonical anchors; otherwise weighted full 8..14",
        "valid": "8..14",
        "doc": "Exact grid height; explicit overrides use the full domain in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "strongly weighted canonical anchors; otherwise weighted full 9..16",
        "valid": "9..16",
        "doc": "Exact grid width; explicit overrides use the full domain in every band.",
    },
    "domino_count": {
        "type": "int",
        "default": "strongly weighted 2 on canonical profiles; otherwise weighted full 1..6",
        "valid": "1..6",
        "doc": "Exact number of horizontal gray domino components.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (
    "canonical_h3",
    "canonical_square",
    "canonical_h4",
    "mixed",
)

Cell = tuple[int, int]
Grid = list[list[int]]
Shape = frozenset[Cell]

_H_DOMINO: Shape = frozenset({(0, 0), (0, 1)})
_V_DOMINO: Shape = frozenset({(0, 0), (1, 0)})
_NEAR_SHAPES: dict[str, Shape] = {
    "h3": frozenset({(0, 0), (0, 1), (0, 2)}),
    "square": frozenset({(0, 0), (0, 1), (1, 0), (1, 1)}),
    "h4": frozenset({(0, 0), (0, 1), (0, 2), (0, 3)}),
}
_PROFILE_DEFAULTS = {
    "canonical_h3": (8, 10, 2, "h3"),
    "canonical_square": (9, 9, 2, "square"),
    "canonical_h4": (10, 11, 2, "h4"),
    "mixed": (None, None, None, None),
}
_HEIGHT_OPTIONS = {
    None: (8, 9, 10, 10, 11, 11, 12, 13, 14),
    "easy": (8, 8, 9, 9, 10, 11, 12, 13, 14),
    "medium": (8, 9, 10, 10, 11, 11, 12, 13, 14),
    "hard": (8, 9, 10, 11, 12, 12, 13, 13, 14, 14),
}
_WIDTH_OPTIONS = {
    None: (9, 10, 11, 11, 12, 12, 13, 14, 15, 16),
    "easy": (9, 9, 10, 10, 11, 12, 13, 14, 15, 16),
    "medium": (9, 10, 11, 11, 12, 12, 13, 14, 15, 16),
    "hard": (9, 10, 11, 12, 13, 13, 14, 14, 15, 16, 16),
}
_COUNT_OPTIONS = {
    None: (1, 2, 2, 3, 3, 4, 5, 6),
    "easy": (1, 1, 2, 2, 3, 4, 5, 6),
    "medium": (1, 2, 2, 3, 3, 4, 4, 5, 6),
    "hard": (1, 2, 3, 4, 4, 5, 5, 6, 6),
}
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Four consecutive samples cover all canonical-shape teaching profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))
    for label, value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} override must be an integer (not bool)")


def _draw_exact_int(ctx, label: str, scheduled: int | None, lo: int, hi: int, options) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    if scheduled is not None:
        # Keep every declared value in the draw support while making the three
        # public profiles common enough for exact-profile curriculum checks.
        anchored_options = (scheduled,) * 48 + tuple(options)
        return int(ctx.draw_choice(label, anchored_options))
    return int(ctx.draw_choice(label, options))


def _translate(shape: Shape, top: int, left: int) -> set[Cell]:
    return {(top + row, left + col) for row, col in shape}


def _halo(cells: set[Cell], height: int, width: int) -> set[Cell]:
    return {
        (row + dr, col + dc)
        for row, col in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= row + dr < height and 0 <= col + dc < width
    }


def _flip_cells(cells: set[Cell], height: int, width: int, *, vertical: bool, horizontal: bool) -> set[Cell]:
    transformed: set[Cell] = set()
    for row, col in cells:
        if vertical:
            row = height - 1 - row
        if horizontal:
            col = width - 1 - col
        transformed.add((row, col))
    return transformed


def _build_scene(height: int, width: int, domino_count: int, near_kind: str, rng) -> Grid:
    """Construct without retries; every documented integer combination is feasible."""
    near_shape = _NEAR_SHAPES[near_kind]
    near_height = max(row for row, _ in near_shape) + 1
    vertical = _translate(_V_DOMINO, 0, 0)
    near = _translate(near_shape, height - near_height, 0)
    blocked = _halo(vertical, height, width) | _halo(near, height, width)

    feasible_lattices: list[list[set[Cell]]] = []
    # Starts spaced by three rows/columns make every target pair halo-separated.
    for row_offset in range(3):
        for col_offset in range(3):
            slots: list[set[Cell]] = []
            for row in range(row_offset, height, 3):
                for col in range(col_offset, width - 1, 3):
                    cells = {(row, col), (row, col + 1)}
                    if not cells & blocked:
                        slots.append(cells)
            if len(slots) >= domino_count:
                feasible_lattices.append(slots)
    if not feasible_lattices:
        raise AssertionError(
            f"no constructive layout for {height}x{width}, count={domino_count}, near={near_kind}"
        )

    slots = list(rng.choice(feasible_lattices))
    rng.shuffle(slots)
    targets = slots[:domino_count]

    vertical_flip = bool(rng.randrange(2))
    horizontal_flip = bool(rng.randrange(2))
    vertical = _flip_cells(
        vertical, height, width, vertical=vertical_flip, horizontal=horizontal_flip
    )
    near = _flip_cells(
        near, height, width, vertical=vertical_flip, horizontal=horizontal_flip
    )
    targets = [
        _flip_cells(
            cells, height, width, vertical=vertical_flip, horizontal=horizontal_flip
        )
        for cells in targets
    ]

    grid = full_grid(height, width, 0)
    for cells in [vertical, near, *targets]:
        for row, col in cells:
            grid[row][col] = 5
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_count, scheduled_near = _PROFILE_DEFAULTS[profile]
    height = _draw_exact_int(
        ctx, "grid_h", scheduled_h, 8, 14, _HEIGHT_OPTIONS[difficulty]
    )
    width = _draw_exact_int(
        ctx, "grid_w", scheduled_w, 9, 16, _WIDTH_OPTIONS[difficulty]
    )
    domino_count = _draw_exact_int(
        ctx, "domino_count", scheduled_count, 1, 6, _COUNT_OPTIONS[difficulty]
    )
    rng = ctx.draw_rng("layout")
    near_kind = scheduled_near or rng.choice(tuple(_NEAR_SHAPES))
    grid = _build_scene(height, width, domino_count, near_kind, rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    expected = {
        "grid_h": height,
        "grid_w": width,
        "domino_count": domino_count,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and exact public contracts
# ---------------------------------------------------------------------------


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) for row in grid):
        return "every row must be a list"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    if any(type(value) is not int for row in grid for value in row):
        return "grid values must be integers (not bool)"
    return None


def _normalize(cells: set[Cell]) -> Shape:
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return frozenset((row - top, col - left) for row, col in cells)


def _components(grid: Grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            start = (start_row, start_col)
            if color == 0 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: set[Cell] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in _DIR4:
                    neighbor = (row + dr, col + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(
                {"color": color, "cells": cells, "shape": _normalize(cells)}
            )
    return components


def _has_horizontal_pair(cells: set[Cell]) -> bool:
    return any((row, col + 1) in cells for row, col in cells)


def _analyze(grid: Any) -> dict[str, Any]:
    shape_error = _shape_error(grid)
    if shape_error:
        return {"errors": [shape_error]}
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 8 <= height <= 14 or not 9 <= width <= 16:
        errors.append(f"grid dimensions {height}x{width} are outside 8..14 by 9..16")
    if any(value not in (0, 5) for row in grid for value in row):
        errors.append("ordinary task inputs may contain only background 0 and gray 5")
    components = _components(grid)

    # Distinct gray objects must remain visually separated, including diagonals.
    for index, component in enumerate(components):
        halo = _halo(component["cells"], height, width)
        for other in components[index + 1 :]:
            if halo & other["cells"]:
                errors.append("foreground components must be separated by a one-cell halo")
                break
        if errors and errors[-1].startswith("foreground components"):
            break

    horizontal = [component for component in components if component["shape"] == _H_DOMINO]
    vertical = [component for component in components if component["shape"] == _V_DOMINO]
    near = [
        component
        for component in components
        if component["shape"] in set(_NEAR_SHAPES.values())
    ]
    unsupported = [
        component
        for component in components
        if component["shape"] not in {_H_DOMINO, _V_DOMINO, *_NEAR_SHAPES.values()}
    ]
    if not 1 <= len(horizontal) <= 6:
        errors.append(f"expected 1..6 horizontal dominoes, found {len(horizontal)}")
    if len(vertical) != 1:
        errors.append(f"expected exactly one vertical domino, found {len(vertical)}")
    if len(near) != 1:
        errors.append(f"expected exactly one horizontal-adjacency near miss, found {len(near)}")
    if unsupported:
        errors.append(f"found {len(unsupported)} unsupported foreground component shape(s)")
    if len(components) != len(horizontal) + 2:
        errors.append("expected only target dominoes plus the two mandatory distractors")

    return {
        "errors": sorted(set(errors)),
        "height": height,
        "width": width,
        "components": components,
        "horizontal": horizontal,
        "vertical": vertical,
        "near": near,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "domino_count": len(analysis["horizontal"]),
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    near_shape = next(
        name for name, shape in _NEAR_SHAPES.items() if analysis["near"][0]["shape"] == shape
    )
    return {
        **observe_overrides(grid),
        "vertical_dominoes": len(analysis["vertical"]),
        "near_miss_shape": near_shape,
        "palette": tuple(sorted({value for row in grid for value in row})),
    }


def rule_mirror(grid: Grid) -> Grid:
    """Pure test mirror; the pinned Racket source remains output authority."""
    output = deepcopy(grid)
    if _shape_error(grid):
        raise ValueError(_shape_error(grid))
    for component in _components(grid):
        if component["color"] == 5 and component["shape"] == _H_DOMINO:
            for row, col in component["cells"]:
                output[row][col] = 8
    return output


# ---------------------------------------------------------------------------
# Named rivals and lesson identifiability
# ---------------------------------------------------------------------------


def _rival_all_gray_dominoes(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for component in _components(grid):
        if component["color"] == 5 and len(component["cells"]) == 2:
            for row, col in component["cells"]:
                output[row][col] = 8
    return output


def _rival_any_horizontal_pair(grid: Grid) -> Grid:
    output = deepcopy(grid)
    for component in _components(grid):
        if component["color"] == 5 and _has_horizontal_pair(component["cells"]):
            for row, col in component["cells"]:
                output[row][col] = 8
    return output


def _witness_vertical_domino(grid: Grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and len(analysis["vertical"]) == 1


def _witness_horizontal_near_miss(grid: Grid) -> bool:
    analysis = _analyze(grid)
    return bool(
        not analysis["errors"]
        and analysis["near"]
        and _has_horizontal_pair(analysis["near"][0]["cells"])
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "vertical_domino": _witness_vertical_domino,
    "horizontal_pair_near_miss": _witness_horizontal_near_miss,
}
SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "all_gray_dominoes": _rival_all_gray_dominoes,
    "any_horizontal_pair": _rival_any_horizontal_pair,
}
WITNESS_RIVALS = {
    "vertical_domino": ["all_gray_dominoes"],
    "horizontal_pair_near_miss": ["any_horizontal_pair"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report named rivals that fit demonstrations but change the query answer."""
    errors: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict):
        return ["query must be an input/output pair"]
    pairs = list(demos) + [query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output")
            continue
        structural = self_check(pair["input"])
        if structural:
            errors.append(f"pair {index} input: {'; '.join(structural)}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} output disagrees with the pinned rule mirror")
    if errors:
        return sorted(set(errors))

    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                errors.append(f"named rival {name} fits all demos but changes the query")
    return sorted(set(errors))
