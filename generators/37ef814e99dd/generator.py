"""Semantic object-boundary curriculum for ARC task ``37ef814e99dd``.

Each nonzero 4-connected object is replaced by its *actual* cardinal
boundary in the same color.  The production domain intentionally includes
solid rectangles, concave notched objects, and objects with holes so the true
boundary rule cannot collapse to the bounding-box-perimeter shortcut.
"""
from __future__ import annotations

from collections import deque
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "37ef814e99dd"
TASK_ID = "37ef814e99dd"
VERSION = "2.0.0"
RULE_HASH = "509691e53ef9"
SUMMARY = (
    "Outline the actual 4-neighbor boundary of 2-4 distinct-color objects; "
    "the curriculum mixes rectangles with lawful concave and holed shapes."
)
INVARIANTS = [
    "literal zero is background",
    "there are two through four 4-connected objects in distinct colors",
    "every object has a bounding box at least 3x3 and at least one true interior cell",
    "objects do not cardinally touch one another",
    "rectangles, nonrectangular notches, and mixed scenes occur in production",
]

SCENE_PROFILES = ("rectangles", "notched", "mixed")
DEGENERATE_TEXTURES = ("no_blobs", "all_2x2", "already_outline")
HELPFUL_TEXTURES = SCENE_PROFILES
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
AXES = {
    "grid_h": {"type": "int", "default": "difficulty band", "valid": "10..30"},
    "grid_w": {"type": "int", "default": "difficulty band", "valid": "10..30"},
    "n_blobs": {"type": "int", "default": "difficulty band", "valid": "2..4"},
    "scene_profile": {
        "type": "str",
        "default": "sample-index cycle",
        "valid": "|".join(SCENE_PROFILES),
    },
    "texture": {
        "type": "str",
        "default": "alias for scene_profile",
        "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES),
    },
}

_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be nonempty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(cell, bool) or not isinstance(cell, int) or not 0 <= cell <= 9
        for row in grid
        for cell in row
    ):
        return ["cells must be literal ARC integer colors 0..9"]
    return []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Return same-color cardinal components in stable top-left order."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                cr, cc = current
                for dr, dc in _DIRS4:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells.sort()
            components.append({"color": color, "cells": cells})
    return components


def analyze_scene(grid: Any) -> dict[str, Any]:
    """Parse the full semantic domain or raise ``ValueError``.

    The returned objects expose their true cell sets, cardinal-boundary cells,
    bounding boxes, solidity, and genuine interior cells.  This is shared by
    the validator, Python rule mirror, parametric family, and shortcut audit.
    """
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    data = [list(row) for row in grid]
    components = _components(data)
    if not 2 <= len(components) <= 4:
        raise ValueError("expected two through four nonzero objects")

    colors = [component["color"] for component in components]
    if len(set(colors)) != len(colors):
        raise ValueError("each object must use a distinct nonzero color")

    height, width = len(data), len(data[0])
    scene_objects: list[dict[str, Any]] = []
    for component in components:
        color = component["color"]
        cells = component["cells"]
        cell_set = set(cells)
        top = min(row for row, _ in cells)
        left = min(col for _, col in cells)
        bottom = max(row for row, _ in cells)
        right = max(col for _, col in cells)
        box_height, box_width = bottom - top + 1, right - left + 1
        if box_height < 3 or box_width < 3:
            raise ValueError(f"object color {color} must span at least 3x3")

        boundary = [
            (row, col)
            for row, col in cells
            if any((row + dr, col + dc) not in cell_set for dr, dc in _DIRS4)
        ]
        interior = [
            (row, col)
            for row, col in cells
            if all((row + dr, col + dc) in cell_set for dr, dc in _DIRS4)
        ]
        if not interior:
            raise ValueError(f"object color {color} needs at least one true interior cell")
        scene_objects.append(
            {
                "color": color,
                "cells": cells,
                "size": len(cells),
                "bbox": (top, left, bottom, right),
                "height": box_height,
                "width": box_width,
                "solid_bbox": len(cells) == box_height * box_width,
                "boundary_cells": boundary,
                "interior_cells": interior,
            }
        )

    # Adjacent different colors would make the scene's object grammar depend
    # on color segmentation rather than spatial objects.  Production never
    # emits it, and the validator rejects it explicitly.
    for row in range(height):
        for col in range(width):
            color = data[row][col]
            if color == 0:
                continue
            for dr, dc in _DIRS4:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    other = data[nr][nc]
                    if other not in (0, color):
                        raise ValueError("objects of different colors must not cardinally touch")

    if all(obj["solid_bbox"] for obj in scene_objects):
        profile = "rectangles"
    elif all(not obj["solid_bbox"] for obj in scene_objects):
        profile = "notched"
    else:
        profile = "mixed"
    return {
        "height": height,
        "width": width,
        "objects": scene_objects,
        "scene_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Fail closed on identity-like or shortcut-ambiguous domains."""
    try:
        analysis = analyze_scene(grid)
    except ValueError as exc:
        return [str(exc)]
    requested = ((meta or {}).get("overrides") or {}).get("scene_profile")
    if requested is None:
        requested = ((meta or {}).get("overrides") or {}).get("texture")
    if requested in SCENE_PROFILES and analysis["scene_profile"] != requested:
        return [
            f"scene profile drifted from {requested!r} "
            f"to {analysis['scene_profile']!r}"
        ]
    return []


def _selected_objects(analysis: dict[str, Any], scope: str) -> list[dict[str, Any]]:
    if scope == "all_objects":
        return list(analysis["objects"])
    if scope not in ("largest_only", "smallest_only"):
        raise ValueError("scope must be all_objects, largest_only, or smallest_only")
    key = max if scope == "largest_only" else min
    target_size = key(obj["size"] for obj in analysis["objects"])
    selected = [obj for obj in analysis["objects"] if obj["size"] == target_size]
    if len(selected) != 1:
        raise ValueError(f"{scope} requires a unique selected object")
    return selected


def rule_mirror(grid: Any, scope: str = "all_objects") -> list[list[int]]:
    """Independent Python transcription of the true cardinal-boundary rule."""
    analysis = analyze_scene(grid)
    out = full_grid(analysis["height"], analysis["width"], 0)
    for obj in _selected_objects(analysis, scope):
        for row, col in obj["boundary_cells"]:
            out[row][col] = obj["color"]
    return out


def bbox_outline_rival(grid: Any, scope: str = "all_objects") -> list[list[int]]:
    """Plausible but wrong shortcut: paint full bounding-box perimeters."""
    analysis = analyze_scene(grid)
    out = full_grid(analysis["height"], analysis["width"], 0)
    for obj in _selected_objects(analysis, scope):
        top, left, bottom, right = obj["bbox"]
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                if row in (top, bottom) or col in (left, right):
                    out[row][col] = obj["color"]
    return out


def observe_overrides(grid: Any) -> dict[str, Any]:
    analysis = analyze_scene(grid)
    profile = analysis["scene_profile"]
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_blobs": len(analysis["objects"]),
        "scene_profile": profile,
        "texture": profile,
    }


def _shape_cells(height: int, width: int, kind: str) -> set[tuple[int, int]]:
    cells = {(row, col) for row in range(height) for col in range(width)}
    if kind == "rect":
        return cells
    if kind == "corner_notch":
        cells.remove((0, 0))
        if height >= 5 and width >= 5:
            cells.discard((0, 1))
            cells.discard((1, 0))
        return cells
    if kind == "opposite_notch":
        cells.remove((height - 1, width - 1))
        if height >= 5 and width >= 5:
            cells.discard((height - 1, width - 2))
            cells.discard((height - 2, width - 1))
        return cells
    if kind == "hole" and height >= 5 and width >= 5:
        cells.remove((height // 2, width // 2))
        return cells
    # Small boxes cannot afford a hole while retaining a true interior cell.
    cells.remove((0, width - 1))
    return cells


def _profile_kinds(profile: str, count: int) -> list[str]:
    if profile == "rectangles":
        return ["rect"] * count
    if profile == "notched":
        cycle = ("corner_notch", "opposite_notch", "hole")
        return [cycle[index % len(cycle)] for index in range(count)]
    if profile == "mixed":
        cycle = ("corner_notch", "rect", "hole", "rect")
        return [cycle[index] for index in range(count)]
    raise ValueError(f"unknown scene_profile: {profile!r}")


def _slots(height: int, width: int) -> list[tuple[int, int, int, int]]:
    """Four disjoint boxes separated by one empty center row and column."""
    middle_row, middle_col = height // 2, width // 2
    raw = [
        (1, 1, middle_row - 1, middle_col - 1),
        (middle_row + 1, middle_col + 1, height - middle_row - 2, width - middle_col - 2),
        (1, middle_col + 1, middle_row - 1, width - middle_col - 2),
        (middle_row + 1, 1, height - middle_row - 2, middle_col - 1),
    ]
    if any(slot_height < 3 or slot_width < 3 for _, _, slot_height, slot_width in raw):
        raise ValueError("grid is too small for four separated teaching slots")
    # Largest available slot first, stable order on ties.  The first authored
    # object uses it at full size; all later objects are shrunken, guaranteeing
    # a unique input-derived largest component.
    return sorted(raw, key=lambda slot: slot[2] * slot[3], reverse=True)


def _bounds_for_difficulty(difficulty: Any) -> tuple[tuple[int, int], tuple[int, int]]:
    if difficulty is None or difficulty == "medium":
        return (12, 21), (2, 3)
    if difficulty == "easy":
        return (10, 16), (2, 2)
    if difficulty == "hard":
        return (22, 30), (3, 4)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(
        set(overrides) - {"grid_h", "grid_w", "n_blobs", "scene_profile", "texture"}
    )
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture)
    if texture is not None and texture not in SCENE_PROFILES:
        raise ValueError(f"unknown texture: {texture!r}")
    if texture is not None and overrides.get("scene_profile") not in (None, texture):
        raise ValueError("texture and scene_profile disagree")
    normalized = dict(overrides)
    if texture in SCENE_PROFILES:
        normalized["scene_profile"] = texture

    dimension_band, count_band = _bounds_for_difficulty(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=normalized,
    )
    if "grid_h" in normalized and normalized["grid_h"] is not None:
        height = ctx.draw_int_strict("grid_h", 10, 30)
    else:
        height = ctx.draw_int("grid_h", *dimension_band)
    if "grid_w" in normalized and normalized["grid_w"] is not None:
        width = ctx.draw_int_strict("grid_w", 10, 30)
    else:
        width = ctx.draw_int("grid_w", *dimension_band)
    if "n_blobs" in normalized and normalized["n_blobs"] is not None:
        count = ctx.draw_int_strict("n_blobs", 2, 4)
    else:
        count = ctx.draw_int("n_blobs", *count_band)

    scheduled = SCENE_PROFILES[sample_index % len(SCENE_PROFILES)]
    profile_options = SCENE_PROFILES if normalized.get("scene_profile") is not None else (scheduled,)
    profile = ctx.draw_choice("scene_profile", profile_options)
    colors = ctx.draw_distinct_colors("object_colors", n=count, exclude={0})
    layout_rng = ctx.draw_rng("layout")

    grid = full_grid(height, width, 0)
    slots = _slots(height, width)[:count]
    kinds = _profile_kinds(profile, count)
    for index, ((slot_top, slot_left, slot_height, slot_width), color, kind) in enumerate(
        zip(slots, colors, kinds)
    ):
        if index == 0:
            box_height, box_width = slot_height, slot_width
        else:
            shrink_h = 1 + (1 if index == 3 and slot_height >= 5 else 0)
            shrink_w = 1 + (1 if index == 2 and slot_width >= 5 else 0)
            box_height = max(3, slot_height - shrink_h)
            box_width = max(3, slot_width - shrink_w)
        row_slack, col_slack = slot_height - box_height, slot_width - box_width
        top = slot_top + (layout_rng.randrange(row_slack + 1) if row_slack else 0)
        left = slot_left + (layout_rng.randrange(col_slack + 1) if col_slack else 0)
        for local_row, local_col in _shape_cells(box_height, box_width, kind):
            grid[top + local_row][left + local_col] = color

    analysis = analyze_scene(grid)
    if analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile!r} -> {analysis['scene_profile']!r}")
    sizes = [obj["size"] for obj in analysis["objects"]]
    if sizes.count(max(sizes)) != 1:
        raise AssertionError(f"internal largest-object tie: {sizes!r}")
    return grid


def _draw_from_degenerate(name: str) -> list[list[int]]:
    height, width = 9, 10
    grid = full_grid(height, width, 0)
    if name == "no_blobs":
        return grid
    if name == "all_2x2":
        for row in range(2):
            for col in range(2):
                grid[1 + row][1 + col] = 4
                grid[5 + row][6 + col] = 6
        return grid
    if name == "already_outline":
        for col in range(2, 6):
            grid[2][col] = 3
            grid[6][col] = 3
        for row in range(2, 7):
            grid[row][2] = 3
            grid[row][5] = 3
        # Add a second outline so rejection is about missing interiors rather
        # than merely the two-object cardinality requirement.
        for col in range(7, 10):
            grid[1][col] = 5
            grid[4][col] = 5
        for row in range(1, 5):
            grid[row][7] = 5
            grid[row][9] = 5
        return grid
    raise ValueError(f"unknown degenerate texture: {name!r}")
