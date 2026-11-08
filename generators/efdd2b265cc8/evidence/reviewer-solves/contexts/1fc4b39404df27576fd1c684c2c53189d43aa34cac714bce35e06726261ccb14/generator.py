"""Canonical-scale curriculum for ARC task efdd2b265cc8.

The authoritative rule transposes a square grid across its main diagonal.  The
curriculum cycles through four canonical morphology profiles, exposes only two
exactly observable axes (side length and palette size), and rejects examples
where transpose is visually inert or collides with another D4 transform.

The Python mirror and semantic rivals are diagnostics only.  The retained
Racket rule remains label authority.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "efdd2b265cc8"
TASK_ID = "efdd2b265cc8"
VERSION = "3.0.0"
RULE_HASH = "f5d00e3992ee"
SUMMARY = (
    "Sparse 4x4 to 6x6 square grids drawn from four canonical morphology "
    "profiles. The output is the main-diagonal transpose; every generated "
    "example visibly and uniquely distinguishes transpose from the other D4 "
    "transforms."
)

INVARIANTS = [
    "background is 0 and at least two nonzero colors are present",
    "the canvas is square with side length 4..6",
    "the input belongs to the sparse canonical teaching grammar",
    "transpose visibly changes the input and is unique among D4 transforms",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95


AXES = {
    "grid_size": {
        "type": "int",
        "default": "four-profile canonical schedule",
        "valid": "4..6",
        "doc": "Exact square input-grid side length.",
    },
    "n_colors": {
        "type": "int",
        "default": "four-profile canonical schedule",
        "valid": "2..4",
        "doc": "Exact number of distinct nonzero colors.",
    },
}

_PROFILE_TABLE: dict[
    str, tuple[int, int, str, tuple[tuple[int, int], ...]]
] = {
    "four_points_5": (
        5,
        4,
        "four_points",
        ((0, 1), (1, 1), (2, 1), (3, 1)),
    ),
    "two_triads_6": (6, 2, "two_triads", ((0, 3), (1, 3))),
    "three_points_4": (4, 3, "three_points", ((0, 1), (1, 1), (2, 1))),
    "blob_plus_point_5": (5, 2, "blob_plus_point", ((0, 4), (1, 1))),
}
SCHEDULE_PROFILES = tuple(_PROFILE_TABLE)
_BAND_OFFSET = {None: 0, "easy": 0, "medium": 1, "hard": 2}


Grid = list[list[int]]


def _copy_grid(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


def rule_mirror(grid: Sequence[Sequence[int]]) -> Grid:
    """Fresh-output Python mirror used for tests and semantic diagnostics."""
    return [list(row) for row in zip(*grid)]


def _transpose(grid: Sequence[Sequence[int]]) -> Grid:
    return rule_mirror(grid)


def _identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


def _rotate_cw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_ccw(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)][::-1]


def _rotate_180(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in reversed(grid)]


def _flip_lr(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid: Grid) -> Grid:
    return [list(row) for row in reversed(grid)]


def _anti_transpose(grid: Grid) -> Grid:
    return _rotate_180(rule_mirror(grid))


SEMANTIC_RIVALS = {
    "identity": _identity,
    "rotate_cw": _rotate_cw,
    "rotate_ccw": _rotate_ccw,
    "rotate_180": _rotate_180,
    "flip_left_right": _flip_lr,
    "flip_up_down": _flip_ud,
    "anti_transpose": _anti_transpose,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], Grid]] = {}


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Sequence[Sequence[int]]) -> list[dict[str, object]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, object]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (row + drow, col + dcol)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors
    normalized = _copy_grid(grid)
    height, width = len(normalized), len(normalized[0])
    findings: list[str] = []
    if height != width or not 4 <= height <= 6:
        findings.append("canvas must be square with side length 4..6")

    nonzero = [value for row in normalized for value in row if value != 0]
    if not 3 <= len(nonzero) <= 6:
        findings.append("expected three to six nonzero cells")
    colors = set(nonzero)
    if not 2 <= len(colors) <= 4:
        findings.append("expected two to four distinct nonzero colors")
    if 0 not in {value for row in normalized for value in row}:
        findings.append("background color 0 must be present")

    components = _components(normalized)
    if not 2 <= len(components) <= 4:
        findings.append("expected two to four nonzero connected components")
    if components and max(len(component["cells"]) for component in components) > 4:
        findings.append("connected components may contain at most four cells")

    truth = rule_mirror(normalized)
    if truth == normalized:
        findings.append("transpose must visibly change the input")
    for name, rival in SEMANTIC_RIVALS.items():
        if truth == rival(normalized):
            findings.append(f"transpose is ambiguous with rival {name}")
    return findings


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _morphology(grid: Grid) -> str:
    components = _components(grid)
    sizes = sorted(len(component["cells"]) for component in components)
    n_colors = len({component["color"] for component in components})
    if n_colors == 4 and sizes == [1, 1, 1, 1]:
        return "four_points"
    if n_colors == 2 and sizes == [3, 3]:
        return "two_triads"
    if n_colors == 3 and sizes == [1, 1, 1]:
        return "three_points"
    if n_colors == 2 and sizes == [1, 4]:
        return "blob_plus_point"
    return "sparse_components"


def semantic_observables(grid: Grid) -> dict[str, object]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    truth = rule_mirror(grid)
    return {
        **observe_overrides(grid),
        "morphology": _morphology(grid),
        "nonzero_cells": sum(value != 0 for row in grid for value in row),
        "component_sizes": sorted(
            len(component["cells"]) for component in _components(grid)
        ),
        "visible_transpose": truth != grid,
        "unique_among_d4": all(
            truth != rival(grid) for rival in SEMANTIC_RIVALS.values()
        ),
    }


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed
    if difficulty not in _BAND_OFFSET:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    position = (int(sample_index) + _BAND_OFFSET[difficulty]) % len(SCHEDULE_PROFILES)
    return SCHEDULE_PROFILES[position]


_AXIS_LIMITS = {"grid_size": (4, 6), "n_colors": (2, 4)}
_BANDS = set(_BAND_OFFSET)

_SHAPE_VARIANTS: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (((0, 0),),),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
}


def observe_overrides(grid: Grid) -> dict[str, int]:
    errors = _grid_errors(grid)
    if errors:
        raise ValueError(errors[0])
    return {
        "grid_size": len(grid),
        "n_colors": len({value for row in grid for value in row if value != 0}),
    }


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _BANDS:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override axis/axes: " + ", ".join(unknown))
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        low, high = _AXIS_LIMITS[name]
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside declared range {low}..{high}")


def _draw_axis(ctx, overrides: dict[str, Any], name: str, default: int) -> int:
    low, high = _AXIS_LIMITS[name]
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, low, high)
    return ctx.draw_int_strict(name, default, default)


def _candidate_placements(
    size: int,
    shape: Sequence[tuple[int, int]],
    occupied: set[tuple[int, int]],
) -> list[set[tuple[int, int]]]:
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    result: list[set[tuple[int, int]]] = []
    for top in range(size - shape_h + 1):
        for left in range(size - shape_w + 1):
            cells = {(top + row, left + col) for row, col in shape}
            if not cells & occupied:
                result.append(cells)
    return result


def _construct_components(
    size: int,
    specs: Sequence[tuple[int, int]],
    palette: Sequence[int],
    rng,
) -> Grid:
    for _attempt in range(256):
        occupied: dict[tuple[int, int], int] = {}
        complete = True
        for symbolic_color, component_size in specs:
            placements: list[set[tuple[int, int]]] = []
            for shape in _SHAPE_VARIANTS[component_size]:
                placements.extend(_candidate_placements(size, shape, set(occupied)))
            if not placements:
                complete = False
                break
            for cell in rng.choice(placements):
                occupied[cell] = symbolic_color
        if not complete:
            continue
        grid = full_grid(size, size, 0)
        for (row, col), symbolic_color in occupied.items():
            grid[row][col] = palette[symbolic_color]
        if not self_check(grid):
            return grid
    raise RuntimeError(f"could not construct an unambiguous transpose grid on {size}x{size}")


def _generic_specs(n_colors: int) -> tuple[tuple[int, int], ...]:
    if n_colors == 2:
        return ((0, 3), (1, 1))
    if n_colors == 3:
        return ((0, 1), (1, 1), (2, 1))
    return ((0, 1), (1, 1), (2, 1), (3, 1))


def generate(seed, sample_index, *, difficulty=None, **overrides) -> Grid:
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_size, scheduled_colors, _morphology_name, scheduled_specs = _PROFILE_TABLE[profile]
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    size = _draw_axis(ctx, overrides, "grid_size", scheduled_size)
    n_colors = _draw_axis(ctx, overrides, "n_colors", scheduled_colors)
    palette = ctx.draw_distinct_colors("colors", n=n_colors, exclude={0})
    specs = (
        _generic_specs(n_colors)
        if any(value is not None for value in overrides.values())
        else scheduled_specs
    )
    grid = _construct_components(
        size,
        specs,
        palette,
        ctx.draw_rng("layout"),
    )
    observed = observe_overrides(grid)
    expected = {"grid_size": size, "n_colors": n_colors}
    if observed != expected:
        raise AssertionError(f"constructor failed exact axes: {observed!r} != {expected!r}")
    return _copy_grid(grid)


def _rival_disagrees(grid: Grid, name: str) -> bool:
    try:
        return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    f"transpose_not_{name}": (
        lambda grid, rival_name=name: _rival_disagrees(grid, rival_name)
    )
    for name in SEMANTIC_RIVALS
}
SEMANTIC_WITNESSES.update(
    {
        "branch_four_points": lambda grid: _morphology(grid) == "four_points",
        "branch_two_triads": lambda grid: _morphology(grid) == "two_triads",
        "branch_three_points": lambda grid: _morphology(grid) == "three_points",
        "branch_blob_plus_point": lambda grid: _morphology(grid) == "blob_plus_point",
    }
)
WITNESS_RIVALS = {
    f"transpose_not_{name}": [name] for name in SEMANTIC_RIVALS
}
BRANCH_WITNESSES = (
    "branch_four_points",
    "branch_two_triads",
    "branch_three_points",
    "branch_blob_plus_point",
)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons that leave any declared D4 competitor viable."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    valid_demos: list[dict[str, Grid]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} outside teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the transpose")
            continue
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query outside teaching grammar: {query_errors[0]}")
    else:
        expected_query = rule_mirror(query["input"])
        if query.get("output") is not None and query["output"] != expected_query:
            reasons.append("query output is not the transpose")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        )
        if fits_demos and competitor(query["input"]) != rule_mirror(query["input"]):
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons

