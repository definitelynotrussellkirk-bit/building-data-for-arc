"""Semantic generator for ``73906110dd67`` — stack objects by area.

The authoritative rule extracts every non-zero connected component, crops it
to its bounding box, sorts the crops by component cell count descending, and
stacks them top-to-bottom with one zero row between crops.  Crops are left
aligned and the output width is the widest crop.

The former generator declared fixed or ignored axes and offered no task-linked
semantic contract.  This version makes every axis recoverable from the grid and
uses a four-profile schedule whose every four consecutive demonstrations refute
plausible scan-order, color-order, bbox-area, alignment, gap, and fixed-cardinality
shortcuts.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "73906110dd67"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9b7f117d5438"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "A 10..18 by 10..18 zero-background grid contains three or four "
    "diagonally separated monochrome objects with distinct colors and distinct "
    "cell areas. Extract each object, crop it tightly, sort the crops by object "
    "cell area from largest to smallest, and stack them vertically with one "
    "zero row between neighboring crops. Crops are left aligned; output width "
    "equals the maximum crop width."
)

INVARIANTS = [
    "three or four 4-connected non-zero components",
    "component colors and component cell areas are pairwise distinct",
    "different components do not touch, including diagonally",
    "component crops fit inside 4x3 boxes and include at least two crop widths",
    "the output order is descending cell area, not scan order, color, or bbox area",
]

COUNTER_HYPOTHESES = [
    "stack components in input scan order",
    "stack smallest first",
    "sort by bounding-box area instead of occupied cell count",
    "sort by color instead of size",
    "omit the one-row separators",
    "center-align narrower crops",
    "always emit width three or always keep only three components",
    "memorize canonical 10x10 inputs or fixed object positions",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 10 or generalized 11..18",
        "valid": "10..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 10 or generalized 11..18",
        "valid": "10..18",
    },
    "n_blobs": {
        "type": "int",
        "default": "scheduled 3 or 4",
        "valid": "3..4",
    },
    "size_pattern": {
        "type": "str",
        "default": "scheduled consecutive|spread",
        "valid": "consecutive|spread",
    },
    "input_size_order": {
        "type": "str",
        "default": "scheduled ascending|descending|zigzag",
        "valid": "ascending|descending|zigzag",
    },
    "palette_kind": {
        "type": "str",
        "default": "scheduled low|high|mixed",
        "valid": "low|high|mixed",
    },
    "max_bbox_width": {
        "type": "int",
        "default": "scheduled 2 or 3",
        "valid": "2..3",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)
_SIZE_PATTERNS = ("consecutive", "spread")
_INPUT_ORDERS = ("ascending", "descending", "zigzag")
_PALETTE_KINDS = ("low", "high", "mixed")

SCHEDULE_PROFILES = (
    "canonical_consecutive_ascending_w2",
    "canonical_consecutive_zigzag_w3",
    "generalized_spread_descending_bbox_conflict",
    "generalized_spread_ascending_four_objects",
)

_CANONICAL_DIMENSIONS = {(9, 10), (10, 10), (8, 11)}
_CANONICAL_SIZE_SETS = {(3, 4, 5), (3, 4, 6)}

# All templates are normalized, 4-connected, and fit inside a 4x3 slot.
_NARROW_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
    8: (
        (
            (0, 0), (0, 1), (1, 0), (1, 1),
            (2, 0), (2, 1), (3, 0), (3, 1),
        ),
    ),
}

_WIDE_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    3: ((0, 0), (0, 1), (0, 2)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    8: (
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
}

# These sparse 3x3 shapes have bbox area 9.  In the conflict profile they are
# paired with the larger 8-cell 4x2 rectangle (bbox area 8), making bbox-area
# sorting provably disagree with occupied-cell sorting.
_SPRAWLING_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    5: ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    6: ((0, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 2)),
}


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

    integer_bounds = {
        "grid_h": (10, 18),
        "grid_w": (10, 18),
        "n_blobs": (3, 4),
        "max_bbox_width": (2, 3),
    }
    for name, (lo, hi) in integer_bounds.items():
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"override {name!r} must be an integer")
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo}, {hi}]")

    choices = {
        "size_pattern": _SIZE_PATTERNS,
        "input_size_order": _INPUT_ORDERS,
        "palette_kind": _PALETTE_KINDS,
    }
    for name, options in choices.items():
        value = overrides.get(name)
        if value is not None and value not in options:
            raise ValueError(f"override {name!r}={value!r} not in {options}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every four consecutive sample indexes visit all semantic profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(seed: int, sample_index: int, band: str) -> dict[str, Any]:
    profile = schedule_profile(seed, sample_index, band)
    rng = stable_rng(
        int(seed), f"{TASK_ID}|{sample_index}|scheduled_defaults", VERSION
    )
    generalized_dims = {
        "easy": ((11, 12), (12, 13)),
        "medium": ((13, 14), (14, 15)),
        "hard": ((16, 17), (18, 18)),
    }[band]

    if profile == "canonical_consecutive_ascending_w2":
        return {
            "grid_h": 10,
            "grid_w": 10,
            "n_blobs": 3,
            "size_pattern": "consecutive",
            "input_size_order": "ascending",
            "palette_kind": "low",
            "max_bbox_width": 2,
        }
    if profile == "canonical_consecutive_zigzag_w3":
        return {
            "grid_h": 10,
            "grid_w": 10,
            "n_blobs": 3,
            "size_pattern": "consecutive",
            "input_size_order": "zigzag",
            "palette_kind": "mixed",
            "max_bbox_width": 3,
        }

    h, w = rng.choice(generalized_dims)
    if profile == "generalized_spread_descending_bbox_conflict":
        return {
            "grid_h": h,
            "grid_w": w,
            "n_blobs": 3,
            "size_pattern": "spread",
            "input_size_order": "descending",
            "palette_kind": "high",
            "max_bbox_width": 3,
        }
    return {
        "grid_h": h,
        "grid_w": w,
        "n_blobs": 4,
        "size_pattern": "spread",
        "input_size_order": "ascending",
        "palette_kind": "mixed",
        "max_bbox_width": 2,
    }


def _normalize_shape(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = list(cells)
    r0 = min(r for r, _ in values)
    c0 = min(c for _, c in values)
    return tuple(sorted((r - r0, c - c0) for r, c in values))


def _reflect_shape(
    shape: tuple[tuple[int, int], ...], *, flip_r: bool, flip_c: bool
) -> tuple[tuple[int, int], ...]:
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    reflected = (
        ((height - 1 - r) if flip_r else r, (width - 1 - c) if flip_c else c)
        for r, c in shape
    )
    return _normalize_shape(reflected)


def _shape_bbox(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = list(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _sizes_for(pattern: str, n_blobs: int) -> list[int]:
    if pattern == "consecutive":
        return [3, 4, 5] if n_blobs == 3 else [3, 4, 5, 6]
    return [2, 5, 8] if n_blobs == 3 else [2, 4, 6, 8]


def _sizes_in_input_order(sizes: list[int], order: str) -> list[int]:
    ascending = sorted(sizes)
    if order == "ascending":
        return ascending
    if order == "descending":
        return list(reversed(ascending))
    if len(ascending) == 3:
        return [ascending[1], ascending[0], ascending[2]]
    return [ascending[2], ascending[0], ascending[3], ascending[1]]


def _shape_for(
    size: int,
    *,
    max_width: int,
    largest_size: int,
    second_largest_size: int,
    bbox_conflict: bool,
    rng,
) -> tuple[tuple[int, int], ...]:
    if bbox_conflict and max_width == 3:
        if size == largest_size:
            shape = _NARROW_SHAPES[size][0]  # size 8, 4x2 bbox area 8
        elif size == second_largest_size:
            shape = _SPRAWLING_SHAPES[size]  # bbox area 9
        else:
            shape = rng.choice(_NARROW_SHAPES[size])
    elif max_width == 3 and size == largest_size:
        shape = _WIDE_SHAPES[size]
    else:
        candidates = _NARROW_SHAPES[size]
        # The canonical w3 profile keeps a one-column crop so centered and
        # left-aligned stacking cannot be answer-equivalent.
        if max_width == 3 and size == 3:
            shape = _NARROW_SHAPES[3][0]
        else:
            shape = rng.choice(candidates)

    shape = _reflect_shape(
        shape,
        flip_r=bool(rng.randrange(2)),
        flip_c=bool(rng.randrange(2)),
    )
    height, width = _shape_bbox(shape)
    if height > 4 or width > max_width:
        raise AssertionError(f"shape {size} escaped its 4x{max_width} slot")
    return shape


def _palette(kind: str, n_blobs: int, rng) -> list[int]:
    if kind == "low":
        colors = [1, 2, 3, 4][:n_blobs]
    elif kind == "high":
        colors = [6, 7, 8, 9][:n_blobs]
    else:
        colors = [1, 6, 3, 8][:n_blobs]
    rng.shuffle(colors)
    return colors


def _component_order_by_size(sizes: list[int]) -> list[int]:
    return sorted(range(len(sizes)), key=lambda i: sizes[i], reverse=True)


def _ensure_color_order_disagrees(
    colors: list[int], sizes_in_slots: list[int]
) -> list[int]:
    size_order = _component_order_by_size(sizes_in_slots)
    color_order = sorted(range(len(colors)), key=lambda i: colors[i], reverse=True)
    if color_order == size_order:
        colors = list(colors)
        colors[0], colors[1] = colors[1], colors[0]
    return colors


def _slot_origins(h: int, w: int, n_blobs: int, rng) -> list[tuple[int, int]]:
    top = rng.randint(0, min(1, h - 10)) if h > 10 else 0
    left = rng.randint(0, min(1, w - 10)) if w > 10 else 0
    bottom = h - 4
    right = w - 4
    slots = [(top, left), (top, right), (bottom, left), (bottom, right)]
    if n_blobs == 4:
        return slots
    omitted = rng.randrange(4)
    return [slot for i, slot in enumerate(slots) if i != omitted]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, band)
    defaults = _scheduled_defaults(int(seed), int(sample_index), band)
    effective_overrides = {**defaults, **overrides}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=effective_overrides,
    )

    h = ctx.draw_int("grid_h", 10, 18)
    w = ctx.draw_int("grid_w", 10, 18)
    n_blobs = ctx.draw_int("n_blobs", 3, 4)
    size_pattern = ctx.draw_choice("size_pattern", _SIZE_PATTERNS)
    input_order = ctx.draw_choice("input_size_order", _INPUT_ORDERS)
    palette_kind = ctx.draw_choice("palette_kind", _PALETTE_KINDS)
    max_bbox_width = ctx.draw_int("max_bbox_width", 2, 3)

    layout_rng = ctx.draw_rng("layout")
    sizes = _sizes_for(size_pattern, n_blobs)
    sizes_in_slots = _sizes_in_input_order(sizes, input_order)
    colors = _ensure_color_order_disagrees(
        _palette(palette_kind, n_blobs, layout_rng), sizes_in_slots
    )
    slots = _slot_origins(h, w, n_blobs, layout_rng)
    bbox_conflict = (
        profile == "generalized_spread_descending_bbox_conflict"
        and size_pattern == "spread"
        and max_bbox_width == 3
    )

    largest = max(sizes)
    second_largest = sorted(sizes)[-2]
    grid = full_grid(h, w, 0)
    for index, ((r0, c0), size, color) in enumerate(
        zip(slots, sizes_in_slots, colors)
    ):
        shape_rng = ctx.draw_rng(f"shape_{index}_{size}")
        shape = _shape_for(
            size,
            max_width=max_bbox_width,
            largest_size=largest,
            second_largest_size=second_largest,
            bbox_conflict=bbox_conflict,
            rng=shape_rng,
        )
        shape_h, shape_w = _shape_bbox(shape)
        # Keep every bbox at its slot origin so row-major component order is
        # exact and observable. Slot omission, grid-scale offsets, colors,
        # reflections, and shape templates still vary the scene.
        dr = 0
        dc = 0
        for rr, cc in shape:
            r, c = r0 + dr + rr, c0 + dc + cc
            if grid[r][c] != 0:
                raise AssertionError("slot layout overlap")
            grid[r][c] = color

    errors = self_check(grid)
    if errors:
        raise ValueError("internal generation error: " + "; ".join(errors))
    observed = observe_overrides(grid)
    for axis, expected in ctx.recorded_draws().items():
        if axis in AXES and observed[axis] != expected:
            raise ValueError(
                f"internal axis mismatch for {axis}: requested {expected!r}, "
                f"observed {observed[axis]!r}"
            )
    return grid


# ---------------------------------------------------------------------------
# Structural analysis and Python rule mirror (Racket remains authority)
# ---------------------------------------------------------------------------


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    width: int | None = None
    for r, row in enumerate(grid):
        if isinstance(row, str):
            try:
                values = [int(ch) for ch in row]
            except ValueError:
                return None, [f"row {r} is not a digit grid"]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            return None, [f"row {r} is not a sequence"]
        if width is None:
            width = len(values)
            if width == 0:
                return None, ["grid rows must be nonempty"]
        elif len(values) != width:
            return None, ["grid must be rectangular"]
        for c, value in enumerate(values):
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return None, [f"invalid ARC color at ({r},{c}): {value!r}"]
        rows.append(values)
    return rows, []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            crop = [row[c1 : c2 + 1] for row in grid[r1 : r2 + 1]]
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (r1, c1, r2, c2),
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                    "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
                    "crop": crop,
                }
            )
    components.sort(key=lambda comp: (comp["bbox"][0], comp["bbox"][1]))
    return components


def _stack_components(
    components: list[dict[str, Any]],
    *,
    order: list[int],
    gap: int = 1,
    alignment: str = "left",
    forced_width: int | None = None,
) -> list[list[int]]:
    selected = [components[i] for i in order]
    width = forced_width or max(comp["width"] for comp in selected)
    height = sum(comp["height"] for comp in selected) + gap * (len(selected) - 1)
    out = full_grid(height, width, 0)
    top = 0
    for comp in selected:
        crop = comp["crop"]
        if alignment == "left":
            offset = 0
        elif alignment == "center":
            offset = (width - comp["width"] + 1) // 2
        else:
            raise ValueError(f"unknown alignment: {alignment}")
        if offset < 0 or offset + comp["width"] > width:
            raise ValueError("crop does not fit requested output width")
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    out[top + r][offset + c] = value
        top += comp["height"] + gap
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Python mirror used for focused tests and rivals; Racket is authority."""
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid: " + "; ".join(errors))
    comps = _components(values)
    if not comps:
        raise ValueError("no objects")
    order = sorted(range(len(comps)), key=lambda i: comps[i]["size"], reverse=True)
    return _stack_components(comps, order=order)


def _classify_size_pattern(sizes: list[int]) -> str | None:
    ordered = tuple(sorted(sizes))
    if ordered in {(3, 4, 5), (3, 4, 5, 6)}:
        return "consecutive"
    if ordered in {(2, 5, 8), (2, 4, 6, 8)}:
        return "spread"
    return None


def _classify_input_order(sizes: list[int]) -> str | None:
    ordered = sorted(sizes)
    if sizes == ordered:
        return "ascending"
    if sizes == list(reversed(ordered)):
        return "descending"
    if len(ordered) == 3 and sizes == [ordered[1], ordered[0], ordered[2]]:
        return "zigzag"
    if len(ordered) == 4 and sizes == [ordered[2], ordered[0], ordered[3], ordered[1]]:
        return "zigzag"
    return None


def _classify_palette(colors: list[int]) -> str | None:
    values = set(colors)
    if values and values <= {1, 2, 3, 4}:
        return "low"
    if values and values <= {6, 7, 8, 9}:
        return "high"
    if values <= {1, 2, 3, 4, 6, 7, 8, 9} and values & {1, 2, 3, 4} and values & {6, 7, 8, 9}:
        return "mixed"
    return None


def semantic_observables(grid: Any) -> dict[str, Any]:
    values, errors = _coerce_grid(grid)
    result: dict[str, Any] = {"errors": list(errors)}
    if errors or values is None:
        return result
    comps = _components(values)
    sizes = [comp["size"] for comp in comps]
    colors = [comp["color"] for comp in comps]
    widths = [comp["width"] for comp in comps]
    result.update(
        {
            "grid": values,
            "height": len(values),
            "width": len(values[0]),
            "components": comps,
            "n_blobs": len(comps),
            "sizes_scan_order": sizes,
            "sizes_sorted": tuple(sorted(sizes)),
            "colors": colors,
            "bbox_widths": widths,
            "max_bbox_width": max(widths) if widths else None,
            "size_pattern": _classify_size_pattern(sizes),
            "input_size_order": _classify_input_order(sizes),
            "palette_kind": _classify_palette(colors),
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding scenes."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors

    h, w = facts["height"], facts["width"]
    if not 8 <= h <= 18 or not 10 <= w <= 18:
        errors.append(f"supported authority envelope is h=8..18, w=10..18; found {h}x{w}")
    comps = facts["components"]
    if not 3 <= len(comps) <= 4:
        errors.append(f"expected 3-4 components, found {len(comps)}")

    colors = [comp["color"] for comp in comps]
    if len(colors) != len(set(colors)):
        errors.append("component colors must be pairwise distinct")
    sizes = [comp["size"] for comp in comps]
    if len(sizes) != len(set(sizes)):
        errors.append(f"component areas must be distinct, found {sizes}")
    if any(not 2 <= size <= 8 for size in sizes):
        errors.append(f"component areas must lie in 2..8, found {sizes}")

    owner = {
        cell: index
        for index, comp in enumerate(comps)
        for cell in comp["cells"]
    }
    for (r, c), index in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                other = owner.get((r + dr, c + dc))
                if other is not None and other != index:
                    errors.append("different components touch, including diagonally")
                    return errors

    for comp in comps:
        if comp["height"] > 4 or comp["width"] > 3:
            errors.append(
                f"component crop exceeds 4x3: {comp['height']}x{comp['width']}"
            )
    if comps and max(comp["width"] for comp in comps) < 2:
        errors.append("all crops have width one; output-width lesson is hidden")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Match the actual canonical dimensions, component counts, and area sets."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if (facts["height"], facts["width"]) not in _CANONICAL_DIMENSIONS:
        reasons.append("dimensions are outside the three canonical profiles")
    if facts["n_blobs"] != 3:
        reasons.append("canonical scenes contain exactly three components")
    if facts["sizes_sorted"] not in _CANONICAL_SIZE_SETS:
        reasons.append("component area multiset is not canonical")
    return reasons


def observe_overrides(grid) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors") or self_check(grid):
        raise ValueError("cannot observe axes from an invalid grid")
    observed = {
        "grid_h": facts["height"],
        "grid_w": facts["width"],
        "n_blobs": facts["n_blobs"],
        "size_pattern": facts["size_pattern"],
        "input_size_order": facts["input_size_order"],
        "palette_kind": facts["palette_kind"],
        "max_bbox_width": facts["max_bbox_width"],
    }
    missing = [name for name, value in observed.items() if value is None]
    if missing:
        raise ValueError("unobservable generated axes: " + ", ".join(missing))
    return observed


def profile_signature(grid: Any) -> tuple[Any, ...]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        return ("invalid", tuple(facts["errors"]))
    return (
        facts["height"],
        facts["width"],
        facts["n_blobs"],
        facts["sizes_sorted"],
        facts["input_size_order"],
        facts["palette_kind"],
        facts["max_bbox_width"],
        tuple(facts["bbox_widths"]),
    )


# ---------------------------------------------------------------------------
# Named rivals, witnesses, and lesson-level identifiability
# ---------------------------------------------------------------------------


def _rival_input_scan_order(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    return _stack_components(comps, order=list(range(len(comps))))


def _rival_smallest_first(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["size"])
    return _stack_components(comps, order=order)


def _rival_bbox_area_desc(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["bbox_area"], reverse=True)
    return _stack_components(comps, order=order)


def _rival_color_desc(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["color"], reverse=True)
    return _stack_components(comps, order=order)


def _rival_no_gap(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["size"], reverse=True)
    return _stack_components(comps, order=order, gap=0)


def _rival_center_align(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["size"], reverse=True)
    return _stack_components(comps, order=order, alignment="center")


def _rival_fixed_width_3(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["size"], reverse=True)
    return _stack_components(comps, order=order, forced_width=3)


def _rival_largest_three_only(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    order = sorted(range(len(comps)), key=lambda i: comps[i]["size"], reverse=True)[:3]
    return _stack_components(comps, order=order)


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "input_scan_order": _rival_input_scan_order,
    "smallest_first": _rival_smallest_first,
    "bbox_area_desc": _rival_bbox_area_desc,
    "color_desc": _rival_color_desc,
    "omit_gap_rows": _rival_no_gap,
    "center_align": _rival_center_align,
    "fixed_output_width_3": _rival_fixed_width_3,
    "largest_three_only": _rival_largest_three_only,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _grids_equal(left: Any, right: Any) -> bool:
    try:
        return [list(row) for row in left] == [list(row) for row in right]
    except TypeError:
        return False


def _rival_disagrees(name: str, grid: Any) -> bool:
    return not _grids_equal(rule_mirror(grid), SEMANTIC_RIVALS[name](grid))


def _witness_scan_order_conflict(grid) -> bool:
    return _rival_disagrees("input_scan_order", grid)


def _witness_bbox_area_conflict(grid) -> bool:
    return _rival_disagrees("bbox_area_desc", grid)


def _witness_color_order_conflict(grid) -> bool:
    return _rival_disagrees("color_desc", grid)


def _witness_left_alignment(grid) -> bool:
    return _rival_disagrees("center_align", grid)


def _witness_width_two(grid) -> bool:
    facts = semantic_observables(grid)
    return facts.get("max_bbox_width") == 2 and _rival_disagrees("fixed_output_width_3", grid)


def _witness_four_objects(grid) -> bool:
    facts = semantic_observables(grid)
    return facts.get("n_blobs") == 4 and _rival_disagrees("largest_three_only", grid)


def _witness_gap_rows(grid) -> bool:
    return _rival_disagrees("omit_gap_rows", grid)


SEMANTIC_WITNESSES = {
    "input_order_differs_from_size_order": _witness_scan_order_conflict,
    "bbox_area_sort_conflict": _witness_bbox_area_conflict,
    "color_sort_conflict": _witness_color_order_conflict,
    "left_alignment_is_visible": _witness_left_alignment,
    "two_column_output": _witness_width_two,
    "four_object_scene": _witness_four_objects,
    "one_row_gaps_are_visible": _witness_gap_rows,
}
WITNESS_RIVALS = {
    "input_order_differs_from_size_order": ["input_scan_order"],
    "bbox_area_sort_conflict": ["bbox_area_desc"],
    "color_sort_conflict": ["color_desc"],
    "left_alignment_is_visible": ["center_align"],
    "two_column_output": ["fixed_output_width_3"],
    "four_object_scene": ["largest_three_only"],
    "one_row_gaps_are_visible": ["omit_gap_rows"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a named wrong rule survives every demo."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                _grids_equal(rival(pair["input"]), pair["output"])
                for pair in demos
            )
            if not fits_demos:
                continue
            if _grids_equal(rival(query["input"]), query["output"]):
                reasons.append(f"competitor {name!r} survives demos and query")
            else:
                reasons.append(
                    f"competitor {name!r} fits every demo but disagrees on query"
                )
        except Exception as exc:
            reasons.append(f"competitor {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
