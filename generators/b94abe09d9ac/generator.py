"""Semantic generator for ARC task b94abe09d9ac.

Read every nonzero 4-connected component from left to right, normalize each
component by translation, and compare the resulting literal shapes. The Racket
oracle returns an N x N matrix with 8 for equal shapes and 0 otherwise.

The curriculum mixes complete official shape profiles with broader partitions.
Colors and absolute positions deliberately vary because the canonical rule
normalizes both away.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "b94abe09d9ac"
TASK_ID = "b94abe09d9ac"
VERSION = "3.0.0"
RULE_HASH = "f8c93b65800b"
SUMMARY = (
    "Place 3-5 separated monochrome objects left-to-right with a nontrivial "
    "shape-equivalence partition; compare translation-normalized shapes into "
    "an N x N 8/0 equality matrix."
)
INVARIANTS = [
    "literal 0 is the unique modal background and each nonzero object is monochrome and 4-connected",
    "3-5 objects have disjoint left-to-right column spans separated by at least one zero column",
    "at least one object pair has equal shape and at least one pair has unequal shape",
    "an equal-shape pair uses different colors, proving that color is ignored",
    "when colors repeat, at least one repeated color crosses unequal shapes",
    "the output is the left-to-right object shape-equivalence matrix, 8 for equal and 0 otherwise",
]

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
EXPECTED_OUTPUT_CODOMAIN = 66
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware rng 7..9", "valid": "7..9"},
    "grid_w": {"type": "int", "default": "difficulty-aware rng 13..18", "valid": "13..18"},
    "n_blobs": {"type": "int", "default": "coverage schedule 3..5", "valid": "3..5"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..3"},
}

Shape = tuple[tuple[int, int], ...]

CANONICAL_PROFILES: tuple[tuple[str, int, int, tuple[Shape, ...]], ...] = (
    ("train_1", 7, 13, (
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    )),
    ("train_2", 8, 16, (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    )),
    ("train_3", 9, 15, (
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    )),
    ("train_4", 8, 14, (
        ((0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 1), (1, 0), (1, 1), (2, 0)),
    )),
    ("test_1", 8, 18, (
        ((0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    )),
)
_CANONICAL_SIGNATURES = {
    (height, width, shapes): name
    for name, height, width, shapes in CANONICAL_PROFILES
}

# Four distinct width-one shapes make the tight 13-column/five-object boundary
# constructive even when the requested partition has four equivalence classes.
_SHAPE_BANK: tuple[Shape, ...] = (
    ((0, 0), (1, 0)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (1, 0), (2, 0), (3, 0)),
    ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)),
    ((0, 0), (0, 1)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2)),
    ((0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (1, 2), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
    ((0, 0), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
)


def _partition_labelings(n: int) -> tuple[tuple[int, ...], ...]:
    """All nontrivial ordered equality patterns as restricted-growth strings."""
    out: list[tuple[int, ...]] = []

    def visit(prefix: list[int], maximum: int) -> None:
        if len(prefix) == n:
            if 1 < maximum + 1 < n:
                out.append(tuple(prefix))
            return
        for label in range(maximum + 2):
            prefix.append(label)
            visit(prefix, max(maximum, label))
            prefix.pop()

    visit([0], 0)
    return tuple(out)


_LABELINGS_BY_N = {n: _partition_labelings(n) for n in (3, 4, 5)}
_ALL_LABELINGS = tuple(
    labels for n in (3, 4, 5) for labels in _LABELINGS_BY_N[n]
)
assert tuple(len(_LABELINGS_BY_N[n]) for n in (3, 4, 5)) == (3, 13, 50)
assert len(_ALL_LABELINGS) == EXPECTED_OUTPUT_CODOMAIN


def _shape_height(shape: Shape) -> int:
    return max(row for row, _ in shape) + 1


def _shape_width(shape: Shape) -> int:
    return max(col for _, col in shape) + 1


def _components_nonzero(grid) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r0, c0 = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (r0 + dr, c0 + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] != 0
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(cells)
    components.sort(key=lambda cells: min(col for _, col in cells))
    return components


def _shape_norm(cells) -> Shape:
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _valid_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _valid_grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if not 7 <= height <= 9:
        errors.append(f"height must be in 7..9, saw {height}")
    if not 13 <= width <= 18:
        errors.append(f"width must be in 13..18, saw {width}")

    frequencies = Counter(value for row in grid for value in row)
    if frequencies[0] <= max(
        (count for color, count in frequencies.items() if color != 0),
        default=0,
    ):
        errors.append("literal 0 must be the unique modal background")

    components = _components_nonzero(grid)
    if not 3 <= len(components) <= 5:
        errors.append(f"expected 3..5 nonzero components, saw {len(components)}")

    shapes: list[Shape] = []
    colors: list[int] = []
    spans: list[tuple[int, int]] = []
    component_facts = []
    for index, cells in enumerate(components):
        values = {grid[row][col] for row, col in cells}
        if len(values) != 1:
            errors.append(f"component {index} must be monochrome, saw {sorted(values)}")
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        bbox_h = max(rows) - min(rows) + 1
        bbox_w = max(cols) - min(cols) + 1
        if not 2 <= len(cells) <= 7:
            errors.append(f"component {index} size must be in 2..7, saw {len(cells)}")
        if not 1 <= bbox_h <= 5 or not 1 <= bbox_w <= 3:
            errors.append(f"component {index} bbox must fit 1..5 by 1..3, saw {bbox_h}x{bbox_w}")
        shapes.append(_shape_norm(cells))
        colors.append(grid[cells[0][0]][cells[0][1]])
        spans.append((min(cols), max(cols)))
        component_facts.append({
            "cells": tuple(sorted(cells)),
            "shape": shapes[-1],
            "color": colors[-1],
            "bbox": (min(rows), min(cols), max(rows), max(cols)),
            "size": len(cells),
        })

    for index in range(1, len(spans)):
        if spans[index - 1][1] + 1 >= spans[index][0]:
            errors.append("component spans need a zero-column gap and strict left-to-right order")
            break

    shape_counts = Counter(shapes)
    if shape_counts and not any(count >= 2 for count in shape_counts.values()):
        errors.append("missing an equal-shape pair")
    if shape_counts and len(shape_counts) < 2:
        errors.append("missing an unequal-shape pair")
    duplicate_diff_color = any(
        shapes[left] == shapes[right] and colors[left] != colors[right]
        for left in range(len(shapes)) for right in range(left + 1, len(shapes))
    )
    if shapes and not duplicate_diff_color:
        errors.append("an equal-shape pair must use different colors")

    distinct_colors = len(set(colors))
    if components and not 2 <= distinct_colors <= 3:
        errors.append(f"expected 2..3 distinct object colors, saw {distinct_colors}")
    same_color_diff_shape = any(
        shapes[left] != shapes[right] and colors[left] == colors[right]
        for left in range(len(shapes)) for right in range(left + 1, len(shapes))
    )
    if components and distinct_colors < len(components) and not same_color_diff_shape:
        errors.append("reused colors must cross at least one unequal-shape pair")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": component_facts,
        "shapes": tuple(shapes),
        "colors": tuple(colors),
        "n_blobs": len(components),
        "n_distinct_colors": distinct_colors,
        "duplicate_shape_different_color": duplicate_diff_color,
        "same_color_different_shape": same_color_diff_shape,
    }


def _assign_colors(labels: list[int], n_colors: int, rng) -> list[int]:
    palette = rng.sample(list(range(1, 10)), n_colors)
    by_class: dict[int, list[int]] = {}
    for index, label in enumerate(labels):
        by_class.setdefault(label, []).append(index)
    duplicate_class = next(label for label, positions in by_class.items() if len(positions) >= 2)
    duplicate_positions = by_class[duplicate_class]
    colors: list[int | None] = [None] * len(labels)
    colors[duplicate_positions[0]] = palette[0]
    colors[duplicate_positions[1]] = palette[1]

    if n_colors < len(labels):
        cross_position = next(
            index for index, label in enumerate(labels)
            if label != duplicate_class and colors[index] is None
        )
        colors[cross_position] = palette[0]
    for color in palette:
        if color not in colors:
            target = next(index for index, value in enumerate(colors) if value is None)
            colors[target] = color
    for index, value in enumerate(colors):
        if value is None:
            colors[index] = rng.choice(palette)
    return [int(value) for value in colors]


def _spread_extra(total: int, buckets: int, rng) -> list[int]:
    out = [0] * buckets
    for _ in range(total):
        out[rng.randrange(buckets)] += 1
    return out


def _render_scene(height, width, shapes, labels, n_colors, rng):
    widths = [_shape_width(shape) for shape in shapes]
    occupied = sum(widths) + (len(shapes) - 1) + 2
    if occupied > width:
        raise ValueError(f"selected shapes need {occupied} columns, requested {width}")
    extras = _spread_extra(width - occupied, len(shapes) + 1, rng)
    colors = _assign_colors(labels, n_colors, rng)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    col = 1 + extras[0]
    for index, shape in enumerate(shapes):
        shape_h = _shape_height(shape)
        row = rng.randint(1, height - shape_h - 1)
        for dr, dc in shape:
            grid[row + dr][col + dc] = colors[index]
        if index + 1 < len(shapes):
            col += widths[index] + 1 + extras[index + 1]
    return grid


def _canonical_scene(ctx):
    rng = ctx.draw_rng(f"canonical_profile|{ctx.difficulty or 'all'}")
    name, profile_h, profile_w, profile_shapes = rng.choice(CANONICAL_PROFILES)
    # Even this correlated prior records every exact AXES value by its own key.
    height = ctx.draw_int("grid_h", profile_h, profile_h)
    width = ctx.draw_int("grid_w", profile_w, profile_w)
    n_blobs = ctx.draw_int("n_blobs", len(profile_shapes), len(profile_shapes))
    n_colors = ctx.draw_int("n_distinct_colors", 2, 3)
    class_ids: dict[Shape, int] = {}
    labels = []
    for shape in profile_shapes:
        class_ids.setdefault(shape, len(class_ids))
        labels.append(class_ids[shape])
    assert n_blobs == len(labels) and name
    return _render_scene(
        height, width, list(profile_shapes), labels, n_colors,
        ctx.draw_rng(f"canonical_layout|{name}"),
    )


def _general_scene(ctx):
    # Typed draws always use global valid ranges; exact overrides are therefore
    # difficulty-independent instead of being rejected by a band-local bound.
    height = ctx.draw_int_diff("grid_h", 7, 9)
    width = ctx.draw_int_diff("grid_w", 13, 18)
    n_colors = ctx.draw_int("n_distinct_colors", 2, 3)
    rng = ctx.draw_rng(f"general_scene|{ctx.difficulty or 'all'}")
    if ctx.overrides:
        n_blobs = ctx.draw_int_diff("n_blobs", 3, 5)
        labels = list(rng.choice(_LABELINGS_BY_N[n_blobs]))
    else:
        # Cycle the finite answer alphabet so ordinary batches teach every
        # equality pattern rather than sampling one duplicate-pair template.
        labels = list(_ALL_LABELINGS[(4 * int(ctx.seed) + int(ctx.sample_index)) % len(_ALL_LABELINGS)])
        n_blobs = ctx.draw_int("n_blobs", len(labels), len(labels))

    max_width = max(1, (width - 2 - (n_blobs - 1)) // n_blobs)
    class_count = max(labels) + 1
    legal_shapes = [
        shape for shape in _SHAPE_BANK
        if _shape_width(shape) <= max_width and _shape_height(shape) <= height - 2
    ]
    if len(legal_shapes) < class_count:
        raise ValueError(f"no legal shape set for {height=} {width=} {n_blobs=}")
    class_shapes = rng.sample(legal_shapes, class_count)
    shapes = [class_shapes[label] for label in labels]
    return _render_scene(height, width, shapes, labels, n_colors, rng)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION,
        task_id=TASK_ID, difficulty=difficulty, overrides=overrides,
    )
    use_canonical = not overrides and (
        ctx.draw_rng(f"source_mix|{difficulty or 'all'}").random() < 0.28
    )
    grid = _canonical_scene(ctx) if use_canonical else _general_scene(ctx)
    errors = self_check(grid, difficulty=difficulty, meta=None)
    if errors:
        raise AssertionError("constructed invalid scene: " + "; ".join(errors))
    return grid


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis.get("errors"):
        raise ValueError("cannot observe invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_blobs": analysis["n_blobs"],
        "n_distinct_colors": analysis["n_distinct_colors"],
    }


def canonical_profile_signature(grid):
    analysis = _analysis(grid)
    if analysis.get("errors"):
        return None
    return _CANONICAL_SIGNATURES.get((analysis["height"], analysis["width"], analysis["shapes"]))


def rule_mirror(grid):
    """Test-only semantic mirror; the Racket program remains output authority."""
    errors = _valid_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    shapes = [_shape_norm(cells) for cells in _components_nonzero(grid)]
    return [[8 if left == right else 0 for right in shapes] for left in shapes]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    # Observational only: never mutate the grid or trust saved generation metadata.
    return list(_analysis(grid).get("errors", []))
