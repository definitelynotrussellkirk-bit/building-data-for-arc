"""Generator for arc_additional_puzzles_21_set2:M12.

For every 4-connected magenta (6) object, compute its tight bounding box and
paint that rectangle's perimeter red (2).  Magenta cells strictly inside the
box survive, zero cells strictly inside the box stay zero, and all other cells
are unchanged.
"""
from __future__ import annotations

from itertools import product
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "74d1cf8c8502"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "a17667e8f90e"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A zero-background grid contains two to four separated 4-connected "
    "magenta (6) objects. For each object independently, paint every cell on "
    "the perimeter of its tight bounding box red (2). Existing magenta on "
    "that perimeter is overwritten; cells strictly inside each box and all "
    "cells outside the boxes are preserved."
)

INVARIANTS = [
    "the input palette is exactly background 0 plus magenta 6",
    "there are 2..4 four-connected magenta objects",
    "every object has a 2..4 by 2..4 non-trivial tight bounding box",
    "object bounding boxes have at least a one-cell moat",
    "ordinary draws include both a thin object and a thick object",
    "ordinary draws require adding red to absent border cells and preserve at least one interior magenta cell",
]

# Every caller-facing axis is exact and recoverable from the returned grid.
# All boundary combinations are feasible on the four-zone layout.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile schedule anchored to canonical heights",
        "valid": "10..16",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile schedule anchored to canonical widths",
        "valid": "12..18",
    },
    "n_blobs": {
        "type": "int",
        "default": "four-profile schedule",
        "valid": "2..4",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[tuple[str, ...], ...] = ()

SCHEDULE_PROFILES = (0, 1, 2, 3)
_BAND_PROFILES = {
    "easy": (
        (10, 12, 2),
        (11, 13, 2),
        (12, 14, 3),
        (10, 12, 4),
    ),
    "medium": (
        (10, 12, 2),
        (11, 13, 3),
        (12, 14, 4),
        (14, 16, 3),
    ),
    "hard": (
        (10, 12, 3),
        (11, 13, 4),
        (12, 14, 4),
        (16, 18, 4),
    ),
}

# The first two families in every profile jointly guarantee the decisive
# teaching controls even when n_blobs is explicitly overridden to its minimum:
# one thick object with an interior magenta cell, and one thin/sparse object
# whose bbox perimeter contains zero cells that must become red.
_TEMPLATE_CELLS = {
    "plus": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "thin_v": ((0, 0), (0, 1), (1, 1), (2, 0), (2, 1)),
    "thin_h": ((0, 0), (0, 1), (0, 2), (1, 1)),
    "zigzag": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
    "solid": tuple(product(range(3), range(3))),
    "hook": ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0), (2, 1)),
    "ring": (
        (0, 0), (0, 1), (0, 2),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 2),
    ),
}
_PROFILE_TEMPLATES = (
    ("plus", "thin_v", "ring", "zigzag"),
    ("zigzag", "thin_h", "plus", "ring"),
    ("solid", "thin_v", "hook", "plus"),
    ("plus", "thin_h", "solid", "hook"),
)
_ZONE_ORDERS = (
    (0, 3, 1, 2),
    (1, 2, 0, 3),
    (0, 1, 3, 2),
    (2, 3, 0, 1),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Expose the four-step curriculum schedule to the semantic gate."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _scheduled_int(ctx, name: str, lo: int, hi: int, default: int) -> int:
    """Record a scheduled ordinary value while preserving exact overrides."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _shape_size(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(cells)
    return (
        max(r for r, _ in cells) + 1,
        max(c for _, c in cells) + 1,
    )


def _shape_variants(name: str) -> tuple[tuple[tuple[int, int], ...], ...]:
    """D4 variants that fit the minimum 3x4 quadrant interior."""
    base = _TEMPLATE_CELLS[name]
    variants = set()
    transforms = (
        lambda r, c: (r, c),
        lambda r, c: (-r, c),
        lambda r, c: (r, -c),
        lambda r, c: (-r, -c),
        lambda r, c: (c, r),
        lambda r, c: (-c, r),
        lambda r, c: (c, -r),
        lambda r, c: (-c, -r),
    )
    for transform in transforms:
        variant = _normalize_cells(transform(r, c) for r, c in base)
        shape_h, shape_w = _shape_size(variant)
        if 2 <= shape_h <= 3 and 2 <= shape_w <= 4:
            variants.add(variant)
    return tuple(sorted(variants))


_TEMPLATE_VARIANTS = {
    name: _shape_variants(name)
    for name in _TEMPLATE_CELLS
}


def _quadrant_zones(height: int, width: int) -> tuple[tuple[int, int, int, int], ...]:
    """Four half-open zones, each with a guaranteed 3x4 inset interior."""
    split_r = height // 2
    split_c = width // 2
    zones = (
        (0, split_r, 0, split_c),
        (0, split_r, split_c, width),
        (split_r, height, 0, split_c),
        (split_r, height, split_c, width),
    )
    for r0, r1, c0, c1 in zones:
        if r1 - r0 < 5 or c1 - c0 < 6:
            raise ValueError(
                f"grid {height}x{width} is too small for four separated zones"
            )
    return zones


def _place_shape(
    grid: list[list[int]],
    zone: tuple[int, int, int, int],
    cells: tuple[tuple[int, int], ...],
    rng,
) -> None:
    r0, r1, c0, c1 = zone
    shape_h, shape_w = _shape_size(cells)
    inner_r0, inner_r1 = r0 + 1, r1 - 1
    inner_c0, inner_c1 = c0 + 1, c1 - 1
    room_h = inner_r1 - inner_r0
    room_w = inner_c1 - inner_c0
    if shape_h > room_h or shape_w > room_w:
        raise ValueError(
            f"shape {shape_h}x{shape_w} does not fit zone interior "
            f"{room_h}x{room_w}"
        )
    top = inner_r0 + rng.randint(0, room_h - shape_h)
    left = inner_c0 + rng.randint(0, room_w - shape_w)
    for dr, dc in cells:
        grid[top + dr][left + dc] = 6


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int):
                return ["cells must be literal ARC integers"]
            if not 0 <= value <= 9:
                return ["cell values must lie in 0..9"]
    return []


def _six_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != 6 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                cr, cc = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (cr + dr, cc + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == 6
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            components.append(sorted(cells))
    return components


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_border(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if row in (r1, r2) or col in (c1, c2)
    }


def _boxes_have_moat(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
) -> bool:
    ar1, ac1, ar2, ac2 = first
    br1, bc1, br2, bc2 = second
    return (
        ar2 < br1 - 1
        or br2 < ar1 - 1
        or ac2 < bc1 - 1
        or bc2 < ac1 - 1
    )


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "components": []}

    height = len(grid)
    width = len(grid[0])
    if not 10 <= height <= 16:
        errors.append(f"grid height must be in 10..16, found {height}")
    if not 12 <= width <= 18:
        errors.append(f"grid width must be in 12..18, found {width}")

    palette = {value for row in grid for value in row}
    if not palette <= {0, 6}:
        errors.append(f"input palette must be a subset of {{0, 6}}, found {sorted(palette)}")
    if 6 not in palette:
        errors.append("input must contain magenta (6) objects")

    components = _six_components(grid)
    if not 2 <= len(components) <= 4:
        errors.append(f"expected 2..4 magenta objects, found {len(components)}")

    descriptions: list[dict[str, Any]] = []
    for index, cells in enumerate(components):
        box = _bbox(cells)
        r1, c1, r2, c2 = box
        box_h = r2 - r1 + 1
        box_w = c2 - c1 + 1
        if not 2 <= box_h <= 4 or not 2 <= box_w <= 4:
            errors.append(
                f"object {index} bbox must be 2..4 by 2..4, found {box_h}x{box_w}"
            )
        if not 3 <= len(cells) <= 12:
            errors.append(
                f"object {index} must contain 3..12 magenta cells, found {len(cells)}"
            )
        cell_set = set(cells)
        border = _bbox_border(box)
        interior = {
            (row, col)
            for row in range(r1 + 1, r2)
            for col in range(c1 + 1, c2)
        }
        descriptions.append(
            {
                "cells": cell_set,
                "bbox": box,
                "bbox_h": box_h,
                "bbox_w": box_w,
                "border": border,
                "missing_border": border - cell_set,
                "border_magenta": border & cell_set,
                "interior_magenta": interior & cell_set,
                "interior_zero": interior - cell_set,
            }
        )

    for left_index, left in enumerate(descriptions):
        for right in descriptions[left_index + 1:]:
            if not _boxes_have_moat(left["bbox"], right["bbox"]):
                errors.append("object bounding boxes must have at least a one-cell moat")
                break

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "components": descriptions,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid: Any) -> dict[str, int]:
    """Recover every exact axis from a lawful returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_blobs": len(analysis["components"]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed distribution inputs while accepting all canonical inputs."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The generated teaching grammar is a strict subset of the task manifold."""
    return self_check(grid)


def _paint_border(
    output: list[list[int]],
    box: tuple[int, int, int, int],
    *,
    only_if: Callable[[int, int], bool] | None = None,
) -> None:
    for row, col in _bbox_border(box):
        if only_if is None or only_if(row, col):
            output[row][col] = 2


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for cells in _six_components(grid):
        _paint_border(output, _bbox(cells))
    return output


def _rival_fill_bbox(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for cells in _six_components(grid):
        r1, c1, r2, c2 = _bbox(cells)
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                output[row][col] = 2
    return output


def _rival_existing_border_only(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for cells in _six_components(grid):
        cell_set = set(cells)
        _paint_border(
            output,
            _bbox(cells),
            only_if=lambda row, col, cell_set=cell_set: (row, col) in cell_set,
        )
    return output


def _rival_zero_border_only(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    for cells in _six_components(grid):
        _paint_border(
            output,
            _bbox(cells),
            only_if=lambda row, col, output=output: output[row][col] == 0,
        )
    return output


def _rival_global_bbox(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    all_cells = [cell for cells in _six_components(grid) for cell in cells]
    if all_cells:
        _paint_border(output, _bbox(all_cells))
    return output


def _rival_largest_only(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    components = _six_components(grid)
    if components:
        chosen = max(components, key=lambda cells: (len(cells), cells))
        _paint_border(output, _bbox(chosen))
    return output


def _rival_fixed_3x3(grid: list[list[int]]) -> list[list[int]]:
    output = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])
    for cells in _six_components(grid):
        r1, c1, _, _ = _bbox(cells)
        fixed = (r1, c1, min(r1 + 2, height - 1), min(c1 + 2, width - 1))
        _paint_border(output, fixed)
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fill_each_bbox": _rival_fill_bbox,
    "recolor_existing_bbox_border_only": _rival_existing_border_only,
    "paint_only_zero_bbox_border_cells": _rival_zero_border_only,
    "outline_one_global_bbox": _rival_global_bbox,
    "outline_largest_object_only": _rival_largest_only,
    "assume_every_bbox_is_3x3": _rival_fixed_3x3,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _valid_analysis(grid: Any) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return analysis if not analysis["errors"] else None


def _multiple_components(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(analysis and len(analysis["components"]) >= 2)


def _interior_magenta_survives(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and any(component["interior_magenta"] for component in analysis["components"])
    )


def _new_border_cells_required(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and any(component["missing_border"] for component in analysis["components"])
    )


def _border_magenta_recolored(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    return bool(
        analysis
        and all(component["border_magenta"] for component in analysis["components"])
    )


def _thin_and_thick_components(grid: Any) -> bool:
    analysis = _valid_analysis(grid)
    if not analysis:
        return False
    components = analysis["components"]
    thin = any(
        component["bbox_h"] == 2 or component["bbox_w"] == 2
        for component in components
    )
    thick = any(
        component["bbox_h"] >= 3 and component["bbox_w"] >= 3
        for component in components
    )
    return thin and thick


SEMANTIC_WITNESSES = {
    "multiple_components_are_processed_independently": _multiple_components,
    "interior_magenta_survives_bbox_outline": _interior_magenta_survives,
    "absent_bbox_border_cells_become_red": _new_border_cells_required,
    "magenta_on_bbox_border_is_overwritten": _border_magenta_recolored,
    "thin_and_thick_bbox_sizes_coexist": _thin_and_thick_components,
}
WITNESS_RIVALS = {
    "multiple_components_are_processed_independently": [
        "outline_one_global_bbox",
        "outline_largest_object_only",
    ],
    "interior_magenta_survives_bbox_outline": ["fill_each_bbox"],
    "absent_bbox_border_cells_become_red": [
        "recolor_existing_bbox_border_only"
    ],
    "magenta_on_bbox_border_is_overwritten": [
        "paint_only_zero_bbox_border_cells"
    ],
    "thin_and_thick_bbox_sizes_coexist": ["assume_every_bbox_is_3x3"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every lesson to refute all named shortcut transformations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the teaching grammar")

    valid_demos = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        if self_check(demo["input"]):
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output is not the per-object bbox outline rule")
            continue
        valid_demos.append(demo)

    if len(valid_demos) != len(demos):
        return reasons

    for name, predicate in SEMANTIC_WITNESSES.items():
        if not any(predicate(demo["input"]) for demo in valid_demos):
            reasons.append(f"demonstrations never show witness: {name}")

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"named competitor survives every demonstration: {name}")
    return reasons


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic input grid; the canonical Racket rule owns output."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in _BAND_PROFILES else "medium"
    profile = schedule_profile(seed, sample_index, difficulty)
    default_h, default_w, default_n = _BAND_PROFILES[band][profile]
    height = _scheduled_int(ctx, "grid_h", 10, 16, default_h)
    width = _scheduled_int(ctx, "grid_w", 12, 18, default_w)
    n_blobs = _scheduled_int(ctx, "n_blobs", 2, 4, default_n)

    grid = full_grid(height, width, 0)
    zones = _quadrant_zones(height, width)
    rng = ctx.draw_rng(f"layout:profile={profile}:band={band}")
    zone_order = list(_ZONE_ORDERS[profile])
    # Rotating all four corners by a deterministic amount varies absolute
    # positions without changing the branch schedule or override observability.
    rotation = rng.randrange(len(zone_order))
    zone_order = zone_order[rotation:] + zone_order[:rotation]

    template_names = _PROFILE_TEMPLATES[profile]
    for index in range(n_blobs):
        name = template_names[index]
        variants = _TEMPLATE_VARIANTS[name]
        cells = variants[rng.randrange(len(variants))]
        _place_shape(grid, zones[zone_order[index]], cells, rng)

    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": dict(overrides)},
    )
    if errors:
        raise ValueError("constructed invalid instance: " + "; ".join(errors))

    # These are curriculum obligations, not authority-grammar restrictions.
    curriculum_checks = {
        "interior magenta witness": _interior_magenta_survives(grid),
        "new border-cell witness": _new_border_cells_required(grid),
        "thin/thick contrast": _thin_and_thick_components(grid),
    }
    missing = [name for name, present in curriculum_checks.items() if not present]
    if missing:
        raise ValueError("constructed rule-hiding instance: " + ", ".join(missing))
    return [row[:] for row in grid]
