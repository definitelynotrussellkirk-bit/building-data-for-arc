"""Generator for ``S5_M1`` — quadrant palette summary.

The input is split at its horizontal and vertical midpoints.  Each non-empty
quadrant contains exactly one color, and the four non-empty colors are distinct.
The output is the 2x2 row-major table of those quadrant colors, using 0 for the
(optional) empty quadrant.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.blobs import grow_blob
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "31e0316dace3"
VERSION = "3.0.0"
TASK_ID = "31e0316dace3"
RULE_HASH = "00eaf58ae429"
SUMMARY = (
    "Split an even 6..14 by 6..14 zero-background grid into four equal "
    "quadrants. Each non-empty quadrant contains 2..6 cells of one color; "
    "the quadrant colors are distinct, and at most one quadrant is empty. "
    "Return a 2x2 grid containing the first non-zero color in each quadrant "
    "in row-major order, or 0 for the empty quadrant."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and every value is an ARC color 0..9",
    "height and width are even, with half-dimensions in 3..7",
    "exactly three or four quadrants are non-empty",
    "each non-empty quadrant contains 2..6 cells of exactly one color",
    "non-empty quadrants use pairwise-distinct colors",
]

EMPTY_QUADRANTS = (
    "none",
    "top_left",
    "top_right",
    "bottom_left",
    "bottom_right",
)
MASS_PROFILES = ("uniform", "stair", "zigzag")
COMPONENT_PATTERNS = ("connected", "split")

AXES = {
    "half_h": {
        "type": "int",
        "default": "difficulty-skewed 3..7",
        "valid": "3..7",
    },
    "half_w": {
        "type": "int",
        "default": "difficulty-skewed 3..7",
        "valid": "3..7",
    },
    "base_cells": {
        "type": "int",
        "default": "sample-index schedule",
        "valid": "2..3",
    },
    "mass_profile": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "uniform|stair|zigzag",
    },
    "component_pattern": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "connected|split",
    },
    "empty_quadrant": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "none|top_left|top_right|bottom_left|bottom_right",
    },
}

_QUADRANT_NAMES = ("top_left", "top_right", "bottom_left", "bottom_right")


def _scheduled_choice(ctx, label: str, options: tuple, index: int):
    """Use a deterministic lesson schedule unless the caller overrides it.

    A singleton keyed draw records the scheduled value in ``GenCtx``.  Explicit
    overrides are validated against the full declared domain, so every boundary
    remains available in every difficulty band.
    """
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (options[index % len(options)],))


def _quadrants(h: int, w: int) -> list[tuple[int, int, int, int]]:
    hh, hw = h // 2, w // 2
    return [
        (0, hh, 0, hw),
        (0, hh, hw, w),
        (hh, h, 0, hw),
        (hh, h, hw, w),
    ]


def _profile_counts(base_cells: int, mass_profile: str) -> list[int]:
    if mass_profile == "uniform":
        return [base_cells] * 4
    if mass_profile == "stair":
        return [base_cells, base_cells + 1, base_cells + 2, base_cells + 3]
    if mass_profile == "zigzag":
        return [base_cells + 2, base_cells, base_cells + 3, base_cells + 1]
    raise ValueError(f"unknown mass_profile {mass_profile!r}")


def _split_cells(rng, qh: int, qw: int, size: int) -> set[tuple[int, int]]:
    """Return exactly two orthogonally disconnected components.

    The compact component occupies one corner of a 3x3 stencil; one isolated
    cell occupies the opposite corner.  Reflections and translations vary the
    geometry while preserving exact component count for sizes 2..6.
    """
    if not 2 <= size <= 6 or qh < 3 or qw < 3:
        raise ValueError("split pattern requires size 2..6 in a >=3x3 quadrant")
    connected_order = [(0, 0), (0, 1), (1, 0), (1, 1), (0, 2)]
    cells = set(connected_order[: size - 1])
    cells.add((2, 2))
    if rng.randrange(2):
        cells = {(2 - r, c) for r, c in cells}
    if rng.randrange(2):
        cells = {(r, 2 - c) for r, c in cells}
    r0 = rng.randint(0, qh - 3)
    c0 = rng.randint(0, qw - 3)
    return {(r + r0, c + c0) for r, c in cells}


def _component_count(cells: set[tuple[int, int]]) -> int:
    remaining = set(cells)
    count = 0
    while remaining:
        count += 1
        stack = [remaining.pop()]
        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


def _analysis(grid) -> dict | None:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return None
    h = len(grid)
    if h % 2 or w % 2:
        return None
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return None

    colors: list[set[int]] = []
    cells: list[set[tuple[int, int]]] = []
    for r0, r1, c0, c1 in _quadrants(h, w):
        quadrant_cells = {
            (r - r0, c - c0)
            for r in range(r0, r1)
            for c in range(c0, c1)
            if grid[r][c] != 0
        }
        quadrant_colors = {
            grid[r][c]
            for r in range(r0, r1)
            for c in range(c0, c1)
            if grid[r][c] != 0
        }
        cells.append(quadrant_cells)
        colors.append(quadrant_colors)
    return {
        "h": h,
        "w": w,
        "colors": colors,
        "cells": cells,
        "counts": [len(item) for item in cells],
        "components": [_component_count(item) if item else 0 for item in cells],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lesson grammar while accepting every canonical input."""
    del difficulty, meta
    analysis = _analysis(grid)
    if analysis is None:
        return ["grid must be rectangular, even-sized, and contain ARC colors 0..9"]

    h, w = analysis["h"], analysis["w"]
    errors: list[str] = []
    if not 6 <= h <= 14:
        errors.append(f"height {h} outside 6..14")
    if not 6 <= w <= 14:
        errors.append(f"width {w} outside 6..14")

    nonempty_colors: list[int] = []
    empty_count = 0
    for index, (colors, cells) in enumerate(zip(analysis["colors"], analysis["cells"])):
        name = _QUADRANT_NAMES[index]
        if not colors:
            empty_count += 1
            continue
        if len(colors) != 1:
            errors.append(f"{name} contains {len(colors)} non-zero colors (need exactly 1)")
            continue
        if not 2 <= len(cells) <= 6:
            errors.append(f"{name} has {len(cells)} colored cells (need 2..6)")
        nonempty_colors.append(next(iter(colors)))

    if empty_count > 1:
        errors.append(f"{empty_count} empty quadrants (at most 1 allowed)")
    if len(nonempty_colors) != len(set(nonempty_colors)):
        errors.append("non-empty quadrant colors must be pairwise distinct")
    return errors


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every declared semantic axis from a returned generated grid."""
    analysis = _analysis(grid)
    if analysis is None:
        return {}

    observed: dict[str, int | str] = {
        "half_h": analysis["h"] // 2,
        "half_w": analysis["w"] // 2,
    }
    empty_indices = [i for i, colors in enumerate(analysis["colors"]) if not colors]
    if len(empty_indices) == 0:
        observed["empty_quadrant"] = "none"
    elif len(empty_indices) == 1:
        observed["empty_quadrant"] = _QUADRANT_NAMES[empty_indices[0]]
    else:
        return observed

    empty_index = empty_indices[0] if empty_indices else -1
    profile_matches: list[tuple[str, int]] = []
    for profile in MASS_PROFILES:
        for base_cells in (2, 3):
            expected = _profile_counts(base_cells, profile)
            if all(
                index == empty_index or analysis["counts"][index] == expected[index]
                for index in range(4)
            ):
                profile_matches.append((profile, base_cells))
    if len(profile_matches) == 1:
        observed["mass_profile"], observed["base_cells"] = profile_matches[0]

    active_components = [
        count for count in analysis["components"] if count != 0
    ]
    if active_components and set(active_components) == {1}:
        observed["component_pattern"] = "connected"
    elif active_components and set(active_components) == {2}:
        observed["component_pattern"] = "split"
    return observed


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python mirror of the canonical Racket rule for focused tests."""
    h, w = len(grid), len(grid[0])
    output = full_grid(2, 2, 0)
    for index, (r0, r1, c0, c1) in enumerate(_quadrants(h, w)):
        values = [
            grid[r][c]
            for r in range(r0, r1)
            for c in range(c0, c1)
            if grid[r][c] != 0
        ]
        output[index // 2][index % 2] = values[0] if values else 0
    return output


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    half_h = ctx.draw_int_diff("half_h", 3, 7)
    half_w = ctx.draw_int_diff("half_w", 3, 7)
    base_cells = _scheduled_choice(ctx, "base_cells", (2, 3), sample_index)
    mass_profile = _scheduled_choice(
        ctx, "mass_profile", MASS_PROFILES, sample_index
    )
    component_pattern = _scheduled_choice(
        ctx, "component_pattern", COMPONENT_PATTERNS, sample_index
    )
    empty_quadrant = _scheduled_choice(
        ctx, "empty_quadrant", EMPTY_QUADRANTS, sample_index
    )

    h, w = half_h * 2, half_w * 2
    grid = full_grid(h, w, 0)
    palette = ctx.draw_rng("palette").sample(range(1, 10), 4)
    counts = _profile_counts(base_cells, mass_profile)
    empty_index = (
        -1 if empty_quadrant == "none" else _QUADRANT_NAMES.index(empty_quadrant)
    )

    for index, ((r0, r1, c0, c1), color, size) in enumerate(
        zip(_quadrants(h, w), palette, counts)
    ):
        if index == empty_index:
            continue
        rng = ctx.draw_rng(f"quadrant_{index}_shape")
        qh, qw = r1 - r0, c1 - c0
        if component_pattern == "connected":
            local_cells = grow_blob(rng, qh, qw, set(), size, max_attempts=100)
            if local_cells is None:
                raise RuntimeError(
                    f"failed to place connected size-{size} blob in {qh}x{qw} quadrant"
                )
        else:
            local_cells = _split_cells(rng, qh, qw, size)
        for r, c in local_cells:
            grid[r0 + r][c0 + c] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failure: {errors}")
    return grid
