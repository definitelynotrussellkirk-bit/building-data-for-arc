"""Constructive generator for ARC task b8259d813f79.

The unchanged Racket authority replaces every 4-connected nonzero object with
one same-colour cell at the floor midpoint of its tight bounding box.  This
sampler deliberately separates *objects* from *colours*: two disconnected
objects may share a colour, and asymmetric even-width objects distinguish the
bbox midpoint from cell-centroid and upper-midpoint shortcuts.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b8259d813f79"
TASK_ID = GENERATOR_ID
RULE_HASH = "60b82500e77c"
VERSION = "2.0.0"

SUMMARY = (
    "Three or four isolated 4-connected objects occupy a 0-background grid. "
    "Objects contain five or six cells and use two or three foreground colours, "
    "so disconnected objects can share a colour. Replace each object—not each "
    "colour—with one same-colour cell at floor((r1+r2)/2, (c1+c2)/2) of its "
    "tight bounding box. A three-profile schedule alternates canonical 3x3 "
    "objects with repeated-colour asymmetric 2x4 witnesses."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
MIN_STRICT_FRAC = 0.20

INVARIANTS = [
    "rectangular 8..14 by 10..16 grid with background 0",
    "exactly 3..4 isolated 4-connected objects",
    "each object has 5..6 cells and a 3x3 or 2x4 bounding box",
    "exactly 2..3 foreground colours; repeated colours may label disconnected objects",
    "all object bbox-center positions are distinct",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "three-profile deterministic schedule with canonical anchors",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "three-profile deterministic schedule with canonical anchors",
        "valid": "10..16",
    },
    "n_blobs": {
        "type": "int",
        "default": "3 on canonical/witness-B profiles; 4 on witness-A",
        "valid": "3..4",
    },
    "n_distinct_colors": {
        "type": "int",
        "default": "3 on canonical profile; 2 on witness profiles",
        "valid": "2..3",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = ("canonical", "witness_a", "witness_b")
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_CANONICAL_DIMS = ((9, 10), (8, 11), (10, 10), (9, 11))
_HEIGHT_CYCLES = {
    "easy": (8, 9, 10, 11, 12, 13, 14),
    "medium": (9, 11, 13, 14, 12, 10, 8),
    "hard": (14, 13, 12, 11, 10, 9, 8),
}
_WIDTH_CYCLES = {
    "easy": (10, 11, 12, 13, 14, 15, 16),
    "medium": (11, 13, 15, 16, 14, 12, 10),
    "hard": (16, 15, 14, 13, 12, 11, 10),
}

# Every canonical shape spans a 3x3 bbox and contains five or six cells.
_CANONICAL_SHAPES: tuple[tuple[tuple[int, int], ...], ...] = (
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 1), (0, 2), (1, 1), (2, 0), (2, 1), (2, 2)),
)

# Bbox floor midpoint=(0,1); nearest cell centroid=(0,2); upper midpoint=(1,2).
_ASYMMETRIC_WITNESS: tuple[tuple[int, int], ...] = (
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (1, 3),
)
_BROAD_SHAPES = _CANONICAL_SHAPES + (
    _ASYMMETRIC_WITNESS,
    ((0, 0), (0, 1), (0, 2), (0, 3), (1, 2), (1, 3)),
)

# Placement reserves a 3x4 footprint around every shape. Compatible footprints
# have at least one blank row or column between them, so objects never 4-touch.
_FOOTPRINT_H = 3
_FOOTPRINT_W = 4


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the finite semantic profile for a production sample."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_controls(seed, sample_index, difficulty, overrides) -> None:
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    bounds = {
        "grid_h": (8, 14),
        "grid_w": (10, 16),
        "n_blobs": (3, 4),
        "n_distinct_colors": (2, 3),
    }
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool or a coercible value)")
        lo, hi = bounds[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def _scheduled_int(ctx, overrides, name: str, scheduled: int, lo: int, hi: int) -> int:
    """Record an exact scheduled default while preserving the full override domain."""
    if name in overrides and overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _defaults(seed: int, sample_index: int, difficulty) -> tuple[int, int, int, int]:
    profile = schedule_profile(seed, sample_index, difficulty)
    band = difficulty or "medium"
    block = sample_index // LESSON_SCHEDULE_PERIOD
    if profile == "canonical":
        height, width = _CANONICAL_DIMS[(block + abs(seed)) % len(_CANONICAL_DIMS)]
        return height, width, 3, 3
    offset = (block + abs(seed)) % len(_HEIGHT_CYCLES[band])
    height = _HEIGHT_CYCLES[band][offset]
    width = _WIDTH_CYCLES[band][(offset * 3 + (profile == "witness_b")) % len(_WIDTH_CYCLES[band])]
    if profile == "witness_a":
        return height, width, 4, 2
    return height, width, 3, 2


def _footprints_compatible(first: tuple[int, int], second: tuple[int, int]) -> bool:
    r1, c1 = first
    r2, c2 = second
    return (
        r1 + _FOOTPRINT_H < r2
        or r2 + _FOOTPRINT_H < r1
        or c1 + _FOOTPRINT_W < c2
        or c2 + _FOOTPRINT_W < c1
    )


def _choose_anchors(height: int, width: int, count: int, rng) -> list[tuple[int, int]]:
    candidates = [
        (row, column)
        for row in range(height - _FOOTPRINT_H + 1)
        for column in range(width - _FOOTPRINT_W + 1)
    ]
    rng.shuffle(candidates)

    def search(start: int, chosen: list[tuple[int, int]]) -> list[tuple[int, int]] | None:
        if len(chosen) == count:
            return list(chosen)
        need = count - len(chosen)
        if len(candidates) - start < need:
            return None
        for index in range(start, len(candidates)):
            candidate = candidates[index]
            if all(_footprints_compatible(candidate, prior) for prior in chosen):
                chosen.append(candidate)
                found = search(index + 1, chosen)
                if found is not None:
                    return found
                chosen.pop()
        return None

    found = search(0, [])
    if found is None:  # The declared minimum 8x10 has four corner placements.
        raise RuntimeError(
            f"could not place {count} isolated 3x4 footprints in {height}x{width}"
        )
    return sorted(found)


def _shape_schedule(profile: str, count: int, rng) -> list[tuple[tuple[int, int], ...]]:
    if profile == "canonical":
        pool = list(_CANONICAL_SHAPES)
        rng.shuffle(pool)
        return [pool[index % len(pool)] for index in range(count)]
    # Both witness profiles include the same decisive first object. This means
    # any three demonstrations obtained by holding one item out of four
    # consecutive samples still retain a centroid/upper-midpoint witness.
    return [_ASYMMETRIC_WITNESS] + [rng.choice(_BROAD_SHAPES) for _ in range(count - 1)]


def _color_schedule(count: int, distinct: int, rng) -> list[int]:
    palette = rng.sample(list(range(1, 10)), distinct)
    colors = list(palette)
    colors.extend(palette[index % distinct] for index in range(count - distinct))
    rng.shuffle(colors)
    return colors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one lawful input with exact, observable public controls."""
    _validate_controls(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_blobs, default_colors = _defaults(
        seed, sample_index, difficulty
    )
    height = _scheduled_int(ctx, overrides, "grid_h", default_h, 8, 14)
    width = _scheduled_int(ctx, overrides, "grid_w", default_w, 10, 16)
    n_blobs = _scheduled_int(ctx, overrides, "n_blobs", default_blobs, 3, 4)
    n_distinct = _scheduled_int(
        ctx, overrides, "n_distinct_colors", default_colors, 2, 3
    )

    profile = schedule_profile(seed, sample_index, difficulty)
    anchors = _choose_anchors(height, width, n_blobs, ctx.draw_rng("placements"))
    shapes = _shape_schedule(profile, n_blobs, ctx.draw_rng("shapes"))
    colors = _color_schedule(n_blobs, n_distinct, ctx.draw_rng("colors"))

    grid = full_grid(height, width, 0)
    for (top, left), shape, color in zip(anchors, shapes, colors):
        for drow, dcolumn in shape:
            row, column = top + drow, left + dcolumn
            if grid[row][column] != 0:
                raise RuntimeError("constructive placement overlap")
            grid[row][column] = color
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for drow, dcolumn in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + drow, cc + dcolumn
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            columns = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "bbox": (min(rows), min(columns), max(rows), max(columns)),
                }
            )
    return sorted(result, key=lambda item: (item["bbox"][0], item["bbox"][1]))


def _bbox_center(component: dict[str, Any]) -> tuple[int, int]:
    r1, c1, r2, c2 = component["bbox"]
    return (r1 + r2) // 2, (c1 + c2) // 2


def _nearest_centroid(component: dict[str, Any]) -> tuple[int, int]:
    cells = component["cells"]
    count = len(cells)
    return (
        (2 * sum(row for row, _ in cells) + count) // (2 * count),
        (2 * sum(column for _, column in cells) + count) // (2 * count),
    )


def _upper_center(component: dict[str, Any]) -> tuple[int, int]:
    r1, c1, r2, c2 = component["bbox"]
    return (r1 + r2 + 1) // 2, (c1 + c2 + 1) // 2


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject structural impostors while accepting canonical and generated inputs."""
    del difficulty, meta
    errors = _basic_grid_errors(grid)
    if errors:
        return errors
    height, width = len(grid), len(grid[0])
    if not (8 <= height <= 14 and 10 <= width <= 16):
        errors.append(f"grid shape {height}x{width} outside 8..14 by 10..16")
    components = _components(grid)
    if not 3 <= len(components) <= 4:
        errors.append(f"expected 3..4 objects, found {len(components)}")
    distinct = len({component["color"] for component in components})
    if not 2 <= distinct <= 3:
        errors.append(f"expected 2..3 foreground colors, found {distinct}")
    centers: list[tuple[int, int]] = []
    for index, component in enumerate(components):
        cells = component["cells"]
        r1, c1, r2, c2 = component["bbox"]
        bbox_shape = (r2 - r1 + 1, c2 - c1 + 1)
        if not 5 <= len(cells) <= 6:
            errors.append(f"object {index} has {len(cells)} cells, expected 5..6")
        if bbox_shape not in {(3, 3), (2, 4)}:
            errors.append(f"object {index} bbox {bbox_shape}, expected 3x3 or 2x4")
        centers.append(_bbox_center(component))
    if len(set(centers)) != len(centers):
        errors.append("two objects share the same bbox-center output cell")
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0:
                continue
            for drow, dcolumn in ((1, 0), (0, 1)):
                nr, nc = row + drow, column + dcolumn
                if 0 <= nr < height and 0 <= nc < width:
                    neighbor = grid[nr][nc]
                    if neighbor != 0 and neighbor != color:
                        errors.append(
                            f"different-color objects 4-touch at ({row},{column}) and ({nr},{nc})"
                        )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover each public exact axis from a generated grid."""
    components = _components(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_blobs": len(components),
        "n_distinct_colors": len({component["color"] for component in components}),
    }


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical 3-object, 3x3-bbox input manifold."""
    reasons = self_check(grid)
    if reasons:
        return reasons
    profile = (len(grid), len(grid[0]))
    if profile not in set(_CANONICAL_DIMS):
        reasons.append(f"grid dimensions {profile} are outside canonical profiles")
    components = _components(grid)
    if len(components) != 3:
        reasons.append(f"canonical inputs contain 3 objects, found {len(components)}")
    if len({component["color"] for component in components}) != 3:
        reasons.append("canonical inputs use a distinct color for every object")
    for index, component in enumerate(components):
        r1, c1, r2, c2 = component["bbox"]
        if (r2 - r1 + 1, c2 - c1 + 1) != (3, 3):
            reasons.append(f"canonical object {index} does not span a 3x3 bbox")
        if len(component["cells"]) not in {5, 6}:
            reasons.append(f"canonical object {index} does not contain 5 or 6 cells")
    return reasons


def _blank_like(grid):
    return [[0 for _ in row] for row in grid]


def rule_mirror(grid):
    """Independent Python mirror of the pinned Racket object/bbox rule."""
    output = _blank_like(grid)
    for component in _components(grid):
        row, column = _bbox_center(component)
        output[row][column] = component["color"]
    return output


def _one_center_per_color(grid):
    output = _blank_like(grid)
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        cells = [
            (row, column)
            for row, values in enumerate(grid)
            for column, value in enumerate(values)
            if value == color
        ]
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        output[(min(rows) + max(rows)) // 2][(min(columns) + max(columns)) // 2] = color
    return output


def _nearest_cell_centroid(grid):
    output = _blank_like(grid)
    for component in _components(grid):
        row, column = _nearest_centroid(component)
        output[row][column] = component["color"]
    return output


def _upper_bbox_midpoint(grid):
    output = _blank_like(grid)
    for component in _components(grid):
        row, column = _upper_center(component)
        output[row][column] = component["color"]
    return output


def _has_repeated_color_objects(grid) -> bool:
    counts = Counter(component["color"] for component in _components(grid))
    return any(count > 1 for count in counts.values())


def _centroid_differs(grid) -> bool:
    return any(
        _nearest_centroid(component) != _bbox_center(component)
        for component in _components(grid)
    )


def _floor_midpoint_matters(grid) -> bool:
    return any(
        _upper_center(component) != _bbox_center(component)
        for component in _components(grid)
    )


SEMANTIC_RIVALS = {
    "one_center_per_color": _one_center_per_color,
    "nearest_cell_centroid": _nearest_cell_centroid,
    "upper_bbox_midpoint": _upper_bbox_midpoint,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "repeated_color_objects": _has_repeated_color_objects,
    "centroid_differs": _centroid_differs,
    "floor_midpoint_matters": _floor_midpoint_matters,
}
WITNESS_RIVALS = {
    "repeated_color_objects": ("one_center_per_color",),
    "centroid_differs": ("nearest_cell_centroid",),
    "floor_midpoint_matters": ("upper_bbox_midpoint",),
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report declared shortcut ambiguity for one labeled lesson."""
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(deepcopy(pair["input"]))
        except Exception as exc:  # pragma: no cover - defensive contract report
            reasons.append(f"demo {index} is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the bbox-center rule")
    try:
        query_answer = rule_mirror(deepcopy(query["input"]))
    except Exception as exc:  # pragma: no cover - defensive contract report
        reasons.append(f"query is invalid: {type(exc).__name__}: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the bbox-center rule")
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(deepcopy(pair["input"])) == pair.get("output") for pair in demos
        )
        if survives and rival(deepcopy(query["input"])) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
