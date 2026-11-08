"""Generator for ARC task ``492fe98aff2b``: crop to nonzero content.

The authoritative rule finds the minimum and maximum row/column containing any
nonzero cell, then returns that rectangular subgrid unchanged.  Ordinary draws
use sparse, disconnected, multicolour content so identity, largest-component,
solid-fill, and monochrome shortcuts all disagree with the true crop.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "492fe98aff2b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "debb1a8a129a"

SUMMARY = (
    "Crop the input to the tight bounding rectangle containing every nonzero "
    "cell. Preserve all colours, component spacing, and interior background "
    "cells exactly. Ordinary scenes place two to four disconnected, "
    "multicolour components inside a visible zero margin, so the output is a "
    "strictly smaller sparse rectangle and cannot be explained by identity, "
    "largest-object-only, solid-bbox, or monochrome-crop shortcuts."
)

INVARIANTS = [
    "background is colour 0 and occurs outside the active bounding box",
    "two to four disconnected nonzero components jointly determine the crop",
    "at least two nonzero colours occur and are preserved exactly",
    "the tight nonzero bounding box has a visible margin on every grid side",
    "the cropped rectangle contains interior zero cells that remain zero",
    "the canonical Racket program is the sole output authority",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled 7..14", "valid": "7..14"},
    "grid_w": {"type": "int", "default": "scheduled 9..16", "valid": "9..16"},
    "bbox_h": {"type": "int", "default": "scheduled 3..5", "valid": "3..5"},
    "bbox_w": {"type": "int", "default": "scheduled 4..7", "valid": "4..7"},
    "palette_size": {"type": "int", "default": "scheduled 3..5", "valid": "3..5"},
    "component_count": {"type": "int", "default": "scheduled 2..4", "valid": "2..4"},
}

# The global ranges were chosen so every Cartesian override combination fits
# with a one-cell margin and can realize all requested colours/components.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_PROFILE_NAMES = (
    "canonical_8x10",
    "two_component_generalization",
    "canonical_9x9",
    "three_component_generalization",
    "canonical_10x12",
    "four_component_generalization",
    "canonical_7x11",
    "palette_extent_generalization",
)
SCHEDULE_PROFILES = _PROFILE_NAMES
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.40

Grid = list[list[int]]
Cell = tuple[int, int]


def schedule_profile(seed, sample_index, difficulty=None):
    """Eight consecutive draws alternate canonical anchors and extensions."""
    del seed, difficulty
    return _PROFILE_NAMES[int(sample_index) % len(_PROFILE_NAMES)]


def _validate_grid(grid: Any) -> tuple[int, int, list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return 0, 0, ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return len(grid), 0, ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return len(grid), width, ["grid must be rectangular"]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return len(grid), width, [
                    f"cell ({r},{c}) is not a literal ARC colour 0..9: {value!r}"
                ]
    return len(grid), width, []


def _nonzero_cells(grid: Grid) -> set[Cell]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    }


def _bbox(cells: set[Cell]) -> tuple[int, int, int, int] | None:
    if not cells:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(grid: Grid) -> list[set[Cell]]:
    remaining = _nonzero_cells(grid)
    result: list[set[Cell]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    queue.append(nxt)
        result.append(component)
    return result


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror used only by tests and semantic hooks."""
    cells = _nonzero_cells(grid)
    bounds = _bbox(cells)
    if bounds is None:
        return [[0]]
    r1, c1, r2, c2 = bounds
    return [list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed and rule-hiding lesson inputs; accept all canonicals."""
    del difficulty, meta
    height, width, issues = _validate_grid(grid)
    if issues:
        return issues
    if not (5 <= height <= 20):
        issues.append(f"height {height} outside supported lesson range 5..20")
    if not (5 <= width <= 24):
        issues.append(f"width {width} outside supported lesson range 5..24")

    cells = _nonzero_cells(grid)
    if not cells:
        issues.append("at least one nonzero crop cell is required")
        return issues
    bounds = _bbox(cells)
    assert bounds is not None
    r1, c1, r2, c2 = bounds
    if r1 == 0 or c1 == 0 or r2 == height - 1 or c2 == width - 1:
        issues.append("the tight crop must leave a visible zero margin on every side")

    components = _components(grid)
    if not (2 <= len(components) <= 4):
        issues.append(f"expected 2..4 disconnected nonzero components, found {len(components)}")

    nonzero_colours = {grid[r][c] for r, c in cells}
    if len(nonzero_colours) < 2:
        issues.append("at least two nonzero colours are required to refute colour shortcuts")

    crop = rule_mirror(grid)
    crop_area = len(crop) * len(crop[0])
    if crop_area == len(cells):
        issues.append("the crop must preserve at least one interior background cell")

    perimeter = {
        (r1, c) for c in range(c1, c2 + 1)
    } | {
        (r2, c) for c in range(c1, c2 + 1)
    } | {
        (r, c1) for r in range(r1, r2 + 1)
    } | {
        (r, c2) for r in range(r1, r2 + 1)
    }
    if perimeter <= cells:
        issues.append("a fully painted bbox frame hides the general crop rule")
    return issues


_CANONICAL_PROFILES = {(8, 10, 3), (9, 9, 3), (10, 12, 3), (7, 11, 3)}


def strict_canonical_like(grid) -> list[str]:
    """Empirical canonical manifold shared by all four canonical inputs."""
    reasons = list(self_check(grid))
    if reasons:
        return reasons
    profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
    if profile not in _CANONICAL_PROFILES:
        reasons.append(f"profile {profile} is outside canonical h/w/palette profiles")
    if len(_components(grid)) != 2:
        reasons.append("canonical inputs contain exactly two disconnected components")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    cells = _nonzero_cells(grid)
    bounds = _bbox(cells)
    if bounds is None:
        bbox_h = bbox_w = 0
    else:
        r1, c1, r2, c2 = bounds
        bbox_h, bbox_w = r2 - r1 + 1, c2 - c1 + 1
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "palette_size": len({value for row in grid for value in row}),
        "component_count": len(_components(grid)),
    }


def _identity(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _largest_component_crop(grid: Grid) -> Grid:
    components = _components(grid)
    if not components:
        return [[0]]
    component = min(components, key=lambda cells: (-len(cells), min(cells)))
    r1, c1, r2, c2 = _bbox(component)  # type: ignore[misc]
    return [list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]]


def _solid_bbox_fill(grid: Grid) -> Grid:
    crop = rule_mirror(grid)
    nonzero = [value for row in crop for value in row if value != 0]
    fill = min(nonzero) if nonzero else 0
    return [[fill if value == 0 else value for value in row] for row in crop]


def _monochrome_crop(grid: Grid) -> Grid:
    crop = rule_mirror(grid)
    nonzero = [value for row in crop for value in row if value != 0]
    colour = min(nonzero) if nonzero else 0
    return [[colour if value != 0 else 0 for value in row] for row in crop]


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity": _identity,
    "largest_component_only": _largest_component_crop,
    "solid_bbox_fill": _solid_bbox_fill,
    "monochrome_crop": _monochrome_crop,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _valid_and(predicate: Callable[[Grid], bool], grid: Grid) -> bool:
    return not self_check(grid) and predicate(grid)


def _witness_visible_crop(grid: Grid) -> bool:
    return _valid_and(lambda g: rule_mirror(g) != g, grid)


def _witness_all_components(grid: Grid) -> bool:
    return _valid_and(lambda g: _largest_component_crop(g) != rule_mirror(g), grid)


def _witness_sparse_bbox(grid: Grid) -> bool:
    return _valid_and(lambda g: _solid_bbox_fill(g) != rule_mirror(g), grid)


def _witness_colour_preservation(grid: Grid) -> bool:
    return _valid_and(lambda g: _monochrome_crop(g) != rule_mirror(g), grid)


SEMANTIC_WITNESSES = {
    "visible_margin_refutes_identity": _witness_visible_crop,
    "all_components_determine_bbox": _witness_all_components,
    "interior_background_is_preserved": _witness_sparse_bbox,
    "all_nonzero_colours_are_preserved": _witness_colour_preservation,
}
WITNESS_RIVALS = {
    "visible_margin_refutes_identity": ["identity"],
    "all_components_determine_bbox": ["largest_component_only"],
    "interior_background_is_preserved": ["solid_bbox_fill"],
    "all_nonzero_colours_are_preserved": ["monochrome_crop"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require exact demos that collectively falsify every named shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    reasons: list[str] = []
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        query_issues = self_check(query["input"])
        if query_issues:
            reasons.append(f"query input is invalid: {query_issues[0]}")

    refuted = {name: False for name in SEMANTIC_RIVALS}
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = self_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is invalid: {errors[0]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the exact nonzero bbox crop")
        for name, rival in SEMANTIC_RIVALS.items():
            refuted[name] = refuted[name] or rival(demo["input"]) != expected
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demonstrations do not refute rival {name}")
    return reasons


def _profile_defaults(sample_index: int, difficulty) -> tuple[int, int, int, int, int, int]:
    profile = schedule_profile(0, sample_index, difficulty)
    canonical = {
        "canonical_8x10": (8, 10, 3, 5, 3, 2),
        "canonical_9x9": (9, 9, 5, 5, 3, 2),
        "canonical_10x12": (10, 12, 4, 4, 3, 2),
        "canonical_7x11": (7, 11, 4, 6, 3, 2),
    }
    if profile in canonical:
        return canonical[profile]

    band = {
        "easy": (8, 10, 3, 4, 3),
        "medium": (11, 13, 4, 6, 4),
        "hard": (14, 16, 5, 7, 5),
    }.get(difficulty, (10, 12, 4, 5, 4))
    height, width, bbox_h, bbox_w, palette_size = band
    component_count = {
        "two_component_generalization": 2,
        "three_component_generalization": 3,
        "four_component_generalization": 4,
        "palette_extent_generalization": 2 + (int(sample_index) % 3),
    }[profile]
    return height, width, bbox_h, bbox_w, palette_size, component_count


def _scheduled_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _local_components(bbox_h: int, bbox_w: int, count: int, variant: int) -> list[set[Cell]]:
    last_r, last_c = bbox_h - 1, bbox_w - 1
    if count == 2:
        # Two separated four-cell bars cover the canonical object-size scale.
        # Their row gap keeps them disconnected even at the minimum 3x4 bbox.
        span = min(4, bbox_w)
        return [
            {(0, c) for c in range(span)},
            {(last_r, last_c - c) for c in range(span)},
        ]
    if count == 3:
        return [
            {(0, 0), (1, 0)},
            {(0, last_c), (1, last_c)},
            {(last_r, max(1, last_c // 2)), (last_r, min(last_c - 1, last_c // 2 + 1))},
        ]

    components = [
        {(0, 0)},
        {(0, last_c)},
        {(last_r, 0)},
        {(last_r, last_c)},
    ]
    if bbox_w >= 5 and variant % 2 == 0:
        components[0].add((0, 1))
        components[1].add((0, last_c - 1))
        components[2].add((last_r, 1))
        components[3].add((last_r, last_c - 1))
    elif bbox_h >= 5:
        components[0].add((1, 0))
        components[1].add((1, last_c))
        components[2].add((last_r - 1, 0))
        components[3].add((last_r - 1, last_c))
    return components


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _profile_defaults(sample_index, difficulty)
    height = _scheduled_int(ctx, overrides, "grid_h", defaults[0], 7, 14)
    width = _scheduled_int(ctx, overrides, "grid_w", defaults[1], 9, 16)
    bbox_h = _scheduled_int(ctx, overrides, "bbox_h", defaults[2], 3, 5)
    bbox_w = _scheduled_int(ctx, overrides, "bbox_w", defaults[3], 4, 7)
    palette_size = _scheduled_int(ctx, overrides, "palette_size", defaults[4], 3, 5)
    component_count = _scheduled_int(ctx, overrides, "component_count", defaults[5], 2, 4)

    layout_rng = ctx.draw_rng("layout")
    row0 = layout_rng.randint(1, height - bbox_h - 1)
    col0 = layout_rng.randint(1, width - bbox_w - 1)
    components = _local_components(bbox_h, bbox_w, component_count, sample_index)
    palette = ctx.draw_distinct_colors(
        "nonzero_palette", n=palette_size - 1, exclude={0}
    )

    ordered_cells = [
        cell
        for component in components
        for cell in sorted(component)
    ]
    colour_stream = list(palette)
    while len(colour_stream) < len(ordered_cells):
        colour_stream.append(palette[layout_rng.randrange(len(palette))])
    layout_rng.shuffle(colour_stream)

    grid = full_grid(height, width, 0)
    for (r, c), colour in zip(ordered_cells, colour_stream):
        grid[row0 + r][col0 + c] = colour

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal construction violated self_check: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "bbox_h": bbox_h,
        "bbox_w": bbox_w,
        "palette_size": palette_size,
        "component_count": component_count,
    }
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")
    return grid
