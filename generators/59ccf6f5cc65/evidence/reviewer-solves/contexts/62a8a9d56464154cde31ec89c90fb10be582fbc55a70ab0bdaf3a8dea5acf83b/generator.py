"""Canonical-profile sampler for recoloring orange components at exact corners.

The unchanged Racket authority recolors a color-7 component iff one of its cells
is an exact grid corner.  Every ordinary draw includes a color-5 corner marker,
a true corner component, a strictly interior component, and an L-shaped orange
component whose bounding box reaches a corner while the corner cell itself is
absent.  That last witness rules out the strongest canonical-demonstration
shortcut: testing a component's bounding box or its two touched borders instead
of exact cell membership.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "59ccf6f5cc65"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "bf30289ab720"
SUMMARY = (
    "Use exact 4-connected orange(7) component membership: recolor an orange "
    "component blue(1) iff it contains one of the four grid-corner cells. "
    "A color-5 corner marker and near-corner orange decoys remain unchanged."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

CANONICAL_PROFILES = ((8, 9), (9, 10), (8, 10), (9, 11))
SCHEDULE_PROFILES = (0, 1, 2, 3)

INVARIANTS = [
    "input profile is one of the four canonical height/width profiles",
    "the exact input palette is background 0, marker 5, and orange 7",
    "exactly one color-5 singleton occupies a grid corner",
    "at least one orange component contains an exact corner",
    "at least one orange component contains no exact corner",
    "ordinary draws include a two-edge corner-gap decoy and an interior object",
]

AXES = {
    "profile": {
        "type": "int",
        "default": "four-slot canonical profile schedule",
        "valid": "0..3",
    },
    "n_corner": {
        "type": "int",
        "default": "scheduled 1|1|2|2",
        "valid": "1..2",
    },
    "n_interior": {
        "type": "int",
        "default": "scheduled 2|1|2|1",
        "valid": "1..2",
    },
    "layout_rotation": {
        "type": "int",
        "default": "scheduled 0..3 with a difficulty rotation",
        "valid": "0..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_CORNER_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),              # non-rectangular L
    ((0, 0), (1, 0), (2, 0)),              # vertical line
    ((0, 0), (0, 1), (0, 2)),              # horizontal line
    ((0, 0), (0, 1), (1, 0), (1, 1)),      # 2x2 block
)
_INTERIOR_SHAPES = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
)


def _difficulty_offset(difficulty: str | None) -> int:
    try:
        return {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    except KeyError as exc:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'") from exc


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the canonical profile slot; seed and difficulty do not change coverage."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override key(s): " + ", ".join(unknown))
    bounds = {
        "profile": (0, 3),
        "n_corner": (1, 2),
        "n_interior": (1, 2),
        "layout_rotation": (0, 3),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def _draw_axis(ctx, overrides, name: str, scheduled: int, lo: int, hi: int) -> int:
    if name in overrides and overrides[name] is not None:
        return int(ctx.draw_int(name, lo, hi))
    return int(ctx.draw_choice(name, (scheduled,)))


def _corner_frame(height: int, width: int, index: int):
    """Return ``(corner_row, corner_col, inward_row_step, inward_col_step)``."""
    return (
        (0, 0, 1, 1),
        (0, width - 1, 1, -1),
        (height - 1, width - 1, -1, -1),
        (height - 1, 0, -1, 1),
    )[index]


def _at_corner(height: int, width: int, index: int, local_cells):
    row, col, dr, dc = _corner_frame(height, width, index)
    return {(row + u * dr, col + v * dc) for u, v in local_cells}


def _paint(grid, cells, color: int) -> None:
    for row, col in cells:
        if grid[row][col] != 0:
            raise RuntimeError(f"constructive placement overlap at {(row, col)}")
    for row, col in cells:
        grid[row][col] = color


def _can_place_component(grid, cells) -> bool:
    height, width = len(grid), len(grid[0])
    cells = set(cells)
    for row, col in cells:
        if not (1 <= row < height - 1 and 1 <= col < width - 1):
            return False
        if grid[row][col] != 0:
            return False
        for dr, dc in _CARDINAL:
            neighbor = row + dr, col + dc
            if neighbor not in cells and grid[neighbor[0]][neighbor[1]] == 7:
                return False
    return True


def _interior_options(grid, shape_order):
    height, width = len(grid), len(grid[0])
    options = []
    for shape_index in shape_order:
        shape = _INTERIOR_SHAPES[shape_index]
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(col for _, col in shape) + 1
        for top in range(1, height - shape_h):
            for left in range(1, width - shape_w):
                cells = {(top + row, left + col) for row, col in shape}
                if _can_place_component(grid, cells):
                    options.append(cells)
    return options


def _place_interiors(grid, count: int, rng, shape_offset: int) -> None:
    """Backtrack over bounded candidate placements so requested counts are exact."""
    shape_order = list(range(len(_INTERIOR_SHAPES)))
    shape_order = shape_order[shape_offset:] + shape_order[:shape_offset]

    def search(remaining: int) -> bool:
        if remaining == 0:
            return True
        options = _interior_options(grid, shape_order)
        rng.shuffle(options)
        for cells in options:
            for row, col in cells:
                grid[row][col] = 7
            if search(remaining - 1):
                return True
            for row, col in cells:
                grid[row][col] = 0
        return False

    if not search(count):
        raise RuntimeError(f"could not constructively place {count} interior components")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _difficulty_offset(difficulty)  # validate before constructing the context
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    slot = schedule_profile(seed, sample_index, difficulty)
    profile = _draw_axis(ctx, overrides, "profile", slot, 0, 3)
    n_corner = _draw_axis(ctx, overrides, "n_corner", (1, 1, 2, 2)[slot], 1, 2)
    n_interior = _draw_axis(ctx, overrides, "n_interior", (2, 1, 2, 1)[slot], 1, 2)
    rotation = _draw_axis(
        ctx,
        overrides,
        "layout_rotation",
        (slot + _difficulty_offset(difficulty)) % 4,
        0,
        3,
    )

    height, width = CANONICAL_PROFILES[profile]
    grid = full_grid(height, width, 0)

    marker_corner = rotation
    gap_corner = (rotation + 1) % 4
    true_corners = ((rotation + 2) % 4, (rotation + 3) % 4)

    marker_cell = _at_corner(height, width, marker_corner, ((0, 0),))
    _paint(grid, marker_cell, 5)

    # Connected L around a missing corner: touches both adjoining borders and
    # has a corner-containing bounding box, but no orange cell is at the corner.
    gap_cells = _at_corner(
        height,
        width,
        gap_corner,
        ((0, 1), (1, 1), (1, 0)),
    )
    _paint(grid, gap_cells, 7)

    for ordinal, corner_index in enumerate(true_corners[:n_corner]):
        # The first true corner is always non-rectangular; the second varies.
        shape_index = 0 if ordinal == 0 else (slot + _difficulty_offset(difficulty)) % len(_CORNER_SHAPES)
        cells = _at_corner(height, width, corner_index, _CORNER_SHAPES[shape_index])
        _paint(grid, cells, 7)

    _place_interiors(
        grid,
        n_interior,
        ctx.draw_rng("interior_placement"),
        (slot + _difficulty_offset(difficulty)) % len(_INTERIOR_SHAPES),
    )
    return grid


def _orange_components(grid):
    """Return color-7 components as sets of ``(row, col)`` cells."""
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 7
    }
    components = []
    while unseen:
        start = unseen.pop()
        cells = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                neighbor = row + dr, col + dc
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        components.append(cells)
    return components


def _component_facts(grid):
    height, width = len(grid), len(grid[0])
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    facts = []
    for cells in _orange_components(grid):
        edges = set()
        for row, col in cells:
            if row == 0:
                edges.add("top")
            if row == height - 1:
                edges.add("bottom")
            if col == 0:
                edges.add("left")
            if col == width - 1:
                edges.add("right")
        facts.append(
            {
                "cells": cells,
                "corner": bool(cells & corners),
                "edges": edges,
                "bbox": (
                    min(row for row, _ in cells),
                    min(col for _, col in cells),
                    max(row for row, _ in cells),
                    max(col for _, col in cells),
                ),
            }
        )
    return facts


def rule_mirror(grid):
    """Pure Python mirror of the pinned Racket authority for tests/contracts."""
    if not grid:
        return []
    out = [list(row) for row in grid]
    for component in _component_facts(grid):
        if component["corner"]:
            for row, col in component["cells"]:
                out[row][col] = 1
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the public input grammar without consulting private outputs."""
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be nonempty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    errors = []
    height = len(grid)
    if (height, width) not in CANONICAL_PROFILES:
        errors.append(
            f"grid profile must be one of {CANONICAL_PROFILES}, got {(height, width)}"
        )
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return errors
    palette = {value for row in grid for value in row}
    if palette != {0, 5, 7}:
        errors.append(f"expected exact input palette [0, 5, 7], got {sorted(palette)}")
    marker_cells = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    ]
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    if len(marker_cells) != 1 or marker_cells[0] not in corners:
        errors.append("expected exactly one color-5 marker at a grid corner")
    components = _component_facts(grid)
    if not any(component["corner"] for component in components):
        errors.append("expected at least one orange component containing an exact corner")
    if not any(not component["corner"] for component in components):
        errors.append("expected at least one orange component containing no exact corner")
    return errors


def strict_canonical_like(grid):
    """Accept exactly the canonical size/palette/input-domain envelope."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every exact public axis from the generated grid."""
    height, width = len(grid), len(grid[0])
    try:
        profile = CANONICAL_PROFILES.index((height, width))
    except ValueError as exc:
        raise ValueError("grid does not use a declared canonical profile") from exc
    marker = next(
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 5
    )
    corner_positions = (
        (0, 0),
        (0, width - 1),
        (height - 1, width - 1),
        (height - 1, 0),
    )
    layout_rotation = corner_positions.index(marker)
    components = _component_facts(grid)
    return {
        "profile": profile,
        "n_corner": sum(component["corner"] for component in components),
        "n_interior": sum(not component["edges"] for component in components),
        "layout_rotation": layout_rotation,
    }


def _bbox_contains_grid_corner(fact, height: int, width: int) -> bool:
    top, left, bottom, right = fact["bbox"]
    return any(
        top <= row <= bottom and left <= col <= right
        for row, col in (
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
        )
    )


def _apply_orange_rival(grid, predicate):
    """Apply a rival component selector without mutating ``grid``."""
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for fact in _component_facts(grid):
        if predicate(fact, height, width):
            for row, col in fact["cells"]:
                out[row][col] = 1
    return out


def _identity(grid):
    return [list(row) for row in grid]


def _recolor_all_orange(grid):
    return _apply_orange_rival(grid, lambda _fact, _height, _width: True)


def _touches_any_border(grid):
    return _apply_orange_rival(
        grid,
        lambda fact, _height, _width: bool(fact["edges"]),
    )


def _touches_two_borders(grid):
    return _apply_orange_rival(
        grid,
        lambda fact, _height, _width: len(fact["edges"]) >= 2,
    )


def _bbox_contains_corner(grid):
    return _apply_orange_rival(
        grid,
        lambda fact, height, width: _bbox_contains_grid_corner(fact, height, width),
    )


def _solid_rectangle_at_corner_only(grid):
    def selected(fact, _height, _width):
        top, left, bottom, right = fact["bbox"]
        bbox_area = (bottom - top + 1) * (right - left + 1)
        return fact["corner"] and len(fact["cells"]) == bbox_area

    return _apply_orange_rival(grid, selected)


def _any_nonzero_component_at_corner(grid):
    """Rival: use corner occupancy, ignoring the distinguished orange color."""
    out = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 0
    }
    corners = {(0, 0), (0, width - 1), (height - 1, 0), (height - 1, width - 1)}
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        cells = {start}
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in _CARDINAL:
                neighbor = row + dr, col + dc
                if neighbor in unseen and grid[neighbor[0]][neighbor[1]] == color:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    stack.append(neighbor)
        if cells & corners:
            for row, col in cells:
                out[row][col] = 1
    return out


def _first_true_corner_only(grid):
    out = [list(row) for row in grid]
    corner_components = sorted(
        (fact for fact in _component_facts(grid) if fact["corner"]),
        key=lambda fact: min(fact["cells"]),
    )
    if corner_components:
        for row, col in corner_components[0]["cells"]:
            out[row][col] = 1
    return out


def _has_true_corner_component(grid) -> bool:
    return any(fact["corner"] for fact in _component_facts(grid))


def _has_corner_gap_decoy(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        not fact["corner"]
        and len(fact["edges"]) >= 2
        and _bbox_contains_grid_corner(fact, height, width)
        for fact in _component_facts(grid)
    )


def _has_strictly_interior_component(grid) -> bool:
    return any(not fact["edges"] for fact in _component_facts(grid))


def _has_nonrectangular_true_corner(grid) -> bool:
    for fact in _component_facts(grid):
        top, left, bottom, right = fact["bbox"]
        bbox_area = (bottom - top + 1) * (right - left + 1)
        if fact["corner"] and len(fact["cells"]) < bbox_area:
            return True
    return False


def _has_color5_corner_marker(grid) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        grid[row][col] == 5
        for row, col in (
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
        )
    )


def _has_multiple_true_corners(grid) -> bool:
    return sum(fact["corner"] for fact in _component_facts(grid)) >= 2


SEMANTIC_WITNESSES = {
    "true_corner_component": _has_true_corner_component,
    "corner_gap_decoy": _has_corner_gap_decoy,
    "strictly_interior_component": _has_strictly_interior_component,
    "nonrectangular_true_corner": _has_nonrectangular_true_corner,
    "color5_corner_marker": _has_color5_corner_marker,
    "multiple_true_corners": _has_multiple_true_corners,
}
SEMANTIC_RIVALS = {
    "identity": _identity,
    "recolor_all_orange": _recolor_all_orange,
    "touches_any_border": _touches_any_border,
    "touches_two_borders": _touches_two_borders,
    "bbox_contains_corner": _bbox_contains_corner,
    "solid_rectangle_at_corner_only": _solid_rectangle_at_corner_only,
    "any_nonzero_component_at_corner": _any_nonzero_component_at_corner,
    "first_true_corner_only": _first_true_corner_only,
}
WITNESS_RIVALS = {
    "true_corner_component": ["identity"],
    "corner_gap_decoy": [
        "recolor_all_orange",
        "touches_any_border",
        "touches_two_borders",
        "bbox_contains_corner",
    ],
    "strictly_interior_component": ["recolor_all_orange"],
    "nonrectangular_true_corner": ["solid_rectangle_at_corner_only"],
    "color5_corner_marker": ["any_nonzero_component_at_corner"],
    "multiple_true_corners": ["first_true_corner_only"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, object] = {}


def lesson_identifiable(demos, query) -> list[str]:
    """Name any executable rival that fits all demos but changes the query."""
    reasons = []
    pairs = list(demos) + [query]
    for ordinal, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {ordinal} must contain input and output grids")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {ordinal} does not follow the pinned exact-corner rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        changes_query = rival(query["input"]) != query["output"]
        if fits_demos and changes_query:
            reasons.append(f"{name} fits every demo but changes the query")
    return reasons
