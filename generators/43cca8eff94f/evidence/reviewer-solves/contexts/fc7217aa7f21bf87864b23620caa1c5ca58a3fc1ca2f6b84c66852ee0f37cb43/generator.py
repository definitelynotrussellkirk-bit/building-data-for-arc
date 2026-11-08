"""Constructive inputs for *Dock the Shape to the Frame*.

The pinned Racket authority keeps the cyan (8) hollow frame fixed and slides
the single red (2) object in the unique cardinal direction toward that frame.
The entire red shape translates rigidly until the next step would intersect a
non-red non-zero cell or leave the grid.

This sampler deliberately schedules two ``up`` cases in every five examples.
The canonical task contains right/down/left only, so that redundancy makes a
four-demo lesson refute the canonical-fitting shortcut "never move upward" no
matter which member of the five-example window is used as the query.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from itertools import combinations
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid, paint_at

GENERATOR_ID = "43cca8eff94f"
TASK_ID = GENERATOR_ID
RULE_HASH = "ced1f6ce57f8"
VERSION = "3.0.0"
SUMMARY = (
    "A connected red (2) polyomino lies wholly to one side of a hollow cyan "
    "(8) rectangular frame. Translate the red shape rigidly toward the frame "
    "until the next step would touch it. Every five-sample teaching window "
    "contains right, left, down, and two up examples."
)
EXAMPLES_NEEDED = 4
LESSON_SCHEDULE_PERIOD = 5
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "9..18 by 10..20 rectangular grid using exactly colors 0, 2, and 8",
    "one connected 3..7-cell red object contained in a 3x3 box",
    "one connected hollow cyan rectangular frame with side lengths 3..6",
    "the object is cleanly left/right/above/below the frame with 1..3 empty cells of gap",
    "the leading edge overlaps the frame lane, so the object docks to the frame rather than a wall",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled core or broad", "valid": "9..18"},
    "grid_w": {"type": "int", "default": "scheduled core or broad", "valid": "10..20"},
    "direction": {"type": "str", "default": "scheduled", "valid": "right|left|down|up"},
    "obj_size": {"type": "int", "default": "difficulty-weighted", "valid": "3..7"},
    "gap": {"type": "int", "default": "difficulty-weighted", "valid": "1..3"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

DIRECTIONS = ("right", "left", "down", "up")
_DIRECTION_SCHEDULE = ("right", "left", "down", "up", "up")
SCHEDULE_PROFILES = (
    "canonical_right",
    "broad_left",
    "broad_down",
    "canonical_up_a",
    "canonical_up_b",
)
_CANONICAL_DIMS = {
    0: (9, 11),
    3: (10, 10),
    4: (9, 12),
}
_ALLOWED_DIFFICULTIES = {None, "easy", "medium", "hard"}
_AXIS_NAMES = frozenset(AXES)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_STEP = {"right": (0, 1), "left": (0, -1), "down": (1, 0), "up": (-1, 0)}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the profile name; each consecutive five indices cover all."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _is_connected(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {min(cells)}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARDINAL:
            nxt = (r + dr, c + dc)
            if nxt in cells and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen == cells


def _shape_catalog() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    """All normalized connected subsets of a 3x3 box, deterministically sorted."""
    cells = tuple((r, c) for r in range(3) for c in range(3))
    result: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size in range(3, 8):
        shapes = {
            _normalize(choice)
            for choice in combinations(cells, size)
            if _is_connected(choice)
        }
        result[size] = tuple(sorted(shapes))
    return result


_SHAPES_BY_SIZE = _shape_catalog()


def _validate_call(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be non-negative")
    if difficulty not in _ALLOWED_DIFFICULTIES:
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - _AXIS_NAMES)
    if unknown:
        raise KeyError(f"unknown override axis/axes: {', '.join(unknown)}")


def _difficulty_name(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    value = float(difficulty)
    return "easy" if value < 1 / 3 else "hard" if value >= 2 / 3 else "medium"


def _weighted_values(lo: int, hi: int, difficulty, *, preferred=()) -> tuple[int, ...]:
    values = list(range(lo, hi + 1))
    band = _difficulty_name(difficulty)
    span = hi - lo
    if band == "easy":
        favored = range(lo, min(hi, lo + max(1, span // 3)) + 1)
    elif band == "hard":
        favored = range(max(lo, hi - max(1, span // 3)), hi + 1)
    else:
        center = (lo + hi) // 2
        favored = range(max(lo, center - 1), min(hi, center + 1) + 1)
    values.extend(favored)
    values.extend(v for v in preferred if lo <= v <= hi)
    return tuple(values)


def _draw_int_axis(ctx, label: str, lo: int, hi: int, options: tuple[int, ...]) -> int:
    if ctx.overrides.get(label) is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_choice(label, options)


def _draw_dimensions(ctx, slot: int, difficulty) -> tuple[int, int]:
    core = _CANONICAL_DIMS.get(slot)
    h_options = (core[0],) if core else _weighted_values(9, 18, difficulty, preferred=(9, 10))
    w_options = (core[1],) if core else _weighted_values(10, 20, difficulty, preferred=(10, 11, 12))
    h = _draw_int_axis(ctx, "grid_h", 9, 18, h_options)
    w = _draw_int_axis(ctx, "grid_w", 10, 20, w_options)
    return h, w


def _leading_offsets(shape, direction: str) -> tuple[tuple[int, int], ...]:
    max_r = max(r for r, _ in shape)
    max_c = max(c for _, c in shape)
    if direction == "right":
        return tuple((r, c) for r, c in shape if c == max_c)
    if direction == "left":
        return tuple((r, c) for r, c in shape if c == 0)
    if direction == "down":
        return tuple((r, c) for r, c in shape if r == max_r)
    return tuple((r, c) for r, c in shape if r == 0)


def _place_horizontal(ctx, h, w, shape, frame_h, frame_w, gap, direction):
    obj_h = max(r for r, _ in shape) + 1
    obj_w = max(c for _, c in shape) + 1
    slack = w - (obj_w + gap + frame_w)
    axis_offset = ctx.draw_rng("motion_axis_offset").randint(0, slack)
    if direction == "right":
        obj_left = axis_offset
        frame_left = obj_left + obj_w + gap
    else:
        frame_left = axis_offset
        obj_left = frame_left + frame_w + gap

    leading_rows = {r for r, _ in _leading_offsets(shape, direction)}
    candidates = []
    for frame_top in range(h - frame_h + 1):
        frame_rows = set(range(frame_top, frame_top + frame_h))
        for obj_top in range(h - obj_h + 1):
            if any(obj_top + r in frame_rows for r in leading_rows):
                candidates.append((frame_top, obj_top))
    frame_top, obj_top = ctx.draw_rng("perpendicular_alignment").choice(candidates)
    return frame_top, frame_left, obj_top, obj_left


def _place_vertical(ctx, h, w, shape, frame_h, frame_w, gap, direction):
    obj_h = max(r for r, _ in shape) + 1
    obj_w = max(c for _, c in shape) + 1
    slack = h - (obj_h + gap + frame_h)
    axis_offset = ctx.draw_rng("motion_axis_offset").randint(0, slack)
    if direction == "down":
        obj_top = axis_offset
        frame_top = obj_top + obj_h + gap
    else:
        frame_top = axis_offset
        obj_top = frame_top + frame_h + gap

    leading_cols = {c for _, c in _leading_offsets(shape, direction)}
    candidates = []
    for frame_left in range(w - frame_w + 1):
        frame_cols = set(range(frame_left, frame_left + frame_w))
        for obj_left in range(w - obj_w + 1):
            if any(obj_left + c in frame_cols for c in leading_cols):
                candidates.append((frame_left, obj_left))
    frame_left, obj_left = ctx.draw_rng("perpendicular_alignment").choice(candidates)
    return frame_top, frame_left, obj_top, obj_left


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = sample_index % LESSON_SCHEDULE_PERIOD
    h, w = _draw_dimensions(ctx, slot, difficulty)

    if ctx.overrides.get("direction") is not None:
        direction = ctx.draw_choice("direction", DIRECTIONS)
    else:
        direction = ctx.draw_choice("direction", (_DIRECTION_SCHEDULE[slot],))
    object_cell_count = _draw_int_axis(
        ctx,
        "obj_size",
        3,
        7,
        _weighted_values(3, 7, difficulty, preferred=(4, 5)),
    )
    gap = _draw_int_axis(
        ctx,
        "gap",
        1,
        3,
        _weighted_values(1, 3, difficulty, preferred=(1, 2)),
    )
    shape = ctx.draw_rng("object_shape").choice(_SHAPES_BY_SIZE[object_cell_count])
    obj_h = max(r for r, _ in shape) + 1
    obj_w = max(c for _, c in shape) + 1

    max_frame_h = min(6, h)
    max_frame_w = min(6, w)
    if direction in ("right", "left"):
        max_frame_w = min(max_frame_w, w - obj_w - gap)
    else:
        max_frame_h = min(max_frame_h, h - obj_h - gap)
    if max_frame_h < 3 or max_frame_w < 3:  # defensive; public domains fit constructively
        raise ValueError("requested axis combination leaves no room for a 3x3 frame")

    frame_h = ctx.draw_rng("frame_h").choice(
        _weighted_values(3, max_frame_h, difficulty, preferred=(5, 4))
    )
    frame_w = ctx.draw_rng("frame_w").choice(
        _weighted_values(3, max_frame_w, difficulty, preferred=(4, 5))
    )
    if direction in ("right", "left"):
        frame_top, frame_left, obj_top, obj_left = _place_horizontal(
            ctx, h, w, shape, frame_h, frame_w, gap, direction
        )
    else:
        frame_top, frame_left, obj_top, obj_left = _place_vertical(
            ctx, h, w, shape, frame_h, frame_w, gap, direction
        )

    grid = full_grid(h, w, 0)
    draw_frame(
        grid,
        frame_top,
        frame_left,
        frame_top + frame_h - 1,
        frame_left + frame_w - 1,
        8,
    )
    paint_at(grid, obj_top, obj_left, shape, 2)
    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:  # construction invariant: fail loudly rather than emit a poisoned sample
        raise AssertionError("constructed invalid grid: " + "; ".join(errors))
    return grid


def _components(grid, color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    groups = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        group = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    group.add(nxt)
                    queue.append(nxt)
        groups.append(group)
    return groups


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _border(box) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _direction_gap(obj_box, frame_box) -> tuple[str, int] | None:
    or1, oc1, or2, oc2 = obj_box
    fr1, fc1, fr2, fc2 = frame_box
    candidates = []
    if oc2 < fc1 and max(or1, fr1) <= min(or2, fr2):
        candidates.append(("right", fc1 - oc2 - 1))
    if oc1 > fc2 and max(or1, fr1) <= min(or2, fr2):
        candidates.append(("left", oc1 - fc2 - 1))
    if or2 < fr1 and max(oc1, fc1) <= min(oc2, fc2):
        candidates.append(("down", fr1 - or2 - 1))
    if or1 > fr2 and max(oc1, fc1) <= min(oc2, fc2):
        candidates.append(("up", or1 - fr2 - 1))
    return candidates[0] if len(candidates) == 1 else None


def _analyze(grid) -> tuple[dict, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a non-empty list of rows"]
    if not all(isinstance(row, list) for row in grid):
        return {}, ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {}, ["grid must be non-empty and rectangular"]
    height = len(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) must be an integer color 0..9 (not bool)")
    if errors:
        return {}, errors
    if not 9 <= height <= 18 or not 10 <= width <= 20:
        errors.append(f"grid dimensions {height}x{width} outside declared 9..18 by 10..20")
    palette = {value for row in grid for value in row}
    if palette != {0, 2, 8}:
        errors.append(f"expected exactly palette {{0,2,8}}, got {sorted(palette)}")

    frames = _components(grid, 8)
    object_components = _components(grid, 2)
    if len(frames) != 1:
        errors.append(f"expected one connected color-8 frame, got {len(frames)}")
    if len(object_components) != 1:
        errors.append(f"expected one connected color-2 object, got {len(object_components)}")
    if len(frames) != 1 or len(object_components) != 1:
        return {}, errors

    frame, obj = frames[0], object_components[0]
    frame_box, obj_box = _bbox(frame), _bbox(obj)
    fr1, fc1, fr2, fc2 = frame_box
    or1, oc1, or2, oc2 = obj_box
    frame_h, frame_w = fr2 - fr1 + 1, fc2 - fc1 + 1
    obj_h, obj_w = or2 - or1 + 1, oc2 - oc1 + 1
    if frame != _border(frame_box):
        errors.append("color-8 component must be exactly a hollow rectangular border")
    if not (3 <= frame_h <= 6 and 3 <= frame_w <= 6):
        errors.append(f"frame dimensions {frame_h}x{frame_w} outside 3..6")
    if not 3 <= len(obj) <= 7:
        errors.append(f"object size {len(obj)} outside 3..7")
    if obj_h > 3 or obj_w > 3:
        errors.append(f"object bbox {obj_h}x{obj_w} exceeds 3x3")

    relation = _direction_gap(obj_box, frame_box)
    if relation is None:
        errors.append("object must occupy exactly one clean cardinal lane toward the frame")
        return {}, errors
    direction, gap = relation
    if not 1 <= gap <= 3:
        errors.append(f"empty-cell gap {gap} outside 1..3")

    dr, dc = _STEP[direction]
    blockers = set(frame)
    cells = set(obj)
    steps = 0
    height, width = len(grid), len(grid[0])
    while True:
        nxt = {(r + dr, c + dc) for r, c in cells}
        if not all(0 <= r < height and 0 <= c < width for r, c in nxt):
            errors.append("object reaches a wall before docking to the frame")
            break
        if nxt & blockers:
            if steps != gap:
                errors.append(
                    f"object docks after {steps} steps, inconsistent with geometric gap {gap}"
                )
            break
        cells = nxt
        steps += 1
        if steps > max(height, width):
            errors.append("unbounded slide analysis")
            break

    stats = {
        "grid_h": height,
        "grid_w": width,
        "direction": direction,
        "obj_size": len(obj),
        "gap": gap,
        "frame_box": frame_box,
        "object_box": obj_box,
        "frame_cells": frame,
        "object_cells": obj,
    }
    return stats, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate canonical semantics and every declared sampler invariant."""
    del difficulty
    stats, errors = _analyze(grid)
    if not errors and isinstance(meta, dict):
        requested = meta.get("overrides")
        if isinstance(requested, dict):
            for name, expected in requested.items():
                if name in AXES and expected is not None and stats.get(name) != expected:
                    errors.append(
                        f"override {name}={expected!r} not observable; got {stats.get(name)!r}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    stats, errors = _analyze(grid)
    if errors:
        raise ValueError("cannot observe axes on invalid grid: " + "; ".join(errors))
    return {name: stats[name] for name in AXES}


def _slide_reference(grid):
    """Pure Python mirror of the pinned rule, used only for rivals/checks."""
    out = deepcopy(grid)
    stats, errors = _analyze(grid)
    if errors:
        return out
    cells = set(stats["object_cells"])
    dr, dc = _STEP[stats["direction"]]
    blockers = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 2)
    }
    height, width = len(grid), len(grid[0])
    while True:
        nxt = {(r + dr, c + dc) for r, c in cells}
        if not all(0 <= r < height and 0 <= c < width for r, c in nxt):
            break
        if nxt & blockers:
            break
        cells = nxt
    for r, row in enumerate(out):
        for c, value in enumerate(row):
            if value == 2:
                out[r][c] = 0
    for r, c in cells:
        out[r][c] = 2
    return out


def _no_up(grid):
    stats, errors = _analyze(grid)
    if errors or stats["direction"] == "up":
        return deepcopy(grid)
    return _slide_reference(grid)


def _up_direction_witness(grid) -> bool:
    stats, errors = _analyze(grid)
    return bool(
        not errors
        and stats["direction"] == "up"
        and _no_up(grid) != _slide_reference(grid)
    )


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "no_up": _no_up,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "up_direction": _up_direction_witness,
}
WITNESS_RIVALS = {"up_direction": ["no_up"]}


def lesson_identifiable(demos, query) -> list[str]:
    """Return surviving finite rivals that disagree with the query label."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(
                    f"rival {name!r} fits every demonstration but predicts a different query output"
                )
    return reasons
