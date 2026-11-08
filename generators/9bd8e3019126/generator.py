"""Generator for ``hard_h20`` — build the four Boolean-shape gallery.

The input contains exactly two monochrome 4-connected objects.  Their absolute
positions and source colors are discarded.  After cropping each object to its
own bounding box, the left object is A and the right object is B; both masks are
padded at the top-left to a common canvas.  The canonical Racket rule emits a
2x2 gallery of independently cropped Boolean masks: union in 2, intersection
in 3, xor in 4, and A-minus-B in 6.

A four-profile cyclic schedule makes every consecutive four demonstrations
show: partial overlap at equal bbox size, partial overlap at mismatched bbox
size (where top-left alignment matters), A proper-subset-of B (empty A-B), and
B proper-subset-of A (non-empty directional A-B).  This defeats symmetric,
center-aligned, fixed-panel, and copied-shape shortcuts at lesson level.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "9bd8e3019126"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "2ce8e0c3d188"

SUMMARY = (
    "Two separated monochrome source shapes are cropped and top-left aligned; "
    "the output is a four-panel gallery of union(2), intersection(3), xor(4), "
    "and left-shape-minus-right-shape(6), with one-cell black separators."
)

INVARIANTS = [
    "background is 0 and the input contains exactly two monochrome 4-connected objects",
    "the object with the smaller left bbox column is A and the other object is B",
    "source colors and absolute positions do not affect the output",
    "cropped A and B are padded at the top-left before Boolean comparison",
    "union/intersection/xor/A-minus-B panels use fixed colors 2/3/4/6",
    "each Boolean panel is cropped independently before the 2x2 gallery is packed",
    "ordinary lessons cycle through two partial-overlap and two proper-subset profiles",
    "the canonical Racket program is the sole output authority",
]

_PROFILE_PARTIAL_SAME = "partial_same_bbox"
_PROFILE_PARTIAL_MISMATCH = "partial_mismatched_bbox"
_PROFILE_A_SUBSET = "a_subset_b"
_PROFILE_B_SUBSET = "b_subset_a"
_PROFILES = (
    _PROFILE_PARTIAL_SAME,
    _PROFILE_PARTIAL_MISMATCH,
    _PROFILE_A_SUBSET,
    _PROFILE_B_SUBSET,
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-scale cyclic 8/9",
        "valid": "8..9",
        "doc": "Returned input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-scale cyclic 11/12/13",
        "valid": "11..13",
        "doc": "Returned input-grid width.",
    },
    "profile": {
        "type": "enum",
        "default": "sample_index modulo four",
        "valid": [
            "partial_same_bbox",
            "partial_mismatched_bbox",
            "a_subset_b",
            "b_subset_a",
        ],
        "doc": "Exact top-left-normalized relation between A and B.",
    },
    "a_color": {
        "type": "color",
        "default": "rng nonzero",
        "valid": "1..9",
        "doc": "Color of the left source object A.",
    },
    "b_color": {
        "type": "color",
        "default": "rng nonzero",
        "valid": "1..9",
        "doc": "Color of the right source object B; it may equal A's color.",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = _PROFILES

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CANONICAL_DIMS = ((8, 11), (9, 12), (8, 13), (9, 12))

Grid = list[list[int]]
Mask = tuple[tuple[int, ...], ...]
CellSet = set[tuple[int, int]]


def _copy_grid(grid: Sequence[Sequence[int]]) -> Grid:
    return [list(row) for row in grid]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    if not any(value == 0 for row in grid for value in row):
        return ["background color 0 must be present"]
    return []


def _extract_components(grid: Sequence[Sequence[int]]) -> list[dict[str, object]]:
    """Mirror ``objects g 0``: same-color, 4-connected nonzero components."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, object]] = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or (r0, c0) in seen:
                continue
            color = grid[r0][c0]
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _DIRS4:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            components.append({"color": color, "cells": tuple(sorted(cells)), "bbox": bbox})
    return components


def _mask_from_object(obj: dict[str, object]) -> Mask:
    r1, c1, r2, c2 = obj["bbox"]  # type: ignore[misc]
    cells = set(obj["cells"])  # type: ignore[arg-type]
    return tuple(
        tuple(1 if (r, c) in cells else 0 for c in range(c1, c2 + 1))
        for r in range(r1, r2 + 1)
    )


def _mask_cells(mask: Sequence[Sequence[int]]) -> CellSet:
    return {
        (r, c)
        for r, row in enumerate(mask)
        for c, value in enumerate(row)
        if value != 0
    }


def _cells_to_mask(cells: CellSet, h: int, w: int) -> Mask:
    return tuple(tuple(1 if (r, c) in cells else 0 for c in range(w)) for r in range(h))


def _crop_mask(mask: Sequence[Sequence[int]]) -> Mask:
    cells = _mask_cells(mask)
    if not cells:
        return ((0,),)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r1, r2 = min(rows), max(rows)
    c1, c2 = min(cols), max(cols)
    return tuple(
        tuple(1 if mask[r][c] else 0 for c in range(c1, c2 + 1))
        for r in range(r1, r2 + 1)
    )


def _pad_mask(mask: Sequence[Sequence[int]], h: int, w: int, *, align: str) -> Mask:
    mh, mw = len(mask), len(mask[0])
    if align == "top_left":
        top = left = 0
    elif align == "center":
        top = (h - mh) // 2
        left = (w - mw) // 2
    else:
        raise ValueError(f"unknown alignment: {align!r}")
    cells = {(top + r, left + c) for r, c in _mask_cells(mask)}
    return _cells_to_mask(cells, h, w)


def _normalized_masks(a: Mask, b: Mask, *, align: str = "top_left") -> tuple[Mask, Mask]:
    h = max(len(a), len(b))
    w = max(len(a[0]), len(b[0]))
    return _pad_mask(a, h, w, align=align), _pad_mask(b, h, w, align=align)


def _relation_profile(a: Mask, b: Mask) -> str:
    aa, bb = _normalized_masks(a, b)
    aset, bset = _mask_cells(aa), _mask_cells(bb)
    if aset == bset:
        return "equal"
    if aset < bset:
        return _PROFILE_A_SUBSET
    if bset < aset:
        return _PROFILE_B_SUBSET
    if not aset.intersection(bset):
        return "disjoint"
    if aset - bset and bset - aset:
        if (len(a), len(a[0])) == (len(b), len(b[0])):
            return _PROFILE_PARTIAL_SAME
        return _PROFILE_PARTIAL_MISMATCH
    return "other"


def _paint_mask(mask: Sequence[Sequence[int]], color: int) -> Grid:
    return [[color if value else 0 for value in row] for row in mask]


def _boolean_mask(a: Mask, b: Mask, op: str, *, align: str, crop: bool) -> Mask:
    aa, bb = _normalized_masks(a, b, align=align)
    aset, bset = _mask_cells(aa), _mask_cells(bb)
    if op == "union":
        cells = aset | bset
    elif op == "intersection":
        cells = aset & bset
    elif op == "xor":
        cells = aset ^ bset
    elif op == "a_minus_b":
        cells = aset - bset
    elif op == "b_minus_a":
        cells = bset - aset
    else:
        raise ValueError(f"unknown Boolean operation: {op!r}")
    raw = _cells_to_mask(cells, len(aa), len(aa[0]))
    return _crop_mask(raw) if crop else raw


def _pack_horizontal(shapes: Sequence[Grid], gap: int = 1) -> Grid:
    h = max(len(shape) for shape in shapes)
    w = sum(len(shape[0]) for shape in shapes) + gap * (len(shapes) - 1)
    out = full_grid(h, w, 0)
    left = 0
    for shape in shapes:
        for r, row in enumerate(shape):
            for c, value in enumerate(row):
                if value != 0:
                    out[r][left + c] = value
        left += len(shape[0]) + gap
    return out


def _gallery_from_masks(
    a: Mask,
    b: Mask,
    *,
    align: str = "top_left",
    crop_panels: bool = True,
    difference_op: str = "a_minus_b",
    swap_top: bool = False,
    copy_a_only: bool = False,
) -> Grid:
    if copy_a_only:
        panel_masks = [_crop_mask(a)] * 4
    else:
        panel_masks = [
            _boolean_mask(a, b, "union", align=align, crop=crop_panels),
            _boolean_mask(a, b, "intersection", align=align, crop=crop_panels),
            _boolean_mask(a, b, "xor", align=align, crop=crop_panels),
            _boolean_mask(a, b, difference_op, align=align, crop=crop_panels),
        ]
    panels = [
        _paint_mask(panel_masks[0], 2),
        _paint_mask(panel_masks[1], 3),
        _paint_mask(panel_masks[2], 4),
        _paint_mask(panel_masks[3], 6),
    ]
    if swap_top:
        panels[0], panels[1] = panels[1], panels[0]
    top = _pack_horizontal(panels[:2])
    bottom = _pack_horizontal(panels[2:])
    width = max(len(top[0]), len(bottom[0]))
    top = [row + [0] * (width - len(row)) for row in top]
    bottom = [row + [0] * (width - len(row)) for row in bottom]
    return top + [[0] * width] + bottom


def _analyze(grid) -> dict[str, object]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    components = _extract_components(grid)
    if len(components) != 2:
        return {
            "errors": [f"expected exactly two nonzero 4-connected objects, got {len(components)}"],
            "components": components,
        }
    components.sort(key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))  # type: ignore[index]
    a_obj, b_obj = components
    a_mask, b_mask = _mask_from_object(a_obj), _mask_from_object(b_obj)
    profile = _relation_profile(a_mask, b_mask)
    truth = _gallery_from_masks(a_mask, b_mask)
    return {
        "errors": [],
        "components": components,
        "a": a_obj,
        "b": b_obj,
        "a_mask": a_mask,
        "b_mask": b_mask,
        "profile": profile,
        "truth": truth,
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "a_color": a_obj["color"],
        "b_color": b_obj["color"],
    }


def rule_mirror(grid) -> Grid:
    """Pure Python mirror used only for tests and rival discrimination."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))  # type: ignore[arg-type]
    return _copy_grid(analysis["truth"])  # type: ignore[arg-type]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the oracle-facing grammar, not curriculum-only profile duties."""
    del difficulty, meta
    analysis = _analyze(grid)
    return list(analysis["errors"])  # type: ignore[arg-type]


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])  # type: ignore[arg-type]
    if reasons:
        return reasons
    h, w = analysis["grid_h"], analysis["grid_w"]
    if not (7 <= h <= 14 and 11 <= w <= 20):
        reasons.append(f"input dimensions {(h, w)} are outside the teaching envelope")
    a_obj, b_obj = analysis["a"], analysis["b"]
    a_bbox, b_bbox = a_obj["bbox"], b_obj["bbox"]  # type: ignore[index]
    if a_bbox[1] >= b_bbox[1]:
        reasons.append("A and B must be visibly ordered left-to-right")
    for name, obj in (("A", a_obj), ("B", b_obj)):
        r1, c1, r2, c2 = obj["bbox"]  # type: ignore[misc]
        oh, ow = r2 - r1 + 1, c2 - c1 + 1
        if not (2 <= oh <= 5 and 2 <= ow <= 5):
            reasons.append(f"{name} bbox {(oh, ow)} is outside 2..5 canonical-like scale")
        if len(obj["cells"]) < 3:  # type: ignore[arg-type]
            reasons.append(f"{name} is too small to expose a nontrivial shape relation")
    if analysis["profile"] not in _PROFILES:
        reasons.append(
            f"normalized relation {analysis['profile']!r} is rule-hiding; expected one of {_PROFILES}"
        )
    return reasons


def observe_overrides(grid) -> dict[str, object]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))  # type: ignore[arg-type]
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "profile": analysis["profile"],
        "a_color": analysis["a_color"],
        "b_color": analysis["b_color"],
    }


def _spanning_path(h: int, w: int, rng) -> CellSet:
    steps = [(1, 0)] * (h - 1) + [(0, 1)] * (w - 1)
    rng.shuffle(steps)
    r = c = 0
    cells = {(r, c)}
    for dr, dc in steps:
        r += dr
        c += dc
        cells.add((r, c))
    return cells


def _grow(cells: CellSet, h: int, w: int, target: int, rng, *, forbidden: CellSet | None = None) -> CellSet:
    out = set(cells)
    forbidden = set() if forbidden is None else set(forbidden)
    target = min(target, h * w - len(forbidden))
    while len(out) < target:
        candidates = sorted(
            {
                (r + dr, c + dc)
                for r, c in out
                for dr, dc in _DIRS4
                if 0 <= r + dr < h and 0 <= c + dc < w
                and (r + dr, c + dc) not in out
                and (r + dr, c + dc) not in forbidden
            }
        )
        if not candidates:
            break
        out.add(rng.choice(candidates))
    return out


def _difficulty_cap(difficulty, grid_h: int, grid_w: int) -> int:
    band_cap = {None: 4, "easy": 4, "medium": 4, "hard": 5}[difficulty]
    fit_cap = min(grid_h - 2, (grid_w - 3) // 2)
    return max(3, min(band_cap, fit_cap, 5))


def _pair_partial_same(rng, cap: int, difficulty) -> tuple[Mask, Mask]:
    h = rng.randint(3, cap)
    w = rng.randint(3, cap)
    shared = _spanning_path(h, w, rng)
    free = sorted(set((r, c) for r in range(h) for c in range(w)) - shared)
    adjacent = [
        cell
        for cell in free
        if any((cell[0] + dr, cell[1] + dc) in shared for dr, dc in _DIRS4)
    ]
    if len(adjacent) < 2:
        raise ValueError("partial-same template lacks two exclusive attachment cells")
    a_only = rng.choice(adjacent)
    b_only = rng.choice([cell for cell in adjacent if cell != a_only])
    a_cells = set(shared) | {a_only}
    b_cells = set(shared) | {b_only}
    extra = {"easy": 0, "medium": 1, "hard": 2, None: 1}[difficulty]
    a_cells = _grow(a_cells, h, w, min(h * w - 1, len(a_cells) + rng.randint(0, extra)), rng, forbidden={b_only})
    b_cells = _grow(b_cells, h, w, min(h * w - 1, len(b_cells) + rng.randint(0, extra)), rng, forbidden={a_only})
    return _cells_to_mask(a_cells, h, w), _cells_to_mask(b_cells, h, w)


def _pair_partial_mismatch(rng, cap: int, difficulty) -> tuple[Mask, Mask]:
    h = rng.randint(4, cap)
    w = rng.randint(4, cap)
    if rng.random() < 0.5:
        ah, aw, bh, bw = h, w - 2, h - 2, w
    else:
        ah, aw, bh, bw = h - 2, w, h, w - 2
    a_cells = _spanning_path(ah, aw, rng)
    b_cells = _spanning_path(bh, bw, rng)
    extra = {"easy": 1, "medium": 2, "hard": 4, None: 2}[difficulty]
    a_cells = _grow(a_cells, ah, aw, min(ah * aw - 1, len(a_cells) + rng.randint(0, extra)), rng)
    b_cells = _grow(b_cells, bh, bw, min(bh * bw - 1, len(b_cells) + rng.randint(0, extra)), rng)
    return _cells_to_mask(a_cells, ah, aw), _cells_to_mask(b_cells, bh, bw)


def _proper_subset_pair(rng, cap: int, difficulty, *, a_is_subset: bool) -> tuple[Mask, Mask]:
    h = rng.randint(3, cap)
    w = rng.randint(3, cap)
    if rng.random() < 0.5:
        sh, sw = max(2, h - 1), w
    else:
        sh, sw = h, max(2, w - 1)
    small = _spanning_path(sh, sw, rng)
    extra_small = {"easy": 0, "medium": 1, "hard": 2, None: 1}[difficulty]
    small = _grow(small, sh, sw, min(sh * sw - 1, len(small) + rng.randint(0, extra_small)), rng)
    big = set(small)
    r, c = sh - 1, sw - 1
    steps = [(1, 0)] * (h - sh) + [(0, 1)] * (w - sw)
    rng.shuffle(steps)
    for dr, dc in steps:
        r += dr
        c += dc
        big.add((r, c))
    extra_big = {"easy": 1, "medium": 3, "hard": 5, None: 3}[difficulty]
    big = _grow(big, h, w, min(h * w, len(big) + 1 + rng.randint(0, extra_big)), rng)
    small_mask = _cells_to_mask(small, sh, sw)
    big_mask = _cells_to_mask(big, h, w)
    return (small_mask, big_mask) if a_is_subset else (big_mask, small_mask)


def _rival_identity(grid) -> Grid:
    return _copy_grid(grid)


def _rival_center_align(grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))  # type: ignore[arg-type]
    return _gallery_from_masks(analysis["a_mask"], analysis["b_mask"], align="center")  # type: ignore[arg-type]


def _rival_b_minus_a(grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))  # type: ignore[arg-type]
    return _gallery_from_masks(
        analysis["a_mask"], analysis["b_mask"], difference_op="b_minus_a"  # type: ignore[arg-type]
    )


def _rival_uncropped_panels(grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))  # type: ignore[arg-type]
    return _gallery_from_masks(
        analysis["a_mask"], analysis["b_mask"], crop_panels=False  # type: ignore[arg-type]
    )


def _rival_swap_union_intersection(grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))  # type: ignore[arg-type]
    return _gallery_from_masks(
        analysis["a_mask"], analysis["b_mask"], swap_top=True  # type: ignore[arg-type]
    )


def _rival_copy_a_four_times(grid) -> Grid:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))  # type: ignore[arg-type]
    return _gallery_from_masks(
        analysis["a_mask"], analysis["b_mask"], copy_a_only=True  # type: ignore[arg-type]
    )


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "leave the input unchanged": _rival_identity,
    "center-align the two cropped shapes": _rival_center_align,
    "use B-minus-A in the directional panel": _rival_b_minus_a,
    "keep every Boolean panel on the full shared canvas": _rival_uncropped_panels,
    "swap the union and intersection panels": _rival_swap_union_intersection,
    "recolor four copies of A": _rival_copy_a_four_times,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _profile_witness(profile: str) -> Callable[[Grid], bool]:
    return lambda grid: _analyze(grid).get("profile") == profile


def _rival_difference_witness(rival_name: str, *, profile: str | None = None) -> Callable[[Grid], bool]:
    rival = SEMANTIC_RIVALS[rival_name]

    def witness(grid) -> bool:
        analysis = _analyze(grid)
        if analysis["errors"]:
            return False
        if profile is not None and analysis["profile"] != profile:
            return False
        return analysis["truth"] != rival(grid)

    return witness


SEMANTIC_WITNESSES = {
    _PROFILE_PARTIAL_SAME: _profile_witness(_PROFILE_PARTIAL_SAME),
    _PROFILE_PARTIAL_MISMATCH: _profile_witness(_PROFILE_PARTIAL_MISMATCH),
    _PROFILE_A_SUBSET: _profile_witness(_PROFILE_A_SUBSET),
    _PROFILE_B_SUBSET: _profile_witness(_PROFILE_B_SUBSET),
    "top_left_alignment_matters": _rival_difference_witness(
        "center-align the two cropped shapes", profile=_PROFILE_PARTIAL_MISMATCH
    ),
    "directional_A_minus_B_matters": _rival_difference_witness(
        "use B-minus-A in the directional panel"
    ),
    "independent_panel_crops_matter": _rival_difference_witness(
        "keep every Boolean panel on the full shared canvas"
    ),
}

WITNESS_RIVALS = {
    _PROFILE_PARTIAL_SAME: ["swap the union and intersection panels", "recolor four copies of A"],
    _PROFILE_PARTIAL_MISMATCH: ["swap the union and intersection panels", "recolor four copies of A"],
    _PROFILE_A_SUBSET: ["swap the union and intersection panels", "recolor four copies of A"],
    _PROFILE_B_SUBSET: ["swap the union and intersection panels", "recolor four copies of A"],
    "top_left_alignment_matters": ["center-align the two cropped shapes"],
    "directional_A_minus_B_matters": ["use B-minus-A in the directional panel"],
    "independent_panel_crops_matter": ["keep every Boolean panel on the full shared canvas"],
}


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _PROFILES[sample_index % len(_PROFILES)]


def _draw_int_axis(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _draw_choice_axis(ctx, overrides, label: str, default: str, options: Sequence[str]) -> str:
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (default,))


def _build_pair(profile: str, rng, cap: int, difficulty) -> tuple[Mask, Mask]:
    for _ in range(200):
        if profile == _PROFILE_PARTIAL_SAME:
            a, b = _pair_partial_same(rng, cap, difficulty)
        elif profile == _PROFILE_PARTIAL_MISMATCH:
            a, b = _pair_partial_mismatch(rng, cap, difficulty)
        elif profile == _PROFILE_A_SUBSET:
            a, b = _proper_subset_pair(rng, cap, difficulty, a_is_subset=True)
        elif profile == _PROFILE_B_SUBSET:
            a, b = _proper_subset_pair(rng, cap, difficulty, a_is_subset=False)
        else:
            raise ValueError(f"unknown profile: {profile!r}")
        if _relation_profile(a, b) != profile:
            continue
        truth = _gallery_from_masks(a, b)
        if profile == _PROFILE_PARTIAL_MISMATCH and truth == _gallery_from_masks(a, b, align="center"):
            continue
        if truth == _gallery_from_masks(a, b, crop_panels=False):
            continue
        if profile in (_PROFILE_A_SUBSET, _PROFILE_B_SUBSET):
            if truth == _gallery_from_masks(a, b, difference_op="b_minus_a"):
                continue
        return a, b
    raise ValueError(f"could not build a discriminating {profile!r} shape pair")


def _place_pair(
    grid_h: int,
    grid_w: int,
    a_mask: Mask,
    b_mask: Mask,
    a_color: int,
    b_color: int,
    rng,
) -> Grid:
    ah, aw = len(a_mask), len(a_mask[0])
    bh, bw = len(b_mask), len(b_mask[0])
    min_width = aw + bw + 1
    if min_width > grid_w:
        raise ValueError(f"shape pair needs width {min_width}, grid_w is {grid_w}")
    if max(ah, bh) > grid_h:
        raise ValueError(f"shape pair needs height {max(ah, bh)}, grid_h is {grid_h}")

    extra = grid_w - aw - bw - 1
    extra_gap = rng.randint(0, min(2, extra))
    gap = 1 + extra_gap
    remaining = grid_w - aw - bw - gap
    left_margin = rng.randint(0, remaining)
    a_left = left_margin
    b_left = a_left + aw + gap
    a_top = rng.randint(0, grid_h - ah)
    b_top = rng.randint(0, grid_h - bh)

    grid = full_grid(grid_h, grid_w, 0)
    for r, c in _mask_cells(a_mask):
        grid[a_top + r][a_left + c] = a_color
    for r, c in _mask_cells(b_mask):
        grid[b_top + r][b_left + c] = b_color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic task input; the runner applies the Racket rule."""
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown!r}")

    default_h, default_w = _CANONICAL_DIMS[sample_index % len(_CANONICAL_DIMS)]
    default_profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    grid_h = _draw_int_axis(ctx, overrides, "grid_h", default_h, 8, 9)
    grid_w = _draw_int_axis(ctx, overrides, "grid_w", default_w, 11, 13)
    profile = _draw_choice_axis(ctx, overrides, "profile", default_profile, _PROFILES)
    a_color = ctx.draw_color("a_color", exclude={0})
    b_color = ctx.draw_color("b_color", exclude={0})

    cap = _difficulty_cap(difficulty, grid_h, grid_w)
    pair_rng = ctx.draw_rng("shape_pair")
    a_mask, b_mask = _build_pair(profile, pair_rng, cap, difficulty)
    grid = _place_pair(
        grid_h,
        grid_w,
        a_mask,
        b_mask,
        a_color,
        b_color,
        ctx.draw_rng("placement"),
    )

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    strict_errors = strict_canonical_like(grid)
    if strict_errors:
        raise ValueError(f"constructed non-canonical-like instance: {strict_errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "profile": profile,
        "a_color": a_color,
        "b_color": b_color,
    }
    if observed != expected:
        raise ValueError(f"constructed scene did not realize exact axes: {observed!r} != {expected!r}")
    return _copy_grid(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a named plausible rival survives with a new answer."""
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with the Boolean-gallery rule")

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query input is unlawful: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the Boolean-gallery rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"plausible rival survives every demo but changes the query: {name}")
    return reasons
