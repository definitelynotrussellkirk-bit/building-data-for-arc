"""Reviewed generator for ARC task 20b5e7246250 (keyed frame embedding).

Each input contains exactly two hollow gray (5) rectangular frames.  A
single colored key sits immediately above each frame, and a connected source
motif of the same color appears elsewhere.  The transformation returns a
fresh zero background, preserves only the gray frames, removes keys and source
motifs, and centers each normalized source shape inside the frame selected by
its key color.

The public axes are intentionally limited to facts that are exact and
recoverable from the returned grid.  Frame geometry, key placement, motif
shape, palette, and upper/lower layout still vary internally through keyed
GenCtx draws.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "20b5e7246250"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "42dd98d10175"

SUMMARY = (
    "Two hollow gray rectangular frames each have one distinct colored key "
    "cell directly above them.  Elsewhere are two connected source motifs, "
    "one in each key color.  Match by color, normalize each source motif, and "
    "center it inside the corresponding frame.  The output is rebuilt on a "
    "zero background: frames and centered copies remain; original keys and "
    "source motifs are removed."
)

INVARIANTS = [
    "background is 0 and the only foreground colors are gray 5 plus two distinct key colors",
    "exactly two 4-connected color-5 components are hollow rectangular frames",
    "each frame has exactly one singleton key immediately above an interior column",
    "each key color has exactly one separate connected source motif of size 3..5",
    "each normalized source motif fits inside its keyed frame and is centered there by the rule",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "12..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware keyed draw",
        "valid": "16..20",
    },
    "motif_size_a": {
        "type": "int",
        "default": "independent keyed draw for first frame",
        "valid": "3..5",
    },
    "motif_size_b": {
        "type": "int",
        "default": "independent keyed draw for second frame",
        "valid": "3..5",
    },
    "source_order": {
        "type": "str",
        "default": "keyed choice",
        "valid": "aligned|crossed",
    },
}

# Every shape is normalized, 4-connected, and at most 3x3.  The library
# deliberately includes equal-area alternatives so size alone never identifies
# the shape that must be embedded.
_MOTIF_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (0, 1), (1, 1)),
        ((0, 0), (1, 0), (1, 1)),
        ((0, 1), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 0)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
}

# Canonical examples use this family, including the test-only 8x6 frame.
_FRAME_SPECS = (
    (5, 7),
    (6, 6),
    (6, 7),
    (6, 8),
    (7, 5),
    (7, 6),
    (7, 7),
    (8, 6),
)


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid must have at least one column"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    errors: list[str] = []
    if height > 30 or width > 30:
        errors.append(f"grid exceeds ARC limit: {height}x{width}")
    for row in grid:
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("grid values must be integer colors 0..9")
                return errors
    return errors


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    materialized = tuple(cells)
    rows = [row for row, _ in materialized]
    cols = [col for _, col in materialized]
    return min(rows), min(cols), max(rows), max(cols)


def _shape_dims(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    r1, c1, r2, c2 = _bbox(cells)
    return r2 - r1 + 1, c2 - c1 + 1


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    materialized = tuple(cells)
    r1, c1, _, _ = _bbox(materialized)
    return tuple(sorted((row - r1, col - c1) for row, col in materialized))


def _components4(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + drow
                    next_col = current_col + dcol
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            normalized_cells = tuple(sorted(cells))
            components.append(
                {
                    "color": color,
                    "cells": normalized_cells,
                    "cell_set": frozenset(normalized_cells),
                    "bbox": _bbox(normalized_cells),
                    "size": len(normalized_cells),
                }
            )
    return sorted(components, key=lambda obj: (obj["bbox"], obj["color"]))


def _frame_border(bbox: tuple[int, int, int, int]) -> frozenset[tuple[int, int]]:
    r1, c1, r2, c2 = bbox
    return frozenset(
        [(r1, col) for col in range(c1, c2 + 1)]
        + [(r2, col) for col in range(c1, c2 + 1)]
        + [(row, c1) for row in range(r1 + 1, r2)]
        + [(row, c2) for row in range(r1 + 1, r2)]
    )


def _is_hollow_frame(grid: list[list[int]], obj: dict[str, Any]) -> bool:
    if obj["color"] != 5:
        return False
    r1, c1, r2, c2 = obj["bbox"]
    if r2 - r1 + 1 < 5 or c2 - c1 + 1 < 5:
        return False
    if obj["cell_set"] != _frame_border(obj["bbox"]):
        return False
    return all(
        grid[row][col] == 0
        for row in range(r1 + 1, r2)
        for col in range(c1 + 1, c2)
    )


def _touching8(
    left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]]
) -> bool:
    right_set = set(right)
    return any(
        (row + drow, col + dcol) in right_set
        for row, col in left
        for drow in (-1, 0, 1)
        for dcol in (-1, 0, 1)
    )


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    assert isinstance(grid, list)
    height, width = len(grid), len(grid[0])
    components = _components4(grid)
    five_objects = [obj for obj in components if obj["color"] == 5]
    frames = [obj for obj in five_objects if _is_hollow_frame(grid, obj)]
    if len(five_objects) != 2 or len(frames) != 2:
        errors.append(
            "expected exactly two color-5 components, both hollow rectangular frames"
        )
        return {"errors": errors, "components": components, "frames": frames}
    frames.sort(key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))

    if _touching8(frames[0]["cells"], frames[1]["cells"]):
        errors.append("the two frame borders must be spatially separated")

    keys: list[dict[str, Any]] = []
    for index, frame in enumerate(frames):
        r1, c1, _, c2 = frame["bbox"]
        if r1 == 0:
            errors.append(f"frame {index} has no row available for a key")
            continue
        found = [
            (r1 - 1, col, grid[r1 - 1][col])
            for col in range(c1, c2 + 1)
            if grid[r1 - 1][col] != 0
        ]
        if len(found) != 1:
            errors.append(
                f"frame {index} must have exactly one nonzero key above its top edge"
            )
            continue
        key_row, key_col, key_color = found[0]
        if not c1 < key_col < c2:
            errors.append(f"frame {index} key must lie above an interior column")
        if key_color in {0, 5}:
            errors.append(f"frame {index} key color must be neither 0 nor 5")
        keys.append(
            {
                "frame_index": index,
                "position": (key_row, key_col),
                "color": key_color,
            }
        )

    if len(keys) != 2:
        return {
            "errors": errors,
            "components": components,
            "frames": frames,
            "keys": keys,
        }
    if keys[0]["color"] == keys[1]["color"]:
        errors.append("frame keys must use two distinct colors")

    allowed_colors = {0, 5, keys[0]["color"], keys[1]["color"]}
    palette = {value for row in grid for value in row}
    extra_colors = sorted(palette - allowed_colors)
    if extra_colors:
        errors.append(f"unexpected foreground colors: {extra_colors}")

    sources: list[dict[str, Any]] = []
    for index, (frame, key) in enumerate(zip(frames, keys)):
        same_color = [obj for obj in components if obj["color"] == key["color"]]
        key_objects = [obj for obj in same_color if key["position"] in obj["cell_set"]]
        if len(key_objects) != 1 or key_objects[0]["size"] != 1:
            errors.append(f"key {index} must be a singleton component")
            continue
        source_candidates = [obj for obj in same_color if obj is not key_objects[0]]
        if len(source_candidates) != 1:
            errors.append(
                f"key color {key['color']} must have exactly one separate source motif"
            )
            continue
        source = source_candidates[0]
        if not 3 <= source["size"] <= 5:
            errors.append(f"source motif {index} must contain 3..5 cells")
        source_h, source_w = _shape_dims(source["cells"])
        r1, c1, r2, c2 = frame["bbox"]
        if source_h > r2 - r1 - 1 or source_w > c2 - c1 - 1:
            errors.append(f"source motif {index} does not fit its frame interior")
        for source_cell in source["cells"]:
            if any(
                fr1 <= source_cell[0] <= fr2 and fc1 <= source_cell[1] <= fc2
                for fr1, fc1, fr2, fc2 in (item["bbox"] for item in frames)
            ):
                errors.append(f"source motif {index} overlaps a frame bounding box")
                break
        sources.append(source)

    if len(sources) != 2:
        return {
            "errors": errors,
            "components": components,
            "frames": frames,
            "keys": keys,
            "sources": sources,
        }

    source_sort_keys = [
        (source["bbox"][0], source["bbox"][1]) for source in sources
    ]
    if source_sort_keys[0] == source_sort_keys[1]:
        errors.append("source motifs must have distinct reading-order positions")
        source_order = "unknown"
    else:
        source_order = (
            "aligned" if source_sort_keys[0] < source_sort_keys[1] else "crossed"
        )

    frame_top = min(frame["bbox"][0] for frame in frames)
    frame_bottom = max(frame["bbox"][2] for frame in frames)
    source_top = min(source["bbox"][0] for source in sources)
    source_bottom = max(source["bbox"][2] for source in sources)
    if source_bottom < frame_top:
        layout_family = "sources_above"
    elif source_top > frame_bottom:
        layout_family = "sources_below"
    else:
        layout_family = "mixed"

    return {
        "errors": errors,
        "components": components,
        "frames": frames,
        "keys": keys,
        "sources": sources,
        "facts": {
            "grid_h": height,
            "grid_w": width,
            "motif_size_a": sources[0]["size"],
            "motif_size_b": sources[1]["size"],
            "source_order": source_order,
            "layout_family": layout_family,
            "frame_sizes": tuple(
                (
                    frame["bbox"][2] - frame["bbox"][0] + 1,
                    frame["bbox"][3] - frame["bbox"][1] + 1,
                )
                for frame in frames
            ),
            "motif_shapes": tuple(_normalize(source["cells"]) for source in sources),
            "key_colors": tuple(key["color"] for key in keys),
            "key_columns": tuple(key["position"][1] for key in keys),
        },
    }


def self_check(
    grid: Any, *, difficulty: Any = None, meta: Any = None
) -> list[str]:
    """Return exact grammar violations; an empty list means rule-safe input."""
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every exact public axis from a generated grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe malformed scene: " + "; ".join(analysis["errors"]))
    facts = analysis["facts"]
    return {axis: facts[axis] for axis in AXES}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the canonical Racket transformation."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid keyed-frame scene: " + "; ".join(analysis["errors"]))
    height, width = len(grid), len(grid[0])
    output = full_grid(height, width, 0)
    for frame in analysis["frames"]:
        for row, col in frame["cells"]:
            output[row][col] = 5
    for frame, source, key in zip(
        analysis["frames"], analysis["sources"], analysis["keys"]
    ):
        del key
        normalized = _normalize(source["cells"])
        shape_h, shape_w = _shape_dims(normalized)
        r1, c1, r2, c2 = frame["bbox"]
        interior_h = r2 - r1 - 1
        interior_w = c2 - c1 - 1
        target_row = r1 + 1 + (interior_h - shape_h) // 2
        target_col = c1 + 1 + (interior_w - shape_w) // 2
        for drow, dcol in normalized:
            output[target_row + drow][target_col + dcol] = source["color"]
    return output


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if isinstance(difficulty, str) and difficulty not in {"easy", "medium", "hard"}:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        if not 0 <= float(difficulty) <= 1:
            raise ValueError("numeric difficulty must lie in [0, 1]")
    elif difficulty is not None and not isinstance(difficulty, str):
        raise ValueError("difficulty must be None, easy/medium/hard, or a number in [0, 1]")

    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    for name in ("grid_h", "grid_w", "motif_size_a", "motif_size_b"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(f"{name} override must be an integer")
    if "source_order" in overrides and overrides["source_order"] is not None:
        if not isinstance(overrides["source_order"], str):
            raise ValueError("source_order override must be a string")


def _choose_shape(ctx: Any, label: str, size: int, avoid: tuple[tuple[int, int], ...] | None = None) -> tuple[tuple[int, int], ...]:
    choices = list(_MOTIF_SHAPES[size])
    if avoid is not None and len(choices) > 1:
        choices = [shape for shape in choices if shape != avoid]
    return ctx.draw_rng(label).choice(choices)


def _placed_cells(
    shape: Iterable[tuple[int, int]], top: int, left: int
) -> tuple[tuple[int, int], ...]:
    return tuple((top + row, left + col) for row, col in shape)


def _source_position_pairs(
    shape_a: tuple[tuple[int, int], ...],
    shape_b: tuple[tuple[int, int], ...],
    *,
    width: int,
    row_limits_a: tuple[int, int],
    row_limits_b: tuple[int, int],
    source_order: str,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    shape_a_h, shape_a_w = _shape_dims(shape_a)
    shape_b_h, shape_b_w = _shape_dims(shape_b)
    del shape_a_h, shape_b_h
    positions_a = [
        (row, col)
        for row in range(row_limits_a[0], row_limits_a[1] + 1)
        for col in range(0, width - shape_a_w + 1)
    ]
    positions_b = [
        (row, col)
        for row in range(row_limits_b[0], row_limits_b[1] + 1)
        for col in range(0, width - shape_b_w + 1)
    ]
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for position_a in positions_a:
        cells_a = _placed_cells(shape_a, *position_a)
        for position_b in positions_b:
            if source_order == "aligned" and not position_a < position_b:
                continue
            if source_order == "crossed" and not position_b < position_a:
                continue
            cells_b = _placed_cells(shape_b, *position_b)
            if _touching8(cells_a, cells_b):
                continue
            pairs.append((position_a, position_b))
    return pairs


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: Any = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    height = ctx.draw_int_diff("grid_h", 12, 14)
    width = ctx.draw_int_diff("grid_w", 16, 20)
    motif_size_a = ctx.draw_int("motif_size_a", 3, 5)
    motif_size_b = ctx.draw_int("motif_size_b", 3, 5)
    source_order = ctx.draw_choice("source_order", ("aligned", "crossed"))

    shape_a = _choose_shape(ctx, "motif_shape_a", motif_size_a)
    shape_b = _choose_shape(
        ctx,
        "motif_shape_b",
        motif_size_b,
        avoid=shape_a if motif_size_a == motif_size_b else None,
    )
    shape_a_h, shape_a_w = _shape_dims(shape_a)
    shape_b_h, shape_b_w = _shape_dims(shape_b)
    max_shape_h = max(shape_a_h, shape_b_h)

    layout_family = ctx.draw_choice(
        "layout_family", ("sources_above", "sources_below")
    )
    max_frame_h = height - max_shape_h - 2
    frame_pairs = [
        (left, right)
        for left in _FRAME_SPECS
        for right in _FRAME_SPECS
        if left[0] <= max_frame_h
        and right[0] <= max_frame_h
        and left[1] >= shape_a_w + 2
        and left[0] >= shape_a_h + 2
        and right[1] >= shape_b_w + 2
        and right[0] >= shape_b_h + 2
        and left[1] + right[1] + 1 <= width
    ]
    if not frame_pairs:
        raise ValueError("no feasible frame pair for requested dimensions and motifs")
    frame_a_size, frame_b_size = ctx.draw_rng("frame_specs").choice(frame_pairs)
    max_frame_height = max(frame_a_size[0], frame_b_size[0])

    if layout_family == "sources_below":
        max_frame_top = height - max_frame_height - max_shape_h - 1
        if max_frame_top < 1:
            raise ValueError("no upper-frame placement fits requested scene")
        frame_top = ctx.draw_rng("frame_top").randint(1, max_frame_top)
        source_min_row = frame_top + max_frame_height + 1
        row_limits_a = (source_min_row, height - shape_a_h)
        row_limits_b = (source_min_row, height - shape_b_h)
    else:
        min_frame_top = max_shape_h + 2
        max_frame_top = height - max_frame_height
        if min_frame_top > max_frame_top:
            raise ValueError("no lower-frame placement fits requested scene")
        frame_top = ctx.draw_rng("frame_top").randint(min_frame_top, max_frame_top)
        row_limits_a = (0, frame_top - shape_a_h - 2)
        row_limits_b = (0, frame_top - shape_b_h - 2)

    frame_a_h, frame_a_w = frame_a_size
    frame_b_h, frame_b_w = frame_b_size
    max_gap = width - frame_a_w - frame_b_w
    gap = ctx.draw_rng("frame_gap").randint(1, max_gap)
    remaining = width - frame_a_w - frame_b_w - gap
    frame_a_col = ctx.draw_rng("frame_shift").randint(0, remaining)
    frame_b_col = frame_a_col + frame_a_w + gap

    positions = _source_position_pairs(
        shape_a,
        shape_b,
        width=width,
        row_limits_a=row_limits_a,
        row_limits_b=row_limits_b,
        source_order=source_order,
    )
    if not positions:
        raise ValueError("no isolated source placements satisfy requested source order")
    source_a_pos, source_b_pos = ctx.draw_rng("source_positions").choice(positions)

    grid = full_grid(height, width, 0)
    draw_frame(
        grid,
        frame_top,
        frame_a_col,
        frame_top + frame_a_h - 1,
        frame_a_col + frame_a_w - 1,
        5,
    )
    draw_frame(
        grid,
        frame_top,
        frame_b_col,
        frame_top + frame_b_h - 1,
        frame_b_col + frame_b_w - 1,
        5,
    )

    key_colors = ctx.draw_distinct_colors("key_colors", n=2, exclude=(0, 5))
    key_a_col = ctx.draw_rng("key_position_a").randint(
        frame_a_col + 1, frame_a_col + frame_a_w - 2
    )
    key_b_col = ctx.draw_rng("key_position_b").randint(
        frame_b_col + 1, frame_b_col + frame_b_w - 2
    )
    grid[frame_top - 1][key_a_col] = key_colors[0]
    grid[frame_top - 1][key_b_col] = key_colors[1]

    for row, col in _placed_cells(shape_a, *source_a_pos):
        grid[row][col] = key_colors[0]
    for row, col in _placed_cells(shape_b, *source_b_pos):
        grid[row][col] = key_colors[1]

    errors = self_check(grid)
    if errors:
        raise AssertionError("constructed invalid keyed-frame scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "motif_size_a": motif_size_a,
        "motif_size_b": motif_size_b,
        "source_order": source_order,
    }
    if observed != expected:
        raise AssertionError(f"override observer mismatch: {observed!r} != {expected!r}")
    return grid
