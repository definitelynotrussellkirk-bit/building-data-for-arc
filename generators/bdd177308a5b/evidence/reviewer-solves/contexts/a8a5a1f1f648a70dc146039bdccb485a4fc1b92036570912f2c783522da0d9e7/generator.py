"""Generator for ARC task 63613498 / content hash bdd177308a5b.

A colored template occupies part of the top-left 3x3 chamber.  A gray
(color-5) L-frame forms the chamber's right and bottom edges.  Several
single-color objects appear outside the chamber; exactly one has the same
translation-normalized shape *and orientation* as the template.  The oracle
recolors that one object gray and leaves the cue, template, and near-miss
objects unchanged.

The distribution deliberately includes same-size rotated/reflected near
misses, a different-size distractor, and target locations in multiple board
zones.  These witnesses refute count-only, dihedral-invariant, fixed-position,
and "recolor the nearest/modal object" shortcuts.
"""
from __future__ import annotations

from collections.abc import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bdd177308a5b"
TASK_ID = "bdd177308a5b"
VERSION = "3.0.0"  # canonical cue/orientation grammar + honest axes + structural checker
RULE_HASH = "5b8904c8dace"

SUMMARY = (
    "A non-{0,5} template lies in the top-left 3x3 chamber, whose bottom "
    "row and right column form a seven-cell gray L-frame. Outside the cue "
    "are 3..5 colored objects. Exactly one object has the template's exact "
    "translation-normalized shape and orientation; recolor only that object "
    "to gray (5). Rotated/reflected and different-size objects are decoys."
)

INVARIANTS = [
    "background is modal color 0 and the input palette is within 0..9",
    "the gray cue is exactly row 3, columns 0..3 plus column 3, rows 0..3",
    "the template is one connected 3..5-cell color object inside rows/cols 0..2",
    "there are 3..5 outside objects and exactly one exact normalized-shape match",
    "at least one outside distractor is a non-identical dihedral near miss",
    "the matching target may occur top-right, bottom-left, or bottom-right",
]

DEGENERATE_TEXTURES: tuple[str, ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()

TARGET_ZONES = ("top_right", "bottom_left", "bottom_right")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-linked keyed draw 10..14",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-linked keyed draw 10..14",
        "valid": "10..14",
    },
    "template_size": {
        "type": "int",
        "default": "difficulty-linked keyed draw 3..5",
        "valid": "3..5",
    },
    "distractor_count": {
        "type": "int",
        "default": "difficulty-linked keyed draw 2..4",
        "valid": "2..4",
    },
    "target_zone": {
        "type": "str",
        "default": "keyed choice across all outside zones",
        "valid": "top_right|bottom_left|bottom_right",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CUE_CELLS = frozenset(
    {(3, c) for c in range(4)} | {(r, 3) for r in range(4)}
)

Shape = tuple[tuple[int, int], ...]


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    pts = tuple(cells)
    if not pts:
        return ()
    r0 = min(r for r, _ in pts)
    c0 = min(c for _, c in pts)
    return tuple(sorted((r - r0, c - c0) for r, c in pts))


def _dihedral(shape: Shape) -> tuple[Shape, ...]:
    """All unique rotations/reflections, sorted for hash-seed independence."""
    variants: set[Shape] = set()
    for reflected in (False, True):
        for turns in range(4):
            transformed = []
            for r, c in shape:
                x, y = (r, -c) if reflected else (r, c)
                for _ in range(turns):
                    x, y = y, -x
                transformed.append((x, y))
            variants.add(_normalize(transformed))
    return tuple(sorted(variants))


def _bbox_size(shape: Shape) -> tuple[int, int]:
    return (
        max(r for r, _ in shape) + 1,
        max(c for _, c in shape) + 1,
    )


# Canonical template families: L triomino, T/L tetrominoes, and the five-cell
# staircase.  Orientation is preserved by the task, so each dihedral variant is
# a separate lawful template value.
_L3 = ((0, 0), (1, 0), (1, 1))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_L4 = ((0, 0), (1, 0), (2, 0), (2, 1))
_ZIG5 = ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2))

TEMPLATE_SHAPES_BY_SIZE: dict[int, tuple[Shape, ...]] = {
    3: _dihedral(_L3),
    4: tuple(sorted(set(_dihedral(_T4)) | set(_dihedral(_L4)))),
    5: _dihedral(_ZIG5),
}

# Extra decoy-only families witnessed by the canonical examples: a 3-line,
# square/skew tetrominoes, and compact five-cell alternatives.  They make size
# and bounding-box equality insufficient while never duplicating the target.
_DECOY_BASES = (
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)),
)
_ALL_DECOY_SHAPES = tuple(
    sorted(
        set().union(
            *(
                set(shapes)
                for shapes in TEMPLATE_SHAPES_BY_SIZE.values()
            ),
            *(_dihedral(_normalize(base)) for base in _DECOY_BASES),
        )
    )
)


def _connected4(cells: Iterable[tuple[int, int]]) -> bool:
    pts = set(cells)
    if not pts:
        return False
    seen = {next(iter(pts))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in _DIRS4:
            nxt = (r + dr, c + dc)
            if nxt in pts and nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen == pts


def _components(grid: list[list[int]]) -> list[dict[str, object]]:
    """4-connected, single-color components excluding background and gray."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 5) or (r, c) in seen:
                continue
            cells: list[tuple[int, int]] = []
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            cells_t = tuple(sorted(cells))
            out.append(
                {
                    "color": color,
                    "cells": cells_t,
                    "norm": _normalize(cells_t),
                    "rmin": min(rr for rr, _ in cells_t),
                    "cmin": min(cc for _, cc in cells_t),
                }
            )
    return out


def _target_zone(cells: Iterable[tuple[int, int]]) -> str | None:
    pts = tuple(cells)
    rmin = min(r for r, _ in pts)
    cmin = min(c for _, c in pts)
    if rmin <= 3 and cmin >= 4:
        return "top_right"
    if rmin >= 4 and cmin <= 3:
        return "bottom_left"
    if rmin >= 4 and cmin >= 4:
        return "bottom_right"
    return None


def _template_cells(grid: list[list[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (r, c)
        for r in range(3)
        for c in range(3)
        if grid[r][c] not in (0, 5)
    )


def _semantic_parts(grid: list[list[int]]) -> tuple[
    Shape,
    list[dict[str, object]],
    list[dict[str, object]],
]:
    template_norm = _normalize(_template_cells(grid))
    outside = [
        obj
        for obj in _components(grid)
        if not any(r < 3 and c < 3 for r, c in obj["cells"])
    ]
    matches = [obj for obj in outside if obj["norm"] == template_norm]
    return template_norm, outside, matches


def observe_overrides(grid: list[list[int]]) -> dict[str, int | str]:
    """Recover every declared exact axis from the returned grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("cannot observe axes from an empty or ragged grid")
    template_norm, outside, matches = _semantic_parts(grid)
    if not template_norm or len(matches) != 1:
        raise ValueError("grid does not contain exactly one observable target")
    zone = _target_zone(matches[0]["cells"])
    if zone is None:
        raise ValueError("matching target is not in a declared zone")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "template_size": len(template_norm),
        "distractor_count": len(outside) - 1,
        "target_zone": zone,
    }


def self_check(
    grid: list[list[int]], *, difficulty=None, meta=None
) -> list[str]:
    """Validate the input grammar, including the exact matching relation."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-grid input"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs: list[str] = []

    if not (10 <= h <= 14 and 10 <= w <= 14):
        errs.append(f"grid dimensions must be within 10..14, got {h}x{w}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errs.append("grid contains a non-integer or color outside 0..9")
        return errs

    actual_fives = {
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 5
    }
    if actual_fives != _CUE_CELLS:
        missing = sorted(_CUE_CELLS - actual_fives)
        extra = sorted(actual_fives - _CUE_CELLS)
        errs.append(
            "gray cue must be exactly the seven-cell bottom/right L-frame "
            f"(missing={missing[:4]}, extra={extra[:4]})"
        )

    zero_count = sum(value == 0 for row in grid for value in row)
    if zero_count * 2 <= h * w:
        errs.append("background color 0 must be strictly modal")

    template_cells = _template_cells(grid)
    template_norm = _normalize(template_cells)
    if not (3 <= len(template_cells) <= 5):
        errs.append(
            f"template must contain 3..5 cells in the top-left 3x3, got {len(template_cells)}"
        )
    if template_cells:
        template_colors = {grid[r][c] for r, c in template_cells}
        if len(template_colors) != 1:
            errs.append("template cells must have one color")
        if not _connected4(template_cells):
            errs.append("template must be 4-connected")
        allowed = TEMPLATE_SHAPES_BY_SIZE.get(len(template_cells), ())
        if template_norm not in allowed:
            errs.append(f"unsupported template shape {template_norm}")

    components = _components(grid)
    template_components = [
        obj
        for obj in components
        if any(r < 3 and c < 3 for r, c in obj["cells"])
    ]
    if len(template_components) != 1:
        errs.append(
            f"expected exactly one colored component in the template chamber, got {len(template_components)}"
        )
    elif set(template_components[0]["cells"]) != set(template_cells):
        errs.append("template chamber contains a component crossing its 3x3 boundary")

    outside = [obj for obj in components if obj not in template_components]
    if not (3 <= len(outside) <= 5):
        errs.append(f"expected 3..5 outside objects, got {len(outside)}")
    bad_sizes = [len(obj["cells"]) for obj in outside if not 3 <= len(obj["cells"]) <= 5]
    if bad_sizes:
        errs.append(f"outside objects must contain 3..5 cells, got sizes {bad_sizes}")
    bad_zones = [obj["cells"][0] for obj in outside if _target_zone(obj["cells"]) is None]
    if bad_zones:
        errs.append(f"outside object(s) cross the cue-only quadrant boundary: {bad_zones[:3]}")

    matches = [obj for obj in outside if obj["norm"] == template_norm]
    if len(matches) != 1:
        errs.append(f"expected exactly one exact normalized-shape match, got {len(matches)}")

    distractors = [obj for obj in outside if obj not in matches]
    if not (2 <= len(distractors) <= 4):
        errs.append(f"expected 2..4 distractors, got {len(distractors)}")
    if template_norm:
        same_size = [
            obj for obj in distractors if len(obj["cells"]) == len(template_norm)
        ]
        if not same_size:
            errs.append("missing a same-size non-matching distractor")

    return errs


def _paint(
    grid: list[list[int]], shape: Shape, r0: int, c0: int, color: int
) -> None:
    for dr, dc in shape:
        grid[r0 + dr][c0 + dc] = color


def _anchors_for_zone(
    shape: Shape, h: int, w: int, zone: str
) -> list[tuple[int, int]]:
    sh, sw = _bbox_size(shape)
    if zone == "top_right":
        r_values = range(0, min(3, h - sh) + 1)
        c_values = range(4, w - sw + 1)
    elif zone == "bottom_left":
        r_values = range(4, h - sh + 1)
        c_values = range(0, min(3, w - sw) + 1)
    elif zone == "bottom_right":
        r_values = range(4, h - sh + 1)
        c_values = range(4, w - sw + 1)
    else:
        raise ValueError(f"unknown target zone {zone!r}")
    return [(r, c) for r in r_values for c in c_values]


def _choose_distractors(ctx, template: Shape, count: int) -> list[Shape]:
    orbit = [shape for shape in _dihedral(template) if shape != template]
    if not orbit:
        raise ValueError("template has no orientation-sensitive near miss")
    first = ctx.draw_choice("near_miss_shape", tuple(orbit))

    different_size = tuple(
        shape
        for shape in _ALL_DECOY_SHAPES
        if len(shape) != len(template)
    )
    second = ctx.draw_choice("different_size_shape", different_size)
    chosen = [first, second]

    pool = [
        shape
        for shape in _ALL_DECOY_SHAPES
        if shape != template and shape not in chosen
    ]
    rng = ctx.draw_rng("remaining_distractor_shapes")
    rng.shuffle(pool)
    chosen.extend(pool[: max(0, count - len(chosen))])
    if len(chosen) != count:
        raise ValueError(f"unable to choose {count} distinct distractor shapes")
    return chosen


def _place_outside_objects(
    grid: list[list[int]],
    ctx,
    items: list[tuple[Shape, int, tuple[str, ...]]],
) -> None:
    """Backtracking placement with deterministic candidate orders."""
    h, w = len(grid), len(grid[0])
    occupied = {
        (r, c) for r in range(h) for c in range(w) if grid[r][c] != 0
    }
    candidate_lists: list[list[tuple[int, int]]] = []
    for idx, (shape, _color, zones) in enumerate(items):
        candidates: list[tuple[int, int]] = []
        for zone in zones:
            candidates.extend(_anchors_for_zone(shape, h, w, zone))
        # Stable de-duplication followed by keyed random order.
        candidates = sorted(set(candidates))
        ctx.draw_rng(f"placement_{idx}").shuffle(candidates)
        candidate_lists.append(candidates)

    placements: list[tuple[int, int] | None] = [None] * len(items)

    def search(index: int) -> bool:
        if index == len(items):
            return True
        shape, _color, _zones = items[index]
        for r0, c0 in candidate_lists[index]:
            cells = {(r0 + dr, c0 + dc) for dr, dc in shape}
            if cells & occupied:
                continue
            occupied.update(cells)
            placements[index] = (r0, c0)
            if search(index + 1):
                return True
            occupied.difference_update(cells)
            placements[index] = None
        return False

    if not search(0):
        raise ValueError(
            "unable to place target and distractors under the requested axes"
        )
    for (shape, color, _zones), placement in zip(items, placements):
        assert placement is not None
        _paint(grid, shape, placement[0], placement[1], color)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 10, 14)
    w = ctx.draw_int_diff("grid_w", 10, 14)
    template_size = ctx.draw_int_diff("template_size", 3, 5)
    distractor_count = ctx.draw_int_diff("distractor_count", 2, 4)
    target_zone = ctx.draw_choice("target_zone", TARGET_ZONES)

    template = ctx.draw_choice(
        "template_shape", TEMPLATE_SHAPES_BY_SIZE[template_size]
    )
    template_h, template_w = _bbox_size(template)
    template_offsets = tuple(
        (r, c)
        for r in range(4 - template_h)
        for c in range(4 - template_w)
    )
    template_r, template_c = ctx.draw_choice("template_offset", template_offsets)

    # Maximum draw is template + target + four distractors = six colors.
    colors = ctx.draw_distinct_colors("object_colors", n=6, exclude={0, 5})
    template_color = colors[0]
    target_color = colors[1]
    distractor_colors = colors[2 : 2 + distractor_count]

    grid = full_grid(h, w, 0)
    for r, c in _CUE_CELLS:
        grid[r][c] = 5
    _paint(grid, template, template_r, template_c, template_color)

    distractor_shapes = _choose_distractors(ctx, template, distractor_count)
    zone_rng = ctx.draw_rng("distractor_zone_order")
    zone_cycle = list(TARGET_ZONES)
    zone_rng.shuffle(zone_cycle)

    items: list[tuple[Shape, int, tuple[str, ...]]] = [
        (template, target_color, (target_zone,))
    ]
    for index, (shape, color) in enumerate(
        zip(distractor_shapes, distractor_colors)
    ):
        preferred = zone_cycle[index % len(zone_cycle)]
        alternatives = tuple(
            [preferred]
            + [zone for zone in zone_cycle if zone != preferred]
        )
        items.append((shape, color, alternatives))

    # Place larger/sparser constraints first only after the target, whose exact
    # zone is an externally observable axis.  Stable order keeps replay exact.
    target_item, rest = items[0], items[1:]
    rest = sorted(
        rest,
        key=lambda item: (-len(item[0]), -_bbox_size(item[0])[0] * _bbox_size(item[0])[1], item[0]),
    )
    _place_outside_objects(grid, ctx, [target_item, *rest])

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError("generated invalid instance: " + "; ".join(errors))
    return grid
