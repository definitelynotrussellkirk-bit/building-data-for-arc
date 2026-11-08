"""Generator for 9758187b19ad — multicolor transform-coded stamps.

The input contains one colored stencil and marker cells.  Stencil cells use
colors {1, 2, 7, 8, 9}; markers use the disjoint code palette {3, 4, 5, 6}.
The canonical Racket rule normalizes the stencil to its bounding-box origin and
stamps it on a blank output at every marker anchor:

* 3: identity
* 4: horizontal reflection (flip left/right)
* 5: vertical reflection (flip up/down)
* 6: clockwise rotation

The marker is the top-left anchor of the transformed stencil's bounding box.
It is not necessarily painted in the output when the normalized stencil has an
empty top-left corner.  Internal stencil colors are preserved exactly.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
from itertools import combinations
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9758187b19ad"
TASK_ID = "9758187b19ad"
VERSION = "3.2.0"
RULE_HASH = "bb29b95b6fe8"

SUMMARY = (
    "A four-color stencil in colors {1,2,7,8,9} is normalized to its bounding "
    "box. Marker colors encode identity (3), horizontal reflection (4), "
    "vertical reflection (5), and clockwise rotation (6). The transformed "
    "colored stencil is stamped with its bounding-box top-left at each marker "
    "onto an otherwise blank output."
)

INVARIANTS = [
    "one 8-connected stencil of 5..8 cells using exactly four colors from {1,2,7,8,9}",
    "4..6 marker cells, including every code color 3, 4, 5, and 6",
    "every transformed stencil stays in bounds and stamp bounding boxes do not overlap",
    "the source stencil bounding box is 2..4 cells on each side and is disjoint from all stamp boxes",
    "profile-constrained morphology varies beyond the six canonical-linked base masks",
    "source placement cycles through left, middle, and right regions rather than identifying the stencil by position",
    "every three-example curriculum window contains a repeated marker code and a non-left source",
    "every three-example curriculum window also exposes a noncanonical grid/template size, more than five stencil cells, and template color 1",
    "ordinary draws make identity, both reflections, and clockwise rotation color-distinct",
    "the output authority is the canonical Racket rule; Python solvers below are audit-only rivals",
]

# Only properties that can be recovered exactly from the returned input are
# public axes.  Stencil morphology and palette choice still vary, but they are
# intentionally internal distribution choices rather than unverifiable knobs.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-linked profile",
        "valid": "19..24",
    },
    "n_markers": {
        "type": "int",
        "default": "scheduled 4..6",
        "valid": "4..6",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.95

_TEMPLATE_COLORS = (1, 2, 7, 8, 9)
_MARKER_COLORS = (3, 4, 5, 6)
_BANNED_FROM_TEMPLATE = {0, *_MARKER_COLORS}
_NEIGHBORS_8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# Six curriculum profiles preserve the canonical dimensions and anchor cases,
# but each profile describes a morphology class rather than one immutable mask.
# Source side and marker multiplicity use separate coprime schedules below, so
# those semantic factors are crossed with morphology instead of aliased to it.
_PROFILES = (
    {
        "name": "canonical_l",
        "grid_h": 12,
        "grid_w": 19,
        "bbox": (3, 2),
        "top_left_filled": True,
        "cells": ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
    },
    {
        "name": "canonical_cross_empty_corner",
        "grid_h": 13,
        "grid_w": 19,
        "bbox": (3, 3),
        "top_left_filled": False,
        "cells": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    },
    {
        "name": "canonical_x",
        "grid_h": 13,
        "grid_w": 20,
        "bbox": (3, 3),
        "top_left_filled": True,
        "cells": ((0, 0), (0, 2), (1, 1), (2, 0), (2, 2)),
    },
    {
        "name": "wide_zig",
        "grid_h": 12,
        "grid_w": 20,
        "bbox": (2, 4),
        "top_left_filled": True,
        "cells": ((0, 0), (0, 1), (1, 1), (1, 2), (1, 3)),
    },
    {
        "name": "tall_hook_empty_corner",
        "grid_h": 14,
        "grid_w": 21,
        "bbox": (4, 2),
        "top_left_filled": False,
        "cells": ((0, 1), (1, 0), (1, 1), (2, 0), (3, 0)),
    },
    {
        "name": "asymmetric_square",
        "grid_h": 16,
        "grid_w": 22,
        "bbox": (4, 4),
        "top_left_filled": True,
        "cells": (
            (0, 0), (0, 2), (1, 1), (1, 2),
            (2, 1), (2, 3), (3, 0), (3, 1),
        ),
    },
)
# Alternate canonical-size and expanded-size profiles.  The previous order put
# all three canonical grid/template size classes in one three-demo window.
_PROFILE_SCHEDULE_ORDER = (0, 3, 1, 4, 2, 5)
SCHEDULE_PROFILES = tuple(
    _PROFILES[index]["name"] for index in _PROFILE_SCHEDULE_ORDER
)
_DIFFICULTY_OFFSETS = {None: 0, "easy": 0, "medium": 2, "hard": 4}
_SOURCE_SIDE_SCHEDULE = ("left", "middle", "left", "right", "middle")
_MARKER_COUNT_SCHEDULE = (4, 5, 4, 6, 5, 4, 6)
_SHORTCUT_BREAKER_SCHEDULE = (False, True, False)
_CANONICAL_TEMPLATE_BOXES = frozenset({(3, 2), (3, 3)})
_CANONICAL_GRID_SIZES = frozenset({(12, 19), (13, 19), (13, 20)})


def _scheduled_value(values, sample_index: int, difficulty: str | None):
    if difficulty not in _DIFFICULTY_OFFSETS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    slot = int(sample_index) + _DIFFICULTY_OFFSETS[difficulty]
    return values[slot % len(values)]


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum profile name for gate auditing."""
    del seed
    return str(_scheduled_value(SCHEDULE_PROFILES, sample_index, difficulty))


def _source_side_for(sample_index: int, difficulty: str | None) -> str:
    """Cross source placement with the six morphology profiles (period 5)."""
    return str(_scheduled_value(_SOURCE_SIDE_SCHEDULE, sample_index, difficulty))


def _marker_count_for(sample_index: int, difficulty: str | None) -> int:
    """Cross marker multiplicity with morphology and source side (period 7)."""
    return int(_scheduled_value(_MARKER_COUNT_SCHEDULE, sample_index, difficulty))


def _shortcut_breaker_required(sample_index: int, difficulty: str | None) -> bool:
    """Designate one sample in every three-example window as feature-expanding."""
    return bool(_scheduled_value(_SHORTCUT_BREAKER_SCHEDULE, sample_index, difficulty))


def _profile_for(sample_index: int, difficulty: str | None) -> dict[str, object]:
    name = schedule_profile(0, sample_index, difficulty)
    return next(profile for profile in _PROFILES if profile["name"] == name)


def _draw_profile_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    """Use the scheduled default while allowing every declared boundary."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _normalize_entries(entries: Iterable[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    entries = list(entries)
    r0 = min(r for r, _, _ in entries)
    c0 = min(c for _, c, _ in entries)
    return [(r - r0, c - c0, value) for r, c, value in entries]


def _connected_8(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _NEIGHBORS_8:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


@lru_cache(maxsize=None)
def _shape_candidates(
    box_h: int, box_w: int, top_left_filled: bool
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Enumerate connected 5..8-cell masks spanning one profile bounding box."""
    positions = tuple((r, c) for r in range(box_h) for c in range(box_w))
    candidates: list[tuple[tuple[int, int], ...]] = []
    for count in range(5, min(8, len(positions)) + 1):
        for combo in combinations(positions, count):
            cells = set(combo)
            if ((0, 0) in cells) != top_left_filled:
                continue
            if {r for r, _ in cells} != set(range(box_h)):
                continue
            if {c for _, c in cells} != set(range(box_w)):
                continue
            if not _connected_8(cells):
                continue
            candidates.append(tuple(sorted(cells)))
    if not candidates:
        raise RuntimeError(
            f"no lawful stencil masks for {box_h}x{box_w}, "
            f"top_left_filled={top_left_filled}"
        )
    return tuple(candidates)


def _cells_for_profile(
    rng,
    profile: dict[str, object],
    *,
    require_extra_cell: bool = False,
) -> tuple[tuple[int, int], ...]:
    """Retain canonical masks while forcing >5 cells in scheduled witnesses."""
    box_h, box_w = profile["bbox"]
    base = tuple(profile["cells"])
    pool = _shape_candidates(
        int(box_h), int(box_w), bool(profile["top_left_filled"])
    )
    normalized_base = tuple(sorted(base))
    if normalized_base not in pool:
        raise RuntimeError(f"profile {profile['name']} base mask violates its class")
    minimum_cells = 6 if require_extra_cell else 5
    eligible = tuple(cells for cells in pool if len(cells) >= minimum_cells)
    if not eligible:
        raise RuntimeError(
            f"profile {profile['name']} has no mask with {minimum_cells}+ cells"
        )
    if normalized_base in eligible and rng.random() < 0.20:
        return base
    alternatives = tuple(cells for cells in eligible if cells != normalized_base)
    return rng.choice(alternatives or eligible)


def _transform_entries(
    entries: Iterable[tuple[int, int, int]], op: int | str
) -> list[tuple[int, int, int]]:
    """Mirror the canonical Racket transform coordinates exactly."""
    entries = list(entries)
    h = 1 + max(r for r, _, _ in entries)
    w = 1 + max(c for _, c, _ in entries)
    transformed: list[tuple[int, int, int]] = []
    for r, c, value in entries:
        if op == 0:
            rr, cc = r, c
        elif op == 1:
            rr, cc = r, w - 1 - c
        elif op == 2:
            rr, cc = h - 1 - r, c
        elif op == 3:  # canonical marker 6: clockwise rotation
            rr, cc = c, h - 1 - r
        elif op == "transpose":  # deliberately wrong rival
            rr, cc = c, r
        else:
            raise ValueError(f"unknown transform op: {op!r}")
        transformed.append((rr, cc, value))
    return transformed


def _signature(entries: Iterable[tuple[int, int, int]]) -> tuple[tuple[int, int, int], ...]:
    return tuple(sorted(entries))


def _colored_entries(
    rng,
    cells: tuple[tuple[int, int], ...],
    *,
    require_color_one: bool = False,
) -> list[tuple[int, int, int]]:
    """Assign four colors while making all transforms distinguishable."""
    for _ in range(256):
        if require_color_one:
            palette = [1, *rng.sample([2, 7, 8, 9], 3)]
            rng.shuffle(palette)
        else:
            palette = rng.sample(list(_TEMPLATE_COLORS), 4)
        values = palette + [rng.choice(palette) for _ in range(len(cells) - 4)]
        rng.shuffle(values)
        entries = [(r, c, value) for (r, c), value in zip(cells, values)]
        true_signatures = [_signature(_transform_entries(entries, op)) for op in range(4)]
        if len(set(true_signatures)) != 4:
            continue
        if _signature(_transform_entries(entries, 3)) == _signature(
            _transform_entries(entries, "transpose")
        ):
            continue
        return entries
    raise RuntimeError("could not color the scheduled stencil without transform ambiguity")


def _rectangles_overlap(
    first: tuple[int, int, int, int], second: tuple[int, int, int, int]
) -> bool:
    ar, ac, ah, aw = first
    br, bc, bh, bw = second
    return ar < br + bh and br < ar + ah and ac < bc + bw and bc < ac + aw


def _source_columns(side: str, grid_w: int, source_w: int) -> range:
    """Columns that put the full source box in a left/middle/right region."""
    if side == "left":
        lo, hi = 0, 5 - source_w
    elif side == "right":
        lo, hi = grid_w - 5, grid_w - source_w
    elif side == "middle":
        lo, hi = 5, grid_w - 5 - source_w
    else:
        raise ValueError(f"unknown source side: {side!r}")
    if hi < lo:
        raise ValueError(
            f"grid width {grid_w} cannot place a {source_w}-wide source on {side}"
        )
    return range(lo, hi + 1)


def _pack_layout(
    rng,
    h: int,
    w: int,
    source_h: int,
    source_w: int,
    marker_codes: list[int],
    source_side: str,
) -> tuple[tuple[int, int], list[tuple[int, int]]]:
    """Randomly pack the source and all transformed stamp boxes without overlap."""
    source_candidates = [
        (r, c)
        for r in range(h - source_h + 1)
        for c in _source_columns(source_side, w, source_w)
    ]
    marker_items = [
        (
            index,
            source_w if color == 6 else source_h,
            source_h if color == 6 else source_w,
        )
        for index, color in enumerate(marker_codes)
    ]

    for _ in range(256):
        source_anchor = rng.choice(source_candidates)
        placed = [(*source_anchor, source_h, source_w)]
        positions: dict[int, tuple[int, int]] = {}
        order = marker_items[:]
        rng.shuffle(order)
        for index, box_h, box_w in order:
            candidates = [
                (r, c)
                for r in range(h - box_h + 1)
                for c in range(w - box_w + 1)
                if not any(
                    _rectangles_overlap((r, c, box_h, box_w), other)
                    for other in placed
                )
            ]
            if not candidates:
                break
            anchor = rng.choice(candidates)
            positions[index] = anchor
            placed.append((*anchor, box_h, box_w))
        if len(positions) == len(marker_codes):
            return source_anchor, [positions[index] for index in range(len(marker_codes))]
    raise RuntimeError(
        f"could not pack source plus {len(marker_codes)} stamp boxes in {h}x{w}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    profile = _profile_for(sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_profile_int(ctx, overrides, "grid_h", int(profile["grid_h"]), 12, 18)
    w = _draw_profile_int(ctx, overrides, "grid_w", int(profile["grid_w"]), 19, 24)
    n_markers = _draw_profile_int(
        ctx,
        overrides,
        "n_markers",
        _marker_count_for(sample_index, difficulty),
        4,
        6,
    )
    shape_rng = ctx.draw_rng("shape")
    color_rng = ctx.draw_rng("colors")
    marker_rng = ctx.draw_rng("markers")
    layout_rng = ctx.draw_rng("layout")

    shortcut_breaker = _shortcut_breaker_required(sample_index, difficulty)
    cells = _cells_for_profile(
        shape_rng, profile, require_extra_cell=shortcut_breaker
    )
    entries = _colored_entries(
        color_rng, cells, require_color_one=shortcut_breaker
    )
    th = 1 + max(r for r, _, _ in entries)
    tw = 1 + max(c for _, c, _ in entries)

    marker_codes = list(_MARKER_COLORS)
    marker_codes.extend(
        marker_rng.choice(_MARKER_COLORS) for _ in range(n_markers - 4)
    )
    marker_rng.shuffle(marker_codes)
    source_anchor, marker_anchors = _pack_layout(
        layout_rng,
        h,
        w,
        th,
        tw,
        marker_codes,
        _source_side_for(sample_index, difficulty),
    )

    grid = full_grid(h, w, 0)
    source_r, source_c = source_anchor
    for r, c, value in entries:
        grid[source_r + r][source_c + c] = value
    for (anchor_r, anchor_c), color in zip(marker_anchors, marker_codes):
        grid[anchor_r][anchor_c] = color

    return grid


def _absolute_template_entries(
    grid,
    *,
    max_col_exclusive: int | None = None,
    ignore_color_one: bool = False,
) -> list[tuple[int, int, int]]:
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in _BANNED_FROM_TEMPLATE
        and (not ignore_color_one or value != 1)
        and (max_col_exclusive is None or c < max_col_exclusive)
    ]


def _template_entries_from_grid(
    grid, *, max_col_exclusive: int | None = None
) -> list[tuple[int, int, int]]:
    entries = _absolute_template_entries(
        grid, max_col_exclusive=max_col_exclusive
    )
    return _normalize_entries(entries) if entries else []


def _markers_from_grid(grid) -> dict[int, list[tuple[int, int]]]:
    return {
        color: [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        for color in _MARKER_COLORS
    }


def _paint_entries(out, entries, anchor):
    ar, ac = anchor
    for r, c, value in entries:
        rr, cc = ar + r, ac + c
        if 0 <= rr < len(out) and 0 <= cc < len(out[0]):
            out[rr][cc] = value
    return out


def _solve_candidate(
    grid,
    *,
    all_identity: bool = False,
    color6_transpose: bool = False,
    monochrome: bool = False,
    marker_only: bool = False,
    first_marker_per_code: bool = False,
    template_left_strip_only: bool = False,
    first_five_template_cells: bool = False,
    ignore_color_one: bool = False,
    canonical_template_boxes_only: bool = False,
    canonical_grid_sizes_only: bool = False,
):
    """Audit-only Python mirror used for named rival comparisons."""
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    markers = _markers_from_grid(grid)
    if marker_only:
        for color in _MARKER_COLORS:
            for r, c in markers[color]:
                out[r][c] = color
        return out

    if canonical_grid_sizes_only and (h, w) not in _CANONICAL_GRID_SIZES:
        return out

    absolute_entries = _absolute_template_entries(
        grid,
        max_col_exclusive=5 if template_left_strip_only else None,
        ignore_color_one=ignore_color_one,
    )
    if not absolute_entries:
        return out
    if canonical_template_boxes_only:
        r0, c0, r1, c1 = _bbox((r, c) for r, c, _ in absolute_entries)
        if (r1 - r0 + 1, c1 - c0 + 1) not in _CANONICAL_TEMPLATE_BOXES:
            return out
    if first_five_template_cells:
        absolute_entries = absolute_entries[:5]
    entries = _normalize_entries(absolute_entries)
    if monochrome:
        modal = min(
            value
            for value, count in Counter(v for _, _, v in entries).items()
            if count == max(Counter(v for _, _, v in entries).values())
        )
        entries = [(r, c, modal) for r, c, _ in entries]

    for color in _MARKER_COLORS:
        if all_identity:
            op: int | str = 0
        elif color6_transpose and color == 6:
            op = "transpose"
        else:
            op = {3: 0, 4: 1, 5: 2, 6: 3}[color]
        transformed = _transform_entries(entries, op)
        selected_markers = markers[color][:1] if first_marker_per_code else markers[color]
        for marker in selected_markers:
            _paint_entries(out, transformed, marker)
    return out


def _rect_cells(r0: int, c0: int, h: int, w: int) -> set[tuple[int, int]]:
    return {(r, c) for r in range(r0, r0 + h) for c in range(c0, c0 + w)}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural checker that accepts all canonical inputs and rejects impostors."""
    del difficulty, meta
    errors: list[str] = []
    if not grid or not isinstance(grid, list):
        return ["empty or non-list grid"]
    if not grid[0] or any(not isinstance(row, list) for row in grid):
        return ["empty or non-list row"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    if not (12 <= h <= 18 and 19 <= w <= 24):
        errors.append(f"grid dimensions outside 12..18 by 19..24: {h}x{w}")
    if any(not isinstance(value, int) or not (0 <= value <= 9) for row in grid for value in row):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    absolute_entries = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in _BANNED_FROM_TEMPLATE
    ]
    if not absolute_entries:
        errors.append("no stencil cells in {1,2,7,8,9}")
        return errors
    illegal_template_values = sorted({v for _, _, v in absolute_entries} - set(_TEMPLATE_COLORS))
    if illegal_template_values:
        errors.append(f"illegal stencil colors: {illegal_template_values}")

    source_cells = {(r, c) for r, c, _ in absolute_entries}
    source_colors = [value for _, _, value in absolute_entries]
    if not (5 <= len(source_cells) <= 8):
        errors.append(f"stencil must contain 5..8 cells, found {len(source_cells)}")
    if len(set(source_colors)) != 4:
        errors.append(f"stencil must use exactly four colors, found {sorted(set(source_colors))}")
    if max(Counter(source_colors).values(), default=0) < 2:
        errors.append("stencil must repeat at least one internal color")
    if not _connected_8(source_cells):
        errors.append("stencil cells are not one 8-connected object")

    sr0, sc0, sr1, sc1 = _bbox(source_cells)
    th, tw = sr1 - sr0 + 1, sc1 - sc0 + 1
    if not (2 <= th <= 4 and 2 <= tw <= 4):
        errors.append(f"stencil bounding box must be 2..4 by 2..4, found {th}x{tw}")

    markers = _markers_from_grid(grid)
    marker_count = sum(len(cells) for cells in markers.values())
    missing_codes = [color for color in _MARKER_COLORS if not markers[color]]
    if not (4 <= marker_count <= 6):
        errors.append(f"expected 4..6 marker cells, found {marker_count}")
    if missing_codes:
        errors.append(f"missing marker code(s): {missing_codes}")

    if errors:
        # Continue only when the geometry is still safe to derive.
        if not absolute_entries or missing_codes:
            return errors

    normalized = _normalize_entries(absolute_entries)
    source_box = _rect_cells(sr0, sc0, th, tw)
    stamp_boxes: list[tuple[int, int, set[tuple[int, int]]]] = []
    for color in _MARKER_COLORS:
        transformed = _transform_entries(normalized, {3: 0, 4: 1, 5: 2, 6: 3}[color])
        bh = 1 + max(r for r, _, _ in transformed)
        bw = 1 + max(c for _, c, _ in transformed)
        for anchor_r, anchor_c in markers[color]:
            if anchor_r + bh > h or anchor_c + bw > w:
                errors.append(
                    f"marker {color} at {(anchor_r, anchor_c)} sends a {bh}x{bw} stamp out of bounds"
                )
                continue
            box = _rect_cells(anchor_r, anchor_c, bh, bw)
            if box & source_box:
                errors.append(
                    f"marker {color} stamp box overlaps the source stencil box"
                )
            for other_color, other_index, other_box in stamp_boxes:
                if box & other_box:
                    errors.append(
                        f"marker {color} stamp box overlaps marker {other_color} stamp box #{other_index}"
                    )
            stamp_boxes.append((color, len(stamp_boxes), box))

    # At least one non-identity marker must genuinely require a transform.  This
    # rejects all-symmetric rule-hiding scenes while still accepting the one
    # canonical cross whose vertical flip alone happens to equal identity.
    try:
        if _solve_candidate(grid) == _solve_candidate(grid, all_identity=True):
            errors.append("all coded transforms collapse to identity on this stencil")
    except Exception as exc:
        errors.append(f"could not audit transform distinctness: {type(exc).__name__}: {exc}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked canonical-manifold predicate used by the semantic gate."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public-axis value from the returned input grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_markers": sum(value in _MARKER_COLORS for row in grid for value in row),
    }


def _source_side_observation(grid) -> str:
    """Classify the source box by the three placement regions used in generation."""
    source_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in _BANNED_FROM_TEMPLATE
    ]
    _, c0, _, c1 = _bbox(source_cells)
    if c1 < 5:
        return "left"
    if c0 >= len(grid[0]) - 5:
        return "right"
    return "middle"


def _template_shape(grid) -> tuple[int, int, set[tuple[int, int]]]:
    entries = _template_entries_from_grid(grid)
    h = 1 + max(r for r, _, _ in entries)
    w = 1 + max(c for _, c, _ in entries)
    return h, w, {(r, c) for r, c, _ in entries}


def _pairwise_transform_distinct(grid) -> bool:
    entries = _template_entries_from_grid(grid)
    return len({_signature(_transform_entries(entries, op)) for op in range(4)}) == 4


def _rival_differs(grid, rival: Callable) -> bool:
    try:
        return _solve_candidate(grid) != rival(grid)
    except Exception:
        return False


SEMANTIC_RIVALS: dict[str, Callable] = {
    "all_markers_identity": lambda grid: _solve_candidate(grid, all_identity=True),
    "color6_is_transpose": lambda grid: _solve_candidate(grid, color6_transpose=True),
    "monochrome_stencil": lambda grid: _solve_candidate(grid, monochrome=True),
    "copy_marker_cells": lambda grid: _solve_candidate(grid, marker_only=True),
    # The six distributional shortcuts below fit every canonical pair exactly.
    # Generated lessons must actively disprove them rather than relying on
    # out-of-distribution hope.
    "first_marker_per_code": lambda grid: _solve_candidate(
        grid, first_marker_per_code=True
    ),
    "template_only_in_left_strip": lambda grid: _solve_candidate(
        grid, template_left_strip_only=True
    ),
    "first_five_template_cells": lambda grid: _solve_candidate(
        grid, first_five_template_cells=True
    ),
    "ignore_color_one": lambda grid: _solve_candidate(
        grid, ignore_color_one=True
    ),
    "canonical_template_boxes_only": lambda grid: _solve_candidate(
        grid, canonical_template_boxes_only=True
    ),
    "canonical_grid_sizes_only": lambda grid: _solve_candidate(
        grid, canonical_grid_sizes_only=True
    ),
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "first_marker_per_code",
        "template_only_in_left_strip",
        "first_five_template_cells",
        "ignore_color_one",
        "canonical_template_boxes_only",
        "canonical_grid_sizes_only",
    )
}

SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "all_identity_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["all_markers_identity"]
    ),
    "color6_transpose_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["color6_is_transpose"]
    ),
    "monochrome_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["monochrome_stencil"]
    ),
    "marker_only_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["copy_marker_cells"]
    ),
    "first_marker_per_code_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["first_marker_per_code"]
    ),
    "left_strip_template_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["template_only_in_left_strip"]
    ),
    "first_five_template_cells_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["first_five_template_cells"]
    ),
    "ignore_color_one_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["ignore_color_one"]
    ),
    "canonical_template_boxes_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["canonical_template_boxes_only"]
    ),
    "canonical_grid_sizes_refuted": lambda grid: _rival_differs(
        grid, SEMANTIC_RIVALS["canonical_grid_sizes_only"]
    ),
    "source_left": lambda grid: _source_side_observation(grid) == "left",
    "source_middle": lambda grid: _source_side_observation(grid) == "middle",
    "source_right": lambda grid: _source_side_observation(grid) == "right",
    "square_template": lambda grid: _template_shape(grid)[0] == _template_shape(grid)[1],
    "non_square_template": lambda grid: _template_shape(grid)[0] != _template_shape(grid)[1],
    "filled_top_left_anchor": lambda grid: (0, 0) in _template_shape(grid)[2],
    "empty_top_left_anchor": lambda grid: (0, 0) not in _template_shape(grid)[2],
    "repeated_marker_code": lambda grid: observe_overrides(grid)["n_markers"] > 4,
    "all_four_transforms_distinct": _pairwise_transform_distinct,
}

WITNESS_RIVALS = {
    "all_identity_refuted": ["all_markers_identity"],
    "color6_transpose_refuted": ["color6_is_transpose"],
    "monochrome_refuted": ["monochrome_stencil"],
    "marker_only_refuted": ["copy_marker_cells"],
    "first_marker_per_code_refuted": ["first_marker_per_code"],
    "left_strip_template_refuted": ["template_only_in_left_strip"],
    "first_five_template_cells_refuted": ["first_five_template_cells"],
    "ignore_color_one_refuted": ["ignore_color_one"],
    "canonical_template_boxes_refuted": ["canonical_template_boxes_only"],
    "canonical_grid_sizes_refuted": ["canonical_grid_sizes_only"],
}


# These predicates are positive curriculum/coverage facts, not claims that one
# firing alone refutes a fixed rival.  Classifying them explicitly keeps the
# strict after-phase semantic gate honest without inventing disagreement claims.
BRANCH_WITNESSES = {
    "square_template",
    "non_square_template",
    "filled_top_left_anchor",
    "empty_top_left_anchor",
    "repeated_marker_code",
    "all_four_transforms_distinct",
    "source_left",
    "source_middle",
    "source_right",
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to reject every named plausible shortcut for the query."""
    reasons: list[str] = []
    if not demos:
        return ["lesson has no demonstrations"]

    for index, pair in enumerate(demos):
        errors = strict_canonical_like(pair.get("input"))
        if errors:
            reasons.append(f"demo {index} is not canonical-like: {errors[0]}")
    query_errors = strict_canonical_like(query.get("input"))
    if query_errors:
        reasons.append(f"query is not canonical-like: {query_errors[0]}")

    seen_codes = {
        value
        for pair in demos
        for row in pair["input"]
        for value in row
        if value in _MARKER_COLORS
    }
    if seen_codes != set(_MARKER_COLORS):
        reasons.append(f"demos do not expose every marker code: {sorted(seen_codes)}")
    if not any(_pairwise_transform_distinct(pair["input"]) for pair in demos):
        reasons.append("no demo makes all four coded transforms distinguishable")

    for name, rival in LESSON_COMPETITORS.items():
        try:
            survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except Exception as exc:
            reasons.append(f"competitor {name} errored: {type(exc).__name__}: {exc}")
            continue
        if survives:
            reasons.append(f"competitor {name} fits every demo")
    return reasons
