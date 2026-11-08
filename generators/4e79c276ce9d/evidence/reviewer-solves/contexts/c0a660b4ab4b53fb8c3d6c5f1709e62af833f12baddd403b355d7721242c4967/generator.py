"""Reviewed generator for ARC task 4e79c276ce9d.

Canonical rule
--------------
Find monochrome four-connected nonzero components.  Select the component with
fewest cells (canonical tie-break: top row, then left column), translate its
cells to the origin, and output that exact monochrome shape cropped to its
bounding box.

Curriculum
----------
The six-step schedule alternates two canonical-profile examples with four
counterexample-rich examples.  Every three consecutive demonstrations contain
at least two rich examples, so holding out any one of four consecutive pairs
still leaves a demonstration that distinguishes the declared rivals.

The rich scene makes the true smallest component sparse while a larger compact
component has the smaller bounding box.  The target also shares its color with
a larger diagonally touching component and touches a different-colored object
by an edge.  Those constructions distinguish cell count from bbox area, color
frequency, color buckets, eight-connectivity, multicolor connectivity, solid
bbox output, and scan-position selection.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "4e79c276ce9d"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "5d74c60efd43"

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 6
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A canonical-scale zero-background grid contains four monochrome "
    "four-connected objects with one uniquely smallest by cell count. Crop "
    "that component exactly to its bbox. A six-step schedule preserves exact "
    "canonical dimension/palette profiles and repeatedly contrasts cell count "
    "with bbox area, color frequency, color grouping, 8-connectivity, "
    "multicolor connectivity, solid-bbox output, and scan-order selection."
)

INVARIANTS = [
    "background is 0 and all cells are literal ARC colors 0..9",
    "there are at least two monochrome four-connected foreground components",
    "exactly one component has the minimum cell count",
    "the selected component's bbox contains only its color and background",
    "ordinary draws contain four components and match an exact canonical input profile",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "six-step canonical-profile schedule",
        "valid": "9..12",
    },
    "grid_w": {
        "type": "int",
        "default": "six-step canonical-profile schedule",
        "valid": "10..13",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# profile, default (height, width).  Together with the profile palette, every
# entry is one of the five exact canonical (height, width, palette-size) tuples.
_SCHEDULE = (
    ("canonical", (11, 11)),
    ("witness_l", (10, 12)),
    ("witness_z", (12, 10)),
    ("canonical", (10, 10)),
    ("witness_l", (9, 13)),
    ("witness_z", (10, 12)),
)

# Object order is target, compact distractor, upper distractor, right distractor.
_CANONICAL_OBJECTS = (
    ((6, 4), (7, 4)),
    ((6, 1), (6, 2), (6, 3)),
    ((0, 2), (0, 3), (1, 2), (1, 3)),
    ((0, 7), (0, 8), (0, 9), (1, 7), (2, 7)),
)
_WITNESS_L_OBJECTS = (
    ((4, 4), (5, 4), (6, 4), (7, 4), (7, 5)),
    ((4, 1), (4, 2), (4, 3), (5, 1), (5, 2), (5, 3)),
    ((0, 2), (0, 3), (1, 2), (1, 3), (2, 2), (2, 3), (3, 3)),
    ((0, 6), (0, 7), (0, 8), (0, 9), (1, 6), (1, 7), (1, 8), (1, 9)),
)
_WITNESS_Z_OBJECTS = (
    ((4, 4), (5, 4), (6, 4), (6, 5), (7, 5)),
    _WITNESS_L_OBJECTS[1],
    _WITNESS_L_OBJECTS[2],
    _WITNESS_L_OBJECTS[3],
)


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Return the versioned semantic profile for this ordinary draw."""
    del seed, difficulty
    return _SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD][0]


def _components(
    grid: list[list[int]], *, connectivity: int = 4, multicolor: bool = False
) -> list[dict[str, Any]]:
    """Monochrome components by default; optional any-color connectivity."""
    h, w = len(grid), len(grid[0])
    if connectivity == 4:
        steps = ((-1, 0), (0, -1), (0, 1), (1, 0))
    elif connectivity == 8:
        steps = (
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1), (0, 1),
            (1, -1), (1, 0), (1, 1),
        )
    else:
        raise ValueError("connectivity must be 4 or 8")

    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(h):
        for col in range(w):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            anchor_color = grid[row][col]
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in steps:
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < h and 0 <= next_col < w):
                        continue
                    if (next_row, next_col) in seen or grid[next_row][next_col] == 0:
                        continue
                    if not multicolor and grid[next_row][next_col] != anchor_color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            rows = [position[0] for position in cells]
            cols = [position[1] for position in cells]
            colors = {grid[r][c] for r, c in cells}
            result.append({
                "color": anchor_color if len(colors) == 1 else None,
                "colors": tuple(sorted(colors)),
                "cells": tuple(sorted(cells)),
                "size": len(cells),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return result


def _color_buckets(grid: list[list[int]]) -> list[dict[str, Any]]:
    by_color: dict[int, list[tuple[int, int]]] = {}
    for row, line in enumerate(grid):
        for col, value in enumerate(line):
            if value:
                by_color.setdefault(value, []).append((row, col))
    result = []
    for color, cells in sorted(by_color.items()):
        rows = [position[0] for position in cells]
        cols = [position[1] for position in cells]
        result.append({
            "color": color,
            "colors": (color,),
            "cells": tuple(sorted(cells)),
            "size": len(cells),
            "bbox": (min(rows), min(cols), max(rows), max(cols)),
        })
    return result


def _rank(component: dict[str, Any]) -> tuple[Any, ...]:
    return component["size"], component["bbox"]


def _bbox_area(component: dict[str, Any]) -> int:
    top, left, bottom, right = component["bbox"]
    return (bottom - top + 1) * (right - left + 1)


def _render_component(
    grid: list[list[int]], component: dict[str, Any], *, solid: bool = False
) -> list[list[int]]:
    top, left, bottom, right = component["bbox"]
    out_h, out_w = bottom - top + 1, right - left + 1
    if solid:
        color = component["color"]
        if color is None:
            raise ValueError("cannot solid-fill a multicolor component")
        return full_grid(out_h, out_w, color)
    out = full_grid(out_h, out_w, 0)
    for row, col in component["cells"]:
        out[row - top][col - left] = grid[row][col]
    return out


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains label authority."""
    components = _components(grid)
    if not components:
        raise ValueError("cannot select an object from an empty foreground")
    return _render_component(grid, min(components, key=_rank))


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(
    grid: list[list[int]], *, difficulty: str | None = None, meta: dict[str, Any] | None = None
) -> list[str]:
    """Accept the canonical domain and verify the unique-smallest contract."""
    del difficulty
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["grid rows must be nonempty sequences"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]
    height = len(grid)
    if not (1 <= height <= 30 and 1 <= width <= 30):
        return [f"grid dimensions must be within 1..30, got {height}x{width}"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid values must be literal integer ARC colors 0..9"]
    if not any(value == 0 for row in grid for value in row):
        return ["background color 0 must be present"]

    components = sorted(_components([list(row) for row in grid]), key=_rank)
    errors: list[str] = []
    if len(components) < 2:
        errors.append(f"expected at least two components, got {len(components)}")
    elif components[0]["size"] == components[1]["size"]:
        errors.append("minimum component size must be unique")

    if components:
        target = components[0]
        target_color = target["color"]
        top, left, bottom, right = target["bbox"]
        if any(
            grid[row][col] not in (0, target_color)
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        ):
            errors.append("smallest component's bbox contains another color")

    requested = meta.get("overrides") if isinstance(meta, dict) else None
    if isinstance(requested, dict):
        observed = observe_overrides([list(row) for row in grid])
        for name in AXES:
            value = requested.get(name)
            if value is not None and observed[name] != value:
                errors.append(
                    f"override {name}={value!r} realized as {observed[name]!r}"
                )
    return errors


def strict_canonical_like(grid: list[list[int]]) -> list[str]:
    return self_check(grid)


def _transform_point(row: int, col: int, code: int) -> tuple[int, int]:
    if code == 1:
        return col, -row
    if code == 2:
        return -row, -col
    if code == 3:
        return -col, row
    if code == 4:
        return row, -col
    if code == 5:
        return -row, col
    if code == 6:
        return col, row
    if code == 7:
        return -col, -row
    return row, col


def _transform_objects(
    motifs: tuple[tuple[tuple[int, int], ...], ...], code: int
) -> tuple[tuple[tuple[int, int], ...], ...]:
    transformed = [
        [_transform_point(row, col, code) for row, col in cells]
        for cells in motifs
    ]
    all_cells = [cell for cells in transformed for cell in cells]
    min_row = min(row for row, _ in all_cells)
    min_col = min(col for _, col in all_cells)
    return tuple(
        tuple(sorted((row - min_row, col - min_col) for row, col in cells))
        for cells in transformed
    )


def _scene_dims(motifs: tuple[tuple[tuple[int, int], ...], ...]) -> tuple[int, int]:
    cells = [cell for motif in motifs for cell in motif]
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def _validate_call(
    seed: int, sample_index: int, difficulty: str | None, overrides: dict[str, Any]
) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axes: {', '.join(unknown)}")
    bounds = {"grid_h": (9, 12), "grid_w": (10, 13)}
    for name, (low, high) in bounds.items():
        value = overrides.get(name)
        if value is not None and (type(value) is not int or not low <= value <= high):
            raise ValueError(f"{name} must be a literal integer in {low}..{high}")


def generate(
    seed: int,
    sample_index: int,
    *,
    difficulty: str | None = None,
    **overrides: Any,
) -> list[list[int]]:
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile, default_dims = _SCHEDULE[sample_index % LESSON_SCHEDULE_PERIOD]
    if overrides.get("grid_h") is None:
        height = ctx.draw_int("grid_h", default_dims[0], default_dims[0])
    else:
        height = ctx.draw_int("grid_h", 9, 12)
    if overrides.get("grid_w") is None:
        width = ctx.draw_int("grid_w", default_dims[1], default_dims[1])
    else:
        width = ctx.draw_int("grid_w", 10, 13)

    rng = ctx.draw_rng(f"scene:{difficulty}")
    if profile == "canonical":
        motifs = _CANONICAL_OBJECTS
        colors = rng.sample(range(1, 10), 4)
    else:
        motifs = _WITNESS_L_OBJECTS if profile == "witness_l" else _WITNESS_Z_OBJECTS
        palette = rng.sample(range(1, 10), 3)
        colors = [palette[0], palette[1], palette[0], palette[2]]

    # Preserve a non-target object before the target in scan order so the
    # declared top-left rival is contradicted on every ordinary draw.  These
    # four dihedral transforms retain that ordering while still varying target
    # orientation.
    transformed = _transform_objects(motifs, rng.choice((0, 1, 4, 6)))
    scene_h, scene_w = _scene_dims(transformed)
    if scene_h > height or scene_w > width:
        raise AssertionError(
            f"scene {scene_h}x{scene_w} does not fit requested {height}x{width}"
        )
    top = rng.randrange(height - scene_h + 1)
    left = rng.randrange(width - scene_w + 1)
    grid = full_grid(height, width, 0)
    for cells, color in zip(transformed, colors):
        for row, col in cells:
            if grid[top + row][left + col] != 0:
                raise AssertionError("scene objects unexpectedly overlap")
            grid[top + row][left + col] = color

    observed = observe_overrides(grid)
    expected = {"grid_h": height, "grid_w": width}
    if observed != expected:
        raise AssertionError(f"layout realized {observed}, expected {expected}")
    findings = self_check(grid, meta={"overrides": expected})
    if findings:
        raise AssertionError(f"constructed grid violates its contract: {findings}")
    return grid


# Plausible alternatives.  The first six fit every labeled canonical pair;
# generated witness profiles are designed to refute all seven.
def _rival_bbox_area(grid: list[list[int]]) -> list[list[int]]:
    components = _components(grid)
    target = min(components, key=lambda obj: (_bbox_area(obj), obj["size"], obj["bbox"]))
    return _render_component(grid, target)


def _rival_solid_bbox(grid: list[list[int]]) -> list[list[int]]:
    target = min(_components(grid), key=_rank)
    return _render_component(grid, target, solid=True)


def _rival_multicolor_connectivity(grid: list[list[int]]) -> list[list[int]]:
    target = min(_components(grid, multicolor=True), key=_rank)
    return _render_component(grid, target)


def _rival_eight_connectivity(grid: list[list[int]]) -> list[list[int]]:
    target = min(_components(grid, connectivity=8), key=_rank)
    return _render_component(grid, target)


def _rival_rare_color(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value)
    target = min(
        _components(grid),
        key=lambda obj: (counts[obj["color"]], obj["bbox"]),
    )
    return _render_component(grid, target)


def _rival_color_partition(grid: list[list[int]]) -> list[list[int]]:
    target = min(_color_buckets(grid), key=_rank)
    return _render_component(grid, target)


def _rival_top_left(grid: list[list[int]]) -> list[list[int]]:
    target = min(_components(grid), key=lambda obj: obj["bbox"])
    return _render_component(grid, target)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "bbox_area": _rival_bbox_area,
    "solid_bbox": _rival_solid_bbox,
    "multicolor_connectivity": _rival_multicolor_connectivity,
    "eight_connectivity": _rival_eight_connectivity,
    "rare_color": _rival_rare_color,
    "color_partition": _rival_color_partition,
    "top_left": _rival_top_left,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "bbox_area",
        "solid_bbox",
        "multicolor_connectivity",
        "eight_connectivity",
        "rare_color",
        "color_partition",
    )
}

SEMANTIC_WITNESSES = {
    "cell_count_not_bbox_area": lambda grid: _rival_bbox_area(grid) != rule_mirror(grid),
    "preserve_shape_not_solid_bbox": lambda grid: _rival_solid_bbox(grid) != rule_mirror(grid),
    "colors_separate_edge_touching_objects": lambda grid: _rival_multicolor_connectivity(grid) != rule_mirror(grid),
    "four_not_eight_connectivity": lambda grid: _rival_eight_connectivity(grid) != rule_mirror(grid),
    "component_size_not_color_frequency": lambda grid: _rival_rare_color(grid) != rule_mirror(grid),
    "components_not_whole_color_buckets": lambda grid: _rival_color_partition(grid) != rule_mirror(grid),
    "size_not_scan_position": lambda grid: _rival_top_left(grid) != rule_mirror(grid),
}
WITNESS_RIVALS = {
    "cell_count_not_bbox_area": ["bbox_area"],
    "preserve_shape_not_solid_bbox": ["solid_bbox"],
    "colors_separate_edge_touching_objects": ["multicolor_connectivity"],
    "four_not_eight_connectivity": ["eight_connectivity"],
    "component_size_not_color_frequency": ["rare_color"],
    "components_not_whole_color_buckets": ["color_partition"],
    "size_not_scan_position": ["top_left"],
}


def lesson_identifiable(
    demos: list[dict[str, list[list[int]]]],
    query: dict[str, list[list[int]]],
) -> list[str]:
    """Check finite declared-rival support; not universal identifiability."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {index} must contain input and output")
            continue
        findings = self_check(pair["input"])
        errors.extend(f"demo {index}: {finding}" for finding in findings)
        if not findings and rule_mirror(pair["input"]) != pair["output"]:
            errors.append(f"demo {index}: output disagrees with the rule mirror")
    if not isinstance(query, dict) or "input" not in query:
        errors.append("query must contain an input")
    else:
        findings = self_check(query["input"])
        errors.extend(f"query: {finding}" for finding in findings)
        if not findings and "output" in query and rule_mirror(query["input"]) != query["output"]:
            errors.append("query output disagrees with the rule mirror")
    if errors:
        return errors
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            errors.append(f"competitor {name!r} survives all demonstrations")
    return errors
