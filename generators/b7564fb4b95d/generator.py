"""Constructive generator for b7564fb4b95d — Select, Rotate, and Stamp.

The top-left color selects a source component; the top-right color is a
rotation command (1=identity, 2=90° clockwise, 3=180°, 4=270° clockwise).
The largest selected component, excluding the top-left marker, is normalized,
rotated, and centered inside every hollow rectangular frame, recolored with
that frame's color.  All non-frame material disappears from the output.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_frame

GENERATOR_ID = "b7564fb4b95d"
TASK_ID = GENERATOR_ID
RULE_HASH = "dfa4e91b5010"
VERSION = "2.0.0"
SUMMARY = (
    "Use (0,0) to select the largest same-colored source component and "
    "(0,w-1) as a 1/2/3/4 rotation command. Normalize and rotate the source, "
    "then center a recolored copy inside every hollow rectangular frame."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "the grid is rectangular, at most 30x30, and uses exact ARC colors 0..9",
    "(0,0) is a nonzero selector and (0,w-1) is a command in 1..4",
    "excluding (0,0), the selector color has a unique largest component",
    "there are 1..3 hollow rectangular frames in other colors",
    "centering the transformed source keeps every stamped cell in the grid",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-aware 11..30", "valid": "11..30"},
    "grid_w": {"type": "int", "default": "difficulty-aware 14..30", "valid": "14..30"},
    "n_frames": {"type": "int", "default": "difficulty-aware 1..3", "valid": "1..3"},
    "command_code": {"type": "int", "default": "keyed draw 1..4", "valid": "1..4"},
}

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_STEPS = ((-1, 0), (1, 0), (0, -1), (0, 1))
# Every shape fits a 3x3 box and has four distinct quarter-turn orientations.
_SOURCE_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
    ((0, 1), (1, 1), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
)


def _validate_controls(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    bounds = {
        "grid_h": (11, 30),
        "grid_w": (14, 30),
        "n_frames": (1, 3),
        "command_code": (1, 4),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer (not bool)")
        low, high = bounds[name]
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")


def _draw_axis(ctx, name: str, global_low: int, global_high: int, default_low: int, default_high: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, global_low, global_high)
    return ctx.draw_int_strict(name, default_low, default_high)


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def transform_cells(cells: Iterable[tuple[int, int]], command: int) -> tuple[tuple[int, int], ...]:
    """Normalize and apply the canonical command transform."""
    points = _normalize(cells)
    if not points:
        return ()
    height = max(row for row, _ in points) + 1
    width = max(col for _, col in points) + 1
    if command == 2:
        raw = ((col, height - 1 - row) for row, col in points)
    elif command == 3:
        raw = ((height - 1 - row, width - 1 - col) for row, col in points)
    elif command == 4:
        raw = ((width - 1 - col, row) for row, col in points)
    else:
        raw = points
    return _normalize(raw)


def _components_of_color(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component: list[tuple[int, int]] = []
        while queue:
            row, col = queue.popleft()
            component.append((row, col))
            for delta_row, delta_col in _STEPS:
                neighbor = (row + delta_row, col + delta_col)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    queue.append(neighbor)
        components.append(sorted(component))
    return components


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = tuple(cells)
    return (
        min(row for row, _ in points),
        min(col for _, col in points),
        max(row for row, _ in points),
        max(col for _, col in points),
    )


def _rect_border(cells: Iterable[tuple[int, int]]) -> bool:
    points = set(cells)
    if len(points) < 8:
        return False
    row1, col1, row2, col2 = _bbox(points)
    height = row2 - row1 + 1
    width = col2 - col1 + 1
    border = {
        (row, col)
        for row in range(row1, row2 + 1)
        for col in range(col1, col2 + 1)
        if row in (row1, row2) or col in (col1, col2)
    }
    return height >= 3 and width >= 3 and points == border


def _grid_errors(grid: Any) -> list[str]:
    if type(grid) is not list or not grid or not all(type(row) is list for row in grid):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["ragged or empty-row grid"]
    if len(grid) > 30 or width > 30:
        return [f"grid too large: {len(grid)}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be exact integer colors 0..9"]
    return []


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    """Parse the canonical source, frames, and observable control values."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    height, width = len(grid), len(grid[0])
    selector = grid[0][0]
    command = grid[0][width - 1]
    if selector == 0:
        raise ValueError("selector marker at (0,0) must be nonzero")
    if command == 0:
        raise ValueError("command marker at (0,w-1) must be nonzero")

    source_candidates = [
        component
        for component in _components_of_color(grid, selector)
        if (0, 0) not in component
    ]
    if not source_candidates:
        raise ValueError("no selector-colored source component")
    source_candidates.sort(key=lambda component: (-len(component), min(component)))
    source = source_candidates[0]
    source_size = len(source)
    tied = [component for component in source_candidates if len(component) == source_size]

    colors = sorted({value for row in grid for value in row if value != 0})
    frame_records: list[dict[str, Any]] = []
    for color in colors:
        if color in (selector, command):
            continue
        for component in _components_of_color(grid, color):
            if _rect_border(component):
                row1, col1, row2, col2 = _bbox(component)
                frame_records.append(
                    {
                        "color": color,
                        "cells": tuple(component),
                        "size": len(component),
                        "bbox": (row1, col1, row2, col2),
                        "height": row2 - row1 + 1,
                        "width": col2 - col1 + 1,
                    }
                )
    frame_records.sort(key=lambda frame: (frame["color"], frame["bbox"]))
    return {
        "grid_h": height,
        "grid_w": width,
        "selector": selector,
        "command_code": command,
        "source": tuple(source),
        "source_size": source_size,
        "source_tie_count": len(tied),
        "source_components": tuple(tuple(component) for component in source_candidates),
        "frames": tuple(frame_records),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    errors = _grid_errors(grid)
    if errors:
        return errors
    try:
        facts = scene_facts(grid)
    except ValueError as exc:
        return [str(exc)]
    if not 1 <= facts["command_code"] <= 4:
        errors.append("command marker must be one of 1, 2, 3, or 4")
    if facts["source_tie_count"] != 1:
        errors.append("selector source must be the unique largest candidate")
    if facts["source_size"] < 4:
        errors.append("source component must contain at least four cells")
    if not facts["frames"]:
        errors.append("at least one hollow rectangular frame is required")
    if len(facts["frames"]) > 3:
        errors.append("at most three hollow rectangular frames are supported")

    # The preserved rule intentionally allows a centered template to touch or
    # overwrite a thin frame border (one canonical 3x5 frame does so).  Its
    # actual safety boundary is the grid, not the nominal frame interior.
    template = transform_cells(facts["source"], facts["command_code"])
    template_height = max((row for row, _ in template), default=-1) + 1
    template_width = max((col for _, col in template), default=-1) + 1
    for index, frame in enumerate(facts["frames"]):
        row1, col1, _, _ = frame["bbox"]
        start_row = row1 + 1 + ((frame["height"] - 2) - template_height) // 2
        start_col = col1 + 1 + ((frame["width"] - 2) - template_width) // 2
        if (start_row < 0 or start_col < 0 or
                start_row + template_height > facts["grid_h"] or
                start_col + template_width > facts["grid_w"]):
            errors.append(f"centered source would leave the grid at frame {index}")

    if meta and isinstance(meta, dict) and isinstance(meta.get("overrides"), dict) and not errors:
        observed = observe_overrides(grid)
        for name, expected in meta["overrides"].items():
            if name in AXES and expected is not None and observed.get(name) != expected:
                errors.append(
                    f"override {name}={expected!r} realized as {observed.get(name)!r}"
                )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    facts = scene_facts(grid)
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_frames": len(facts["frames"]),
        "command_code": facts["command_code"],
    }


def _center_stamp(output: list[list[int]], template: tuple[tuple[int, int], ...], frame: dict[str, Any]) -> None:
    template_height = max(row for row, _ in template) + 1
    template_width = max(col for _, col in template) + 1
    row1, col1, _, _ = frame["bbox"]
    interior_height = frame["height"] - 2
    interior_width = frame["width"] - 2
    start_row = row1 + 1 + (interior_height - template_height) // 2
    start_col = col1 + 1 + (interior_width - template_width) // 2
    for row, col in template:
        output[start_row + row][start_col + col] = frame["color"]


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror of the preserved canonical Racket rule."""
    facts = scene_facts(grid)
    template = transform_cells(facts["source"], facts["command_code"])
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    for frame in facts["frames"]:
        for row, col in frame["cells"]:
            output[row][col] = frame["color"]
        _center_stamp(output, template, frame)
    return output


def _frame_boxes(
    height: int,
    width: int,
    frame_count: int,
    *,
    expansive: bool = False,
) -> tuple[tuple[int, int, int, int], ...]:
    """Return canonical-scale boxes, except for an explicit 30x30 stress request."""
    start_col = 4
    if not expansive:
        if frame_count == 1:
            frame_height = 6
            top = max(1, (height - frame_height) // 2)
            return ((top, width - 5, top + frame_height - 1, width - 1),)
        if frame_count == 2:
            return (
                (1, width - 5, 5, width - 1),
                (height - 5, width - 5, height - 1, width - 1),
            )
        return (
            (1, start_col, 5, start_col + 4),
            (1, width - 5, 5, width - 1),
            (height - 5, width - 5, height - 1, width - 1),
        )

    if frame_count == 1:
        return ((1, max(start_col, width // 2), height - 1, width - 1),)
    middle_row = (height + 1) // 2
    if frame_count == 2:
        right_col = max(start_col, width // 2)
        return (
            (1, right_col, middle_row - 1, width - 1),
            (middle_row, right_col, height - 1, width - 1),
        )
    middle_col = (start_col + width) // 2
    return (
        (1, start_col, middle_row - 1, middle_col - 1),
        (1, middle_col, middle_row - 1, width - 1),
        (middle_row, middle_col, height - 1, width - 1),
    )


def _shape_variant(shape: tuple[tuple[int, int], ...], rng) -> tuple[tuple[int, int], ...]:
    # Reflections add variety while retaining a 3x3 asymmetric source.
    points = _normalize(shape)
    height = max(row for row, _ in points) + 1
    width = max(col for _, col in points) + 1
    if rng.randrange(2):
        points = _normalize((row, width - 1 - col) for row, col in points)
    if rng.randrange(2):
        points = _normalize((height - 1 - row, col) for row, col in points)
    return points


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one exact-axis lawful selector/rotation/frame scene."""
    _validate_controls(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    bands = {
        None: ((11, 30), (14, 30), (1, 3)),
        "easy": ((11, 15), (14, 18), (1, 1)),
        "medium": ((15, 23), (18, 25), (1, 2)),
        "hard": ((23, 30), (24, 30), (2, 3)),
    }
    height_band, width_band, frame_band = bands[difficulty]
    height = _draw_axis(ctx, "grid_h", 11, 30, *height_band)
    width = _draw_axis(ctx, "grid_w", 14, 30, *width_band)
    frame_count = _draw_axis(ctx, "n_frames", 1, 3, *frame_band)
    command = _draw_axis(ctx, "command_code", 1, 4, 1, 4)

    layout_rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    shape_rng = ctx.draw_rng("source-shape")

    selector = color_rng.choice((5, 6, 7, 8, 9))
    frame_palette = [color for color in range(1, 10) if color not in (selector, command)]
    color_rng.shuffle(frame_palette)
    frame_colors = frame_palette[:frame_count]

    grid = full_grid(height, width, 0)
    grid[0][0] = selector
    grid[0][width - 1] = command

    shape = _shape_variant(shape_rng.choice(_SOURCE_SHAPES), shape_rng)
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(col for _, col in shape) + 1
    source_row = layout_rng.randint(2, max(2, height - shape_height))
    source_col = layout_rng.randint(0, max(0, 3 - shape_width))
    for delta_row, delta_col in shape:
        grid[source_row + delta_row][source_col + delta_col] = selector

    explicit_stress = (
        height == 30
        and width == 30
        and frame_count == 3
        and all(name in overrides and overrides[name] is not None
                for name in ("grid_h", "grid_w", "n_frames"))
    )
    boxes = _frame_boxes(height, width, frame_count, expansive=explicit_stress)
    for color, (row1, col1, row2, col2) in zip(frame_colors, boxes):
        if row2 - row1 + 1 < 5 or col2 - col1 + 1 < 5:
            raise RuntimeError("internal frame layout is smaller than 5x5")
        draw_frame(grid, row1, col1, row2, col2, color)

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    return grid


# Reviewer-facing semantic rivals used by generic lesson probes.
def rival_identity_transform(grid):
    facts = scene_facts(grid)
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    template = transform_cells(facts["source"], 1)
    for frame in facts["frames"]:
        for row, col in frame["cells"]:
            output[row][col] = frame["color"]
        _center_stamp(output, template, frame)
    return output


def rival_frames_only(grid):
    facts = scene_facts(grid)
    output = full_grid(facts["grid_h"], facts["grid_w"], 0)
    for frame in facts["frames"]:
        for row, col in frame["cells"]:
            output[row][col] = frame["color"]
    return output


SEMANTIC_RIVALS = {
    "ignore_command_rotation": rival_identity_transform,
    "frames_only": rival_frames_only,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
MIN_STRICT_FRAC = 1.0
