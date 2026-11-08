"""Generator for ARC task 20014c9d3729 — keep the largest object per color.

Inputs are zero-background grids containing five to eight monochrome
4-connected objects in two to four colors.  Object sizes are distinct within
each color, so every color has one unambiguous largest object.  The output is a
blank grid of the same size with only that largest object of each color kept.

The public examples also admit a misleading shortcut: every kept object has
size at least four and every discarded object has size at most three.  The
``threshold_counterexample`` axis deliberately creates a same-color size-4
loser beside a size-5 winner, forcing the intended *relative per-color* rule.
"""
from __future__ import annotations

from collections.abc import Callable
from functools import lru_cache
from math import gcd
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components


GENERATOR_ID = "20014c9d3729"
TASK_ID = "20014c9d3729"
VERSION = "4.0.0"
RULE_HASH = "0149d1fbd1ae"
EXAMPLES_NEEDED = 2

SUMMARY = (
    "On a zero-background grid, group 4-connected objects by color and keep "
    "only the largest object of each color in its original position. Object "
    "sizes are distinct within each color. Normal generation includes "
    "counterexamples where an absolute size>=4 threshold keeps a size-4 "
    "loser, so the lesson identifies relative per-color selection."
)

INVARIANTS = [
    "the grid contains 2..4 nonzero colors and 5..8 same-color components",
    "at least one color has multiple components",
    "component sizes are 1..6 and pairwise distinct within each color",
    "each color therefore has one unique largest component",
    "threshold_counterexample=true makes the size>=4 shortcut disagree",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware rng",
        "valid": "8..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware rng",
        "valid": "9..18",
    },
    "n_colors": {
        "type": "int",
        "default": "canonical anchor or difficulty-aware rng",
        "valid": "2..4",
    },
    "total_objects": {
        "type": "int",
        "default": "5 on canonical anchors, otherwise difficulty-aware rng",
        "valid": "5..8",
    },
    "threshold_counterexample": {
        "type": "bool",
        "default": "alternates false/true by sample index",
        "valid": "false|true",
    },
}

_EXACT_AXES = tuple(AXES)
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# (height, width, number of nonzero colors).  The profile gate counts the
# background too, so these correspond exactly to the four demonstrated
# (height, width, palette-cardinality) profiles.
_CANONICAL_PROFILES = (
    (8, 9, 3),
    (9, 9, 2),
    (9, 10, 3),
    (10, 10, 3),
)

# Several connected seeds per size.  D4 closure supplies orientation variety.
_BASE_SHAPES: dict[int, tuple[tuple[tuple[int, int], ...], ...]] = {
    1: (
        ((0, 0),),
    ),
    2: (
        ((0, 0), (0, 1)),
    ),
    3: (
        ((0, 0), (0, 1), (0, 2)),
        ((0, 0), (1, 0), (1, 1)),
    ),
    4: (
        ((0, 0), (0, 1), (0, 2), (0, 3)),
        ((0, 0), (0, 1), (1, 0), (1, 1)),
        ((0, 0), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1)),
        ((0, 0), (0, 1), (1, 1), (1, 2)),
    ),
    5: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ),
    6: (
        ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5)),
        ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
        ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3)),
        ((0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
        ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1)),
    ),
}


def _normalize_shape(cells: tuple[tuple[int, int], ...] | list[tuple[int, int]]):
    min_row = min(row for row, _col in cells)
    min_col = min(col for _row, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _shape_variants(size: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    variants: set[tuple[tuple[int, int], ...]] = set()
    for base in _BASE_SHAPES[size]:
        for reflected in (False, True):
            for turns in range(4):
                transformed: list[tuple[int, int]] = []
                for row, col in base:
                    x, y = row, (-col if reflected else col)
                    for _ in range(turns):
                        x, y = y, -x
                    transformed.append((x, y))
                variants.add(_normalize_shape(transformed))
    return tuple(sorted(variants))


_SHAPE_VARIANTS = {size: _shape_variants(size) for size in _BASE_SHAPES}


@lru_cache(maxsize=None)
def _candidate_cells(height: int, width: int, size: int):
    """Every translated D4 shape of ``size`` that fits the canvas."""
    candidates: set[tuple[tuple[int, int], ...]] = set()
    for shape in _SHAPE_VARIANTS[size]:
        shape_h = max(row for row, _col in shape) + 1
        shape_w = max(col for _row, col in shape) + 1
        for top in range(height - shape_h + 1):
            for left in range(width - shape_w + 1):
                candidates.add(tuple((top + row, left + col) for row, col in shape))
    return tuple(sorted(candidates))


def _validate_call(difficulty: str | None, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    if (
        "threshold_counterexample" in overrides
        and overrides["threshold_counterexample"] is not None
        and type(overrides["threshold_counterexample"]) is not bool
    ):
        raise ValueError("threshold_counterexample override must be bool")


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Every two consecutive examples include one shortcut counterexample."""
    del seed, difficulty
    return (
        "relative_size_not_absolute"
        if int(sample_index) % 2
        else "canonical_threshold_pattern"
    )


def _draw_axis_int(ctx, label: str, lo: int, hi: int, anchor: int | None) -> int:
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_int(label, lo, hi)
    if anchor is not None:
        return int(ctx.draw_choice(label, (anchor,)))
    return ctx.draw_int_diff(label, lo, hi)


def _object_counts(rng, n_colors: int, total_objects: int) -> list[int]:
    counts = [1] * n_colors
    order = list(range(n_colors))
    rng.shuffle(order)
    for index in range(total_objects - n_colors):
        counts[order[index % n_colors]] += 1
    return counts


def _size_plan(rng, counts: list[int], threshold_counterexample: bool):
    repeated = [index for index, count in enumerate(counts) if count >= 2]
    if not repeated:
        raise ValueError("total_objects must leave at least one repeated color")
    witness_color = rng.choice(repeated) if threshold_counterexample else None

    plans: list[list[int]] = []
    for color_index, count in enumerate(counts):
        if color_index == witness_color:
            # The size-4 object is a real loser.  The fixed >=4 shortcut keeps
            # both it and the unique size-5 winner.
            extra_losers = rng.sample((1, 2, 3), count - 2)
            sizes = extra_losers + [4, 5]
        else:
            loser_sizes = rng.sample((1, 2, 3), count - 1)
            sizes = loser_sizes + [rng.choice((4, 5, 6))]
        rng.shuffle(sizes)
        plans.append(sizes)
    return plans


def _candidate_order(count: int, rng):
    if count <= 1:
        return range(count)
    start = rng.randrange(count)
    step = rng.randrange(1, count)
    while gcd(step, count) != 1:
        step = (step + 1) % count or 1
    return ((start + offset * step) % count for offset in range(count))


def _can_place(grid: list[list[int]], color: int, cells) -> bool:
    height = len(grid)
    width = len(grid[0])
    for row, col in cells:
        if grid[row][col] != 0:
            return False
        for delta_row, delta_col in _CARDINAL:
            neighbor_row = row + delta_row
            neighbor_col = col + delta_col
            if (
                0 <= neighbor_row < height
                and 0 <= neighbor_col < width
                and grid[neighbor_row][neighbor_col] == color
            ):
                return False
    return True


def _write_cells(grid: list[list[int]], cells, color: int) -> None:
    for row, col in cells:
        grid[row][col] = color


def _place_objects(height: int, width: int, object_specs, rng) -> list[list[int]]:
    """Complete bounded backtracking over cached shape translations."""
    grid = full_grid(height, width, 0)
    shuffled = list(object_specs)
    rng.shuffle(shuffled)
    shuffled.sort(key=lambda item: -item[1])

    starts = []
    for _color, size, _serial in shuffled:
        candidates = _candidate_cells(height, width, size)
        order_rng = rng.__class__()
        order_rng.setstate(rng.getstate())
        # Advance the shared RNG once so equal-size objects receive different
        # permutations while the search itself remains deterministic.
        rng.random()
        starts.append(tuple(_candidate_order(len(candidates), order_rng)))

    visited = 0
    node_limit = 500_000

    def place(index: int) -> bool:
        nonlocal visited
        if index == len(shuffled):
            return True
        color, size, _serial = shuffled[index]
        candidates = _candidate_cells(height, width, size)
        for candidate_index in starts[index]:
            visited += 1
            if visited > node_limit:
                return False
            cells = candidates[candidate_index]
            if not _can_place(grid, color, cells):
                continue
            _write_cells(grid, cells, color)
            if place(index + 1):
                return True
            _write_cells(grid, cells, 0)
        return False

    if not place(0):
        raise ValueError(
            "could not place lawful objects: "
            f"canvas={height}x{width}, objects={[(c, s) for c, s, _ in object_specs]}"
        )
    return grid


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

    canonical_anchor = int(sample_index) % 2 == 0
    profile = _CANONICAL_PROFILES[(int(sample_index) // 2) % len(_CANONICAL_PROFILES)]
    anchor_h, anchor_w, anchor_colors = profile if canonical_anchor else (None, None, None)

    height = _draw_axis_int(ctx, "grid_h", 8, 16, anchor_h)
    width = _draw_axis_int(ctx, "grid_w", 9, 18, anchor_w)
    n_colors = _draw_axis_int(ctx, "n_colors", 2, 4, anchor_colors)
    total_objects = _draw_axis_int(
        ctx, "total_objects", 5, 8, 5 if canonical_anchor else None
    )

    if "threshold_counterexample" in overrides and overrides["threshold_counterexample"] is not None:
        threshold_counterexample = bool(
            ctx.draw_choice("threshold_counterexample", (False, True))
        )
    else:
        scheduled = schedule_profile(seed, sample_index, difficulty) == "relative_size_not_absolute"
        threshold_counterexample = bool(
            ctx.draw_choice("threshold_counterexample", (scheduled,))
        )

    rng = ctx.draw_rng("layout")
    colors = rng.sample(tuple(range(1, 10)), n_colors)
    counts = _object_counts(rng, n_colors, total_objects)
    plans = _size_plan(rng, counts, threshold_counterexample)
    object_specs = [
        (color, size, serial)
        for color, sizes in zip(colors, plans, strict=True)
        for serial, size in enumerate(sizes)
    ]
    grid = _place_objects(height, width, object_specs, rng)

    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid lesson: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_colors": n_colors,
        "total_objects": total_objects,
        "threshold_counterexample": threshold_counterexample,
    }
    if observed != expected:
        raise AssertionError(f"axis realization drift: expected {expected}, observed {observed}")
    return grid


def _coerce_grid(grid: Any):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None, ["grid must be a nonempty rectangular sequence"]
    first = grid[0]
    width = len(first) if isinstance(first, (list, tuple)) else 0
    if width == 0:
        return None, ["grid rows must be nonempty"]
    errors: list[str] = []
    rows: list[list[int]] = []
    for row_index, row in enumerate(grid):
        if not isinstance(row, (list, tuple)) or len(row) != width:
            errors.append(f"grid must be rectangular; row {row_index} has wrong width")
            continue
        converted: list[int] = []
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                errors.append("all cells must be integer ARC colors 0..9")
                converted.append(0)
            else:
                converted.append(value)
        rows.append(converted)
    if errors:
        return None, errors
    return rows, []


def _component_groups(grid: list[list[int]]):
    groups: dict[int, list[dict[str, Any]]] = {}
    for component in components(grid):
        groups.setdefault(component["color"], []).append(component)
    return groups


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural demonstrated-manifold contract; accepts every public input."""
    del difficulty, meta
    rows, errors = _coerce_grid(grid)
    if errors:
        return errors
    assert rows is not None
    height = len(rows)
    width = len(rows[0])
    if not 8 <= height <= 16:
        errors.append(f"grid height must be 8..16, got {height}")
    if not 9 <= width <= 18:
        errors.append(f"grid width must be 9..18, got {width}")
    if not any(value == 0 for row in rows for value in row):
        errors.append("grid must contain background color 0")

    groups = _component_groups(rows)
    if not 2 <= len(groups) <= 4:
        errors.append(f"expected 2..4 nonzero colors, got {sorted(groups)}")
    all_components = [component for group in groups.values() for component in group]
    if not 5 <= len(all_components) <= 8:
        errors.append(f"expected 5..8 objects, got {len(all_components)}")
    if groups and not any(len(group) >= 2 for group in groups.values()):
        errors.append("at least one color must have multiple objects")

    for color, group in sorted(groups.items()):
        sizes = [len(component["cells"]) for component in group]
        if any(not 1 <= size <= 6 for size in sizes):
            errors.append(f"color {color} object sizes must be 1..6, got {sorted(sizes)}")
        if len(set(sizes)) != len(sizes):
            errors.append(f"color {color} object sizes must be distinct, got {sorted(sizes)}")
        if sizes and sizes.count(max(sizes)) != 1:
            errors.append(f"color {color} must have a unique largest object")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Task-linked lawful-manifold predicate used by the semantic gate."""
    return self_check(grid)


def _lawful_rows(grid) -> list[list[int]]:
    rows, structural_errors = _coerce_grid(grid)
    if structural_errors:
        raise ValueError("solver requires a rectangular ARC grid: " + "; ".join(structural_errors))
    assert rows is not None
    return rows


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; Racket remains output authority."""
    rows = _lawful_rows(grid)
    output = full_grid(len(rows), len(rows[0]), 0)
    for color, group in _component_groups(rows).items():
        chosen = min(
            group,
            key=lambda component: (
                -len(component["cells"]),
                component["bbox"][0],
                component["bbox"][1],
            ),
        )
        for row, col in chosen["cells"]:
            output[row][col] = color
    return output


def _fixed_size_threshold_four(grid) -> list[list[int]]:
    rows = _lawful_rows(grid)
    output = full_grid(len(rows), len(rows[0]), 0)
    for component in components(rows):
        if len(component["cells"]) >= 4:
            for row, col in component["cells"]:
                output[row][col] = component["color"]
    return output


def _relative_size_witness(grid) -> bool:
    try:
        return _fixed_size_threshold_four(grid) != rule_mirror(grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "fixed_size_threshold_four": _fixed_size_threshold_four,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
SEMANTIC_WITNESSES = {
    "relative_size_not_absolute": _relative_size_witness,
}
WITNESS_RIVALS = {
    "relative_size_not_absolute": ("fixed_size_threshold_four",),
}


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every declared exact axis solely from the returned input grid."""
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    rows = _lawful_rows(grid)
    groups = _component_groups(rows)
    total_objects = sum(len(group) for group in groups.values())
    return {
        "grid_h": len(rows),
        "grid_w": len(rows[0]),
        "n_colors": len(groups),
        "total_objects": total_objects,
        "threshold_counterexample": _relative_size_witness(rows),
    }
