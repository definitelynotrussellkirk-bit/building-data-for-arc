"""Semantic generator for ``677dcb71e2be`` — component-size bars.

The authoritative rule finds every non-zero 4-connected component, sorts the
components by occupied cell count from largest to smallest, and emits one row.
Each component becomes a solid bar of its own color and occupied-cell length;
neighboring bars are separated by one zero.

The four-profile sample-index schedule is intentionally pedagogical. Every four
consecutive demonstrations include a canonical-scale anchor, a scan/color-order
conflict, a bounding-box-area conflict, and a four-component scene. Placements
range across the full legal canvas and color assignments vary independently of
size rank, closing two retained curriculum shortcuts from the previous version.
"""
from __future__ import annotations

from collections import deque
from itertools import permutations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "677dcb71e2be"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a1028386df20"  # sha256[:12] of whitespace-normalized canonical rule
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.15

SUMMARY = (
    "A 10..18 by 10..18 zero-background grid contains three or four "
    "diagonally separated monochrome components with distinct colors and "
    "distinct occupied-cell counts. Sort components by occupied-cell count "
    "descending and emit one row of same-color bars with those lengths, "
    "separated by one zero."
)

INVARIANTS = [
    "three or four 4-connected non-zero components",
    "component colors and occupied-cell counts are pairwise distinct",
    "different components do not touch, including diagonally",
    "every component fits inside a 4x3 bounding box",
    "bar order is descending occupied-cell count, not scan, color, or bbox area",
]

COUNTER_HYPOTHESES = [
    "emit components in input scan order",
    "sort smallest first",
    "sort by bounding-box area instead of occupied-cell count",
    "sort by color instead of occupied-cell count",
    "use bounding-box area as each bar length",
    "omit the zero separators",
    "always keep only the largest three components",
    "memorize canonical dimensions, positions, palettes, or shapes",
    "inspect only the old four corner slots",
    "use the old fixed palette-rank permutation without comparing sizes",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical 10..12 or generalized 10..18",
        "valid": "10..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical 10..13 or generalized 10..18",
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
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)
_SIZE_PATTERNS = ("consecutive", "spread")
_INPUT_ORDERS = ("ascending", "descending", "zigzag")
_PALETTE_KINDS = ("low", "high", "mixed")

SCHEDULE_PROFILES = (
    "canonical_anchor",
    "scan_and_color_conflict",
    "bbox_area_conflict",
    "four_component_generalization",
)

_CANONICAL_DIMENSIONS = {(10, 10), (12, 12), (10, 13), (11, 12), (12, 13)}
_CANONICAL_SIZE_SETS = {
    (2, 4, 5),
    (2, 3, 6),
    (3, 4, 5),
    (2, 5, 6),
}

# Normalized 4-connected shapes, all fitting inside a 4x3 box. Multiple bbox
# areas for the same occupied-cell count let the curriculum explicitly separate
# true component area from bounding-box area.
_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    2: (
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
    ),
    3: (
        ((0, 0), (0, 1), (1, 0)),
        ((0, 0), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (0, 2)),
    ),
    4: (
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (3, 0)),
    ),
    5: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (3, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (1, 0), (2, 0), (3, 0), (2, 1), (3, 1)),
    ),
    7: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (3, 1), (3, 2)),
    ),
    8: (
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2)),
    ),
}

_CONSECUTIVE_SIZE_SETS = {
    3: ((2, 3, 4), (3, 4, 5), (4, 5, 6)),
    4: ((2, 3, 4, 5), (3, 4, 5, 6), (4, 5, 6, 7)),
}
_SPREAD_SIZE_SETS = {
    3: ((2, 4, 5), (2, 3, 6), (2, 5, 6), (2, 5, 7), (3, 5, 8)),
    4: ((2, 4, 6, 8), (2, 3, 6, 8), (3, 5, 7, 8)),
}

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_public_inputs(seed: Any, sample_index: Any, difficulty: Any) -> None:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise TypeError("seed must be an integer in 0..2^63-1 (bool is forbidden)")
    if type(sample_index) is not int or sample_index < 0:
        raise TypeError("sample_index must be a nonnegative integer (bool is forbidden)")
    if difficulty not in {None, "easy", "medium", "hard"}:
        raise ValueError("difficulty must be one of None, easy, medium, hard")


def _band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be one of None, easy, medium, hard")
    return difficulty


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    _validate_public_inputs(seed, sample_index, difficulty)
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _scheduled_defaults(seed: int, sample_index: int, band: str) -> dict[str, Any]:
    profile = schedule_profile(seed, sample_index, band)
    rng = stable_rng(seed, f"{TASK_ID}|schedule|{sample_index}|{band}", VERSION)
    canonical_dims = {
        "easy": (10, 10),
        "medium": (11, 12),
        "hard": (12, 13),
    }
    if profile == "canonical_anchor":
        h, w = canonical_dims[band]
        return {
            "grid_h": h,
            "grid_w": w,
            "n_blobs": 3,
            "size_pattern": "consecutive" if band == "medium" else "spread",
            "input_size_order": "ascending",
            "palette_kind": "mixed",
        }

    ranges = {
        "easy": ((10, 12), (10, 13)),
        "medium": ((12, 15), (12, 16)),
        "hard": ((15, 18), (15, 18)),
    }
    (h_lo, h_hi), (w_lo, w_hi) = ranges[band]
    h = rng.randint(h_lo, h_hi)
    w = rng.randint(w_lo, w_hi)
    if profile == "scan_and_color_conflict":
        return {
            "grid_h": h,
            "grid_w": w,
            "n_blobs": 3,
            "size_pattern": "consecutive",
            "input_size_order": "ascending",
            "palette_kind": "low",
        }
    if profile == "bbox_area_conflict":
        return {
            "grid_h": h,
            "grid_w": w,
            "n_blobs": 3,
            "size_pattern": "spread",
            "input_size_order": "descending",
            "palette_kind": "high",
        }
    return {
        "grid_h": h,
        "grid_w": w,
        "n_blobs": 4,
        "size_pattern": "spread",
        "input_size_order": "zigzag",
        "palette_kind": "mixed",
    }


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError("unknown override axis/axes: " + ", ".join(unknown))


def _normalize_shape(cells: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform_shape(
    cells: tuple[tuple[int, int], ...], rng
) -> tuple[tuple[int, int], ...]:
    transformed = list(cells)
    if rng.choice((False, True)):
        max_c = max(c for _, c in transformed)
        transformed = [(r, max_c - c) for r, c in transformed]
    if rng.choice((False, True)):
        max_r = max(r for r, _ in transformed)
        transformed = [(max_r - r, c) for r, c in transformed]
    return _normalize_shape(tuple(transformed))


def _bbox_dims(cells: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _bbox_area(cells: tuple[tuple[int, int], ...]) -> int:
    h, w = _bbox_dims(cells)
    return h * w


def _select_sizes(
    pattern: str,
    n_blobs: int,
    profile: str,
    band: str,
    rng,
) -> tuple[int, ...]:
    if profile == "canonical_anchor" and n_blobs == 3:
        canonical = {
            "easy": (2, 4, 5),
            "medium": (3, 4, 5),
            "hard": (2, 5, 6),
        }[band]
        if _classify_size_pattern(canonical) == pattern:
            return canonical
    if profile == "bbox_area_conflict" and pattern == "spread" and n_blobs == 3:
        return (2, 5, 7)
    choices = (
        _CONSECUTIVE_SIZE_SETS[n_blobs]
        if pattern == "consecutive"
        else _SPREAD_SIZE_SETS[n_blobs]
    )
    return tuple(rng.choice(choices))


def _order_sizes(sizes: tuple[int, ...], order: str) -> tuple[int, ...]:
    ordered = tuple(sorted(sizes))
    if order == "ascending":
        return ordered
    if order == "descending":
        return tuple(reversed(ordered))
    if len(ordered) == 3:
        return (ordered[2], ordered[0], ordered[1])
    return (ordered[3], ordered[0], ordered[2], ordered[1])


def _palette(kind: str, n: int, rng) -> tuple[int, ...]:
    if kind == "low":
        selected = sorted(rng.sample((1, 2, 3, 4), n))
    elif kind == "high":
        selected = sorted(rng.sample((6, 7, 8, 9), n))
    elif n == 3:
        selected = sorted(
            rng.sample((1, 2, 3, 4), 1) + rng.sample((6, 7, 8, 9), 2)
        )
    else:
        selected = sorted(
            rng.sample((1, 2, 3, 4), 2) + rng.sample((6, 7, 8, 9), 2)
        )
    return tuple(selected)


def _assign_colors(
    sizes_in_slots: tuple[int, ...], palette: tuple[int, ...], rng
) -> tuple[int, ...]:
    """Assign a palette independently of size rank while killing color-order rivals.

    Version 2 used one fixed rank permutation, so a learner could count each
    color and emit a memorized palette-rank sequence without comparing sizes.
    Choose among many non-monotone permutations and explicitly exclude that old
    mapping as well as ascending/descending color order.
    """
    n = len(palette)
    old = (1, 2, 0) if n == 3 else (1, 3, 0, 2)
    ascending = tuple(range(n))
    descending = tuple(reversed(ascending))
    options = [
        order
        for order in permutations(range(n))
        if order not in {old, ascending, descending}
    ]
    rank_colors = tuple(palette[index] for index in rng.choice(options))
    size_rank = sorted(
        range(len(sizes_in_slots)), key=lambda i: sizes_in_slots[i], reverse=True
    )
    by_slot = [0] * len(sizes_in_slots)
    for rank, slot_index in enumerate(size_rank):
        by_slot[slot_index] = rank_colors[rank]
    return tuple(by_slot)


def _old_corner_slot(origin: tuple[int, int], h: int, w: int) -> bool:
    top, left = origin
    return top in {0, 1, h - 4} and left in {0, 1, w - 4, w - 3}


def _shape_cells(
    origin: tuple[int, int], shape: tuple[tuple[int, int], ...]
) -> set[tuple[int, int]]:
    top, left = origin
    return {(top + r, left + c) for r, c in shape}


def _separated(cells: set[tuple[int, int]], occupied: set[tuple[int, int]]) -> bool:
    return all(
        (r + dr, c + dc) not in occupied
        for r, c in cells
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
    )


def _place_shapes(
    h: int,
    w: int,
    shapes_in_slots: tuple[tuple[tuple[int, int], ...], ...],
    rng,
) -> tuple[tuple[int, int], ...]:
    """Place shapes across the full canvas in exact scan-order.

    Recursive construction is bounded by the small 3/4-object grammar.  The
    second object is required to leave the old four-slot support, and the final
    layout spans both axes, so location is not a hidden proxy for inclusion.
    """
    candidate_lists: list[list[tuple[int, int]]] = []
    for shape in shapes_in_slots:
        sh, sw = _bbox_dims(shape)
        candidates = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    chosen: list[tuple[int, int]] = []
    occupied: set[tuple[int, int]] = set()
    node_budget = 200_000
    nodes = 0

    def search(index: int) -> bool:
        nonlocal nodes
        nodes += 1
        if nodes > node_budget:
            return False
        if index == len(shapes_in_slots):
            rows = [r for r, _ in chosen]
            cols = [c for _, c in chosen]
            return (
                max(rows) - min(rows) >= max(2, h // 3)
                and max(cols) - min(cols) >= max(2, w // 3)
            )
        previous = chosen[-1] if chosen else None
        shape = shapes_in_slots[index]
        for origin in candidate_lists[index]:
            if previous is not None and origin <= previous:
                continue
            if index == 1 and _old_corner_slot(origin, h, w):
                continue
            cells = _shape_cells(origin, shape)
            if not _separated(cells, occupied):
                continue
            chosen.append(origin)
            occupied.update(cells)
            if search(index + 1):
                return True
            occupied.difference_update(cells)
            chosen.pop()
        return False

    if not search(0):
        raise ValueError(f"unable to place {len(shapes_in_slots)} separated shapes in {h}x{w}")
    return tuple(chosen)


def _choose_shapes(
    sizes: tuple[int, ...], profile: str, rng
) -> dict[int, tuple[tuple[int, int], ...]]:
    chosen: dict[int, tuple[tuple[int, int], ...]] = {}
    for size in sizes:
        chosen[size] = rng.choice(_SHAPES[size])

    if profile == "bbox_area_conflict" and len(sizes) >= 2:
        largest, second = sorted(sizes, reverse=True)[:2]
        chosen[largest] = min(_SHAPES[largest], key=lambda cells: (_bbox_area(cells), cells))
        chosen[second] = max(_SHAPES[second], key=lambda cells: (_bbox_area(cells), cells))

    # Keep at least one non-rectangular/bbox-expanded object in ordinary scenes
    # so "bar length = bbox area" is visibly wrong.
    if all(_bbox_area(shape) == size for size, shape in chosen.items()):
        candidate = min(sizes)
        expanded = max(_SHAPES[candidate], key=lambda cells: _bbox_area(cells))
        if _bbox_area(expanded) > candidate:
            chosen[candidate] = expanded

    return {size: _transform_shape(shape, rng) for size, shape in chosen.items()}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_public_inputs(seed, sample_index, difficulty)
    band = _band(difficulty)
    _validate_overrides(overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    defaults = _scheduled_defaults(seed, sample_index, band)
    effective_overrides = {**defaults, **overrides}
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=effective_overrides,
    )

    h = ctx.draw_int_strict("grid_h", 10, 18)
    w = ctx.draw_int_strict("grid_w", 10, 18)
    n_blobs = ctx.draw_int_strict("n_blobs", 3, 4)
    size_pattern = ctx.draw_choice("size_pattern", _SIZE_PATTERNS)
    input_order = ctx.draw_choice("input_size_order", _INPUT_ORDERS)
    palette_kind = ctx.draw_choice("palette_kind", _PALETTE_KINDS)

    layout_rng = ctx.draw_rng("layout")
    sizes = _select_sizes(
        size_pattern, n_blobs, profile, band, ctx.draw_rng("size_set")
    )
    sizes_in_slots = _order_sizes(sizes, input_order)
    palette_rng = ctx.draw_rng("palette")
    colors_in_slots = _assign_colors(
        sizes_in_slots, _palette(palette_kind, n_blobs, palette_rng), palette_rng
    )
    shapes = _choose_shapes(sizes, profile, ctx.draw_rng("shapes"))
    shapes_in_slots = tuple(shapes[size] for size in sizes_in_slots)
    slots = _place_shapes(h, w, shapes_in_slots, layout_rng)

    grid = full_grid(h, w, 0)
    for (top, left), size, color, shape in zip(
        slots, sizes_in_slots, colors_in_slots, shapes_in_slots
    ):
        for rr, cc in shape:
            r, c = top + rr, left + cc
            if not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0:
                raise AssertionError("slot layout overlap or out-of-bounds paint")
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
# Structural analysis and Python mirrors (Racket remains output authority)
# ---------------------------------------------------------------------------


def _coerce_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty sequence of rows"]
    rows: list[list[int]] = []
    width: int | None = None
    for row_index, row in enumerate(grid):
        if isinstance(row, str):
            try:
                values = [int(ch) for ch in row]
            except ValueError:
                return None, [f"row {row_index} is not a digit grid"]
        elif isinstance(row, (list, tuple)):
            values = list(row)
        else:
            return None, [f"row {row_index} is not a sequence"]
        if width is None:
            width = len(values)
        if not values or len(values) != width:
            return None, ["grid must be rectangular and nonempty"]
        if any(
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 9
            for value in values
        ):
            return None, [f"row {row_index} contains a non-ARC color"]
        rows.append(values)
    return rows, []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0
    }
    result: list[dict[str, Any]] = []
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        remaining.remove(start)
        queue = deque([start])
        cells = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining and grid[nxt[0]][nxt[1]] == color:
                    remaining.remove(nxt)
                    queue.append(nxt)
                    cells.append(nxt)
        r1 = min(r for r, _ in cells)
        c1 = min(c for _, c in cells)
        r2 = max(r for r, _ in cells)
        c2 = max(c for _, c in cells)
        result.append(
            {
                "cells": tuple(sorted(cells)),
                "color": color,
                "size": len(cells),
                "bbox": (r1, c1, r2, c2),
                "height": r2 - r1 + 1,
                "width": c2 - c1 + 1,
                "bbox_area": (r2 - r1 + 1) * (c2 - c1 + 1),
            }
        )
    return sorted(result, key=lambda comp: (comp["bbox"][0], comp["bbox"][1]))


def _classify_size_pattern(sizes: tuple[int, ...]) -> str | None:
    ordered = tuple(sorted(sizes))
    return "consecutive" if all(b - a == 1 for a, b in zip(ordered, ordered[1:])) else "spread"


def _classify_input_order(sizes: tuple[int, ...]) -> str | None:
    ordered = tuple(sorted(sizes))
    for name in _INPUT_ORDERS:
        if sizes == _order_sizes(ordered, name):
            return name
    return None


def _classify_palette(colors: tuple[int, ...]) -> str | None:
    if all(1 <= color <= 4 for color in colors):
        return "low"
    if all(6 <= color <= 9 for color in colors):
        return "high"
    if all(color in {1, 2, 3, 4, 6, 7, 8, 9} for color in colors):
        return "mixed"
    return None


def semantic_observables(grid: Any) -> dict[str, Any]:
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        return {"errors": errors}
    comps = _components(values)
    sizes = tuple(comp["size"] for comp in comps)
    colors = tuple(comp["color"] for comp in comps)
    return {
        "errors": [],
        "height": len(values),
        "width": len(values[0]),
        "components": comps,
        "n_blobs": len(comps),
        "sizes_scan_order": sizes,
        "sizes_sorted": tuple(sorted(sizes)),
        "colors_scan_order": colors,
        "palette_size": len(set(colors)) + 1,
        "size_pattern": _classify_size_pattern(sizes),
        "input_size_order": _classify_input_order(sizes),
        "palette_kind": _classify_palette(colors),
        "bbox_areas_scan_order": tuple(comp["bbox_area"] for comp in comps),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept authority-valid inputs and reject malformed/rule-hiding scenes."""
    del difficulty, meta
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors

    h, w = facts["height"], facts["width"]
    if not 10 <= h <= 18 or not 10 <= w <= 18:
        errors.append(f"supported authority envelope is 10..18 square/rectangular; found {h}x{w}")
    comps = facts["components"]
    if not 3 <= len(comps) <= 4:
        errors.append(f"expected 3-4 components, found {len(comps)}")

    colors = [comp["color"] for comp in comps]
    if len(colors) != len(set(colors)):
        errors.append("component colors must be pairwise distinct")
    sizes = [comp["size"] for comp in comps]
    if len(sizes) != len(set(sizes)):
        errors.append(f"component occupied-cell counts must be distinct, found {sizes}")
    if any(not 2 <= size <= 8 for size in sizes):
        errors.append(f"component occupied-cell counts must lie in 2..8, found {sizes}")

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
    # Curriculum-only axes such as scan order and palette band are checked by
    # observe_overrides/semantic witnesses. Authority-valid canonical scenes
    # may use any component order and any nonzero ARC colors.
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    facts = semantic_observables(grid)
    if (facts["height"], facts["width"]) not in _CANONICAL_DIMENSIONS:
        reasons.append("dimensions are outside canonical profiles")
    if facts["n_blobs"] != 3:
        reasons.append("canonical scenes contain exactly three components")
    if facts["sizes_sorted"] not in _CANONICAL_SIZE_SETS:
        reasons.append("component-size multiset is not canonical")
    if facts["palette_size"] != 4:
        reasons.append("canonical inputs use background plus three component colors")
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
        facts["sizes_scan_order"],
        facts["colors_scan_order"],
        facts["bbox_areas_scan_order"],
    )


def _bars_from_components(
    comps: list[dict[str, Any]], *, separator: bool = True, use_bbox_length: bool = False
) -> list[list[int]]:
    row: list[int] = []
    for index, comp in enumerate(comps):
        if index and separator:
            row.append(0)
        length = comp["bbox_area"] if use_bbox_length else comp["size"]
        row.extend([comp["color"]] * length)
    return [row]


def _official_output(grid: Any) -> list[list[int]]:
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = sorted(_components(values), key=lambda comp: (-comp["size"], comp["color"]))
    return _bars_from_components(comps)


def _rival_input_scan_order(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    return _bars_from_components(_components(values))


def _rival_smallest_first(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = sorted(_components(values), key=lambda comp: (comp["size"], comp["color"]))
    return _bars_from_components(comps)


def _rival_bbox_area_desc(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = sorted(
        _components(values), key=lambda comp: (-comp["bbox_area"], comp["color"])
    )
    return _bars_from_components(comps)


def _rival_color_asc(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    return _bars_from_components(sorted(_components(values), key=lambda comp: comp["color"]))


def _rival_color_desc(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    return _bars_from_components(
        sorted(_components(values), key=lambda comp: comp["color"], reverse=True)
    )


def _rival_bbox_lengths(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = sorted(_components(values), key=lambda comp: (-comp["size"], comp["color"]))
    return _bars_from_components(comps, use_bbox_length=True)


def _rival_no_separators(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = sorted(_components(values), key=lambda comp: (-comp["size"], comp["color"]))
    return _bars_from_components(comps, separator=False)


def _rival_largest_three_only(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = sorted(_components(values), key=lambda comp: (-comp["size"], comp["color"]))[:3]
    return _bars_from_components(comps)


def _rival_old_palette_rank(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    comps = _components(values)
    colors = sorted(comp["color"] for comp in comps)
    ranks = (1, 2, 0) if len(colors) == 3 else (1, 3, 0, 2)
    by_color = {comp["color"]: comp for comp in comps}
    return _bars_from_components([by_color[colors[index]] for index in ranks])


def _rival_old_corner_slots(grid):
    values, errors = _coerce_grid(grid)
    if errors or values is None:
        raise ValueError("invalid grid")
    h, w = len(values), len(values[0])
    comps = [
        comp
        for comp in _components(values)
        if _old_corner_slot((comp["bbox"][0], comp["bbox"][1]), h, w)
    ]
    return _bars_from_components(
        sorted(comps, key=lambda comp: (-comp["size"], comp["color"]))
    )


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "input_scan_order": _rival_input_scan_order,
    "smallest_first": _rival_smallest_first,
    "bbox_area_desc": _rival_bbox_area_desc,
    "color_asc": _rival_color_asc,
    "color_desc": _rival_color_desc,
    "bbox_area_lengths": _rival_bbox_lengths,
    "omit_separators": _rival_no_separators,
    "largest_three_only": _rival_largest_three_only,
    "old_fixed_palette_rank": _rival_old_palette_rank,
    "old_corner_slots_only": _rival_old_corner_slots,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _grids_equal(left: Any, right: Any) -> bool:
    left_grid, left_errors = _coerce_grid(left)
    right_grid, right_errors = _coerce_grid(right)
    return not left_errors and not right_errors and left_grid == right_grid


def _rival_disagrees(name: str, grid: Any) -> bool:
    return not _grids_equal(SEMANTIC_RIVALS[name](grid), _official_output(grid))


def _witness_scan_order(grid) -> bool:
    return _rival_disagrees("input_scan_order", grid)


def _witness_bbox_order(grid) -> bool:
    return _rival_disagrees("bbox_area_desc", grid)


def _witness_color_asc(grid) -> bool:
    return _rival_disagrees("color_asc", grid)


def _witness_color_desc(grid) -> bool:
    return _rival_disagrees("color_desc", grid)


def _witness_bbox_lengths(grid) -> bool:
    return _rival_disagrees("bbox_area_lengths", grid)


def _witness_separators(grid) -> bool:
    return _rival_disagrees("omit_separators", grid)


def _witness_four_components(grid) -> bool:
    facts = semantic_observables(grid)
    return facts.get("n_blobs") == 4 and _rival_disagrees("largest_three_only", grid)


SEMANTIC_WITNESSES = {
    "scan_order_differs_from_size_order": _witness_scan_order,
    "bbox_area_order_differs_from_cell_area": _witness_bbox_order,
    "ascending_color_order_is_wrong": _witness_color_asc,
    "descending_color_order_is_wrong": _witness_color_desc,
    "bbox_area_is_not_bar_length": _witness_bbox_lengths,
    "zero_separators_are_visible": _witness_separators,
    "four_component_scene": _witness_four_components,
}
WITNESS_RIVALS = {
    "scan_order_differs_from_size_order": ["input_scan_order"],
    "bbox_area_order_differs_from_cell_area": ["bbox_area_desc"],
    "ascending_color_order_is_wrong": ["color_asc"],
    "descending_color_order_is_wrong": ["color_desc"],
    "bbox_area_is_not_bar_length": ["bbox_area_lengths"],
    "zero_separators_are_visible": ["omit_separators"],
    "four_component_scene": ["largest_three_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a materialized lesson whenever a named wrong rule survives."""
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
