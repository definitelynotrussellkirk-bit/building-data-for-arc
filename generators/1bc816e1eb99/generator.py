"""High-integrity input generator for ARC task 1bc816e1eb99.

The selected Racket authority recolors each yellow (4) component by topology:
zero enclosed holes -> red (2), exactly one enclosed hole -> cyan (8).
This sampler keeps the canonical 0/4 input palette, reproduces every public
size/morphology profile, and schedules explicit counterexamples to three
plausible visual shortcuts (size, bounding-box fullness, and pixel count).
"""
from __future__ import annotations

from collections import deque
from typing import Iterable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1bc816e1eb99"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0c3f64fb33c3"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "A 0-background grid contains two to four separated yellow components. "
    "Components include filled rectangles, one-cell-thick rectangular frames, "
    "and scheduled concave zero-hole counterexamples. Recolor each component "
    "red when it encloses no hole and cyan when it encloses exactly one hole."
)

INVARIANTS = [
    "input colors are exactly the canonical background/yellow palette subset {0,4}",
    "there are exactly 2..4 four-connected yellow components",
    "each component is a supported solid, frame, or one-notch zero-hole shape",
    "every component has zero or one enclosed hole",
    "declared axes are exact and reconstructible from the returned grid",
    "the canonical Racket program is the sole output authority",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "linked profile default; canonical profiles use public heights",
        "valid": "11..15",
    },
    "grid_w": {
        "type": "int",
        "default": "linked profile default; canonical profiles use public widths",
        "valid": "12..18",
    },
    "n_components": {
        "type": "int",
        "default": "linked profile draw 2..4; canonical profile uses 2..3",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (
    "canonical",
    "small_frame_large_solid",
    "concave_zero_hole",
    "same_area_opposite_topology",
)

_CANONICAL_DIMS = ((12, 12), (11, 14), (11, 15), (11, 12), (12, 13))
_DIR4 = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _solid(height: int, width: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(1 for _ in range(width)) for _ in range(height))


def _frame(height: int, width: int) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(int(r in (0, height - 1) or c in (0, width - 1)) for c in range(width))
        for r in range(height)
    )


# One missing edge cell creates a concavity connected to the exterior, not a hole.
_CONCAVE = (
    (1, 0, 1),
    (1, 1, 1),
    (1, 1, 1),
)
_CANONICAL_SOLIDS = (_solid(2, 2), _solid(2, 3), _solid(3, 2), _solid(2, 4), _solid(3, 4))
_CANONICAL_FRAMES = (_frame(4, 4), _frame(4, 5))
_EXTRA_SHAPES = (_solid(2, 2), _solid(2, 3), _solid(3, 2), _frame(3, 3), _frame(4, 4))


def _validate_scalars(seed, sample_index) -> None:
    """Reject public scalar coercions before schedule or GenCtx use."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the linked curriculum profile; every four-example window is complete."""
    _validate_scalars(seed, sample_index)
    offsets = {None: 0, "easy": 0, "medium": 1, "hard": 2}
    if difficulty not in offsets:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return SCHEDULE_PROFILES[(sample_index + offsets[difficulty]) % len(SCHEDULE_PROFILES)]


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    _validate_scalars(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ranges = {"grid_h": (11, 15), "grid_w": (12, 18), "n_components": (2, 4)}
    for name, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"override {name!r} must be an integer")
        lo, hi = ranges[name]
        if not lo <= value <= hi:
            raise ValueError(f"override {name!r}={value} outside [{lo},{hi}]")


def _draw_axis(ctx, overrides, name: str, default: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _default_dimensions(ctx, profile: str, difficulty: str | None) -> tuple[int, int]:
    if profile == "canonical":
        return ctx.draw_choice("canonical_dimensions", _CANONICAL_DIMS)
    choices = {
        None: ((11, 12), (11, 14), (12, 13), (13, 15), (14, 17), (15, 18)),
        "easy": ((11, 12), (11, 14), (12, 13)),
        "medium": ((12, 13), (13, 15), (14, 16)),
        "hard": ((13, 15), (14, 17), (15, 18)),
    }[difficulty]
    return ctx.draw_choice("profile_dimensions", choices)


def _profile_shapes(profile: str, n_components: int, ctx) -> list[tuple[tuple[int, ...], ...]]:
    rng = ctx.draw_rng("shape_selection")
    if profile == "canonical":
        mode = ctx.draw_choice("canonical_shape_mode", ("mixed", "all_solid"))
        shapes: list[tuple[tuple[int, ...], ...]] = []
        if mode == "mixed":
            shapes.append(rng.choice(_CANONICAL_FRAMES))
        while len(shapes) < n_components:
            shapes.append(rng.choice(_CANONICAL_SOLIDS))
    elif profile == "small_frame_large_solid":
        shapes = [_frame(3, 3), _solid(4, 4)]
    elif profile == "concave_zero_hole":
        shapes = [_CONCAVE, _frame(4, 4)]
    elif profile == "same_area_opposite_topology":
        # Both components contain eight yellow cells but have different topology.
        shapes = [_frame(3, 3), _solid(2, 4)]
    else:  # Defensive: schedule_profile is the only caller.
        raise ValueError(f"unknown schedule profile {profile!r}")
    while len(shapes) < n_components:
        shapes.append(rng.choice(_EXTRA_SHAPES))
    rng.shuffle(shapes)
    return shapes


def _slots(height: int, width: int) -> list[tuple[int, int, int, int]]:
    """Four border-adjacent slots separated by one full background row/column."""
    top_end = (height - 1) // 2
    bottom_start = top_end + 1
    left_end = (width - 1) // 2
    right_start = left_end + 1
    return [
        (0, top_end, 0, left_end),
        (0, top_end, right_start, width),
        (bottom_start, height, 0, left_end),
        (bottom_start, height, right_start, width),
    ]


def _stamp(grid, shape: Sequence[Sequence[int]], top: int, left: int) -> None:
    for rr, row in enumerate(shape):
        for cc, value in enumerate(row):
            if value:
                grid[top + rr][left + cc] = 4


def _place_shapes(grid, shapes, rng, *, force_edge: bool) -> None:
    height, width = len(grid), len(grid[0])
    slots = _slots(height, width)
    rng.shuffle(slots)
    for index, (shape, slot) in enumerate(zip(shapes, slots[: len(shapes)], strict=True)):
        r0, r1, c0, c1 = slot
        sh, sw = len(shape), len(shape[0])
        if sh > r1 - r0 or sw > c1 - c0:
            raise ValueError(f"shape {sh}x{sw} does not fit slot {slot}")
        top = rng.randint(r0, r1 - sh)
        left = rng.randint(c0, c1 - sw)
        if index == 0 and force_edge:
            edges = []
            if r0 == 0:
                edges.append("top")
            if r1 == height:
                edges.append("bottom")
            if c0 == 0:
                edges.append("left")
            if c1 == width:
                edges.append("right")
            edge = rng.choice(edges)
            if edge == "top":
                top = 0
            elif edge == "bottom":
                top = height - sh
            elif edge == "left":
                left = 0
            else:
                left = width - sw
        _stamp(grid, shape, top, left)


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return ["grid must be rectangular"]
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == 4}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in _DIR4:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    stack.append(point)
        result.append(cells)
    return result


def _hole_count(cells: Iterable[tuple[int, int]]) -> int:
    cells = set(cells)
    min_r, max_r = min(r for r, _ in cells), max(r for r, _ in cells)
    min_c, max_c = min(c for _, c in cells), max(c for _, c in cells)
    local = {(r - min_r, c - min_c) for r, c in cells}
    height, width = max_r - min_r + 1, max_c - min_c + 1
    empty = {(r, c) for r in range(height) for c in range(width) if (r, c) not in local}
    outside = {
        point for point in empty
        if point[0] in (0, height - 1) or point[1] in (0, width - 1)
    }
    queue = deque(outside)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _DIR4:
            point = (r + dr, c + dc)
            if point in empty and point not in outside:
                outside.add(point)
                queue.append(point)
    enclosed = empty - outside
    holes = 0
    while enclosed:
        holes += 1
        start = enclosed.pop()
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _DIR4:
                point = (r + dr, c + dc)
                if point in enclosed:
                    enclosed.remove(point)
                    queue.append(point)
    return holes


def _component_stats(grid) -> list[dict[str, object]]:
    stats = []
    for cells in _components(grid):
        min_r, max_r = min(r for r, _ in cells), max(r for r, _ in cells)
        min_c, max_c = min(c for _, c in cells), max(c for _, c in cells)
        height, width = max_r - min_r + 1, max_c - min_c + 1
        area = len(cells)
        stats.append({
            "cells": cells,
            "height": height,
            "width": width,
            "area": area,
            "bbox_area": height * width,
            "fills_bbox": area == height * width,
            "holes": _hole_count(cells),
            "missing": {
                (r, c)
                for r in range(min_r, max_r + 1)
                for c in range(min_c, max_c + 1)
                if (r, c) not in cells
            },
            "bbox": (min_r, max_r, min_c, max_c),
        })
    return stats


def _shape_kind(stat: dict[str, object]) -> str | None:
    height, width = int(stat["height"]), int(stat["width"])
    area = int(stat["area"])
    holes = int(stat["holes"])
    if stat["fills_bbox"] and holes == 0:
        return "solid"
    if holes == 1 and height >= 3 and width >= 3:
        expected = 2 * height + 2 * width - 4
        if area == expected:
            return "frame"
    if holes == 0 and height == width == 3 and area == 8:
        # Exactly one missing perimeter cell: a visible notch, not a hidden hole.
        (min_r, max_r, min_c, max_c) = stat["bbox"]
        missing = next(iter(stat["missing"]))
        if missing[0] in (min_r, max_r) or missing[1] in (min_c, max_c):
            return "notched_solid"
    return None


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del meta
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    errors = _grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not 11 <= height <= 15 or not 12 <= width <= 18:
        errors.append(f"dimensions {height}x{width} outside declared 11..15 x 12..18")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 4}:
        errors.append(f"input palette {sorted(palette)} is not a subset of {{0,4}}")
    if 0 not in palette:
        errors.append("background color 0 must be present")
    components = _component_stats(grid)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2..4 yellow components, found {len(components)}")
    for index, stat in enumerate(components):
        if int(stat["height"]) > 5 or int(stat["width"]) > 5:
            errors.append(f"component {index} bounding box exceeds 5x5")
        if _shape_kind(stat) is None:
            errors.append(f"component {index} is not a supported solid/frame/notch shape")
        if int(stat["holes"]) not in (0, 1):
            errors.append(f"component {index} has {stat['holes']} holes, expected zero or one")
    return errors


def strict_canonical_like(grid):
    errors = self_check(grid)
    if errors:
        return errors
    dimensions = (len(grid), len(grid[0]))
    if dimensions not in _CANONICAL_DIMS:
        return [f"dimensions {dimensions} are outside the five public profiles"]
    stats = _component_stats(grid)
    if not 2 <= len(stats) <= 3:
        return ["canonical profiles contain two or three yellow components"]
    for index, stat in enumerate(stats):
        kind = _shape_kind(stat)
        height, width = int(stat["height"]), int(stat["width"])
        if kind == "solid" and not (2 <= height <= 3 and 2 <= width <= 4):
            return [f"solid component {index} has unsupported public size {height}x{width}"]
        if kind == "frame" and not (height == 4 and width in (4, 5)):
            return [f"frame component {index} has unsupported public size {height}x{width}"]
        if kind == "notched_solid":
            return [f"component {index} is a generated counterexample, not public-profile morphology"]
    return []


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_components": len(_components(grid))}


def rule_mirror(grid) -> list[list[int]]:
    """Independent-looking Python mirror for probes; Racket remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    out = [list(row) for row in grid]
    for stat in _component_stats(grid):
        color = 8 if stat["holes"] == 1 else 2
        for r, c in stat["cells"]:
            out[r][c] = color
    return out


def _recolor_by(grid, predicate) -> list[list[int]]:
    out = [list(row) for row in grid]
    for stat in _component_stats(grid):
        color = 8 if predicate(stat) else 2
        for r, c in stat["cells"]:
            out[r][c] = color
    return out


def _rival_large_bbox(grid):
    return _recolor_by(grid, lambda stat: stat["height"] >= 4)


def _rival_bbox_not_full(grid):
    return _recolor_by(grid, lambda stat: not stat["fills_bbox"])


def _rival_area_threshold(grid):
    return _recolor_by(grid, lambda stat: stat["area"] >= 10)


def _small_frame_large_solid(grid) -> bool:
    stats = _component_stats(grid)
    return (
        any(stat["holes"] == 1 and stat["bbox_area"] <= 9 for stat in stats)
        and any(stat["holes"] == 0 and stat["bbox_area"] >= 16 for stat in stats)
    )


def _concave_zero_hole(grid) -> bool:
    return any(
        stat["holes"] == 0 and not stat["fills_bbox"]
        for stat in _component_stats(grid)
    )


def _same_area_opposite_topology(grid) -> bool:
    stats = _component_stats(grid)
    return any(
        left["area"] == right["area"] and left["holes"] != right["holes"]
        for i, left in enumerate(stats)
        for right in stats[i + 1 :]
    )


SEMANTIC_WITNESSES = {
    "small_frame_large_solid": _small_frame_large_solid,
    "concave_zero_hole": _concave_zero_hole,
    "same_area_opposite_topology": _same_area_opposite_topology,
}
SEMANTIC_RIVALS = {
    "large_bbox_means_cyan": _rival_large_bbox,
    "non_rectangular_means_cyan": _rival_bbox_not_full,
    "large_area_means_cyan": _rival_area_threshold,
}
WITNESS_RIVALS = {
    "small_frame_large_solid": ["large_bbox_means_cyan"],
    "concave_zero_hole": ["non_rectangular_means_cyan"],
    "same_area_opposite_topology": ["large_area_means_cyan"],
}
CANONICAL_SHORTCUTS = {
    "large_bbox_means_cyan": _rival_large_bbox,
    "non_rectangular_means_cyan": _rival_bbox_not_full,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named wrong rule fits all demos but changes query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is unlawful: {errors[0]}")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with topology recoloring")
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is unlawful: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with topology recoloring")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"competitor survives all demos: {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one deterministic lawful input; the Racket rule owns outputs."""
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w = _default_dimensions(ctx, profile, difficulty)
    default_n = (
        ctx.draw_choice("canonical_component_count", (2, 3))
        if profile == "canonical"
        else ctx.draw_choice("profile_component_count", (2, 3, 4))
    )
    height = _draw_axis(ctx, overrides, "grid_h", default_h, 11, 15)
    width = _draw_axis(ctx, overrides, "grid_w", default_w, 12, 18)
    n_components = _draw_axis(ctx, overrides, "n_components", default_n, 2, 4)

    grid = full_grid(height, width, 0)
    shapes = _profile_shapes(profile, n_components, ctx)
    edge_contact = ctx.draw_choice("edge_contact", (False, True))
    layout_rng = ctx.draw_rng(f"layout:{difficulty or 'default'}")
    _place_shapes(grid, shapes, layout_rng, force_edge=edge_contact)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError("constructed invalid scene: " + "; ".join(errors))
    expected = {"grid_h": height, "grid_w": width, "n_components": n_components}
    actual = observe_overrides(grid)
    if actual != expected:
        raise ValueError(f"constructed scene did not realize axes: {actual!r} != {expected!r}")
    return [row[:] for row in grid]
