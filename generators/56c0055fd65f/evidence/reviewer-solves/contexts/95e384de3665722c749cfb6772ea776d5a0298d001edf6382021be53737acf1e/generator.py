"""Generator for arc_additional_puzzle_bank_volume8:M55.

True rule
---------
For every yellow (4) component, count enclosed 0-background holes and recolor
that whole component by the exact mapping 0 -> red (2), 1 -> green (3),
2 -> cyan (8).  A two-cell magenta (6) domino may appear as a distractor and
must be preserved.

The normal teaching distribution always contains one component from every
rule branch.  Each four-row schedule mixes one canonical-morphology profile
(including the solid 0-hole rectangle) with three profiles whose 0-hole and
1-hole components have the SAME area and bounding box.  Layout slots and
semantic roles are sampled independently, so neither a morphology-only nor a
fixed-position shortcut can replace the authoritative topology rule.
"""
from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "56c0055fd65f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # canonical morphology + layout decoupling + portable tests
RULE_HASH = "d0be87fb4806"

SUMMARY = (
    "Recolor each yellow component by its enclosed-background-hole count: "
    "0 holes -> 2, 1 hole -> 3, 2 holes -> 8; preserve the optional color-6 "
    "domino distractor."
)
INVARIANTS = [
    "the input contains exactly three 4-connected yellow components",
    "their enclosed 0-background hole counts are exactly 0, 1, and 2",
    "profile 0 replays the canonical solid/ring/two-hole morphology",
    "profiles 1..3 pair the 0-hole and 1-hole components at equal area and equal bounding-box dimensions",
    "shape profile does not determine which sampled layout slot receives a semantic branch",
    "the only optional non-background/non-yellow object is one two-cell color-6 domino",
]

_GRID_H_LO, _GRID_H_HI = 11, 18
_GRID_W_LO, _GRID_W_HI = 11, 18

AXES = {
    "grid_h": {
        "type": "int",
        "default": "banded rng with a 25% canonical-profile schedule",
        "valid": "11..18",
    },
    "grid_w": {
        "type": "int",
        "default": "banded rng with a 25% canonical-profile schedule",
        "valid": "11..18",
    },
    "include_distractor": {
        "type": "bool",
        "default": "rng (forced true on canonical-profile schedule draws)",
        "valid": "true|false",
    },
}

# Every boundary combination is supported.  Declaring the empty matrix makes
# any future rejection a checker-visible regression rather than a legacy warn.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = (0, 1, 2, 3)

# Profile 0 mirrors the canonical component morphology.  Profiles 1..3 give
# the 0-hole and 1-hole component the same area and bounding box.  The missing
# cells of their 0-hole shapes reach the exterior; the missing cells of their
# 1-hole shapes are enclosed.
_ZERO_ONE_PAIRS: tuple[
    tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]], ...
] = (
    (
        (
            (1, 1, 1),
            (1, 1, 1),
        ),
        (
            (1, 1, 1),
            (1, 0, 1),
            (1, 1, 1),
        ),
    ),
    (
        (
            (0, 0, 1, 1),
            (1, 1, 1, 1),
            (1, 1, 1, 1),
        ),
        (
            (1, 1, 1, 1),
            (1, 0, 0, 1),
            (1, 1, 1, 1),
        ),
    ),
    (
        (
            (0, 1, 1, 0),
            (1, 1, 1, 1),
            (1, 1, 1, 1),
            (0, 1, 1, 0),
        ),
        (
            (1, 1, 1, 1),
            (1, 0, 0, 1),
            (1, 0, 0, 1),
            (1, 1, 1, 1),
        ),
    ),
    (
        (
            (0, 1, 1, 1, 0),
            (1, 1, 1, 1, 1),
            (1, 1, 1, 1, 0),
        ),
        (
            (1, 1, 1, 1, 1),
            (1, 0, 0, 0, 1),
            (1, 1, 1, 1, 1),
        ),
    ),
)

_TWO_HOLE_PATTERNS: tuple[tuple[tuple[int, ...], ...], ...] = (
    (
        (1, 1, 1, 1, 1),
        (1, 0, 1, 0, 1),
        (1, 1, 1, 1, 1),
    ),
    (
        (1, 1, 1, 1, 1),
        (1, 0, 1, 0, 1),
        (1, 0, 1, 0, 1),
        (1, 1, 1, 1, 1),
    ),
)

_CANONICAL_PROFILES = ((11, 11), (11, 12), (12, 12), (12, 13), (13, 13))


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Four-way morphology schedule; consecutive lesson rows cover 3+1."""
    del seed, difficulty
    return int(sample_index) % 4


def schedule_layout_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Cycle four role layouts with a seed offset, independently of morphology."""
    del difficulty
    return (int(seed) + int(sample_index)) % 4


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid, color: int = 4) -> list[list[tuple[int, int]]]:
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                component.append(current)
                cr, cc = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = cr + dr, cc + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] == color
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append(component)
    return result


def _bbox(component: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(component)
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bbox_dims(component: Iterable[tuple[int, int]]) -> tuple[int, int]:
    r0, c0, r1, c1 = _bbox(component)
    return r1 - r0 + 1, c1 - c0 + 1


def _normalized_shape(component: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = list(component)
    r0, c0, _, _ = _bbox(cells)
    return tuple(sorted((row - r0, col - c0) for row, col in cells))


def _hole_count(component: Iterable[tuple[int, int]]) -> int:
    cells = set(component)
    r0, c0, r1, c1 = _bbox(cells)
    seen: set[tuple[int, int]] = set()
    holes = 0
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            if (row, col) in cells or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            touches_bbox_edge = False
            while stack:
                cr, cc = stack.pop()
                if cr in (r0, r1) or cc in (c0, c1):
                    touches_bbox_edge = True
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nxt = cr + dr, cc + dc
                    if (
                        r0 <= nxt[0] <= r1
                        and c0 <= nxt[1] <= c1
                        and nxt not in cells
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            if not touches_bbox_edge:
                holes += 1
    return holes


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    if not (_GRID_H_LO <= height <= _GRID_H_HI and _GRID_W_LO <= width <= _GRID_W_HI):
        errors.append(
            f"dims {height}x{width} outside declared "
            f"{_GRID_H_LO}..{_GRID_H_HI} x {_GRID_W_LO}..{_GRID_W_HI}"
        )
    palette = {value for row in grid for value in row}
    unsupported = sorted(palette - {0, 4, 6})
    if unsupported:
        errors.append(f"unsupported non-background colors: {unsupported}")

    yellow = _components(grid, 4)
    by_holes: dict[int, list[tuple[int, int]]] = {}
    hole_values: list[int] = []
    for component in yellow:
        holes = _hole_count(component)
        hole_values.append(holes)
        if holes in by_holes:
            errors.append(f"duplicate yellow component with {holes} holes")
        by_holes[holes] = component
    if sorted(hole_values) != [0, 1, 2]:
        errors.append(
            "expected exactly one yellow component with each hole count "
            f"[0, 1, 2], got {sorted(hole_values)}"
        )

    six_cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    include_distractor = bool(six_cells)
    if six_cells:
        if len(six_cells) != 2:
            errors.append(f"color-6 distractor must contain exactly 2 cells, got {len(six_cells)}")
        elif abs(six_cells[0][0] - six_cells[1][0]) + abs(six_cells[0][1] - six_cells[1][1]) != 1:
            errors.append("color-6 distractor cells must form one orthogonal domino")

    equal_area = False
    equal_bbox = False
    if 0 in by_holes and 1 in by_holes:
        equal_area = len(by_holes[0]) == len(by_holes[1])
        equal_bbox = _bbox_dims(by_holes[0]) == _bbox_dims(by_holes[1])

    component_rows = {
        holes: min(row for row, _ in component)
        for holes, component in by_holes.items()
        if component
    }
    position_order = tuple(
        holes for holes, _ in sorted(component_rows.items(), key=lambda item: (item[1], item[0]))
    )
    profile = None
    if 0 in by_holes and 1 in by_holes:
        profile = (
            len(by_holes[0]),
            _bbox_dims(by_holes[0]),
            _normalized_shape(by_holes[0]),
            _normalized_shape(by_holes[1]),
        )

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "palette": palette,
        "components": yellow,
        "by_holes": by_holes,
        "hole_values": sorted(hole_values),
        "include_distractor": include_distractor,
        "equal_area": equal_area,
        "equal_bbox": equal_bbox,
        "position_order": position_order,
        "shape_profile": profile,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed scenes and any scene that hides a rule branch."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """The teaching grammar is a generalized but fully canonical task manifold."""
    return self_check(grid)


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    by_holes = analysis["by_holes"]
    return {
        "grid_shape": [analysis["height"], analysis["width"]],
        "hole_counts": analysis["hole_values"],
        "component_areas": {str(h): len(by_holes[h]) for h in (0, 1, 2)},
        "component_bboxes": {str(h): list(_bbox_dims(by_holes[h])) for h in (0, 1, 2)},
        "component_position_order": list(analysis["position_order"]),
        "equal_area_zero_one": analysis["equal_area"],
        "equal_bbox_zero_one": analysis["equal_bbox"],
        "include_distractor": analysis["include_distractor"],
    }


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "include_distractor": analysis["include_distractor"],
    }


def _rotate(pattern: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in zip(*pattern[::-1]))


def _reflect(pattern: tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(reversed(row)) for row in pattern)


def _variants(pattern: tuple[tuple[int, ...], ...]) -> list[tuple[tuple[int, ...], ...]]:
    variants: list[tuple[tuple[int, ...], ...]] = []
    current = pattern
    for _ in range(4):
        for candidate in (current, _reflect(current)):
            if candidate not in variants:
                variants.append(candidate)
        current = _rotate(current)
    return variants


def _pattern_cells(pattern, top: int, left: int) -> list[tuple[int, int]]:
    return [
        (top + row, left + col)
        for row, values in enumerate(pattern)
        for col, bit in enumerate(values)
        if bit
    ]


def _can_stamp_yellow(grid, cells: Iterable[tuple[int, int]]) -> bool:
    height, width = len(grid), len(grid[0])
    cells = list(cells)
    if any(not (0 <= row < height and 0 <= col < width) for row, col in cells):
        return False
    if any(grid[row][col] != 0 for row, col in cells):
        return False
    cell_set = set(cells)
    for row, col in cells:
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = row + dr, col + dc
            if 0 <= nr < height and 0 <= nc < width and (nr, nc) not in cell_set:
                if grid[nr][nc] == 4:
                    return False
    return True


def _stamp_cells(grid, cells: Iterable[tuple[int, int]], color: int) -> None:
    for row, col in cells:
        grid[row][col] = color


_SLOT_SIZE = 5


def _separated_bands(length: int, rng) -> tuple[tuple[int, int], tuple[int, int]]:
    """Return two five-cell bands with a guaranteed blank separator.

    Extra space is split between the leading margin, the middle gap, and the
    trailing margin.  This keeps placement constructive for every declared
    11..18 override while allowing the whole layout to move away from edges.
    """
    required = 2 * _SLOT_SIZE + 1
    if length < required:
        raise ValueError(f"axis length {length} is smaller than required {required}")
    slack = length - required
    leading = rng.choice(tuple(range(slack + 1)))
    remaining = slack - leading
    gap_extra = rng.choice(tuple(range(remaining + 1)))
    first = leading
    second = first + _SLOT_SIZE + 1 + gap_extra
    return (first, first + _SLOT_SIZE), (second, second + _SLOT_SIZE)


def _place_components(
    grid,
    patterns: dict[int, tuple[tuple[int, ...], ...]],
    profile: int,
    layout_profile: int,
    rng,
) -> None:
    """Place three branches in independently sampled, separated 5x5 slots.

    A 2x2 slot frame always fits the declared minimum grid.  Four role layouts
    cycle independently of the morphology profile, with a seed offset; any
    four-row lesson therefore moves every branch while a fixed morphology can
    occupy every layout across seeds.  Horizontal jitter and movable slot bands
    add variation without losing the bounded constructive placement guarantee.
    """
    height, width = len(grid), len(grid[0])
    row_bands = _separated_bands(height, rng)
    col_bands = _separated_bands(width, rng)
    slots = {
        "top_left": (row_bands[0][0], col_bands[0][0]),
        "top_right": (row_bands[0][0], col_bands[1][0]),
        "bottom_left": (row_bands[1][0], col_bands[0][0]),
        "bottom_right": (row_bands[1][0], col_bands[1][0]),
    }
    role_layouts = (
        {0: "bottom_left", 1: "top_right", 2: "top_left"},
        {0: "top_left", 1: "bottom_right", 2: "top_right"},
        {0: "top_right", 1: "top_left", 2: "bottom_left"},
        {0: "bottom_right", 1: "bottom_left", 2: "top_left"},
    )
    slot_for_holes = {
        holes: slots[name] for holes, name in role_layouts[layout_profile].items()
    }

    # Profile 0 is the literal canonical morphology profile.  The remaining
    # profiles vary orientation while keeping their paired 0/1 transform equal.
    pair_turns = 0 if profile == 0 else rng.choice((0, 1, 2, 3))
    pair_reflected = False if profile == 0 else rng.choice((False, True))

    for holes in (2, 0, 1):
        if holes in (0, 1):
            variant = patterns[holes]
            for _ in range(pair_turns):
                variant = _rotate(variant)
            if pair_reflected:
                variant = _reflect(variant)
        elif profile == 0:
            variant = patterns[holes]
        else:
            variant = rng.choice(_variants(patterns[holes]))

        ph, pw = len(variant), len(variant[0])
        if ph > _SLOT_SIZE or pw > _SLOT_SIZE:
            raise ValueError(f"pattern {ph}x{pw} exceeds {_SLOT_SIZE}x{_SLOT_SIZE} slot")
        slot_top, slot_left = slot_for_holes[holes]
        top = slot_top
        left = slot_left + rng.choice(tuple(range(_SLOT_SIZE - pw + 1)))
        cells = _pattern_cells(variant, top, left)
        if not _can_stamp_yellow(grid, cells):
            raise ValueError(
                f"separated-slot placement failed for {holes}-hole pattern on "
                f"{height}x{width} at slot {(slot_top, slot_left)}"
            )
        _stamp_cells(grid, cells, 4)


def _place_distractor(grid, rng) -> None:
    analysis = _analysis_without_distribution_requirements(grid)
    forbidden: set[tuple[int, int]] = set()
    for component in analysis["components"]:
        r0, c0, r1, c1 = _bbox(component)
        forbidden.update((row, col) for row in range(r0, r1 + 1) for col in range(c0, c1 + 1))
    candidates: list[tuple[tuple[int, int], tuple[int, int]]] = []
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            for dr, dc in ((0, 1), (1, 0)):
                other = row + dr, col + dc
                if other[0] >= height or other[1] >= width:
                    continue
                pair = ((row, col), other)
                if all(grid[r][c] == 0 and (r, c) not in forbidden for r, c in pair):
                    candidates.append(pair)
    if not candidates:
        raise ValueError("could not place the requested color-6 distractor outside yellow holes")
    pair = rng.choice(candidates)
    _stamp_cells(grid, pair, 6)


def _analysis_without_distribution_requirements(grid) -> dict[str, Any]:
    """Internal component parse used while a grid is still being assembled."""
    return {"components": _components(grid, 4)}


def _banded_dimension(ctx, overrides, name: str, lo: int, hi: int, valid_lo: int, valid_hi: int) -> int:
    if name in overrides:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")
    band = difficulty or "medium"
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi = 11, 13, 11, 13
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi = 11, 18, 11, 18
    else:
        h_lo, h_hi, w_lo, w_hi = 11, 15, 11, 15

    canonical_schedule = not overrides and schedule_profile(seed, sample_index, band) == 0
    if canonical_schedule:
        profile_h, profile_w = rng.choice(_CANONICAL_PROFILES)
        height = ctx.draw_int("grid_h", profile_h, profile_h)
        width = ctx.draw_int("grid_w", profile_w, profile_w)
        include_distractor = ctx.draw_choice("include_distractor", (True,))
    else:
        height = _banded_dimension(ctx, overrides, "grid_h", h_lo, h_hi, _GRID_H_LO, _GRID_H_HI)
        width = _banded_dimension(ctx, overrides, "grid_w", w_lo, w_hi, _GRID_W_LO, _GRID_W_HI)
        include_distractor = ctx.draw_choice("include_distractor", (True, False))

    profile = schedule_profile(seed, sample_index, band)
    layout_profile = schedule_layout_profile(seed, sample_index, band)
    zero_pattern, one_pattern = _ZERO_ONE_PAIRS[profile]
    two_pattern = _TWO_HOLE_PATTERNS[0] if profile == 0 else rng.choice(_TWO_HOLE_PATTERNS)
    patterns = {0: zero_pattern, 1: one_pattern, 2: two_pattern}

    grid = full_grid(height, width, 0)
    _place_components(grid, patterns, profile, layout_profile, rng)
    if include_distractor:
        _place_distractor(grid, rng)

    errors = self_check(grid)
    if errors:
        raise ValueError(f"constructed invalid generator scene: {errors}")
    return [row[:] for row in grid]


def _paint_rule(grid, color_for_component) -> list[list[int]]:
    out = [list(row) for row in grid]
    for component in _components(grid, 4):
        color = color_for_component(component)
        if color is None:
            continue
        for row, col in component:
            out[row][col] = color
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Pure Python test mirror; the canonical Racket program remains authority."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    mapping = {0: 2, 1: 3, 2: 8}
    return _paint_rule(grid, lambda component: mapping.get(_hole_count(component)))


def _all_yellow(color: int):
    return lambda grid: _paint_rule(grid, lambda component: color)


def _area_lookup(grid):
    # Fits the canonical morphology: areas 6/8/13 -> 2/3/8.  Generated 0/1
    # components deliberately share area, so one of them must be mislabeled.
    mapping = {6: 2, 8: 3, 13: 8}
    return _paint_rule(grid, lambda component: mapping.get(len(component), 3))


def _bbox_lookup(grid):
    # Fits canonical 2x3 / 3x3 / 3x5 bodies but cannot distinguish generated
    # 0-hole and 1-hole bodies, whose bounding boxes are equal by construction.
    mapping = {(2, 3): 2, (3, 3): 3, (3, 5): 8}
    return _paint_rule(grid, lambda component: mapping.get(_bbox_dims(component), 3))


_CANONICAL_SHAPE_COLORS = {
    tuple((row, col) for row in range(2) for col in range(3)): 2,
    tuple(sorted((row, col) for row in range(3) for col in range(3) if (row, col) != (1, 1))): 3,
    tuple(sorted((row, col) for row in range(3) for col in range(5) if (row, col) not in {(1, 1), (1, 3)})): 8,
}


def _canonical_shape_lookup(grid):
    return _paint_rule(grid, lambda component: _CANONICAL_SHAPE_COLORS.get(_normalized_shape(component)))


SEMANTIC_RIVALS = {
    "all_red": _all_yellow(2),
    "all_green": _all_yellow(3),
    "all_cyan": _all_yellow(8),
    "canonical_area_lookup": _area_lookup,
    "canonical_bbox_lookup": _bbox_lookup,
    "canonical_shape_lookup": _canonical_shape_lookup,
}

CANONICAL_SHORTCUTS = {
    "canonical_area_lookup": _area_lookup,
    "canonical_bbox_lookup": _bbox_lookup,
    "canonical_shape_lookup": _canonical_shape_lookup,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _novel_zero_shape(grid) -> bool:
    analysis = _lawful(grid)
    if analysis is None:
        return False
    return _normalized_shape(analysis["by_holes"][0]) not in _CANONICAL_SHAPE_COLORS


SEMANTIC_WITNESSES = {
    "zero_hole_branch": lambda grid: (analysis := _lawful(grid)) is not None and 0 in analysis["by_holes"],
    "one_hole_branch": lambda grid: (analysis := _lawful(grid)) is not None and 1 in analysis["by_holes"],
    "two_hole_branch": lambda grid: (analysis := _lawful(grid)) is not None and 2 in analysis["by_holes"],
    "equal_area_zero_one": lambda grid: (analysis := _lawful(grid)) is not None and analysis["equal_area"],
    "equal_bbox_zero_one": lambda grid: (analysis := _lawful(grid)) is not None and analysis["equal_bbox"],
    "novel_zero_hole_shape": _novel_zero_shape,
}

WITNESS_RIVALS = {
    "zero_hole_branch": ["all_green", "all_cyan"],
    "one_hole_branch": ["all_red", "all_cyan"],
    "two_hole_branch": ["all_red", "all_green"],
    "equal_area_zero_one": ["canonical_area_lookup"],
    "equal_bbox_zero_one": ["canonical_bbox_lookup"],
    "novel_zero_hole_shape": ["canonical_shape_lookup"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require branch-complete demos, varied profiles, and an unseen query form."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    demo_profiles = []
    demo_orders = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        analysis = _lawful(demo["input"])
        if analysis is None:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        truth = rule_mirror(demo["input"])
        if demo["output"] != truth:
            reasons.append(f"demo {index} output disagrees with the hole-count rule")
        demo_profiles.append(analysis["shape_profile"])
        demo_orders.append(analysis["position_order"])

    query_analysis = _lawful(query["input"])
    if query_analysis is None:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    query_truth = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != query_truth:
        reasons.append("query output disagrees with the hole-count rule")

    if len(set(demo_profiles)) < EXAMPLES_NEEDED:
        reasons.append("demonstrations do not expose three distinct same-area shape profiles")
    if query_analysis["shape_profile"] in set(demo_profiles):
        reasons.append("query repeats a demonstrated raw-shape profile; template lookup remains viable")
    if len(set(demo_orders)) < 2:
        reasons.append("demonstrations do not move hole-count roles between positions")

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives:
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"competing rule {name!r} matches every demo but predicts a different query"
                )
            else:
                reasons.append(
                    f"competing rule {name!r} survives every demo and the query; lesson is not discriminating"
                )
    return reasons


def mutation_fixtures() -> list[tuple[str, list[list[int]]]]:
    """Named structural impostors that self_check must reject."""
    base = generate(77123, 5, difficulty="medium", include_distractor=False)
    analysis = _analysis(base)

    missing_zero = deepcopy(base)
    for row, col in analysis["by_holes"][0]:
        missing_zero[row][col] = 0

    filled_one_hole = deepcopy(base)
    one = analysis["by_holes"][1]
    r0, c0, r1, c1 = _bbox(one)
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            if filled_one_hole[row][col] == 0:
                filled_one_hole[row][col] = 4

    malformed_distractor = deepcopy(base)
    zero_cell = next(
        (row, col)
        for row in range(len(base))
        for col in range(len(base[0]))
        if base[row][col] == 0
    )
    malformed_distractor[zero_cell[0]][zero_cell[1]] = 6

    unsupported_color = deepcopy(base)
    zero_cell_2 = next(
        (row, col)
        for row in range(len(base) - 1, -1, -1)
        for col in range(len(base[0]) - 1, -1, -1)
        if base[row][col] == 0
    )
    unsupported_color[zero_cell_2[0]][zero_cell_2[1]] = 5

    duplicate_zero = deepcopy(base)
    extra_cells = None
    for row in range(len(base)):
        for col in range(len(base[0]) - 1):
            candidate = [(row, col), (row, col + 1)]
            if _can_stamp_yellow(duplicate_zero, candidate):
                extra_cells = candidate
                break
        if extra_cells is not None:
            break
    if extra_cells is None:
        raise AssertionError("fixture setup could not place an extra component")
    _stamp_cells(duplicate_zero, extra_cells, 4)

    return [
        ("missing_zero_hole_branch", missing_zero),
        ("filled_one_hole", filled_one_hole),
        ("single_cell_distractor", malformed_distractor),
        ("unsupported_color", unsupported_color),
        ("duplicate_zero_hole_branch", duplicate_zero),
    ]
