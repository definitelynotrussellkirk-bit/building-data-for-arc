"""Constructive curriculum for exemplar-shape matching.

The authoritative rule lives in the unchanged task-local Racket source.  This
module only samples lawful inputs: a connected shape appears in the top-left
5x5 exemplar window, and exactly one of three colored body components has the
same normalized binary shape.  The selected component is cropped and recolored
2 by the authority.

The curriculum deliberately makes all three body components share cell count
and bounding-box dimensions.  Therefore exact normalized shape—not position,
area, or bounding-box signature—is required.  The correct component rotates
through scan-order ranks 0, 1, and 2 so a three-example lesson defeats fixed
rank shortcuts, including the canonical-data shortcut "always choose the
middle component".
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from itertools import combinations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6be2608558c4"
TASK_ID = GENERATOR_ID
RULE_HASH = "11381854d14b"
VERSION = "3.0.0"
SUMMARY = (
    "A 5x5 top-left exemplar names a normalized binary shape.  Of three "
    "same-signature body components, exactly one is an exact shape match; "
    "the authority crops it and recolors it 2."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (0, 1, 2)
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "grid_h": {
        "type": "int",
        "default": "uniform 11..12",
        "valid": "11..12",
    },
    "grid_w": {
        "type": "int",
        "default": "uniform 13..15",
        "valid": "13..15",
    },
    "exemplar_size": {
        "type": "int",
        "default": "uniform 4..6",
        "valid": "4..6",
    },
}

INVARIANTS = [
    "the 5x5 top-left window contains one connected monochromatic 4..6-cell exemplar",
    "outside that window are exactly three disconnected monochromatic body components",
    "all three body components share exemplar cell count and bounding-box dimensions",
    "the three normalized body shapes are distinct and exactly one equals the exemplar",
    "four distinct nonzero input colors are used and reserved output color 2 is absent",
    "the exact-match component scan-order rank follows schedule_profile 0,1,2",
]

_ALLOWED_COLORS = (1, 3, 4, 5, 6, 7, 8, 9)
_AXIS_BOUNDS = {
    "grid_h": (11, 12),
    "grid_w": (13, 15),
    "exemplar_size": (4, 6),
}
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))

Shape = frozenset[tuple[int, int]]
Grid = list[list[int]]


def _normalize(cells: Iterable[tuple[int, int]]) -> Shape:
    points = tuple(cells)
    if not points:
        raise ValueError("cannot normalize an empty shape")
    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)
    return frozenset((row - min_row, col - min_col) for row, col in points)


def _shape_info(cells: Iterable[tuple[int, int]]) -> tuple[Shape, int, int]:
    shape = _normalize(cells)
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    return shape, height, width


def _connected(shape: Shape) -> bool:
    if not shape:
        return False
    seen = {next(iter(shape))}
    stack = list(seen)
    while stack:
        row, col = stack.pop()
        for dr, dc in _NEIGHBORS:
            point = (row + dr, col + dc)
            if point in shape and point not in seen:
                seen.add(point)
                stack.append(point)
    return len(seen) == len(shape)


@lru_cache(maxsize=1)
def _shape_groups() -> dict[int, tuple[tuple[Shape, ...], ...]]:
    """Enumerate connected 3x3 polyomino groups sharing (size, bbox)."""
    by_size: dict[int, list[tuple[Shape, ...]]] = {}
    universe = tuple((row, col) for row in range(3) for col in range(3))
    for size in range(4, 7):
        signatures: dict[tuple[int, int], set[Shape]] = {}
        for selected in combinations(universe, size):
            shape = _normalize(selected)
            if not _connected(shape):
                continue
            _, height, width = _shape_info(shape)
            if height < 2 or width < 2:
                continue
            signatures.setdefault((height, width), set()).add(shape)
        groups = []
        for signature in sorted(signatures):
            shapes = signatures[signature]
            if len(shapes) >= 3:
                groups.append(tuple(sorted(shapes, key=lambda item: tuple(sorted(item)))))
        if not groups:
            raise RuntimeError(f"no three-way shape group exists for size {size}")
        by_size[size] = groups
    return {size: tuple(groups) for size, groups in by_size.items()}


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Rotate the correct component through all three scan-order ranks."""
    del seed, difficulty
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer")
    return sample_index % 3


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not {type(value).__name__})")
        low, high = _AXIS_BOUNDS[name]
        if not low <= value <= high:
            raise ValueError(f"{name}={value} outside [{low}, {high}]")


def _placement_starts(width: int, shape_width: int) -> tuple[tuple[int, int, int], ...]:
    """All ordered three-component starts with at least one blank column."""
    starts = []
    for first in range(0, width - shape_width + 1):
        for second in range(first + shape_width + 1, width - shape_width + 1):
            for third in range(second + shape_width + 1, width - shape_width + 1):
                starts.append((first, second, third))
    return tuple(starts)


def _paint(grid: Grid, shape: Shape, row0: int, col0: int, color: int) -> None:
    for row, col in shape:
        if grid[row0 + row][col0 + col] != 0:
            raise RuntimeError("constructive placement collision")
        grid[row0 + row][col0 + col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic lawful input; every advertised override is exact."""
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    height = ctx.draw_int_strict("grid_h", 11, 12)
    width = ctx.draw_int_strict("grid_w", 13, 15)
    exemplar_size = ctx.draw_int_strict("exemplar_size", 4, 6)

    shape_rng = ctx.draw_rng("shape_curriculum")
    group = shape_rng.choice(_shape_groups()[exemplar_size])
    exemplar = shape_rng.choice(group)
    remaining = [shape for shape in group if shape != exemplar]
    ranked_decoys = sorted(
        remaining,
        key=lambda shape: (
            len(exemplar.symmetric_difference(shape)),
            tuple(sorted(shape)),
        ),
    )
    if difficulty == "easy":
        # Large symmetric differences make the exact-shape distinction clearer.
        decoy_a, decoy_b = ranked_decoys[-2:]
    elif difficulty == "hard":
        # Near-neighbor polyominoes force cell-level comparison, not signatures.
        decoy_a, decoy_b = ranked_decoys[:2]
    else:
        decoy_a, decoy_b = shape_rng.sample(remaining, 2)
    _, shape_height, shape_width = _shape_info(exemplar)

    match_rank = schedule_profile(seed, sample_index, difficulty)
    body_shapes = [decoy_a, decoy_b]
    body_shapes.insert(match_rank, exemplar)

    color_rng = ctx.draw_rng("palette")
    colors = color_rng.sample(_ALLOWED_COLORS, 4)
    exemplar_color, match_color, decoy_a_color, decoy_b_color = colors
    body_colors = [decoy_a_color, decoy_b_color]
    body_colors.insert(match_rank, match_color)

    grid = full_grid(height, width, 0)
    exemplar_rng = ctx.draw_rng("exemplar_position")
    exemplar_row = exemplar_rng.randint(0, 5 - shape_height)
    exemplar_col = exemplar_rng.randint(0, 5 - shape_width)
    _paint(grid, exemplar, exemplar_row, exemplar_col, exemplar_color)

    body_rng = ctx.draw_rng("body_position")
    body_row = body_rng.randint(6, height - shape_height)
    possible_starts = _placement_starts(width, shape_width)
    if not possible_starts:
        raise RuntimeError("declared grid width cannot fit the three-component curriculum")
    body_cols = body_rng.choice(possible_starts)
    for shape, col, color in zip(body_shapes, body_cols, body_colors):
        _paint(grid, shape, body_row, col, color)

    # This should be impossible by construction; keep a loud boundary assertion
    # so a future shape-bank or layout edit cannot silently shorten the lesson.
    errors = self_check(grid)
    if errors:
        raise RuntimeError(f"constructive generator produced an invalid grid: {errors}")
    return grid


def _grid_shape_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9 (bool is not an integer color)"]
    return []


def _body_components(grid) -> list[list[tuple[int, int]]]:
    """4-connected nonzero components after erasing the 5x5 exemplar window."""
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            if start_row < 5 and start_col < 5:
                continue
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in _NEIGHBORS:
                    next_row, next_col = row + dr, col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if next_row < 5 and next_col < 5:
                        continue
                    point = (next_row, next_col)
                    if point in seen or grid[next_row][next_col] == 0:
                        continue
                    seen.add(point)
                    stack.append(point)
            components.append(sorted(cells))
    return components


def _analyze(grid) -> tuple[list[str], dict[str, Any]]:
    errors = _grid_shape_errors(grid)
    if errors:
        return errors, {}

    height, width = len(grid), len(grid[0])
    if not 11 <= height <= 12:
        errors.append(f"grid height {height} outside canonical envelope 11..12")
    if not 13 <= width <= 15:
        errors.append(f"grid width {width} outside canonical envelope 13..15")
    if any(value == 2 for row in grid for value in row):
        errors.append("reserved output color 2 must be absent from the input")

    exemplar_cells = [
        (row, col)
        for row in range(min(5, height))
        for col in range(min(5, width))
        if grid[row][col] != 0
    ]
    exemplar_colors = {grid[row][col] for row, col in exemplar_cells}
    exemplar_shape: Shape | None = None
    exemplar_height = exemplar_width = 0
    if not 4 <= len(exemplar_cells) <= 6:
        errors.append(f"exemplar must contain 4..6 cells, found {len(exemplar_cells)}")
    if len(exemplar_colors) != 1:
        errors.append(f"exemplar must be monochromatic, found colors {sorted(exemplar_colors)}")
    if exemplar_cells:
        exemplar_shape, exemplar_height, exemplar_width = _shape_info(exemplar_cells)
        if not _connected(exemplar_shape):
            errors.append("exemplar must be 4-connected")
        if not (2 <= exemplar_height <= 3 and 2 <= exemplar_width <= 3):
            errors.append(
                f"exemplar bounding box must be 2..3 by 2..3, found "
                f"{exemplar_height}x{exemplar_width}"
            )

    components = _body_components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly three body components, found {len(components)}")

    body_records: list[dict[str, Any]] = []
    body_colors: list[int] = []
    for index, cells in enumerate(components):
        colors = {grid[row][col] for row, col in cells}
        if len(colors) != 1:
            errors.append(f"body component {index} must be monochromatic, found {sorted(colors)}")
        elif colors:
            body_colors.append(next(iter(colors)))
        shape, component_height, component_width = _shape_info(cells)
        if not 3 <= len(cells) <= 6:
            errors.append(f"body component {index} must contain 3..6 cells, found {len(cells)}")
        if component_height > 3 or component_width > 3:
            errors.append(
                f"body component {index} bounding box exceeds 3x3: "
                f"{component_height}x{component_width}"
            )
        body_records.append(
            {
                "cells": cells,
                "shape": shape,
                "height": component_height,
                "width": component_width,
                "signature": (len(cells), component_height, component_width),
            }
        )

    if len(body_colors) == len(components) and len(set(body_colors)) != len(body_colors):
        errors.append("body components must use distinct colors")
    if exemplar_colors and any(color in exemplar_colors for color in body_colors):
        errors.append("exemplar and body components must use distinct colors")
    palette = {value for row in grid for value in row if value != 0}
    if len(palette) != 4:
        errors.append(f"expected exactly four distinct nonzero input colors, found {len(palette)}")

    matches: list[int] = []
    if exemplar_shape is not None:
        matches = [
            index for index, record in enumerate(body_records)
            if record["shape"] == exemplar_shape
        ]
        if len(matches) != 1:
            errors.append(f"expected exactly one exact exemplar match, found {len(matches)}")

    return errors, {
        "height": height,
        "width": width,
        "exemplar_cells": exemplar_cells,
        "exemplar_shape": exemplar_shape,
        "exemplar_height": exemplar_height,
        "exemplar_width": exemplar_width,
        "components": body_records,
        "matches": matches,
        "match_rank": matches[0] if len(matches) == 1 else None,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes; never raise on arbitrary input."""
    del difficulty, meta
    try:
        errors, _ = _analyze(grid)
        return errors
    except Exception as exc:  # defensive API boundary for malformed foreign objects
        return [f"could not analyze grid: {type(exc).__name__}: {exc}"]


def strict_canonical_like(grid) -> list[str]:
    """The declared ordinary distribution is exactly the checked manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors, analysis = _analyze(grid)
    if errors:
        raise ValueError(f"cannot observe axes on malformed grid: {errors}")
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "exemplar_size": len(analysis["exemplar_cells"]),
    }


def _component_output(record: dict[str, Any]) -> Grid:
    shape: Shape = record["shape"]
    return [
        [2 if (row, col) in shape else 0 for col in range(record["width"])]
        for row in range(record["height"])
    ]


def rule_mirror(grid) -> Grid:
    """Independent Python mirror used only for tests and semantic diagnostics."""
    errors, analysis = _analyze(grid)
    if errors:
        raise ValueError(f"rule_mirror requires a lawful grid: {errors}")
    return _component_output(analysis["components"][analysis["match_rank"]])


def _always_middle(grid) -> Grid:
    errors, analysis = _analyze(grid)
    if errors:
        raise ValueError(f"rival requires a lawful grid: {errors}")
    return _component_output(analysis["components"][1])


def _signature_rank(grid, *, last: bool) -> Grid:
    errors, analysis = _analyze(grid)
    if errors:
        raise ValueError(f"rival requires a lawful grid: {errors}")
    signature = (
        len(analysis["exemplar_cells"]),
        analysis["exemplar_height"],
        analysis["exemplar_width"],
    )
    candidates = [
        record for record in analysis["components"]
        if record["signature"] == signature
    ]
    if not candidates:
        return _always_middle(grid)
    return _component_output(candidates[-1] if last else candidates[0])


def _first_same_signature(grid) -> Grid:
    return _signature_rank(grid, last=False)


def _last_same_signature(grid) -> Grid:
    return _signature_rank(grid, last=True)


def _disagrees(grid, rival) -> bool:
    try:
        return rival(grid) != rule_mirror(grid)
    except (TypeError, ValueError):
        return False


SEMANTIC_RIVALS = {
    "always_middle_component": _always_middle,
    "first_same_signature": _first_same_signature,
    "last_same_signature": _last_same_signature,
}
SEMANTIC_WITNESSES = {
    "match_not_middle": lambda grid: _disagrees(grid, _always_middle),
    "match_not_first_signature": lambda grid: _disagrees(grid, _first_same_signature),
    "match_not_last_signature": lambda grid: _disagrees(grid, _last_same_signature),
}
WITNESS_RIVALS = {
    "match_not_middle": ["always_middle_component"],
    "match_not_first_signature": ["first_same_signature"],
    "match_not_last_signature": ["last_same_signature"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Require demos to eliminate every declared rival that changes the query."""
    errors: list[str] = []
    query_input = query.get("input") if isinstance(query, dict) else None
    query_errors = self_check(query_input)
    if query_errors:
        return [f"query input is not lawful: {query_errors}"]
    truth = rule_mirror(query_input)
    if query.get("output") != truth:
        errors.append("query output disagrees with the exemplar-match rule")

    for index, demo in enumerate(demos):
        demo_input = demo.get("input") if isinstance(demo, dict) else None
        demo_errors = self_check(demo_input)
        if demo_errors:
            errors.append(f"demo {index} input is not lawful: {demo_errors}")
            continue
        if demo.get("output") != rule_mirror(demo_input):
            errors.append(f"demo {index} output disagrees with the exemplar-match rule")
    if errors:
        return errors

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo["output"]
            for demo in demos
        )
        if survives and competitor(query_input) != truth:
            errors.append(
                f"demos remain compatible with competitor {name!r}, which changes the query answer"
            )
    return errors


def mutation_fixtures() -> list[tuple[str, Grid]]:
    """Task-specific must-reject near misses for generic defect lint."""
    base = generate(95017, 5, difficulty="medium")

    no_exemplar = deepcopy(base)
    for row in range(5):
        for col in range(5):
            no_exemplar[row][col] = 0

    reserved_output_color = deepcopy(base)
    reserved_output_color[-1][-1] = 2

    missing_component = deepcopy(base)
    _, analysis = _analyze(base)
    missing_color = base[analysis["components"][0]["cells"][0][0]][
        analysis["components"][0]["cells"][0][1]
    ]
    for row in range(len(missing_component)):
        for col in range(len(missing_component[0])):
            if missing_component[row][col] == missing_color:
                missing_component[row][col] = 0

    tied_match = deepcopy(base)
    _, analysis = _analyze(base)
    replacement_index = next(
        index for index in range(3) if index != analysis["match_rank"]
    )
    replacement = analysis["components"][replacement_index]
    replacement_color = tied_match[replacement["cells"][0][0]][replacement["cells"][0][1]]
    top = min(row for row, _ in replacement["cells"])
    left = min(col for _, col in replacement["cells"])
    for row, col in replacement["cells"]:
        tied_match[row][col] = 0
    for row, col in analysis["exemplar_shape"]:
        tied_match[top + row][left + col] = replacement_color

    return [
        ("missing_exemplar", no_exemplar),
        ("reserved_output_color_in_input", reserved_output_color),
        ("missing_body_component", missing_component),
        ("two_exact_matches", tied_match),
    ]
