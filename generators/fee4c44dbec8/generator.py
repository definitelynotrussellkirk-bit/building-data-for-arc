"""Generator for M153 — histogram of connected components by color.

For each non-background color, count its 4-connected components.  Sort the
colors numerically and emit one left-aligned bar per color; the output width is
the largest component count.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "fee4c44dbec8"
TASK_ID = "fee4c44dbec8"
VERSION = "4.0.0"
RULE_HASH = "934d81b66c5f"

SUMMARY = (
    "On an 8-10 by 10-12 zero-background grid, place two or three colors as "
    "several isolated 4-connected components.  Component counts vary by color, "
    "and at least one color mixes a singleton with a multi-cell component.  "
    "Sort the non-background colors in ascending numeric order.  For each color, "
    "count its connected components and output a left-aligned bar of that color "
    "with one cell per component.  Pad shorter rows with zero to the largest "
    "component count."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "grid dimensions are 8..10 rows by 10..12 columns",
    "exactly 2 or 3 distinct non-background colors occur",
    "each color has 1..3 isolated 4-connected components",
    "component counts vary across colors and the largest count is 2 or 3",
    "every component has 1..3 cells",
    "at least one singleton and one multi-cell component occur",
    "different components never touch orthogonally",
]

# Every axis below is exact, keyed through GenCtx, and recoverable from the
# returned grid by observe_overrides().
AXES = {
    "grid_h": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "8..10",
    },
    "grid_w": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "10..12",
    },
    "n_colors": {
        "type": "int",
        "default": "keyed uniform",
        "valid": "2..3",
    },
    "comp_count": {
        "type": "int",
        "default": "keyed uniform maximum component count",
        "valid": "2..3",
    },
    "blob_size": {
        "type": "int",
        "default": "keyed uniform maximum component size",
        "valid": "2..3",
    },
}


def _component_shape(
    anchor: tuple[int, int], size: int, variant: int
) -> set[tuple[int, int]]:
    """Return a connected size-1..3 shape inside the anchor's 2x2 slot."""
    r, c = anchor
    cells = ((r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1))
    if size == 1:
        return {cells[variant % 4]}
    if size == 2:
        pairs = (
            (cells[0], cells[1]),
            (cells[0], cells[2]),
            (cells[2], cells[3]),
            (cells[1], cells[3]),
        )
        return set(pairs[variant % len(pairs)])
    if size == 3:
        missing = variant % 4
        return {cell for index, cell in enumerate(cells) if index != missing}
    raise ValueError(f"component size must be 1..3, got {size}")


def _component_counts(n_colors: int, maximum: int, rng) -> list[int]:
    """Produce varied positive counts whose realized maximum is exact."""
    if n_colors == 2:
        counts = [maximum, maximum - 1]
    else:
        counts = [maximum, maximum - 1, 1]
    rng.shuffle(counts)
    return counts


def _component_sizes(
    counts: list[int], maximum: int, difficulty: str, rng
) -> list[list[int]]:
    """Assign exact maximum size while preserving a cell-count rebuttal."""
    sizes = [[1 for _ in range(count)] for count in counts]
    target = next(index for index, count in enumerate(counts) if count >= 2)
    sizes[target][0] = maximum

    # Difficulty changes texture without changing any declared exact axis.
    if difficulty == "medium":
        for row in sizes:
            for index in range(1, len(row)):
                row[index] = rng.randint(1, maximum)
    elif difficulty == "hard":
        for row_index, row in enumerate(sizes):
            for index in range(1, len(row)):
                row[index] = maximum if (row_index + index) % 2 else 1

    # Keep at least one singleton even after texture enrichment.
    singleton_target = next(
        (row for row in sizes if any(size == 1 for size in row)), None
    )
    if singleton_target is None:
        sizes[target][-1] = 1
    return sizes


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Generate one deterministic input grid for the canonical Racket rule."""
    band = difficulty if difficulty in {"easy", "medium", "hard"} else "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int("grid_h", 8, 10)
    w = ctx.draw_int("grid_w", 10, 12)
    n_colors = ctx.draw_int("n_colors", 2, 3)
    maximum_count = ctx.draw_int("comp_count", 2, 3)
    maximum_size = ctx.draw_int("blob_size", 2, 3)

    # The band-specific labels make the three difficulty streams genuinely
    # distinct while all exact AXES retain the same lawful boundary contract.
    colors = sorted(
        ctx.draw_distinct_colors(f"palette_{band}", n=n_colors, exclude={0})
    )
    rng = ctx.draw_rng(f"layout_{band}")
    counts = _component_counts(n_colors, maximum_count, rng)
    sizes = _component_sizes(counts, maximum_size, band, rng)
    plan = {color: list(color_sizes) for color, color_sizes in zip(colors, sizes)}

    # A 2x2 component slot every three cells leaves a full blank row/column
    # between slots.  The minimum 8x10 canvas has nine slots; this generator
    # needs at most six, so no requested component can be silently dropped.
    slots = [
        (r, c)
        for r in range(0, h - 1, 3)
        for c in range(0, w - 1, 3)
    ]
    total_components = sum(counts)
    if len(slots) < total_components:
        raise ValueError(
            f"{h}x{w} provides {len(slots)} isolated slots for "
            f"{total_components} requested components"
        )
    selected_slots = sorted(rng.sample(slots, total_components))

    # Put each color's first component into the earliest selected slots in
    # descending color order.  Thus first-appearance order disagrees with the
    # required ascending output order on every ordinary draw, explicitly
    # refuting a spatial-order shortcut.
    records: list[tuple[int, int]] = []
    for color in sorted(colors, reverse=True):
        records.append((color, plan[color].pop(0)))
    remainder = [
        (color, size)
        for color in colors
        for size in plan[color]
    ]
    rng.shuffle(remainder)
    records.extend(remainder)

    grid = full_grid(h, w, 0)
    for index, ((color, size), slot) in enumerate(zip(records, selected_slots)):
        # Each color's first component contains the slot's top-left cell, so
        # row-major first appearance follows descending color order exactly.
        if index < n_colors:
            if size == 1:
                variant = 0
            elif size == 2:
                variant = rng.choice((0, 1))
            else:
                variant = rng.choice((1, 2, 3))
        else:
            variant = rng.randrange(4)
        for r, c in _component_shape(slot, size, variant):
            grid[r][c] = color
    return grid


def _components_by_color(
    grid: list[list[int]],
) -> dict[int, list[set[tuple[int, int]]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: dict[int, list[set[tuple[int, int]]]] = {}
    for start_r in range(h):
        for start_c in range(w):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            component: set[tuple[int, int]] = set()
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            while stack:
                r, c = stack.pop()
                component.add((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.setdefault(color, []).append(component)
    return components


def _first_seen_colors(grid: list[list[int]]) -> list[int]:
    seen: set[int] = set()
    order: list[int] = []
    for row in grid:
        for color in row:
            if color and color not in seen:
                seen.add(color)
                order.append(color)
    return order


def _bars_for_counts(colors: list[int], counts: list[int]) -> list[list[int]]:
    width = max(counts)
    return [
        [color if column < count else 0 for column in range(width)]
        for color, count in zip(colors, counts)
    ]


def _solve_grid(grid: list[list[int]]) -> list[list[int]]:
    components = _components_by_color(grid)
    colors = sorted(components)
    return _bars_for_counts(colors, [len(components[color]) for color in colors])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact AXES value from a returned grid."""
    components = _components_by_color(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_colors": len(components),
        "comp_count": max(len(groups) for groups in components.values()),
        "blob_size": max(
            len(component)
            for groups in components.values()
            for component in groups
        ),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-hiding component-histogram lessons."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"]
    if not (8 <= h <= 10 and 10 <= w <= 12):
        errors.append(f"expected canonical-scale dimensions 8..10x10..12, got {h}x{w}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has invalid ARC color {value!r}")
    if errors:
        return errors

    components = _components_by_color(grid)
    colors = sorted(components)
    if not (2 <= len(colors) <= 3):
        errors.append(f"expected 2..3 non-background colors, got {len(colors)}")
    counts = [len(components[color]) for color in colors]
    if counts and any(count < 1 or count > 3 for count in counts):
        errors.append(f"component counts must be 1..3, got {dict(zip(colors, counts))}")
    if counts and max(counts) not in {2, 3}:
        errors.append(f"largest component count must be 2 or 3, got {max(counts)}")
    if len(counts) > 1 and len(set(counts)) == 1:
        errors.append("component counts must vary across colors")

    component_sizes: list[int] = []
    touching_pairs: set[tuple[tuple[int, int], tuple[int, int]]] = set()
    for color, groups in components.items():
        for component in groups:
            size = len(component)
            component_sizes.append(size)
            if not 1 <= size <= 3:
                errors.append(f"color {color} component has size {size}, expected 1..3")
            for r, c in component:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 0
                        and (nr, nc) not in component
                    ):
                        pair = tuple(sorted(((r, c), (nr, nc))))
                        if pair not in touching_pairs:
                            touching_pairs.add(pair)
                            errors.append(
                                f"component of color {color} touches a different component at ({nr},{nc})"
                            )
    if component_sizes and 1 not in component_sizes:
        errors.append("at least one singleton component is required")
    if component_sizes and not any(size > 1 for size in component_sizes):
        errors.append("at least one multi-cell component is required to refute cell counting")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The teaching grammar is deliberately pinned to the canonical manifold."""
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _has_tied_counts(grid: list[list[int]]) -> bool:
    counts = [len(groups) for groups in _components_by_color(grid).values()]
    return len(counts) != len(set(counts))


def _has_mixed_sizes_within_color(grid: list[list[int]]) -> bool:
    for groups in _components_by_color(grid).values():
        sizes = {len(component) for component in groups}
        if 1 in sizes and any(size > 1 for size in sizes):
            return True
    return False


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "two_color_chart": lambda grid: len(_components_by_color(grid)) == 2,
    "three_color_chart": lambda grid: len(_components_by_color(grid)) == 3,
    "width_two_chart": lambda grid: observe_overrides(grid)["comp_count"] == 2,
    "width_three_chart": lambda grid: observe_overrides(grid)["comp_count"] == 3,
    "tied_component_counts": _has_tied_counts,
    "mixed_blob_sizes_within_color": _has_mixed_sizes_within_color,
    "spatial_order_differs_from_numeric_order": lambda grid: (
        _first_seen_colors(grid) != sorted(_components_by_color(grid))
    ),
}


def _cell_count_rival(grid: list[list[int]]) -> list[list[int]]:
    colors = sorted(_components_by_color(grid))
    counts = [sum(value == color for row in grid for value in row) for color in colors]
    return _bars_for_counts(colors, counts)


def _first_seen_rival(grid: list[list[int]]) -> list[list[int]]:
    components = _components_by_color(grid)
    colors = _first_seen_colors(grid)
    return _bars_for_counts(colors, [len(components[color]) for color in colors])


def _uniform_bar_rival(grid: list[list[int]]) -> list[list[int]]:
    components = _components_by_color(grid)
    colors = sorted(components)
    width = max(len(groups) for groups in components.values())
    return [[color] * width for color in colors]


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons still compatible with named plausible shortcut rules."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    all_pairs = [*demos, query]
    for index, pair in enumerate(all_pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        expected = _solve_grid(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with component-count rule")

    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        "count colored cells instead of components": _cell_count_rival,
        "order rows by first spatial appearance": _first_seen_rival,
        "make every row the maximum bar length": _uniform_bar_rival,
    }
    for name, rival in rivals.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(
                    f"demonstrations leave rival answer-equivalent on this query: {name}"
                )
    return reasons
