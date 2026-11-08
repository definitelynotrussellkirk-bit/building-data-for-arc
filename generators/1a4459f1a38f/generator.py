"""Generator for ARC task 1a4459f1a38f — crop the largest component.

The input is a black grid containing two to four separated monochrome
4-connected components.  Exactly one component has the greatest cell count.
The answer is the original-grid crop of that component's bounding box, with
its color and any background holes/indentations preserved.

The four-sample lesson schedule deliberately includes: a canonical hollow
frame, a larger-bounding-box decoy with fewer cells, a repeated-color decoy,
and an irregular/non-square target at a different reading-order position.
The repeated-color and irregular slots also place a same-color distractor at
diagonal contact, so 4-connectivity and 8-connectivity disagree.  The irregular
slot repeats the bbox and modal-color counterexamples so every sliding
three-demo window identifies the intended rule, not only windows aligned to
the four-slot schedule.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1a4459f1a38f"
TASK_ID = "1a4459f1a38f"
VERSION = "4.1.1"
RULE_HASH = "f1a4398aee4e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "On background 0, find the same-color 4-connected components. Select the "
    "unique component with the greatest CELL COUNT, breaking no tie because "
    "generated lessons forbid ties. Return the rectangular crop of the "
    "ORIGINAL input at that component's bounding box, preserving its color "
    "and all background holes or indentations. Distractors remain outside the "
    "selected bounding box. A four-position lesson schedule includes canonical "
    "3x3/4x4 hollow frames, a larger-bbox-but-smaller decoy, a second component "
    "sharing the target color, and irregular non-square targets in varied "
    "reading-order positions."
)

INVARIANTS = [
    "background is 0",
    "there are 2 to 4 separated same-color 4-connected components",
    "one component is uniquely largest by cell count",
    "the selected component's bbox contains background, so cropping is visible",
    "no distractor cell lies inside the selected component's bounding box",
    "the crop preserves the original colors and background cells",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware 10..14",
        "valid": "10..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware 10..16",
        "valid": "10..16",
    },
    "component_count": {
        "type": "int",
        "default": "2..4 (canonical schedule fixes 3)",
        "valid": "2..4",
    },
}

_DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
_DIRS8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)
_DIAGONALS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

# Every target template is connected, spans its bbox, and leaves at least one
# background cell inside that bbox.  Rotations/reflections provide texture
# variation without changing the exact largest_size axis.
_BASE_SHAPES: dict[int, frozenset[tuple[int, int]]] = {
    1: frozenset({(0, 0)}),
    2: frozenset({(0, 0), (0, 1)}),
    3: frozenset({(0, 0), (1, 0), (1, 1)}),
    4: frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    5: frozenset({(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}),
    6: frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)}),
    7: frozenset({(0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1), (2, 2)}),
    8: frozenset({
        (0, 0), (0, 1), (0, 2),
        (1, 0),         (1, 2),
        (2, 0), (2, 1), (2, 2),
    }),
    9: frozenset({
        (0, 0), (0, 1), (0, 2), (0, 3),
        (1, 0),
        (2, 0), (2, 1), (2, 2), (2, 3),
    }),
    10: frozenset({
        (0, 0), (0, 1), (0, 2), (0, 3),
        (1, 0),                         (1, 3),
        (2, 0), (2, 1), (2, 2), (2, 3),
    }),
    11: frozenset({
                (0, 1), (0, 2), (0, 3),
        (1, 0),                   (1, 3),
        (2, 0),                   (2, 3),
        (3, 0), (3, 1), (3, 2), (3, 3),
    }),
    12: frozenset({
        (0, 0), (0, 1), (0, 2), (0, 3),
        (1, 0),                   (1, 3),
        (2, 0),                   (2, 3),
        (3, 0), (3, 1), (3, 2), (3, 3),
    }),
}

# Seven cells, but a 4x4 bbox: this is the explicit bbox-area shortcut decoy.
_BBOX_DECOY = frozenset({
    (0, 0),
    (1, 0), (1, 1),
            (2, 1), (2, 2),
                    (3, 2), (3, 3),
})


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_area(cells) -> int:
    r0, c0, r1, c1 = _bbox(cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1)


def _normalize(cells):
    r0, c0, _, _ = _bbox(cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _dihedral(shape):
    variants = set()
    current = set(shape)
    for _ in range(4):
        variants.add(_normalize(current))
        variants.add(_normalize({(r, -c) for r, c in current}))
        current = {(c, -r) for r, c in current}
    return tuple(sorted(variants, key=lambda s: sorted(s)))


def _shape_for_size(size: int, rng):
    return rng.choice(_dihedral(_BASE_SHAPES[size]))


def _random_target_shape(
    size: int, rng, *, require_non_square: bool = False
) -> frozenset[tuple[int, int]]:
    """Grow a bounded connected polyomino with visible bbox background."""
    for _ in range(256):
        cells = {(0, 0)}
        while len(cells) < size:
            r, c = rng.choice(sorted(cells))
            dr, dc = rng.choice(_DIRS4)
            candidate = (r + dr, c + dc)
            trial = cells | {candidate}
            normalized = _normalize(trial)
            _, _, r1, c1 = _bbox(normalized)
            if r1 + 1 > 5 or c1 + 1 > 5:
                continue
            cells.add(candidate)
        shape = _normalize(cells)
        r0, c0, r1, c1 = _bbox(shape)
        height, width = r1 - r0 + 1, c1 - c0 + 1
        if height * width <= size:
            continue
        if require_non_square and height == width:
            continue
        obj = {"bbox": (r0, c0, r1, c1), "cells": tuple(shape)}
        if _hollow_frame(obj):
            continue
        return shape
    fallback = _shape_for_size(size, rng)
    r0, c0, r1, c1 = _bbox(fallback)
    if require_non_square and (r1 - r0) == (c1 - c0):
        fallback = _BASE_SHAPES[9]
    return fallback


def _components(grid, *, connectivity: int = 4):
    """Same-color components under explicit 4- or 8-connectivity."""
    if connectivity == 4:
        directions = _DIRS4
    elif connectivity == 8:
        directions = _DIRS8
    else:
        raise ValueError(f"unsupported connectivity {connectivity!r}")
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in directions:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({
                "color": color,
                "cells": tuple(cells),
                "size": len(cells),
                "bbox": _bbox(cells),
            })
    return result


def _hollow_frame(obj) -> bool:
    r0, c0, r1, c1 = obj["bbox"]
    h, w = r1 - r0 + 1, c1 - c0 + 1
    if h < 3 or w < 3:
        return False
    expected = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    return set(obj["cells"]) == expected


def _largest_object(grid, *, connectivity: int = 4):
    components = _components(grid, connectivity=connectivity)
    if not components:
        return None
    return min(
        components,
        key=lambda obj: (-obj["size"], obj["bbox"][0], obj["bbox"][1]),
    )


def _crop(grid, bbox):
    r0, c0, r1, c1 = bbox
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def observe_overrides(grid) -> dict[str, int]:
    components = _components(grid)
    largest = _largest_object(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "component_count": len(components),
        "largest_size": 0 if largest is None else largest["size"],
        "foreground_colors": len({obj["color"] for obj in components}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the teaching grammar, not merely grid shape/palette."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    h = len(grid)
    errors = []
    if not (1 <= h <= 30 and 1 <= width <= 30):
        errors.append(f"grid outside ARC bounds: {h}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors

    components = _components(grid)
    if not (2 <= len(components) <= 4):
        errors.append(f"expected 2..4 components, got {len(components)}")
    if not components:
        return errors

    sizes = sorted((obj["size"] for obj in components), reverse=True)
    if len(sizes) < 2 or sizes[0] == sizes[1]:
        errors.append("largest component must be unique by cell count")
    largest = _largest_object(grid)
    if largest is None:
        return errors
    if largest["size"] < 6:
        errors.append(f"largest component too small to teach cropping: {largest['size']}")
    if _bbox_area(largest["cells"]) <= largest["size"]:
        errors.append("largest component fills its bbox; crop would hide shape/background preservation")
    r0, c0, r1, c1 = largest["bbox"]
    if (r1 - r0 + 1) == h and (c1 - c0 + 1) == width:
        errors.append("largest bbox equals the entire input")
    largest_cells = set(largest["cells"])
    largest_key = (largest["color"], frozenset(largest["cells"]))
    for obj in components:
        if (obj["color"], frozenset(obj["cells"])) == largest_key:
            continue
        if any(
            r0 <= r <= r1 and c0 <= c <= c1
            for r, c in obj["cells"]
        ):
            errors.append("a distractor lies inside the selected bounding box")
            break
        orthogonally_touches = any(
            (r + dr, c + dc) in largest_cells
            for r, c in obj["cells"]
            for dr, dc in _DIRS4
        )
        diagonally_touches = any(
            (r + dr, c + dc) in largest_cells
            for r, c in obj["cells"]
            for dr, dc in _DIAGONALS
        )
        if orthogonally_touches or (
            diagonally_touches and obj["color"] != largest["color"]
        ):
            errors.append(
                "a distractor touches the largest component outside the allowed "
                "same-color diagonal 4-connectivity witness"
            )
            break
    color_count = len({obj["color"] for obj in components})
    if not (2 <= color_count <= 3):
        errors.append(f"expected 2..3 foreground colors, got {color_count}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Recognize the actual five-example canonical manifold."""
    reasons = []
    if not grid or not grid[0]:
        return ["empty grid"]
    if (len(grid), len(grid[0])) != (10, 10):
        reasons.append("canonical canvas is 10x10")
    components = _components(grid)
    if len(components) != 3:
        reasons.append("canonical scenes have exactly three components")
        return reasons
    if len({obj["color"] for obj in components}) != 3:
        reasons.append("canonical components use three distinct foreground colors")
    sizes = sorted((obj["size"] for obj in components), reverse=True)
    if sizes[0] == sizes[1]:
        reasons.append("canonical largest component is unique")
    largest = _largest_object(grid)
    if largest is None or not _hollow_frame(largest):
        reasons.append("canonical target is a hollow rectangular frame")
    elif largest["size"] not in (8, 12):
        reasons.append("canonical target is a 3x3 or 4x4 frame")
    if largest is not None:
        r0, c0, r1, c1 = largest["bbox"]
        if any(
            (obj["color"], frozenset(obj["cells"]))
            != (largest["color"], frozenset(largest["cells"]))
            and any(r0 <= r <= r1 and c0 <= c <= c1 for r, c in obj["cells"])
            for obj in components
        ):
            reasons.append("canonical distractors stay outside the target bbox")
    if any(
        obj["size"] not in range(4, 7)
        for obj in components
        if (obj["color"], frozenset(obj["cells"]))
        != (largest["color"], frozenset(largest["cells"]))
    ):
        reasons.append("canonical distractors have 4..6 cells")
    return reasons


def _is_bbox_decoy(grid) -> bool:
    components = _components(grid)
    largest = _largest_object(grid)
    if largest is None:
        return False
    area = _bbox_area(largest["cells"])
    return any(
        (obj["color"], frozenset(obj["cells"]))
        != (largest["color"], frozenset(largest["cells"]))
        and obj["size"] < largest["size"]
        and _bbox_area(obj["cells"]) > area
        for obj in components
    )


def _repeated_largest_color(grid) -> bool:
    components = _components(grid)
    largest = _largest_object(grid)
    return bool(
        largest
        and sum(obj["color"] == largest["color"] for obj in components) >= 2
    )


def _largest_rank(grid) -> tuple[int, int] | None:
    components = _components(grid)
    largest = _largest_object(grid)
    if largest is None:
        return None
    ordered = sorted(components, key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))
    return ordered.index(largest), len(ordered)


def _largest_first(grid) -> bool:
    rank = _largest_rank(grid)
    return bool(rank and rank[0] == 0)


def _largest_last(grid) -> bool:
    rank = _largest_rank(grid)
    return bool(rank and rank[0] == rank[1] - 1)


def _irregular_largest(grid) -> bool:
    largest = _largest_object(grid)
    return bool(largest and not _hollow_frame(largest))


def _non_square_crop(grid) -> bool:
    largest = _largest_object(grid)
    if largest is None:
        return False
    r0, c0, r1, c1 = largest["bbox"]
    return (r1 - r0) != (c1 - c0)


def _four_vs_eight_connectivity(grid) -> bool:
    largest_four = _largest_object(grid, connectivity=4)
    largest_eight = _largest_object(grid, connectivity=8)
    if largest_four is None or largest_eight is None:
        return False
    return _crop(grid, largest_four["bbox"]) != _crop(grid, largest_eight["bbox"])


def _canonical_frame_size(grid, size: int) -> bool:
    largest = _largest_object(grid)
    return bool(
        not strict_canonical_like(grid)
        and largest
        and largest["size"] == size
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    # Keep this contract rival-backed.  Descriptive curriculum/profile checks
    # belong in focused tests; semantic witnesses must prove disagreement with
    # a named shortcut under the after-phase gate.
    "larger_bbox_smaller_cells_decoy": _is_bbox_decoy,
    "target_color_repeated_in_distractor": _repeated_largest_color,
    "irregular_non_frame_target": _irregular_largest,
    "four_connected_not_eight_connected": _four_vs_eight_connectivity,
}


def _draw_axis_int(ctx, overrides, name, band_lo, band_hi, global_lo, global_hi):
    if overrides.get(name) is not None:
        return ctx.draw_int(name, global_lo, global_hi)
    return ctx.draw_int(name, band_lo, band_hi)


def _shape_cells(shape, top, left):
    return frozenset((top + r, left + c) for r, c in shape)


def _placement_candidates(shape, h, w):
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    return [
        _shape_cells(shape, top, left)
        for top in range(h - sh + 1)
        for left in range(w - sw + 1)
    ]


def _bboxes_overlap(a, b) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _reading_rank(placements) -> int:
    order = sorted(
        range(len(placements)),
        key=lambda index: (_bbox(placements[index])[0], _bbox(placements[index])[1]),
    )
    return order.index(0)


def _place_shapes(
    h,
    w,
    shapes,
    rng,
    *,
    target_rank="any",
    target_diagonal_touch=False,
):
    """Backtracking placement with a clean target bbox.

    Ordinary components have an 8-neighbor moat.  When
    ``target_diagonal_touch`` is true, component 1 must touch component 0 only
    diagonally.  They therefore remain distinct under the task's 4-connectivity
    while merging under the explicit 8-connectivity rival.
    """
    candidate_lists = [_placement_candidates(shape, h, w) for shape in shapes]
    for candidates in candidate_lists:
        rng.shuffle(candidates)

    def rank_possible(main_cells, mode):
        top, left, _, _ = _bbox(main_cells)
        if mode == "first":
            return top <= h // 2
        if mode == "last":
            return top >= h // 3
        if mode == "middle":
            return 0 < top < h - 1
        return True

    main_candidates = [
        cells for cells in candidate_lists[0]
        if rank_possible(cells, target_rank)
    ]
    rng.shuffle(main_candidates)

    for main_cells in main_candidates:
        placements = [main_cells]
        occupied = set(main_cells)
        main_bbox = _bbox(main_cells)

        def rec(index):
            if index == len(shapes):
                rank = _reading_rank(placements)
                if target_rank == "first" and rank != 0:
                    return None
                if target_rank == "last" and rank != len(placements) - 1:
                    return None
                if target_rank == "middle" and rank in (0, len(placements) - 1):
                    return None
                return list(placements)
            for cells in candidate_lists[index]:
                if _bboxes_overlap(_bbox(cells), main_bbox):
                    continue
                if cells & occupied:
                    continue
                diagonal_pair = target_diagonal_touch and index == 1
                if diagonal_pair:
                    if any(
                        (r + dr, c + dc) in occupied
                        for r, c in cells
                        for dr, dc in _DIRS4
                    ):
                        continue
                    if not any(
                        (r + dr, c + dc) in main_cells
                        for r, c in cells
                        for dr, dc in _DIAGONALS
                    ):
                        continue
                elif any(
                    (r + dr, c + dc) in occupied
                    for r, c in cells
                    for dr, dc in _DIRS8
                ):
                    continue
                placements.append(cells)
                occupied.update(cells)
                result = rec(index + 1)
                if result is not None:
                    return result
                placements.pop()
                occupied.difference_update(cells)
            return None

        result = rec(1)
        if result is not None:
            return result
    raise ValueError(
        f"cannot place component shapes in {h}x{w} with target_rank={target_rank}"
    )


def _component_sizes(largest_size, component_count, *, branch):
    if branch == "canonical":
        return [largest_size, 4, 5] if largest_size == 8 else [largest_size, 5, 6]
    if branch == "bbox_decoy":
        sizes = [largest_size, largest_size - 1]
        while len(sizes) < component_count:
            sizes.append(max(1, largest_size - 3 - len(sizes)))
        return sizes
    if branch == "irregular":
        sizes = [largest_size, 7]
        while len(sizes) < component_count:
            sizes.append(max(1, largest_size - len(sizes) - 2))
        return sizes
    candidates = [largest_size - 1, largest_size - 3, largest_size - 4]
    sizes = [largest_size]
    for size in candidates:
        if len(sizes) >= component_count:
            break
        sizes.append(max(1, size))
    while len(sizes) < component_count:
        sizes.append(max(1, largest_size - len(sizes) - 1))
    return sizes


def _assign_colors(colors, component_count, *, repeat_target):
    if len(colors) > component_count:
        raise ValueError(
            f"foreground_colors={len(colors)} exceeds component_count={component_count}"
        )
    assigned = [colors[0]]
    remaining = list(colors[1:])
    if repeat_target and component_count > 1:
        assigned.append(colors[0])
    while len(assigned) < component_count and remaining:
        assigned.append(remaining.pop(0))
    cycle = list(colors[1:] or colors)
    index = 0
    while len(assigned) < component_count:
        assigned.append(cycle[index % len(cycle)])
        index += 1
    if len(set(assigned)) != len(colors):
        raise RuntimeError("failed to realize requested foreground color count")
    return assigned


CURRICULUM_SCHEDULE = (
    "canonical",
    "bbox_decoy",
    "repeated_color",
    "irregular",
)


def _branch_defaults(ctx, sample_index, band, explicit):
    slot = int(sample_index) % (EXAMPLES_NEEDED + 1)
    episode = int(sample_index) // (EXAMPLES_NEEDED + 1)
    if explicit:
        return "general", slot, episode
    return CURRICULUM_SCHEDULE[slot], slot, episode


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    unknown = sorted(
        key for key, value in overrides.items()
        if value is not None and key not in AXES
    )
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty or "medium"
    explicit = {key for key, value in overrides.items() if value is not None}
    branch, slot, episode = _branch_defaults(ctx, sample_index, band, explicit)

    if branch == "canonical":
        h = ctx.draw_int("grid_h", 10, 10)
        w = ctx.draw_int("grid_w", 10, 10)
        component_count = ctx.draw_int("component_count", 3, 3)
        largest_size = ctx.draw_int("largest_size", 8 if episode % 2 == 0 else 12,
                                    8 if episode % 2 == 0 else 12)
        foreground_colors = ctx.draw_int("foreground_colors", 3, 3)
    else:
        h_ranges = {"easy": (10, 11), "medium": (10, 13), "hard": (12, 14)}
        w_ranges = {"easy": (10, 12), "medium": (11, 14), "hard": (13, 16)}
        size_ranges = {"easy": (6, 9), "medium": (7, 11), "hard": (9, 12)}
        ten_by_ten_anchor = (
            branch in ("bbox_decoy", "irregular") and episode % 2 == 0
        )
        canonical_palette_anchor = branch == "bbox_decoy" and episode % 2 == 0
        if ten_by_ten_anchor:
            h = ctx.draw_int("grid_h", 10, 10)
            w = ctx.draw_int("grid_w", 10, 10)
        else:
            h = _draw_axis_int(ctx, overrides, "grid_h", *h_ranges[band], 10, 14)
            w = _draw_axis_int(ctx, overrides, "grid_w", *w_ranges[band], 10, 16)

        if overrides.get("component_count") is not None:
            component_count = ctx.draw_int("component_count", 2, 4)
        elif branch in ("bbox_decoy", "repeated_color", "irregular"):
            component_count = ctx.draw_int("component_count", 3, 3)
        else:
            component_count = ctx.draw_int("component_count", 2, 4)

        if branch in ("repeated_color", "irregular"):
            foreground_colors = ctx.draw_int("foreground_colors", 2, 2)
        elif canonical_palette_anchor:
            # Preserve exact 10x10 + three-foreground-color canonical mass in
            # a branch that does not need a repeated target color.
            foreground_colors = ctx.draw_int("foreground_colors", 3, 3)
        else:
            foreground_colors = ctx.draw_int("foreground_colors", 2, min(3, component_count))

        if branch == "bbox_decoy":
            largest_size = ctx.draw_int("largest_size", 8, 8)
        elif branch == "irregular":
            largest_size = ctx.draw_int("largest_size", 9, 9)
        else:
            size_lo, size_hi = size_ranges[band]
            if h <= 10 and w <= 10 and component_count >= 4:
                size_hi = min(size_hi, 9)
            largest_size = ctx.draw_int("largest_size", size_lo, size_hi)

    layout_rng = ctx.draw_rng("layout")
    sizes = _component_sizes(largest_size, component_count, branch=branch)
    if branch == "bbox_decoy":
        shapes = [_BASE_SHAPES[8], _BBOX_DECOY]
        shapes.extend(
            _shape_for_size(size, ctx.draw_rng(f"distractor_shape_{index}"))
            for index, size in enumerate(sizes[2:], start=2)
        )
        target_rank = "last"
    else:
        if branch == "canonical":
            target_shape = _BASE_SHAPES[largest_size]
        elif branch == "irregular":
            # A 3x4, nine-cell non-frame keeps its bbox smaller than the
            # seven-cell 4x4 decoy below, deterministically refuting bbox area.
            target_shape = _shape_for_size(largest_size, ctx.draw_rng("target_shape"))
        else:
            target_shape = _random_target_shape(
                largest_size,
                ctx.draw_rng("target_shape"),
                require_non_square=(branch == "irregular"),
            )
        shapes = [target_shape]
        if branch == "irregular":
            shapes.append(_BBOX_DECOY)
            shapes.extend(
                _shape_for_size(size, ctx.draw_rng(f"distractor_shape_{index}"))
                for index, size in enumerate(sizes[2:], start=2)
            )
        else:
            shapes.extend(
                _shape_for_size(size, ctx.draw_rng(f"distractor_shape_{index}"))
                for index, size in enumerate(sizes[1:], start=1)
            )
        target_rank = {
            "canonical": "first",
            "repeated_color": "middle",
            "irregular": "first",
            "general": "any",
        }[branch]

    placements = _place_shapes(
        h,
        w,
        shapes,
        layout_rng,
        target_rank=target_rank,
        target_diagonal_touch=branch in ("repeated_color", "irregular"),
    )
    colors = ctx.draw_distinct_colors(
        "scene_colors", n=foreground_colors, exclude={0}
    )
    assigned_colors = _assign_colors(
        colors,
        component_count,
        repeat_target=branch in ("repeated_color", "irregular"),
    )

    grid = full_grid(h, w, 0)
    for cells, color in zip(placements, assigned_colors, strict=True):
        for r, c in cells:
            grid[r][c] = color

    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise RuntimeError(f"generator built an invalid lesson: {findings}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "component_count": component_count,
        "largest_size": largest_size,
        "foreground_colors": foreground_colors,
    }
    if observed != expected:
        raise RuntimeError(
            f"axis realization mismatch: expected {expected}, observed {observed}"
        )
    if branch == "bbox_decoy" and not _is_bbox_decoy(grid):
        raise RuntimeError("bbox-decoy schedule failed to realize its semantic witness")
    if branch == "repeated_color" and not _repeated_largest_color(grid):
        raise RuntimeError("repeated-color schedule failed to realize its semantic witness")
    if branch in ("repeated_color", "irregular") and not _four_vs_eight_connectivity(grid):
        raise RuntimeError("schedule failed to distinguish 4- from 8-connectivity")
    if branch == "irregular" and (
        not _irregular_largest(grid)
        or not _non_square_crop(grid)
        or not _is_bbox_decoy(grid)
        or not _repeated_largest_color(grid)
    ):
        raise RuntimeError("irregular schedule failed to realize its combined semantic witnesses")
    return grid


def _candidate_output(name, grid):
    components = _components(grid)
    if not components:
        return None
    scan = sorted(components, key=lambda obj: (obj["bbox"][0], obj["bbox"][1]))

    if name == "largest_cells":
        chosen = min(scan, key=lambda obj: (-obj["size"], obj["bbox"][0], obj["bbox"][1]))
        return _crop(grid, chosen["bbox"])
    if name == "largest_8_connected":
        components_8 = _components(grid, connectivity=8)
        chosen = min(
            components_8,
            key=lambda obj: (-obj["size"], obj["bbox"][0], obj["bbox"][1]),
        )
        return _crop(grid, chosen["bbox"])
    if name == "largest_bbox_area":
        chosen = min(
            scan,
            key=lambda obj: (-_bbox_area(obj["cells"]), obj["bbox"][0], obj["bbox"][1]),
        )
        return _crop(grid, chosen["bbox"])
    if name == "first_component":
        return _crop(grid, scan[0]["bbox"])
    if name == "last_component":
        return _crop(grid, scan[-1]["bbox"])
    if name == "leftmost_component":
        chosen = min(scan, key=lambda obj: (obj["bbox"][1], obj["bbox"][0]))
        return _crop(grid, chosen["bbox"])
    if name == "rightmost_component":
        chosen = max(scan, key=lambda obj: (obj["bbox"][3], obj["bbox"][2]))
        return _crop(grid, chosen["bbox"])
    if name == "modal_color_all_cells":
        counts = Counter(value for row in grid for value in row if value != 0)
        first = {}
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value != 0 and value not in first:
                    first[value] = (r, c)
        color = min(counts, key=lambda value: (-counts[value], first[value]))
        cells = [
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        ]
        return _crop(grid, _bbox(cells))
    if name == "largest_hollow_frame":
        frames = [obj for obj in scan if _hollow_frame(obj)]
        if not frames:
            return None
        chosen = min(frames, key=lambda obj: (-obj["size"], obj["bbox"][0], obj["bbox"][1]))
        return _crop(grid, chosen["bbox"])
    raise KeyError(name)


_CANDIDATE_RULES = (
    "largest_cells",
    "largest_8_connected",
    "largest_bbox_area",
    "first_component",
    "last_component",
    "modal_color_all_cells",
    "largest_hollow_frame",
)


def _candidate_solver(name):
    return lambda grid, _name=name: _candidate_output(_name, grid)


SEMANTIC_RIVALS = {
    name: _candidate_solver(name)
    for name in _CANDIDATE_RULES
    if name != "largest_cells"
}
WITNESS_RIVALS = {
    "larger_bbox_smaller_cells_decoy": ["largest_bbox_area"],
    "target_color_repeated_in_distractor": ["modal_color_all_cells"],
    "irregular_non_frame_target": ["largest_hollow_frame"],
    "four_connected_not_eight_connected": ["largest_8_connected"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "largest_8_connected",
        "largest_bbox_area",
        "modal_color_all_cells",
        "largest_hollow_frame",
    )
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a plausible shortcut predicts another query answer."""
    consistent = []
    for name in _CANDIDATE_RULES:
        if all(
            _candidate_output(name, pair["input"]) == pair["output"]
            for pair in demos
        ):
            consistent.append(name)
    if "largest_cells" not in consistent:
        return ["official largest-cell rule is not consistent with the demonstrations"]
    official = _candidate_output("largest_cells", query["input"])
    differing = []
    for name in consistent:
        candidate = _candidate_output(name, query["input"])
        if candidate != official:
            differing.append(name)
    if differing:
        return [
            "demonstrations admit shortcut rule(s) with a different query answer: "
            + ", ".join(differing)
        ]
    return []
