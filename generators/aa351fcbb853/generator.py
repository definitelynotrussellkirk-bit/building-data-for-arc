"""Generator for ``aa351fcbb853`` — bottom-row key recolors objects in order.

The nonzero cells of the final row form an ordered color key.  Every monochrome
4-connected component above that row is sorted by its bounding-box left edge,
then top edge, and recolored with the corresponding key color.  The output is a
blank same-size canvas containing only the recolored objects; the key row is
removed.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "aa351fcbb853"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6369d6244c02"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

SUMMARY = (
    "A zero-background grid has 2-4 separated monochrome objects above a "
    "bottom-row key of the same length. Read the nonzero key colors from left "
    "to right, sort the objects by left edge and then top edge, recolor object "
    "i with key color i, and erase the key row."
)

INVARIANTS = [
    "background is color 0",
    "the final row contains 2-4 distinct nonzero key colors",
    "the same number of monochrome 4-connected objects lies above the key row",
    "key colors are disjoint from all original object colors",
    "object order is bounding-box left edge, with top edge breaking a tie",
    "the output preserves every object mask, recolors every object, and removes the key row",
]

COUNTER_HYPOTHESES = [
    "drop the key row but keep the original object colors",
    "use the key colors in right-to-left order",
    "sort objects top-to-bottom instead of left-to-right",
    "recolor every object with only the first or modal key color",
    "give equal-colored input objects the same output color",
    "copy the key row or paint the key cells as the answer",
    "predict from object count, fixed positions, fixed sizes, or one memorized canvas",
]

OBJECT_PALETTES = ("distinct", "repeated")
ORDER_PATTERNS = ("strict_columns", "shared_left_edge")
KEY_SPACINGS = ("clustered", "spread")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 8/9 or generalized by difficulty",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 9/10 or generalized by difficulty",
        "valid": "9..16",
    },
    "n_objects": {
        "type": "int",
        "default": "scheduled 2..4; canonical profiles use 3",
        "valid": "2..4",
    },
    "object_palette": {
        "type": "enum",
        "default": "scheduled distinct/repeated",
        "valid": OBJECT_PALETTES,
    },
    "order_pattern": {
        "type": "enum",
        "default": "scheduled strict columns/shared left edge",
        "valid": ORDER_PATTERNS,
    },
    "key_spacing": {
        "type": "enum",
        "default": "scheduled clustered/spread",
        "valid": KEY_SPACINGS,
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)

SCHEDULE_PROFILES = (
    "canonical_8x9",
    "canonical_9x10",
    "repeated_palette_spread_key",
    "shared_left_edge_tiebreak",
)

# Canonical linked signatures after normalizing away absolute position/color.
# The three official inputs have one of these two size multisets.
_CANONICAL_SIZE_SIGNATURES = {(2, 3, 3), (2, 3, 4)}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise TypeError(f"unknown override axis: {unknown[0]}")
    bounds = {"grid_h": (8, 14), "grid_w": (9, 16), "n_objects": (2, 4)}
    for name, (lo, hi) in bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")
    choices = {
        "object_palette": OBJECT_PALETTES,
        "order_pattern": ORDER_PATTERNS,
        "key_spacing": KEY_SPACINGS,
    }
    for name, options in choices.items():
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"override {name!r}={value!r} not in {options}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive examples exercise all decisive controls."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(seed: int, sample_index: int, band: str) -> dict[str, Any]:
    profile = schedule_profile(seed, sample_index, band)
    rng = stable_rng(
        int(seed), f"{TASK_ID}|{sample_index}|scheduled-defaults", VERSION
    )
    if profile == "canonical_8x9":
        return {
            "grid_h": 8,
            "grid_w": 9,
            "n_objects": 3,
            "object_palette": "distinct",
            "order_pattern": "strict_columns",
            "key_spacing": "clustered",
        }
    if profile == "canonical_9x10":
        return {
            "grid_h": 9,
            "grid_w": 10,
            "n_objects": 3,
            "object_palette": "distinct",
            "order_pattern": "strict_columns",
            "key_spacing": "clustered",
        }
    if profile == "repeated_palette_spread_key":
        dims = {
            "easy": ((8, 11), (9, 12)),
            "medium": ((10, 12), (11, 13)),
            "hard": ((13, 15), (14, 16)),
        }[band]
        height, width = rng.choice(dims)
        return {
            "grid_h": height,
            "grid_w": width,
            "n_objects": {"easy": 2, "medium": 3, "hard": 4}[band],
            "object_palette": "repeated",
            "order_pattern": "strict_columns",
            "key_spacing": "spread",
        }
    dims = {
        "easy": ((8, 10), (9, 11)),
        "medium": ((10, 13), (11, 14)),
        "hard": ((13, 15), (14, 16)),
    }[band]
    height, width = rng.choice(dims)
    return {
        "grid_h": height,
        "grid_w": width,
        "n_objects": {"easy": 3, "medium": 3, "hard": 4}[band],
        "object_palette": rng.choice(OBJECT_PALETTES),
        "order_pattern": "shared_left_edge",
        "key_spacing": rng.choice(KEY_SPACINGS),
    }


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options) -> str:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(row for row, _col in cells)
    c0 = min(col for _row, col in cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _shape_dims(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return (
        max(row for row, _col in shape) + 1,
        max(col for _row, col in shape) + 1,
    )


_SHAPES = (
    ((0, 0), (1, 0)),
    ((0, 0), (0, 1)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (0, 1), (1, 1)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1)),
)


def _choose_shape(
    rng,
    max_h: int,
    max_w: int,
    preferred_size: int | None = None,
) -> tuple[tuple[int, int], ...]:
    candidates = [
        shape
        for shape in _SHAPES
        if _shape_dims(shape)[0] <= max_h and _shape_dims(shape)[1] <= max_w
    ]
    if preferred_size is not None:
        sized = [shape for shape in candidates if len(shape) == preferred_size]
        if sized:
            candidates = sized
    if not candidates:
        raise ValueError(f"no object shape fits {max_h}x{max_w}")
    return _normalize(rng.choice(candidates))


def _strict_column_layout(
    height: int,
    width: int,
    n: int,
    rng,
    preferred_sizes: tuple[int, ...],
    row_mixing: bool,
):
    placements = []
    for index in range(n):
        start = (index * width) // n
        end = ((index + 1) * width) // n - 1
        lane_width = end - start + 1
        max_shape_w = max(1, lane_width - (0 if index == n - 1 else 1))
        shape = _choose_shape(
            rng,
            height - 1,
            max_shape_w,
            preferred_sizes[index] if index < len(preferred_sizes) else None,
        )
        shape_h, shape_w = _shape_dims(shape)
        max_row = height - 1 - shape_h
        if row_mixing:
            row = max_row if index % 2 == 0 else 0
        else:
            row = rng.randint(0, max_row)
        max_col = end - shape_w + (1 if index == n - 1 else 0)
        col = rng.randint(start, max_col)
        placements.append((shape, row, col))
    return placements


def _shared_left_edge_layout(
    height: int,
    width: int,
    n: int,
    rng,
    preferred_sizes: tuple[int, ...],
):
    left_span = max(2, width // max(2, n))
    max_left_w = max(1, left_span - 1)
    first = _choose_shape(rng, 2, max_left_w, preferred_sizes[0])
    second = _choose_shape(rng, 2, max_left_w, preferred_sizes[1])
    h1, _w1 = _shape_dims(first)
    h2, _w2 = _shape_dims(second)
    top_row = 0
    bottom_row = height - 1 - h2
    if bottom_row <= top_row + h1:
        raise ValueError("grid too short for shared-left-edge tiebreak")
    left_col = rng.randint(0, max(0, left_span - max(_w1, _w2)))
    placements = [(first, top_row, left_col), (second, bottom_row, left_col)]

    remaining = n - 2
    if remaining <= 0:
        return placements
    right_start = left_span + 1
    available = width - right_start
    if available < remaining:
        raise ValueError("grid too narrow for right-side objects")
    for offset in range(remaining):
        start = right_start + (offset * available) // remaining
        end = right_start + ((offset + 1) * available) // remaining - 1
        lane_width = end - start + 1
        max_shape_w = max(1, lane_width - (0 if offset == remaining - 1 else 1))
        pref_index = offset + 2
        shape = _choose_shape(
            rng,
            height - 1,
            max_shape_w,
            preferred_sizes[pref_index] if pref_index < len(preferred_sizes) else None,
        )
        shape_h, shape_w = _shape_dims(shape)
        max_row = height - 1 - shape_h
        row = 0 if offset % 2 == 0 else max_row
        max_col = end - shape_w + (1 if offset == remaining - 1 else 0)
        col = rng.randint(start, max_col)
        placements.append((shape, row, col))
    return placements


def _key_columns(width: int, n: int, spacing: str, rng) -> list[int]:
    if spacing == "spread":
        return [round(index * (width - 1) / (n - 1)) for index in range(n)]
    span = 2 * (n - 1)
    start = rng.randint(0, width - span - 1)
    return [start + 2 * index for index in range(n)]


def _object_colors(n: int, mode: str, legal: list[int], rng) -> list[int]:
    if mode == "distinct":
        return rng.sample(legal, n)
    if n == 2:
        color = rng.choice(legal)
        return [color, color]
    distinct_n = n - 1
    palette = rng.sample(legal, distinct_n)
    colors = palette + [palette[0]]
    rng.shuffle(colors)
    return colors


def _preferred_sizes(profile: str, n: int) -> tuple[int, ...]:
    if profile == "canonical_8x9":
        return (2, 3, 3)
    if profile == "canonical_9x10":
        return (4, 3, 2)
    base = (2, 3, 4, 3)
    return base[:n]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    band = _band(difficulty)
    profile = schedule_profile(seed, sample_index, band)
    defaults = _scheduled_defaults(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height = _draw_int_axis(ctx, overrides, "grid_h", defaults["grid_h"], 8, 14)
    width = _draw_int_axis(ctx, overrides, "grid_w", defaults["grid_w"], 9, 16)
    n_objects = _draw_int_axis(
        ctx, overrides, "n_objects", defaults["n_objects"], 2, 4
    )
    object_palette = _draw_choice_axis(
        ctx,
        overrides,
        "object_palette",
        defaults["object_palette"],
        OBJECT_PALETTES,
    )
    order_pattern = _draw_choice_axis(
        ctx,
        overrides,
        "order_pattern",
        defaults["order_pattern"],
        ORDER_PATTERNS,
    )
    key_spacing = _draw_choice_axis(
        ctx,
        overrides,
        "key_spacing",
        defaults["key_spacing"],
        KEY_SPACINGS,
    )

    layout_rng = ctx.draw_rng("layout")
    preferred = _preferred_sizes(profile, n_objects)
    if order_pattern == "shared_left_edge":
        placements = _shared_left_edge_layout(
            height, width, n_objects, layout_rng, preferred
        )
    else:
        placements = _strict_column_layout(
            height,
            width,
            n_objects,
            layout_rng,
            preferred,
            row_mixing=profile == "repeated_palette_spread_key",
        )

    key_rng = ctx.draw_rng("key-colors")
    key_colors = key_rng.sample(list(range(1, 10)), n_objects)
    object_legal = [color for color in range(1, 10) if color not in key_colors]
    object_colors = _object_colors(
        n_objects, object_palette, object_legal, ctx.draw_rng("object-colors")
    )
    key_cols = _key_columns(width, n_objects, key_spacing, ctx.draw_rng("key-columns"))

    grid = full_grid(height, width, 0)
    for (shape, top, left), color in zip(placements, object_colors):
        for row, col in shape:
            grid[top + row][left + col] = color
    for col, color in zip(key_cols, key_colors):
        grid[height - 1][col] = color

    errors = self_check(
        grid,
        difficulty=band,
        meta={
            "n_objects": n_objects,
            "object_palette": object_palette,
            "order_pattern": order_pattern,
            "key_spacing": key_spacing,
        },
    )
    if errors:
        raise RuntimeError("constructed invalid key-row scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {name: ctx.axis_value(name) for name in AXES}
    if observed != expected:
        raise RuntimeError(
            f"returned grid lost keyed axis values: expected {expected}, observed {observed}"
        )
    return grid


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    width: int | None = None
    for row_index, row in enumerate(grid):
        if isinstance(row, str):
            try:
                values = [int(char) for char in row]
            except ValueError:
                return None, [f"row {row_index} is not a digit grid"]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            return None, [f"row {row_index} is not a sequence"]
        if width is None:
            width = len(values)
            if width == 0:
                return None, ["grid rows must be nonempty"]
        if len(values) != width:
            return None, ["grid must be rectangular"]
        if any(
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 <= value <= 9
            for value in values
        ):
            return None, ["all cells must be integer ARC colors 0..9"]
        rows.append(values)
    return rows, []


def _components(grid: list[list[int]], bg: int = 0):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == bg or (start_row, start_col) in seen:
                continue
            color = grid[start_row][start_col]
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [row for row, _col in cells]
            cols = [col for _row, col in cells]
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "shape": _normalize(cells),
                }
            )
    return components


def _output_from_parts(
    height: int,
    width: int,
    objs: list[dict[str, Any]],
    key_colors: list[int],
) -> list[list[int]]:
    output = full_grid(height, width, 0)
    for index, obj in enumerate(objs):
        for row, col in obj["cells"]:
            output[row][col] = key_colors[index]
    return output


def _analyze(grid: Any) -> dict[str, Any]:
    normalized, errors = _coerce_grid(grid)
    if errors:
        return {"errors": errors}
    assert normalized is not None
    height, width = len(normalized), len(normalized[0])
    errors = []
    if not 8 <= height <= 14:
        errors.append(f"grid height must be 8..14, got {height}")
    if not 9 <= width <= 16:
        errors.append(f"grid width must be 9..16, got {width}")

    last_row = normalized[-1]
    key_cols = [col for col, value in enumerate(last_row) if value != 0]
    key_colors = [last_row[col] for col in key_cols]
    if not 2 <= len(key_colors) <= 4:
        errors.append(f"key length must be 2..4, got {len(key_colors)}")
    if len(set(key_colors)) != len(key_colors):
        errors.append("key colors must be distinct")

    all_components = _components(normalized)
    key_components = [
        component
        for component in all_components
        if any(row == height - 1 for row, _col in component["cells"])
    ]
    if any(any(row != height - 1 for row, _col in comp["cells"]) for comp in key_components):
        errors.append("a key color is 4-connected to an above-row object")
    objs = [
        component
        for component in all_components
        if all(row != height - 1 for row, _col in component["cells"])
    ]
    objs.sort(key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
    if len(objs) != len(key_colors):
        errors.append(f"object count {len(objs)} != key length {len(key_colors)}")

    object_colors = [obj["color"] for obj in objs]
    if set(object_colors) & set(key_colors):
        errors.append("object colors and key colors must be disjoint")
    if objs and len({obj["size"] for obj in objs}) < 2:
        errors.append("object sizes must vary so fixed-size recoloring is not enough")
    if objs and not all(2 <= obj["size"] <= 4 for obj in objs):
        errors.append("every object must contain 2..4 cells")

    output = None
    if len(objs) == len(key_colors):
        output = _output_from_parts(height, width, objs, key_colors)
        for index, obj in enumerate(objs):
            if obj["color"] == key_colors[index]:
                errors.append(f"object {index} already has its assigned key color")
    c1s = [obj["bbox"][1] for obj in objs]
    order_pattern = (
        "shared_left_edge" if len(c1s) != len(set(c1s)) else "strict_columns"
    )
    object_palette = (
        "distinct" if len(set(object_colors)) == len(object_colors) else "repeated"
    )
    if key_cols and key_cols[0] == 0 and key_cols[-1] == width - 1:
        key_spacing = "spread"
    elif len(key_cols) >= 2 and all(
        right - left == 2 for left, right in zip(key_cols, key_cols[1:])
    ):
        key_spacing = "clustered"
    else:
        key_spacing = "other"

    return {
        "errors": errors,
        "grid": normalized,
        "height": height,
        "width": width,
        "key_cols": key_cols,
        "key_colors": key_colors,
        "objects": objs,
        "object_colors": object_colors,
        "object_palette": object_palette,
        "order_pattern": order_pattern,
        "key_spacing": key_spacing,
        "output": output,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the authority-valid grammar and reject shortcut-hiding scenes."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if analysis["key_spacing"] == "other":
        errors.append("key spacing must be the declared clustered or spread form")
    if analysis["output"] == analysis["grid"]:
        errors.append("the authoritative recoloring is an identity")
    if isinstance(meta, dict):
        observed = {
            "n_objects": len(analysis["objects"]),
            "object_palette": analysis["object_palette"],
            "order_pattern": analysis["order_pattern"],
            "key_spacing": analysis["key_spacing"],
        }
        for name, actual in observed.items():
            requested = meta.get(name)
            if requested is not None and requested != actual:
                errors.append(f"{name} requested {requested!r}, observed {actual!r}")
    return errors


def observe_overrides(grid: Any) -> dict[str, int | str]:
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if not errors and analysis["key_spacing"] == "other":
        errors.append("key spacing is not observable as clustered or spread")
    if errors:
        raise ValueError("cannot observe axes: " + "; ".join(errors))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_objects": len(analysis["objects"]),
        "object_palette": analysis["object_palette"],
        "order_pattern": analysis["order_pattern"],
        "key_spacing": analysis["key_spacing"],
    }


def _canonical_signature(analysis: dict[str, Any]):
    return (
        analysis["height"],
        analysis["width"],
        len(analysis["objects"]),
        len(set(value for row in analysis["grid"] for value in row)),
        tuple(sorted(obj["size"] for obj in analysis["objects"])),
    )


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    signature = _canonical_signature(analysis)
    if signature[:2] not in {(8, 9), (9, 9), (9, 10)}:
        return [f"canonical dimensions are 8x9, 9x9, or 9x10, got {signature[:2]}"]
    if signature[2] != 3:
        return [f"canonical object/key count is 3, got {signature[2]}"]
    if signature[3] != 7:
        return [f"canonical palette size is 7, got {signature[3]}"]
    if signature[4] not in _CANONICAL_SIZE_SIGNATURES:
        return [f"canonical object-size multiset not observed: {signature[4]}"]
    if analysis["object_palette"] != "distinct":
        return ["canonical object colors are distinct"]
    if analysis["order_pattern"] != "strict_columns":
        return ["canonical objects have distinct left edges"]
    return []


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    return _canonical_signature(analysis)


def semantic_signature(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    object_order = tuple(
        (obj["bbox"][1], obj["bbox"][0]) for obj in analysis["objects"]
    )
    row_order = tuple(
        (obj["bbox"][0], obj["bbox"][1])
        for obj in sorted(
            analysis["objects"], key=lambda obj: (obj["bbox"][0], obj["bbox"][1])
        )
    )
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "n_objects": len(analysis["objects"]),
        "object_palette": analysis["object_palette"],
        "order_pattern": analysis["order_pattern"],
        "key_spacing": analysis["key_spacing"],
        "object_sizes": tuple(obj["size"] for obj in analysis["objects"]),
        "object_shapes": tuple(obj["shape"] for obj in analysis["objects"]),
        "key_colors": tuple(analysis["key_colors"]),
        "object_colors": tuple(analysis["object_colors"]),
        "column_order": object_order,
        "row_order": row_order,
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return deepcopy(analysis["output"])


def _drop_key_keep_colors(grid):
    analysis = _analyze(grid)
    output = full_grid(analysis["height"], analysis["width"], 0)
    for obj in analysis["objects"]:
        for row, col in obj["cells"]:
            output[row][col] = obj["color"]
    return output


def _reverse_key_order(grid):
    analysis = _analyze(grid)
    return _output_from_parts(
        analysis["height"],
        analysis["width"],
        analysis["objects"],
        list(reversed(analysis["key_colors"])),
    )


def _row_major_order(grid):
    analysis = _analyze(grid)
    objs = sorted(
        analysis["objects"], key=lambda obj: (obj["bbox"][0], obj["bbox"][1])
    )
    return _output_from_parts(
        analysis["height"], analysis["width"], objs, analysis["key_colors"]
    )


def _single_key_color(grid):
    analysis = _analyze(grid)
    return _output_from_parts(
        analysis["height"],
        analysis["width"],
        analysis["objects"],
        [analysis["key_colors"][0]] * len(analysis["objects"]),
    )


def _same_input_color_same_output(grid):
    analysis = _analyze(grid)
    assigned: dict[int, int] = {}
    colors = []
    for index, obj in enumerate(analysis["objects"]):
        assigned.setdefault(obj["color"], analysis["key_colors"][index])
        colors.append(assigned[obj["color"]])
    return _output_from_parts(
        analysis["height"], analysis["width"], analysis["objects"], colors
    )


def _leave_key_row(grid):
    analysis = _analyze(grid)
    output = deepcopy(analysis["output"])
    output[-1] = list(analysis["grid"][-1])
    return output


def _key_cells_only(grid):
    analysis = _analyze(grid)
    output = full_grid(analysis["height"], analysis["width"], 0)
    output[-1] = list(analysis["grid"][-1])
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "drop_key_keep_original_colors": _drop_key_keep_colors,
    "reverse_key_sequence": _reverse_key_order,
    "row_major_object_order": _row_major_order,
    "single_key_color": _single_key_color,
    "same_input_color_same_output": _same_input_color_same_output,
    "leave_key_row_in_output": _leave_key_row,
    "key_cells_are_answer": _key_cells_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _valid_analysis(grid):
    analysis = _analyze(grid)
    return analysis if not analysis["errors"] else None


def _row_order_differs(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and _row_major_order(grid) != analysis["output"])


def _repeated_palette_rival_killed(grid) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and analysis["object_palette"] == "repeated"
        and _same_input_color_same_output(grid) != analysis["output"]
    )


SEMANTIC_WITNESSES = {
    "every_object_recolored": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and _drop_key_keep_colors(grid) != analysis["output"]
    ),
    "ordered_multi_color_key": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and len(analysis["key_colors"]) >= 2
        and _reverse_key_order(grid) != analysis["output"]
    ),
    "row_order_disagrees_with_column_order": _row_order_differs,
    "multiple_key_colors_matter": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and _single_key_color(grid) != analysis["output"]
    ),
    "repeated_input_colors_still_get_sequential_keys": _repeated_palette_rival_killed,
    "key_row_removed": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and _leave_key_row(grid) != analysis["output"]
    ),
    "object_masks_not_key_cells": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and _key_cells_only(grid) != analysis["output"]
    ),
    "clustered_key_positions": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and analysis["key_spacing"] == "clustered"
    ),
    "spread_key_positions": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and analysis["key_spacing"] == "spread"
    ),
    "shared_left_edge_tiebreak": lambda grid: bool(
        (analysis := _valid_analysis(grid))
        and analysis["order_pattern"] == "shared_left_edge"
    ),
    "canonical_linked_profile": lambda grid: not strict_canonical_like(grid),
}

WITNESS_RIVALS = {
    "every_object_recolored": ["drop_key_keep_original_colors"],
    "ordered_multi_color_key": ["reverse_key_sequence"],
    "row_order_disagrees_with_column_order": ["row_major_object_order"],
    "multiple_key_colors_matter": ["single_key_color"],
    "repeated_input_colors_still_get_sequential_keys": [
        "same_input_color_same_output"
    ],
    "key_row_removed": ["leave_key_row_in_output"],
    "object_masks_not_key_cells": ["key_cells_are_answer"],
    "clustered_key_positions": ["leave_key_row_in_output"],
    "spread_key_positions": ["leave_key_row_in_output"],
    "shared_left_edge_tiebreak": ["reverse_key_sequence"],
    "canonical_linked_profile": ["reverse_key_sequence"],
}


def _pair_analysis(pair, label: str):
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return None, [f"{label} must contain input and output grids"]
    analysis = _analyze(pair["input"])
    if analysis["errors"]:
        return None, [f"{label}: {error}" for error in analysis["errors"]]
    if pair["output"] != analysis["output"]:
        return None, [f"{label} output does not follow the ordered key-row rule"]
    return analysis, []


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons on which a named shortcut survives all demonstrations."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    analyses = []
    for index, pair in enumerate(demos):
        analysis, pair_errors = _pair_analysis(pair, f"demo {index}")
        reasons.extend(pair_errors)
        if analysis is not None:
            analyses.append((pair, analysis))
    _query_analysis, query_errors = _pair_analysis(query, "query")
    reasons.extend(query_errors)
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair, _ in analyses):
            reasons.append(f"competitor {name!r} survives every demonstration")

    signatures = [semantic_signature(pair["input"]) for pair, _ in analyses]
    if not any(sig["object_palette"] == "repeated" for sig in signatures):
        reasons.append("no demonstration separates object identity from input color")
    if not any(sig["order_pattern"] == "shared_left_edge" for sig in signatures):
        reasons.append("no demonstration exercises the top-edge tiebreak")
    if not any(_row_order_differs(pair["input"]) for pair, _ in analyses):
        reasons.append("no demonstration distinguishes column order from row order")
    if {sig["key_spacing"] for sig in signatures} != {"clustered", "spread"}:
        reasons.append("demonstrations do not vary irrelevant key-cell spacing")
    if len({(sig["height"], sig["width"]) for sig in signatures}) < 3:
        reasons.append("fewer than three canvas sizes leave a fixed-canvas shortcut")
    if len({sig["object_shapes"] for sig in signatures}) < 3:
        reasons.append("object masks vary fewer than three ways")
    by_count: dict[int, set[tuple[tuple[int, ...], ...]]] = {}
    for pair, sig in zip((pair for pair, _ in analyses), signatures):
        by_count.setdefault(sig["n_objects"], set()).add(
            tuple(tuple(row) for row in pair["output"])
        )
    if not any(len(outputs) >= 2 for outputs in by_count.values()):
        reasons.append("count-only prediction is not contradicted at a fixed count")
    return reasons
