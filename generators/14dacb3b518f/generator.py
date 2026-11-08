"""Generator for task 14dacb3b518f: recolor objects by hole count.

Every input contains separated 4-connected color-6 objects on a color-0
background.  An object with one or more enclosed background regions is
recolored 8; a hole-free object is recolored 2.

The five-profile curriculum deliberately goes beyond the canonical thin-frame
examples.  It includes filled pockets with an enclosed cavity, a connected
object with two holes, leaky C-shaped near-misses, and a hole-free object larger
than every holed object.  Those examples make topology necessary instead of
letting frame shape, component size, rank, or "any bbox gap" stand in for the
rule.
"""
from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "14dacb3b518f"
VERSION = "3.0.0"
TASK_ID = "14dacb3b518f"
RULE_HASH = "fe78a969401a"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Separated color-6 objects on a 0 background. Recolor each 4-connected "
    "object by topology: one or more enclosed holes -> 8; no enclosed holes "
    "-> 2. Scheduled examples include non-frame and multi-hole positives, "
    "leaky C-shaped negatives, and large hole-free negatives."
)

INVARIANTS = [
    "grid colors are exactly 0 and 6",
    "1..2 color-6 components have at least one enclosed hole",
    "1..2 color-6 components are hole-free",
    "components are placed in separated slots and never share an edge",
    "all declared axes are exactly recoverable from the returned grid",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "five-profile band-aware schedule with canonical anchors",
        "valid": "10..14",
        "doc": "Exact grid height; every explicit value is accepted in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "five-profile band-aware schedule with canonical anchors",
        "valid": "12..16",
        "doc": "Exact grid width; every explicit value is accepted in every band.",
    },
    "n_holed": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
        "doc": "Exact number of components recolored to 8.",
    },
    "n_solid": {
        "type": "int",
        "default": "scheduled 1 or 2",
        "valid": "1..2",
        "doc": "Exact number of components recolored to 2.",
    },
}

INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
SCHEDULE_PROFILES = (0, 1, 2, 3, 4)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed, sample_index, difficulty=None) -> int:
    """Five is coprime to the common ``sample_index == seed`` probe cadence."""
    del difficulty
    return (int(seed) + int(sample_index)) % len(SCHEDULE_PROFILES)


# ---------------------------------------------------------------------------
# Grid and topology analysis
# ---------------------------------------------------------------------------


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
            if isinstance(value, bool) or not isinstance(value, int):
                return "grid values must be integers"
            if value not in (0, 6):
                return f"input grid colors must be 0 or 6, found {value}"
    return None


def _bbox(cells: set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _normalize(cells: set[tuple[int, int]]) -> set[tuple[int, int]]:
    r0, c0, _, _ = _bbox(cells)
    return {(row - r0, col - c0) for row, col in cells}


def _background_regions(cells: set[tuple[int, int]]) -> list[dict[str, Any]]:
    """Return background regions inside a component's bounding box."""
    if not cells:
        return []
    r0, c0, r1, c1 = _bbox(cells)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    filled = {(row - r0, col - c0) for row, col in cells}
    seen: set[tuple[int, int]] = set()
    regions: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if start in filled or start in seen:
                continue
            stack = [start]
            seen.add(start)
            region: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                region.add((row, col))
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
            touches_edge = any(
                row in (0, height - 1) or col in (0, width - 1)
                for row, col in region
            )
            regions.append(
                {
                    "cells": {(row + r0, col + c0) for row, col in region},
                    "touches_edge": touches_edge,
                }
            )
    return regions


def _hole_count(cells: set[tuple[int, int]]) -> int:
    return sum(not region["touches_edge"] for region in _background_regions(cells))


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
    """A rectangular perimeter with one non-corner wall cell removed."""
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
    corners = {
        (0, 0),
        (0, width - 1),
        (height - 1, 0),
        (height - 1, width - 1),
    }
    return (row, col) not in corners


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if grid[start_row][start_col] != 6 or start in seen:
                continue
            stack = [start]
            seen.add(start)
            cells: set[tuple[int, int]] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in _DIR4:
                    neighbor = (row + dr, col + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == 6
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            holes = _hole_count(cells)
            components.append(
                {
                    "index": len(components),
                    "cells": cells,
                    "size": len(cells),
                    "hole_count": holes,
                    "holed": holes >= 1,
                    "thin_frame": _is_thin_frame(cells),
                    "c_shape": _is_c_shape(cells),
                }
            )
    return components


def _analyze(grid: Any) -> dict[str, Any]:
    error = _shape_error(grid)
    if error:
        return {"errors": [error]}

    height, width = len(grid), len(grid[0])
    errors: list[str] = []
    if not 10 <= height <= 14:
        errors.append(f"grid height must be in 10..14, got {height}")
    if not 12 <= width <= 16:
        errors.append(f"grid width must be in 12..16, got {width}")

    components = _components(grid)
    holed = [component for component in components if component["holed"]]
    solid = [component for component in components if not component["holed"]]
    c_shapes = [component for component in solid if component["c_shape"]]

    if not 1 <= len(holed) <= 2:
        errors.append(f"expected 1..2 holed components, found {len(holed)}")
    if not 1 <= len(solid) <= 2:
        errors.append(f"expected 1..2 hole-free components, found {len(solid)}")
    if any(component["hole_count"] > 2 for component in holed):
        errors.append("a holed component may contain at most two enclosed holes")
    if len(c_shapes) > 1:
        errors.append(f"expected at most one leaky C-shaped component, found {len(c_shapes)}")

    output = full_grid(height, width, 0)
    for component in components:
        color = 8 if component["holed"] else 2
        for row, col in component["cells"]:
            output[row][col] = color

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
        "output": output,
    }


# ---------------------------------------------------------------------------
# Shape construction and guaranteed placement
# ---------------------------------------------------------------------------


def _variants(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    variants: set[frozenset[tuple[int, int]]] = set()
    current = set(cells)
    for _ in range(4):
        variants.add(frozenset(_normalize(current)))
        variants.add(frozenset(_normalize({(row, -col) for row, col in current})))
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


def _frame_shape(rng, max_h, max_w):
    height = rng.randint(3, max_h)
    width = rng.randint(3, max_w)
    return {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }


def _pocket_shape(rng, max_h, max_w):
    """Filled rectangle with an enclosed carved pocket and interior material."""
    height = rng.randint(3, max_h)
    width = rng.randint(4, max_w)
    shape = {(row, col) for row in range(height) for col in range(width)}
    interior = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(interior)
    max_carve = max(1, min(3, len(interior) - 1))
    carve_target = rng.randint(1, max_carve)
    carve = {interior[0]}
    while len(carve) < carve_target:
        frontier = [
            neighbor
            for row, col in carve
            for dr, dc in _DIR4
            if (neighbor := (row + dr, col + dc)) in interior
            and neighbor not in carve
        ]
        if not frontier:
            break
        carve.add(rng.choice(frontier))
    shape -= carve
    if _hole_count(shape) != 1 or _is_thin_frame(shape):
        raise AssertionError("pocket constructor failed its topology contract")
    return shape


def _double_hole_shape():
    shape = {
        (row, col)
        for row in range(3)
        for col in range(5)
        if row in (0, 2) or col in (0, 2, 4)
    }
    if _hole_count(shape) != 2:
        raise AssertionError("double-hole constructor failed its topology contract")
    return shape


def _c_shape(rng, max_h, max_w):
    height = rng.randint(3, max_h)
    width = rng.randint(3, max_w)
    shape = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    removable = [
        cell
        for cell in shape
        if cell
        not in {
            (0, 0),
            (0, width - 1),
            (height - 1, 0),
            (height - 1, width - 1),
        }
    ]
    shape.remove(rng.choice(removable))
    if _hole_count(shape) or not _is_c_shape(shape):
        raise AssertionError("C-shape constructor failed its topology contract")
    return shape


def _solid_shape(kind, rng, max_h, max_w):
    if kind == "large_rect":
        return {(row, col) for row in range(max_h) for col in range(max_w)}
    if kind == "ell":
        base = {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}
        return _choose_fitting_variant(base, max_h, max_w, rng)
    if kind == "plus":
        base = {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
        return _choose_fitting_variant(base, max_h, max_w, rng)
    if kind == "line":
        length = rng.randint(2, max(max_h, max_w))
        base = {(0, col) for col in range(min(length, max_w))}
        return _choose_fitting_variant(base, max_h, max_w, rng)
    if kind == "rect":
        height = rng.randint(1, min(3, max_h))
        width = rng.randint(2, min(4, max_w))
        return {(row, col) for row in range(height) for col in range(width)}
    raise ValueError(f"unsupported solid kind {kind!r}")


def _slot_rectangles(height: int, width: int):
    slot_h = min(5, (height - 1) // 2)
    slot_w = min(5, (width - 1) // 2)
    if slot_h < 4 or slot_w < 5:
        raise ValueError(f"grid {height}x{width} cannot hold four topology slots")
    row_starts = (0, height - slot_h)
    col_starts = (0, width - slot_w)
    return [
        (row_start, col_start, slot_h, slot_w)
        for row_start in row_starts
        for col_start in col_starts
    ]


def _paint_in_slot(grid, cells, slot, rng):
    row0, col0, slot_h, slot_w = slot
    _, _, r1, c1 = _bbox(set(cells))
    shape_h, shape_w = r1 + 1, c1 + 1
    if shape_h > slot_h or shape_w > slot_w:
        raise ValueError("shape exceeds its assigned slot")
    row_offset = row0 + rng.randint(0, slot_h - shape_h)
    col_offset = col0 + rng.randint(0, slot_w - shape_w)
    for row, col in cells:
        target = (row_offset + row, col_offset + col)
        if grid[target[0]][target[1]] != 0:
            raise AssertionError("slot overlap")
        grid[target[0]][target[1]] = 6


def _draw_exact_int(ctx, label, scheduled, lo, hi):
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, scheduled, scheduled)


def _scheduled_axes(profile, difficulty):
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    dimensions = {
        "easy": ((10, 14), (11, 13), (12, 12), (12, 13), (10, 12)),
        "medium": ((10, 14), (11, 13), (12, 12), (12, 13), (13, 15)),
        "hard": ((10, 14), (11, 13), (12, 12), (12, 13), (14, 16)),
    }
    n_holed, n_solid = ((2, 2), (1, 2), (2, 1), (1, 1), (2, 2))[profile]
    height, width = dimensions[band][profile]
    return height, width, n_holed, n_solid


def _unique_prefix(preferred, fallback, count):
    result = []
    for item in [*preferred, *fallback]:
        if item not in result:
            result.append(item)
        if len(result) == count:
            return result
    raise AssertionError("shape catalog cannot satisfy requested object count")


def _shape_specs(profile, n_holed, n_solid):
    preferred_holed = {
        0: ["frame", "pocket"],
        1: ["double_hole", "pocket"],
        2: ["pocket", "frame"],
        3: ["pocket", "frame"],
        4: ["double_hole", "frame"],
    }[profile]
    preferred_solid = {
        0: ["c_shape", "large_rect"],
        1: ["large_rect", "ell"],
        2: ["c_shape", "plus"],
        3: ["large_rect", "line"],
        4: ["plus", "line"],
    }[profile]
    holed = _unique_prefix(
        preferred_holed, ["frame", "pocket", "double_hole"], n_holed
    )
    solid = _unique_prefix(
        preferred_solid, ["c_shape", "large_rect", "ell", "plus", "line", "rect"], n_solid
    )
    return holed, solid


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
    scheduled_h, scheduled_w, scheduled_holed, scheduled_solid = _scheduled_axes(
        profile, difficulty
    )
    height = _draw_exact_int(ctx, "grid_h", scheduled_h, 10, 14)
    width = _draw_exact_int(ctx, "grid_w", scheduled_w, 12, 16)
    n_holed = _draw_exact_int(ctx, "n_holed", scheduled_holed, 1, 2)
    n_solid = _draw_exact_int(ctx, "n_solid", scheduled_solid, 1, 2)

    rng = ctx.draw_rng("layout")
    slots = _slot_rectangles(height, width)
    rng.shuffle(slots)
    holed_kinds, solid_kinds = _shape_specs(profile, n_holed, n_solid)
    specs = [("holed", kind) for kind in holed_kinds] + [
        ("solid", kind) for kind in solid_kinds
    ]
    grid = full_grid(height, width, 0)

    for (role, kind), slot in zip(specs, slots):
        _, _, slot_h, slot_w = slot
        if role == "holed":
            if kind == "frame":
                shape = _frame_shape(rng, slot_h, slot_w)
            elif kind == "pocket":
                shape = _pocket_shape(rng, slot_h, slot_w)
            elif kind == "double_hole":
                shape = _double_hole_shape()
            else:
                raise ValueError(f"unsupported holed shape {kind!r}")
            shape = _choose_fitting_variant(shape, slot_h, slot_w, rng)
        elif kind == "c_shape":
            shape = _choose_fitting_variant(
                _c_shape(rng, slot_h, slot_w), slot_h, slot_w, rng
            )
        else:
            shape = _solid_shape(kind, rng, slot_h, slot_w)

        holes = _hole_count(shape)
        if (holes >= 1) != (role == "holed"):
            raise AssertionError(f"constructed {role} object has {holes} holes")
        _paint_in_slot(grid, shape, slot, rng)

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("internal generator contract failure: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_holed": n_holed,
        "n_solid": n_solid,
    }
    if observed != expected:
        raise AssertionError(
            f"axis realization mismatch: expected {expected}, observed {observed}"
        )
    return grid


# ---------------------------------------------------------------------------
# Public structural and semantic contracts
# ---------------------------------------------------------------------------


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_analyze(grid)["errors"])


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure test mirror; the pinned Racket program remains output authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["output"])


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_holed": analysis["n_holed"],
        "n_solid": analysis["n_solid"],
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
        "hole_counts": [component["hole_count"] for component in analysis["holed"]],
        "holed_sizes": holed_sizes,
        "solid_sizes": solid_sizes,
        "thin_frame_count": sum(component["thin_frame"] for component in analysis["holed"]),
        "non_frame_holed_count": sum(
            not component["thin_frame"] for component in analysis["holed"]
        ),
        "c_shape_count": len(analysis["c_shapes"]),
        "solid_larger_than_every_holed": bool(
            solid_sizes and holed_sizes and max(solid_sizes) > max(holed_sizes)
        ),
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
    "non_frame_holed": lambda grid: _witness(
        grid, lambda analysis: any(not item["thin_frame"] for item in analysis["holed"])
    ),
    "multi_hole_component": lambda grid: _witness(
        grid, lambda analysis: any(item["hole_count"] >= 2 for item in analysis["holed"])
    ),
    "leaky_c_solid": lambda grid: _witness(
        grid, lambda analysis: bool(analysis["c_shapes"])
    ),
    "solid_larger_than_every_holed": lambda grid: _witness(
        grid,
        lambda analysis: max(item["size"] for item in analysis["solid"])
        > max(item["size"] for item in analysis["holed"]),
    ),
}


def _recolor_where(grid, predicate):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    output = full_grid(analysis["height"], analysis["width"], 0)
    for component in analysis["components"]:
        color = 8 if predicate(component, analysis) else 2
        for row, col in component["cells"]:
            output[row][col] = color
    return output


def _rival_thin_frames(grid):
    return _recolor_where(grid, lambda component, _: component["thin_frame"])


def _rival_size_at_least_eight(grid):
    return _recolor_where(grid, lambda component, _: component["size"] >= 8)


def _rival_exactly_one_hole(grid):
    return _recolor_where(grid, lambda component, _: component["hole_count"] == 1)


def _rival_two_largest(grid):
    analysis = _lawful_analysis(grid)
    if analysis is None:
        return None
    ranked = sorted(
        analysis["components"],
        key=lambda component: (-component["size"], component["index"]),
    )
    selected = {component["index"] for component in ranked[:2]}
    return _recolor_where(grid, lambda component, _: component["index"] in selected)


def _rival_any_bbox_gap(grid):
    return _recolor_where(
        grid,
        lambda component, _: (
            (_bbox(component["cells"])[2] - _bbox(component["cells"])[0] + 1)
            * (_bbox(component["cells"])[3] - _bbox(component["cells"])[1] + 1)
            > component["size"]
        ),
    )


SEMANTIC_RIVALS = {
    "recolor_only_thin_frames": _rival_thin_frames,
    "recolor_size_at_least_8": _rival_size_at_least_eight,
    "recolor_exactly_one_hole": _rival_exactly_one_hole,
    "recolor_two_largest_components": _rival_two_largest,
    "recolor_any_component_with_bbox_gap": _rival_any_bbox_gap,
}

WITNESS_RIVALS = {
    "non_frame_holed": ["recolor_only_thin_frames"],
    "multi_hole_component": ["recolor_exactly_one_hole"],
    "leaky_c_solid": ["recolor_any_component_with_bbox_gap"],
    "solid_larger_than_every_holed": [
        "recolor_size_at_least_8",
        "recolor_two_largest_components",
    ],
}

CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "recolor_only_thin_frames",
        "recolor_size_at_least_8",
        "recolor_exactly_one_hole",
        "recolor_two_largest_components",
    )
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"demo {index} is outside the task grammar: {exc}")
            continue
        if demo.get("output") != expected:
            reasons.append(f"demo {index} output disagrees with the hole-count rule")
    try:
        query_answer = rule_mirror(query["input"])
    except (KeyError, TypeError, ValueError) as exc:
        reasons.append(f"query is outside the task grammar: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output disagrees with the hole-count rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(demo["input"]) == demo.get("output") for demo in demos
        )
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but changes the query answer"
            )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Task-local malformed scenes that ``self_check`` must reject."""
    valid = generate(
        7001,
        2,
        difficulty="hard",
        grid_h=14,
        grid_w=16,
        n_holed=2,
        n_solid=2,
    )
    analysis = _analyze(valid)

    blank = full_grid(14, 16, 0)

    all_holed = copy.deepcopy(valid)
    for component in analysis["solid"]:
        for row, col in component["cells"]:
            all_holed[row][col] = 0

    all_solid = copy.deepcopy(valid)
    for component in analysis["holed"]:
        for row, col in component["cells"]:
            all_solid[row][col] = 0

    wrong_color = copy.deepcopy(valid)
    row, col = next(iter(analysis["components"][0]["cells"]))
    wrong_color[row][col] = 5

    extra_singleton = copy.deepcopy(valid)
    center = (len(valid) // 2, len(valid[0]) // 2)
    if extra_singleton[center[0]][center[1]] != 0:
        raise AssertionError("central separator unexpectedly occupied")
    extra_singleton[center[0]][center[1]] = 6

    too_tall = copy.deepcopy(valid) + [[0] * len(valid[0])]
    ragged = copy.deepcopy(valid)
    ragged[-1] = ragged[-1][:-1]

    return [
        ("blank_grid", blank),
        ("all_holed_no_negative_class", all_holed),
        ("all_solid_no_positive_class", all_solid),
        ("unexpected_input_color", wrong_color),
        ("third_hole_free_component", extra_singleton),
        ("height_outside_declared_domain", too_tall),
        ("ragged_grid", ragged),
    ]
