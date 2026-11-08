"""Input generator for the height-sorted palette-row task.

The unchanged Racket authority extracts non-background objects, ranks them by
bounding-box height (descending; then left edge and color for deterministic tie
handling), and returns their colors as one row.  This sampler keeps heights
strictly distinct while deliberately breaking area, position, and numeric-color
shortcuts in every generated instance.
"""
from __future__ import annotations

from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4c04ce6c5477"
TASK_ID = GENERATOR_ID
RULE_HASH = "cf026680a0b6"
VERSION = "4.0.0"
SUMMARY = (
    "A 0-background grid contains 2..5 isolated, single-color connected objects "
    "with distinct bounding-box heights. Object shapes, areas, rows, columns, and "
    "colors vary independently enough to refute area-, position-, and color-order "
    "shortcuts. The reference rule outputs one row of object colors ranked by "
    "descending bounding-box height."
)

INVARIANTS = [
    "background is color 0 and all non-background cells form 2..5 four-connected objects",
    "each object has one color, object colors are distinct, and bbox heights are distinct",
    "generated examples refute largest-area, left-to-right, top-to-bottom, and numeric-color sorting",
]

AXES = {
    "grid_h": {"type": "int", "default": "weighted 7..16", "valid": "7..16"},
    "grid_w": {"type": "int", "default": "weighted 10..18", "valid": "10..18"},
    "n_blobs": {"type": "int", "default": "weighted 2..5", "valid": "2..5"},
}

# The constructive band layout supports every advertised cross-product in every
# difficulty band, including the smallest 7x10 grid with five objects.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []


def _weighted_int(ctx, name: str, lo: int, hi: int, *, anchors: tuple[int, ...]) -> int:
    """Draw from the full exact domain while weighting curriculum anchors."""
    options = list(range(lo, hi + 1)) + list(anchors) * 18
    return ctx.draw_choice(name, options)


def _axis_anchors(difficulty: Any, canonical_core: bool) -> tuple[tuple[int, ...], ...]:
    if canonical_core:
        # These pairs cover the canonical 7x11 and 8x12 profiles; independent
        # keyed draws still retain the full legal domain for exact overrides.
        return (7, 8), (11, 12), (3,)
    if difficulty == "easy":
        return (7, 8, 9), (10, 11, 12), (2, 3)
    if difficulty == "hard":
        # Hardness mostly comes from more objects and richer shapes, but retain
        # canonical-profile mass so every band teaches the original manifold.
        return (8, 12, 14, 16), (11, 14, 16, 18), (3, 4, 5)
    return (7, 8, 10, 12), (11, 12, 14, 16), (3, 4)


def _band_widths(
    width: int,
    n_blobs: int,
    minimum_widths: dict[int, int],
    rng,
) -> list[int]:
    """Partition columns into object bands separated by one blank column."""
    widths = [max(1, minimum_widths.get(slot, 1)) for slot in range(n_blobs)]
    remaining = width - (n_blobs - 1) - sum(widths)
    if remaining < 0:
        raise ValueError("grid width cannot realize the requested object bands")
    order = list(range(n_blobs))
    rng.shuffle(order)
    for index in range(remaining):
        widths[order[index % n_blobs]] += 1
    return widths


def _bands(widths: list[int]) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    left = 0
    for band_width in widths:
        result.append((left, left + band_width - 1))
        left += band_width + 1
    return result


def _paint_rectangle(
    grid: list[list[int]], top: int, height: int, left: int, width: int, color: int
) -> None:
    for row in range(top, top + height):
        for col in range(left, left + width):
            grid[row][col] = color


def _paint_area_witness(
    grid: list[list[int]],
    top: int,
    height: int,
    left: int,
    width: int,
    color: int,
    target_area: int,
) -> None:
    """Paint a connected bbox-exact object with the requested area.

    The spine and one full arm realize the bounding box.  Additional cells are
    attached to the spine until the second-tallest object has strictly greater
    area than the tallest object.  Except for the unavoidable one-row case,
    this remains non-rectangular and therefore teaches shape invariance too.
    """
    minimum_area = height + width - 1
    maximum_area = height * width
    if not minimum_area <= target_area <= maximum_area:
        raise ValueError(
            f"target area {target_area} outside connected bbox range "
            f"[{minimum_area},{maximum_area}]"
        )

    for row in range(top, top + height):
        grid[row][left] = color
    for col in range(left + 1, left + width):
        grid[top][col] = color

    remaining = target_area - minimum_area
    for row in range(top + 1, top + height):
        for col in range(left + 1, left + width):
            if remaining == 0:
                return
            grid[row][col] = color
            remaining -= 1


def _paint_branch(
    grid: list[list[int]],
    top: int,
    height: int,
    left: int,
    width: int,
    color: int,
    rng,
) -> None:
    """Paint a connected non-rectangle with the requested bounding box."""
    if width == 1 or height == 1:
        _paint_rectangle(grid, top, height, left, width, color)
        return

    spine = left + rng.randrange(width)
    for row in range(top, top + height):
        grid[row][spine] = color

    # One full arm realizes the width. Other rows get shorter random arms,
    # keeping the object connected while avoiding a solid rectangle.
    full_row = top + rng.randrange(height)
    for col in range(left, left + width):
        grid[full_row][col] = color
    for row in range(top, top + height):
        if row == full_row or rng.random() >= 0.55:
            continue
        endpoint = left + rng.randrange(width)
        lo, hi = sorted((spine, endpoint))
        for col in range(lo, hi + 1):
            grid[row][col] = color


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
    canonical_core = (
        ctx.draw_choice(
            "curriculum_profile",
            ("canonical", "canonical", "canonical", "broad"),
        )
        == "canonical"
    )
    h_anchor, w_anchor, n_anchor = _axis_anchors(difficulty, canonical_core)
    height = _weighted_int(ctx, "grid_h", 7, 16, anchors=h_anchor)
    width = _weighted_int(ctx, "grid_w", 10, 18, anchors=w_anchor)
    n_blobs = _weighted_int(ctx, "n_blobs", 2, 5, anchors=n_anchor)

    layout_rng = ctx.draw_rng("constructive_layout")

    # Consecutive heights give broad absolute scale while guaranteeing that a
    # wider second-tallest object can outrank the tallest by area.
    start_height = layout_rng.randint(1, height - n_blobs)
    height_values = list(range(start_height, start_height + n_blobs))
    ranked_heights = sorted(height_values, reverse=True)
    tallest_height, second_height = ranked_heights[:2]

    # The tallest is never leftmost, so left-to-right cannot mimic the rule.
    tallest_slot = layout_rng.randrange(1, n_blobs)
    area_slot = layout_rng.choice([slot for slot in range(n_blobs) if slot != tallest_slot])
    slot_heights: list[int | None] = [None] * n_blobs
    slot_heights[tallest_slot] = tallest_height
    slot_heights[area_slot] = second_height
    remaining_slots = [slot for slot in range(n_blobs) if slot_heights[slot] is None]
    remaining_heights = ranked_heights[2:]
    layout_rng.shuffle(remaining_heights)
    for slot, object_height in zip(remaining_slots, remaining_heights):
        slot_heights[slot] = object_height

    # Keep the area counterexample non-rectangular whenever its height permits.
    # With a two-row runner-up, width three leaves holes while still beating the
    # tallest by area.  A one-row runner-up is possible only for two objects; in
    # that case the tallest itself becomes an L and the runner-up needs width four.
    area_width = 4 if second_height == 1 else (3 if second_height == 2 else 2)
    tallest_width = 2 if second_height == 1 else 1
    tallest_area = tallest_height + (1 if tallest_width > 1 else 0)
    area_target = tallest_area + 1
    widths = _band_widths(
        width,
        n_blobs,
        {area_slot: area_width, tallest_slot: tallest_width},
        layout_rng,
    )
    bands = _bands(widths)

    # Assign colors by height rank, explicitly avoiding numeric ascending order.
    ranked_colors = layout_rng.sample(range(1, 10), n_blobs)
    if ranked_colors == sorted(ranked_colors):
        ranked_colors[0], ranked_colors[1] = ranked_colors[1], ranked_colors[0]
    color_by_height = dict(zip(ranked_heights, ranked_colors))

    grid = full_grid(height, width, 0)
    for slot, (band_left, band_right) in enumerate(bands):
        object_height = int(slot_heights[slot])
        color = color_by_height[object_height]
        band_width = band_right - band_left + 1

        if slot == tallest_slot:
            # Bottom-align the tallest while the second-tallest starts at row 0;
            # this guarantees that top-to-bottom order is a false rule.
            top = height - object_height
            shape_width = tallest_width
            left = band_left + layout_rng.randrange(band_width - shape_width + 1)
            if shape_width > 1:
                # The two-object one-row runner-up case needs an exact L here;
                # a random branch could fill the 2x2 box and tie the area witness.
                _paint_area_witness(
                    grid,
                    top,
                    object_height,
                    left,
                    shape_width,
                    color,
                    tallest_area,
                )
            else:
                _paint_rectangle(grid, top, object_height, left, 1, color)
            continue

        if slot == area_slot:
            top = 0
            shape_width = area_width
            left = band_left + layout_rng.randrange(band_width - shape_width + 1)
            _paint_area_witness(
                grid,
                top,
                object_height,
                left,
                shape_width,
                color,
                area_target,
            )
            continue

        top = layout_rng.randint(0, height - object_height)
        max_shape_width = min(4, band_width)
        shape_width = layout_rng.randint(1, max_shape_width)
        left = band_left + layout_rng.randrange(band_width - shape_width + 1)
        if shape_width > 1 and object_height > 1 and layout_rng.random() < 0.82:
            _paint_branch(grid, top, object_height, left, shape_width, color, layout_rng)
        else:
            _paint_rectangle(grid, top, object_height, left, shape_width, color)

    return grid


def _analyze(grid: Any) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {"errors": ["expected a nonempty rectangular grid"], "components": []}
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return {"errors": ["expected nonempty rows"], "components": []}
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return {"errors": ["grid is ragged"], "components": []}
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return {"errors": ["cells must be integer ARC colors 0..9"], "components": []}

    height = len(grid)
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            colors: set[int] = set()
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                colors.add(grid[r][c])
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            components.append(
                {
                    "cells": tuple(cells),
                    "colors": tuple(sorted(colors)),
                    "color": min(colors),
                    "area": len(cells),
                    "top": min(rows),
                    "bottom": max(rows),
                    "left": min(cols),
                    "right": max(cols),
                    "height": max(rows) - min(rows) + 1,
                    "width": max(cols) - min(cols) + 1,
                }
            )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    facts = _analyze(grid)
    errors = list(facts["errors"])
    if errors:
        return errors

    height, width = facts["height"], facts["width"]
    components = facts["components"]
    if not 7 <= height <= 16:
        errors.append(f"grid height {height} outside [7,16]")
    if not 10 <= width <= 18:
        errors.append(f"grid width {width} outside [10,18]")
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 is absent")
    if not 2 <= len(components) <= 5:
        errors.append(f"expected 2..5 objects, got {len(components)}")

    colors: list[int] = []
    heights: list[int] = []
    for component in components:
        if len(component["colors"]) != 1:
            errors.append(f"connected object mixes colors {component['colors']}")
        colors.append(component["color"])
        heights.append(component["height"])
    if len(colors) != len(set(colors)):
        errors.append(f"object colors are not distinct: {colors}")
    if len(heights) != len(set(heights)):
        errors.append(f"object bbox heights are not distinct: {heights}")
    return errors


def strict_canonical_like(grid):
    """The sampler's lawful task manifold, including all canonical inputs."""
    return self_check(grid)


def observe_overrides(grid):
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_blobs": len(facts["components"]),
    }


def _palette(grid, key: Callable[[dict[str, Any]], Any]) -> list[list[int]]:
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    return [[obj["color"] for obj in sorted(facts["components"], key=key)]]


def _height_palette(grid):
    return _palette(grid, lambda obj: (-obj["height"], obj["left"], obj["color"]))


def _largest_area_first(grid):
    return _palette(grid, lambda obj: (-obj["area"], obj["left"], obj["color"]))


def _left_to_right(grid):
    return _palette(grid, lambda obj: (obj["left"], obj["color"]))


def _top_to_bottom(grid):
    return _palette(grid, lambda obj: (obj["top"], obj["left"], obj["color"]))


def _numeric_color(grid):
    return _palette(grid, lambda obj: obj["color"])


def _differs_from(rival: Callable[[Any], list[list[int]]]):
    def witness(grid) -> bool:
        return not self_check(grid) and rival(grid) != _height_palette(grid)

    return witness


SEMANTIC_RIVALS = {
    "largest_area_first": _largest_area_first,
    "left_to_right": _left_to_right,
    "top_to_bottom": _top_to_bottom,
    "numeric_color": _numeric_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "height_not_area": _differs_from(_largest_area_first),
    "height_not_left": _differs_from(_left_to_right),
    "height_not_top": _differs_from(_top_to_bottom),
    "height_not_numeric_color": _differs_from(_numeric_color),
}
WITNESS_RIVALS = {
    "height_not_area": ["largest_area_first"],
    "height_not_left": ["left_to_right"],
    "height_not_top": ["top_to_bottom"],
    "height_not_numeric_color": ["numeric_color"],
}


def lesson_identifiable(demos, query):
    """Report any named shortcut that survives all visible demonstrations."""
    del query
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one complete demonstration is required"]
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                reasons.append(f"competitor {name!r} survives all demonstrations")
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
