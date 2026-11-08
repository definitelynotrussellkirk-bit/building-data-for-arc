"""Generator for ARC task c9b2eae14052 — keep exactly-one-border objects.

The input is a zero-background grid containing separated monochromatic
objects.  The canonical rule copies only objects whose bounding box touches
exactly one of the four grid borders.  Interior objects and objects touching
multiple borders are erased.

Every ordinary generated scene contains all three semantic classes.  Across
sequential sample indices the kept object rotates through top/right/bottom/
left, so a materialized lesson cannot be solved by a fixed-side shortcut.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c9b2eae14052"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "83a03df6b45f"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "On a zero-background grid with 3-6 separated, uniquely colored objects, "
    "copy exactly the objects whose bounding boxes touch one grid border. "
    "Erase interior objects and corner/multi-border objects."
)

INVARIANTS = [
    "grid dimensions are 8..14 rows by 7..14 columns and background is 0",
    "there are 3..6 separated monochromatic 4-connected objects",
    "each object has a distinct nonzero color and 2..4 cells",
    "at least one object touches exactly one border and is kept",
    "at least one interior object touches zero borders and is erased",
    "ordinary generated scenes also contain a two-border corner object",
]

# Public axes are exact scene properties recoverable from observe_overrides().
# Difficulty changes only the default schedule; every declared boundary remains
# legal in every band and in every Cartesian override combination.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-aware variants",
        "valid": "8..14",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-aware variants",
        "valid": "7..14",
    },
    "n_objects": {
        "type": "int",
        "default": "canonical-profile schedule plus difficulty-aware variants",
        "valid": "3..6",
    },
}

CANONICAL_PROFILES = (
    (9, 7, 3),  # canonical train 0: 9x7 and 3 object colors (+ background)
    (8, 8, 3),  # canonical train 1: 8x8 and 3 object colors (+ background)
    (9, 9, 6),  # canonical test:    9x9 and 6 object colors (+ background)
)

TARGET_SIDES = ("top", "right", "bottom", "left")
SCHEDULE_PROFILES = tuple(range(12))


def schedule_profile(seed, sample_index, difficulty=None):
    """Expose the complete deterministic branch schedule to the semantic gate."""
    del seed, difficulty
    return sample_index % 12


def _draw_scheduled_int(ctx, label: str, default: int, lo: int, hi: int) -> int:
    """Record an exact scheduled default while preserving the global override domain."""
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_int(label, default, default)


def _default_profile(sample_index: int, difficulty) -> tuple[int, int, int]:
    """Return (height, width, object count), with frequent canonical anchors."""
    residue = sample_index % 6
    if residue < 3:
        return CANONICAL_PROFILES[residue]

    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    variants = {
        "easy": ((8, 7, 4), (9, 8, 3), (8, 10, 4)),
        "medium": ((10, 10, 4), (11, 9, 5), (9, 12, 5)),
        "hard": ((12, 13, 5), (14, 14, 6), (13, 11, 6)),
    }
    return variants[band][residue - 3]


def _orthogonal_neighbors(cell: tuple[int, int]):
    r, c = cell
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        yield r + dr, c + dc


def _can_place(cells: set[tuple[int, int]], occupied: set[tuple[int, int]], h: int, w: int) -> bool:
    if not cells or any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
        return False
    if cells & occupied:
        return False
    return not any(neighbor in occupied for cell in cells for neighbor in _orthogonal_neighbors(cell))


@lru_cache(maxsize=None)
def _connected_shapes(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return every translation-normalized fixed polyomino of ``size`` cells."""
    if not 1 <= size <= 4:
        raise ValueError(f"unsupported object size {size}")
    shapes: set[tuple[tuple[int, int], ...]] = {((0, 0),)}
    for _ in range(1, size):
        grown: set[tuple[tuple[int, int], ...]] = set()
        for shape in shapes:
            cells = set(shape)
            for cell in shape:
                for neighbor in _orthogonal_neighbors(cell):
                    if neighbor in cells:
                        continue
                    candidate = cells | {neighbor}
                    min_r = min(r for r, _c in candidate)
                    min_c = min(c for _r, c in candidate)
                    normalized = tuple(
                        sorted((r - min_r, c - min_c) for r, c in candidate)
                    )
                    grown.add(normalized)
        shapes = grown
    return tuple(sorted(shapes))


CORNER_SIDES = {
    "corner_nw": frozenset(("top", "left")),
    "corner_ne": frozenset(("top", "right")),
    "corner_se": frozenset(("bottom", "right")),
    "corner_sw": frozenset(("bottom", "left")),
}
CORNER_SLOTS = tuple(CORNER_SIDES)


def _required_sides(slot: str) -> frozenset[str]:
    if slot == "interior":
        return frozenset()
    if slot in TARGET_SIDES:
        return frozenset((slot,))
    if slot in CORNER_SIDES:
        return CORNER_SIDES[slot]
    raise ValueError(f"unknown semantic slot {slot!r}")


@lru_cache(maxsize=None)
def _candidate_placements(
    slot: str, size: int, h: int, w: int
) -> tuple[frozenset[tuple[int, int]], ...]:
    """Enumerate lawful connected placements for a semantic border class."""
    required = _required_sides(slot)
    candidates: list[frozenset[tuple[int, int]]] = []
    for shape in _connected_shapes(size):
        shape_h = max(r for r, _c in shape) + 1
        shape_w = max(c for _r, c in shape) + 1
        for row0 in range(h - shape_h + 1):
            for col0 in range(w - shape_w + 1):
                cells = frozenset((row0 + r, col0 + c) for r, c in shape)
                if _border_sides(list(cells), h, w) == required:
                    candidates.append(cells)
    return tuple(sorted(set(candidates), key=lambda cells: tuple(sorted(cells))))


def _pack_scene(
    plan: list[tuple[str, str, int]], h: int, w: int, rng
) -> list[frozenset[tuple[int, int]]]:
    """Choose isolated seed-varying placements with exhaustive backtracking."""
    candidate_lists: list[list[frozenset[tuple[int, int]]]] = []
    for _kind, slot, size in plan:
        candidates = list(_candidate_placements(slot, size, h, w))
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    order = sorted(range(len(plan)), key=lambda index: len(candidate_lists[index]))
    placements: list[frozenset[tuple[int, int]] | None] = [None] * len(plan)

    def search(depth: int, occupied: set[tuple[int, int]]) -> bool:
        if depth == len(order):
            return True
        index = order[depth]
        for cells in candidate_lists[index]:
            if not _can_place(set(cells), occupied, h, w):
                continue
            placements[index] = cells
            if search(depth + 1, occupied | set(cells)):
                return True
            placements[index] = None
        return False

    if not search(0, set()):
        description = [(slot, size) for _kind, slot, size in plan]
        raise ValueError(f"cannot pack scene {description!r} on {h}x{w}")
    return [cells for cells in placements if cells is not None]


def _scene_plan(sample_index: int, n_objects: int) -> list[tuple[str, str, int]]:
    """Return (semantic class, slot, desired size) records.

    The first three entries are always one-border/interior/two-border.  Extra
    objects add other sides and the opposite corner without weakening those
    mandatory witnesses.  Size schedules deliberately make the target smaller
    than a distractor on one residue and larger on another.
    """
    target_side = TARGET_SIDES[sample_index % 4]
    opposite_side = TARGET_SIDES[(sample_index + 2) % 4]
    third_side = TARGET_SIDES[(sample_index + 1) % 4]
    first_corner = CORNER_SLOTS[sample_index % len(CORNER_SLOTS)]
    second_corner = CORNER_SLOTS[(sample_index + 2) % len(CORNER_SLOTS)]

    size_residue = sample_index % 3
    if size_residue == 0:
        target_size, interior_size, corner_size = 2, 4, 3
    elif size_residue == 1:
        target_size, interior_size, corner_size = 3, 2, 2
    else:
        target_size, interior_size, corner_size = 3, 4, 2

    plan = [
        ("one", target_side, target_size),
        ("zero", "interior", interior_size),
        ("multi", first_corner, corner_size),
        ("one", opposite_side, target_size),
        ("multi", second_corner, 4 if corner_size != 4 else 3),
        ("one", third_side, target_size),
    ]
    return plan[:n_objects]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return a deterministic fresh scene for the canonical Racket oracle."""
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w, default_n = _default_profile(sample_index, difficulty)
    h = _draw_scheduled_int(ctx, "grid_h", default_h, 8, 14)
    w = _draw_scheduled_int(ctx, "grid_w", default_w, 7, 14)
    n_objects = _draw_scheduled_int(ctx, "n_objects", default_n, 3, 6)

    colors = list(ctx.draw_distinct_colors("object_colors", n=n_objects, exclude=(0,)))
    color_rng = ctx.draw_rng("color_order")
    color_rng.shuffle(colors)

    plan = _scene_plan(sample_index, n_objects)
    placements = _pack_scene(plan, h, w, ctx.draw_rng("object_geometry"))
    grid = full_grid(h, w, 0)
    for color, cells in zip(colors, placements):
        for r, c in cells:
            grid[r][c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise AssertionError("generator constructed invalid scene: " + "; ".join(errors))
    # Ordinary generated scenes must contain the stronger three-way teaching
    # coverage even though canonical train rows lawfully omit the corner case.
    info = _analysis(grid)
    if not info["multi"]:
        raise AssertionError("generator omitted the multi-border negative branch")
    return grid


def _shape_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["empty or non-list grid"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["ragged or non-list row"]
    errors = []
    if len(grid) > 30 or width > 30:
        errors.append(f"grid exceeds ARC bounds: {len(grid)}x{width}")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("grid contains a non-integer or color outside 0..9")
    return errors


def _border_sides(cells: list[tuple[int, int]], h: int, w: int) -> frozenset[str]:
    sides: set[str] = set()
    for r, c in cells:
        if r == 0:
            sides.add("top")
        if r == h - 1:
            sides.add("bottom")
        if c == 0:
            sides.add("left")
        if c == w - 1:
            sides.add("right")
    return frozenset(sides)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _shape_errors(grid)
    if errors:
        return {
            "errors": errors,
            "height": 0,
            "width": 0,
            "records": [],
            "one": [],
            "zero": [],
            "multi": [],
        }

    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    records: list[dict[str, Any]] = []
    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color == 0 or (r0, c0) in seen:
                continue
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for nr, nc in _orthogonal_neighbors((r, c)):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            sides = _border_sides(cells, h, w)
            records.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "sides": sides,
                    "border_count": len(sides),
                }
            )

    records.sort(key=lambda record: record["cells"][0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0:
                continue
            for nr, nc in ((r + 1, c), (r, c + 1)):
                if 0 <= nr < h and 0 <= nc < w:
                    other = grid[nr][nc]
                    if other != 0 and other != grid[r][c]:
                        errors.append("distinct-colored objects touch orthogonally")
                        break

    color_counts = Counter(record["color"] for record in records)
    duplicates = sorted(color for color, count in color_counts.items() if count > 1)
    if duplicates:
        errors.append(f"object colors are reused across components: {duplicates}")

    return {
        "errors": errors,
        "height": h,
        "width": w,
        "records": records,
        "one": [record for record in records if record["border_count"] == 1],
        "zero": [record for record in records if record["border_count"] == 0],
        "multi": [record for record in records if record["border_count"] >= 2],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the lawful task grammar while accepting every canonical input."""
    del difficulty
    info = _analysis(grid)
    errors = list(info["errors"])
    if errors:
        return errors

    h, w = info["height"], info["width"]
    records = info["records"]
    if not (8 <= h <= 14):
        errors.append(f"height {h} outside teaching range 8..14")
    if not (7 <= w <= 14):
        errors.append(f"width {w} outside teaching range 7..14")
    if not (3 <= len(records) <= 6):
        errors.append(f"expected 3..6 objects, found {len(records)}")
    for record in records:
        if not (2 <= record["size"] <= 4):
            errors.append(
                f"object color {record['color']} has {record['size']} cells; expected 2..4"
            )
        if record["border_count"] > 2:
            errors.append(
                f"object color {record['color']} touches {record['border_count']} borders"
            )
    if not info["one"]:
        errors.append("missing an exactly-one-border object (the keep branch)")
    if not info["zero"]:
        errors.append("missing an interior object (the zero-border drop branch)")

    if meta and isinstance(meta, dict):
        requested = meta.get("overrides", meta)
        if isinstance(requested, dict):
            observed = observe_overrides(grid)
            for axis, value in requested.items():
                if axis in AXES and observed.get(axis) != value:
                    errors.append(
                        f"{axis} requested {value!r}, observed {observed.get(axis)!r}"
                    )
    return errors


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public axis from a returned lawful scene."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot observe malformed scene: " + "; ".join(info["errors"]))
    return {
        "grid_h": info["height"],
        "grid_w": info["width"],
        "n_objects": len(info["records"]),
    }


def strict_canonical_like(grid) -> list[str]:
    """Task-linked semantic predicate used by the strict semantic gate."""
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests only; Racket remains authoritative."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot apply mirror to malformed scene: " + "; ".join(info["errors"]))
    out = full_grid(info["height"], info["width"], 0)
    for record in info["one"]:
        for r, c in record["cells"]:
            out[r][c] = record["color"]
    return out


def _rival_select(grid, predicate: Callable[[dict[str, Any]], bool]) -> list[list[int]]:
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("cannot apply rival to malformed scene")
    out = full_grid(info["height"], info["width"], 0)
    for record in info["records"]:
        if predicate(record):
            for r, c in record["cells"]:
                out[r][c] = record["color"]
    return out


def _copy_input(grid):
    return [row[:] for row in grid]


def _keep_any_border(grid):
    return _rival_select(grid, lambda record: record["border_count"] >= 1)


def _keep_side(grid, side: str):
    return _rival_select(
        grid,
        lambda record: record["border_count"] == 1 and side in record["sides"],
    )


def _keep_largest(grid):
    info = _analysis(grid)
    maximum = max(record["size"] for record in info["records"])
    return _rival_select(grid, lambda record: record["size"] == maximum)


def _keep_smallest(grid):
    info = _analysis(grid)
    minimum = min(record["size"] for record in info["records"])
    return _rival_select(grid, lambda record: record["size"] == minimum)


SEMANTIC_RIVALS = {
    "copy_input": _copy_input,
    "keep_any_border": _keep_any_border,
    "keep_top_only": lambda grid: _keep_side(grid, "top"),
    "keep_right_only": lambda grid: _keep_side(grid, "right"),
    "keep_bottom_only": lambda grid: _keep_side(grid, "bottom"),
    "keep_left_only": lambda grid: _keep_side(grid, "left"),
    "keep_largest": _keep_largest,
    "keep_smallest": _keep_smallest,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _lawful_info(grid) -> dict[str, Any] | None:
    return None if self_check(grid) else _analysis(grid)


def _witness(predicate: Callable[[dict[str, Any]], bool], grid) -> bool:
    info = _lawful_info(grid)
    return False if info is None else bool(predicate(info))


def _has_target_side(info: dict[str, Any], side: str) -> bool:
    return any(side in record["sides"] for record in info["one"])


def _targets_strictly_smaller_than_a_drop(info: dict[str, Any]) -> bool:
    drops = info["zero"] + info["multi"]
    return bool(drops) and max(record["size"] for record in info["one"]) < max(
        record["size"] for record in drops
    )


def _targets_strictly_larger_than_a_drop(info: dict[str, Any]) -> bool:
    drops = info["zero"] + info["multi"]
    return bool(drops) and min(record["size"] for record in info["one"]) > min(
        record["size"] for record in drops
    )


SEMANTIC_WITNESSES = {
    "top_target": lambda grid: _witness(lambda info: _has_target_side(info, "top"), grid),
    "right_target": lambda grid: _witness(lambda info: _has_target_side(info, "right"), grid),
    "bottom_target": lambda grid: _witness(lambda info: _has_target_side(info, "bottom"), grid),
    "left_target": lambda grid: _witness(lambda info: _has_target_side(info, "left"), grid),
    "interior_drop_present": lambda grid: _witness(lambda info: bool(info["zero"]), grid),
    "multi_border_drop_present": lambda grid: _witness(lambda info: bool(info["multi"]), grid),
    "target_strictly_smaller_than_a_drop": lambda grid: _witness(
        _targets_strictly_smaller_than_a_drop, grid
    ),
    "target_strictly_larger_than_a_drop": lambda grid: _witness(
        _targets_strictly_larger_than_a_drop, grid
    ),
}

WITNESS_RIVALS = {
    "top_target": ["keep_bottom_only"],
    "right_target": ["keep_left_only"],
    "bottom_target": ["keep_top_only"],
    "left_target": ["keep_right_only"],
    "interior_drop_present": ["copy_input"],
    "multi_border_drop_present": ["keep_any_border"],
    "target_strictly_smaller_than_a_drop": ["keep_largest"],
    "target_strictly_larger_than_a_drop": ["keep_smallest"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named shortcut fits every demo but changes query."""
    reasons: list[str] = []
    for index, pair in enumerate([*demos, query]):
        role = f"demo {index}" if index < len(demos) else "query"
        if not isinstance(pair, dict):
            reasons.append(f"{role} is not a pair dict")
            continue
        grid = pair.get("input")
        output = pair.get("output")
        findings = strict_canonical_like(grid)
        if findings:
            reasons.append(f"{role} is not lawful: {findings[:2]}")
            continue
        if rule_mirror(grid) != output:
            reasons.append(f"{role} output does not match exactly-one-border selection")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(
                f"demos do not falsify shortcut {name!r}, which changes the query"
            )
    return reasons
