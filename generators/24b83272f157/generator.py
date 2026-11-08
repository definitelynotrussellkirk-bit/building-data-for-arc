"""Semantic generator for ARC task 24b83272f157.

Find every same-color 4-connected object. Two objects are neighbors when
their one-step orthogonal dilations overlap (equivalently, their minimum
Manhattan cell distance is at most two). Recolor each whole object by degree:
0 -> 2, 1 -> 3, 2 -> 8, 3 -> 6, and 4 or more -> 9.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "24b83272f157"
VERSION = "3.0.0"
TASK_ID = "24b83272f157"
RULE_HASH = "ede817c8e772"
SUMMARY = (
    "Recolor each same-color 4-connected object by the number of other "
    "objects whose one-step orthogonal contact halos overlap: degree "
    "0/1/2/3/4+ becomes red/green/cyan/magenta/maroon (2/3/8/6/9)."
)
EXAMPLES_NEEDED = 4
AXES = {
    "scene_family": {
        "type": "str",
        "default": "rng linked|generalized (3:7)",
        "valid": "linked|generalized",
        "doc": (
            "linked preserves one complete public contact graph; generalized "
            "varies graph topology, object shape, degree, and repeated colors"
        ),
    },
}
INVARIANTS = [
    "background is black (0) and output dimensions equal input dimensions",
    "objects are same-color 4-connected components",
    "contact depends on minimum Manhattan cell distance <= 2",
    "each returned scene contains at least two distinct object degrees",
    "every object is recolored uniformly by degree, not by input color or size",
]

BACKGROUND = 0
COLORS = tuple(range(1, 10))
INPUT_COLORS = tuple(color for color in COLORS if color != 8)
DIFFICULTIES = {None, "default", "easy", "medium", "hard"}
DEGREE_COLORS = {0: 2, 1: 3, 2: 8, 3: 6, 4: 9}
GENERAL_PROFILES = (
    "short_chain_isolated",
    "chain_isolated",
    "star3_isolated",
    "star4_isolated",
    "cycle_isolated",
    "branched",
    "poly_chain",
)

# Input-only public descriptors. Coordinates are the nonzero singleton cells;
# colors are freshly permuted and outputs are always computed from semantics.
PUBLIC_PROFILES = (
    (
        "public_train_1",
        6,
        7,
        ((1, 1), (1, 3), (2, 2), (4, 6)),
    ),
    (
        "public_train_2",
        6,
        9,
        ((1, 1), (1, 3), (1, 5), (4, 8)),
    ),
    (
        "public_test_1",
        6,
        10,
        ((1, 1), (1, 3), (1, 5), (1, 7), (4, 9)),
    ),
)

POINT_PROFILES = {
    "short_chain_isolated": ((0, 0), (0, 2), (0, 4), (4, 5)),
    "chain_isolated": ((0, 0), (0, 2), (0, 4), (0, 6), (4, 3)),
    "star3_isolated": (
        (2, 2),
        (0, 2),
        (2, 0),
        (2, 4),
        (0, 4),
        (6, 6),
    ),
    "star4_isolated": (
        (2, 2),
        (0, 2),
        (2, 0),
        (2, 4),
        (4, 2),
        (0, 4),
        (6, 6),
    ),
    "cycle_isolated": ((0, 0), (0, 2), (2, 0), (2, 2), (6, 6)),
    "branched": ((2, 2), (0, 2), (2, 0), (2, 4), (0, 4)),
}


def _copy_grid(grid):
    return [list(row) for row in grid]


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == BACKGROUND or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in (
                    (-1, 0),
                    (1, 0),
                    (0, -1),
                    (0, 1),
                ):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))
            components.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                }
            )
    return components


def _objects_touch(first, second):
    return min(
        abs(row_a - row_b) + abs(col_a - col_b)
        for row_a, col_a in first["cells"]
        for row_b, col_b in second["cells"]
    ) <= 2


def _contact_graph(components):
    neighbors = [set() for _ in components]
    for first_index, first in enumerate(components):
        for second_index in range(first_index + 1, len(components)):
            if _objects_touch(first, components[second_index]):
                neighbors[first_index].add(second_index)
                neighbors[second_index].add(first_index)
    return tuple(frozenset(values) for values in neighbors)


def _linked_profile(height, width, components, degrees):
    if any(obj["size"] != 1 for obj in components):
        return None
    signature = (height, width, tuple(sorted(degrees)))
    return {
        (6, 7, (0, 2, 2, 2)): "public_train_1",
        (6, 9, (0, 1, 1, 2)): "public_train_2",
        (6, 10, (0, 1, 1, 2, 2)): "public_test_1",
    }.get(signature)


def _general_profile(components, degrees):
    ordered = tuple(sorted(degrees))
    if any(obj["size"] > 1 for obj in components):
        return "poly_chain"
    if ordered == (0, 1, 1, 2):
        return "short_chain_isolated"
    if ordered == (0, 1, 1, 2, 2):
        return "chain_isolated"
    if ordered == (0, 1, 2, 2, 2, 3):
        return "star3_isolated"
    if ordered == (0, 1, 1, 2, 2, 2, 4):
        return "star4_isolated"
    if ordered == (0, 2, 2, 2, 2):
        return "cycle_isolated"
    if ordered == (1, 2, 2, 2, 3):
        return "branched"
    return "other"


def _analyze(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return {
            "errors": ["grid must be a nonempty rectangular matrix"],
            "facts": None,
        }
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return {"errors": ["grid rows must be lists or tuples"], "facts": None}
    widths = {len(row) for row in grid}
    if len(widths) != 1 or 0 in widths:
        return {
            "errors": ["grid must be rectangular and nonempty"],
            "facts": None,
        }
    height = len(grid)
    width = next(iter(widths))
    if not (5 <= height <= 30 and 5 <= width <= 30):
        errors.append("grid must be 5..30 rows by 5..30 columns")
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cell values must be integer ARC colors 0..9")
        return {"errors": errors, "facts": None}

    components = _components(grid)
    graph = _contact_graph(components)
    degrees = tuple(len(neighbors) for neighbors in graph)
    if not 3 <= len(components) <= 10:
        errors.append("need 3..10 same-color connected objects")
    if components and max(obj["size"] for obj in components) > 6:
        errors.append("objects must stay small (at most six cells)")
    if len(set(degrees)) < 2:
        errors.append("scene must demonstrate at least two object degrees")
    if not any(degrees):
        errors.append("scene must contain at least one contact relation")
    if sum(obj["size"] for obj in components) > 0.25 * height * width:
        errors.append("objects must leave substantial black context")

    output = full_grid(height, width, BACKGROUND)
    for obj, degree in zip(components, degrees):
        output_color = DEGREE_COLORS.get(degree, 9)
        for row, col in obj["cells"]:
            output[row][col] = output_color
    linked_profile = _linked_profile(height, width, components, degrees)
    family = "linked" if linked_profile else "generalized"
    general_profile = None if linked_profile else _general_profile(
        components, degrees
    )
    facts = {
        "height": height,
        "width": width,
        "components": tuple(components),
        "graph": graph,
        "degrees": degrees,
        "degree_histogram": {
            degree: degrees.count(degree) for degree in sorted(set(degrees))
        },
        "output": output,
        "family": family,
        "linked_profile": linked_profile,
        "generalized_profile": general_profile,
        "object_count": len(components),
        "object_sizes": tuple(obj["size"] for obj in components),
        "edge_count": sum(degrees) // 2,
    }
    return {"errors": errors, "facts": facts}


def self_check(grid, *, difficulty=None, meta=None):
    return list(_analyze(grid)["errors"])


def rule_mirror(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return _copy_grid(analysis["facts"]["output"])


def canonical_profile_signature(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return "invalid"
    return analysis["facts"]["family"]


def observe_overrides(grid):
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    return {"scene_family": analysis["facts"]["family"]}


def _transform_cells(cell_groups, rng):
    groups = [list(cells) for cells in cell_groups]
    turns = rng.randrange(4)
    reflect = rng.random() < 0.5
    transformed = []
    for cells in groups:
        result = []
        for row, col in cells:
            for _ in range(turns):
                row, col = col, -row
            if reflect:
                col = -col
            result.append((row, col))
        transformed.append(result)
    min_row = min(row for cells in transformed for row, _ in cells)
    min_col = min(col for cells in transformed for _, col in cells)
    return [
        [(row - min_row, col - min_col) for row, col in cells]
        for cells in transformed
    ]


def _jitter_groups(cell_groups, rng):
    """Move whole objects slightly; the caller rejects graph changes."""
    shifted = []
    for cells in cell_groups:
        delta_row = rng.randint(-1, 1)
        delta_col = rng.randint(-1, 1)
        shifted.append(
            [
                (row + delta_row, col + delta_col)
                for row, col in cells
            ]
        )
    min_row = min(row for cells in shifted for row, _ in cells)
    min_col = min(col for cells in shifted for _, col in cells)
    return [
        [(row - min_row, col - min_col) for row, col in cells]
        for cells in shifted
    ]


def _paint_groups(height, width, groups, colors, rng):
    shape_height = max(row for cells in groups for row, _ in cells) + 1
    shape_width = max(col for cells in groups for _, col in cells) + 1
    if shape_height > height or shape_width > width:
        raise ValueError("contact graph does not fit canvas")
    top = rng.randint(0, height - shape_height)
    left = rng.randint(0, width - shape_width)
    grid = full_grid(height, width, BACKGROUND)
    for cells, color in zip(groups, colors):
        for row, col in cells:
            grid[top + row][left + col] = color
    return grid


def _build_linked(rng):
    profile, height, width, coordinates = rng.choice(PUBLIC_PROFILES)
    for _ in range(30):
        groups = [[coordinate] for coordinate in coordinates]
        groups = _transform_cells(groups, rng)
        colors = rng.sample(INPUT_COLORS, len(groups))
        try:
            grid = _paint_groups(height, width, groups, colors, rng)
        except ValueError:
            continue
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["linked_profile"] == profile
        ):
            return grid
    raise RuntimeError("linked contact profile construction drift")


def _shape_for_band(rng, band):
    ranges = {
        "easy": ((7, 10), (7, 12)),
        "medium": ((10, 14), (11, 16)),
        "hard": ((14, 18), (16, 21)),
    }
    (height_low, height_high), (width_low, width_high) = ranges[band]
    return (
        rng.randint(height_low, height_high),
        rng.randint(width_low, width_high),
    )


def _colors_for_groups(rng, count):
    colors = rng.sample(INPUT_COLORS, count)
    if count >= 4 and rng.random() < 0.45:
        # Repeat an input color on non-adjacent objects. The construction uses
        # a black gap, so these remain separate same-color components.
        colors[-1] = colors[0]
    return colors


def _build_generalized(rng, band):
    for _ in range(100):
        profile = rng.choice(GENERAL_PROFILES)
        height, width = _shape_for_band(rng, band)
        if profile == "poly_chain":
            groups = [
                [(0, 0), (1, 0)],
                [(0, 2), (1, 2)],
                [(0, 4), (1, 4)],
                [(5, 7), (6, 7), (6, 8)],
            ]
        else:
            groups = [
                [coordinate] for coordinate in POINT_PROFILES[profile]
            ]
        groups = _transform_cells(groups, rng)
        if rng.random() < 0.8:
            groups = _jitter_groups(groups, rng)
        colors = _colors_for_groups(rng, len(groups))
        try:
            grid = _paint_groups(height, width, groups, colors, rng)
        except ValueError:
            continue
        analysis = _analyze(grid)
        if (
            not analysis["errors"]
            and analysis["facts"]["family"] == "generalized"
            and analysis["facts"]["generalized_profile"] == profile
        ):
            return grid
    raise RuntimeError("could not realize generalized contact graph")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    family = ctx.draw_choice(
        "scene_family",
        (
            "linked",
            "linked",
            "linked",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
            "generalized",
        ),
    )
    band = "medium" if difficulty in (None, "default") else difficulty
    rng = ctx.draw_rng("scene")
    grid = (
        _build_linked(rng)
        if family == "linked"
        else _build_generalized(rng, band)
    )
    analysis = _analyze(grid)
    if analysis["errors"] or analysis["facts"]["family"] != family:
        raise RuntimeError(
            "internal construction error: "
            + "; ".join(
                analysis["errors"]
                or [
                    f"wanted {family}, observed "
                    f"{analysis['facts']['family']}"
                ]
            )
        )
    return grid
