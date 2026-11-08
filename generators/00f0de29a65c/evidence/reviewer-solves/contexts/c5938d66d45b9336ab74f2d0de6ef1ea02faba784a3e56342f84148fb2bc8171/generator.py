"""Semantic curriculum for task ``00f0de29a65c``.

The selected authority treats each monochromatic 4-connected nonzero region as
an object.  Exactly one object is a singleton marker.  Sort the remaining
objects by ``(cell_count, bbox_top, bbox_left)``; tightly crop the first object,
upscale it by two, and recolor every nonzero crop cell to the marker color.

The imported sampler mixed ordinary and deliberately ambiguous textures, ignored
some exact overrides, and almost never matched the canonical size/palette
profile.  This version uses a four-example cyclic curriculum containing a unique
minimum, a two-way minimum tie, and an all-tied canonical case.  Spatial roles
rotate independently of those profiles, and every two-way tie puts a larger
object earlier in scan order.  Every four consecutive examples therefore teach
size selection and the bbox tie-break without a profile-to-position shortcut.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00f0de29a65c"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "708518128a6f"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.50

SUMMARY = (
    "A 0-background grid contains one singleton marker and 2-4 distinct-color "
    "sparse polyominoes. Select the smallest polyomino, breaking size ties by "
    "bbox top then left; crop it, upscale 2x, and recolor nonzero cells to the "
    "marker color. A four-example schedule exposes unique minima and tied minima."
)

INVARIANTS = [
    "grid dimensions are 10..18 rows by 11..18 columns",
    "background is 0 and exactly one nonzero component is a singleton marker",
    "2-4 multi-cell monochromatic components use distinct colors",
    "all shape colors differ from the marker color",
    "shape sizes are 3..8 and every shape is sparse inside its tight bbox",
    "selection order is (cell count, bbox top, bbox left) ascending",
    "the output is the raw target bbox crop, recolored to the marker, at 2x scale",
]

SCHEDULE_PROFILES = ("unique_min", "two_way_tie", "all_tied")
_SCHEDULE_SEQUENCE = ("unique_min", "two_way_tie", "all_tied", "two_way_tie")
_CANONICAL_DIMENSIONS = ((12, 13), (11, 12), (10, 14), (12, 12), (11, 13))
_CANONICAL_PROFILES = {
    (12, 13, 5),
    (11, 12, 5),
    (10, 14, 5),
    (12, 12, 5),
    (11, 13, 5),
}
_CANONICAL_SIZE_PROFILES = {(5, 5, 5), (5, 5, 7)}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "cyclic canonical profile",
        "valid": "10..18",
        "doc": "Exact grid height; defaults stay anchored to canonical profiles.",
    },
    "grid_w": {
        "type": "int",
        "default": "cyclic canonical profile",
        "valid": "11..18",
        "doc": "Exact grid width; defaults stay anchored to canonical profiles.",
    },
    "n_shapes": {
        "type": "int",
        "default": "3",
        "valid": "2..4",
        "doc": "Exact number of multi-cell shapes.",
    },
    "texture": {
        "type": "str",
        "default": "four-slot cyclic semantic schedule",
        "valid": "|".join(SCHEDULE_PROFILES),
        "doc": (
            "unique_min has one minimum; two_way_tie has exactly two minima and "
            "a larger shape; all_tied gives every shape equal size."
        ),
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": "two_way_tie", "n_shapes": 2},
]
HELPFUL_TEXTURES = SCHEDULE_PROFILES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_COLORS = tuple(range(1, 10))

# Every base is connected, fits within 3x3, and leaves at least one zero in its
# tight bbox.  Dihedral closure provides enough morphology without a brittle
# rejection sampler.
_SHAPE_BASES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    3: (
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (1, 0), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (2, 0), (2, 1)),
    ),
    7: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    ),
    8: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ),
}


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple(sorted((row - row0, col - col0) for row, col in cells))


def _dihedral(cells: Iterable[tuple[int, int]]) -> tuple[tuple[tuple[int, int], ...], ...]:
    current = tuple(cells)
    result: set[tuple[tuple[int, int], ...]] = set()
    for _ in range(4):
        result.add(_normalize(current))
        result.add(_normalize((row, -col) for row, col in current))
        current = tuple((col, -row) for row, col in current)
    return tuple(sorted(result))


def _shape_library() -> dict[int, tuple[tuple[tuple[int, int], ...], ...]]:
    library: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {}
    for size, bases in _SHAPE_BASES.items():
        variants: set[tuple[tuple[int, int], ...]] = set()
        for base in bases:
            variants.update(_dihedral(base))
        for shape in variants:
            height = max(row for row, _ in shape) + 1
            width = max(col for _, col in shape) + 1
            if len(shape) != size or height > 3 or width > 3 or height * width <= size:
                raise AssertionError(f"invalid internal shape size={size}: {shape}")
        library[size] = tuple(sorted(variants))
    return library


_SHAPES = _shape_library()


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every consecutive four default examples cover all semantic profiles."""
    del seed, difficulty
    return _SCHEDULE_SEQUENCE[sample_index % len(_SCHEDULE_SEQUENCE)]


def _scheduled_dimensions(sample_index: int, difficulty) -> tuple[int, int]:
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return _CANONICAL_DIMENSIONS[(sample_index + offset) % len(_CANONICAL_DIMENSIONS)]


def _validate_override_types(overrides: dict[str, Any]) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_shapes"):
        if name in overrides and overrides[name] is not None:
            value = overrides[name]
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer, found {value!r}")
    if "texture" in overrides and overrides["texture"] is not None:
        if not isinstance(overrides["texture"], str):
            raise ValueError("texture must be a string")


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row0 in range(height):
        for col0 in range(width):
            color = grid[row0][col0]
            if color == 0 or (row0, col0) in seen:
                continue
            queue = deque([(row0, col0)])
            seen.add((row0, col0))
            cells: list[tuple[int, int]] = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for drow, dcol in _DIR4:
                    nxt = row + drow, col + dcol
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        queue.append(nxt)
            ordered = tuple(sorted(cells))
            components.append(
                {
                    "color": color,
                    "cells": ordered,
                    "size": len(ordered),
                    "bbox": _bbox(ordered),
                }
            )
    return components


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    if not (10 <= len(grid) <= 18 and 11 <= width <= 18):
        return [f"grid dimensions must be 10..18 by 11..18; found {len(grid)}x{width}"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid values must be integer ARC colors 0..9"]
    return []


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    if errors:
        return {
            "errors": errors,
            "components": [],
            "singles": [],
            "shapes": [],
            "texture": None,
            "target": None,
        }

    components = _components(grid)
    singles = [component for component in components if component["size"] == 1]
    shapes = [component for component in components if component["size"] > 1]
    if not any(value == 0 for row in grid for value in row):
        errors.append("background color 0 must be present")
    if len(singles) != 1:
        errors.append(f"expected exactly one singleton marker; found {len(singles)}")
    if not (2 <= len(shapes) <= 4):
        errors.append(f"expected 2..4 multi-cell shapes; found {len(shapes)}")

    colors = [component["color"] for component in components]
    if len(colors) != len(set(colors)):
        errors.append("marker and shape component colors must be pairwise distinct")

    for component in shapes:
        size = component["size"]
        if not (3 <= size <= 8):
            errors.append(f"shape sizes must be 3..8; found {size}")
        row1, col1, row2, col2 = component["bbox"]
        bbox_area = (row2 - row1 + 1) * (col2 - col1 + 1)
        if bbox_area <= size:
            errors.append("every shape must be sparse inside its tight bbox")
        own = set(component["cells"])
        intruders = [
            (row, col)
            for row in range(row1, row2 + 1)
            for col in range(col1, col2 + 1)
            if grid[row][col] != 0 and (row, col) not in own
        ]
        if intruders:
            errors.append("a shape bbox contains cells from another component")

    sizes = [component["size"] for component in shapes]
    texture = None
    target = None
    if shapes:
        target = min(
            shapes,
            key=lambda component: (
                component["size"],
                component["bbox"][0],
                component["bbox"][1],
            ),
        )
        minimum_count = sizes.count(min(sizes))
        if len(set(sizes)) == 1:
            texture = "all_tied"
        elif minimum_count == 2:
            texture = "two_way_tie"
        elif minimum_count == 1:
            texture = "unique_min"
        else:
            errors.append(
                "shape-size profile must have one minimum, exactly two minima, or all tied"
            )

    return {
        "errors": errors,
        "components": components,
        "singles": singles,
        "shapes": shapes,
        "sizes": tuple(sizes),
        "texture": texture,
        "target": target,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["texture"] is None:
        return {}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_shapes": len(analysis["shapes"]),
        "texture": analysis["texture"],
    }


def strict_canonical_like(grid) -> list[str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
    if profile not in _CANONICAL_PROFILES:
        return [f"dimensions/palette profile {profile} is outside the canonical set"]
    sizes = tuple(sorted(analysis["sizes"]))
    if sizes not in _CANONICAL_SIZE_PROFILES:
        return [f"shape-size profile {sizes} is outside the canonical set"]
    return []


def _slots_and_sizes(
    texture: str,
    n_shapes: int,
    layout_variant: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Construct a profile without binding its semantic role to one quadrant.

    Slots are TL/TR/BL/BR = 0/1/2/3.  Unique minima rotate through all four.
    Two-way ties deliberately place their larger distractor in the only occupied
    top slot and their minima in both bottom slots, so scan-order is visibly
    wrong in every tied-minimum example.  All-tied scenes rotate their omitted
    slot when fewer than four shapes are requested.
    """
    variant = layout_variant % 4
    if texture == "unique_min":
        target_slot = variant
        if n_shapes == 2:
            occupied = {target_slot, (target_slot + 2) % 4}
        elif n_shapes == 3:
            occupied = {
                target_slot,
                (target_slot + 1) % 4,
                (target_slot + 2) % 4,
            }
        else:
            occupied = set(range(4))
        slots = tuple(sorted(occupied))
        distractor_sizes = iter((5, 7, 8))
        sizes = tuple(3 if slot == target_slot else next(distractor_sizes) for slot in slots)
        return slots, sizes

    if texture == "two_way_tie":
        if n_shapes == 2:
            raise ValueError("texture='two_way_tie' requires n_shapes >= 3")
        top_distractor = variant % 2
        if n_shapes == 3:
            slots = tuple(sorted((top_distractor, 2, 3)))
            sizes = tuple(7 if slot == top_distractor else 5 for slot in slots)
        else:
            slots = (0, 1, 2, 3)
            top_sizes = {top_distractor: 7, 1 - top_distractor: 8}
            sizes = tuple(top_sizes.get(slot, 5) for slot in slots)
        return slots, sizes

    if texture == "all_tied":
        if n_shapes == 2:
            slot_options = ((0, 3), (1, 2), (0, 2), (1, 3))
            slots = slot_options[variant]
        elif n_shapes == 3:
            slots = tuple(slot for slot in range(4) if slot != variant)
        else:
            slots = (0, 1, 2, 3)
        return slots, (5,) * n_shapes
    raise ValueError(f"unknown texture {texture!r}")


def _slot_origin(slot: int, height: int, width: int) -> tuple[int, int]:
    return {
        0: (0, 0),
        1: (0, width - 4),
        2: (height - 4, 0),
        3: (height - 4, width - 4),
    }[slot]


def _place_shapes(ctx, grid, slots: tuple[int, ...], sizes: tuple[int, ...], band_tag: str):
    chosen_same_size: dict[int, set[tuple[tuple[int, int], ...]]] = {}
    placements: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for ordinal, (slot, size) in enumerate(zip(slots, sizes)):
        rng = ctx.draw_rng(f"shape:{band_tag}:{slot}:{ordinal}")
        variants = list(_SHAPES[size])
        rng.shuffle(variants)
        used = chosen_same_size.setdefault(size, set())
        shape = next((variant for variant in variants if variant not in used), variants[0])
        used.add(shape)
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        base_row, base_col = _slot_origin(slot, len(grid), len(grid[0]))
        row0 = base_row + rng.randint(0, 4 - shape_h)
        col0 = base_col + rng.randint(0, 4 - shape_w)
        cells = tuple((row0 + row, col0 + col) for row, col in shape)
        placements.append((slot, cells))
    return placements


def _marker_candidates(grid, occupied_bboxes):
    height, width = len(grid), len(grid[0])
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 0:
                continue
            if any(r1 <= row <= r2 and c1 <= col <= c2 for r1, c1, r2, c2 in occupied_bboxes):
                continue
            if any(
                0 <= row + drow < height
                and 0 <= col + dcol < width
                and grid[row + drow][col + dcol] != 0
                for drow, dcol in _DIR4
            ):
                continue
            result.append((row, col))
    return result


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_types(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"difficulty must be easy/medium/hard/None, found {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_h, scheduled_w = _scheduled_dimensions(sample_index, difficulty)
    height = ctx.draw_choice(
        "grid_h",
        tuple(range(10, 19)) if overrides.get("grid_h") is not None else (scheduled_h,),
    )
    width = ctx.draw_choice(
        "grid_w",
        tuple(range(11, 19)) if overrides.get("grid_w") is not None else (scheduled_w,),
    )
    n_shapes = ctx.draw_choice(
        "n_shapes",
        (2, 3, 4) if overrides.get("n_shapes") is not None else (3,),
    )

    scheduled_texture = schedule_profile(seed, sample_index, difficulty)
    if n_shapes == 2 and scheduled_texture == "two_way_tie" and overrides.get("texture") is None:
        scheduled_texture = "all_tied"
    texture = ctx.draw_choice(
        "texture",
        SCHEDULE_PROFILES if overrides.get("texture") is not None else (scheduled_texture,),
    )
    if texture == "two_way_tie" and n_shapes == 2:
        raise ValueError("texture='two_way_tie' is incompatible with n_shapes=2")

    layout_variant = sample_index // len(_SCHEDULE_SEQUENCE)
    slots, sizes = _slots_and_sizes(texture, n_shapes, layout_variant)
    band_tag = difficulty or "unbanded"
    grid = full_grid(height, width, 0)
    palette_rng = ctx.draw_rng(f"palette:{band_tag}")
    palette = palette_rng.sample(_COLORS, n_shapes + 1)
    marker_color, shape_colors = palette[0], palette[1:]

    placements = _place_shapes(ctx, grid, slots, sizes, band_tag)
    occupied_bboxes = []
    for color, (_slot, cells) in zip(shape_colors, placements):
        for row, col in cells:
            if grid[row][col] != 0:
                raise RuntimeError("constructive placement overlapped")
            grid[row][col] = color
        occupied_bboxes.append(_bbox(cells))

    candidates = _marker_candidates(grid, occupied_bboxes)
    if not candidates:
        raise RuntimeError("constructive placement left no isolated marker position")
    marker_rng = ctx.draw_rng(f"marker:{band_tag}")
    marker_row, marker_col = marker_rng.choice(candidates)
    grid[marker_row][marker_col] = marker_color

    findings = self_check(grid)
    if findings:
        raise RuntimeError(f"constructive generator produced invalid grid: {findings}")
    observed = observe_overrides(grid)
    requested = {
        "grid_h": height,
        "grid_w": width,
        "n_shapes": n_shapes,
        "texture": texture,
    }
    if observed != requested:
        raise RuntimeError(f"realization drift: requested {requested}, observed {observed}")
    return grid


def _raw_crop(grid, component) -> list[list[int]]:
    row1, col1, row2, col2 = component["bbox"]
    return [row[col1 : col2 + 1] for row in grid[row1 : row2 + 1]]


def _recolor(crop, color: int) -> list[list[int]]:
    return [[color if value != 0 else 0 for value in row] for row in crop]


def _upscale2(crop) -> list[list[int]]:
    output: list[list[int]] = []
    for row in crop:
        expanded = [value for value in row for _ in range(2)]
        output.extend([expanded[:], expanded[:]])
    return output


def _require_scene(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return analysis


def _render_component(grid, component, *, recolor_to=None, upscale=True, fill=False):
    crop = _raw_crop(grid, component)
    if fill:
        fill_color = recolor_to if recolor_to is not None else component["color"]
        crop = [[fill_color for _value in row] for row in crop]
    elif recolor_to is not None:
        crop = _recolor(crop, recolor_to)
    return _upscale2(crop) if upscale else crop


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for probes; Racket remains label authority."""
    analysis = _require_scene(grid)
    marker_color = analysis["singles"][-1]["color"]
    return _render_component(grid, analysis["target"], recolor_to=marker_color)


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {"errors": list(analysis["errors"])}
    target = analysis["target"]
    row1, col1, row2, col2 = target["bbox"]
    bbox_area = (row2 - row1 + 1) * (col2 - col1 + 1)
    sizes = analysis["sizes"]
    first_shape = analysis["shapes"][0]
    return {
        **observe_overrides(grid),
        "sizes": sizes,
        "minimum_count": sizes.count(min(sizes)),
        "size_contrast": min(sizes) < max(sizes),
        "target_not_first_scan": target["cells"] != first_shape["cells"],
        "target_sparse": target["size"] < bbox_area,
        "target_source_color": target["color"],
        "marker_color": analysis["singles"][-1]["color"],
        "target_size": target["size"],
        "has_size_five": 5 in sizes,
    }


def _rival_largest_shape(grid):
    analysis = _require_scene(grid)
    selected = max(
        analysis["shapes"],
        key=lambda component: (
            component["size"],
            -component["bbox"][0],
            -component["bbox"][1],
        ),
    )
    return _render_component(grid, selected, recolor_to=analysis["singles"][-1]["color"])


def _rival_scan_order(grid):
    analysis = _require_scene(grid)
    return _render_component(
        grid,
        analysis["shapes"][0],
        recolor_to=analysis["singles"][-1]["color"],
    )


def _rival_reverse_bbox_ties(grid):
    analysis = _require_scene(grid)
    selected = min(
        analysis["shapes"],
        key=lambda component: (
            component["size"],
            -component["bbox"][0],
            -component["bbox"][1],
        ),
    )
    return _render_component(grid, selected, recolor_to=analysis["singles"][-1]["color"])


def _rival_keep_source_color(grid):
    analysis = _require_scene(grid)
    return _render_component(grid, analysis["target"])


def _rival_no_upscale(grid):
    analysis = _require_scene(grid)
    return _render_component(
        grid,
        analysis["target"],
        recolor_to=analysis["singles"][-1]["color"],
        upscale=False,
    )


def _rival_bbox_fill(grid):
    analysis = _require_scene(grid)
    return _render_component(
        grid,
        analysis["target"],
        recolor_to=analysis["singles"][-1]["color"],
        fill=True,
    )


def _rival_fixed_size_five(grid):
    analysis = _require_scene(grid)
    candidates = [component for component in analysis["shapes"] if component["size"] == 5]
    selected = min(
        candidates or analysis["shapes"],
        key=lambda component: (component["bbox"][0], component["bbox"][1]),
    )
    return _render_component(grid, selected, recolor_to=analysis["singles"][-1]["color"])


def _component_quadrant(grid, component):
    row1, col1, row2, col2 = component["bbox"]
    return (
        "top" if row1 + row2 < len(grid) else "bottom",
        "left" if col1 + col2 < len(grid[0]) else "right",
    )


def _rival_profile_position(grid):
    """Old shortcut: unique minima are bottom-left; ties use first scan hit."""
    analysis = _require_scene(grid)
    if analysis["texture"] == "unique_min":
        bottom_left = [
            component
            for component in analysis["shapes"]
            if _component_quadrant(grid, component) == ("bottom", "left")
        ]
        selected = bottom_left[0] if bottom_left else analysis["shapes"][0]
    else:
        selected = analysis["shapes"][0]
    return _render_component(grid, selected, recolor_to=analysis["singles"][-1]["color"])


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "largest_shape": _rival_largest_shape,
    "scan_order": _rival_scan_order,
    "reverse_bbox_ties": _rival_reverse_bbox_ties,
    "keep_source_color": _rival_keep_source_color,
    "no_upscale": _rival_no_upscale,
    "bbox_fill": _rival_bbox_fill,
    "fixed_size_five": _rival_fixed_size_five,
    "profile_position": _rival_profile_position,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"fixed_size_five": _rival_fixed_size_five}


def _valid_observable(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    observables = semantic_observables(grid)
    return not observables.get("errors") and bool(predicate(observables))


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "size_contrast": lambda grid: _valid_observable(
        grid,
        lambda obs: obs["size_contrast"]
        and _rival_largest_shape(grid) != rule_mirror(grid),
    ),
    "position_conflict": lambda grid: _valid_observable(
        grid,
        lambda obs: obs["target_not_first_scan"]
        and _rival_scan_order(grid) != rule_mirror(grid),
    ),
    "minimum_tie": lambda grid: _valid_observable(
        grid,
        lambda obs: obs["minimum_count"] >= 2
        and _rival_reverse_bbox_ties(grid) != rule_mirror(grid),
    ),
    "marker_recolor": lambda grid: _valid_observable(
        grid,
        lambda obs: obs["target_source_color"] != obs["marker_color"]
        and _rival_keep_source_color(grid) != rule_mirror(grid),
    ),
    "upscale_factor_two": lambda grid: _valid_observable(
        grid,
        lambda _obs: _rival_no_upscale(grid) != rule_mirror(grid),
    ),
    "sparse_target": lambda grid: _valid_observable(
        grid,
        lambda obs: obs["target_sparse"]
        and _rival_bbox_fill(grid) != rule_mirror(grid),
    ),
    "fixed_size_five_distractor": lambda grid: _valid_observable(
        grid,
        lambda obs: obs["target_size"] != 5
        and obs["has_size_five"]
        and _rival_fixed_size_five(grid) != rule_mirror(grid),
    ),
    "profile_position_conflict": lambda grid: _valid_observable(
        grid,
        lambda _obs: _rival_profile_position(grid) != rule_mirror(grid),
    ),
}
WITNESS_RIVALS = {
    "size_contrast": ["largest_shape"],
    "position_conflict": ["scan_order"],
    "minimum_tie": ["reverse_bbox_ties"],
    "marker_recolor": ["keep_source_color"],
    "upscale_factor_two": ["no_upscale"],
    "sparse_target": ["bbox_fill"],
    "fixed_size_five_distractor": ["fixed_size_five"],
    "profile_position_conflict": ["profile_position"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require valid pairs and at least one visible refutation per rival."""
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is not an input/output mapping")
            continue
        findings = self_check(pair["input"])
        if findings:
            reasons.append(f"pair {index} input is unlawful: {'; '.join(findings)}")
            continue
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} output disagrees with the selected rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"lesson does not refute rival {name}")
    return reasons
