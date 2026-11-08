"""Task-linked sampler for legend-ordered largest-component packing.

The selected Racket authority reads every nonzero color in row 0 from left to
right.  For each color it chooses the largest 4-connected body component,
crops that component's bounding box, and packs the crops horizontally with one
zero separator column.

This module generates labels only through the external Racket authority.  The
Python solvers below are diagnostic mirrors used by review witnesses and lesson
identifiability checks.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "192d2bc2de61"
TASK_ID = "192d2bc2de61"
RULE_HASH = "5ea0808c0383"
VERSION = "4.0.0"
SUMMARY = (
    "Three distinct colors form a row-0 legend whose cells may be contiguous, "
    "spaced, or offset.  One canonical-core profile has a single body motif per "
    "color; the diagnostic profiles add early small decoys before a uniquely "
    "larger body motif.  The largest motifs appear in a body order that "
    "differs from the legend.  Read all nonzero legend cells left-to-right, pick "
    "the largest 4-connected body component of each color, crop its bounding "
    "box, and pack the crops horizontally with one zero column between them."
)
INVARIANTS = [
    "row 0 contains three distinct nonzero legend colors; zero gaps and a leading zero are lawful",
    "row 1 is blank, so legend cells are disconnected from every body component",
    "each legend color has one uniquely largest main component; diagnostic profiles add one or two earlier singleton decoys",
    "main-component spatial order differs from legend order, so the legend controls output order",
    "ordinary draws use one of the four exact canonical canvas/palette profiles",
]

SCENE_PROFILES = {
    "prefix_10x13": {
        "height": 10,
        "width": 13,
        "legend_columns": (0, 1, 2),
        "decoys": 0,
        "main_sizes": (4, 5, 6),
    },
    "spaced_10x14": {
        "height": 10,
        "width": 14,
        "legend_columns": (0, 2, 4),
        "decoys": 1,
        "main_sizes": (5, 6, 4),
    },
    "offset_11x14": {
        "height": 11,
        "width": 14,
        "legend_columns": (1, 3, 5),
        "decoys": 2,
        "main_sizes": (6, 4, 5),
    },
    "wide_11x15": {
        "height": 11,
        "width": 15,
        "legend_columns": (0, 3, 6),
        "decoys": 2,
        "main_sizes": (4, 6, 5),
    },
}
SCHEDULE_PROFILES = tuple(SCENE_PROFILES)
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot deterministic curriculum",
        "valid": "prefix_10x13|spaced_10x14|offset_11x14|wide_11x15",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list = []
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

# Every shape is normalized, 4-connected, and contained in a 3x3 box.
_SHAPES = {
    4: (
        ((0, 0), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (1, 0), (2, 0)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
        ((0, 1), (1, 0), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
        ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
        ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)),
        ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0)),
        ((0, 0), (1, 0), (1, 1), (1, 2), (2, 1), (2, 2)),
    ),
}
_DERANGEMENTS = (
    (1, 2, 0),
    (2, 0, 1),
    (1, 0, 2),
    (2, 1, 0),
)
_PROFILE_BY_DIMS = {
    (spec["height"], spec["width"]): name
    for name, spec in SCENE_PROFILES.items()
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Cycle every profile; bands use distinct phase offsets."""
    del seed
    offset = {None: 0, "easy": 0, "medium": 1, "hard": 2}[difficulty]
    return SCHEDULE_PROFILES[(int(sample_index) + offset) % len(SCHEDULE_PROFILES)]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    if "scene_profile" in overrides:
        value = overrides["scene_profile"]
        if type(value) is not str or value not in SCENE_PROFILES:
            raise ValueError(
                "scene_profile must be one of " + ", ".join(SCHEDULE_PROFILES)
            )


def _paint(grid, cells: Iterable[tuple[int, int]], top: int, left: int, color: int) -> None:
    for dr, dc in cells:
        grid[top + dr][left + dc] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if "scene_profile" in overrides:
        profile_name = ctx.draw_choice("scene_profile", SCHEDULE_PROFILES)
    else:
        profile_name = ctx.draw_choice(
            "scene_profile", (schedule_profile(seed, sample_index, difficulty),)
        )
    spec = SCENE_PROFILES[profile_name]
    h, w = spec["height"], spec["width"]
    grid = full_grid(h, w, 0)

    legend = ctx.draw_distinct_colors("legend_colors", n=3, exclude=(0,))
    for column, color in zip(spec["legend_columns"], legend):
        grid[0][column] = color

    # Decoys are deliberately above every main motif.  The canonical examples
    # contain only one component per color, so "take the first component" fits
    # them all; these decoys make that rival visibly wrong.
    for index, color in enumerate(legend):
        if spec["decoys"] >= 1:
            first = (2, 4 * index)
            grid[first[0]][first[1]] = color
        if spec["decoys"] == 2:
            second = (3, 4 * index + 2)
            grid[second[0]][second[1]] = color

    # Three disjoint 3x3 body slots fit every profile.  A keyed derangement
    # breaks body-spatial order while preserving legend order as the authority.
    slot_columns = (0, 5, w - 3)
    slot_for_legend = ctx.draw_rng("body_order").choice(_DERANGEMENTS)
    shape_rng = ctx.draw_rng("main_shapes")
    main_top = h - 4
    for legend_index, color in enumerate(legend):
        size = spec["main_sizes"][legend_index]
        shape = shape_rng.choice(_SHAPES[size])
        _paint(
            grid,
            shape,
            main_top,
            slot_columns[slot_for_legend[legend_index]],
            color,
        )
    return grid


def _grid_error(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return "expected a nonempty rectangular grid"
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return "expected a nonempty rectangular grid"
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return "ragged grid"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "cells must be integer colors 0..9 (not bool/float)"
    return None


def _legend(grid):
    return [value for value in grid[0] if value != 0]


def _components_below(grid, color):
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(1, h)
        for c in range(w)
        if grid[r][c] == color
    }
    components = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        cells = {first}
        stack = [first]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    stack.append(point)
        components.append(cells)
    return components


def _component_key_largest(cells):
    return (-len(cells), min(r for r, _ in cells), min(c for _, c in cells))


def _component_key_first(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells), -len(cells))


def _crop(grid, cells):
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    return [list(row[c1 : c2 + 1]) for row in grid[r1 : r2 + 1]]


def _pack(blocks):
    if not blocks:
        return [[0]]
    height = max(len(block) for block in blocks)
    width = sum(len(block[0]) for block in blocks) + len(blocks) - 1
    out = full_grid(height, width, 0)
    left = 0
    for block in blocks:
        for r, row in enumerate(block):
            for c, value in enumerate(row):
                if value != 0:
                    out[r][left + c] = value
        left += len(block[0]) + 1
    return out


def _solve_with_legend_and_selector(grid, legend, selector: Callable):
    blocks = []
    for color in legend:
        components = _components_below(grid, color)
        if not components:
            return [[0]]
        blocks.append(_crop(grid, selector(components)))
    return _pack(blocks)


def _solve_intended(grid):
    """Diagnostic Python mirror; Racket remains the generated-label authority."""
    return _solve_with_legend_and_selector(
        grid,
        _legend(grid),
        lambda components: sorted(components, key=_component_key_largest)[0],
    )


def _solve_first_component(grid):
    return _solve_with_legend_and_selector(
        grid,
        _legend(grid),
        lambda components: sorted(components, key=_component_key_first)[0],
    )


def _solve_prefix_legend(grid):
    legend = []
    for value in grid[0]:
        if value == 0:
            break
        legend.append(value)
    return _solve_with_legend_and_selector(
        grid,
        legend,
        lambda components: sorted(components, key=_component_key_largest)[0],
    )


def _solve_body_order(grid):
    chosen = []
    for color in _legend(grid):
        components = _components_below(grid, color)
        if not components:
            return [[0]]
        chosen.append(sorted(components, key=_component_key_largest)[0])
    chosen.sort(key=lambda cells: (min(r for r, _ in cells), min(c for _, c in cells)))
    return _pack([_crop(grid, cells) for cells in chosen])


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    error = _grid_error(grid)
    if error:
        return [error]
    h, w = len(grid), len(grid[0])
    errors = []
    if not (8 <= h <= 20 and 9 <= w <= 20):
        errors.append("canvas dimensions must be within 8..20 by 9..20")

    legend = _legend(grid)
    if not 2 <= len(legend) <= 4:
        errors.append("row 0 must contain 2..4 nonzero legend cells")
    if len(legend) != len(set(legend)):
        errors.append("legend colors must be distinct")
    if h > 1 and any(value != 0 for value in grid[1]):
        errors.append("row 1 must separate the legend from body components")

    legend_colors = set(legend)
    body_colors = {value for row in grid[1:] for value in row if value != 0}
    unknown = sorted(body_colors - legend_colors)
    if unknown:
        errors.append(f"body contains colors absent from legend: {unknown}")

    for color in legend:
        components = _components_below(grid, color)
        if not components:
            errors.append(f"legend color {color} has no body component")
            continue
        sizes = [len(cells) for cells in components]
        if sizes.count(max(sizes)) != 1:
            errors.append(f"legend color {color} has no unique largest body component")
    return errors


def strict_canonical_like(grid):
    """Task grammar: sparse/offset legends and optional decoys are both lawful."""
    return self_check(grid)


def observe_overrides(grid):
    error = _grid_error(grid)
    if error:
        raise ValueError(error)
    dims = (len(grid), len(grid[0]))
    profile_name = _PROFILE_BY_DIMS.get(dims)
    if profile_name is None:
        raise ValueError(f"dimensions {dims} do not identify a declared scene_profile")
    spec = SCENE_PROFILES[profile_name]
    positions = tuple(c for c, value in enumerate(grid[0]) if value != 0)
    if positions != spec["legend_columns"]:
        raise ValueError(
            f"legend positions {positions} do not match scene_profile {profile_name}"
        )
    legend = _legend(grid)
    expected_components = spec["decoys"] + 1
    if len(legend) != 3 or any(
        len(_components_below(grid, color)) != expected_components for color in legend
    ):
        raise ValueError(
            f"body component counts do not match scene_profile {profile_name}"
        )
    return {"scene_profile": profile_name}


def _has_largest_choice(grid):
    try:
        for color in _legend(grid):
            components = _components_below(grid, color)
            if len(components) < 2:
                continue
            largest = sorted(components, key=_component_key_largest)[0]
            first = sorted(components, key=_component_key_first)[0]
            if largest != first:
                return _solve_first_component(grid) != _solve_intended(grid)
    except Exception:
        return False
    return False


def _has_nonprefix_legend(grid):
    try:
        positions = tuple(c for c, value in enumerate(grid[0]) if value != 0)
        return positions != tuple(range(len(positions))) and _solve_prefix_legend(grid) != _solve_intended(grid)
    except Exception:
        return False


def _has_legend_order_choice(grid):
    try:
        return _solve_body_order(grid) != _solve_intended(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "same_color_largest_choice": _has_largest_choice,
    "nonprefix_legend": _has_nonprefix_legend,
    "legend_order_controls_packing": _has_legend_order_choice,
}
SEMANTIC_RIVALS = {
    "first_component": _solve_first_component,
    "prefix_legend": _solve_prefix_legend,
    "body_order": _solve_body_order,
}
WITNESS_RIVALS = {
    "same_color_largest_choice": ["first_component"],
    "nonprefix_legend": ["prefix_legend"],
    "legend_order_controls_packing": ["body_order"],
}
# All five canonical pairs contain exactly one body component per legend color,
# so this wrong selector reproduces every public answer.
CANONICAL_SHORTCUTS = {"first_component": _solve_first_component}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Name declared rivals that fit every demonstration but change the query."""
    reasons = []
    for name, solver in sorted(LESSON_COMPETITORS.items()):
        try:
            fits = all(solver(deepcopy(pair["input"])) == pair["output"] for pair in demos)
            disagrees = solver(deepcopy(query["input"])) != query["output"]
        except Exception as exc:
            reasons.append(f"rival {name!r} could not be evaluated: {type(exc).__name__}: {exc}")
            continue
        if fits and disagrees:
            reasons.append(f"declared rival {name!r} fits every demo but changes the query")
    return reasons
