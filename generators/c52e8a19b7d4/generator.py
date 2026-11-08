"""Independent generator family for ARC task 902510d5.

This construction starts from the *output*: choose a corner, paint the target
triangle, and place a connected multicolour pattern in the opposite quadrant.
It then encodes that output as an input by removing the triangle and scattering
isolated marker dots.  The marker at the orientation corner is deliberately a
minority colour; the triangle colour must therefore be inferred from the strict
majority across all markers rather than copied from the corner.

The existing ``747486860e56`` family uses a monochrome staircase first and then
places a majority-coloured corner marker.  Keeping those construction choices
opposite gives this family an executable shortcut witness, not merely a new
random seed stream.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c52e8a19b7d4"
TASK_ID = GENERATOR_ID
SOURCE_TASK_ID = "902510d5"
RULE_TASK_ID = "747486860e56"
RULE_HASH = "f0c2f236288d"
VERSION = "1.0.0"
CONSTRUCTION_ALGORITHM_ID = "output-first-multicolor-pattern-then-minority-corner-markers-v1"

SUMMARY = (
    "Build the intended output first: a corner triangle plus a connected "
    "multicolour pattern in the opposite quadrant. Remove the triangle and "
    "encode its corner, side length, and colour with isolated markers. The "
    "unique corner marker is intentionally not the majority marker colour."
)

INVARIANTS = [
    "background is 0",
    "exactly one 8-connected multicolour pattern has at least 6 cells",
    "the preserved pattern uses at least two colours",
    "5-8 other nonzero cells are pairwise 8-isolated markers",
    "exactly one marker is at a grid corner",
    "the marker colours have a strict majority",
    "the unique corner marker is not the majority colour",
    "triangle side length equals isolated-marker count minus one",
]

CORNERS = ("tl", "tr", "bl", "br")

AXES = {
    "grid_h": {"type": "int", "default": "14..19", "valid": "14..19"},
    "grid_w": {"type": "int", "default": "14..19", "valid": "14..19"},
    "corner": {"type": "str", "default": "tl|tr|bl|br", "valid": "tl|tr|bl|br"},
    "marker_count": {"type": "int", "default": "5..8", "valid": "5..8"},
    "pattern_width": {"type": "int", "default": "4..6", "valid": "4..6"},
    "pattern_teeth": {"type": "int", "default": "2..4", "valid": "2..4"},
    "colors": {"type": "tuple[int]", "default": "six distinct nonzero colours", "valid": "1..9 distinct"},
}


def _triangle_cells(h: int, w: int, corner: str, side: int) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for i in range(side):
        width = side - i
        rr = i if corner.startswith("t") else h - 1 - i
        for j in range(width):
            cc = j if corner.endswith("l") else w - 1 - j
            cells.add((rr, cc))
    return cells


def _pattern_plan(ctx, h: int, w: int, corner: str, forbidden: set[tuple[int, int]]):
    """Plan a connected, branchy multicolour object opposite the triangle."""
    width = ctx.draw_int("pattern_width", 4, 6)
    teeth = ctx.draw_int("pattern_teeth", 2, min(4, width))
    height = 4

    # Put the pattern in the quadrant opposite the signal corner.  The local
    # comb is four-connected, but unlike the source staircase it branches and
    # receives several colours after geometry is fixed.
    r0 = 2 if corner.startswith("b") else h - height - 2
    c0 = 2 if corner.endswith("r") else w - width - 2
    spine_r = r0 + 1
    cells = {(spine_r, c0 + c) for c in range(width)}

    tooth_columns = list(range(width))
    rng = ctx.draw_rng("pattern-teeth-columns")
    rng.shuffle(tooth_columns)
    for index, c in enumerate(sorted(tooth_columns[:teeth])):
        direction = -1 if index % 2 == 0 else 1
        cells.add((spine_r + direction, c0 + c))
        # At least one two-cell tooth makes the family visibly non-staircase.
        if index == 0:
            cells.add((spine_r + 2 * direction, c0 + c))

    if cells & forbidden:
        raise RuntimeError("planned preserved pattern overlaps target triangle")
    if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
        raise RuntimeError("planned preserved pattern leaves the grid")
    return sorted(cells)


def _colour_pattern(
    cells: Iterable[tuple[int, int]], colors: tuple[int, int, int]
) -> dict[tuple[int, int], int]:
    """Colour a fixed geometry after construction, preserving connectivity."""
    ordered = sorted(cells)
    return {cell: colors[index % len(colors)] for index, cell in enumerate(ordered)}


def _halo(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    return {
        (r + dr, c + dc)
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    }


def _encode_markers(
    *,
    ctx,
    grid: list[list[int]],
    corner: str,
    triangle: set[tuple[int, int]],
    pattern: set[tuple[int, int]],
    total_markers: int,
    triangle_color: int,
    corner_color: int,
    other_color: int,
) -> list[tuple[int, int, int]]:
    """Scatter pairwise isolated markers encoding the planned triangle."""
    h, w = len(grid), len(grid[0])
    corner_cell = {
        "tl": (0, 0),
        "tr": (0, w - 1),
        "bl": (h - 1, 0),
        "br": (h - 1, w - 1),
    }[corner]
    all_corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}

    markers = [(corner_cell[0], corner_cell[1], corner_color)]
    grid[corner_cell[0]][corner_cell[1]] = corner_color

    majority_count = total_markers // 2 + 1
    colors = [triangle_color] * majority_count
    colors += [other_color] * (total_markers - majority_count - 1)
    rng = ctx.draw_rng("marker-layout")
    rng.shuffle(colors)

    blocked = _halo(pattern) | _halo({corner_cell}) | triangle | all_corners
    candidates = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in blocked and grid[r][c] == 0
    ]
    rng.shuffle(candidates)

    for color in colors:
        choice = next(
            (
                cell
                for cell in candidates
                if cell not in blocked and grid[cell[0]][cell[1]] == 0
            ),
            None,
        )
        if choice is None:
            raise RuntimeError("not enough isolated marker positions")
        r, c = choice
        grid[r][c] = color
        markers.append((r, c, color))
        blocked |= _halo({choice})
    return markers


def _multicolor_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Eight-connected components over all nonzero colours."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue: deque[tuple[int, int]] = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = rr + dr, cc + dc
                        if (
                            0 <= nr < h
                            and 0 <= nc < w
                            and grid[nr][nc] != 0
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))
            components.append(sorted(cells))
    return components


def _marker_facts(grid: list[list[int]]) -> dict[str, Any]:
    h, w = len(grid), len(grid[0])
    components = sorted(_multicolor_components(grid), key=len, reverse=True)
    if not components:
        return {"valid": False, "reason": "no nonzero components"}
    pattern = components[0]
    markers = [cell for comp in components[1:] for cell in comp]
    counts = Counter(grid[r][c] for r, c in markers)
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    corner_markers = [cell for cell in markers if cell in corners]
    ordered_counts = counts.most_common()
    majority = ordered_counts[0][0] if ordered_counts else None
    strict = bool(ordered_counts) and (
        len(ordered_counts) == 1 or ordered_counts[0][1] > ordered_counts[1][1]
    ) and ordered_counts[0][1] > len(markers) // 2
    return {
        "valid": True,
        "components": components,
        "pattern": pattern,
        "markers": markers,
        "counts": counts,
        "corner_markers": corner_markers,
        "majority_color": majority,
        "strict_majority": strict,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]

    facts = _marker_facts(grid)
    if not facts.get("valid"):
        return [facts.get("reason", "invalid component structure")]
    components = facts["components"]
    errors: list[str] = []
    if len(facts["pattern"]) < 6:
        errors.append(f"preserved pattern too small: {len(facts['pattern'])}")
    if any(len(comp) != 1 for comp in components[1:]):
        errors.append("all non-pattern components must be singleton markers")
    markers = facts["markers"]
    if not (5 <= len(markers) <= 8):
        errors.append(f"expected 5-8 isolated markers, found {len(markers)}")
    if len(facts["corner_markers"]) != 1:
        errors.append(
            f"expected exactly one corner marker, found {len(facts['corner_markers'])}"
        )
    if not facts["strict_majority"]:
        errors.append(f"marker colours lack a strict majority: {dict(facts['counts'])}")
    pattern_colors = {grid[r][c] for r, c in facts["pattern"]}
    if len(pattern_colors) < 2:
        errors.append("preserved pattern must be multicolour")
    if len(facts["corner_markers"]) == 1 and facts["majority_color"] is not None:
        r, c = facts["corner_markers"][0]
        if grid[r][c] == facts["majority_color"]:
            errors.append("corner marker must be a minority colour")
    return errors


def generate_with_metadata(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 14, 19)
    w = ctx.draw_int("grid_w", 14, 19)
    corner = ctx.draw_choice("corner", CORNERS)
    total_markers = ctx.draw_int("marker_count", 5, 8)
    triangle_side = total_markers - 1
    (
        triangle_color,
        corner_color,
        other_marker_color,
        pattern_a,
        pattern_b,
        pattern_c,
    ) = ctx.draw_distinct_colors("colors", n=6, exclude={0})

    triangle = _triangle_cells(h, w, corner, triangle_side)
    pattern_cells = _pattern_plan(ctx, h, w, corner, triangle)
    pattern_colors = _colour_pattern(pattern_cells, (pattern_a, pattern_b, pattern_c))

    # This is the planned output.  The input is encoded from it by deleting the
    # triangle and adding isolated markers.
    planned_output = full_grid(h, w, 0)
    for (r, c), color in pattern_colors.items():
        planned_output[r][c] = color
    for r, c in triangle:
        planned_output[r][c] = triangle_color

    grid = full_grid(h, w, 0)
    for (r, c), color in pattern_colors.items():
        grid[r][c] = color
    markers = _encode_markers(
        ctx=ctx,
        grid=grid,
        corner=corner,
        triangle=triangle,
        pattern=set(pattern_cells),
        total_markers=total_markers,
        triangle_color=triangle_color,
        corner_color=corner_color,
        other_color=other_marker_color,
    )

    findings = self_check(grid)
    if findings:
        raise RuntimeError("generated invalid candidate: " + "; ".join(findings))
    return {
        "grid": grid,
        "metadata": {
            "construction_algorithm_id": CONSTRUCTION_ALGORITHM_ID,
            "rule_task_id": RULE_TASK_ID,
            "corner": corner,
            "triangle_side": triangle_side,
            "triangle_color": triangle_color,
            "corner_marker_color": corner_color,
            "total_markers": total_markers,
            "pattern_cells": [list(cell) for cell in pattern_cells],
            "pattern_colors": sorted({pattern_a, pattern_b, pattern_c}),
            "marker_cells": [[r, c, color] for r, c, color in markers],
            "planned_output": planned_output,
            "draws": ctx.recorded_draws(),
        },
    }


def generate(seed, sample_index, *, difficulty=None, **overrides):
    return generate_with_metadata(
        seed, sample_index, difficulty=difficulty, **overrides
    )["grid"]
