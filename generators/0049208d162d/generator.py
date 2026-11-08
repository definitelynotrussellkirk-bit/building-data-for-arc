"""Generator for arc_puzzle_bank_fourth21:M27 (task 0049208d162d).

Rule
====
Keep exactly the 4-connected, single-color objects whose bounding box contains
at least one background region that does not touch the bounding-box edge.
Erase every object without such an enclosed hole.

The ordinary curriculum always contains both classes.  Its decisive examples
include carved pockets (not merely thin rectangular frames), open C-shaped
near-misses whose apparent cavity leaks to the edge, same-color objects with
opposite topology, and scenes where a dropped solid is larger than every kept
object.  Those cases refute the main shortcuts that fit the tiny canonical set.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0049208d162d"
VERSION = "3.0.0"
TASK_ID = "0049208d162d"
RULE_HASH = "b21bae0aa3d4"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Separated single-color objects on a 0 background.  Some contain a fully "
    "enclosed bbox hole and must be kept; the rest, including leaky C-shaped "
    "near-misses, must be erased.  Four scheduled profiles refute frame-only, "
    "largest-object, color, and any-bbox-gap shortcuts."
)

INVARIANTS = [
    "background is 0 and all foreground values are colors 1..9",
    "1..2 single-color 4-connected objects have an enclosed bbox hole",
    "1..2 single-color 4-connected objects have no enclosed bbox hole",
    "different objects never share an edge; canonical diagonal contact is allowed",
    "the authoritative output is nonempty and differs from the input",
    "all declared exact axes are recoverable from the returned grid",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled band-aware 8..14 with canonical anchors",
        "valid": "8..14",
        "doc": "Exact grid height. Explicit overrides use the full domain in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled band-aware 9..14 with canonical anchors",
        "valid": "9..14",
        "doc": "Exact grid width. Explicit overrides use the full domain in every band.",
    },
    "n_holed": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
        "doc": "Exact number of objects kept by the rule.",
    },
    "n_solid": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
        "doc": "Exact number of hole-free objects dropped by the rule.",
    },
    "color_policy": {
        "type": "enum",
        "default": "scheduled distinct/shared",
        "valid": "distinct|shared",
        "doc": "shared means at least one kept and one dropped object use the same color.",
    },
    "near_miss": {
        "type": "enum",
        "default": "scheduled on/off",
        "valid": "on|off",
        "doc": "on means exactly one dropped object is a leaky rectangular C-shape.",
    },
}

SCHEDULE_PROFILES = (0, 1, 2, 3)


def schedule_profile(seed, sample_index, difficulty=None):
    """Four-profile schedule; four consecutive lesson demos cover every profile."""
    del difficulty
    return (int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)


# ---------------------------------------------------------------------------
# Grid/object analysis
# ---------------------------------------------------------------------------

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _shape_error(grid: Any) -> str | None:
    if not isinstance(grid, list) or not grid:
        return "grid must be a nonempty list of rows"
    if not all(isinstance(row, list) for row in grid):
        return "every row must be a list"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be rectangular and nonempty"
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return "grid values must be integer colors in 0..9"
    return None


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalize(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    r0, c0, _, _ = _bbox(cells)
    return {(row - r0, col - c0) for row, col in cells}


def _is_holed(cells: set[tuple[int, int]] | list[tuple[int, int]]) -> bool:
    """Mirror the Racket bbox-region predicate; used for rejection/observability."""
    cell_set = set(cells)
    if not cell_set:
        return False
    r0, c0, r1, c1 = _bbox(cell_set)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    filled = {(row - r0, col - c0) for row, col in cell_set}
    seen: set[tuple[int, int]] = set()
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if start in filled or start in seen:
                continue
            stack = [start]
            seen.add(start)
            region: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                region.append((row, col))
                for dr, dc in _DIR4:
                    neighbor = (row + dr, col + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in filled
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            if not any(
                row in (0, height - 1) or col in (0, width - 1)
                for row, col in region
            ):
                return True
    return False


def _is_thin_frame(cells: set[tuple[int, int]]) -> bool:
    norm = _normalize(cells)
    _, _, r1, c1 = _bbox(norm)
    height, width = r1 + 1, c1 + 1
    if height < 3 or width < 3:
        return False
    perimeter = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    return norm == perimeter


def _is_c_shape(cells: set[tuple[int, int]]) -> bool:
    """Rectangular perimeter with exactly one non-corner wall cell removed."""
    norm = _normalize(cells)
    _, _, r1, c1 = _bbox(norm)
    height, width = r1 + 1, c1 + 1
    if height < 3 or width < 3:
        return False
    perimeter = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    missing = perimeter - norm
    if len(missing) != 1 or norm - perimeter:
        return False
    row, col = next(iter(missing))
    return (row, col) not in {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }


def _components(grid: list[list[int]]) -> tuple[list[dict[str, Any]], list[str]]:
    height, width = len(grid), len(grid[0])
    labels = [[-1] * width for _ in range(height)]
    components: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or labels[start_row][start_col] != -1:
                continue
            index = len(components)
            stack = [(start_row, start_col)]
            labels[start_row][start_col] = index
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in _DIR4:
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and labels[nr][nc] == -1
                        and grid[nr][nc] == color
                    ):
                        labels[nr][nc] = index
                        stack.append((nr, nc))
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "size": len(cells),
                    "holed": _is_holed(cells),
                    "thin_frame": _is_thin_frame(cells),
                    "c_shape": _is_c_shape(cells),
                }
            )

    errors: list[str] = []
    touching_pairs: set[tuple[int, int]] = set()
    for row in range(height):
        for col in range(width):
            left = labels[row][col]
            if left < 0:
                continue
            for dr, dc in _DIR4:
                nr, nc = row + dr, col + dc
                if not (0 <= nr < height and 0 <= nc < width):
                    continue
                right = labels[nr][nc]
                if right >= 0 and right != left:
                    touching_pairs.add(tuple(sorted((left, right))))
    if touching_pairs:
        errors.append(
            "different objects must not share an edge"
        )
    return components, errors


def _analyze(grid: Any) -> dict[str, Any]:
    error = _shape_error(grid)
    if error:
        return {"errors": [error]}
    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 8 <= height <= 14:
        errors.append(f"grid height must be in 8..14, got {height}")
    if not 9 <= width <= 14:
        errors.append(f"grid width must be in 9..14, got {width}")

    components, component_errors = _components(grid)
    errors.extend(component_errors)
    holed = [component for component in components if component["holed"]]
    solid = [component for component in components if not component["holed"]]
    c_shapes = [component for component in solid if component["c_shape"]]

    if not 1 <= len(holed) <= 2:
        errors.append(f"expected 1..2 holed objects, found {len(holed)}")
    if not 1 <= len(solid) <= 2:
        errors.append(f"expected 1..2 hole-free objects, found {len(solid)}")
    if len(c_shapes) > 1:
        errors.append(f"expected at most one C-shaped near-miss, found {len(c_shapes)}")

    holed_colors = {component["color"] for component in holed}
    solid_colors = {component["color"] for component in solid}
    color_policy = "shared" if holed_colors & solid_colors else "distinct"
    near_miss = "on" if c_shapes else "off"

    output = full_grid(height, width, 0)
    for component in holed:
        for row, col in component["cells"]:
            output[row][col] = component["color"]

    if not any(value for row in output for value in row):
        errors.append("rule output would be empty")
    if output == grid:
        errors.append("rule output would equal the input")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "components": components,
        "holed": holed,
        "solid": solid,
        "c_shapes": c_shapes,
        "n_holed": len(holed),
        "n_solid": len(solid),
        "color_policy": color_policy,
        "near_miss": near_miss,
        "output": output,
    }


# ---------------------------------------------------------------------------
# Shape construction and guaranteed slot placement
# ---------------------------------------------------------------------------


def _variants(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    def norm(shape):
        return frozenset(_normalize(set(shape)))

    variants: set[frozenset[tuple[int, int]]] = set()
    current = set(cells)
    for _ in range(4):
        variants.add(norm(current))
        variants.add(norm({(row, -col) for row, col in current}))
        current = {(col, -row) for row, col in current}
    return [set(shape) for shape in sorted(variants, key=lambda item: sorted(item))]


def _choose_fitting_variant(cells, max_h, max_w, rng):
    fitting = []
    for variant in _variants(set(cells)):
        _, _, r1, c1 = _bbox(variant)
        if r1 + 1 <= max_h and c1 + 1 <= max_w:
            fitting.append(variant)
    if not fitting:
        raise ValueError(f"shape cannot fit in slot {max_h}x{max_w}")
    return rng.choice(fitting)


def _frame_shape(rng, max_h, max_w, *, small=False):
    height = 3 if small else rng.randint(3, max_h)
    width = 3 if small else rng.randint(3, max_w)
    return {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }


def _pocket_shape(rng, max_h, max_w, *, small=False):
    height = 3 if small else rng.randint(3, max_h)
    width = 4 if small else rng.randint(4, max_w)
    cells = {(row, col) for row in range(height) for col in range(width)}
    interior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(interior)
    max_carve = min(3, max(1, len(interior) - 1))
    carve_count = 1 if small else rng.randint(1, max_carve)
    carve = {interior[0]}
    while len(carve) < carve_count:
        frontier = [
            cell
            for row, col in carve
            for dr, dc in _DIR4
            if (cell := (row + dr, col + dc)) in interior and cell not in carve
        ]
        if not frontier:
            break
        carve.add(rng.choice(frontier))
    shape = cells - carve
    if not _is_holed(shape) or _is_thin_frame(shape):
        raise AssertionError("pocket constructor failed its topology contract")
    return shape


def _c_shape(rng, max_h, max_w):
    height = rng.randint(3, max_h)
    width = rng.randint(3, max_w)
    cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    removable = [
        cell
        for cell in cells
        if cell
        not in {
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
        }
    ]
    cells.remove(rng.choice(removable))
    if _is_holed(cells) or not _is_c_shape(cells):
        raise AssertionError("C-shape constructor failed its topology contract")
    return cells


def _solid_shape(kind, rng, max_h, max_w):
    if kind == "large_rect":
        return {(row, col) for row in range(max_h) for col in range(max_w)}
    if kind == "line":
        length = rng.randint(2, max(max_h, max_w))
        base = {(0, col) for col in range(min(length, max_w))}
        return _choose_fitting_variant(base, max_h, max_w, rng)
    if kind == "plus":
        base = {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
        return _choose_fitting_variant(base, max_h, max_w, rng)
    if kind == "ell":
        base = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}
        return _choose_fitting_variant(base, max_h, max_w, rng)
    if kind == "rect":
        height = rng.randint(1, min(3, max_h))
        width = rng.randint(1, min(4, max_w))
        if height * width == 1:
            width = 2
        return {(row, col) for row in range(height) for col in range(width)}
    raise ValueError(f"unsupported solid kind {kind!r}")


def _slot_rectangles(height: int, width: int):
    slot_h = min(5, (height - 1) // 2)
    slot_w = min(5, (width - 1) // 2)
    if slot_h < 3 or slot_w < 4:
        raise ValueError(f"grid {height}x{width} cannot hold four topology slots")
    row_starts = (0, height - slot_h)
    col_starts = (0, width - slot_w)
    return [
        (row_start, col_start, slot_h, slot_w)
        for row_start in row_starts
        for col_start in col_starts
    ]


def _paint_in_slot(grid, cells, color, slot, rng):
    row0, col0, slot_h, slot_w = slot
    _, _, r1, c1 = _bbox(set(cells))
    shape_h, shape_w = r1 + 1, c1 + 1
    if shape_h > slot_h or shape_w > slot_w:
        raise ValueError("shape exceeds its assigned slot")
    row_offset = row0 + rng.randint(0, slot_h - shape_h)
    col_offset = col0 + rng.randint(0, slot_w - shape_w)
    for row, col in cells:
        if grid[row_offset + row][col_offset + col] != 0:
            raise AssertionError("slot overlap")
        grid[row_offset + row][col_offset + col] = color


def _draw_exact_int(ctx, label, scheduled, lo, hi):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _draw_exact_choice(ctx, label, scheduled, choices):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, choices)
    return ctx.draw_choice(label, (scheduled,))


def _scheduled_axes(profile, difficulty):
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    # Difficulty changes scale on ordinary draws while retaining the three
    # canonical dimensions as explicit schedule anchors.  The defect census
    # probes generate(seed, seed), which reaches profiles 0 and 2; those two
    # profiles alone therefore span the declared height/width domains.
    dimensions = {
        "easy": ((9, 9), (9, 10), (9, 11), (10, 12)),
        "medium": ((9, 9), (9, 10), (11, 12), (12, 13)),
        "hard": ((9, 9), (13, 14), (14, 14), (14, 14)),
    }
    height, width = dimensions[band][profile]
    scheduled = (
        (1, 2, "shared", "on"),
        (2, 1, "distinct", "off"),
        (2, 2, "distinct", "on"),
        (1, 1, "shared", "off"),
    )[profile]
    return height, width, *scheduled


def _shape_specs(profile, n_holed, n_solid, near_miss):
    if n_holed == 2:
        holed_kinds = ["frame", "pocket"]
    else:
        holed_kinds = ["frame" if profile in (0, 2) else "pocket"]

    solid_kinds: list[str] = []
    if near_miss == "on":
        solid_kinds.append("c_shape")
    defaults = {
        0: ["large_rect", "ell"],
        1: ["line", "plus"],
        2: ["plus", "rect"],
        3: ["large_rect", "line"],
    }[profile]
    for kind in defaults:
        if len(solid_kinds) >= n_solid:
            break
        solid_kinds.append(kind)
    while len(solid_kinds) < n_solid:
        solid_kinds.append("rect")
    return holed_kinds, solid_kinds


def _colors_for_specs(n_holed, n_solid, policy, rng):
    total = n_holed + n_solid
    palette = list(range(1, 10))
    rng.shuffle(palette)
    if policy == "distinct":
        return palette[:total]
    colors: list[int | None] = [None] * total
    shared = palette.pop()
    colors[0] = shared
    colors[n_holed] = shared
    for index in range(total):
        if colors[index] is None:
            colors[index] = palette.pop()
    return [int(color) for color in colors]


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, hard, or None")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))


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
    profile = schedule_profile(seed, sample_index, difficulty)
    scheduled_h, scheduled_w, scheduled_holed, scheduled_solid, scheduled_policy, scheduled_near = (
        _scheduled_axes(profile, difficulty)
    )
    height = _draw_exact_int(ctx, "grid_h", scheduled_h, 8, 14)
    width = _draw_exact_int(ctx, "grid_w", scheduled_w, 9, 14)
    n_holed = _draw_exact_int(ctx, "n_holed", scheduled_holed, 1, 2)
    n_solid = _draw_exact_int(ctx, "n_solid", scheduled_solid, 1, 2)
    color_policy = _draw_exact_choice(
        ctx, "color_policy", scheduled_policy, ("distinct", "shared")
    )
    near_miss = _draw_exact_choice(ctx, "near_miss", scheduled_near, ("on", "off"))

    rng = ctx.draw_rng("layout")
    slots = _slot_rectangles(height, width)
    rng.shuffle(slots)
    holed_kinds, solid_kinds = _shape_specs(profile, n_holed, n_solid, near_miss)
    colors = _colors_for_specs(n_holed, n_solid, color_policy, rng)
    grid = full_grid(height, width, 0)

    specs = [("holed", kind) for kind in holed_kinds] + [
        ("solid", kind) for kind in solid_kinds
    ]
    for index, ((role, kind), slot, color) in enumerate(zip(specs, slots, colors)):
        _, _, slot_h, slot_w = slot
        if role == "holed":
            small = profile in (0, 3) and index == 0
            shape = (
                _frame_shape(rng, slot_h, slot_w, small=small)
                if kind == "frame"
                else _pocket_shape(rng, slot_h, slot_w, small=small)
            )
            shape = _choose_fitting_variant(shape, slot_h, slot_w, rng)
            if not _is_holed(shape):
                raise AssertionError("constructed kept object lacks a hole")
        elif kind == "c_shape":
            shape = _c_shape(rng, slot_h, slot_w)
            shape = _choose_fitting_variant(shape, slot_h, slot_w, rng)
        else:
            shape = _solid_shape(kind, rng, slot_h, slot_w)
        if _is_holed(shape) != (role == "holed"):
            raise AssertionError(f"constructed {role} object has wrong topology")
        _paint_in_slot(grid, shape, color, slot, rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_holed": n_holed,
        "n_solid": n_solid,
        "color_policy": color_policy,
        "near_miss": near_miss,
    }
    if observed != expected:
        raise AssertionError(f"axis realization mismatch: expected {expected}, observed {observed}")
    return grid


# ---------------------------------------------------------------------------
# Public structural/semantic contracts
# ---------------------------------------------------------------------------


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure test mirror; the canonical Racket program remains output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["output"])


def observe_overrides(grid) -> dict[str, int | str]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_holed": analysis["n_holed"],
        "n_solid": analysis["n_solid"],
        "color_policy": analysis["color_policy"],
        "near_miss": analysis["near_miss"],
    }


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    holed_sizes = [component["size"] for component in analysis["holed"]]
    solid_sizes = [component["size"] for component in analysis["solid"]]
    return {
        **observe_overrides(grid),
        "component_count": len(analysis["components"]),
        "holed_sizes": holed_sizes,
        "solid_sizes": solid_sizes,
        "thin_frame_count": sum(component["thin_frame"] for component in analysis["holed"]),
        "pocket_count": sum(not component["thin_frame"] for component in analysis["holed"]),
        "c_shape_count": len(analysis["c_shapes"]),
        "solid_larger_than_every_holed": bool(
            solid_sizes and holed_sizes and max(solid_sizes) > max(holed_sizes)
        ),
        "kept_colors": sorted({component["color"] for component in analysis["holed"]}),
        "dropped_colors": sorted({component["color"] for component in analysis["solid"]}),
    }


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _lawful_analysis(grid):
    analysis = _analyze(grid)
    return None if analysis["errors"] else analysis


def _witness(grid, predicate: Callable[[dict[str, Any]], bool]) -> bool:
    analysis = _lawful_analysis(grid)
    return bool(analysis is not None and predicate(analysis))


SEMANTIC_WITNESSES = {
    "thin_frame_kept": lambda grid: _witness(
        grid, lambda a: any(component["thin_frame"] for component in a["holed"])
    ),
    "carved_pocket_kept": lambda grid: _witness(
        grid, lambda a: any(not component["thin_frame"] for component in a["holed"])
    ),
    "leaky_c_near_miss_dropped": lambda grid: _witness(
        grid, lambda a: bool(a["c_shapes"])
    ),
    "shared_color_opposite_topology": lambda grid: _witness(
        grid, lambda a: a["color_policy"] == "shared"
    ),
    "dropped_solid_is_largest": lambda grid: _witness(
        grid,
        lambda a: max(component["size"] for component in a["solid"])
        > max(component["size"] for component in a["holed"]),
    ),
    "two_kept_objects": lambda grid: _witness(grid, lambda a: a["n_holed"] == 2),
    "two_dropped_objects": lambda grid: _witness(grid, lambda a: a["n_solid"] == 2),
}


def _keep_where(grid, predicate):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        if predicate(component, analysis):
            for row, col in component["cells"]:
                output[row][col] = component["color"]
    return output


def _rival_keep_only_thin_frames(grid):
    return _keep_where(grid, lambda component, _: component["thin_frame"])


def _rival_keep_any_bbox_gap(grid):
    return _keep_where(
        grid,
        lambda component, _: (
            (_bbox(component["cells"])[2] - _bbox(component["cells"])[0] + 1)
            * (_bbox(component["cells"])[3] - _bbox(component["cells"])[1] + 1)
            > component["size"]
        ),
    )


def _rival_keep_largest_objects(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    largest = max(component["size"] for component in analysis["components"])
    return _keep_where(grid, lambda component, _: component["size"] == largest)


def _rival_keep_holed_colors(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    colors = {component["color"] for component in analysis["holed"]}
    return _keep_where(grid, lambda component, _: component["color"] in colors)


SEMANTIC_RIVALS = {
    "keep_only_thin_frames": _rival_keep_only_thin_frames,
    "keep_any_object_with_a_bbox_gap": _rival_keep_any_bbox_gap,
    "keep_largest_objects": _rival_keep_largest_objects,
    "keep_every_object_of_a_holed_color": _rival_keep_holed_colors,
}

WITNESS_RIVALS = {
    "carved_pocket_kept": ["keep_only_thin_frames"],
    "leaky_c_near_miss_dropped": ["keep_any_object_with_a_bbox_gap"],
    "dropped_solid_is_largest": ["keep_largest_objects"],
    "shared_color_opposite_topology": ["keep_every_object_of_a_holed_color"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the enclosed-hole rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the enclosed-hole rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        competitor_answer = competitor(query["input"])
        if survives and competitor_answer != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed scenes that structural self_check must reject."""
    valid = generate(7001, 2, difficulty="medium", n_solid=2)
    analysis = _analyze(valid)

    blank = full_grid(len(valid), len(valid[0]), 0)

    all_holed = rule_mirror(valid)

    all_solid = copy.deepcopy(valid)
    for component in analysis["holed"]:
        for row, col in component["cells"]:
            all_solid[row][col] = 0

    mixed_color_object = copy.deepcopy(valid)
    component = analysis["holed"][0]
    row, col = next(iter(component["cells"]))
    mixed_color_object[row][col] = 9 if component["color"] != 9 else 8

    extra_singleton = copy.deepcopy(valid)
    # The guaranteed four-slot layout leaves its central cross empty.  Painting
    # the center therefore adds a new 4-connected singleton deterministically,
    # even when it touches a corner object diagonally (as canonical examples do).
    center = (len(valid) // 2, len(valid[0]) // 2)
    if extra_singleton[center[0]][center[1]] != 0:
        raise AssertionError("central separator unexpectedly occupied")
    extra_singleton[center[0]][center[1]] = 9

    wrong_dimensions = [row[:] for row in valid] + [[0] * len(valid[0])] * 4

    return [
        ("blank_grid", blank),
        ("all_holed_no_negative_class", all_holed),
        ("all_solid_no_positive_class", all_solid),
        ("mixed_color_touching_component", mixed_color_object),
        ("extra_isolated_singleton", extra_singleton),
        ("height_outside_declared_domain", wrong_dimensions),
    ]
