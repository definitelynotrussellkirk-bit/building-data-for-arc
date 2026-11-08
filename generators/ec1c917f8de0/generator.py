"""Generator for the corner-marker rigid-transform task.

A single color-9 marker occupies one canvas corner.  The remaining nonzero
cells form one monochrome connected blob.  The canonical Racket rule crops the
blob and chooses one of four transforms from the marker corner:

    TL -> identity, TR -> rotate clockwise,
    BL -> flip left/right, BR -> rotate 180 degrees.

The episode schedule is causal rather than merely random: each consecutive
four-sample block keeps the entire blob scene fixed and cycles through all four
marker corners.  The next block changes the blob profile.  Thus a standard
four-demo/one-query lesson visibly separates marker position from shape, color,
canvas size, placement, and cell count.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "ec1c917f8de0"
TASK_ID = GENERATOR_ID
RULE_HASH = "3a8a12acc2b6"  # sha256[:12] of whitespace-normalized canonical rule
VERSION = "4.0.0"  # causal four-corner lessons + exact observable override axes
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

SUMMARY = (
    "One color-9 marker at TL/TR/BL/BR selects identity/rotate-CW/"
    "flip-left-right/rotate-180 for a cropped monochrome asymmetric blob. "
    "Consecutive four-sample lesson blocks hold the blob scene fixed while "
    "cycling every marker corner; the following block changes blob geometry."
)

INVARIANTS = [
    "background is 0",
    "exactly one color-9 marker occupies a grid corner",
    "exactly one monochrome 4-connected non-9 blob occupies 5..8 cells",
    "the blob avoids every grid corner",
    "identity, rotate-CW, flip-left-right, and rotate-180 crops are pairwise distinct",
]

CORNER_NAMES = ("TL", "TR", "BL", "BR")
CORNER_TO_TRANSFORM = {
    "TL": "identity",
    "TR": "rotate_cw",
    "BL": "flip_lr",
    "BR": "rotate_180",
}

# Every profile is 4-connected and asymmetric under all eight D4 transforms.
# Keeping explicit profiles makes exact shape overrides observable from the
# returned grid and avoids retry/fallback drift.
SHAPE_PROFILES: dict[str, tuple[tuple[int, int], ...]] = {
    "zig5": ((0, 0), (0, 1), (0, 2), (1, 2), (1, 3)),
    "barb5": ((0, 1), (1, 0), (1, 1), (1, 2), (1, 3)),
    "skew5": ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1)),
    "hook5": ((0, 1), (1, 1), (2, 0), (2, 1), (3, 0)),
    "spur6": ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (2, 1)),
    "bent6": ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 2)),
    "fork6": ((0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 3)),
    "shelf6": ((0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 1)),
    "cup7": ((0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1)),
    "crook7": ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 1), (3, 2)),
    "branch7": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (3, 1)),
    "slope7": ((0, 1), (0, 2), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)),
    "crook8": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2), (3, 1), (3, 2)),
    "spine8": ((0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)),
    "tail8": ((0, 2), (1, 2), (1, 3), (2, 2), (2, 3), (3, 0), (3, 1), (3, 2)),
    "crown8": ((0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 1)),
}
SHAPE_NAMES = tuple(SHAPE_PROFILES)
EASY_SHAPES = tuple(name for name, cells in SHAPE_PROFILES.items() if len(cells) == 5)
MEDIUM_SHAPES = tuple(name for name, cells in SHAPE_PROFILES.items() if len(cells) <= 6)

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-banded lesson schedule", "valid": "6..12"},
    "grid_w": {"type": "int", "default": "difficulty-banded lesson schedule", "valid": "6..12"},
    "marker_corner": {"type": "enum", "default": "four-sample causal cycle", "valid": "TL|TR|BL|BR"},
    "blob_color": {"type": "color", "default": "lesson-block schedule", "valid": "1..8"},
    "shape_profile": {"type": "enum", "default": "difficulty-banded lesson-block schedule", "valid": "zig5|barb5|skew5|hook5|spur6|bent6|fork6|shelf6|cup7|crook7|branch7|slope7|crook8|spine8|tail8|crown8"},
}


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    if not cells:
        return ()
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_grid(cells: Iterable[tuple[int, int]]) -> list[list[int]]:
    cells = _normalize_cells(cells)
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    grid = full_grid(height, width, 0)
    for row, col in cells:
        grid[row][col] = 1
    return grid


def _crop_binary(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return ()
    min_r = min(row for row, _ in cells)
    max_r = max(row for row, _ in cells)
    min_c = min(col for _, col in cells)
    max_c = max(col for _, col in cells)
    return tuple(
        tuple(1 if grid[row][col] else 0 for col in range(min_c, max_c + 1))
        for row in range(min_r, max_r + 1)
    )


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _apply_transform(grid, transform: str):
    if transform == "identity":
        return deepcopy(grid)
    if transform == "rotate_cw":
        return _rotate_cw(grid)
    if transform == "flip_lr":
        return _flip_lr(grid)
    if transform == "rotate_180":
        return _rotate_180(grid)
    raise ValueError(f"unknown transform {transform!r}")


def _four_outputs(cells: Iterable[tuple[int, int]]) -> dict[str, tuple[tuple[int, ...], ...]]:
    base = _shape_grid(cells)
    return {
        corner: _crop_binary(_apply_transform(base, transform))
        for corner, transform in CORNER_TO_TRANSFORM.items()
    }


def _four_distinct(cells: Iterable[tuple[int, int]]) -> bool:
    return len(set(_four_outputs(cells).values())) == 4


def _connected_4(cells: Iterable[tuple[int, int]]) -> bool:
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _corner_name(row: int, col: int, height: int, width: int) -> str | None:
    return {
        (0, 0): "TL",
        (0, width - 1): "TR",
        (height - 1, 0): "BL",
        (height - 1, width - 1): "BR",
    }.get((row, col))


def _analyze(grid) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    if not (6 <= height <= 12 and 6 <= width <= 12):
        errors.append(f"grid dimensions must be in 6..12, found {height}x{width}")

    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    markers = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    marker_corner = None
    if len(markers) != 1:
        errors.append(f"expected exactly one color-9 marker, found {len(markers)}")
    else:
        marker_corner = _corner_name(markers[0][0], markers[0][1], height, width)
        if marker_corner is None:
            errors.append("the color-9 marker must occupy a grid corner")

    blob_cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]
    blob_colors = {grid[row][col] for row, col in blob_cells}
    blob_color = next(iter(blob_colors)) if len(blob_colors) == 1 else None
    if not blob_cells:
        errors.append("expected one non-marker blob")
    if len(blob_colors) != 1:
        errors.append(f"blob must be monochrome, found colors {sorted(blob_colors)}")
    elif blob_color not in range(1, 9):
        errors.append(f"blob color must be in 1..8, found {blob_color}")
    if blob_cells and not (5 <= len(blob_cells) <= 8):
        errors.append(f"blob must occupy 5..8 cells, found {len(blob_cells)}")
    if blob_cells and not _connected_4(blob_cells):
        errors.append("blob must be one 4-connected component")
    if any(cell in corners for cell in blob_cells):
        errors.append("blob must avoid all four grid corners")
    if blob_cells and not _four_distinct(blob_cells):
        errors.append("blob must yield four distinct corner-selected transforms")

    normalized = _normalize_cells(blob_cells)
    profile = next(
        (name for name, cells in SHAPE_PROFILES.items() if cells == normalized),
        None,
    )
    bbox = None
    if blob_cells:
        bbox = (
            min(row for row, _ in blob_cells),
            min(col for _, col in blob_cells),
            max(row for row, _ in blob_cells),
            max(col for _, col in blob_cells),
        )

    return {
        "errors": errors,
        "grid_h": height,
        "grid_w": width,
        "marker_corner": marker_corner,
        "blob_color": blob_color,
        "shape_profile": profile,
        "blob_cells": len(blob_cells),
        "bbox": bbox,
        "normalized_shape": normalized,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding scenes, not merely bad palettes."""
    return list(_analyze(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Anchor generated data to the canonical scale without copying examples."""
    facts = _analyze(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if not (8 <= facts["grid_h"] <= 10 and 8 <= facts["grid_w"] <= 10):
        reasons.append("canvas lies outside the canonical 8..10 scale envelope")
    if len({value for row in grid for value in row}) != 3:
        reasons.append("canonical inputs use exactly background, marker, and blob colors")
    return reasons


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared exact axis from the returned grid."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    if facts["shape_profile"] is None:
        raise ValueError("returned blob is not one declared shape_profile")
    return {axis: facts[axis] for axis in AXES}


def rule_mirror(grid) -> list[list[int]]:
    """Test-only Python mirror; the Racket program remains output authority."""
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("invalid corner-marker scene: " + "; ".join(facts["errors"]))
    r1, c1, r2, c2 = facts["bbox"]
    cropped = [list(row[c1:c2 + 1]) for row in grid[r1:r2 + 1]]
    return _apply_transform(cropped, CORNER_TO_TRANSFORM[facts["marker_corner"]])


def _witness_corner(name: str):
    def witness(grid) -> bool:
        facts = _analyze(grid)
        return not facts["errors"] and facts["marker_corner"] == name
    return witness


SEMANTIC_WITNESSES = {
    "marker_top_left_identity": _witness_corner("TL"),
    "marker_top_right_rotate_cw": _witness_corner("TR"),
    "marker_bottom_left_flip_lr": _witness_corner("BL"),
    "marker_bottom_right_rotate_180": _witness_corner("BR"),
}


def _scene_without_marker(grid):
    result = [list(row) for row in grid]
    for row, values in enumerate(result):
        for col, value in enumerate(values):
            if value == 9:
                result[row][col] = 0
    return tuple(tuple(row) for row in result)


def _predict_constant_transform(grid, transform: str):
    facts = _analyze(grid)
    if facts["errors"]:
        raise ValueError("; ".join(facts["errors"]))
    r1, c1, r2, c2 = facts["bbox"]
    cropped = [list(row[c1:c2 + 1]) for row in grid[r1:r2 + 1]]
    return _apply_transform(cropped, transform)


def lesson_identifiable(demos, query) -> list[str]:
    """Require causal evidence that the corner, not a nuisance cue, selects D4."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"expected at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    demo_facts = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        facts = _analyze(pair["input"])
        if facts["errors"]:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the corner transform")
            continue
        demo_facts.append(facts)

    query_facts = _analyze(query["input"])
    if query_facts["errors"]:
        reasons.append("query input is outside the teaching grammar")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with the corner transform")

    if len(demo_facts) == len(demos):
        corners = {facts["marker_corner"] for facts in demo_facts}
        if corners != set(CORNER_NAMES):
            reasons.append("demonstrations do not cover all four marker branches")

        base_scenes = {_scene_without_marker(pair["input"]) for pair in demos}
        if len(base_scenes) != 1:
            reasons.append(
                "demonstrations change nuisance cues; count/shape/color/size shortcuts remain plausible"
            )
        outputs = {
            tuple(tuple(row) for row in pair["output"])
            for pair in demos
        }
        if len(outputs) != 4:
            reasons.append("the four marker branches do not produce four distinct answers")

        if not query_facts["errors"] and _scene_without_marker(query["input"]) in base_scenes:
            reasons.append("query repeats the demonstration blob instead of testing transfer")

        # Named rival rules.  With all four markers on one identical scene,
        # every fixed transform must disagree with at least one demonstration.
        for transform in ("identity", "rotate_cw", "flip_lr", "rotate_180"):
            if all(
                _predict_constant_transform(pair["input"], transform) == pair["output"]
                for pair in demos
            ):
                if _predict_constant_transform(query["input"], transform) != query["output"]:
                    reasons.append(f"demos do not rule out fixed-transform rival {transform}")

    return reasons


def _band_values(difficulty):
    if difficulty == "easy":
        return (8, 9), (8, 9), EASY_SHAPES
    if difficulty == "medium":
        return (8, 9, 10), (8, 9, 10), MEDIUM_SHAPES
    if difficulty == "hard":
        return (9, 10, 11, 12), (9, 10, 11, 12), SHAPE_NAMES
    return (8, 9, 10), (8, 9, 10), SHAPE_NAMES


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input grid; Racket owns the output."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    user_overrides = dict(overrides)

    # Lesson-level phases are independent of sample_index.  All four examples
    # in a block therefore share every nuisance factor while marker_corner
    # cycles; the next block deterministically changes shape_profile.
    lesson_ctx = gen_ctx(
        seed=seed,
        sample_index=0,
        version=VERSION,
        task_id=f"{TASK_ID}::lesson",
        difficulty=difficulty,
        overrides={},
    )
    corner_phase = lesson_ctx.draw_int("corner_phase", 0, 3)
    shape_phase = lesson_ctx.draw_int("shape_phase", 0, len(SHAPE_NAMES) - 1)
    height_phase = lesson_ctx.draw_int("height_phase", 0, 31)
    width_phase = lesson_ctx.draw_int("width_phase", 0, 31)
    color_phase = lesson_ctx.draw_int("color_phase", 0, 7)
    row_phase = lesson_ctx.draw_int("row_phase", 0, 127)
    col_phase = lesson_ctx.draw_int("col_phase", 0, 127)

    block = sample_index // 4
    heights, widths, shape_pool = _band_values(difficulty)
    scheduled_shape = shape_pool[(shape_phase + block) % len(shape_pool)]
    scheduled = {
        "grid_h": heights[(height_phase + block) % len(heights)],
        "grid_w": widths[(width_phase + 2 * block) % len(widths)],
        "marker_corner": CORNER_NAMES[(corner_phase + sample_index) % 4],
        "blob_color": 1 + ((color_phase + block) % 8),
        "shape_profile": scheduled_shape,
    }
    effective = {**scheduled, **user_overrides}

    # Construct this context last: override/default provenance audits inspect
    # the most recent GenCtx and every declared exact axis is recorded here.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h_bounds = (6, 12) if "grid_h" in user_overrides else (min(heights), max(heights))
    w_bounds = (6, 12) if "grid_w" in user_overrides else (min(widths), max(widths))
    height = ctx.draw_int("grid_h", *h_bounds)
    width = ctx.draw_int("grid_w", *w_bounds)
    marker_corner = ctx.draw_choice("marker_corner", CORNER_NAMES)
    blob_color = ctx.draw_choice("blob_color", tuple(range(1, 9)))
    shape_profile = ctx.draw_choice("shape_profile", SHAPE_NAMES)

    shape = SHAPE_PROFILES[shape_profile]
    shape_h = max(row for row, _ in shape) + 1
    shape_w = max(col for _, col in shape) + 1
    row_positions = height - shape_h - 1
    col_positions = width - shape_w - 1
    if row_positions < 1 or col_positions < 1:
        raise ValueError(
            f"shape_profile={shape_profile!r} does not fit inside "
            f"{height}x{width} while avoiding corners"
        )
    top = 1 + ((row_phase + block) % row_positions)
    left = 1 + ((col_phase + 3 * block) % col_positions)

    grid = full_grid(height, width, 0)
    marker_position = {
        "TL": (0, 0),
        "TR": (0, width - 1),
        "BL": (height - 1, 0),
        "BR": (height - 1, width - 1),
    }[marker_corner]
    grid[marker_position[0]][marker_position[1]] = 9
    for dr, dc in shape:
        grid[top + dr][left + dc] = blob_color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise ValueError(f"constructed invalid corner-marker scene: {errors}")
    return [row[:] for row in grid]
