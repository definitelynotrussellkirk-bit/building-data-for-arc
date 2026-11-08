"""Generator for ``91c488d9ffdc`` — opposite corner pairs to outlines.

Every nonzero color occurs exactly twice, at opposite corners of one
axis-aligned rectangle.  The answer is a fresh zero grid with each rectangle's
border painted in its pair color.  The three-slot default curriculum cycles
through a canonical-profile anchor, an all-negative-slant counterexample, and a
mixed-slant multi-rectangle counterexample.  This keeps official scale support
while refuting the positive-diagonal-only shortcut that fits every canonical
pair.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "91c488d9ffdc"
TASK_ID = GENERATOR_ID
VERSION = "3.0.1"
RULE_HASH = "515ca330e152"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A 7..12 by 7..12 zero-background grid contains one to three distinct "
    "nonzero colors. Each color appears exactly twice at different rows and "
    "columns, marking opposite corners of a rectangle at least 3x3. Rectangle "
    "borders do not intersect, although one rectangle may be nested inside "
    "another. On a fresh zero grid of the same size, draw all four border "
    "edges of every marked rectangle in its pair color; interiors remain zero."
)
INVARIANTS = [
    "one to three distinct nonzero colors, each appearing exactly twice",
    "each pair differs in row and column and spans a rectangle at least 3x3",
    "rectangle border cell sets are pairwise disjoint",
    "output is a fresh same-size zero grid containing all colored outlines",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-profile height",
        "valid": "7..12",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-profile width",
        "valid": "7..12",
    },
    "n_rects": {
        "type": "int",
        "default": "scheduled 1..2; override supports 1..3",
        "valid": "1..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

# Linked morphology signatures from every canonical train and test input.
# A scene is (height, width, tuple of rectangle boxes r0,c0,r1,c1).
_CANONICAL_SCENES: tuple[tuple[int, int, tuple[tuple[int, int, int, int], ...]], ...] = (
    (8, 9, ((1, 1, 5, 6),)),
    (9, 10, ((2, 1, 7, 4), (1, 6, 4, 8))),
    (7, 11, ((1, 3, 5, 9),)),
    (10, 10, ((2, 1, 8, 4), (4, 6, 6, 8))),
    (9, 12, ((1, 2, 7, 9), (3, 4, 6, 6))),
)
_TWO_RECT_SCENES = tuple(scene for scene in _CANONICAL_SCENES if len(scene[2]) == 2)


def _box_size(box: tuple[int, int, int, int]) -> tuple[int, int]:
    r0, c0, r1, c1 = box
    return r1 - r0 + 1, c1 - c0 + 1


def _scene_signature(
    h: int, w: int, boxes: Iterable[tuple[int, int, int, int]]
) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    return h, w, tuple(sorted(_box_size(box) for box in boxes))


_CANONICAL_SIGNATURES = {
    _scene_signature(h, w, boxes) for h, w, boxes in _CANONICAL_SCENES
}

SCHEDULE_PROFILES = ("canonical-positive", "negative", "mixed")


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the deterministic three-slot teaching schedule."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _scheduled_scene(sample_index: int):
    index = int(sample_index)
    phase = index % 3
    block = index // 3
    if phase == 0:
        return _CANONICAL_SCENES[block % len(_CANONICAL_SCENES)]
    # Both non-anchor slots are multi-rectangle canonical-scale profiles.
    return _TWO_RECT_SCENES[(2 * block + phase - 1) % len(_TWO_RECT_SCENES)]


def _band(difficulty: Any) -> str:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    return "medium" if difficulty is None else str(difficulty)


def _has_override(overrides: dict[str, Any], name: str) -> bool:
    return name in overrides and overrides[name] is not None


def _draw_scheduled_int(
    ctx,
    overrides: dict[str, Any],
    name: str,
    lo: int,
    hi: int,
    scheduled: int,
) -> int:
    """Record an exact scheduled default while honoring the full public domain."""
    if _has_override(overrides, name):
        return ctx.draw_int_strict(name, lo, hi)
    return int(ctx.draw_choice(name, (scheduled,)))


def _outline_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        *((r0, c) for c in range(c0, c1 + 1)),
        *((r1, c) for c in range(c0, c1 + 1)),
        *((r, c0) for r in range(r0, r1 + 1)),
        *((r, c1) for r in range(r0, r1 + 1)),
    }


def _boxes_have_disjoint_borders(
    boxes: Iterable[tuple[int, int, int, int]],
) -> bool:
    occupied: set[tuple[int, int]] = set()
    for box in boxes:
        border = _outline_cells(box)
        if occupied & border:
            return False
        occupied |= border
    return True


def _box_contains(
    outer: tuple[int, int, int, int], inner: tuple[int, int, int, int]
) -> bool:
    or0, oc0, or1, oc1 = outer
    ir0, ic0, ir1, ic1 = inner
    return or0 < ir0 and oc0 < ic0 and ir1 < or1 and ic1 < oc1


def _transform_box(
    box: tuple[int, int, int, int], h: int, w: int, code: int
) -> tuple[int, int, int, int]:
    r0, c0, r1, c1 = box
    if code == 1:  # horizontal reflection
        return r0, w - 1 - c1, r1, w - 1 - c0
    if code == 2:  # vertical reflection
        return h - 1 - r1, c0, h - 1 - r0, c1
    if code == 3:  # 180-degree rotation
        return h - 1 - r1, w - 1 - c1, h - 1 - r0, w - 1 - c0
    return box


def _canonical_boxes(
    h: int,
    w: int,
    boxes: tuple[tuple[int, int, int, int], ...],
    rng,
) -> list[tuple[int, int, int, int]]:
    code = rng.randrange(4)
    result = [_transform_box(box, h, w, code) for box in boxes]
    rng.shuffle(result)
    return result


def _corner_boxes(h: int, w: int) -> list[tuple[int, int, int, int]]:
    return [
        (0, 0, 2, 2),
        (0, w - 3, 2, w - 1),
        (h - 3, 0, h - 1, 2),
        (h - 3, w - 3, h - 1, w - 1),
    ]


def _general_boxes(
    h: int, w: int, n_rects: int, phase: int, rng
) -> list[tuple[int, int, int, int]]:
    """Construct one to three rectangles without retry-based count loss."""
    if n_rects == 1:
        bh = rng.randint(3, h)
        bw = rng.randint(3, w)
        r0 = rng.randint(0, h - bh)
        c0 = rng.randint(0, w - bw)
        return [(r0, c0, r0 + bh - 1, c0 + bw - 1)]

    if n_rects == 2 and phase == 1:
        # Nested rectangles exercise lawful bbox overlap while their borders
        # remain separated by one zero-cell moat on every side.
        outer = (0, 0, h - 1, w - 1)
        inner = (2, 2, h - 3, w - 3)
        return [outer, inner]

    candidates = _corner_boxes(h, w)
    rng.shuffle(candidates)
    result = candidates[:n_rects]
    if len(result) != n_rects or not _boxes_have_disjoint_borders(result):
        raise RuntimeError(
            f"constructive placement failed for {n_rects} rectangles in {h}x{w}"
        )
    return result


def _slants(phase: int, n_rects: int) -> tuple[str, ...]:
    if phase == 0:
        return ("positive",) * n_rects
    if phase == 1:
        return ("negative",) * n_rects
    if n_rects == 1:
        return ("negative",)
    return tuple("positive" if index % 2 == 0 else "negative" for index in range(n_rects))


def _endpoints(
    box: tuple[int, int, int, int], slant: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    r0, c0, r1, c1 = box
    if slant == "positive":
        return (r0, c0), (r1, c1)
    return (r0, c1), (r1, c0)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")

    scheduled_h, scheduled_w, scheduled_boxes = _scheduled_scene(sample_index)
    scheduled_n = len(scheduled_boxes)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _draw_scheduled_int(ctx, overrides, "grid_h", 7, 12, scheduled_h)
    w = _draw_scheduled_int(ctx, overrides, "grid_w", 7, 12, scheduled_w)
    n_rects = _draw_scheduled_int(ctx, overrides, "n_rects", 1, 3, scheduled_n)

    phase = int(sample_index) % 3
    layout_rng = ctx.draw_rng("layout")
    uses_anchor = (
        phase == 0
        and h == scheduled_h
        and w == scheduled_w
        and n_rects == scheduled_n
    )
    if uses_anchor:
        boxes = _canonical_boxes(h, w, scheduled_boxes, layout_rng)
    else:
        boxes = _general_boxes(h, w, n_rects, phase, layout_rng)

    if len(boxes) != n_rects or not _boxes_have_disjoint_borders(boxes):
        raise RuntimeError("generator constructed an invalid rectangle layout")

    palette_excludes = {
        "easy": {0, 5, 6, 7, 8, 9},
        "medium": {0},
        "hard": {0, 1, 2, 3, 4},
    }[band]
    colors = list(
        ctx.draw_distinct_colors("colors", n=n_rects, exclude=palette_excludes)
    )
    layout_rng.shuffle(colors)
    grid = full_grid(h, w, 0)
    for color, box, slant in zip(colors, boxes, _slants(phase, n_rects)):
        for r, c in _endpoints(box, slant):
            if grid[r][c] != 0:
                raise RuntimeError("rectangle endpoints unexpectedly collided")
            grid[r][c] = color
    return grid


def _analyze(grid):
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return {"errors": ["grid must be a non-empty list of rows"]}
    h = len(grid)
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return {"errors": ["grid rows must be non-empty and rectangular"]}
    if not 7 <= h <= 12:
        errors.append(f"grid height {h} outside 7..12")
    if not 7 <= w <= 12:
        errors.append(f"grid width {w} outside 7..12")

    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
                continue
            if value:
                positions[value].append((r, c))
    if any("invalid ARC color" in error for error in errors):
        return {"errors": errors}
    if not 1 <= len(positions) <= 3:
        errors.append(
            f"expected one to three nonzero colors, got {len(positions)}"
        )

    pairs: list[dict[str, Any]] = []
    for color, cells in sorted(positions.items()):
        if len(cells) != 2:
            errors.append(
                f"color {color} must appear exactly twice, got {len(cells)}"
            )
            continue
        ordered = sorted(cells)
        (r0, first_c), (r1, second_c) = ordered
        if r0 == r1 or first_c == second_c:
            errors.append(
                f"color {color} endpoints must differ in row and column"
            )
            continue
        c0, c1 = sorted((first_c, second_c))
        box = (r0, c0, r1, c1)
        bh, bw = _box_size(box)
        if bh < 3 or bw < 3:
            errors.append(
                f"color {color} bbox {bh}x{bw} must be at least 3x3"
            )
        pairs.append(
            {
                "color": color,
                "cells": tuple(cells),
                "box": box,
                "size": (bh, bw),
                "slant": "positive" if second_c > first_c else "negative",
            }
        )

    if len(pairs) == len(positions) and not _boxes_have_disjoint_borders(
        pair["box"] for pair in pairs
    ):
        errors.append("rectangle border cell sets must be pairwise disjoint")

    signature = None
    if pairs and len(pairs) == len(positions):
        signature = _scene_signature(h, w, (pair["box"] for pair in pairs))
    return {
        "errors": errors,
        "grid_h": h,
        "grid_w": w,
        "n_rects": len(pairs),
        "pairs": pairs,
        "signature": signature,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_rects": analysis["n_rects"],
    }


def _has_nested_pair(boxes: list[tuple[int, int, int, int]]) -> bool:
    return any(
        _box_contains(a, b) or _box_contains(b, a)
        for index, a in enumerate(boxes)
        for b in boxes[index + 1 :]
    )


def _touches_border(box, h: int, w: int) -> bool:
    r0, c0, r1, c1 = box
    return r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    pairs = analysis["pairs"]
    slants = tuple(pair["slant"] for pair in pairs)
    boxes = [pair["box"] for pair in pairs]
    return {
        **observe_overrides(grid),
        "linked_profile": analysis["signature"],
        "strict_canonical": analysis["signature"] in _CANONICAL_SIGNATURES,
        "has_positive_slant": "positive" in slants,
        "has_negative_slant": "negative" in slants,
        "mixed_slants": len(set(slants)) > 1,
        "multiple_rectangles": len(pairs) > 1,
        "nested_rectangles": _has_nested_pair(boxes),
        "touches_border": any(
            _touches_border(box, analysis["grid_h"], analysis["grid_w"])
            for box in boxes
        ),
        "outline_adds_cells": any(len(_outline_cells(box)) > 2 for box in boxes),
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    if analysis["signature"] not in _CANONICAL_SIGNATURES:
        return [f"linked profile {analysis['signature']!r} is not canonical"]
    return []


def rule_mirror(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    analysis = _analyze(grid)
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for pair in analysis["pairs"]:
        for r, c in _outline_cells(pair["box"]):
            out[r][c] = pair["color"]
    return out


def _solid_fill(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for pair in analysis["pairs"]:
        r0, c0, r1, c1 = pair["box"]
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                out[r][c] = pair["color"]
    return out


def _positive_slant_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for pair in analysis["pairs"]:
        cells = pair["cells"]
        paint = _outline_cells(pair["box"]) if pair["slant"] == "positive" else set(cells)
        for r, c in paint:
            out[r][c] = pair["color"]
    return out


def _single_global_bbox(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    cells = [cell for pair in analysis["pairs"] for cell in pair["cells"]]
    box = (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )
    color = min(pair["color"] for pair in analysis["pairs"])
    for r, c in _outline_cells(box):
        out[r][c] = color
    return out


def _first_pair_only(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    pair = analysis["pairs"][0]
    for r, c in _outline_cells(pair["box"]):
        out[r][c] = pair["color"]
    return out


def _l_path_pairs(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return None
    out = full_grid(analysis["grid_h"], analysis["grid_w"], 0)
    for pair in analysis["pairs"]:
        (r0, c0), (r1, c1) = sorted(pair["cells"])
        for c in range(min(c0, c1), max(c0, c1) + 1):
            out[r0][c] = pair["color"]
        for r in range(r0, r1 + 1):
            out[r][c1] = pair["color"]
    return out


def _identity(grid):
    return [row[:] for row in grid]


SEMANTIC_RIVALS: dict[str, Callable] = {
    "solid_fill_each_pair_bbox": _solid_fill,
    "positive_slant_pairs_only": _positive_slant_only,
    "one_global_bbox": _single_global_bbox,
    "first_pair_only": _first_pair_only,
    "l_path_between_each_pair": _l_path_pairs,
    "identity": _identity,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "positive_slant_pairs_only": _positive_slant_only,
}


def _witness(grid, key: str) -> bool:
    observables = semantic_observables(grid)
    return not observables.get("errors") and bool(observables.get(key))


SEMANTIC_WITNESSES = {
    "strict_canonical_profile": lambda grid: _witness(grid, "strict_canonical"),
    "negative_slant": lambda grid: _witness(grid, "has_negative_slant"),
    "mixed_slants": lambda grid: _witness(grid, "mixed_slants"),
    "multiple_rectangles": lambda grid: _witness(grid, "multiple_rectangles"),
    "nested_rectangles": lambda grid: _witness(grid, "nested_rectangles"),
    "border_contact": lambda grid: _witness(grid, "touches_border"),
    "outline_adds_cells": lambda grid: _witness(grid, "outline_adds_cells"),
}
WITNESS_RIVALS = {
    "strict_canonical_profile": ["solid_fill_each_pair_bbox"],
    "negative_slant": ["positive_slant_pairs_only"],
    "mixed_slants": ["positive_slant_pairs_only"],
    "multiple_rectangles": ["one_global_bbox", "first_pair_only"],
    "nested_rectangles": ["one_global_bbox"],
    "border_contact": ["identity"],
    "outline_adds_cells": ["identity", "l_path_between_each_pair"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return ["query input is not a lawful opposite-corner scene"]
    query_truth = rule_mirror(query_input)

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        errors = self_check(demo_input)
        if errors:
            reasons.append(f"demo {index} input is unlawful: {errors[0]}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            reasons.append(f"demo {index} output disagrees with the outline rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query_input) != query_truth:
                reasons.append(
                    f"demos still fit competitor {name!r}, which changes the query answer"
                )
    return reasons
