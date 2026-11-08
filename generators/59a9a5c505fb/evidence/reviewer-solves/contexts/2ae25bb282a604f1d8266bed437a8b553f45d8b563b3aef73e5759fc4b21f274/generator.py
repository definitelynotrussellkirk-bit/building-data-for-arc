"""Curriculum for counting how many object bounding boxes contain each cell.

The selected Racket authority is unchanged.  Canonical examples contain only
strictly nested rectangle frames, so a frame-specific shortcut fits every one.
This sampler cycles four observable scene profiles: one canonical frame anchor,
one nested sparse counterexample, and two non-nested crossing-bbox profiles.
Every three-of-four lesson rotation therefore refutes both canonical-fitting
shortcuts while every default draw retains an exact canonical size/palette.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "59a9a5c505fb"
TASK_ID = GENERATOR_ID
RULE_HASH = "058f695b6f59"
VERSION = "3.0.0"
SUMMARY = (
    "A 0-background grid contains two or three differently colored connected "
    "objects whose bounding boxes share an overlap. For every output cell, "
    "count the object bounding boxes containing that coordinate. A four-profile "
    "cycle includes nested frames, nested sparse L-shapes, crossing sparse "
    "boxes, and a crossing frame/sparse mixture so frame-only and nesting-only "
    "shortcuts are explicitly contradicted."
)

INVARIANTS = [
    "background is 0 and every nonzero color forms exactly one 4-connected object",
    "two or three object bounding boxes have a nonempty common intersection",
    "object colors are distinct; output colors are dropped in favor of bbox counts",
    "every default four-instance cycle contains a canonical anchor and three shortcut counterexamples",
]

SCENE_PROFILES = (
    "nested_frames",
    "nested_sparse",
    "crossing_sparse",
    "crossing_mixed",
)
SCHEDULE_PROFILES = SCENE_PROFILES
SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20

# Exact profiles across all five selected canonical train/test inputs.  Every
# default draw uses one of them; variation comes from profile, orientation,
# placement, colors, and the band-specific profile subset rather than drifting
# away from the task's observed scale.
CANONICAL_SCENE_SIZES = (
    (9, 9, 2),
    (10, 12, 2),
    (11, 11, 3),
    (12, 14, 3),
    (11, 13, 3),
)
CANONICAL_PROFILES = frozenset((h, w, n_objects + 1) for h, w, n_objects in CANONICAL_SCENE_SIZES)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "cyclic nested_frames / nested_sparse / crossing_sparse / crossing_mixed",
        "valid": "|".join(SCENE_PROFILES),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = ()

Grid = list[list[int]]
Point = tuple[int, int]
Box = tuple[int, int, int, int]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Public deterministic four-profile lesson schedule."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise ValueError("sample_index must be an integer")
    return SCHEDULE_PROFILES[sample_index % SCHEDULE_PERIOD]


def _ring(r1: int, c1: int, r2: int, c2: int) -> frozenset[Point]:
    return frozenset(
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    )


def _top_left_l(r1: int, c1: int, r2: int, c2: int) -> frozenset[Point]:
    return frozenset(
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
    )


def _bottom_right_l(r1: int, c1: int, r2: int, c2: int) -> frozenset[Point]:
    return frozenset(
        {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )


# Each profile is an 8x8, three-object template.  Taking the first two objects
# remains lawful and preserves the profile's diagnostic property.  The crossing
# profiles use two incomparable bboxes whose overlap contains the optional third
# object, so the intended count reaches the full object count.
_PROFILE_OBJECTS: dict[str, tuple[frozenset[Point], ...]] = {
    "nested_frames": (
        _ring(0, 0, 7, 7),
        _ring(1, 1, 6, 6),
        _ring(2, 2, 5, 5),
    ),
    "nested_sparse": (
        _top_left_l(0, 0, 7, 7),
        _bottom_right_l(1, 1, 6, 6),
        _top_left_l(2, 2, 5, 5),
    ),
    "crossing_sparse": (
        _top_left_l(1, 0, 6, 5),
        _bottom_right_l(0, 2, 5, 7),
        _top_left_l(2, 3, 4, 5),
    ),
    "crossing_mixed": (
        _ring(0, 0, 6, 5),
        _bottom_right_l(1, 2, 7, 7),
        _ring(2, 2, 4, 4),
    ),
}


def _transform(point: Point, orientation: int) -> Point:
    r, c = point
    if orientation >= 4:
        c = 7 - c
    for _ in range(orientation % 4):
        r, c = c, 7 - r
    return r, c


def _scene_size(ctx) -> tuple[int, int, int]:
    band = ctx.difficulty if ctx.difficulty in ("easy", "medium", "hard") else "mixed"
    choices = {
        "easy": CANONICAL_SCENE_SIZES[:2],
        "medium": CANONICAL_SCENE_SIZES[1:],
        "hard": CANONICAL_SCENE_SIZES[2:],
        "mixed": CANONICAL_SCENE_SIZES,
    }[band]
    return ctx.draw_choice(f"canonical_scene_size_{band}", choices)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if type(seed) is not int or type(sample_index) is not int:
        raise ValueError("seed and sample_index must be integers")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")

    requested = overrides.get("scene_profile", schedule_profile(seed, sample_index, difficulty))
    if not isinstance(requested, str) or requested not in SCENE_PROFILES:
        raise ValueError(f"scene_profile must be one of {SCENE_PROFILES}")
    effective_overrides = dict(overrides)
    effective_overrides["scene_profile"] = requested
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    h, w, n_objects = _scene_size(ctx)
    orientation = ctx.draw_int("orientation", 0, 7)
    top = ctx.draw_int("top", 0, h - 8)
    left = ctx.draw_int("left", 0, w - 8)
    colors = ctx.draw_distinct_colors("object_colors", n=n_objects, exclude=(0,))

    grid = full_grid(h, w, 0)
    occupied: set[Point] = set()
    for color, template in zip(colors, _PROFILE_OBJECTS[profile][:n_objects]):
        cells = {(top + r, left + c) for r, c in map(lambda p: _transform(p, orientation), template)}
        if occupied & cells:
            raise RuntimeError("profile transform produced overlapping object cells")
        occupied.update(cells)
        for r, c in cells:
            grid[r][c] = color
    return grid


def _validate_grid(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty")
    width = len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise ValueError("grid must be rectangular")
        if any(type(value) is not int or not 0 <= value <= 9 for value in row):
            raise ValueError("grid values must be integer ARC colors 0..9")
    return len(grid), width


def _color_components(grid) -> list[dict]:
    h, w = _validate_grid(grid)
    seen: set[Point] = set()
    components: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells: set[Point] = set()
            while todo:
                rr, cc = todo.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    point = (nr, nc)
                    if (0 <= nr < h and 0 <= nc < w and point not in seen
                            and grid[nr][nc] == color):
                        seen.add(point)
                        todo.append(point)
            rs = [rr for rr, _ in cells]
            cs = [cc for _, cc in cells]
            box: Box = (min(rs), min(cs), max(rs), max(cs))
            perimeter = _ring(*box)
            components.append({
                "color": color,
                "cells": frozenset(cells),
                "box": box,
                "is_frame": frozenset(cells) == perimeter and box[0] < box[2] and box[1] < box[3],
            })
    return components


def _contains(outer: Box, inner: Box, *, strict: bool = False) -> bool:
    contains = (
        outer[0] <= inner[0]
        and outer[1] <= inner[1]
        and outer[2] >= inner[2]
        and outer[3] >= inner[3]
    )
    return contains and (not strict or outer != inner)


def _overlap(a: Box, b: Box) -> bool:
    return max(a[0], b[0]) <= min(a[2], b[2]) and max(a[1], b[1]) <= min(a[3], b[3])


def _strict_chain(boxes: Iterable[Box]) -> bool:
    seq = list(boxes)
    return all(
        _contains(first, second, strict=True) or _contains(second, first, strict=True)
        for index, first in enumerate(seq)
        for second in seq[index + 1 :]
    )


def _analyze(grid) -> dict:
    h, w = _validate_grid(grid)
    components = _color_components(grid)
    boxes = [component["box"] for component in components]
    colors = [component["color"] for component in components]
    common = None
    if boxes:
        common = (
            max(box[0] for box in boxes),
            max(box[1] for box in boxes),
            min(box[2] for box in boxes),
            min(box[3] for box in boxes),
        )
    crossing = any(
        _overlap(first, second)
        and not _contains(first, second)
        and not _contains(second, first)
        for index, first in enumerate(boxes)
        for second in boxes[index + 1 :]
    )
    return {
        "height": h,
        "width": w,
        "components": components,
        "boxes": boxes,
        "colors": colors,
        "common": common,
        "strict_chain": _strict_chain(boxes),
        "has_crossing_pair": crossing,
        "all_frames": bool(components) and all(component["is_frame"] for component in components),
        "any_frames": any(component["is_frame"] for component in components),
        "any_non_frame": any(not component["is_frame"] for component in components),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    try:
        info = _analyze(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    errors: list[str] = []
    if not 8 <= info["height"] <= 30 or not 8 <= info["width"] <= 30:
        errors.append("grid dimensions must each be in 8..30")
    count = len(info["components"])
    if not 2 <= count <= 4:
        errors.append(f"expected 2..4 nonzero objects, got {count}")
    if len(info["colors"]) != len(set(info["colors"])):
        errors.append("each nonzero color must form exactly one connected object")
    for component in info["components"]:
        r1, c1, r2, c2 = component["box"]
        if r1 == r2 or c1 == c2:
            errors.append("every object bbox must span at least two rows and two columns")
            break
    common = info["common"]
    if common is None or common[0] > common[2] or common[1] > common[3]:
        errors.append("all object bounding boxes must share a nonempty intersection")
    return errors


def strict_canonical_like(grid) -> list[str]:
    issues = self_check(grid)
    if issues:
        return issues
    info = _analyze(grid)
    profile = (
        info["height"],
        info["width"],
        len({value for row in grid for value in row}),
    )
    reasons: list[str] = []
    if profile not in CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is outside selected canonical sizes/palettes")
    if len(info["components"]) not in (2, 3):
        reasons.append("canonical inputs contain two or three objects")
    if not info["all_frames"]:
        reasons.append("canonical objects are complete rectangle perimeters")
    if not info["strict_chain"]:
        reasons.append("canonical object bboxes form a strict nesting chain")
    return reasons


def _profile_name(info: dict) -> str:
    if info["strict_chain"] and info["all_frames"]:
        return "nested_frames"
    if info["strict_chain"] and info["any_non_frame"] and not info["any_frames"]:
        return "nested_sparse"
    if info["has_crossing_pair"] and not info["any_frames"]:
        return "crossing_sparse"
    if info["has_crossing_pair"] and info["any_frames"] and info["any_non_frame"]:
        return "crossing_mixed"
    raise ValueError("grid does not match a declared scene_profile")


def observe_overrides(grid) -> dict[str, str]:
    issues = self_check(grid)
    if issues:
        raise ValueError("; ".join(issues))
    return {"scene_profile": _profile_name(_analyze(grid))}


def _render_bbox_counts(grid, *, mode: str = "intended") -> Grid:
    info = _analyze(grid)
    out = full_grid(info["height"], info["width"], 0)
    boxes = info["boxes"]
    for index, component in enumerate(info["components"]):
        if mode == "visible_cells":
            cells = component["cells"]
        elif mode == "frame_fill" and not component["is_frame"]:
            cells = component["cells"]
        elif mode == "nested_chain":
            comparable = all(
                index == other
                or _contains(component["box"], boxes[other])
                or _contains(boxes[other], component["box"])
                for other in range(len(boxes))
            )
            if comparable:
                r1, c1, r2, c2 = component["box"]
                cells = ((r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))
            else:
                cells = component["cells"]
        else:
            r1, c1, r2, c2 = component["box"]
            cells = ((r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1))
        for r, c in cells:
            out[r][c] += 1
    return out


def rule_mirror(grid) -> Grid:
    """Executable mirror for contract tests; selected Racket remains authority."""
    return _render_bbox_counts(deepcopy(grid))


def _rival_frame_fill_only(grid) -> Grid:
    return _render_bbox_counts(deepcopy(grid), mode="frame_fill")


def _rival_nested_chain_only(grid) -> Grid:
    return _render_bbox_counts(deepcopy(grid), mode="nested_chain")


def _rival_visible_cells_only(grid) -> Grid:
    return _render_bbox_counts(deepcopy(grid), mode="visible_cells")


def _has_non_frame_bbox_gap(grid) -> bool:
    info = _analyze(grid)
    return info["any_non_frame"] and _rival_frame_fill_only(grid) != rule_mirror(grid)


def _has_crossing_bbox_counterexample(grid) -> bool:
    info = _analyze(grid)
    return info["has_crossing_pair"] and _rival_nested_chain_only(grid) != rule_mirror(grid)


def _has_bbox_interior_semantics(grid) -> bool:
    return _rival_visible_cells_only(grid) != rule_mirror(grid)


def _has_complete_nested_frames(grid) -> bool:
    info = _analyze(grid)
    return info["all_frames"] and info["strict_chain"]


def _has_mixed_frame_and_sparse(grid) -> bool:
    info = _analyze(grid)
    return info["any_frames"] and info["any_non_frame"]


SEMANTIC_RIVALS = {
    "frame_fill_only": _rival_frame_fill_only,
    "nested_chain_only": _rival_nested_chain_only,
    "visible_cells_only": _rival_visible_cells_only,
}
CANONICAL_SHORTCUTS = {
    "frame_fill_only": _rival_frame_fill_only,
    "nested_chain_only": _rival_nested_chain_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "non_frame_bbox_gap": _has_non_frame_bbox_gap,
    "crossing_bbox_counterexample": _has_crossing_bbox_counterexample,
    "bbox_interior_semantics": _has_bbox_interior_semantics,
    "complete_nested_frames": _has_complete_nested_frames,
    "mixed_frame_and_sparse": _has_mixed_frame_and_sparse,
}
BRANCH_WITNESSES = ("complete_nested_frames", "mixed_frame_and_sparse")
WITNESS_RIVALS = {
    "non_frame_bbox_gap": ["frame_fill_only"],
    "crossing_bbox_counterexample": ["nested_chain_only"],
    "bbox_interior_semantics": ["visible_cells_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    del query
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        survived = True
        for demo in demos:
            if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
                return ["demonstrations must contain input/output grids"]
            try:
                survived = rival(demo["input"]) == demo["output"]
            except (TypeError, ValueError) as exc:
                return [f"{name} evaluation failed: {exc}"]
            if not survived:
                break
        if survived:
            reasons.append(f"{name} fits every demonstration")
    return reasons
