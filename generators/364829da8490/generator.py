"""Semantic generator for ARC task 364829da8490 — fill enclosed holes.

The selected Racket rule treats every 4-connected zero region independently.
A region is filled exactly when it does not touch the canvas border and all of
its cardinally adjacent nonzero cells have one color.  The fill color is that
local surrounding color.

Version 3 keeps the rule unchanged while making the teaching schedule safe
under every query rotation.  Its four profiles each occur twice in an
eight-pair cycle; any seven demonstrations therefore retain every profile.
The profiles carry topological counterexamples for diagonal connectivity,
disconnected one-cell boundaries, and irrelevant diagonal boundary colors.
Exact overrides are validated before GenCtx can coerce them.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "364829da8490"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c1200d217d20"
EXAMPLES_NEEDED = 7
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "For each 4-connected color-0 region, fill it with its local surrounding "
    "color iff the region does not touch the canvas border and its cardinal "
    "boundary contains exactly one nonzero color. Open regions and enclosed "
    "regions with mixed-color boundaries remain unchanged."
)

INVARIANTS = [
    "background is color 0 and all object colors are in 1..9",
    "every ordinary draw contains at least one enclosed single-color zero region",
    "closed walls may touch the canvas border; only the zero region's border contact matters",
    "open controls remain connected to the exterior zero region",
    "mixed-border controls use at least two colors around one enclosed zero region",
]

SCENE_PROFILES = (
    "rect_pair",
    "open_vs_closed",
    "mixed_border",
    "irregular_hole",
)

# Seven demonstrations plus one query expose one full eight-pair cycle.
# Repeating every profile twice means that removing any one pair still leaves
# every profile represented in the demonstrations.  Keeping all four profiles
# also preserves the selected baseline's frozen curriculum contract.
SCHEDULE_PROFILES = SCENE_PROFILES + SCENE_PROFILES
LESSON_SCHEDULE_PERIOD = len(SCHEDULE_PROFILES)
TEACHING_PROFILES = frozenset(SCENE_PROFILES)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "9..10 anchor profiles; otherwise 9..11 easy / 9..13 medium / 12..16 hard",
        "valid": "9..16",
    },
    "grid_w": {
        "type": "int",
        "default": "11..13 anchor profiles; otherwise 11..13 easy / 11..15 medium / 14..18 hard",
        "valid": "11..18",
    },
    "scene_profile": {
        "type": "str",
        "default": "eight-phase rotation-safe sample_index schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
}

_ALLOWED_OVERRIDES = frozenset(AXES)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_EIGHT = _CARDINAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))
_LOCAL_H = 9
_LOCAL_W = 11


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    errors: list[str] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"row {row_index} is not rectangular")
            break
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append(f"grid value {value!r} is not an integer color in 0..9")
                return errors
    return errors


def _components(
    grid: list[list[int]],
    *,
    zero: bool,
    same_color: bool = False,
    directions=_CARDINAL,
):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    out: list[set[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if ((value == 0) != zero) or (row, col) in seen:
                continue
            target = value
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: set[tuple[int, int]] = set()
            while queue:
                current_row, current_col = queue.popleft()
                cells.add((current_row, current_col))
                for delta_row, delta_col in directions:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    next_value = grid[next_row][next_col]
                    if zero:
                        matches = next_value == 0
                    elif same_color:
                        matches = next_value == target
                    else:
                        matches = next_value != 0
                    if matches:
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            out.append(cells)
    return out


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _is_rect_region(cells: set[tuple[int, int]]) -> bool:
    row_1, col_1, row_2, col_2 = _bbox(cells)
    return cells == {
        (row, col)
        for row in range(row_1, row_2 + 1)
        for col in range(col_1, col_2 + 1)
    }


def _rect_perimeter(row_1: int, col_1: int, row_2: int, col_2: int):
    return {
        (row, col)
        for row in range(row_1, row_2 + 1)
        for col in range(col_1, col_2 + 1)
        if row in (row_1, row_2) or col in (col_1, col_2)
    }


def _is_open_rect_component(cells: set[tuple[int, int]]) -> bool:
    row_1, col_1, row_2, col_2 = _bbox(cells)
    if row_2 - row_1 + 1 < 4 or col_2 - col_1 + 1 < 4:
        return False
    perimeter = _rect_perimeter(row_1, col_1, row_2, col_2)
    missing = perimeter - cells
    if len(missing) != 1 or not cells <= perimeter:
        return False
    gap_row, gap_col = next(iter(missing))
    return (gap_row, gap_col) not in {
        (row_1, col_1),
        (row_1, col_2),
        (row_2, col_1),
        (row_2, col_2),
    }


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])

    zero_regions = []
    for cells in _components(normalized, zero=True):
        touches_border = any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        )
        adjacent_positions: set[tuple[int, int]] = set()
        adjacent_colors: set[int] = set()
        for row, col in cells:
            for delta_row, delta_col in _CARDINAL:
                next_row, next_col = row + delta_row, col + delta_col
                if not (0 <= next_row < height and 0 <= next_col < width):
                    continue
                value = normalized[next_row][next_col]
                if value != 0:
                    adjacent_positions.add((next_row, next_col))
                    adjacent_colors.add(value)
        zero_regions.append(
            {
                "cells": cells,
                "size": len(cells),
                "touches_border": touches_border,
                "adjacent_positions": adjacent_positions,
                "adjacent_colors": tuple(sorted(adjacent_colors)),
                "rectangular": _is_rect_region(cells),
            }
        )

    fillable = [
        region
        for region in zero_regions
        if not region["touches_border"] and len(region["adjacent_colors"]) == 1
    ]
    mixed = [
        region
        for region in zero_regions
        if not region["touches_border"] and len(region["adjacent_colors"]) >= 2
    ]
    irregular_fillable = [region for region in fillable if not region["rectangular"]]

    nonzero_components = _components(normalized, zero=False, same_color=False)
    enclosed_boundary_cells = set().union(
        *(region["adjacent_positions"] for region in fillable + mixed)
    ) if fillable or mixed else set()
    components_touching_enclosure = {
        index
        for index, component in enumerate(nonzero_components)
        if component & enclosed_boundary_cells
    }

    open_components: list[set[tuple[int, int]]] = []
    for component in _components(normalized, zero=False, same_color=True):
        if _is_open_rect_component(component):
            open_components.append(component)
    open_cells = set().union(*open_components) if open_components else set()
    unknown_components = [
        component
        for index, component in enumerate(nonzero_components)
        if index not in components_touching_enclosure and not component <= open_cells
    ]

    categories = sum(
        bool(items)
        for items in (irregular_fillable, mixed, open_components)
    )
    profile = None
    if fillable and not unknown_components and categories <= 1:
        if irregular_fillable:
            profile = "irregular_hole"
        elif mixed:
            profile = "mixed_border"
        elif open_components:
            profile = "open_vs_closed"
        elif all(region["rectangular"] for region in fillable):
            profile = "rect_pair"

    local_fill_colors = [region["adjacent_colors"][0] for region in fillable]
    border_touching_fillable = sum(
        any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in region["adjacent_positions"]
        )
        for region in fillable
    )
    return {
        "errors": [],
        "grid_h": height,
        "grid_w": width,
        "profile": profile,
        "zero_region_count": len(zero_regions),
        "fillable_count": len(fillable),
        "fillable_regions": fillable,
        "rect_fillable_count": len(fillable) - len(irregular_fillable),
        "irregular_fillable_count": len(irregular_fillable),
        "mixed_border_count": len(mixed),
        "open_frame_count": len(open_components),
        "unknown_component_count": len(unknown_components),
        "border_touching_fillable_count": border_touching_fillable,
        "local_fill_colors": tuple(local_fill_colors),
        "has_multiple_local_colors": len(set(local_fill_colors)) >= 2,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or rule-hiding scenes."""
    del difficulty
    facts = semantic_observables(grid)
    errors = list(facts.get("errors", []))
    if errors:
        return errors
    if facts["fillable_count"] < 1:
        errors.append("at least one enclosed single-color zero region is required")
    if facts["unknown_component_count"]:
        errors.append("every nonzero component must bound a recognized hole or open-frame control")
    if facts["profile"] not in SCENE_PROFILES:
        errors.append("scene does not match one unambiguous declared profile")

    requested = ((meta or {}).get("overrides") or {})
    for key in _ALLOWED_OVERRIDES:
        if key not in requested:
            continue
        observed = {
            "grid_h": facts["grid_h"],
            "grid_w": facts["grid_w"],
            "scene_profile": facts["profile"],
        }[key]
        if observed != requested[key]:
            errors.append(f"override {key}={requested[key]!r} realized as {observed!r}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The declared distribution stays inside the task's topological grammar."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int | str]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts.get("profile") not in SCENE_PROFILES:
        raise ValueError("grid has no declared scene profile")
    return {
        "grid_h": int(facts["grid_h"]),
        "grid_w": int(facts["grid_w"]),
        "scene_profile": str(facts["profile"]),
    }


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Every eight-pair lesson survives any one query rotation."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    integer_axes = {
        "grid_h": (9, 16),
        "grid_w": (11, 18),
    }
    for label, (low, high) in integer_axes.items():
        if label not in overrides:
            continue
        value = overrides[label]
        if type(value) is not int:
            raise TypeError(f"override {label} must be an integer, got {value!r}")
        if not low <= value <= high:
            raise ValueError(f"override {label} must be in {low}..{high}, got {value!r}")

    if "scene_profile" in overrides:
        value = overrides["scene_profile"]
        if not isinstance(value, str):
            raise TypeError(f"override scene_profile must be a string, got {value!r}")
        if value not in SCENE_PROFILES:
            raise ValueError(
                f"override scene_profile must be one of {', '.join(SCENE_PROFILES)}, got {value!r}"
            )


def _draw_int_axis(ctx, overrides, label, default_low, default_high, valid_low, valid_high):
    low, high = (valid_low, valid_high) if label in overrides else (default_low, default_high)
    return ctx.draw_int(label, low, high)


def _band_ranges(difficulty: str | None):
    if difficulty == "easy":
        return {"grid_h": (9, 11), "grid_w": (11, 13)}
    if difficulty == "hard":
        return {"grid_h": (12, 16), "grid_w": (14, 18)}
    return {"grid_h": (9, 13), "grid_w": (11, 15)}


def _paint_outline(grid, row_1, col_1, row_2, col_2, color, *, gap=None):
    for row, col in _rect_perimeter(row_1, col_1, row_2, col_2):
        if gap is None or (row, col) != gap:
            grid[row][col] = color


def _local_scene(profile: str, colors: tuple[int, int, int, int], variant: int):
    grid = full_grid(_LOCAL_H, _LOCAL_W, 0)
    color_a, color_b, color_c, _ = colors

    if profile == "rect_pair":
        if variant % 3 == 0:
            first = (0, 0, 4, 4)
            second = (4, 6, 8, 10)
        elif variant % 3 == 1:
            first = (0, 0, 3, 5)
            second = (4, 6, 8, 10)
        else:
            first = (0, 0, 5, 4)
            second = (5, 6, 8, 10)
        _paint_outline(grid, *first, color_a)
        _paint_outline(grid, *second, color_b)

    elif profile == "open_vs_closed":
        # The missing corner joins the interior to the exterior only under
        # 8-connectivity.  The closed and open walls deliberately share a
        # color so that a rival which ignores border contact also changes the
        # exterior region.
        _paint_outline(grid, 1, 0, 5, 4, color_a)
        closed_corners = ((1, 0), (1, 4), (5, 0), (5, 4))
        closed_gap = closed_corners[variant % len(closed_corners)]
        grid[closed_gap[0]][closed_gap[1]] = 0
        # Preserve the canonical two-nonzero-color palette without changing
        # either zero-region boundary: color_b is buried inside a solid block
        # attached to the closed wall, so every cardinally adjacent zero still
        # sees only color_a.
        for row in range(5, 8):
            for col in range(1, 4):
                grid[row][col] = color_a
        grid[6][2] = color_b
        gap_options = ((5, 6), (3, 8), (6, 10), (8, 8))
        _paint_outline(grid, 3, 6, 8, 10, color_a, gap=gap_options[variant % 4])

    elif profile == "mixed_border":
        # Four disconnected cardinal neighbors enclose one zero cell.  The
        # rule depends on the boundary colors, not on wall connectivity or a
        # minimum hole area.
        center_row, center_col = 2, 2
        for delta_row, delta_col in _CARDINAL:
            grid[center_row + delta_row][center_col + delta_col] = color_a
        row_1, col_1, row_2, col_2 = 4, 6, 8, 10
        _paint_outline(grid, row_1, col_1, row_2, col_2, color_b)
        if variant % 2 == 0:
            for row in range(row_1 + 1, row_2 + 1):
                grid[row][col_2] = color_c
            for col in range(col_1 + 1, col_2 + 1):
                grid[row_2][col] = color_c
        else:
            for row in range(row_1, row_2):
                grid[row][col_1] = color_c
            for col in range(col_1, col_2):
                grid[row_1][col] = color_c

    elif profile == "irregular_hole":
        for row in range(1, 8):
            for col in range(0, 6):
                grid[row][col] = color_a
        holes = (
            {(2, 1), (2, 2), (3, 1), (4, 1), (4, 2)},
            {(2, 1), (2, 2), (2, 3), (3, 2), (4, 2)},
            {(2, 1), (2, 2), (3, 2), (3, 3), (4, 3)},
        )
        for row, col in holes[variant % len(holes)]:
            grid[row][col] = 0
        _paint_outline(grid, 2, 7, 6, 10, color_b)
        diagonal_corners = ((2, 7), (2, 10), (6, 7), (6, 10))
        corner_row, corner_col = diagonal_corners[variant % len(diagonal_corners)]
        grid[corner_row][corner_col] = color_c
    else:
        raise ValueError(f"unknown scene_profile {profile!r}")
    return grid


def _flip_local(grid, *, vertical: bool, horizontal: bool):
    out = [list(row) for row in grid]
    if vertical:
        out.reverse()
    if horizontal:
        out = [list(reversed(row)) for row in out]
    return out


def _paste_nonzero(canvas, local, top: int, left: int):
    for row in range(len(local)):
        for col in range(len(local[0])):
            if local[row][col] != 0:
                canvas[top + row][left + col] = local[row][col]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)

    scheduled = schedule_profile(seed, sample_index, difficulty)
    context_overrides = dict(overrides)
    context_overrides.setdefault("scene_profile", scheduled)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=context_overrides,
    )
    profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    # Half of every band remains anchored to the canonical 9-10 x 11-13
    # manifold.  The mixed-boundary and irregular profiles carry the larger
    # medium/hard scale, so difficulty still expands without starving hard
    # lessons of exact canonical-scale examples.
    ranges = (
        {"grid_h": (9, 10), "grid_w": (11, 13)}
        if profile in {"rect_pair", "open_vs_closed"}
        else _band_ranges(difficulty)
    )
    height = _draw_int_axis(ctx, overrides, "grid_h", *ranges["grid_h"], 9, 16)
    width = _draw_int_axis(ctx, overrides, "grid_w", *ranges["grid_w"], 11, 18)

    rng = ctx.draw_rng("layout")
    colors = tuple(rng.sample(range(1, 10), 4))
    variant = rng.randrange(12)
    local = _local_scene(profile, colors, variant)

    if profile in {"rect_pair", "open_vs_closed"}:
        corner = rng.randrange(4)
        vertical = corner >= 2
        horizontal = corner % 2 == 1
        top = height - _LOCAL_H if vertical else 0
        left = width - _LOCAL_W if horizontal else 0
    else:
        vertical = bool(rng.randrange(2))
        horizontal = bool(rng.randrange(2))
        top = rng.randint(0, height - _LOCAL_H)
        left = rng.randint(0, width - _LOCAL_W)

    local = _flip_local(local, vertical=vertical, horizontal=horizontal)
    canvas = full_grid(height, width, 0)
    _paste_nonzero(canvas, local, top, left)

    expected = {"grid_h": height, "grid_w": width, "scene_profile": profile}
    errors = self_check(canvas, difficulty=difficulty, meta={"overrides": expected})
    if errors:
        raise RuntimeError(f"constructed invalid fill-enclosed-holes scene: {errors}")
    observed = observe_overrides(canvas)
    if observed != expected:
        raise RuntimeError(f"keyed axes were not realized: {expected} -> {observed}")
    return deepcopy(canvas)


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent exact mirror for tests; Racket remains output authority."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    output = deepcopy(grid)
    facts = semantic_observables(grid)
    for region in facts["fillable_regions"]:
        color = region["adjacent_colors"][0]
        for row, col in region["cells"]:
            output[row][col] = color
    return output


def _identity(grid):
    return deepcopy(grid)


def _fill_all_enclosed_lowest_color(grid):
    output = deepcopy(grid)
    facts = semantic_observables(grid)
    for region in facts.get("fillable_regions", []):
        color = region["adjacent_colors"][0]
        for row, col in region["cells"]:
            output[row][col] = color
    errors = _grid_errors(grid)
    if errors:
        return output
    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    for cells in _components(normalized, zero=True):
        if any(row in (0, height - 1) or col in (0, width - 1) for row, col in cells):
            continue
        colors = set()
        for row, col in cells:
            for delta_row, delta_col in _CARDINAL:
                next_row, next_col = row + delta_row, col + delta_col
                if 0 <= next_row < height and 0 <= next_col < width:
                    value = normalized[next_row][next_col]
                    if value:
                        colors.add(value)
        if colors:
            color = min(colors)
            for row, col in cells:
                output[row][col] = color
    return output


def _fill_rectangular_holes_only(grid):
    output = deepcopy(grid)
    facts = semantic_observables(grid)
    for region in facts.get("fillable_regions", []):
        if not region["rectangular"]:
            continue
        color = region["adjacent_colors"][0]
        for row, col in region["cells"]:
            output[row][col] = color
    return output


def _fill_component_bboxes(grid):
    output = deepcopy(grid)
    for component in _components([list(row) for row in grid], zero=False, same_color=True):
        row_1, col_1, row_2, col_2 = _bbox(component)
        color = grid[next(iter(component))[0]][next(iter(component))[1]]
        for row in range(row_1 + 1, row_2):
            for col in range(col_1 + 1, col_2):
                if output[row][col] == 0:
                    output[row][col] = color
    return output


def _skip_border_touching_walls(grid):
    output = deepcopy(grid)
    facts = semantic_observables(grid)
    height, width = len(grid), len(grid[0])
    for region in facts.get("fillable_regions", []):
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in region["adjacent_positions"]
        ):
            continue
        color = region["adjacent_colors"][0]
        for row, col in region["cells"]:
            output[row][col] = color
    return output


def _fill_only_largest_hole(grid):
    output = deepcopy(grid)
    regions = list(semantic_observables(grid).get("fillable_regions", []))
    if not regions:
        return output
    region = max(regions, key=lambda item: (item["size"], -min(item["cells"])[0], -min(item["cells"])[1]))
    color = region["adjacent_colors"][0]
    for row, col in region["cells"]:
        output[row][col] = color
    return output


def _fill_with_global_modal_color(grid):
    output = deepcopy(grid)
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return output
    color = min((-count, value) for value, count in counts.items())[1]
    for region in semantic_observables(grid).get("fillable_regions", []):
        for row, col in region["cells"]:
            output[row][col] = color
    return output


def _fill_ignoring_border_contact(grid):
    output = deepcopy(grid)
    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    for cells in _components(normalized, zero=True):
        colors = {
            normalized[row + delta_row][col + delta_col]
            for row, col in cells
            for delta_row, delta_col in _CARDINAL
            if 0 <= row + delta_row < height
            and 0 <= col + delta_col < width
            and normalized[row + delta_row][col + delta_col] != 0
        }
        if len(colors) != 1:
            continue
        color = next(iter(colors))
        for row, col in cells:
            output[row][col] = color
    return output


def _fill_using_eight_connected_zero_regions(grid):
    output = deepcopy(grid)
    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    for cells in _components(normalized, zero=True, directions=_EIGHT):
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        ):
            continue
        colors = {
            normalized[row + delta_row][col + delta_col]
            for row, col in cells
            for delta_row, delta_col in _CARDINAL
            if 0 <= row + delta_row < height
            and 0 <= col + delta_col < width
            and normalized[row + delta_row][col + delta_col] != 0
        }
        if len(colors) != 1:
            continue
        color = next(iter(colors))
        for row, col in cells:
            output[row][col] = color
    return output


def _fill_using_eight_neighbor_boundary_colors(grid):
    output = deepcopy(grid)
    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    for cells in _components(normalized, zero=True):
        if any(
            row in (0, height - 1) or col in (0, width - 1)
            for row, col in cells
        ):
            continue
        colors = {
            normalized[row + delta_row][col + delta_col]
            for row, col in cells
            for delta_row, delta_col in _EIGHT
            if 0 <= row + delta_row < height
            and 0 <= col + delta_col < width
            and normalized[row + delta_row][col + delta_col] != 0
        }
        if len(colors) != 1:
            continue
        color = next(iter(colors))
        for row, col in cells:
            output[row][col] = color
    return output


def _positions_are_four_connected(positions: set[tuple[int, int]]) -> bool:
    if not positions:
        return False
    seen = {next(iter(positions))}
    queue = deque(seen)
    while queue:
        row, col = queue.popleft()
        for delta_row, delta_col in _CARDINAL:
            neighbor = row + delta_row, col + delta_col
            if neighbor in positions and neighbor not in seen:
                seen.add(neighbor)
                queue.append(neighbor)
    return seen == positions


def _fill_only_connected_boundaries(grid):
    output = deepcopy(grid)
    for region in semantic_observables(grid).get("fillable_regions", []):
        if not _positions_are_four_connected(region["adjacent_positions"]):
            continue
        color = region["adjacent_colors"][0]
        for row, col in region["cells"]:
            output[row][col] = color
    return output


def _skip_single_cell_holes(grid):
    output = deepcopy(grid)
    for region in semantic_observables(grid).get("fillable_regions", []):
        if region["size"] == 1:
            continue
        color = region["adjacent_colors"][0]
        for row, col in region["cells"]:
            output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity_no_fill": _identity,
    "fill_every_enclosed_region": _fill_all_enclosed_lowest_color,
    "rectangular_holes_only": _fill_rectangular_holes_only,
    "fill_nonzero_component_bboxes": _fill_component_bboxes,
    "skip_walls_touching_canvas_border": _skip_border_touching_walls,
    "fill_only_largest_hole": _fill_only_largest_hole,
    "use_one_global_modal_fill_color": _fill_with_global_modal_color,
    "ignore_border_contact": _fill_ignoring_border_contact,
    "use_eight_connected_zero_regions": _fill_using_eight_connected_zero_regions,
    "use_eight_neighbor_boundary_colors": _fill_using_eight_neighbor_boundary_colors,
    "require_connected_boundary": _fill_only_connected_boundaries,
    "skip_single_cell_holes": _skip_single_cell_holes,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_facts(grid):
    facts = semantic_observables(grid)
    return facts if not self_check(grid) else None


def _has_open_control(grid):
    facts = _valid_facts(grid)
    return bool(facts and facts["open_frame_count"])


def _has_mixed_control(grid):
    facts = _valid_facts(grid)
    return bool(facts and facts["mixed_border_count"])


def _has_irregular_hole(grid):
    facts = _valid_facts(grid)
    return bool(facts and facts["irregular_fillable_count"])


def _has_multiple_holes(grid):
    facts = _valid_facts(grid)
    return bool(facts and facts["fillable_count"] >= 2)


def _has_border_touching_wall(grid):
    facts = _valid_facts(grid)
    return bool(facts and facts["border_touching_fillable_count"])


def _has_local_color_contrast(grid):
    facts = _valid_facts(grid)
    return bool(facts and facts["has_multiple_local_colors"])


def _distinguishes(grid, rival_name: str) -> bool:
    return bool(
        _valid_facts(grid) is not None
        and SEMANTIC_RIVALS[rival_name](grid) != rule_mirror(grid)
    )


SEMANTIC_WITNESSES = {
    "enclosed_single_color_region_fills": lambda grid: _valid_facts(grid) is not None,
    "multiple_holes_are_processed_independently": _has_multiple_holes,
    "open_region_remains_background": _has_open_control,
    "mixed_color_enclosure_remains_background": _has_mixed_control,
    "irregular_enclosed_region_fills": _has_irregular_hole,
    "wall_may_touch_canvas_border": _has_border_touching_wall,
    "fill_color_is_local_to_each_region": _has_local_color_contrast,
    "border_contact_is_tested_on_zero_regions": lambda grid: _distinguishes(
        grid, "ignore_border_contact"
    ),
    "zero_regions_use_four_connectivity": lambda grid: _distinguishes(
        grid, "use_eight_connected_zero_regions"
    ),
    "boundary_colors_use_cardinal_neighbors": lambda grid: _distinguishes(
        grid, "use_eight_neighbor_boundary_colors"
    ),
    "boundary_cells_need_not_be_connected": lambda grid: _distinguishes(
        grid, "require_connected_boundary"
    ),
    "single_cell_holes_are_valid": lambda grid: _distinguishes(
        grid, "skip_single_cell_holes"
    ),
}

WITNESS_RIVALS = {
    "enclosed_single_color_region_fills": ["identity_no_fill"],
    "multiple_holes_are_processed_independently": ["fill_only_largest_hole"],
    "open_region_remains_background": ["fill_nonzero_component_bboxes"],
    "mixed_color_enclosure_remains_background": ["fill_every_enclosed_region"],
    "irregular_enclosed_region_fills": ["rectangular_holes_only"],
    "wall_may_touch_canvas_border": ["skip_walls_touching_canvas_border"],
    "fill_color_is_local_to_each_region": ["use_one_global_modal_fill_color"],
    "border_contact_is_tested_on_zero_regions": ["ignore_border_contact"],
    "zero_regions_use_four_connectivity": ["use_eight_connected_zero_regions"],
    "boundary_colors_use_cardinal_neighbors": ["use_eight_neighbor_boundary_colors"],
    "boundary_cells_need_not_be_connected": ["require_connected_boundary"],
    "single_cell_holes_are_valid": ["skip_single_cell_holes"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a rotation-safe seven-demo teaching window."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons: list[str] = []
    profiles: set[str] = set()
    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} is outside the teaching grammar: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output disagrees with the selected rule")
            continue
        profiles.add(observe_overrides(demo["input"])["scene_profile"])
        valid_demos.append(demo)

    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is outside the teaching grammar: {query_errors[0]}")
    elif query["output"] != rule_mirror(query["input"]):
        reasons.append("query output disagrees with the selected rule")

    missing = sorted(TEACHING_PROFILES - profiles)
    if missing:
        reasons.append(f"demonstrations omit decisive profile(s): {', '.join(missing)}")

    for name, competitor in LESSON_COMPETITORS.items():
        if valid_demos and all(
            competitor(demo["input"]) == demo["output"] for demo in valid_demos
        ):
            reasons.append(f"competing rule {name!r} survives every demonstration")
    return reasons


def mutation_fixtures():
    """Structural impostors that the old palette-only checker accepted."""
    all_zero = full_grid(9, 11, 0)

    isolated_cell = generate(91, 0, difficulty="easy", grid_h=16, grid_w=18)
    isolated_position = next(
        (row, col)
        for row in range(len(isolated_cell))
        for col in range(len(isolated_cell[0]))
        if isolated_cell[row][col] == 0
        and all(
            not (0 <= row + delta_row < len(isolated_cell)
                 and 0 <= col + delta_col < len(isolated_cell[0]))
            or isolated_cell[row + delta_row][col + delta_col] == 0
            for delta_row, delta_col in _CARDINAL
        )
    )
    isolated_cell[isolated_position[0]][isolated_position[1]] = 9

    solid_block = full_grid(9, 11, 0)
    for row in range(2, 6):
        for col in range(2, 7):
            solid_block[row][col] = 4

    open_only = full_grid(9, 11, 0)
    _paint_outline(open_only, 2, 2, 7, 8, 5, gap=(4, 2))

    mixed_only = full_grid(9, 11, 0)
    _paint_outline(mixed_only, 2, 2, 7, 8, 3)
    for row in range(3, 8):
        mixed_only[row][8] = 7

    return [
        ("all_zero_no_positive_hole", all_zero),
        ("unexplained_isolated_component", isolated_cell),
        ("solid_block_without_hole", solid_block),
        ("open_frame_without_positive_hole", open_only),
        ("mixed_border_hole_without_positive_hole", mixed_only),
    ]
