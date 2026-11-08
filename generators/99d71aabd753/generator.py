"""Generator for ARC task 2753e76c / canonical task 99d71aabd753.

Rule: count the 4-connected non-zero objects of each color, sort colors by
object count descending, and emit a right-aligned staircase whose row lengths
are those counts.  The output height is the number of colors and its width is
the largest object count.

The ordinary distribution deliberately varies rectangle area independently of
object count.  In particular, every ordinary draw makes the cell-count ranking
disagree with the object-count ranking, so a learner cannot solve the lessons
by counting colored cells instead of connected components.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from math import ceil, sqrt
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99d71aabd753"
TASK_ID = "99d71aabd753"
VERSION = "2.0.0"
RULE_HASH = "a6f4f8240a92"

SUMMARY = (
    "Place 3-4 ordinary-draw colors as separated solid rectangles on a zero "
    "background. Each color has a distinct number of 4-connected objects. "
    "Rectangle areas vary independently of those counts, and the colored-cell "
    "ranking conflicts with the object-count ranking. The Racket rule counts "
    "objects per color, sorts counts descending, and emits a right-aligned "
    "staircase with one row per color."
)
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0 and separates every pair of objects by an 8-neighbor gap",
    "ordinary draws use 3-4 non-zero colors; exact overrides support 2-5",
    "component counts are distinct and the largest count is 2-7",
    "every object is a solid axis-aligned rectangle",
    "ordinary draws contain multiple rectangle areas and refute cell counting",
]

# Only expose axes whose exact realized values are recoverable from the grid.
# The previous palette/shape/position/texture declarations were distributional
# knobs or aliases, not exact observable contracts; accepting them caused silent
# precedence, clamping, and thousands of override-contract failures.
AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware, capacity-aware draw",
        "valid": "10..22",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware, capacity-aware draw",
        "valid": "10..22",
    },
    "n_colors": {
        "type": "int",
        "default": "3..4",
        "valid": "2..5",
    },
    "max_count": {
        "type": "int",
        "default": "4..6, with room for a nonconsecutive count profile",
        "valid": "2..7",
    },
}

# The ordinary generator is intentionally 100% inside this task-linked grammar.
MIN_STRICT_FRAC = 1.0

# Solid rectangle dimensions by area.  Shapes stay small enough for dense
# boundary overrides, but include both orientations and canonical-style blocks.
_RECT_DIMS: dict[int, tuple[tuple[int, int], ...]] = {
    1: ((1, 1),),
    2: ((1, 2), (2, 1)),
    3: ((1, 3), (3, 1)),
    4: ((2, 2), (1, 4), (4, 1)),
    6: ((2, 3), (3, 2)),
    25: ((5, 5),),
}


def _validate_override_names(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(
            "unknown override axis/axes: " + ", ".join(repr(x) for x in unknown)
        )


def _draw_count_axes(ctx, overrides: dict[str, Any]) -> tuple[int, int]:
    """Draw an exact feasible (n_colors, max_count) pair.

    A single boundary override must remain usable.  Therefore the unpinned
    partner is drawn from a feasible range rather than drawn broadly and then
    silently clamped.  An explicitly incompatible pair rejects loudly.
    """
    n_explicit = overrides.get("n_colors") is not None
    m_explicit = overrides.get("max_count") is not None

    if n_explicit:
        n_colors = ctx.draw_int("n_colors", 2, 5)
    else:
        n_colors = None
    if m_explicit:
        max_count = ctx.draw_int("max_count", 2, 7)
    else:
        max_count = None

    if n_colors is not None and max_count is not None:
        if n_colors > max_count:
            raise ValueError(
                "n_colors cannot exceed max_count when counts must be distinct "
                f"positive integers: {n_colors} > {max_count}"
            )
        return n_colors, max_count

    if n_colors is not None:
        # Keep a single n_colors override valid at both boundaries.
        lo = max(2, n_colors)
        hi = min(7, max(lo, n_colors + 2))
        max_count = ctx.draw_int_diff("max_count", lo, hi)
        return n_colors, max_count

    if max_count is not None:
        # A single max_count=2 override necessarily implies two colors.
        hi = min(5, max_count)
        lo = 2 if hi == 2 else 3
        n_colors = ctx.draw_int_diff("n_colors", lo, hi)
        return n_colors, max_count

    n_colors = ctx.draw_int("n_colors", 3, 4)
    # Every band must exercise both the narrow (width 4) and broad (width
    # 5-6) chart branches.  Difficulty still controls canvas size, while the
    # semantic target distribution stays comparable across bands.
    max_count = ctx.draw_int("max_count", max(n_colors + 1, 4), 6)
    return n_colors, max_count


def _draw_dimension(
    ctx,
    label: str,
    *,
    minimum_for_plan: int,
    overrides: dict[str, Any],
) -> int:
    if overrides.get(label) is not None:
        return ctx.draw_int(label, 10, 22)
    if ctx.difficulty == "easy":
        # Easy is the explicit canonical-scale anchor.  The public task uses
        # 16x16 inputs, so keeping this band at 16x16 gives downstream models
        # substantial exact-profile support rather than a token 1/60 hit.
        return ctx.draw_int(label, 16, 16)
    if ctx.difficulty == "hard":
        default_lo, default_hi = 18, 22
    else:
        default_lo, default_hi = 15, 20
    lo = min(22, max(default_lo, minimum_for_plan))
    # The band-specific bounds already encode difficulty.  A second
    # draw_int_diff skew would collapse the intended dimensional support.
    return ctx.draw_int(label, lo, default_hi if default_hi >= lo else lo)


def _build_palette(rng, n_colors: int) -> list[int]:
    palette = list(range(1, 10))
    rng.shuffle(palette)
    return palette[:n_colors]


def _build_counts(
    rng,
    palette: list[int],
    max_count: int,
    *,
    require_gap: bool,
) -> dict[int, int]:
    """Return color -> distinct positive count with the requested maximum.

    Every feasible count profile requires at least one skipped count so the
    output cannot be reconstructed from row rank and maximum width alone. Exact
    count overrides retain their boundary contract when a gap is mathematically
    impossible (``max_count == n_colors``).
    """
    n_colors = len(palette)
    candidates: list[tuple[int, ...]] = []
    for lower in combinations(range(1, max_count), n_colors - 1):
        values = tuple(sorted((*lower, max_count), reverse=True))
        has_gap = any(
            upper - lower_value > 1
            for upper, lower_value in zip(values, values[1:])
        )
        if not require_gap or has_gap:
            candidates.append(values)
    if not candidates:
        raise ValueError(
            "cannot realize the requested distinct count profile"
            + (" with a skipped count" if require_gap else "")
            + f": n_colors={n_colors}, max_count={max_count}"
        )
    values = list(rng.choice(candidates))
    rng.shuffle(values)
    return dict(zip(palette, values))


def _count_order(mapping: dict[int, int]) -> list[int]:
    return sorted(mapping, key=lambda color: mapping[color], reverse=True)


def _plan_areas(
    rng,
    palette: list[int],
    counts: dict[int, int],
    *,
    strong_semantics: bool,
) -> dict[int, list[int]]:
    """Choose per-object rectangle areas.

    Ordinary draws receive a guaranteed object-count/cell-count disagreement.
    Explicit boundary draws still use mixed rectangles when feasible, but may
    use a denser plan to honor difficult dimensions and counts.
    """
    by_color: dict[int, list[int]] = {}
    for color in palette:
        count = counts[color]
        areas = [rng.choice((1, 2, 3, 4)) for _ in range(count)]
        by_color[color] = areas

    order = _count_order(counts)
    if strong_semantics:
        # Make the largest-object-count color cell-light and inflate a randomly
        # selected lower-ranked color.  The inflated rank varies independently
        # of numeric color and first position, avoiding a fixed surrogate.
        top = order[0]
        by_color[top] = [1] * counts[top]
        inflated = rng.choice(order[1:])
        by_color[inflated] = [
            25 if i == 0 else rng.choice((3, 4, 6))
            for i in range(counts[inflated])
        ]
        # Guarantee at least one horizontal and one vertical non-singleton by
        # controlling dimensions later, not by changing the observable areas.
    else:
        # Dense override cases: retain at least two areas whenever there are
        # multiple objects, but bias toward compact shapes.
        all_slots = [(c, i) for c in palette for i in range(len(by_color[c]))]
        for c, i in all_slots:
            by_color[c][i] = 1
        if len(all_slots) >= 2:
            c, i = all_slots[-1]
            by_color[c][i] = 2
    return by_color


def _shape_for_area(area: int, rng, orientation_counter: list[int]) -> tuple[int, int]:
    options = list(_RECT_DIMS[area])
    if len(options) == 1:
        return options[0]
    # Ordinary plans should expose both horizontal and vertical rectangles.
    # Alternate the first two non-square choices, then randomize.
    if orientation_counter[0] < 2:
        choice = options[orientation_counter[0] % len(options)]
        orientation_counter[0] += 1
        return choice
    return rng.choice(options)


def _component_plan(
    rng,
    palette: list[int],
    counts: dict[int, int],
    areas: dict[int, list[int]],
) -> list[tuple[int, int, int]]:
    plan: list[tuple[int, int, int]] = []
    orientation_counter = [0]
    for color in palette:
        assert len(areas[color]) == counts[color]
        for area in areas[color]:
            rh, rw = _shape_for_area(area, rng, orientation_counter)
            plan.append((color, rh, rw))
    # Large rectangles first makes greedy packing much more reliable.
    plan.sort(key=lambda item: item[1] * item[2], reverse=True)
    return plan


def _candidate_positions(h: int, w: int, rh: int, rw: int) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r in range(h - rh + 1)
        for c in range(w - rw + 1)
    ]


def _try_place(
    h: int,
    w: int,
    plan: list[tuple[int, int, int]],
    rng,
) -> list[list[int]] | None:
    """Greedily place rectangles with a one-cell Chebyshev moat."""
    g = full_grid(h, w, 0)
    forbidden: set[tuple[int, int]] = set()
    for color, rh, rw in plan:
        positions = _candidate_positions(h, w, rh, rw)
        rng.shuffle(positions)
        placed = False
        for r0, c0 in positions:
            cells = {
                (r0 + dr, c0 + dc)
                for dr in range(rh)
                for dc in range(rw)
            }
            if cells & forbidden:
                continue
            for r, c in cells:
                g[r][c] = color
            for r, c in cells:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            forbidden.add((nr, nc))
            placed = True
            break
        if not placed:
            return None
    return g


def _place_plan(
    h: int,
    w: int,
    plan: list[tuple[int, int, int]],
    rng,
) -> list[list[int]] | None:
    for _ in range(80):
        placed = _try_place(h, w, plan, rng)
        if placed is not None:
            return placed
    return None


def _dense_fallback(
    h: int,
    w: int,
    palette: list[int],
    counts: dict[int, int],
    rng,
) -> list[list[int]]:
    """Always-valid exact-count fallback for hostile boundary combinations.

    Most objects are isolated single cells on a stride-2 lattice.  One domino
    is included when capacity allows, preserving area variation without
    changing any component count.  This path is only used after mixed-rectangle
    packing fails; ordinary draws are checked to never need it.
    """
    anchors = [(r, c) for r in range(0, h, 2) for c in range(0, w, 2)]
    need = sum(counts.values())
    if len(anchors) < need:
        raise ValueError(
            f"requested {need} separated objects do not fit in {h}x{w}"
        )
    rng.shuffle(anchors)
    g = full_grid(h, w, 0)
    entries: list[int] = []
    for color in palette:
        entries.extend([color] * counts[color])
    rng.shuffle(entries)
    for color, (r, c) in zip(entries, anchors):
        g[r][c] = color

    # Turn one isolated singleton into a domino only when its right neighbor
    # and moat remain free.  Counts stay exact because the added cell is 4-adjacent.
    for r, c in anchors:
        if g[r][c] == 0 or c + 1 >= w or g[r][c + 1] != 0:
            continue
        safe = True
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c), min(w, c + 3)):
                if (rr, cc) != (r, c) and g[rr][cc] != 0:
                    safe = False
        if safe:
            g[r][c + 1] = g[r][c]
            break
    return g


def _first_seen_colors(grid: list[list[int]]) -> list[int]:
    out: list[int] = []
    for row in grid:
        for value in row:
            if value != 0 and value not in out:
                out.append(value)
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_override_names(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    n_colors, max_count = _draw_count_axes(ctx, overrides)
    layout_rng = ctx.draw_rng("layout")
    palette = _build_palette(layout_rng, n_colors)

    ordinary = not overrides
    counts = _build_counts(
        layout_rng,
        palette,
        max_count,
        # A dimension-only override must not weaken the count lesson. A skipped
        # count is feasible exactly when max_count exceeds the number of colors.
        require_gap=max_count > n_colors,
    )

    areas = _plan_areas(
        layout_rng,
        palette,
        counts,
        strong_semantics=ordinary,
    )
    plan = _component_plan(layout_rng, palette, counts, areas)

    # Approximate a safe side from the number of isolated rectangles.  Explicit
    # dimensions remain exact; only unpinned defaults use this capacity floor.
    min_side = min(22, max(10, 2 * ceil(sqrt(len(plan))) + 4))
    h = _draw_dimension(
        ctx, "grid_h", minimum_for_plan=min_side, overrides=overrides
    )
    w = _draw_dimension(
        ctx, "grid_w", minimum_for_plan=min_side, overrides=overrides
    )

    # Retry complete layouts.  For ordinary draws, also require first-seen order
    # to disagree with count order so a reading-order shortcut is falsified.
    target_order = _count_order(counts)
    for _ in range(40):
        grid = _place_plan(h, w, plan, layout_rng)
        if grid is None:
            break
        if ordinary and _first_seen_colors(grid) == target_order:
            continue
        errors = self_check(grid)
        if not errors:
            if ordinary and not _ordinary_semantics_hold(grid):
                continue
            return grid

    fallback = _dense_fallback(h, w, palette, counts, layout_rng)
    errors = self_check(fallback)
    if errors:
        raise ValueError("fallback violated generator grammar: " + "; ".join(errors))
    if ordinary:
        # Ordinary draws must never silently weaken into the boundary fallback.
        raise RuntimeError(
            "ordinary mixed-rectangle layout failed; refusing a shortcut-prone fallback"
        )
    return fallback


def _components_by_color(
    grid: list[list[int]],
) -> dict[int, list[set[tuple[int, int]]]]:
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen: set[tuple[int, int]] = set()
    result: dict[int, list[set[tuple[int, int]]]] = defaultdict(list)
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            component: set[tuple[int, int]] = set()
            stack = [(sr, sc)]
            seen.add((sr, sc))
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
            result[color].append(component)
    return dict(result)


def _is_solid_rectangle(component: set[tuple[int, int]]) -> bool:
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    return len(component) == (r1 - r0 + 1) * (c1 - c0 + 1)


def _has_object_gap(grid: list[list[int]], components: dict[int, list[set]]) -> bool:
    owner: dict[tuple[int, int], tuple[int, int]] = {}
    for color, groups in components.items():
        for index, component in enumerate(groups):
            for cell in component:
                owner[cell] = (color, index)
    h, w = len(grid), len(grid[0])
    for (r, c), marker in owner.items():
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w:
                    other = owner.get((nr, nc))
                    if other is not None and other != marker:
                        return False
    return True


def _component_counts(grid: list[list[int]]) -> dict[int, int]:
    return {
        color: len(groups)
        for color, groups in _components_by_color(grid).items()
    }


def _cell_counts(grid: list[list[int]]) -> dict[int, int]:
    counts: dict[int, int] = defaultdict(int)
    for row in grid:
        for value in row:
            if value:
                counts[value] += 1
    return dict(counts)


def observe_overrides(grid) -> dict[str, int]:
    components = _components_by_color(grid)
    counts = {color: len(groups) for color, groups in components.items()}
    return {
        "n_colors": len(components),
        "max_count": max(counts.values(), default=0),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the structural teaching grammar, not merely ARC shape/palette."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and non-empty"]
    h = len(grid)
    if not (10 <= h <= 22 and 10 <= width <= 22):
        return [f"grid dimensions must be 10..22, got {h}x{width}"]
    bad = [
        value
        for row in grid
        for value in row
        if not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
    ]
    if bad:
        return [f"grid contains invalid ARC colors: {sorted(set(map(repr, bad)))}"]

    components = _components_by_color(grid)
    errors: list[str] = []
    n_colors = len(components)
    if not (2 <= n_colors <= 5):
        errors.append(f"expected 2..5 non-zero colors, found {n_colors}")
    counts = {color: len(groups) for color, groups in components.items()}
    values = list(counts.values())
    if values:
        if len(set(values)) != len(values):
            errors.append(f"component counts must be distinct, got {counts}")
        if min(values) < 1 or max(values) > 7:
            errors.append(f"component counts must lie in 1..7, got {counts}")
        if max(values) < 2:
            errors.append("at least one color must have multiple objects")
    if 0 not in {value for row in grid for value in row}:
        errors.append("background color 0 must be present")
    if sum(value == 0 for row in grid for value in row) <= h * width // 2:
        errors.append("background must occupy a strict majority of the grid")

    for color, groups in components.items():
        for index, component in enumerate(groups):
            if not _is_solid_rectangle(component):
                errors.append(
                    f"color {color} object {index} is not a solid rectangle"
                )
    if components and not _has_object_gap(grid, components):
        errors.append("distinct objects must have a one-cell 8-neighbor background gap")
    return errors


def strict_canonical_like(grid) -> list[str]:
    reasons = self_check(grid)
    if reasons:
        return reasons
    components = _components_by_color(grid)
    if not (3 <= len(components) <= 4):
        reasons.append(
            f"ordinary/canonical manifold uses 3..4 colors, found {len(components)}"
        )
    areas = {
        len(component)
        for groups in components.values()
        for component in groups
    }
    if len(areas) < 2:
        reasons.append("canonical-like scenes need at least two rectangle areas")
    return reasons


def _ordinary_semantics_hold(grid: list[list[int]]) -> bool:
    if strict_canonical_like(grid):
        return False
    object_counts = _component_counts(grid)
    cell_counts = _cell_counts(grid)
    object_order = sorted(object_counts, key=object_counts.get, reverse=True)
    cell_order = sorted(cell_counts, key=cell_counts.get, reverse=True)
    if object_order == cell_order:
        return False
    if object_order == _first_seen_colors(grid):
        return False
    return True


def _witness_three_colors(grid) -> bool:
    return len(_components_by_color(grid)) == 3


def _witness_four_colors(grid) -> bool:
    return len(_components_by_color(grid)) == 4


def _witness_low_width(grid) -> bool:
    return max(_component_counts(grid).values(), default=0) <= 4


def _witness_high_width(grid) -> bool:
    return max(_component_counts(grid).values(), default=0) >= 5


def _witness_nonconsecutive_counts(grid) -> bool:
    values = sorted(_component_counts(grid).values(), reverse=True)
    return any(upper - lower > 1 for upper, lower in zip(values, values[1:]))


def _witness_cell_count_conflict(grid) -> bool:
    object_counts = _component_counts(grid)
    cell_counts = _cell_counts(grid)
    return sorted(object_counts, key=object_counts.get, reverse=True) != sorted(
        cell_counts, key=cell_counts.get, reverse=True
    )


def _witness_first_seen_conflict(grid) -> bool:
    object_counts = _component_counts(grid)
    return sorted(
        object_counts, key=object_counts.get, reverse=True
    ) != _first_seen_colors(grid)


def _witness_color_order_conflict(grid) -> bool:
    object_counts = _component_counts(grid)
    return sorted(object_counts, key=object_counts.get, reverse=True) != sorted(
        object_counts
    )


def _witness_mixed_rectangle_areas(grid) -> bool:
    areas = {
        len(component)
        for groups in _components_by_color(grid).values()
        for component in groups
    }
    return len(areas) >= 2


SEMANTIC_WITNESSES = {
    "three_colors": _witness_three_colors,
    "four_colors": _witness_four_colors,
    "output_width_at_most_4": _witness_low_width,
    "output_width_at_least_5": _witness_high_width,
    "nonconsecutive_count_profile": _witness_nonconsecutive_counts,
    "cell_count_ranking_conflicts": _witness_cell_count_conflict,
    "first_seen_order_conflicts": _witness_first_seen_conflict,
    "numeric_color_order_conflicts": _witness_color_order_conflict,
    "mixed_rectangle_areas": _witness_mixed_rectangle_areas,
}


def _chart_output(
    grid: list[list[int]],
    *,
    measure: str = "objects",
    order: str = "descending",
    alignment: str = "right",
) -> list[list[int]]:
    """Python test mirror for ambiguity checks; never used as output authority."""
    if measure == "objects":
        values = _component_counts(grid)
    elif measure == "cells":
        values = _cell_counts(grid)
    else:
        raise ValueError(measure)

    if order == "descending":
        colors = sorted(values, key=values.get, reverse=True)
    elif order == "ascending":
        colors = sorted(values, key=values.get)
    elif order == "numeric":
        colors = sorted(values)
    elif order == "first_seen":
        colors = _first_seen_colors(grid)
    else:
        raise ValueError(order)

    width = max(values.values())
    output: list[list[int]] = []
    for color in colors:
        count = values[color]
        if alignment == "right":
            output.append([0] * (width - count) + [color] * count)
        elif alignment == "left":
            output.append([color] * count + [0] * (width - count))
        else:
            raise ValueError(alignment)
    return output


def _rank_step_output(grid: list[list[int]]) -> list[list[int]]:
    """Shortcut rival: use true rank/max but assume each row shrinks by one."""
    values = _component_counts(grid)
    colors = sorted(values, key=values.get, reverse=True)
    width = max(values.values())
    return [
        [0] * rank + [color] * (width - rank)
        for rank, color in enumerate(colors)
    ]


_CANDIDATE_RULES = {
    "count_cells": lambda g: _chart_output(g, measure="cells"),
    "sort_ascending": lambda g: _chart_output(g, order="ascending"),
    "sort_numeric_colors": lambda g: _chart_output(g, order="numeric"),
    "sort_first_seen": lambda g: _chart_output(g, order="first_seen"),
    "left_align": lambda g: _chart_output(g, alignment="left"),
    "rank_step_lengths": _rank_step_output,
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible shortcut changes the query answer.

    The official demo outputs come from the Racket bridge in the semantic gate.
    This helper only checks whether common rival rules survive all demos.
    """
    reasons: list[str] = []
    for name, candidate in _CANDIDATE_RULES.items():
        try:
            matches_all = all(candidate(pair["input"]) == pair["output"] for pair in demos)
            if not matches_all:
                continue
            candidate_query = candidate(query["input"])
        except Exception as exc:
            reasons.append(f"candidate {name} raised {type(exc).__name__}: {exc}")
            continue
        if candidate_query != query["output"]:
            reasons.append(
                f"candidate {name} matches every demonstration but predicts a different query answer"
            )
    return reasons
