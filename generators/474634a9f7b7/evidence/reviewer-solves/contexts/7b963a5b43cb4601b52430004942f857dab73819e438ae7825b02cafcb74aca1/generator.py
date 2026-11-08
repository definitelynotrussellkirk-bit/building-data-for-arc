"""Semantic generator for ARC task df978a02 / generator 474634a9f7b7.

Four differently colored 8-connected objects point toward the grid center.  The
unique largest object is the target.  The transformation keeps the target tip,
erases the center-facing tip of each other object, and paints a three-cell bar
just outside the target's opposite edge.

A four-slot lesson schedule places the target in every cardinal sector.  Two
slots use the canonical 16x16 scale and two use larger rectangular canvases, so
every four consecutive demonstrations expose all answer-bearing orientations
without collapsing the distribution to the four canonical scenes.  Each scene
also draws one of two independently constructed connected-shape families.
"""
from __future__ import annotations

from collections import deque
from collections.abc import Callable, Iterable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "474634a9f7b7"
TASK_ID = "474634a9f7b7"
VERSION = "4.1.0"
# sha256(" ".join(selected task-local target_code.split()))[:12]
RULE_HASH = "36dadf3bcc6b"

SUMMARY = (
    "On a cyan(8) background, four differently colored 8-connected objects "
    "each have one unique cell nearest the grid center. The unique largest "
    "object is the target. Keep its nearest cell, erase the nearest cell of "
    "each smaller object, and add a three-cell bar outside the target on the "
    "side opposite its center-facing tip."
)

INVARIANTS = [
    "the input palette is cyan(8) plus exactly four distinct object colors",
    "each object is one 8-connected same-color component with a unique center-facing tip",
    "the four tips face the center from four distinct cardinal sectors",
    "one object is uniquely largest and its opposite three-cell bar is fully in bounds",
    "the target tip is retained while exactly three non-target tips are erased",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

SIDES = ("top", "right", "bottom", "left")
GRID_SIZES = (16, 18, 20)
TARGET_SIZES = (16, 19, 22)
SHAPE_FAMILIES = ("layered", "branched")
PROFILE_SCHEDULE = (
    "canonical_top",
    "canonical_right",
    "expanded_bottom",
    "expanded_left",
)
_PROFILE_AXES_BY_BAND = {
    "easy": {
        "canonical_top": (16, 16, "top", 16),
        "canonical_right": (16, 16, "right", 19),
        "expanded_bottom": (16, 18, "bottom", 16),
        "expanded_left": (18, 16, "left", 19),
    },
    "medium": {
        "canonical_top": (16, 16, "top", 16),
        "canonical_right": (16, 16, "right", 19),
        "expanded_bottom": (18, 20, "bottom", 22),
        "expanded_left": (20, 18, "left", 19),
    },
    "hard": {
        "canonical_top": (16, 16, "top", 22),
        "canonical_right": (16, 16, "right", 16),
        "expanded_bottom": (20, 20, "bottom", 22),
        "expanded_left": (20, 18, "left", 19),
    },
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-slot 16|16|18|20 schedule",
        "valid": "16|18|20",
    },
    "grid_w": {
        "type": "int",
        "default": "four-slot 16|16|20|18 schedule",
        "valid": "16|18|20",
    },
    "target_side": {
        "type": "enum",
        "default": "four-slot top|right|bottom|left schedule",
        "valid": "top|right|bottom|left",
    },
    "target_size": {
        "type": "int",
        "default": "four-slot 16|19|22|19 schedule",
        "valid": "16|19|22",
    },
    "shape_family": {
        "type": "enum",
        "default": "seeded layered|branched draw",
        "valid": "layered|branched",
    },
}

# Every declared override cross-product is supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

Grid = list[list[int]]
Cell = tuple[int, int]
_DIR8: tuple[Cell, ...] = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _copy_grid(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions exceed the ARC 30x30 limit"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _neighbors8(cell: Cell) -> Iterable[Cell]:
    row, col = cell
    for dr, dc in _DIR8:
        yield row + dr, col + dc


def _components_by_color(grid: Grid, bg: int = 8) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    pending = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != bg
    }
    components: list[dict[str, Any]] = []
    while pending:
        start = min(pending)
        color = grid[start[0]][start[1]]
        cells = {start}
        pending.remove(start)
        queue: deque[Cell] = deque([start])
        while queue:
            current = queue.popleft()
            for neighbor in _neighbors8(current):
                row, col = neighbor
                if (
                    0 <= row < height
                    and 0 <= col < width
                    and neighbor in pending
                    and grid[row][col] == color
                ):
                    pending.remove(neighbor)
                    cells.add(neighbor)
                    queue.append(neighbor)
        rows = [cell[0] for cell in cells]
        cols = [cell[1] for cell in cells]
        components.append(
            {
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            }
        )
    return components


def _tip_info(component: dict[str, Any], height: int, width: int) -> tuple[Cell, int]:
    center_row = (height - 1) / 2.0
    center_col = (width - 1) / 2.0
    distances = {
        cell: (cell[0] - center_row) ** 2 + (cell[1] - center_col) ** 2
        for cell in component["cells"]
    }
    best_distance = min(distances.values())
    tied = sorted(cell for cell, distance in distances.items() if distance == best_distance)
    return tied[0], len(tied)


def _sector(component: dict[str, Any]) -> str:
    tip_row, tip_col = component["tip"]
    row1, col1, row2, col2 = component["bbox"]
    delta_row = tip_row - (row1 + row2) / 2.0
    delta_col = tip_col - (col1 + col2) / 2.0
    if abs(delta_row) > abs(delta_col):
        return "top" if delta_row > 0 else "bottom"
    return "left" if delta_col > 0 else "right"


def _bar_cells(component: dict[str, Any]) -> list[Cell]:
    tip_row, tip_col = component["tip"]
    row1, col1, row2, col2 = component["bbox"]
    side = component["side"]
    if side == "top":
        return [(row1 - 1, tip_col + offset) for offset in (-1, 0, 1)]
    if side == "bottom":
        return [(row2 + 1, tip_col + offset) for offset in (-1, 0, 1)]
    if side == "left":
        return [(tip_row + offset, col1 - 1) for offset in (-1, 0, 1)]
    return [(tip_row + offset, col2 + 1) for offset in (-1, 0, 1)]


def _analyze(grid: Grid) -> dict[str, Any]:
    height, width = len(grid), len(grid[0])
    components = _components_by_color(grid)
    for component in components:
        component["tip"], component["tip_ties"] = _tip_info(component, height, width)
        component["side"] = _sector(component)
    sizes = [component["size"] for component in components]
    largest_size = max(sizes, default=0)
    targets = [component for component in components if component["size"] == largest_size]
    target = targets[0] if len(targets) == 1 else None
    return {
        "height": height,
        "width": width,
        "components": components,
        "target": target,
        "target_ties": len(targets),
        "bar": _bar_cells(target) if target else [],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the exact task grammar while accepting every canonical input."""
    del difficulty, meta
    errors = _grid_errors(grid)
    if errors:
        return errors

    height, width = len(grid), len(grid[0])
    if not (12 <= height <= 30 and 12 <= width <= 30):
        errors.append(f"grid dimensions {height}x{width} are outside the supported grammar")

    palette = {value for row in grid for value in row}
    if 8 not in palette:
        errors.append("cyan(8) background is missing")
    object_colors = palette - {8}
    if len(object_colors) != 4:
        errors.append(f"expected exactly four object colors besides 8, found {len(object_colors)}")
    background_count = sum(value == 8 for row in grid for value in row)
    if background_count <= height * width // 2:
        errors.append("cyan(8) must be the strict majority background")

    analysis = _analyze(grid)
    components = analysis["components"]
    if len(components) != 4:
        errors.append(f"expected exactly four 8-connected same-color objects, found {len(components)}")
    counts_by_color: dict[int, int] = {}
    for component in components:
        counts_by_color[component["color"]] = counts_by_color.get(component["color"], 0) + 1
        if component["size"] < 3:
            errors.append(f"object color {component['color']} has fewer than three cells")
        if component["tip_ties"] != 1:
            errors.append(
                f"object color {component['color']} does not have a unique cell nearest the grid center"
            )
    if any(count != 1 for count in counts_by_color.values()):
        errors.append("each foreground color must form exactly one object")

    sides = [component["side"] for component in components]
    if sorted(sides) != sorted(SIDES):
        errors.append(f"object tips must represent all four cardinal sectors exactly once, found {sides}")

    target = analysis["target"]
    if analysis["target_ties"] != 1 or target is None:
        errors.append("the largest object must be unique")
    else:
        bar = analysis["bar"]
        if len(set(bar)) != 3:
            errors.append("target opposite bar must contain three distinct cells")
        for row, col in bar:
            if not (0 <= row < height and 0 <= col < width):
                errors.append("target opposite bar would leave the grid")
                break
            if grid[row][col] != 8:
                errors.append("target opposite bar destination must be background")
                break
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Executable empirical-manifold predicate linked to the four canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    analysis = _analyze(grid)
    if (len(grid), len(grid[0])) != (16, 16):
        reasons.append("canonical inputs are 16x16")
    sizes = sorted(component["size"] for component in analysis["components"])
    if not (3 <= sizes[0] <= 9 and 8 <= sizes[-2] <= 18 and 9 <= sizes[-1] <= 22):
        reasons.append(f"component sizes {sizes} are outside the canonical envelope")
    if not (29 <= sum(sizes) <= 59):
        reasons.append(f"canonical total object area is 29..59, found {sum(sizes)}")
    return reasons


def _draw_axis(ctx, overrides: dict[str, Any], label: str, scheduled: Any, legal: Iterable[Any]) -> Any:
    options = tuple(legal) if label in overrides and overrides[label] is not None else (scheduled,)
    return ctx.draw_choice(label, options)


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    del seed, difficulty
    return PROFILE_SCHEDULE[int(sample_index) % EXAMPLES_NEEDED]


def _difficulty_band(difficulty: Any) -> str:
    return difficulty if difficulty in {"easy", "medium", "hard"} else "medium"


def _direction_vectors(side: str) -> tuple[Cell, Cell]:
    if side == "top":
        return (-1, 0), (0, 1)
    if side == "right":
        return (0, 1), (1, 0)
    if side == "bottom":
        return (1, 0), (0, -1)
    if side == "left":
        return (0, -1), (-1, 0)
    raise ValueError(f"unknown side {side!r}")


def _tip_and_vectors(side: str, height: int, width: int) -> tuple[Cell, Cell, Cell]:
    half_h, half_w = height // 2, width // 2
    outward, lateral = _direction_vectors(side)
    if side == "top":
        tip = (half_h - 2, half_w + 2)
    elif side == "right":
        tip = (half_h + 2, half_w + 1)
    elif side == "bottom":
        tip = (half_h + 1, half_w - 3)
    else:
        tip = (half_h - 3, half_w - 2)
    return tip, outward, lateral


def _local_cell(tip: Cell, outward: Cell, lateral: Cell, depth: int, offset: int) -> Cell:
    return (
        tip[0] + outward[0] * depth + lateral[0] * offset,
        tip[1] + outward[1] * depth + lateral[1] * offset,
    )


def _layered_component_cells(side: str, size: int, height: int, width: int, rng) -> set[Cell]:
    """Original nested-layer construction retained as one explicit family."""
    tip, outward, lateral = _tip_and_vectors(side, height, width)
    body_needed = size - 1
    cells = {tip}

    stem_depth = min(5, body_needed)
    for depth in range(1, stem_depth + 1):
        cells.add(_local_cell(tip, outward, lateral, depth, 0))

    remaining = body_needed - stem_depth
    extras: list[Cell] = []
    # Complete each lateral layer before starting the next, so every prefix is
    # connected to the stem. Shuffle only within a layer for lawful variety.
    for offset in (1, 2, 3, 4):
        layer = [
            _local_cell(tip, outward, lateral, depth, offset)
            for depth in range(1, 6)
        ]
        rng.shuffle(layer)
        extras.extend(layer)
    cells.update(extras[:remaining])
    return cells


def _branched_component_cells(side: str, size: int, height: int, width: int, rng) -> set[Cell]:
    """Build a stem with sparse long lateral arms instead of nested layers.

    Every prefix is 8-connected.  The first two local columns are completed,
    then whole arms are added in a seeded order.  Target sizes 16/19/22 thereby
    remain visibly distinct from the layered family while preserving the same
    unique center-facing tip and side classification.
    """
    tip, outward, lateral = _tip_and_vectors(side, height, width)
    body_needed = size - 1
    local_order = [(depth, 0) for depth in range(1, 6)]
    local_order.extend((depth, 1) for depth in range(1, 6))

    arm_depths = [1, 2, 3, 4, 5]
    rng.shuffle(arm_depths)
    for depth in arm_depths:
        local_order.extend((depth, offset) for offset in (2, 3, 4))

    cells = {tip}
    cells.update(
        _local_cell(tip, outward, lateral, depth, offset)
        for depth, offset in local_order[:body_needed]
    )
    return cells


def _component_cells(
    side: str,
    size: int,
    height: int,
    width: int,
    rng,
    family: str = "layered",
) -> set[Cell]:
    constructors = {
        "layered": _layered_component_cells,
        "branched": _branched_component_cells,
    }
    try:
        cells = constructors[family](side, size, height, width, rng)
    except KeyError as exc:
        raise ValueError(f"unknown shape family {family!r}") from exc
    if len(cells) != size:
        raise RuntimeError(f"failed to construct {family} {side} object of size {size}")
    return cells


def _component_local_coordinates(component: dict[str, Any]) -> set[tuple[int, int]]:
    outward, lateral = _direction_vectors(component["side"])
    tip_row, tip_col = component["tip"]
    coordinates = set()
    for row, col in component["cells"]:
        dr, dc = row - tip_row, col - tip_col
        depth = dr * outward[0] + dc * outward[1]
        offset = dr * lateral[0] + dc * lateral[1]
        coordinates.add((depth, offset))
    return coordinates


def _infer_shape_family(component: dict[str, Any]) -> str:
    """Recover the advertised family from a generated target component."""
    coordinates = _component_local_coordinates(component)
    size = component["size"]
    if size in {16, 19}:
        return "branched" if max(offset for _depth, offset in coordinates) == 4 else "layered"
    if size == 22:
        layered_core = {
            (depth, offset)
            for depth in range(1, 6)
            for offset in range(4)
        }
        return "layered" if layered_core <= coordinates else "branched"
    raise ValueError(f"cannot infer shape family from unsupported target size {size}")


def _distractor_sizes(target_size: int) -> tuple[int, int, int]:
    return {
        16: (13, 4, 3),
        19: (18, 9, 7),
        22: (16, 14, 7),
    }[target_size]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override key(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    band = _difficulty_band(difficulty)
    scheduled_h, scheduled_w, scheduled_side, scheduled_target_size = (
        _PROFILE_AXES_BY_BAND[band][profile]
    )
    height = int(_draw_axis(ctx, overrides, "grid_h", scheduled_h, GRID_SIZES))
    width = int(_draw_axis(ctx, overrides, "grid_w", scheduled_w, GRID_SIZES))
    target_side = str(_draw_axis(ctx, overrides, "target_side", scheduled_side, SIDES))
    target_size = int(_draw_axis(ctx, overrides, "target_size", scheduled_target_size, TARGET_SIZES))
    shape_family = str(ctx.draw_choice("shape_family", SHAPE_FAMILIES))

    colors = list(ctx.draw_distinct_colors("colors", n=4, exclude={8}))
    color_rng = ctx.draw_rng("color_assignment")
    color_rng.shuffle(colors)
    size_rng = ctx.draw_rng("distractor_assignment")
    distractor_sizes = list(_distractor_sizes(target_size))
    size_rng.shuffle(distractor_sizes)

    side_sizes = {target_side: target_size}
    remaining_sides = [side for side in SIDES if side != target_side]
    side_sizes.update(dict(zip(remaining_sides, distractor_sizes)))

    grid = full_grid(height, width, 8)
    occupied: set[Cell] = set()
    for side, color in zip(SIDES, colors):
        shape_rng = ctx.draw_rng(f"shape_{side}")
        cells = _component_cells(
            side, side_sizes[side], height, width, shape_rng, family=shape_family
        )
        if occupied & cells:
            raise RuntimeError(f"internal placement collision for side {side}")
        occupied.update(cells)
        for row, col in cells:
            if not (0 <= row < height and 0 <= col < width):
                raise RuntimeError(f"internal out-of-bounds placement for side {side}")
            grid[row][col] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    return grid


def observe_overrides(grid: Grid) -> dict[str, Any]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe malformed grid: " + "; ".join(errors))
    analysis = _analyze(grid)
    target = analysis["target"]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "target_side": target["side"],
        "target_size": target["size"],
        "shape_family": _infer_shape_family(target),
    }


def _paint_bar(output: Grid, component: dict[str, Any]) -> None:
    for row, col in _bar_cells(component):
        if 0 <= row < len(output) and 0 <= col < len(output[0]):
            output[row][col] = component["color"]


def _solve_with_target(grid: Grid, target: dict[str, Any], *, erase_non_target: bool = True) -> Grid:
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    if erase_non_target:
        for component in analysis["components"]:
            if component["color"] != target["color"]:
                row, col = component["tip"]
                output[row][col] = 8
    _paint_bar(output, target)
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Python audit mirror of the selected Racket authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("rule_mirror input outside grammar: " + "; ".join(errors))
    analysis = _analyze(grid)
    return _solve_with_target(grid, analysis["target"])


def _rival_identity(grid: Grid) -> Grid:
    return _copy_grid(grid)


def _rival_largest_only(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    _paint_bar(output, analysis["target"])
    return output


def _rival_erasures_only(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    target_color = analysis["target"]["color"]
    for component in analysis["components"]:
        if component["color"] != target_color:
            row, col = component["tip"]
            output[row][col] = 8
    return output


def _rival_move_target_tip(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    output = rule_mirror(grid)
    row, col = analysis["target"]["tip"]
    output[row][col] = 8
    return output


def _rival_fixed_top_target(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    target = next(component for component in analysis["components"] if component["side"] == "top")
    return _solve_with_target(grid, target)



def _rival_top_or_right_largest(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    candidates = [
        component for component in analysis["components"]
        if component["side"] in {"top", "right"}
    ]
    target = max(candidates, key=lambda component: (component["size"], -component["color"]))
    return _solve_with_target(grid, target)

def _rival_erase_smallest_only(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    output = _copy_grid(grid)
    smallest = min(
        (component for component in analysis["components"] if component is not analysis["target"]),
        key=lambda component: (component["size"], component["color"]),
    )
    row, col = smallest["tip"]
    output[row][col] = 8
    _paint_bar(output, analysis["target"])
    return output


def _rival_fixed_top_bar(grid: Grid) -> Grid:
    analysis = _analyze(grid)
    output = _rival_erasures_only(grid)
    target = analysis["target"]
    row1, _col1, _row2, _col2 = target["bbox"]
    tip_col = target["tip"][1]
    for offset in (-1, 0, 1):
        row, col = row1 - 1, tip_col + offset
        if 0 <= row < len(output) and 0 <= col < len(output[0]):
            output[row][col] = target["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity": _rival_identity,
    "largest_only": _rival_largest_only,
    "erasures_only": _rival_erasures_only,
    "move_target_tip": _rival_move_target_tip,
    "fixed_top_target": _rival_fixed_top_target,
    "top_or_right_only": _rival_top_or_right_largest,
    "erase_smallest_only": _rival_erase_smallest_only,
    "fixed_top_bar": _rival_fixed_top_bar,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _lawful_analysis(grid: Grid) -> dict[str, Any] | None:
    return None if self_check(grid) else _analyze(grid)


def _witness_side(side: str) -> Callable[[Grid], bool]:
    def predicate(grid: Grid) -> bool:
        analysis = _lawful_analysis(grid)
        return bool(analysis and analysis["target"]["side"] == side)

    return predicate


def _witness_non_top_target(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis and analysis["target"]["side"] != "top")


def _witness_target_tip_retained(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    if not analysis:
        return False
    output = rule_mirror(grid)
    row, col = analysis["target"]["tip"]
    return output[row][col] == analysis["target"]["color"]


def _witness_three_tip_erasures(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    if not analysis:
        return False
    output = rule_mirror(grid)
    target_color = analysis["target"]["color"]
    return all(
        output[component["tip"][0]][component["tip"][1]] == 8
        for component in analysis["components"]
        if component["color"] != target_color
    )


def _witness_opposite_bar(grid: Grid) -> bool:
    analysis = _lawful_analysis(grid)
    if not analysis:
        return False
    output = rule_mirror(grid)
    color = analysis["target"]["color"]
    return all(output[row][col] == color for row, col in analysis["bar"])


SEMANTIC_WITNESSES = {
    "target_top": _witness_side("top"),
    "target_right": _witness_side("right"),
    "target_bottom": _witness_side("bottom"),
    "target_left": _witness_side("left"),
    "non_top_target": _witness_non_top_target,
    "target_tip_retained": _witness_target_tip_retained,
    "three_non_target_tips_erased": _witness_three_tip_erasures,
    "opposite_bar_added": _witness_opposite_bar,
}

WITNESS_RIVALS = {
    "target_top": ["identity", "erasures_only"],
    "target_right": ["identity", "fixed_top_target", "fixed_top_bar"],
    "target_bottom": ["identity", "fixed_top_target", "fixed_top_bar", "top_or_right_only"],
    "target_left": ["identity", "fixed_top_target", "fixed_top_bar", "top_or_right_only"],
    "non_top_target": ["fixed_top_target"],
    "target_tip_retained": ["move_target_tip"],
    "three_non_target_tips_erased": ["largest_only", "erase_smallest_only"],
    "opposite_bar_added": ["erasures_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named wrong rule survives demos and changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    candidates: dict[str, Callable[[Grid], Grid]] = {"true": rule_mirror, **SEMANTIC_RIVALS}
    survivors = set(candidates)
    reasons: list[str] = []

    for index, demo in enumerate(demos):
        grid = demo.get("input")
        official = demo.get("output")
        grammar_errors = self_check(grid)
        if grammar_errors:
            reasons.append(f"demo {index} input is outside the declared grammar: {grammar_errors[0]}")
            continue
        outputs = {name: fn(_copy_grid(grid)) for name, fn in candidates.items()}
        if outputs["true"] != official:
            reasons.append(f"demo {index} output disagrees with the Python audit mirror")
            continue
        survivors &= {name for name, output in outputs.items() if output == official}

    query_grid = query.get("input")
    query_answer = query.get("output")
    grammar_errors = self_check(query_grid)
    if grammar_errors:
        reasons.append(f"query input is outside the declared grammar: {grammar_errors[0]}")
        return reasons
    query_outputs = {name: fn(_copy_grid(query_grid)) for name, fn in candidates.items()}
    if query_outputs["true"] != query_answer:
        reasons.append("query output disagrees with the Python audit mirror")
        return reasons
    for name in sorted(survivors - {"true"}):
        if query_outputs[name] != query_answer:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons
