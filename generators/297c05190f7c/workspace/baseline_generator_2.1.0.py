"""Generator for ``arc_puzzle_bank_seventh21:M45`` (297c05190f7c).

Rule: find every non-zero, same-color 4-connected component independently and
fill its tight bounding box with that component's color.  The output otherwise
contains background 0.

The public training pairs contain one component per color, so they alone admit
an unsafe shortcut: fill one bounding box per *color*.  The held-out canonical
query exposes the real unit of work by placing two color-6 components at a
diagonal touch.  All canonical pairs also leave object location and box extent
underspecified.  The curriculum therefore schedules diagonal same-color splits,
non-corner objects, and a 4x4 irregular box instead of teaching corner-local or
small-box-only variants of the rule.
"""
from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "297c05190f7c"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
# sha256(" ".join(canonical program_solution.split()))[:12]
RULE_HASH = "3cad5a2fcf1f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.60

SUMMARY = (
    "On a 0-background grid, treat each same-color 4-connected component as "
    "a separate object and fill that object's tight bounding box with its "
    "color. Scheduled lessons include two distinct-color irregular objects, "
    "a canonical-query-style pair of same-color components touching only "
    "diagonally, non-corner placements in every profile, and an expanded scene "
    "with a 4x4 irregular bounding box."
)

INVARIANTS = [
    "background is 0 and all cells are integer ARC colors 0..9",
    "ordinary scenes contain two to four same-color 4-connected components",
    "component bounding boxes do not overlap, so every filled cell has one label",
    "every ordinary scene has at least two non-rectangular components",
    "every profile contains a non-rectangular component outside the public-corner region",
    "the component_split profile has two same-color objects touching only diagonally",
    "the expanded profile contains a non-rectangular component with 4x4 bounding box",
]

SCENE_PROFILES = ("canonical_pair", "component_split", "expanded")
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-shaped 8..12",
        "valid": "8..12",
        "doc": "Exactly observable as len(grid).",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-shaped 9..13",
        "valid": "9..13",
        "doc": "Exactly observable as len(grid[0]).",
    },
    "scene_profile": {
        "type": "str",
        "default": "period-three teaching schedule",
        "valid": "|".join(SCENE_PROFILES),
        "doc": "Exactly observable from the 4-connected object count: 2, 3, or 4.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
SCHEDULE_PROFILES = SCENE_PROFILES

Grid = list[list[int]]
Cell = tuple[int, int]
Shape = frozenset[Cell]

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))

# Every shape is 4-connected and non-rectangular.  Their small footprints let
# the full override Cartesian product fit even at 8x9.
_IRREGULAR_SHAPES: tuple[Shape, ...] = (
    frozenset({(0, 0), (1, 0), (1, 1)}),
    frozenset({(0, 0), (0, 1), (0, 2), (1, 1)}),
    frozenset({(0, 0), (1, 0), (1, 1), (2, 1)}),
    frozenset({(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)}),
    frozenset({(0, 0), (0, 1), (1, 1), (1, 2)}),
)

# Four-by-four extents prevent a shortcut that only completes 2x2 and 3x3 boxes.
# Each template is 4-connected, non-rectangular, and spans a 4x4 bounding box
# under every D4 transform.
_LARGE_IRREGULAR_SHAPES: tuple[Shape, ...] = (
    frozenset(
        {
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (3, 1),
            (3, 2),
            (3, 3),
            (2, 3),
        }
    ),
    frozenset(
        {
            (0, 0),
            (0, 1),
            (0, 2),
            (1, 2),
            (2, 2),
            (2, 3),
            (3, 3),
        }
    ),
)

# A 3x3 motif: the L component occupies the upper-left 2x2 box and the
# singleton is diagonally adjacent at (2,2).  D4 transforms preserve the fact
# that the two same-color objects are 4-disconnected but 8-connected.
_SPLIT_MAIN = frozenset({(0, 0), (1, 0), (1, 1)})
_SPLIT_SINGLETON = frozenset({(2, 2)})

_CANONICAL_PROFILES = {
    "easy": (8, 9),
    "medium": (9, 10),
    "hard": (10, 10),
}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Expose the period-three curriculum for sliding-window audits."""
    del seed, difficulty
    return SCENE_PROFILES[int(sample_index) % len(SCENE_PROFILES)]


def _validate_override_keys(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _scheduled_choice(ctx, name: str, options: tuple[str, ...], default: str) -> str:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return str(ctx.draw_choice(name, options))
    return str(ctx.draw_choice(name, (default,)))


def _normalize_shape(cells: set[Cell] | frozenset[Cell]) -> Shape:
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _transform_shape(cells: Shape, turns: int, reflect: bool) -> Shape:
    transformed = set(cells)
    for _ in range(turns % 4):
        transformed = {(c, -r) for r, c in transformed}
    if reflect:
        transformed = {(r, -c) for r, c in transformed}
    return _normalize_shape(transformed)


def _shape_size(shape: Shape) -> tuple[int, int]:
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _corner_anchor(
    corner: str, shape: Shape, height: int, width: int, jitter: int
) -> Cell:
    shape_h, shape_w = _shape_size(shape)
    inset_r = min(jitter, max(0, height - shape_h))
    inset_c = min(jitter, max(0, width - shape_w))
    if corner == "tl":
        return inset_r, inset_c
    if corner == "tr":
        return inset_r, width - shape_w - inset_c
    if corner == "bl":
        return height - shape_h - inset_r, inset_c
    if corner == "br":
        return height - shape_h - inset_r, width - shape_w - inset_c
    raise ValueError(f"unknown corner {corner!r}")


def _translated(shape: Shape, top: int, left: int) -> set[Cell]:
    return {(top + r, left + c) for r, c in shape}


def _component_bbox(cells: set[Cell] | frozenset[Cell]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _boxes_overlap(
    first: tuple[int, int, int, int], second: tuple[int, int, int, int]
) -> bool:
    return not (
        first[2] < second[0]
        or second[2] < first[0]
        or first[3] < second[1]
        or second[3] < first[1]
    )


def _choose_anchor(
    rng,
    shape: Shape,
    height: int,
    width: int,
    reserved: list[tuple[int, int, int, int]],
    *,
    preferred: Callable[[tuple[int, int, int, int]], bool] | None = None,
) -> tuple[int, int, tuple[int, int, int, int]]:
    """Choose a deterministic valid placement, honoring a preferred region."""
    shape_h, shape_w = _shape_size(shape)
    candidates: list[tuple[int, int, tuple[int, int, int, int]]] = []
    preferred_candidates: list[tuple[int, int, tuple[int, int, int, int]]] = []
    for top in range(height - shape_h + 1):
        for left in range(width - shape_w + 1):
            bbox = (top, left, top + shape_h - 1, left + shape_w - 1)
            if any(_boxes_overlap(bbox, other) for other in reserved):
                continue
            candidate = (top, left, bbox)
            candidates.append(candidate)
            if preferred is not None and preferred(bbox):
                preferred_candidates.append(candidate)
    pool = preferred_candidates or candidates
    if not pool:
        raise RuntimeError("no non-overlapping anchor fits the requested shapes")
    return pool[rng.randrange(len(pool))]


def _components4(grid: Grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[Cell] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                for dr, dc in _CARDINAL:
                    nr, nc = current[0] + dr, current[1] + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            bbox = _component_bbox(cells)
            area = (bbox[2] - bbox[0] + 1) * (bbox[3] - bbox[1] + 1)
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": bbox,
                    "area": area,
                    "solid": len(cells) == area,
                }
            )
    return components


def _diagonally_touch(first: set[Cell], second: set[Cell]) -> bool:
    return any((r + dr, c + dc) in second for r, c in first for dr, dc in _DIAGONAL)


def _analyze(grid: Grid) -> dict[str, Any]:
    components = _components4(grid)
    same_color_pairs = []
    diagonal_same_color_pairs = []
    for index, first in enumerate(components):
        for second in components[index + 1 :]:
            if first["color"] != second["color"]:
                continue
            same_color_pairs.append((first, second))
            if _diagonally_touch(first["cells"], second["cells"]):
                diagonal_same_color_pairs.append((first, second))
    nonrect = [component for component in components if not component["solid"]]
    return {
        "height": len(grid),
        "width": len(grid[0]),
        "components": components,
        "component_count": len(components),
        "nonrect_components": nonrect,
        "solid_components": [component for component in components if component["solid"]],
        "foreground_colors": tuple(sorted({component["color"] for component in components})),
        "same_color_pairs": same_color_pairs,
        "diagonal_same_color_pairs": diagonal_same_color_pairs,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the structural lesson grammar while accepting all public inputs."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["every cell must be an integer ARC color 0..9"]
    if not (8 <= len(grid) <= 12 and 9 <= width <= 13):
        return [f"grid dimensions {len(grid)}x{width} are outside the task manifold"]
    if not any(value == 0 for row in grid for value in row):
        return ["background color 0 must be present"]

    analysis = _analyze([list(row) for row in grid])
    components = analysis["components"]
    errors: list[str] = []
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2..4 foreground components, found {len(components)}")
    if len(analysis["nonrect_components"]) < 1:
        errors.append("at least one component must be non-rectangular so the rule changes the grid")

    for index, first in enumerate(components):
        for second in components[index + 1 :]:
            if _boxes_overlap(first["bbox"], second["bbox"]):
                errors.append("component bounding boxes must not overlap")
                return errors
    return errors


def rule_mirror(grid: Grid) -> Grid:
    """Python test mirror; the selected Racket program remains authoritative."""
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components4(grid):
        r1, c1, r2, c2 = component["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                output[row][col] = component["color"]
    return output


def strict_canonical_like(grid) -> list[str]:
    """Linked public manifold, including the query's same-color split cue."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze([list(row) for row in grid])
    profile = (
        analysis["height"],
        analysis["width"],
        len(analysis["foreground_colors"]) + 1,
    )
    if profile not in {(8, 9, 3), (9, 10, 3), (10, 10, 3)}:
        return [f"mechanical profile {profile!r} is outside the public manifold"]
    if analysis["component_count"] not in (2, 3):
        return ["public scenes have two or three 4-connected components"]
    if analysis["component_count"] == 3 and not analysis["diagonal_same_color_pairs"]:
        return ["the three-object public query uses a diagonal same-color component split"]
    return []


def observe_overrides(grid: Grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    profile_by_count = {2: "canonical_pair", 3: "component_split", 4: "expanded"}
    profile = profile_by_count.get(analysis["component_count"])
    if profile is None:
        raise ValueError(
            f"cannot infer scene_profile from {analysis['component_count']} components"
        )
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "scene_profile": profile,
    }


def _choose_irregular(rng, index: int) -> Shape:
    base = _IRREGULAR_SHAPES[(rng.randrange(len(_IRREGULAR_SHAPES)) + index) % len(_IRREGULAR_SHAPES)]
    return _transform_shape(base, rng.randrange(4), bool(rng.randrange(2)))


def _paint_object(grid: Grid, cells: set[Cell], color: int) -> None:
    for row, col in cells:
        if grid[row][col] != 0:
            raise RuntimeError("object placement overlap")
        grid[row][col] = color


def _build_canonical_pair(height: int, width: int, layout_rng, palette_rng) -> Grid:
    grid = full_grid(height, width, 0)
    colors = palette_rng.sample(range(1, 10), 2)
    reserved: list[tuple[int, int, int, int]] = []
    for index, color in enumerate(colors):
        shape = _choose_irregular(layout_rng, index)
        preferred = None
        if index == 0:
            preferred = lambda bbox: not _bbox_near_public_corner(
                bbox, height, width
            )
        top, left, bbox = _choose_anchor(
            layout_rng,
            shape,
            height,
            width,
            reserved,
            preferred=preferred,
        )
        _paint_object(grid, _translated(shape, top, left), color)
        reserved.append(bbox)
    return grid


def _build_component_split(height: int, width: int, layout_rng, palette_rng) -> Grid:
    grid = full_grid(height, width, 0)
    motif_turns = layout_rng.randrange(4)
    motif_reflect = bool(layout_rng.randrange(2))
    # Transform each object in the same 3x3 coordinate frame.  Normalizing them
    # separately would destroy the diagonal relationship, so transform the
    # tagged union and split the tags afterwards.
    tagged = {(r, c, 0) for r, c in _SPLIT_MAIN} | {
        (r, c, 1) for r, c in _SPLIT_SINGLETON
    }
    transformed = tagged
    for _ in range(motif_turns % 4):
        transformed = {(c, -r, tag) for r, c, tag in transformed}
    if motif_reflect:
        transformed = {(r, -c, tag) for r, c, tag in transformed}
    min_r = min(r for r, _, _ in transformed)
    min_c = min(c for _, c, _ in transformed)
    motif_main = frozenset((r - min_r, c - min_c) for r, c, tag in transformed if tag == 0)
    motif_singleton = frozenset((r - min_r, c - min_c) for r, c, tag in transformed if tag == 1)
    motif_all = motif_main | motif_singleton

    top, left, motif_bbox = _choose_anchor(
        layout_rng,
        motif_all,
        height,
        width,
        [],
        preferred=lambda bbox: not _bbox_near_public_corner(
            bbox, height, width
        ),
    )
    first_color, other_color = palette_rng.sample(range(1, 10), 2)
    _paint_object(grid, _translated(motif_main, top, left), first_color)
    _paint_object(grid, _translated(motif_singleton, top, left), first_color)

    other_shape = _choose_irregular(layout_rng, 2)
    other_top, other_left, _ = _choose_anchor(
        layout_rng, other_shape, height, width, [motif_bbox]
    )
    _paint_object(grid, _translated(other_shape, other_top, other_left), other_color)
    return grid


def _build_expanded(height: int, width: int, layout_rng, palette_rng) -> Grid:
    grid = full_grid(height, width, 0)
    colors = palette_rng.sample(range(1, 10), 3)
    corners = ("tl", "tr", "bl", "br")

    # One large corner object and one genuinely interior small object refute two
    # spatially plausible shortcuts left open by the public pairs: only process
    # corner objects, or only complete boxes whose extent is at most three.
    large_corner = corners[layout_rng.randrange(len(corners))]
    large_base = _LARGE_IRREGULAR_SHAPES[
        layout_rng.randrange(len(_LARGE_IRREGULAR_SHAPES))
    ]
    large_shape = _transform_shape(
        large_base, layout_rng.randrange(4), bool(layout_rng.randrange(2))
    )
    large_top, large_left = _corner_anchor(
        large_corner, large_shape, height, width, 0
    )
    large_cells = _translated(large_shape, large_top, large_left)
    large_bbox = _component_bbox(large_cells)
    _paint_object(grid, large_cells, colors[0])

    center_shape = _transform_shape(
        _IRREGULAR_SHAPES[0],
        layout_rng.randrange(4),
        bool(layout_rng.randrange(2)),
    )
    center_h, center_w = _shape_size(center_shape)
    center_candidates: list[tuple[int, int]] = []
    for top in range(height - center_h + 1):
        for left in range(width - center_w + 1):
            cells = _translated(center_shape, top, left)
            bbox = _component_bbox(cells)
            r1, c1, r2, c2 = bbox
            if min(r1, height - 1 - r2, c1, width - 1 - c2) < 3:
                continue
            if _boxes_overlap(bbox, large_bbox):
                continue
            center_candidates.append((top, left))
    if not center_candidates:
        raise RuntimeError("expanded profile cannot place its interior object")
    center_top, center_left = center_candidates[
        layout_rng.randrange(len(center_candidates))
    ]
    _paint_object(
        grid, _translated(center_shape, center_top, center_left), colors[1]
    )

    # Two far-apart corner Ls share a color. They remain separate components and
    # preserve the per-color-bounding-box discriminator in this profile.
    remaining_corners = [corner for corner in corners if corner != large_corner]
    chosen_corners = layout_rng.sample(remaining_corners, 2)
    base = _IRREGULAR_SHAPES[0]
    for corner in chosen_corners:
        shape = _transform_shape(
            base, layout_rng.randrange(4), bool(layout_rng.randrange(2))
        )
        top, left = _corner_anchor(corner, shape, height, width, 0)
        _paint_object(grid, _translated(shape, top, left), colors[2])
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_keys(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    scene_profile = _scheduled_choice(
        ctx, "scene_profile", SCENE_PROFILES, scheduled
    )

    canonical_h, canonical_w = _CANONICAL_PROFILES.get(
        str(difficulty), _CANONICAL_PROFILES["medium"]
    )
    if scene_profile == "expanded":
        defaults = {
            "easy": (9, 11),
            "medium": (11, 12),
            "hard": (12, 13),
        }
        default_h, default_w = defaults.get(str(difficulty), (10, 11))
    else:
        default_h, default_w = canonical_h, canonical_w

    height = _scheduled_int(ctx, "grid_h", 8, 12, default_h)
    width = _scheduled_int(ctx, "grid_w", 9, 13, default_w)
    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")

    if scene_profile == "canonical_pair":
        grid = _build_canonical_pair(height, width, layout_rng, palette_rng)
    elif scene_profile == "component_split":
        grid = _build_component_split(height, width, layout_rng, palette_rng)
    elif scene_profile == "expanded":
        grid = _build_expanded(height, width, layout_rng, palette_rng)
    else:  # draw_choice already validates, kept as a defensive invariant.
        raise ValueError(f"unknown scene_profile {scene_profile!r}")

    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"internal generator invariant failed: {errors}")
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "scene_profile": scene_profile,
    }
    if observed != expected:
        raise RuntimeError(f"generated axes are not observable: {observed!r} != {expected!r}")
    return grid


# ---------------------------------------------------------------------------
# Task-linked adversaries and lesson-identifiability contract


def _rival_identity(grid: Grid) -> Grid:
    return deepcopy(grid)


def _rival_per_color_bbox(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = {
            (row, col)
            for row in range(len(grid))
            for col in range(len(grid[0]))
            if grid[row][col] == color
        }
        r1, c1, r2, c2 = _component_bbox(cells)
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                output[row][col] = color
    return output


def _components8(grid: Grid) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    deltas = _CARDINAL + _DIAGONAL
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: set[Cell] = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                for dr, dc in deltas:
                    nr, nc = current[0] + dr, current[1] + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append({"color": color, "cells": cells, "bbox": _component_bbox(cells)})
    return components


def _rival_eight_connected_bbox(grid: Grid) -> Grid:
    output = full_grid(len(grid), len(grid[0]), 0)
    for component in _components8(grid):
        r1, c1, r2, c2 = component["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                output[row][col] = component["color"]
    return output


def _rival_largest_only(grid: Grid) -> Grid:
    output = deepcopy(grid)
    components = _components4(grid)
    largest = max(components, key=lambda component: len(component["cells"]))
    r1, c1, r2, c2 = largest["bbox"]
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            output[row][col] = largest["color"]
    return output


def _bbox_near_public_corner(
    bbox: tuple[int, int, int, int], height: int, width: int, margin: int = 2
) -> bool:
    r1, c1, r2, c2 = bbox
    return (
        min(r1, height - 1 - r2) <= margin
        and min(c1, width - 1 - c2) <= margin
    )


def _rival_corner_components_only(grid: Grid) -> Grid:
    """Fit the public pairs by completing only objects near an outer corner."""
    output = deepcopy(grid)
    height, width = len(grid), len(grid[0])
    for component in _components4(grid):
        if not _bbox_near_public_corner(component["bbox"], height, width):
            continue
        r1, c1, r2, c2 = component["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                output[row][col] = component["color"]
    return output


def _rival_bbox_extent_at_most_three(grid: Grid) -> Grid:
    """Fit the public pairs by refusing to expand any component beyond 3x3."""
    output = deepcopy(grid)
    for component in _components4(grid):
        r1, c1, r2, c2 = component["bbox"]
        if max(r2 - r1 + 1, c2 - c1 + 1) > 3:
            continue
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                output[row][col] = component["color"]
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "identity": _rival_identity,
    "one_bbox_per_color": _rival_per_color_bbox,
    "eight_connected_objects": _rival_eight_connected_bbox,
    "largest_object_only": _rival_largest_only,
    "corner_components_only": _rival_corner_components_only,
    "bbox_extent_at_most_three": _rival_bbox_extent_at_most_three,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    "one_bbox_per_color": _rival_per_color_bbox,
    "eight_connected_objects": _rival_eight_connected_bbox,
    "corner_components_only": _rival_corner_components_only,
    "bbox_extent_at_most_three": _rival_bbox_extent_at_most_three,
}


def _witness_visible_bbox_fill(grid: Grid) -> bool:
    return rule_mirror(grid) != grid


def _witness_same_color_diagonal_split(grid: Grid) -> bool:
    return bool(_analyze(grid)["diagonal_same_color_pairs"])


def _witness_multiple_nonrect_components(grid: Grid) -> bool:
    return len(_analyze(grid)["nonrect_components"]) >= 2


def _witness_noncorner_nonrect_component(grid: Grid) -> bool:
    analysis = _analyze(grid)
    return any(
        not component["solid"]
        and not _bbox_near_public_corner(
            component["bbox"], analysis["height"], analysis["width"]
        )
        for component in analysis["components"]
    )


def _witness_bbox_extent_over_three(grid: Grid) -> bool:
    return any(
        not component["solid"]
        and max(
            component["bbox"][2] - component["bbox"][0] + 1,
            component["bbox"][3] - component["bbox"][1] + 1,
        )
        > 3
        for component in _analyze(grid)["components"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "visible_bbox_fill": _witness_visible_bbox_fill,
    "same_color_diagonal_split": _witness_same_color_diagonal_split,
    "all_components_are_processed": _witness_multiple_nonrect_components,
    "noncorner_nonrect_component": _witness_noncorner_nonrect_component,
    "bbox_extent_over_three": _witness_bbox_extent_over_three,
}
WITNESS_RIVALS = {
    "visible_bbox_fill": ["identity"],
    "same_color_diagonal_split": ["one_bbox_per_color", "eight_connected_objects"],
    "all_components_are_processed": ["largest_object_only"],
    "noncorner_nonrect_component": ["corner_components_only"],
    "bbox_extent_over_three": ["bbox_extent_at_most_three"],
}


def _validate_lesson_pair(pair: Any, label: str) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
        return [f"{label} must contain input and output grids"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output is not exact per-component bounding-box fill"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Require each three-demo window to refute the named shortcut programs."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        reasons.extend(_validate_lesson_pair(demo, f"demo {index}"))
    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
        return reasons
    reasons.extend(
        f"query input: {error}" for error in self_check(query["input"])
    )
    if reasons:
        return reasons

    if not any(_witness_same_color_diagonal_split(demo["input"]) for demo in demos):
        reasons.append("demos lack a same-color diagonal 4-component discriminator")
    if not any(_witness_visible_bbox_fill(demo["input"]) for demo in demos):
        reasons.append("demos do not visibly add any bounding-box cells")
    if not any(_witness_multiple_nonrect_components(demo["input"]) for demo in demos):
        reasons.append("demos do not prove that every component is processed")

    expected_query = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != expected_query:
                reasons.append(
                    f"named competitor {name!r} fits every demo but disagrees on the query"
                )
    return reasons
