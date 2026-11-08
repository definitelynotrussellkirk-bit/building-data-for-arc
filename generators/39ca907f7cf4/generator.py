"""Generator for ARC task 39ca907f7cf4 — crop the nearest corner-marked object.

Exactly one non-zero singleton occupies a grid corner.  It is a control marker,
not an answer object.  Among the remaining monochrome 4-connected objects, the
Racket oracle chooses the one whose *nearest cell* has the smallest Manhattan
distance to the marked corner, then crops that object to its tight bounding box.

Every third ordinary draw is an exact linked canonical-profile anchor (modulo
color relabeling and D4 corner orientation).  The other draws use three equal-
size candidates and place the true target between earlier and later candidates.
One non-anchor residue in each three-sample curriculum block force a nearest-cell versus
centroid-distance disagreement; the third uses a broader polyomino vocabulary.
Across sequential samples the target alternates between the lowest and highest
candidate color.  Thus every three-demo lesson rebuts the strongest shortcuts
admitted by the canonical examples while retaining broad output diversity.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "39ca907f7cf4"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c2f0790b1442"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "A 0-background grid contains one singleton corner marker and two or three "
    "other monochrome 4-connected objects in distinct colors. Ignore the marker. "
    "Choose the candidate containing the cell with minimum Manhattan distance to "
    "the marked corner, requiring a unique winner, and output that candidate "
    "cropped to its tight bounding box with internal zeros preserved."
)

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "exactly one occupied corner exists and its component is a singleton marker",
    "there are 2..3 candidate components, all in distinct colors",
    "candidate components have 3..5 cells and the nearest-cell distance winner is unique",
    "every third ordinary sample matches a linked canonical input profile",
    "every sequential three-demo lesson rebuts reading-order, size, color-rank, centroid-distance, marker, and fixed-2x2 shortcuts",
]

_CORNERS = ("tl", "tr", "bl", "br")
AXES = {
    "grid_h": {"type": "int", "default": "difficulty/schedule 7..12", "valid": "7..12"},
    "grid_w": {"type": "int", "default": "difficulty/schedule 9..14", "valid": "9..14"},
    "n": {"type": "int", "default": "3 on anchors, otherwise 4", "valid": "3..4"},
    "marker_corner": {
        "type": "str",
        "default": "keyed choice over all four corners",
        "valid": "|".join(_CORNERS),
    },
    "target_size": {
        "type": "int",
        "default": "3/4 on anchors, otherwise 5",
        "valid": "3..5",
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_LINE3 = ((0, 0), (0, 1), (0, 2))
_L3 = ((0, 0), (0, 1), (1, 0))
_SQUARE4 = ((0, 0), (0, 1), (1, 0), (1, 1))
_T4 = ((0, 0), (0, 1), (0, 2), (1, 1))
_L4 = ((0, 0), (1, 0), (2, 0), (2, 1))
_LINE4 = ((0, 0), (0, 1), (0, 2), (0, 3))
_LINE5 = ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4))
_PLUS5 = ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1))
_P5 = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1))
_U5 = ((0, 0), (1, 0), (1, 1), (1, 2), (0, 2))
_SHAPES_BY_SIZE = {
    3: (_LINE3, _L3),
    4: (_SQUARE4, _T4, _L4, _LINE4),
    5: (_LINE5, _PLUS5, _P5, _U5),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_variants(shape: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    points = tuple(shape)
    variants = set()
    for mode in range(8):
        transformed = []
        for r, c in points:
            if mode == 0:
                rr, cc = r, c
            elif mode == 1:
                rr, cc = r, -c
            elif mode == 2:
                rr, cc = -r, c
            elif mode == 3:
                rr, cc = -r, -c
            elif mode == 4:
                rr, cc = c, r
            elif mode == 5:
                rr, cc = c, -r
            elif mode == 6:
                rr, cc = -c, r
            else:
                rr, cc = -c, -r
            transformed.append((rr, cc))
        variants.add(_normalize(transformed))
    return tuple(sorted(variants))


_VARIANTS_BY_SIZE = {
    size: tuple(sorted({variant for shape in shapes for variant in _shape_variants(shape)}))
    for size, shapes in _SHAPES_BY_SIZE.items()
}
_TARGET5_VARIANTS = tuple(sorted({
    variant
    for shape in (_LINE5, _P5, _U5)
    for variant in _shape_variants(shape)
}))
_COMPACT5_VARIANTS = tuple(
    sorted({variant for shape in (_PLUS5, _P5, _U5) for variant in _shape_variants(shape)})
)


def _corner_cell(h: int, w: int, corner: str) -> tuple[int, int]:
    return {
        "tl": (0, 0),
        "tr": (0, w - 1),
        "bl": (h - 1, 0),
        "br": (h - 1, w - 1),
    }[corner]


def _corner_name(h: int, w: int, cell: tuple[int, int]) -> str:
    names = {v: k for k, v in {
        "tl": (0, 0), "tr": (0, w - 1), "bl": (h - 1, 0), "br": (h - 1, w - 1)
    }.items()}
    return names[cell]


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells.sort()
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            components.append({
                "color": color,
                "cells": tuple(cells),
                "bbox": (min(rs), min(cs), max(rs), max(cs)),
                "size": len(cells),
                "key": cells[0],
            })
    components.sort(key=lambda obj: obj["key"])
    return components


def _distance(marker: tuple[int, int], obj: dict[str, Any]) -> int:
    mr, mc = marker
    return min(abs(mr - r) + abs(mc - c) for r, c in obj["cells"])


def _mean_distance(marker: tuple[int, int], obj: dict[str, Any]) -> float:
    mr, mc = marker
    return sum(abs(mr - r) + abs(mc - c) for r, c in obj["cells"]) / obj["size"]


def _crop(grid: list[list[int]], obj: dict[str, Any]) -> list[list[int]]:
    r1, c1, r2, c2 = obj["bbox"]
    out = full_grid(r2 - r1 + 1, c2 - c1 + 1, 0)
    for r, c in obj["cells"]:
        out[r - r1][c - c1] = grid[r][c]
    return out


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {"errors": errors}
    grid = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    components = _components(grid)
    colors = [obj["color"] for obj in components]
    corners = {(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)}
    occupied_corners = [cell for cell in sorted(corners) if grid[cell[0]][cell[1]] != 0]

    if not (7 <= h <= 12 and 9 <= w <= 14):
        errors.append(f"dims {h}x{w} outside declared envelope 7..12 x 9..14")
    if not (3 <= len(components) <= 4):
        errors.append(f"need 3..4 components including the marker, found {len(components)}")
    if len(colors) != len(set(colors)):
        errors.append("every component must use a distinct nonzero color")
    if len(occupied_corners) != 1:
        errors.append(f"need exactly one occupied corner, found {len(occupied_corners)}")

    marker_cell = occupied_corners[0] if len(occupied_corners) == 1 else None
    marker_obj = None
    if marker_cell is not None:
        marker_obj = next((obj for obj in components if marker_cell in obj["cells"]), None)
        if marker_obj is None:
            errors.append("occupied corner is not owned by a component")
        elif marker_obj["size"] != 1:
            errors.append(f"corner marker must be a singleton, found size {marker_obj['size']}")

    candidates = [obj for obj in components if obj is not marker_obj]
    for obj in candidates:
        if not (3 <= obj["size"] <= 5):
            errors.append(f"candidate size {obj['size']} outside 3..5")

    distances: list[tuple[int, dict[str, Any]]] = []
    best = None
    if marker_cell is not None and marker_obj is not None and candidates:
        distances = [(_distance(marker_cell, obj), obj) for obj in candidates]
        minimum = min(distance for distance, _ in distances)
        winners = [obj for distance, obj in distances if distance == minimum]
        if len(winners) != 1:
            errors.append(f"nearest-cell distance must have one winner, found {len(winners)}")
        else:
            best = winners[0]

    return {
        "errors": errors,
        "grid": grid,
        "height": h,
        "width": w,
        "objects": components,
        "marker_cell": marker_cell,
        "marker_obj": marker_obj,
        "marker_corner": _corner_name(h, w, marker_cell) if marker_cell is not None else None,
        "candidates": candidates,
        "distances": distances,
        "best": best,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, or rule-hiding nearest-object scenes."""
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Linked empirical manifold, allowing color relabeling and D4 corner symmetry."""
    analysis = _analyze(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    candidates = analysis["candidates"]
    sizes = tuple(sorted(obj["size"] for obj in candidates))
    bbox_dims = tuple(sorted((obj["bbox"][2] - obj["bbox"][0] + 1,
                              obj["bbox"][3] - obj["bbox"][1] + 1)
                             for obj in candidates))
    profile = (analysis["height"], analysis["width"], len(analysis["objects"]), sizes, bbox_dims)
    lawful = {
        (7, 9, 3, (3, 4), ((2, 2), (2, 2))),
        (8, 9, 3, (3, 3), ((2, 2), (2, 2))),
    }
    if profile not in lawful:
        reasons.append(
            "linked dimensions/component-count/candidate-size/bbox profile does not match a canonical train/test input"
        )
    return reasons


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Small test-only mirror of the selected Racket rule; never an output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _crop(analysis["grid"], analysis["best"])


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis from the returned input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n": len(analysis["objects"]),
        "marker_corner": analysis["marker_corner"],
        "target_size": analysis["best"]["size"],
    }


def _translate(shape: tuple[tuple[int, int], ...], r0: int, c0: int) -> frozenset[tuple[int, int]]:
    return frozenset((r0 + r, c0 + c) for r, c in shape)


def _placements(shape: tuple[tuple[int, int], ...], h: int, w: int) -> list[frozenset[tuple[int, int]]]:
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    return [_translate(shape, r0, c0)
            for r0 in range(h - sh + 1)
            for c0 in range(w - sw + 1)]


def _cells_distance(marker: tuple[int, int], cells: frozenset[tuple[int, int]]) -> int:
    mr, mc = marker
    return min(abs(mr - r) + abs(mc - c) for r, c in cells)


def _cells_mean_distance(marker: tuple[int, int], cells: frozenset[tuple[int, int]]) -> float:
    mr, mc = marker
    return sum(abs(mr - r) + abs(mc - c) for r, c in cells) / len(cells)


@lru_cache(maxsize=None)
def _placement_groups(
    shapes: tuple[tuple[tuple[int, int], ...], ...],
    h: int,
    w: int,
) -> tuple[tuple[frozenset[tuple[int, int]], ...], ...]:
    """Cache immutable legal placement catalogs shared by all generated draws."""
    corners = {_corner_cell(h, w, name) for name in _CORNERS}
    return tuple(
        tuple(cells for cells in _placements(shape, h, w) if not (cells & corners))
        for shape in shapes
    )


@lru_cache(maxsize=None)
def _placement_catalog(
    shapes: tuple[tuple[tuple[int, int], ...], ...],
    h: int,
    w: int,
) -> tuple[frozenset[tuple[int, int]], ...]:
    return tuple(cells for group in _placement_groups(shapes, h, w) for cells in group)


def _stable_cells_key(cells: frozenset[tuple[int, int]], salt: int) -> int:
    """Portable pseudo-random ordering without touching process RNG state."""
    value = salt & ((1 << 64) - 1)
    for r, c in sorted(cells):
        value ^= (r + 1) * 0x9E3779B185EBCA87
        value = (value * 0xC2B2AE3D27D4EB4F + c + 1) & ((1 << 64) - 1)
    return value


@lru_cache(maxsize=None)
def _semantic_layout_cached(
    h: int,
    w: int,
    corner: str,
) -> tuple[frozenset, tuple[frozenset, frozenset]]:
    """Cache one prevalidated centroid-disagreement layout per geometry."""
    marker = _corner_cell(h, w, corner)
    target_options = list(_placement_catalog(_TARGET5_VARIANTS, h, w))
    distractor_options = list(_placement_catalog(_COMPACT5_VARIANTS, h, w))
    stable_seed = h * 100_000 + w * 1_000 + _CORNERS.index(corner)
    target_options.sort(key=lambda cells: _stable_cells_key(cells, stable_seed))
    distractor_options.sort(key=lambda cells: _stable_cells_key(cells, stable_seed + 0x517CC1B727220A95))

    for target in target_options:
        target_key = min(target)
        target_distance = _cells_distance(marker, target)
        target_mean = _cells_mean_distance(marker, target)
        before = []
        after = []
        for cells in distractor_options:
            if cells & target or _cells_distance(marker, cells) <= target_distance:
                continue
            if min(cells) < target_key:
                before.append(cells)
            elif min(cells) > target_key:
                after.append(cells)
        for first in before:
            if (_cells_mean_distance(marker, first), min(first)) > (target_mean, target_key):
                continue
            last = next((cells for cells in after if not (first & cells)), None)
            if last is not None:
                return target, (first, last)
    raise ValueError(f"could not realize shortcut-rebutting layout for {h}x{w} {corner}")


def _find_semantic_layout(h: int, w: int, corner: str, rng) -> tuple[frozenset, list[frozenset]]:
    """Return the cached size-5 layout with a centroid disagreement."""
    del rng  # Layout diversity comes from dimensions/corner; palette remains keyed.
    target, distractors = _semantic_layout_cached(h, w, corner)
    return target, list(distractors)


def _find_broad_layout(
    h: int,
    w: int,
    corner: str,
    rng,
) -> tuple[frozenset, list[frozenset]]:
    """Find a diverse size-5 target bracketed in reading order by two rivals."""
    marker = _corner_cell(h, w, corner)
    placement_groups = [list(group) for group in _placement_groups(_VARIANTS_BY_SIZE[5], h, w)]
    all_placements = _placement_catalog(_VARIANTS_BY_SIZE[5], h, w)
    rng.shuffle(placement_groups)

    # Choose the target shape before its position so rare polyominoes are not
    # swamped by shapes with more legal translations.
    for shape_placements in placement_groups:
        rng.shuffle(shape_placements)
        for target in shape_placements:
            target_key = min(target)
            target_distance = _cells_distance(marker, target)
            before = [
                cells for cells in all_placements
                if not (cells & target)
                and _cells_distance(marker, cells) > target_distance
                and min(cells) < target_key
            ]
            after = [
                cells for cells in all_placements
                if not (cells & target)
                and _cells_distance(marker, cells) > target_distance
                and min(cells) > target_key
            ]
            rng.shuffle(before)
            rng.shuffle(after)
            for first in before[:120]:
                last = next((cells for cells in after[:120] if not (first & cells)), None)
                if last is not None:
                    return target, [first, last]
    raise ValueError(f"could not realize broad shortcut-rebutting layout for {h}x{w} {corner}")


def _find_generic_layout(
    h: int,
    w: int,
    n: int,
    corner: str,
    target_size: int,
    rng,
) -> tuple[frozenset, list[frozenset]]:
    """Realize exact overrides while preserving a unique nearest designated target."""
    marker = _corner_cell(h, w, corner)
    variants = _VARIANTS_BY_SIZE[target_size]
    all_placements = list(_placement_catalog(variants, h, w))
    rng.shuffle(all_placements)
    all_placements.sort(key=lambda cells: _cells_distance(marker, cells))

    for target in all_placements:
        target_distance = _cells_distance(marker, target)
        candidates = [
            cells for cells in all_placements
            if not (cells & target) and _cells_distance(marker, cells) > target_distance
        ]
        rng.shuffle(candidates)
        chosen: list[frozenset] = []
        for cells in candidates:
            if all(not (cells & other) for other in chosen):
                chosen.append(cells)
                if len(chosen) == n - 2:
                    return target, chosen
    raise ValueError(
        f"could not realize exact layout h={h} w={w} n={n} corner={corner} target_size={target_size}"
    )


def _orient_from_tl(cells: Iterable[tuple[int, int]], h: int, w: int, corner: str):
    if corner == "tl":
        return frozenset(cells)
    if corner == "tr":
        return frozenset((r, w - 1 - c) for r, c in cells)
    if corner == "bl":
        return frozenset((h - 1 - r, c) for r, c in cells)
    return frozenset((h - 1 - r, w - 1 - c) for r, c in cells)


def _anchor_layout(h: int, target_size: int, corner: str):
    if (h, target_size) == (7, 4):
        target = {(1, 3), (1, 4), (2, 3), (2, 4)}
        distractor = {(4, 6), (4, 7), (5, 7)}
    elif (h, target_size) == (8, 3):
        target = {(2, 3), (2, 4), (3, 4)}
        distractor = {(5, 7), (5, 8), (6, 8)}
    else:
        raise ValueError("unsupported canonical anchor profile")
    return _orient_from_tl(target, h, 9, corner), [_orient_from_tl(distractor, h, 9, corner)]


def _draw_axis_int(ctx, label: str, lo: int, hi: int, default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _paint_scene(
    h: int,
    w: int,
    marker_corner: str,
    target: frozenset[tuple[int, int]],
    distractors: list[frozenset[tuple[int, int]]],
    rng,
    color_phase: int,
) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    marker = _corner_cell(h, w, marker_corner)
    all_colors = rng.sample(range(1, 10), 2 + len(distractors))
    marker_color = all_colors[0]
    candidate_colors = sorted(all_colors[1:])

    # Alternate the target between the lowest and highest candidate color.
    target_color = candidate_colors[0] if color_phase % 2 == 0 else candidate_colors[-1]
    remaining_colors = [color for color in candidate_colors if color != target_color]
    rng.shuffle(remaining_colors)

    grid[marker[0]][marker[1]] = marker_color
    for r, c in target:
        grid[r][c] = target_color
    for cells, color in zip(distractors, remaining_colors):
        for r, c in cells:
            grid[r][c] = color
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _band(difficulty)
    phase = int(seed) + int(sample_index)
    anchor = not overrides and phase % 3 == 0

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")

    if anchor:
        anchor_variant = (phase // 3) % 2
        default_h = 7 if anchor_variant == 0 else 8
        default_target_size = 4 if anchor_variant == 0 else 3
        h = _draw_axis_int(ctx, "grid_h", 7, 12, default_h, default_h)
        w = _draw_axis_int(ctx, "grid_w", 9, 14, 9, 9)
        n = _draw_axis_int(ctx, "n", 3, 4, 3, 3)
        target_size = _draw_axis_int(ctx, "target_size", 3, 5, default_target_size, default_target_size)
    else:
        defaults = {
            "easy": (7, 8, 9, 10),
            "medium": (8, 10, 10, 12),
            "hard": (10, 12, 12, 14),
        }[band]
        h = _draw_axis_int(ctx, "grid_h", 7, 12, defaults[0], defaults[1])
        w = _draw_axis_int(ctx, "grid_w", 9, 14, defaults[2], defaults[3])
        n = _draw_axis_int(ctx, "n", 3, 4, 4, 4)
        target_size = _draw_axis_int(ctx, "target_size", 3, 5, 5, 5)

    marker_corner = ctx.draw_choice("marker_corner", _CORNERS)

    if anchor:
        target, distractors = _anchor_layout(h, target_size, marker_corner)
    elif n == 4 and target_size == 5 and phase % 3 == 2:
        target, distractors = _find_broad_layout(h, w, marker_corner, layout_rng)
    elif n == 4 and target_size == 5:
        target, distractors = _find_semantic_layout(h, w, marker_corner, layout_rng)
    else:
        target, distractors = _find_generic_layout(
            h, w, n, marker_corner, target_size, layout_rng
        )

    grid = _paint_scene(
        h, w, marker_corner, target, distractors, palette_rng, phase
    )
    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("generated invalid nearest-object lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "n": n,
        "marker_corner": marker_corner,
        "target_size": target_size,
    }
    if observed != expected:
        raise AssertionError(f"axis realization drift: expected {expected}, observed {observed}")
    return grid


def _valid_analysis(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _crop_choice(grid, chooser: Callable[[dict[str, Any]], dict[str, Any] | None]):
    analysis = _valid_analysis(grid)
    if analysis is None:
        return None
    chosen = chooser(analysis)
    return None if chosen is None else _crop(analysis["grid"], chosen)


def _rival_first_candidate(grid):
    return _crop_choice(grid, lambda a: min(a["candidates"], key=lambda obj: obj["key"]))


def _rival_last_candidate(grid):
    return _crop_choice(grid, lambda a: max(a["candidates"], key=lambda obj: obj["key"]))


def _rival_smallest_candidate(grid):
    return _crop_choice(grid, lambda a: min(a["candidates"], key=lambda obj: (obj["size"], obj["key"])))


def _rival_largest_candidate(grid):
    return _crop_choice(grid, lambda a: min(a["candidates"], key=lambda obj: (-obj["size"], obj["key"])))


def _rival_lowest_color(grid):
    return _crop_choice(grid, lambda a: min(a["candidates"], key=lambda obj: (obj["color"], obj["key"])))


def _rival_highest_color(grid):
    return _crop_choice(grid, lambda a: min(a["candidates"], key=lambda obj: (-obj["color"], obj["key"])))


def _rival_centroid_distance(grid):
    return _crop_choice(
        grid,
        lambda a: min(
            a["candidates"],
            key=lambda obj: (_mean_distance(a["marker_cell"], obj), obj["key"]),
        ),
    )


def _rival_marker_as_answer(grid):
    return _crop_choice(grid, lambda a: a["marker_obj"])


def _rival_fixed_2x2(grid):
    analysis = _valid_analysis(grid)
    if analysis is None:
        return None
    true = _crop(analysis["grid"], analysis["best"])
    out = full_grid(2, 2, 0)
    for r in range(min(2, len(true))):
        for c in range(min(2, len(true[0]))):
            out[r][c] = true[r][c]
    return out


def _disagrees(grid, rival: Callable) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and rival(grid) != _crop(analysis["grid"], analysis["best"]))


def _marker_is(corner: str):
    return lambda grid: bool((analysis := _valid_analysis(grid)) and analysis["marker_corner"] == corner)


SEMANTIC_WITNESSES = {
    "canonical_profile_anchor": lambda grid: strict_canonical_like(grid) == [],
    "marker_top_left": _marker_is("tl"),
    "marker_top_right": _marker_is("tr"),
    "marker_bottom_left": _marker_is("bl"),
    "marker_bottom_right": _marker_is("br"),
    "reading_order_first_rebutted": lambda grid: _disagrees(grid, _rival_first_candidate),
    "reading_order_last_rebutted": lambda grid: _disagrees(grid, _rival_last_candidate),
    "smallest_size_rebutted": lambda grid: _disagrees(grid, _rival_smallest_candidate),
    "largest_size_rebutted": lambda grid: _disagrees(grid, _rival_largest_candidate),
    "lowest_color_rebutted": lambda grid: _disagrees(grid, _rival_lowest_color),
    "highest_color_rebutted": lambda grid: _disagrees(grid, _rival_highest_color),
    "centroid_distance_rebutted": lambda grid: _disagrees(grid, _rival_centroid_distance),
    "marker_as_answer_rebutted": lambda grid: _disagrees(grid, _rival_marker_as_answer),
    "fixed_2x2_crop_rebutted": lambda grid: _disagrees(grid, _rival_fixed_2x2),
}

SEMANTIC_RIVALS = {
    "first_candidate": _rival_first_candidate,
    "last_candidate": _rival_last_candidate,
    "smallest_candidate": _rival_smallest_candidate,
    "largest_candidate": _rival_largest_candidate,
    "lowest_color": _rival_lowest_color,
    "highest_color": _rival_highest_color,
    "nearest_centroid": _rival_centroid_distance,
    "marker_as_answer": _rival_marker_as_answer,
    "fixed_2x2_crop": _rival_fixed_2x2,
}

WITNESS_RIVALS = {
    "reading_order_first_rebutted": ["first_candidate"],
    "reading_order_last_rebutted": ["last_candidate"],
    "smallest_size_rebutted": ["smallest_candidate"],
    "largest_size_rebutted": ["largest_candidate"],
    "lowest_color_rebutted": ["lowest_color"],
    "highest_color_rebutted": ["highest_color"],
    "centroid_distance_rebutted": ["nearest_centroid"],
    "marker_as_answer_rebutted": ["marker_as_answer"],
    "fixed_2x2_crop_rebutted": ["fixed_2x2_crop"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "first_candidate": _rival_first_candidate,
    "fixed_2x2_crop": _rival_fixed_2x2,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject any lesson where a named plausible rival survives the demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the rule domain: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with nearest-cell crop rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, ValueError) as exc:
        reasons.append(f"query is outside the rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo.get("output") for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule '{name}' fits every demo but answers the query differently"
            )
    return reasons
