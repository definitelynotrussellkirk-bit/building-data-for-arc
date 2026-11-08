"""Generator for arc_puzzle_bank_21_set3:S3_M5 — reduce objects to bbox centers.

Each input contains two to four separated, differently colored 4-connected
objects.  The canonical rule replaces every object by one same-colored cell at
``(floor((r_min+r_max)/2), floor((c_min+c_max)/2))`` on an otherwise-zero grid.

The sequential sample-index schedule deliberately alternates objects whose
bounding-box center is already occupied with objects whose center is blank.
Thus a normal three-demonstration lesson distinguishes the intended bbox-center
construction from shortcuts such as retaining a pre-existing middle cell.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6b9f5bbac608"
VERSION = "2.0.0"  # exact axes, scheduled disambiguation, structural self_check
TASK_ID = "6b9f5bbac608"
RULE_HASH = "606e0d940e28"  # sha256[:12] of whitespace-normalized canonical rule

SUMMARY = (
    "Two to four separated, distinct-color 4-connected objects are replaced "
    "by one same-colored cell at each object's floor-rounded bounding-box "
    "center. Generated lessons vary grid size, object count, palette family, "
    "object size, orientation, placement, and whether the center is initially "
    "occupied. Every three sequential demonstrations include occupied, vacant, "
    "and mixed center profiles."
)

INVARIANTS = [
    "background is 0 and grid dimensions are 8..14 by 8..14",
    "there are 2..4 4-connected objects, each with a unique color",
    "every object is a supported rectilinear shape of size 3..9",
    "object bounding-box centers are pairwise distinct",
    "three sequential sample indices cover occupied, vacant, and mixed center profiles",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted 8..14",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted 8..14",
        "valid": "8..14",
    },
    "n_blobs": {
        "type": "int",
        "default": "difficulty-weighted 2..4",
        "valid": "2..4",
    },
    "palette_kind": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "warm|cool|mixed",
    },
    "center_profile": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "occupied|vacant|mixed",
    },
    "size_profile": {
        "type": "str",
        "default": "sample-index schedule",
        "valid": "small|large|mixed",
    },
}

_WARM = (1, 2, 4, 7, 9)
_COOL = (3, 5, 6, 8)
_PALETTE_KINDS = ("warm", "cool", "mixed")
_CENTER_PROFILES = ("occupied", "vacant", "mixed")
_SIZE_PROFILES = ("small", "large", "mixed")
_DIFFICULTIES = (None, "easy", "medium", "hard")

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _transform(cells, rotation: int, reflect: bool):
    points = list(cells)
    for _ in range(rotation):
        points = [(c, -r) for r, c in points]
    if reflect:
        points = [(r, -c) for r, c in points]
    return _normalize(points)


def _variants(cells) -> set[tuple[tuple[int, int], ...]]:
    return {
        _transform(cells, rotation, reflect)
        for rotation in range(4)
        for reflect in (False, True)
    }


def _local_center(cells) -> tuple[int, int]:
    rows = [r for r, _ in cells]
    columns = [c for _, c in cells]
    return ((min(rows) + max(rows)) // 2, (min(columns) + max(columns)) // 2)


# Generated shapes fit in 3x3 slots.  The canonical task additionally uses
# length-five lines, admitted by self_check but not sampled as a fixed template.
_GENERATED_BASE_SHAPES = (
    # Center occupied, small.
    ((0, 0), (0, 1), (0, 2)),
    ((0, 0), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    # Center occupied, large.
    tuple((r, c) for r in range(2) for c in range(3)),
    tuple((r, c) for r in range(3) for c in range(3)),
    ((0, 0), (1, 0), (2, 0), (1, 1), (0, 2), (1, 2), (2, 2)),
    # Center vacant, small.
    ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)),
    ((0, 0), (0, 1), (1, 1), (2, 1)),
    # Center vacant, large.
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2)),
)
_CANONICAL_EXTRA_SHAPES = (
    tuple((0, column) for column in range(5)),
)


def _build_shape_catalog():
    generated: dict[tuple[bool, str], list[tuple[tuple[int, int], ...]]] = {
        (occupied, size): []
        for occupied in (False, True)
        for size in ("small", "large")
    }
    allowed: set[tuple[tuple[int, int], ...]] = set()
    for base in _GENERATED_BASE_SHAPES:
        for shape in _variants(base):
            size = "small" if len(shape) <= 5 else "large"
            occupied = _local_center(shape) in shape
            generated[(occupied, size)].append(shape)
            allowed.add(shape)
    for base in _CANONICAL_EXTRA_SHAPES:
        allowed.update(_variants(base))
    for key, values in generated.items():
        generated[key] = sorted(set(values))
        if not generated[key]:
            raise RuntimeError(f"empty shape category {key}")
    return generated, frozenset(allowed)


_GENERATED_SHAPES, _ALLOWED_SHAPES = _build_shape_catalog()


def _grid_error(grid) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a non-empty list"
    if isinstance(grid[0], str):
        width = len(grid[0])
        if width == 0 or any(not isinstance(row, str) or len(row) != width for row in grid):
            return "grid must be rectangular"
        if any(not value.isdigit() for row in grid for value in row):
            return "string rows must contain digits only"
        return None
    if not isinstance(grid[0], list) or not grid[0]:
        return "grid rows must be non-empty lists"
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return "grid must be rectangular"
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid colors must be integers in 0..9"
    return None


def _as_int_grid(grid) -> list[list[int]]:
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def _components(grid: list[list[int]]):
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = []
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            queue = deque([(row, column)])
            seen.add((row, column))
            cells = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                for dr, dc in _CARDINAL:
                    rr, cc = current[0] + dr, current[1] + dc
                    if (
                        0 <= rr < height
                        and 0 <= cc < width
                        and (rr, cc) not in seen
                        and grid[rr][cc] == color
                    ):
                        seen.add((rr, cc))
                        queue.append((rr, cc))
            components.append({"color": color, "cells": tuple(sorted(cells))})
    return components


def _analyze_grid(grid):
    result: dict = {"errors": []}
    error = _grid_error(grid)
    if error:
        result["errors"].append(error)
        return result
    grid = _as_int_grid(grid)
    height, width = len(grid), len(grid[0])
    result.update({"grid": grid, "grid_h": height, "grid_w": width})
    if not (8 <= height <= 14 and 8 <= width <= 14):
        result["errors"].append("grid dimensions must each be in 8..14")

    components = _components(grid)
    result["components"] = components
    if not 2 <= len(components) <= 4:
        result["errors"].append("scene must contain 2..4 nonzero objects")

    colors = [component["color"] for component in components]
    if len(set(colors)) != len(colors):
        result["errors"].append("each color must form exactly one object")

    centers = []
    center_occupied = []
    size_classes = []
    for index, component in enumerate(components):
        cells = component["cells"]
        normalized = _normalize(cells)
        if normalized not in _ALLOWED_SHAPES:
            result["errors"].append(
                f"object {index} has an unsupported shape of size {len(cells)}"
            )
        rows = [row for row, _ in cells]
        columns = [column for _, column in cells]
        center = ((min(rows) + max(rows)) // 2, (min(columns) + max(columns)) // 2)
        centers.append(center)
        center_occupied.append(center in cells)
        size_classes.append("small" if len(cells) <= 5 else "large")

    if len(set(centers)) != len(centers):
        result["errors"].append("object bounding-box centers must be distinct")


    if colors:
        color_set = set(colors)
        if color_set <= set(_WARM):
            palette_kind = "warm"
        elif color_set <= set(_COOL):
            palette_kind = "cool"
        else:
            palette_kind = "mixed"
    else:
        palette_kind = None

    if center_occupied:
        if all(center_occupied):
            center_profile = "occupied"
        elif not any(center_occupied):
            center_profile = "vacant"
        else:
            center_profile = "mixed"
    else:
        center_profile = None

    if size_classes:
        if all(size == "small" for size in size_classes):
            size_profile = "small"
        elif all(size == "large" for size in size_classes):
            size_profile = "large"
        else:
            size_profile = "mixed"
    else:
        size_profile = None

    result.update(
        {
            "n_blobs": len(components),
            "colors": tuple(sorted(colors)),
            "centers": tuple(centers),
            "center_occupied": tuple(center_occupied),
            "sizes": tuple(len(component["cells"]) for component in components),
            "palette_kind": palette_kind,
            "center_profile": center_profile,
            "size_profile": size_profile,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding scenes; accept all canonical inputs."""
    return list(_analyze_grid(grid)["errors"])


def observe_overrides(grid) -> dict[str, int | str]:
    """Recover every exact semantic axis from a returned grid."""
    analysis = _analyze_grid(grid)
    if analysis["errors"]:
        raise ValueError("cannot observe overrides on invalid grid: " + "; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_blobs": analysis["n_blobs"],
        "palette_kind": analysis["palette_kind"],
        "center_profile": analysis["center_profile"],
        "size_profile": analysis["size_profile"],
    }


def _draw_int(ctx, label: str, default_bounds: tuple[int, int], full_bounds: tuple[int, int]):
    bounds = full_bounds if ctx.overrides.get(label) is not None else default_bounds
    return ctx.draw_int(label, *bounds)


def _scheduled_choice(ctx, label: str, options: tuple[str, ...], offset: int = 0):
    if ctx.overrides.get(label) is not None:
        return ctx.draw_choice(label, options)
    scheduled = options[(ctx.sample_index + offset) % len(options)]
    return ctx.draw_choice(label, (scheduled,))


def _band_bounds(difficulty):
    if difficulty == "easy":
        return {"grid_h": (8, 10), "grid_w": (8, 10), "n_blobs": (2, 3)}
    if difficulty == "hard":
        return {"grid_h": (11, 14), "grid_w": (11, 14), "n_blobs": (3, 4)}
    return {"grid_h": (9, 12), "grid_w": (9, 12), "n_blobs": (2, 4)}


def _profile_flags(profile: str, count: int, rng, *, true_name: str):
    if profile == true_name:
        values = [True] * count
    elif profile in {"vacant", "small"}:
        values = [False] * count
    elif profile == "mixed":
        values = [True, False]
        values.extend(rng.choice((True, False)) for _ in range(count - 2))
        rng.shuffle(values)
    else:
        raise ValueError(f"unknown profile {profile!r}")
    return values


def _choose_palette(kind: str, count: int, rng) -> list[int]:
    if kind == "warm":
        return rng.sample(list(_WARM), count)
    if kind == "cool":
        return rng.sample(list(_COOL), count)
    if kind == "mixed":
        warm_count = rng.randint(1, count - 1)
        cool_count = count - warm_count
        colors = rng.sample(list(_WARM), warm_count) + rng.sample(list(_COOL), cool_count)
        rng.shuffle(colors)
        return colors
    raise ValueError(f"unknown palette_kind {kind!r}")


def _quadrant_origins(height: int, width: int, shapes, rng):
    """Place up to four <=3x3 shapes in separated quadrants."""
    row_regions = ((0, height // 2 - 1), ((height + 1) // 2 + 1, height))
    col_regions = ((0, width // 2 - 1), ((width + 1) // 2 + 1, width))
    slots = [(row_band, col_band) for row_band in range(2) for col_band in range(2)]
    rng.shuffle(slots)
    origins = []
    for shape, (row_band, col_band) in zip(shapes, slots):
        shape_h = max(row for row, _ in shape) + 1
        shape_w = max(column for _, column in shape) + 1
        row_start, row_stop = row_regions[row_band]
        col_start, col_stop = col_regions[col_band]
        max_row = row_stop - shape_h
        max_col = col_stop - shape_w
        if max_row < row_start or max_col < col_start:
            raise ValueError(
                f"grid {height}x{width} cannot fit shape {shape_h}x{shape_w} in separated slots"
            )
        origins.append((rng.randint(row_start, max_row), rng.randint(col_start, max_col)))
    return origins


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in _DIFFICULTIES:
        raise ValueError("difficulty must be easy, medium, hard, or None")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    bounds = _band_bounds(difficulty)
    height = _draw_int(ctx, "grid_h", bounds["grid_h"], (8, 14))
    width = _draw_int(ctx, "grid_w", bounds["grid_w"], (8, 14))
    count = _draw_int(ctx, "n_blobs", bounds["n_blobs"], (2, 4))
    palette_kind = _scheduled_choice(ctx, "palette_kind", _PALETTE_KINDS, offset=2)
    center_profile = _scheduled_choice(ctx, "center_profile", _CENTER_PROFILES, offset=0)
    size_profile = _scheduled_choice(ctx, "size_profile", _SIZE_PROFILES, offset=1)

    assignment_rng = ctx.draw_rng("profile_assignment")
    occupied_flags = _profile_flags(
        center_profile, count, assignment_rng, true_name="occupied"
    )
    large_flags = _profile_flags(size_profile, count, assignment_rng, true_name="large")

    shapes = []
    for index, (occupied, large) in enumerate(zip(occupied_flags, large_flags)):
        candidates = _GENERATED_SHAPES[(occupied, "large" if large else "small")]
        shapes.append(ctx.draw_rng(f"shape_{index}").choice(candidates))

    colors = _choose_palette(palette_kind, count, ctx.draw_rng("palette"))
    origins = _quadrant_origins(height, width, shapes, ctx.draw_rng("layout"))
    grid = full_grid(height, width, 0)
    for shape, color, (origin_row, origin_column) in zip(shapes, colors, origins):
        for row, column in shape:
            grid[origin_row + row][origin_column + column] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal generator invariant failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_blobs": count,
        "palette_kind": palette_kind,
        "center_profile": center_profile,
        "size_profile": size_profile,
    }
    if observed != expected:
        raise RuntimeError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid
