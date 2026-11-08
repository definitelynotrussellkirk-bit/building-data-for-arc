"""Generator for ARC task 3e0aef964b9e.

A two-colour scene contains several same-colour convex-hull objects and a
second-colour donor.  Exactly one target object has as many background cells
inside its convex hull as there are donor-colour cells in the whole grid.  The
answer erases every donor cell and paints that selected convex-hull gap with
the donor colour.

Version 3.1 retains the three-profile curriculum and adds hull-preserving
side gaps.  Those gaps distinguish true convex-hull completion from horizontal
row interpolation in every three-demo lesson, including query rotations.
Connected and disconnected donors, sparse canonical-scale objects, larger
decoys, and both colour-role orders remain in the sampling support.
"""
from __future__ import annotations

from collections import Counter, deque
from copy import deepcopy
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3e0aef964b9e"
TASK_ID = "3e0aef964b9e"
VERSION = "3.1.0"
RULE_HASH = "cac0ce22f2ed"

SUMMARY = (
    "A strict-mode background surrounds two non-background colours. One colour "
    "forms two or three separated convex-hull objects; exactly one object has "
    "K background cells inside its convex hull. The other colour contributes "
    "exactly K donor cells, which may be connected, scattered, or mixed. Erase "
    "all donor cells and fill only the matching object's convex-hull gap. A "
    "three-profile schedule varies donor connectivity, hull geometry, object "
    "size, and colour-role order. Dense profiles include a side gap outside "
    "horizontal row spans, so a canonical-fitting interpolation shortcut is "
    "contradicted even after any one pair is held out."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = (0, 1, 2)

INVARIANTS = [
    "the background is the unique modal colour and exactly two other colours occur",
    "one target colour forms a candidate plus one or two separated decoy objects",
    "exactly one object across both colour-role directions has a positive convex-hull gap equal to the donor-cell count",
    "the answer clears every donor cell and fills exactly the selected gap",
    "scheduled lessons vary donor connectivity, hull geometry, object size, and colour-role order",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "deterministic broad schedule with canonical 13/15/16 support",
        "valid": "13..24",
    },
    "grid_w": {
        "type": "int",
        "default": "deterministic broad schedule with canonical 13/15/16 support",
        "valid": "13..24",
    },
    "n_holes": {
        "type": "int",
        "default": "scheduled 1..6",
        "valid": "1..6",
    },
    "n_decoys": {
        "type": "int",
        "default": "scheduled 1|2",
        "valid": "1..2",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[tuple[str, ...]] = []
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}
_BOUNDS = {
    "grid_h": (13, 24),
    "grid_w": (13, 24),
    "n_holes": (1, 6),
    "n_decoys": (1, 2),
}

# Six-step hole cycle is aligned with the three semantic profiles:
# profile 0 gets 2/4 (connected), profile 1 gets 1/5 (scattered), and
# profile 2 gets 3/6 (mixed).  Thus every default connected/mixed profile has
# enough cells to expose donor connectivity while all exact overrides remain
# constructive.
_HOLE_CYCLE = (2, 1, 3, 4, 5, 6)
_DECOY_CYCLE = (2, 1)
_HEIGHT_CYCLES = {
    "easy": (13, 15, 16, 14, 17, 18, 19, 20, 21, 22, 23, 24),
    "medium": (16, 13, 15, 18, 14, 20, 17, 22, 19, 24, 21, 23),
    "hard": (15, 16, 13, 24, 23, 22, 21, 20, 19, 18, 17, 14),
}
_WIDTH_CYCLES = {
    "easy": (13, 16, 15, 14, 18, 17, 20, 19, 22, 21, 24, 23),
    "medium": (16, 15, 13, 19, 14, 21, 17, 23, 18, 24, 20, 22),
    "hard": (15, 13, 16, 24, 22, 23, 20, 21, 18, 19, 14, 17),
}

# Mandatory 8-connected outlines in a 5x5 local box.  Candidate cells are the
# complete convex-hull fill minus K selected holes; keeping the mandatory
# outline preserves the intended hull under every legal K.
_RECT_OUTLINE = frozenset(
    (r, c)
    for r in range(5)
    for c in range(5)
    if r in (0, 4) or c in (0, 4)
)
_CLIPPED_OUTLINE = frozenset(
    {(0, 1), (0, 2), (0, 3), (4, 1), (4, 2), (4, 3)}
    | {(r, c) for r in range(1, 4) for c in (0, 4)}
)
_DIAMOND_OUTLINE = frozenset(
    {(0, 2), (1, 1), (1, 3), (2, 0), (2, 4), (3, 1), (3, 3), (4, 2)}
)
_PROFILE_SHAPE = {0: "rectangle", 1: "clipped", 2: "diamond"}

# 8-connected but entirely 4-disconnected templates.  Their convex-hull gap
# counts are exact, so they reproduce the canonical task's diagonal-object
# scale instead of teaching only dense framed objects.
_SPARSE_TEMPLATES = {
    1: frozenset({(0, 0), (0, 2), (1, 1)}),
    2: frozenset({(0, 0), (1, 1), (2, 0)}),
    3: frozenset({(0, 2), (1, 1), (1, 3)}),
    4: frozenset({(0, 0), (0, 4), (1, 1), (1, 3), (2, 2)}),
    5: frozenset({(0, 2), (1, 1), (1, 3), (2, 0)}),
    6: frozenset({(0, 0), (0, 4), (1, 1), (1, 3), (2, 0), (2, 2)}),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the finite semantic-role schedule state for one sample."""
    del seed
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _validate_controls(seed, sample_index, difficulty, overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer (not bool)")
        lo, hi = _BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside {lo}..{hi}")


def _scheduled_int(ctx, name: str, scheduled: int) -> int:
    """Consume an exact override or record a deterministic lawful default."""
    lo, hi = _BOUNDS[name]
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _cross(origin, first, second):
    return (
        (first[0] - origin[0]) * (second[1] - origin[1])
        - (first[1] - origin[1]) * (second[0] - origin[0])
    )


def _convex_hull(points: Iterable[tuple[float, float]]):
    """Monotone-chain hull matching the Racket prelude's <=0 trimming."""
    ordered = sorted(set(points))
    if len(ordered) <= 1:
        return ordered

    def half(sequence):
        result = []
        for point in sequence:
            while len(result) >= 2 and _cross(result[-2], result[-1], point) <= 0:
                result.pop()
            result.append(point)
        return result

    lower = half(ordered)
    upper = half(reversed(ordered))
    return lower[:-1] + upper[:-1]


def _point_in_hull(row: int, col: int, hull) -> bool:
    """Ray-casting predicate matching arc-prelude.rkt point-in-hull?."""
    inside = False
    previous = len(hull) - 1
    for current in range(len(hull)):
        ri, ci = hull[current]
        rj, cj = hull[previous]
        if (ci > col) != (cj > col):
            crossing_row = ri + (rj - ri) * (col - ci) / (cj - ci)
            if float(row) < crossing_row:
                inside = not inside
        previous = current
    return inside


def _convex_hull_cells(cells: Iterable[tuple[int, int]]) -> set[tuple[int, int]]:
    """Return cell centres inside the pixel-corner-expanded convex hull."""
    points = tuple(cells)
    if len(points) < 3:
        return set()
    expanded = []
    for row, col in points:
        expanded.extend(
            (
                (row - 0.5, col - 0.5),
                (row - 0.5, col + 0.5),
                (row + 0.5, col - 0.5),
                (row + 0.5, col + 0.5),
            )
        )
    hull = _convex_hull(expanded)
    min_row = min(row for row, _ in points)
    max_row = max(row for row, _ in points)
    min_col = min(col for _, col in points)
    max_col = max(col for _, col in points)
    return {
        (row, col)
        for row in range(min_row, max_row + 1)
        for col in range(min_col, max_col + 1)
        if _point_in_hull(row, col, hull)
    }


def _components_for_color(grid, color: int) -> list[tuple[tuple[int, int], ...]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            row, col = queue.popleft()
            cells.append((row, col))
            for drow in (-1, 0, 1):
                for dcol in (-1, 0, 1):
                    if drow == 0 and dcol == 0:
                        continue
                    neighbor = (row + drow, col + dcol)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        queue.append(neighbor)
        components.append(tuple(sorted(cells)))
    return sorted(components, key=lambda cells: cells[0])


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a non-empty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be non-empty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["grid cells must be integer ARC colours 0..9"]
    height = len(grid)
    errors = []
    if not 13 <= height <= 24:
        errors.append(f"grid height must be 13..24, got {height}")
    if not 13 <= width <= 24:
        errors.append(f"grid width must be 13..24, got {width}")
    return errors


def _component_missing(grid, background: int, component) -> tuple[tuple[int, int], ...]:
    return tuple(
        sorted(
            cell
            for cell in _convex_hull_cells(component)
            if grid[cell[0]][cell[1]] == background
        )
    )


def _analysis(grid: Any) -> dict[str, Any]:
    """Parse the exact task grammar, retaining concrete violations."""
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}

    height, width = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    maximum = max(counts.values())
    modal = sorted(color for color, count in counts.items() if count == maximum)
    if len(modal) != 1:
        errors.append("background must be the unique modal colour")
        return {"errors": errors}
    background = modal[0]
    colors = sorted(color for color in counts if color != background)
    if len(colors) != 2:
        errors.append(f"expected exactly two non-background colours, got {len(colors)}")
        return {"errors": errors}

    by_color = {color: _components_for_color(grid, color) for color in colors}
    matches = []
    direction_details = {}
    for target in colors:
        donor = colors[1] if target == colors[0] else colors[0]
        donor_cells = tuple(
            sorted((row, col) for row in range(height) for col in range(width)
                   if grid[row][col] == donor)
        )
        target_details = []
        for component in by_color[target]:
            missing = _component_missing(grid, background, component)
            hull = tuple(sorted(_convex_hull_cells(component)))
            detail = {
                "component": component,
                "missing": missing,
                "hull": hull,
            }
            target_details.append(detail)
            if missing and len(missing) == len(donor_cells):
                matches.append((target, donor, detail))
        direction_details[(target, donor)] = target_details

    if len(matches) != 1:
        errors.append(
            "expected exactly one positive convex-hull gap matching the opposite colour count, "
            f"got {len(matches)}"
        )
        return {
            "errors": errors,
            "background": background,
            "colors": tuple(colors),
            "direction_details": direction_details,
        }

    target, donor, selected = matches[0]
    target_details = direction_details[(target, donor)]
    candidate_component = selected["component"]
    decoy_details = [detail for detail in target_details if detail is not selected]
    donor_cells = tuple(
        sorted((row, col) for row in range(height) for col in range(width)
               if grid[row][col] == donor)
    )
    donor_components = by_color[donor]

    if not 1 <= len(selected["missing"]) <= 6:
        errors.append(
            f"selected gap must contain 1..6 cells, got {len(selected['missing'])}"
        )
    if not 1 <= len(donor_cells) <= 6:
        errors.append(f"donor must contain 1..6 cells, got {len(donor_cells)}")
    if not 1 <= len(decoy_details) <= 2:
        errors.append(f"expected one or two target decoys, got {len(decoy_details)}")
    for index, detail in enumerate(decoy_details):
        if not detail["missing"]:
            errors.append(f"decoy {index} must have a positive convex-hull gap")
        if len(detail["missing"]) == len(donor_cells):
            errors.append(f"decoy {index} duplicates the selected gap count")

    ordered_target_components = [candidate_component] + [
        detail["component"] for detail in decoy_details
    ]
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "background": background,
        "colors": tuple(colors),
        "target": target,
        "donor": donor,
        "missing": selected["missing"],
        "hull_cells": selected["hull"],
        "candidate_component": candidate_component,
        "target_components": tuple(ordered_target_components),
        "decoy_components": tuple(detail["component"] for detail in decoy_details),
        "decoy_missing": tuple(detail["missing"] for detail in decoy_details),
        "donor_cells": donor_cells,
        "donor_components": tuple(donor_components),
        "direction_details": direction_details,
    }


def analyze_grid(grid) -> dict[str, Any]:
    """Return a structural parse of a lawful grid; raise on malformed inputs."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid convex-hull donor scene: " + "; ".join(analysis["errors"]))
    return analysis


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    candidate = nested if isinstance(nested, dict) else meta
    return {name: value for name, value in candidate.items() if name in AXES}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Return exact task-grammar violations; [] means a lawful input."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful manifold shared by every canonical and generated input."""
    return list(self_check(grid))


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis directly from a lawful grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "n_holes": len(analysis["missing"]),
        "n_decoys": len(analysis["target_components"]) - 1,
    }


def _transform_local(cells: Iterable[tuple[int, int]], code: int):
    transformed = set(cells)
    if code >= 4:
        transformed = {(row, 4 - col) for row, col in transformed}
    for _ in range(code % 4):
        transformed = {(col, 4 - row) for row, col in transformed}
    return frozenset(transformed)


def _candidate_cells(kind: str, holes: int, rng) -> set[tuple[int, int]]:
    outline_by_kind = {
        "rectangle": _RECT_OUTLINE,
        "clipped": _CLIPPED_OUTLINE,
        "diamond": _DIAMOND_OUTLINE,
    }
    seed_outline = set(_transform_local(outline_by_kind[kind], rng.randrange(8)))

    # Convex-hull-fill tests pixel centres but constructs the hull from complete
    # pixel squares.  Adding a centre-inside cell can therefore enlarge the
    # next hull. Close to a fixed point first, then preserve the hull while
    # removing one non-extreme side cell and optional interior cells.
    full = seed_outline
    while True:
        expanded = _convex_hull_cells(full)
        if expanded == full:
            break
        full = expanded
    boundary = {
        (row, col)
        for row, col in full
        if any(
            (row + drow, col + dcol) not in full
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
    }
    if _convex_hull_cells(boundary) != full:
        raise RuntimeError(f"shape {kind} boundary does not preserve its closed hull")
    optional = sorted(full - boundary)
    # A side gap is inside the convex hull but outside the occupied row span.
    # Keep the remaining boundary itself sufficient to define the full hull;
    # removing any additional interior cells then cannot change that hull.
    row_extents = {
        row: (min(c for r, c in full if r == row),
              max(c for r, c in full if r == row))
        for row, _ in full
    }
    side_cells = sorted(
        cell for cell in boundary
        if cell[1] in row_extents[cell[0]]
        and _convex_hull_cells(boundary - {cell}) == full
    )
    if not side_cells:
        raise RuntimeError(f"shape {kind} has no hull-preserving side gap")
    if holes - 1 > len(optional):
        raise ValueError(f"shape {kind} supports only {len(optional) + 1} holes")
    missing = {rng.choice(side_cells)} | set(rng.sample(optional, holes - 1))
    return set(full) - missing


def _sparse_object_cells(gap_count: int, rng) -> set[tuple[int, int]]:
    # The canonical Racket ray-casting convention is intentionally preserved
    # exactly.  Rotating/reflection these digital templates can change which
    # boundary cell centres count as inside the hull, so vary only by
    # translation inside the 5x5 slot.
    base = set(_SPARSE_TEMPLATES[gap_count])
    max_row = max(row for row, _ in base)
    max_col = max(col for _, col in base)
    row_shift = rng.randrange(5 - max_row)
    col_shift = rng.randrange(5 - max_col)
    cells = {(row + row_shift, col + col_shift) for row, col in base}
    actual_gap = len(_convex_hull_cells(cells) - cells)
    if actual_gap != gap_count:
        raise RuntimeError(
            f"sparse template translation changed gap: {gap_count} -> {actual_gap}"
        )
    return cells


def _decoy_cells(gap_count: int, rng) -> set[tuple[int, int]]:
    interior = [(row, col) for row in range(1, 4) for col in range(1, 4)]
    missing = set(rng.sample(interior, gap_count))
    return {(row, col) for row in range(5) for col in range(5)} - missing


def _connected_donor_cells(count: int, rng) -> set[tuple[int, int]]:
    start = (rng.randrange(5), rng.randrange(5))
    cells = {start}
    while len(cells) < count:
        frontier = sorted(
            {
                (row + drow, col + dcol)
                for row, col in cells
                for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if 0 <= row + drow < 5
                and 0 <= col + dcol < 5
                and (row + drow, col + dcol) not in cells
            }
        )
        cells.add(rng.choice(frontier))
    return cells


def _scattered_donor_cells(count: int, rng) -> set[tuple[int, int]]:
    lattice = [(row, col) for row in (0, 2, 4) for col in (0, 2, 4)]
    return set(rng.sample(lattice, count))


def _mixed_donor_cells(count: int, rng) -> set[tuple[int, int]]:
    if count <= 1:
        return _scattered_donor_cells(count, rng)
    if count == 2:
        return _connected_donor_cells(count, rng)
    cluster_path = {(0, 0), (0, 1), (1, 1), (1, 0), (2, 0)}
    ordered = [(0, 0), (0, 1), (1, 1), (1, 0), (2, 0)]
    cells = set(ordered[: count - 1]) | {(4, 4)}
    assert cells <= cluster_path | {(4, 4)}
    return set(_transform_local(cells, rng.randrange(8)))


def _paint_local(grid, top: int, left: int, cells, color: int) -> None:
    for row, col in cells:
        grid[top + row][left + col] = color


def _palette(ctx, profile: int):
    if profile == 0:
        return 7, 2, 9  # target lower than donor
    if profile == 1:
        return 7, 9, 2  # target higher than donor
    rng = ctx.draw_rng("palette")
    background = rng.choice((0, 1, 3, 4, 5, 6, 7, 8))
    pair = rng.sample([color for color in range(10) if color != background], 2)
    donor, target = sorted(pair)
    return background, target, donor


def _default_dimensions(sample_index: int, band: str):
    # Any four consecutive samples contain every canonical square profile plus
    # one broad off-profile draw.  This makes canonical support independent of
    # the profile-floor tool's pinned seed offsets and of difficulty band.
    phase = sample_index % 4
    if phase == 0:
        return 13, 13
    if phase == 1:
        return 15, 15
    if phase == 2:
        return 16, 16
    offset = sample_index // 4
    return (
        _HEIGHT_CYCLES[band][offset % len(_HEIGHT_CYCLES[band])],
        _WIDTH_CYCLES[band][offset % len(_WIDTH_CYCLES[band])],
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct one lawful input using only deterministic keyed randomness."""
    _validate_controls(seed, sample_index, difficulty, overrides)
    band = difficulty or "medium"
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    default_h, default_w = _default_dimensions(sample_index, band)
    grid_h = _scheduled_int(ctx, "grid_h", default_h)
    grid_w = _scheduled_int(ctx, "grid_w", default_w)
    n_holes = _scheduled_int(ctx, "n_holes", _HOLE_CYCLE[sample_index % len(_HOLE_CYCLE)])
    n_decoys = _scheduled_int(ctx, "n_decoys", _DECOY_CYCLE[sample_index % len(_DECOY_CYCLE)])

    profile = schedule_profile(seed, sample_index, difficulty)
    background, target, donor = _palette(ctx, profile)
    grid = full_grid(grid_h, grid_w, background)

    layout_rng = ctx.draw_rng("object_slots")
    slots = [(0, 0), (0, grid_w - 5), (grid_h - 5, 0), (grid_h - 5, grid_w - 5)]
    layout_rng.shuffle(slots)
    candidate_slot = slots[0]
    donor_slot = slots[1]
    decoy_slots = slots[2: 2 + n_decoys]

    candidate_rng = ctx.draw_rng("candidate_geometry")
    if profile == 1:
        candidate = _sparse_object_cells(n_holes, candidate_rng)
    else:
        candidate = _candidate_cells(_PROFILE_SHAPE[profile], n_holes, candidate_rng)
    _paint_local(grid, *candidate_slot, candidate, target)

    decoy_rng = ctx.draw_rng("decoy_geometry")
    if profile == 1:
        # Keep the canonical-anchor profile 4-disconnected throughout. A
        # five-cell gap-4 decoy with the three-cell gap-1 candidate reproduces
        # the canonical eight persistent target pixels. Other legal templates
        # retain larger decoys and both advertised decoy counts.
        legal = [gap for gap in range(1, 7) if gap != n_holes]
        legal.sort(key=lambda gap: (gap != 4, -len(_SPARSE_TEMPLATES[gap]), gap))
        gap_counts = legal[:n_decoys]
    else:
        decoy_gap_options = [gap for gap in range(1, 10) if gap != n_holes]
        preferred = 1 if n_holes != 1 else 2
        gap_counts = [preferred]
        if n_decoys == 2:
            gap_counts.append(next(gap for gap in decoy_gap_options if gap != preferred))
    for index, (slot, gap_count) in enumerate(zip(decoy_slots, gap_counts)):
        local_rng = ctx.draw_rng(f"decoy_geometry_{index}_{decoy_rng.randrange(1 << 30)}")
        decoy = (
            _sparse_object_cells(gap_count, local_rng)
            if profile == 1
            else _decoy_cells(gap_count, local_rng)
        )
        _paint_local(grid, *slot, decoy, target)

    donor_rng = ctx.draw_rng("donor_geometry")
    if profile == 0:
        donor_cells = _connected_donor_cells(n_holes, donor_rng)
    elif profile == 1:
        donor_cells = _scattered_donor_cells(n_holes, donor_rng)
    else:
        donor_cells = _mixed_donor_cells(n_holes, donor_rng)
    _paint_local(grid, *donor_slot, donor_cells, donor)

    # Construction bugs should fail at their source rather than leaking an
    # invalid training example into a later batch stage.
    errors = self_check(grid)
    if errors:
        raise RuntimeError("constructed invalid scene: " + "; ".join(errors))
    return grid


def _apply_selection(grid, *, background: int, donor: int, missing, donor_cells):
    output = deepcopy(grid)
    for row, col in donor_cells:
        output[row][col] = background
    for row, col in missing:
        output[row][col] = donor
    return output


def rule_mirror(grid):
    """Independent Python oracle; pinned Racket remains output authority."""
    analysis = analyze_grid(grid)
    return _apply_selection(
        grid,
        background=analysis["background"],
        donor=analysis["donor"],
        missing=analysis["missing"],
        donor_cells=analysis["donor_cells"],
    )


def _unchanged(grid):
    return deepcopy(grid)


def _rival_isolated_donors_only(grid):
    try:
        analysis = analyze_grid(grid)
    except ValueError:
        return None
    if all(len(component) == 1 for component in analysis["donor_components"]):
        return rule_mirror(grid)
    return _unchanged(grid)


def _rival_rectangle_only(grid):
    try:
        analysis = analyze_grid(grid)
    except ValueError:
        return None
    component = analysis["candidate_component"]
    min_row = min(row for row, _ in component)
    max_row = max(row for row, _ in component)
    min_col = min(col for _, col in component)
    max_col = max(col for _, col in component)
    rectangle = {
        (row, col)
        for row in range(min_row, max_row + 1)
        for col in range(min_col, max_col + 1)
    }
    if set(analysis["hull_cells"]) == rectangle:
        return rule_mirror(grid)
    return _unchanged(grid)


def _rival_largest_target_object(grid):
    try:
        analysis = analyze_grid(grid)
    except ValueError:
        return None
    chosen = max(
        analysis["target_components"],
        key=lambda component: (len(component), tuple((-r, -c) for r, c in component)),
    )
    missing = _component_missing(grid, analysis["background"], chosen)
    return _apply_selection(
        grid,
        background=analysis["background"],
        donor=analysis["donor"],
        missing=missing,
        donor_cells=analysis["donor_cells"],
    )


def _rival_lower_colour_target(grid):
    analysis = _analysis(grid)
    if analysis["errors"] and "colors" not in analysis:
        return None
    background = analysis.get("background")
    colors = analysis.get("colors")
    if background is None or not colors or len(colors) != 2:
        return None
    target, donor = min(colors), max(colors)
    donor_cells = tuple(
        sorted((row, col) for row in range(len(grid)) for col in range(len(grid[0]))
               if grid[row][col] == donor)
    )
    for component in _components_for_color(grid, target):
        missing = _component_missing(grid, background, component)
        if missing and len(missing) == len(donor_cells):
            return _apply_selection(
                grid,
                background=background,
                donor=donor,
                missing=missing,
                donor_cells=donor_cells,
            )
    return _unchanged(grid)


def _rival_horizontal_row_span(grid):
    """Replace the convex hull with per-row spans; infer both colour roles."""
    if _grid_errors(grid):
        return None
    counts = Counter(value for row in grid for value in row)
    maximum = max(counts.values())
    modes = [color for color, count in counts.items() if count == maximum]
    if len(modes) != 1:
        return None
    background = modes[0]
    colors = sorted(set(counts) - {background})
    if len(colors) != 2:
        return None
    matches = []
    for target in colors:
        donor = colors[1] if target == colors[0] else colors[0]
        donor_cells = tuple((r, c) for r, row in enumerate(grid)
                            for c, value in enumerate(row) if value == donor)
        for component in _components_for_color(grid, target):
            missing = set()
            for row in {r for r, _ in component}:
                columns = [c for r, c in component if r == row]
                missing.update((row, col)
                               for col in range(min(columns), max(columns) + 1)
                               if grid[row][col] == background)
            if missing and len(missing) == len(donor_cells):
                matches.append((donor, donor_cells, missing))
    if len(matches) != 1:
        return _unchanged(grid)
    donor, donor_cells, missing = matches[0]
    return _apply_selection(grid, background=background, donor=donor,
                            missing=missing, donor_cells=donor_cells)


def _witness_horizontal_row_span_fails(grid) -> bool:
    try:
        return _rival_horizontal_row_span(grid) != rule_mirror(grid)
    except ValueError:
        return False


def _witness_connected_donor_component(grid) -> bool:
    try:
        return any(len(component) > 1 for component in analyze_grid(grid)["donor_components"])
    except ValueError:
        return False


def _witness_nonrectangular_candidate_hull(grid) -> bool:
    try:
        analysis = analyze_grid(grid)
    except ValueError:
        return False
    component = analysis["candidate_component"]
    min_row = min(row for row, _ in component)
    max_row = max(row for row, _ in component)
    min_col = min(col for _, col in component)
    max_col = max(col for _, col in component)
    return set(analysis["hull_cells"]) != {
        (row, col)
        for row in range(min_row, max_row + 1)
        for col in range(min_col, max_col + 1)
    }


def _witness_larger_decoy_than_candidate(grid) -> bool:
    try:
        analysis = analyze_grid(grid)
    except ValueError:
        return False
    return max(map(len, analysis["decoy_components"]), default=0) > len(
        analysis["candidate_component"]
    )


def _witness_target_higher_than_donor(grid) -> bool:
    try:
        analysis = analyze_grid(grid)
    except ValueError:
        return False
    return analysis["target"] > analysis["donor"]


SEMANTIC_WITNESSES = {
    "horizontal_row_span_fails": _witness_horizontal_row_span_fails,
    "connected_donor_component": _witness_connected_donor_component,
    "nonrectangular_candidate_hull": _witness_nonrectangular_candidate_hull,
    "larger_decoy_than_candidate": _witness_larger_decoy_than_candidate,
    "target_higher_than_donor": _witness_target_higher_than_donor,
}
SEMANTIC_RIVALS = {
    "horizontal_row_span": _rival_horizontal_row_span,
    "isolated_donors_only": _rival_isolated_donors_only,
    "rectangle_only": _rival_rectangle_only,
    "largest_target_object": _rival_largest_target_object,
    "lower_colour_is_target": _rival_lower_colour_target,
}
WITNESS_RIVALS = {
    "horizontal_row_span_fails": ("horizontal_row_span",),
    "connected_donor_component": ("isolated_donors_only",),
    "nonrectangular_candidate_hull": ("rectangle_only",),
    "larger_decoy_than_candidate": ("largest_target_object",),
    "target_higher_than_donor": ("lower_colour_is_target",),
}
# The remaining partial heuristics fail at least one canonical pair. They
# remain valuable lesson rivals, but must not be claimed as canonical fits.
CANONICAL_SHORTCUTS = {"horizontal_row_span": _rival_horizontal_row_span}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons whose demonstrations leave a declared shortcut viable."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        try:
            expected = rule_mirror(deepcopy(pair["input"]))
        except Exception as exc:
            reasons.append(f"demo {index} is invalid: {type(exc).__name__}: {exc}")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output does not match the convex-hull donor rule")

    try:
        query_answer = rule_mirror(deepcopy(query["input"]))
    except Exception as exc:
        reasons.append(f"query is invalid: {type(exc).__name__}: {exc}")
        return reasons
    if query.get("output") is not None and query.get("output") != query_answer:
        reasons.append("query output does not match the convex-hull donor rule")

    for name, rival in LESSON_COMPETITORS.items():
        survives = all(
            rival(deepcopy(pair["input"])) == pair.get("output")
            for pair in demos
        )
        if survives and rival(deepcopy(query["input"])) != query_answer:
            reasons.append(f"demonstrations remain consistent with shortcut: {name}")
    return reasons
