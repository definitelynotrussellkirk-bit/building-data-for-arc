"""Generator for arc_additional_puzzle_bank_volume18:M124.

The unique non-yellow marker selects an adjacent hollow yellow frame.  Fill
only that frame's zero-valued interior with the marker color; preserve the
marker, border, and every unselected frame.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "0e71518de287"
VERSION = "3.0.0"
TASK_ID = "0e71518de287"
RULE_HASH = "1e4e48495a33"

SUMMARY = (
    "A 9-10 by 10-12 zero-background grid contains exactly two disjoint "
    "hollow yellow rectangular frames and one non-yellow marker. The marker "
    "lies immediately above, below, left, or right of a frame border. Select "
    "the first adjacent frame in row-major frame order, fill only its zero "
    "interior cells with the marker color, and leave the marker, both yellow "
    "borders, and the other hollow frame unchanged. Ordinary generated rows "
    "make the marker adjacent to exactly one frame; self_check also accepts "
    "the canonical tie case because the pinned Racket authority resolves it "
    "by first-frame order."
)

INVARIANTS = [
    "background is color 0",
    "there are exactly two disjoint hollow rectangular color-4 frames",
    "there is exactly one marker whose color is neither 0 nor 4",
    "the marker is cardinally adjacent to at least one frame",
    "ordinary generated rows make the selected frame unambiguous",
    "only zero cells inside the selected frame are recolored",
]

MARKER_COLORS = (1, 2, 3, 5, 6, 7, 8, 9)
MARKER_SIDES = ("top", "bottom", "left", "right")
_CANONICAL_SIZES = ((10, 12), (9, 11), (10, 10), (9, 12))
_RELATION_PROFILES = ("balanced", "selected_smaller", "selected_larger")

AXES = {
    "grid_h": {"type": "int", "default": "canonical schedule", "valid": "9..10"},
    "grid_w": {"type": "int", "default": "canonical schedule", "valid": "10..12"},
    "marker_color": {
        "type": "color",
        "default": "scheduled non-{0,4} color",
        "valid": "1..9 (≠4)",
    },
    "marker_side": {
        "type": "str",
        "default": "scheduled side",
        "valid": "top|bottom|left|right",
    },
    "selected_frame": {
        "type": "int",
        "default": "scheduled row-major frame index",
        "valid": "0..1",
    },
}

Frame = tuple[int, int, int, int]
Grid = list[list[int]]
Scene = tuple[Frame, Frame, int, int]


def _draw_int_axis(ctx, overrides: dict[str, Any], label: str, lo: int, hi: int,
                   scheduled: int) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_choice_axis(ctx, overrides: dict[str, Any], label: str,
                      options: tuple[Any, ...], scheduled: Any) -> Any:
    if overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    return ctx.draw_choice(label, (scheduled,))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic relation schedule used by the lesson-level census."""
    del seed, difficulty
    return _RELATION_PROFILES[int(sample_index) % len(_RELATION_PROFILES)]


SCHEDULE_PROFILES = _RELATION_PROFILES


def _rect_border(frame: Frame) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = frame
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def _interior_area(frame: Frame) -> int:
    r0, c0, r1, c1 = frame
    return (r1 - r0 - 1) * (c1 - c0 - 1)


def _marker_slots(frame: Frame, side: str) -> tuple[tuple[int, int], ...]:
    r0, c0, r1, c1 = frame
    if side == "top":
        return tuple((r0 - 1, c) for c in range(c0, c1 + 1))
    if side == "bottom":
        return tuple((r1 + 1, c) for c in range(c0, c1 + 1))
    if side == "left":
        return tuple((r, c0 - 1) for r in range(r0, r1 + 1))
    if side == "right":
        return tuple((r, c1 + 1) for r in range(r0, r1 + 1))
    raise ValueError(f"unknown marker side: {side!r}")


def _marker_sides(marker: tuple[int, int], frame: Frame) -> tuple[str, ...]:
    mr, mc = marker
    r0, c0, r1, c1 = frame
    sides = []
    if mr == r0 - 1 and c0 <= mc <= c1:
        sides.append("top")
    if mr == r1 + 1 and c0 <= mc <= c1:
        sides.append("bottom")
    if mc == c0 - 1 and r0 <= mr <= r1:
        sides.append("left")
    if mc == c1 + 1 and r0 <= mr <= r1:
        sides.append("right")
    return tuple(sides)


def _candidate_frames(h: int, w: int) -> tuple[Frame, ...]:
    frames = []
    for fh in range(3, min(5, h - 2) + 1):
        for fw in range(3, min(5, w - 2) + 1):
            for r0 in range(1, h - fh):
                for c0 in range(1, w - fw):
                    frames.append((r0, c0, r0 + fh - 1, c0 + fw - 1))
    return tuple(frames)


def _bbox_overlap(a: Frame, b: Frame) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def _borders_touch(a_cells: set[tuple[int, int]],
                   b_cells: set[tuple[int, int]]) -> bool:
    if a_cells & b_cells:
        return True
    return any(
        (r + dr, c + dc) in b_cells
        for r, c in a_cells
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


@lru_cache(maxsize=None)
def _scene_options(h: int, w: int) -> dict[tuple[int, str, str], tuple[Scene, ...]]:
    """Enumerate every lawful exact-axis scene once per canvas size."""
    frames = _candidate_frames(h, w)
    borders = {frame: _rect_border(frame) for frame in frames}
    buckets: dict[tuple[int, str, str], list[Scene]] = defaultdict(list)

    for i, a in enumerate(frames):
        for b in frames[i + 1:]:
            if _bbox_overlap(a, b):
                continue
            if _borders_touch(borders[a], borders[b]):
                continue
            pair = tuple(sorted((a, b)))
            pair_borders = (borders[pair[0]], borders[pair[1]])
            areas = (_interior_area(pair[0]), _interior_area(pair[1]))

            for selected_index in (0, 1):
                other_index = 1 - selected_index
                if areas[selected_index] < areas[other_index]:
                    relation = "selected_smaller"
                elif areas[selected_index] > areas[other_index]:
                    relation = "selected_larger"
                else:
                    relation = "balanced"

                for side in MARKER_SIDES:
                    for mr, mc in _marker_slots(pair[selected_index], side):
                        if not (0 <= mr < h and 0 <= mc < w):
                            continue
                        marker = (mr, mc)
                        if marker in pair_borders[0] or marker in pair_borders[1]:
                            continue
                        # Ordinary training rows must not reproduce the canonical
                        # tie: the marker selects exactly one frame.
                        if _marker_sides(marker, pair[other_index]):
                            continue
                        scene = (pair[0], pair[1], mr, mc)
                        buckets[(selected_index, side, relation)].append(scene)
                        buckets[(selected_index, side, "any")].append(scene)

    return {key: tuple(value) for key, value in buckets.items()}


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

    size_offset = {"easy": 1, "medium": 0, "hard": 2}.get(difficulty, 0)
    scheduled_h, scheduled_w = _CANONICAL_SIZES[
        (int(seed) + int(sample_index) + size_offset) % len(_CANONICAL_SIZES)
    ]
    h = _draw_int_axis(ctx, overrides, "grid_h", 9, 10, scheduled_h)
    w = _draw_int_axis(ctx, overrides, "grid_w", 10, 12, scheduled_w)

    scheduled_color = MARKER_COLORS[
        (int(seed) + 5 * int(sample_index)) % len(MARKER_COLORS)
    ]
    marker_color = _draw_choice_axis(
        ctx, overrides, "marker_color", MARKER_COLORS, scheduled_color
    )
    scheduled_side = MARKER_SIDES[
        (3 * int(seed) + int(sample_index)) % len(MARKER_SIDES)
    ]
    marker_side = _draw_choice_axis(
        ctx, overrides, "marker_side", MARKER_SIDES, scheduled_side
    )
    scheduled_selected = (int(seed) + int(sample_index)) % 2
    selected_index = _draw_int_axis(
        ctx, overrides, "selected_frame", 0, 1, scheduled_selected
    )

    relation = schedule_profile(seed, sample_index, difficulty)
    options = _scene_options(h, w).get((selected_index, marker_side, relation), ())
    if not options:
        options = _scene_options(h, w).get((selected_index, marker_side, "any"), ())
    if not options:
        raise RuntimeError(
            f"no lawful scene for h={h} w={w} selected={selected_index} "
            f"side={marker_side} relation={relation}"
        )

    rng = ctx.draw_rng("placement")
    frame0, frame1, mr, mc = options[rng.randrange(len(options))]
    grid = full_grid(h, w, 0)
    draw_frame(grid, *frame0, 4)
    draw_frame(grid, *frame1, 4)
    grid[mr][mc] = marker_color
    return grid


def _components_of(grid: Grid, color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
                    cells.append(neighbor)
        components.append(sorted(cells))
    return components


def _frame_bbox(cells: list[tuple[int, int]]) -> Frame:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _analyse(grid: Any) -> tuple[dict[str, Any], list[str]]:
    if not isinstance(grid, list) or not grid:
        return {}, ["grid must be a nonempty list"]
    if not all(isinstance(row, list) for row in grid):
        return {}, ["every row must be a list"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return {}, ["grid must be nonempty and rectangular"]

    errors: list[str] = []
    h, w = len(grid), width
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 9):
                errors.append(f"cell {(r, c)} must be an integer color in 0..9")

    frames: list[Frame] = []
    for component in _components_of(grid, 4):
        frame = _frame_bbox(component)
        r0, c0, r1, c1 = frame
        if r1 - r0 < 2 or c1 - c0 < 2 or set(component) != _rect_border(frame):
            errors.append(f"yellow component at {frame} is not a hollow rectangular frame")
        else:
            frames.append(frame)
    frames.sort()
    if len(frames) != 2:
        errors.append(f"expected exactly two hollow yellow frames, got {len(frames)}")

    markers = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 4)
    ]
    if len(markers) != 1:
        errors.append(f"expected exactly one non-yellow marker, got {len(markers)}")
        return {
            "grid_h": h,
            "grid_w": w,
            "frames": tuple(frames),
            "markers": tuple(markers),
        }, errors

    marker = markers[0]
    adjacent = [
        index for index, frame in enumerate(frames)
        if _marker_sides(marker, frame)
    ]
    if not adjacent:
        errors.append("marker must be cardinally adjacent to at least one frame")

    selected_index = adjacent[0] if adjacent else None
    selected_side = None
    if selected_index is not None:
        sides = _marker_sides(marker, frames[selected_index])
        selected_side = sides[0] if sides else None

    info = {
        "grid_h": h,
        "grid_w": w,
        "frames": tuple(frames),
        "marker": marker,
        "marker_color": grid[marker[0]][marker[1]],
        "adjacent_indices": tuple(adjacent),
        "selected_index": selected_index,
        "selected_side": selected_side,
        "interior_areas": tuple(_interior_area(frame) for frame in frames),
    }
    return info, errors


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority grammar, including the canonical tie case."""
    del difficulty, meta
    return _analyse(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


MIN_STRICT_FRAC = 1.0


def generation_check(grid) -> list[str]:
    """Stricter curriculum check: generated markers must be unambiguous."""
    info, errors = _analyse(grid)
    if not errors and len(info["adjacent_indices"]) != 1:
        errors.append(
            f"generated marker must select exactly one frame, got {len(info['adjacent_indices'])}"
        )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "grid_h": info["grid_h"],
        "grid_w": info["grid_w"],
        "marker_color": info["marker_color"],
        "marker_side": info["selected_side"],
        "selected_frame": info["selected_index"],
    }


def _paint_frame_interior(grid: Grid, frame: Frame, color: int) -> Grid:
    output = [list(row) for row in grid]
    r0, c0, r1, c1 = frame
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if output[r][c] == 0:
                output[r][c] = color
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Python mirror of the pinned first-adjacent-frame Racket authority."""
    info, errors = _analyse(grid)
    if errors or info.get("selected_index") is None:
        return [list(row) for row in grid]
    return _paint_frame_interior(
        grid,
        info["frames"][info["selected_index"]],
        info["marker_color"],
    )


def _rival_fill_first_frame(grid: Grid) -> Grid:
    info, errors = _analyse(grid)
    if errors or not info.get("frames"):
        return [list(row) for row in grid]
    return _paint_frame_interior(grid, info["frames"][0], info["marker_color"])


def _rival_fill_largest_frame(grid: Grid) -> Grid:
    info, errors = _analyse(grid)
    if errors or not info.get("frames"):
        return [list(row) for row in grid]
    index = max(range(len(info["frames"])), key=lambda i: info["interior_areas"][i])
    return _paint_frame_interior(grid, info["frames"][index], info["marker_color"])


def _rival_fill_every_frame(grid: Grid) -> Grid:
    info, errors = _analyse(grid)
    if errors or not info.get("frames"):
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for frame in info["frames"]:
        output = _paint_frame_interior(output, frame, info["marker_color"])
    return output


def _rival_fixed_blue_fill(grid: Grid) -> Grid:
    info, errors = _analyse(grid)
    if errors or info.get("selected_index") is None:
        return [list(row) for row in grid]
    return _paint_frame_interior(grid, info["frames"][info["selected_index"]], 2)


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "fill_first_frame": _rival_fill_first_frame,
    "fill_largest_frame": _rival_fill_largest_frame,
    "fill_every_frame": _rival_fill_every_frame,
    "fixed_blue_fill": _rival_fixed_blue_fill,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _witness(grid: Grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(predicate(info))


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "selected_nonfirst_frame": lambda g: _witness(g, lambda i: i["selected_index"] == 1),
    "selected_smaller_frame": lambda g: _witness(
        g,
        lambda i: i["interior_areas"][i["selected_index"]]
        < max(i["interior_areas"]),
    ),
    "selective_fill_only": lambda g: _witness(g, lambda i: len(i["frames"]) == 2),
    "marker_color_not_blue": lambda g: _witness(g, lambda i: i["marker_color"] != 2),
    "marker_above": lambda g: _witness(g, lambda i: i["selected_side"] == "top"),
    "marker_below": lambda g: _witness(g, lambda i: i["selected_side"] == "bottom"),
    "marker_left": lambda g: _witness(g, lambda i: i["selected_side"] == "left"),
    "marker_right": lambda g: _witness(g, lambda i: i["selected_side"] == "right"),
}

WITNESS_RIVALS = {
    "selected_nonfirst_frame": ["fill_first_frame"],
    "selected_smaller_frame": ["fill_largest_frame"],
    "selective_fill_only": ["fill_every_frame"],
    "marker_color_not_blue": ["fixed_blue_fill"],
    "marker_above": ["fill_every_frame"],
    "marker_below": ["fill_every_frame"],
    "marker_left": ["fill_every_frame"],
    "marker_right": ["fill_every_frame"],
}

EXAMPLES_NEEDED = 4


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to reject every named rival before answering the query."""
    errors: list[str] = []
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(list(demos) + [query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"pair {index} must contain input and output")
            continue
        structural = self_check(pair["input"])
        if structural:
            errors.append(f"pair {index} is not authority-valid: {structural}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"pair {index} output does not match the authority")

    if errors:
        return errors

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"demonstrations do not refute rival {name}")
    return errors
