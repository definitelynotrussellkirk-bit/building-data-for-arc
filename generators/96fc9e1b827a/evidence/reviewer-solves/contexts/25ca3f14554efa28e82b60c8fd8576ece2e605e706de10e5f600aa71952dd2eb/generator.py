"""Generator for fe9bb13a9b18:S14_M4 — column histogram of largest.

A 0-background scene contains three separated monochrome objects.  The unique
largest object is selected by cell count; its per-column occupancies become
 top-justified cyan(8) bars.  A deterministic four-slot lesson schedule mixes
canonical-scale anchors with cases where the winner is neither the leftmost,
the widest, nor the object with the largest bounding box.
"""
from __future__ import annotations

from collections import Counter, deque
from collections.abc import Callable, Iterable
from itertools import product
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "96fc9e1b827a"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0fb26a20e01c"

SUMMARY = (
    "Three separated monochrome objects are shown on black. Select the unique "
    "largest by cell count and output its top-justified cyan column-count "
    "histogram. Every four-sample lesson includes canonical-scale anchors and "
    "counterexamples to leftmost, widest, and largest-bounding-box shortcuts."
)

INVARIANTS = [
    "background is 0 and is the modal color",
    "there are exactly three separated monochrome 4-connected objects",
    "the three objects have distinct nonzero colors",
    "exactly one object is largest by cell count",
    "the winner has 8..11 cells and a nonuniform 3..5-column profile",
    "the winner's normalized morphology is canonical or a connected skyline",
    "the output is the top-justified cyan(8) histogram of winner column counts",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled/difficulty-aware", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "scheduled/difficulty-aware", "valid": "17..24"},
    "target_shape": {
        "type": "str",
        "default": "seeded canonical-linked family",
        "valid": "c_shape|staircase|pyramid|irregular",
    },
    "target_slot": {"type": "str", "default": "four-slot lesson schedule", "valid": "left|right|bottom"},
    "distractor_style": {"type": "str", "default": "four-slot lesson schedule", "valid": "compact|shortcut"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = (0, 1, 2, 3)

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)  # keep cyan(8) output-only
_TARGET_SHAPES = ("c_shape", "staircase", "pyramid", "irregular")
_TARGET_SLOTS = ("left", "right", "bottom")
_DISTRACTOR_STYLES = ("compact", "shortcut")
_SIZE_BY_SHAPE = {"c_shape": 8, "pyramid": 9, "staircase": 10, "irregular": 11}
_SHAPE_BY_SIZE = {size: name for name, size in _SIZE_BY_SHAPE.items()}

# Exact normalized selected-object masks in the three public canonical pairs.
_C_MASK = (
    (0, 0), (0, 1), (0, 2),
    (1, 0),
    (2, 0),
    (3, 0), (3, 1), (3, 2),
)
_STAIRCASE_MASK = (
    (0, 0),
    (1, 0), (1, 1),
    (2, 0), (2, 1), (2, 2),
    (3, 0), (3, 1), (3, 2), (3, 3),
)
_PYRAMID_MASK = (
    (0, 2),
    (1, 1), (1, 2), (1, 3),
    (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
)
_CANONICAL_MASKS = (_C_MASK, _STAIRCASE_MASK, _PYRAMID_MASK)
_CANONICAL_DIMENSIONS = ((10, 17), (10, 18), (11, 18))
_CANONICAL_SHAPES = ("c_shape", "staircase", "pyramid")

_COMPACT_A = ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2))
_COMPACT_B = ((0, 0), (0, 1), (1, 0), (1, 1))


def schedule_profile(seed, sample_index, difficulty=None):
    """Four consecutive samples contain one anchor and three shortcut rebuttals."""
    del seed, difficulty
    return int(sample_index) % 4


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(row for row, _ in cells),
        min(col for _, col in cells),
        max(row for row, _ in cells),
        max(col for _, col in cells),
    )


def _mask_dimensions(mask: Iterable[tuple[int, int]]) -> tuple[int, int]:
    normalized = _normalize(mask)
    return (
        max(row for row, _ in normalized) + 1,
        max(col for _, col in normalized) + 1,
    )


def _skyline_mask(heights: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
    height = max(heights)
    return tuple(sorted(
        (row, col)
        for col, bar_height in enumerate(heights)
        for row in range(height - bar_height, height)
    ))


def _teaching_profiles(size: int) -> tuple[tuple[int, ...], ...]:
    # The shortcut decoy must remain strictly smaller while having a strictly
    # wider and larger bounding box.  These bounds make that constructive for
    # every profile rather than relying on retries.
    if size == 8:
        max_width, max_area = 4, 15
    elif size in {9, 10}:
        max_width, max_area = 5, 18
    else:
        max_width, max_area = 5, 24
    candidates: list[tuple[int, ...]] = []
    for width in range(3, max_width + 1):
        for heights in product(range(1, 5), repeat=width):
            if sum(heights) != size or len(set(heights)) < 2:
                continue
            if max(heights) * width >= max_area:
                continue
            candidates.append(tuple(heights))
    return tuple(candidates)


_PROFILES_BY_SHAPE = {
    name: _teaching_profiles(size) for name, size in _SIZE_BY_SHAPE.items()
}
assert all(_PROFILES_BY_SHAPE.values())


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height = len(grid)
    width = len(grid[0]) if grid else 0
    seen: set[tuple[int, int]] = set()
    found: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            value = grid[start_row][start_col]
            if value == 0 or (start_row, start_col) in seen:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in _CARD:
                    neighbor = (row + drow, col + dcol)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == value
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            found.append({"color": value, "cells": tuple(sorted(cells))})
    return found


def _winner(parts: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not parts:
        return None
    return max(parts, key=lambda item: len(item["cells"]))


def _column_counts(cells: Iterable[tuple[int, int]]) -> tuple[int, ...]:
    cells = tuple(cells)
    _, left, _, right = _bbox(cells)
    counts = Counter(col for _, col in cells)
    return tuple(counts[col] for col in range(left, right + 1))


def _histogram_for(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    counts = _column_counts(cells)
    if not counts:
        return []
    height = max(counts)
    return [
        [8 if row < counts[col] else 0 for col in range(len(counts))]
        for row in range(height)
    ]


def solve_intended(grid: list[list[int]]) -> list[list[int]]:
    """Small Python mirror used by focused tests and semantic rival probes."""
    selected = _winner(_components(grid))
    return _histogram_for(selected["cells"]) if selected is not None else []


def _draw_int(ctx, label: str, default_lo: int, default_hi: int) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int_strict(label, 10 if label == "grid_h" else 17, 18 if label == "grid_h" else 24)
    return ctx.draw_int_strict(label, default_lo, default_hi)


def _draw_choice(ctx, label: str, options: tuple[str, ...], scheduled: str | None = None) -> str:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    if scheduled is not None:
        return ctx.draw_choice(label, (scheduled,))
    return ctx.draw_choice(label, options)


def _slot_origin(slot: str, grid_h: int, grid_w: int, mask: tuple[tuple[int, int], ...]) -> tuple[int, int]:
    shape_h, shape_w = _mask_dimensions(mask)
    if slot == "left":
        return (1, 1)
    if slot == "right":
        return (1, grid_w - shape_w - 1)
    if slot == "bottom":
        return (grid_h - shape_h, (grid_w - shape_w) // 2)
    raise ValueError(f"unknown slot {slot!r}")


def _paint(
    grid: list[list[int]],
    slot: str,
    mask: tuple[tuple[int, int], ...],
    value: int,
) -> set[tuple[int, int]]:
    top, left = _slot_origin(slot, len(grid), len(grid[0]), mask)
    cells = {(top + row, left + col) for row, col in mask}
    for row, col in cells:
        if grid[row][col] != 0:
            raise ValueError(f"placement overlap at {(row, col)}")
        grid[row][col] = value
    return cells


def _shortcut_mask(target_size: int) -> tuple[tuple[int, int], ...]:
    if target_size == 8:
        # Seven cells spanning a 3x5 box.
        return tuple([(0, col) for col in range(5)] + [(1, 0), (2, 0)])
    if target_size in {9, 10}:
        # Eight cells spanning a 3x6 box.
        return tuple([(0, col) for col in range(6)] + [(1, 0), (2, 0)])
    # Nine cells spanning a 4x6 box.
    return tuple([(0, col) for col in range(6)] + [(1, 0), (2, 0), (3, 0)])


def _target_mask(ctx, target_shape: str, *, exact_anchor: bool) -> tuple[tuple[int, int], ...]:
    if exact_anchor:
        return {
            "c_shape": _C_MASK,
            "staircase": _STAIRCASE_MASK,
            "pyramid": _PYRAMID_MASK,
        }[target_shape]
    choices = _PROFILES_BY_SHAPE[target_shape]
    heights = ctx.draw_rng("target_profile").choice(choices)
    return _skyline_mask(heights)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    lesson_slot = schedule_profile(seed, sample_index, difficulty)
    exact_anchor = not overrides and lesson_slot == 0

    if exact_anchor:
        anchor_rng = ctx.draw_rng("canonical_anchor")
        anchor_h, anchor_w = _CANONICAL_DIMENSIONS[anchor_rng.randrange(len(_CANONICAL_DIMENSIONS))]
        grid_h = ctx.draw_int_strict("grid_h", anchor_h, anchor_h)
        grid_w = ctx.draw_int_strict("grid_w", anchor_w, anchor_w)
        target_shape = ctx.draw_choice(
            "target_shape", (_CANONICAL_SHAPES[anchor_rng.randrange(len(_CANONICAL_SHAPES))],)
        )
    else:
        if difficulty == "easy":
            h_bounds, w_bounds = (10, 11), (17, 18)
        elif difficulty == "hard":
            h_bounds, w_bounds = (11, 13), (18, 20)
        else:
            h_bounds, w_bounds = (10, 12), (17, 19)
        grid_h = _draw_int(ctx, "grid_h", *h_bounds)
        grid_w = _draw_int(ctx, "grid_w", *w_bounds)
        scheduled_shape = None
        if lesson_slot == 0:
            scheduled_shape = _CANONICAL_SHAPES[
                ctx.draw_rng("canonical_shape").randrange(len(_CANONICAL_SHAPES))
            ]
        target_shape = _draw_choice(ctx, "target_shape", _TARGET_SHAPES, scheduled_shape)

    if lesson_slot == 0:
        default_slot = "left"
        default_style = "compact"
    elif lesson_slot == 1:
        default_slot = "right"
        default_style = "shortcut"
    elif lesson_slot == 2:
        default_slot = "bottom"
        default_style = "shortcut"
    else:
        default_slot = ctx.draw_rng("scheduled_target_slot").choice(("right", "bottom"))
        default_style = "shortcut"

    target_slot = _draw_choice(ctx, "target_slot", _TARGET_SLOTS, default_slot)
    distractor_style = _draw_choice(
        ctx, "distractor_style", _DISTRACTOR_STYLES, default_style
    )

    target = _target_mask(ctx, target_shape, exact_anchor=exact_anchor)
    remaining_slots = [slot for slot in _TARGET_SLOTS if slot != target_slot]
    if distractor_style == "shortcut":
        preferred = "left" if target_slot != "left" else "right"
        if preferred not in remaining_slots:
            preferred = remaining_slots[0]
        shortcut_slot = preferred
        compact_slot = next(slot for slot in remaining_slots if slot != shortcut_slot)
        distractors = [
            (shortcut_slot, _shortcut_mask(len(target))),
            (compact_slot, _COMPACT_B),
        ]
    else:
        distractors = [
            (remaining_slots[0], _COMPACT_A),
            (remaining_slots[1], _COMPACT_B),
        ]

    palette_rng = ctx.draw_rng("palette")
    colors = tuple(palette_rng.sample(_COLORS, 3))
    grid = full_grid(grid_h, grid_w, 0)
    _paint(grid, target_slot, target, colors[0])
    _paint(grid, distractors[0][0], distractors[0][1], colors[1])
    _paint(grid, distractors[1][0], distractors[1][1], colors[2])

    errors = self_check(grid, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise ValueError(f"constructed invalid generator instance: {errors}")
    return [row[:] for row in grid]


def _target_shape_name(selected: dict[str, Any] | None) -> str | None:
    if selected is None:
        return None
    return _SHAPE_BY_SIZE.get(len(selected["cells"]))


def _slot_name(selected: dict[str, Any] | None, height: int, width: int) -> str | None:
    if selected is None:
        return None
    top, left, bottom, right = _bbox(selected["cells"])
    if top <= 1 and left <= 1:
        return "left"
    if top <= 1 and right >= width - 2:
        return "right"
    if bottom >= height - 1:
        return "bottom"
    # Canonical examples are top-left anchors.  The fallback also makes the
    # observer total for diagnostics without weakening generation checks.
    anchors = {
        "left": (1, 1),
        "right": (1, width - (right - left + 1) - 1),
        "bottom": (height - (bottom - top + 1), (width - (right - left + 1)) // 2),
    }
    return min(anchors, key=lambda name: abs(top - anchors[name][0]) + abs(left - anchors[name][1]))


def _distractor_style(parts: list[dict[str, Any]], selected: dict[str, Any] | None) -> str | None:
    if selected is None:
        return None
    target_top, target_left, target_bottom, target_right = _bbox(selected["cells"])
    target_area = (target_bottom - target_top + 1) * (target_right - target_left + 1)
    target_width = target_right - target_left + 1
    for item in parts:
        if item is selected:
            continue
        top, left, bottom, right = _bbox(item["cells"])
        area = (bottom - top + 1) * (right - left + 1)
        item_width = right - left + 1
        if area > target_area and item_width > target_width:
            return "shortcut"
    return "compact"


def observe_overrides(grid) -> dict[str, Any]:
    parts = _components(grid) if grid and grid[0] else []
    selected = _winner(parts)
    height = len(grid)
    width = len(grid[0]) if grid else 0
    return {
        "grid_h": height,
        "grid_w": width,
        "target_shape": _target_shape_name(selected),
        "target_slot": _slot_name(selected, height, width),
        "distractor_style": _distractor_style(parts, selected),
    }


def _is_supported_target(cells: Iterable[tuple[int, int]]) -> bool:
    normalized = _normalize(cells)
    if normalized in _CANONICAL_MASKS:
        return True
    size = len(normalized)
    shape_name = _SHAPE_BY_SIZE.get(size)
    if shape_name is None:
        return False
    return normalized in {
        _skyline_mask(heights) for heights in _PROFILES_BY_SHAPE[shape_name]
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be nonempty and rectangular"]
    height = len(grid)
    if not (10 <= height <= 18 and 17 <= width <= 24):
        errors.append(f"grid dimensions must be within 10..18 by 17..24, found {height}x{width}")
    values = [value for row in grid for value in row]
    if any(type(value) is not int or not 0 <= value <= 9 for value in values):
        errors.append("grid values must be integer ARC colors 0..9")
        return errors
    frequencies = Counter(values)
    if not frequencies or frequencies.most_common(1)[0][0] != 0:
        errors.append("background 0 must be the modal color")

    parts = _components(grid)
    if len(parts) != 3:
        errors.append(f"expected exactly three non-background objects, found {len(parts)}")
    if len({item["color"] for item in parts}) != len(parts):
        errors.append("the three objects must have distinct colors")
    if not parts:
        return errors

    sizes = [len(item["cells"]) for item in parts]
    largest_size = max(sizes)
    if sizes.count(largest_size) != 1:
        errors.append("largest object must be unique by cell count")
        return errors
    selected = _winner(parts)
    assert selected is not None
    if largest_size not in _SHAPE_BY_SIZE:
        errors.append(f"largest object must have 8..11 supported cells, found {largest_size}")
    if not _is_supported_target(selected["cells"]):
        errors.append("largest object is not a supported canonical/skyline morphology")
    counts = _column_counts(selected["cells"])
    if not (3 <= len(counts) <= 5) or len(set(counts)) < 2:
        errors.append("largest object must have a nonuniform 3..5-column occupancy profile")
    if any(size >= largest_size for size in sizes if size != largest_size):
        errors.append("every distractor must be strictly smaller than the target")

    owner: dict[tuple[int, int], int] = {}
    for index, item in enumerate(parts):
        for cell in item["cells"]:
            owner[cell] = index
    touching = False
    for (row, col), index in owner.items():
        for drow, dcol in _CARD:
            neighbor = (row + drow, col + dcol)
            if neighbor in owner and owner[neighbor] != index:
                touching = True
                break
        if touching:
            break
    if touching:
        errors.append("different objects must have cardinal clearance")

    answer = _histogram_for(selected["cells"])
    if {value for row in answer for value in row} != {0, 8}:
        errors.append("column histogram must contain both cyan and background")

    requested = ((meta or {}).get("overrides") or {}) if isinstance(meta, dict) else {}
    if requested and not errors:
        observed = observe_overrides(grid)
        for axis, value in requested.items():
            if value is not None and observed.get(axis) != value:
                errors.append(
                    f"override {axis} requested {value!r}, observed {observed.get(axis)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    dimensions = (len(grid), len(grid[0]))
    if dimensions not in set(_CANONICAL_DIMENSIONS):
        reasons.append(
            f"canonical dimensions are 10x17, 10x18, or 11x18, found {dimensions[0]}x{dimensions[1]}"
        )
    selected = _winner(_components(grid))
    if selected is None or _normalize(selected["cells"]) not in _CANONICAL_MASKS:
        reasons.append("selected-object morphology is not one of the three canonical masks")
    return reasons


def _choose_leftmost(grid: list[list[int]]) -> dict[str, Any] | None:
    parts = _components(grid)
    if not parts:
        return None
    return min(
        parts,
        key=lambda item: (
            _bbox(item["cells"])[1],
            _bbox(item["cells"])[0],
            -len(item["cells"]),
        ),
    )


def _choose_largest_bbox(grid: list[list[int]]) -> dict[str, Any] | None:
    parts = _components(grid)
    if not parts:
        return None
    def key(item):
        top, left, bottom, right = _bbox(item["cells"])
        return ((bottom - top + 1) * (right - left + 1), len(item["cells"]), -top, -left)
    return max(parts, key=key)


def _choose_widest(grid: list[list[int]]) -> dict[str, Any] | None:
    parts = _components(grid)
    if not parts:
        return None
    def key(item):
        top, left, _, right = _bbox(item["cells"])
        return (right - left + 1, len(item["cells"]), -top, -left)
    return max(parts, key=key)


def _solve_selected(grid, chooser) -> list[list[int]]:
    selected = chooser(grid)
    return _histogram_for(selected["cells"]) if selected is not None else []


def _rival_leftmost(grid):
    return _solve_selected(grid, _choose_leftmost)


def _rival_largest_bbox(grid):
    return _solve_selected(grid, _choose_largest_bbox)


def _rival_widest(grid):
    return _solve_selected(grid, _choose_widest)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "leftmost_object": _rival_leftmost,
    "largest_bbox_area": _rival_largest_bbox,
    "widest_object": _rival_widest,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid, rival) -> bool:
    return not self_check(grid) and rival(grid) != solve_intended(grid)


SEMANTIC_WITNESSES = {
    "exact_canonical_anchor": lambda grid: not strict_canonical_like(grid),
    "leftmost_object": lambda grid: _rival_differs(grid, _rival_leftmost),
    "largest_bbox_area": lambda grid: _rival_differs(grid, _rival_largest_bbox),
    "widest_object": lambda grid: _rival_differs(grid, _rival_widest),
}
BRANCH_WITNESSES = ("exact_canonical_anchor",)
WITNESS_RIVALS = {
    "leftmost_object": ["leftmost_object"],
    "largest_bbox_area": ["largest_bbox_area"],
    "widest_object": ["widest_object"],
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or not demos:
        return ["at least one demonstration is required"]
    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if not fits_demos:
            continue
        if competitor(query["input"]) == query["output"]:
            reasons.append(f"{name} survives every demonstration and the query")
        else:
            reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons


def mutation_fixtures():
    base = generate(
        19,
        1,
        difficulty="medium",
        grid_h=10,
        grid_w=17,
        target_shape="staircase",
        target_slot="right",
        distractor_style="shortcut",
    )
    selected = _winner(_components(base))
    assert selected is not None

    blank = full_grid(10, 17, 0)

    tied = full_grid(10, 17, 0)
    for row, col in _C_MASK:
        tied[1 + row][1 + col] = 2
        tied[5 + row][10 + col] = 3

    recolored_target_cell = [row[:] for row in base]
    row, col = selected["cells"][0]
    recolored_target_cell[row][col] = 8

    extra_target_cell = [row[:] for row in base]
    top, left, _, _ = _bbox(selected["cells"])
    extra_target_cell[top][left - 1] = selected["color"]

    fourth_object = [row[:] for row in base]
    fourth_object[0][0] = 8

    repeated_color = [row[:] for row in base]
    parts = _components(repeated_color)
    selected_color = _winner(parts)["color"]
    distractor = next(item for item in parts if item["color"] != selected_color)
    for row, col in distractor["cells"]:
        repeated_color[row][col] = selected_color

    return [
        ("blank_grid", blank),
        ("two_tied_largest_objects", tied),
        ("recolored_target_cell", recolored_target_cell),
        ("extra_target_cell", extra_target_cell),
        ("fourth_object", fourth_object),
        ("repeated_object_color", repeated_color),
    ]
