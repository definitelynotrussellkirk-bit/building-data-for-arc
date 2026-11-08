"""Generator for 461d3a83ca9e — cast colored diagonal rays until blockers.

Every nonzero cell other than gray 5 is a one-cell emitter.  In row-major
emitter order, copy its own color along the four diagonals through cells that
were background in the original input.  A ray stops before the grid edge, a
gray wall, or the other emitter.  Gray wall cells never emit.

The canonical examples contain exactly two distinct emitters and two straight
gray walls.  Ordinary generated lessons retain exactly two emitters, vary one
to three walls, and deliberately avoid ray/ray intersections: overlap color
priority is not identified by the canonical task and therefore is not added as
an accidental training rule.
"""
from __future__ import annotations

from collections import Counter, deque
from functools import lru_cache
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "461d3a83ca9e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "953a9d167b9c"

SUMMARY = (
    "Exactly two distinct non-{0,5} singleton emitters cast their own colors "
    "along all four diagonals through original-background cells. Rays stop "
    "before the edge, a straight gray-5 wall, or the other emitter; gray walls "
    "do not emit. Generated scenes avoid ray/ray overlap because canonical "
    "examples do not identify an overlap-priority convention."
)

INVARIANTS = [
    "background is 0 and gray 5 is reserved for walls",
    "exactly two singleton emitters use two distinct colors outside {0,5}",
    "one to three 4-connected gray wall components are straight length-3..5 segments",
    "each emitter has a visible diagonal ray of length at least two",
    "ordinary generated ray paths do not overlap one another",
    "every four consecutive examples cover wall blocking, irrelevant walls, emitter blocking, and a canonical-scale anchor",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.45

INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled/difficulty-aware draw within 9..16",
        "valid": "9..16",
        "doc": "Returned grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled/difficulty-aware draw within 9..18",
        "valid": "9..18",
        "doc": "Returned grid width.",
    },
    "n_walls": {
        "type": "int",
        "default": "two in canonical slots; otherwise difficulty-aware 1..3",
        "valid": "1..3",
        "doc": "Number of straight 4-connected gray wall components.",
    },
}

_DIAGONALS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
_CARDINALS = ((1, 0), (-1, 0), (0, 1), (0, -1))
_CANONICAL_SHAPES = ((9, 9), (9, 11), (10, 10), (10, 11), (11, 12))

_PROFILE_CANONICAL_BLOCKED = "canonical_wall_block"
_PROFILE_CANONICAL_CLEAR = "canonical_irrelevant_walls"
_PROFILE_EMITTER_BLOCKED = "emitter_block"
_PROFILE_WALL_VARIATION = "wall_count_variation"
SCHEDULE_PROFILES = (
    _PROFILE_CANONICAL_BLOCKED,
    _PROFILE_CANONICAL_CLEAR,
    _PROFILE_EMITTER_BLOCKED,
    _PROFILE_WALL_VARIATION,
)


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the four-slot lesson schedule profile for a draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _draw_axis(
    ctx,
    overrides: dict[str, Any],
    name: str,
    default_lo: int,
    default_hi: int,
    valid_lo: int,
    valid_hi: int,
) -> int:
    """Honor an exact override across its full declared domain."""
    if overrides.get(name) is not None:
        return ctx.draw_int(name, valid_lo, valid_hi)
    return ctx.draw_int(name, default_lo, default_hi)


def _ordinary_ranges(band: str) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if band == "easy":
        return (9, 10), (9, 11), (1, 2)
    if band == "hard":
        return (11, 16), (12, 18), (2, 3)
    return (9, 12), (10, 14), (1, 3)


def _draw_dimensions_and_walls(ctx, overrides, band: str, profile: str) -> tuple[int, int, int]:
    if overrides:
        (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _ordinary_ranges(band)
        return (
            _draw_axis(ctx, overrides, "grid_h", h_lo, h_hi, 9, 16),
            _draw_axis(ctx, overrides, "grid_w", w_lo, w_hi, 9, 18),
            _draw_axis(ctx, overrides, "n_walls", n_lo, n_hi, 1, 3),
        )

    if profile in (_PROFILE_CANONICAL_BLOCKED, _PROFILE_CANONICAL_CLEAR):
        shape = ctx.draw_choice("canonical_shape", _CANONICAL_SHAPES)
        return (
            ctx.draw_int("grid_h", shape[0], shape[0]),
            ctx.draw_int("grid_w", shape[1], shape[1]),
            ctx.draw_int("n_walls", 2, 2),
        )

    (h_lo, h_hi), (w_lo, w_hi), (n_lo, n_hi) = _ordinary_ranges(band)
    if profile == _PROFILE_EMITTER_BLOCKED:
        n_hi = min(2, n_hi)
    return (
        ctx.draw_int("grid_h", h_lo, h_hi),
        ctx.draw_int("grid_w", w_lo, w_hi),
        ctx.draw_int("n_walls", n_lo, n_hi),
    )


def _validate_grid(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _wall_components(walls: Iterable[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(walls)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in _CARDINALS:
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _straight_wall(component: set[tuple[int, int]]) -> bool:
    rows = {row for row, _ in component}
    cols = {col for _, col in component}
    if len(rows) == 1:
        values = sorted(col for _, col in component)
    elif len(cols) == 1:
        values = sorted(row for row, _ in component)
    else:
        return False
    return 3 <= len(values) <= 5 and values == list(range(values[0], values[-1] + 1))


def _trace_rays(grid: Any, emitters: list[tuple[int, int, int]]) -> dict[str, Any]:
    height, width = len(grid), len(grid[0])
    paths_by_cell: dict[tuple[int, int], list[tuple[int, int]]] = {}
    rays: list[dict[str, Any]] = []
    for emitter_index, (row, col, color) in enumerate(emitters):
        for drow, dcol in _DIAGONALS:
            rr, cc = row + drow, col + dcol
            path: list[tuple[int, int]] = []
            while 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == 0:
                path.append((rr, cc))
                paths_by_cell.setdefault((rr, cc), []).append((emitter_index, color))
                rr += drow
                cc += dcol
            if not (0 <= rr < height and 0 <= cc < width):
                stop_kind = "edge"
                stop_cell = None
            elif grid[rr][cc] == 5:
                stop_kind = "wall"
                stop_cell = (rr, cc)
            else:
                stop_kind = "emitter"
                stop_cell = (rr, cc)
            rays.append(
                {
                    "emitter_index": emitter_index,
                    "color": color,
                    "direction": (drow, dcol),
                    "path": path,
                    "stop_kind": stop_kind,
                    "stop_cell": stop_cell,
                }
            )
    return {
        "rays": rays,
        "overlap_cells": {
            cell: owners for cell, owners in paths_by_cell.items() if len(owners) > 1
        },
    }


def _official_output(grid: Any, emitters: list[tuple[int, int, int]]) -> list[list[int]]:
    """Python validation mirror; generated labels still come from Racket."""
    height, width = len(grid), len(grid[0])
    out = [list(row) for row in grid]
    for row, col, color in emitters:
        for drow, dcol in _DIAGONALS:
            rr, cc = row + drow, col + dcol
            while 0 <= rr < height and 0 <= cc < width and grid[rr][cc] == 0:
                out[rr][cc] = color
                rr += drow
                cc += dcol
    return out


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    emitters = sorted(
        (row, col, int(value))
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    )
    walls = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    }
    components = _wall_components(walls)

    if not 1 <= height <= 30 or not 1 <= width <= 30:
        errors.append(f"dimensions {height}x{width} exceed the ARC 30x30 envelope")
    if len(emitters) != 2:
        errors.append(f"need exactly two non-{{0,5}} emitter cells; found {len(emitters)}")
    emitter_colors = [color for _, _, color in emitters]
    if len(set(emitter_colors)) != len(emitter_colors):
        errors.append("the two emitter colors must be distinct")
    if not 1 <= len(components) <= 3:
        errors.append(f"need one to three gray wall components; found {len(components)}")
    for index, component in enumerate(components):
        if not _straight_wall(component):
            errors.append(f"gray wall component {index} is not a straight contiguous length-3..5 segment")

    trace = _trace_rays(grid, emitters) if len(emitters) == 2 else {"rays": [], "overlap_cells": {}}
    per_emitter_lengths = Counter()
    for ray in trace["rays"]:
        per_emitter_lengths[ray["emitter_index"]] += len(ray["path"])
    if len(emitters) == 2 and any(per_emitter_lengths[index] < 2 for index in range(2)):
        errors.append("each emitter must paint at least two diagonal background cells in total")

    output = _official_output(grid, emitters) if len(emitters) == 2 else [list(row) for row in grid]
    if len(emitters) == 2 and output == [list(row) for row in grid]:
        errors.append("ray transformation would be an identity")

    stop_counts = Counter(ray["stop_kind"] for ray in trace["rays"])
    result.update(
        {
            "grid_h": height,
            "grid_w": width,
            "emitters": emitters,
            "emitter_colors": emitter_colors,
            "walls": walls,
            "wall_components": components,
            "n_walls": len(components),
            "palette_size": len({int(value) for row in grid for value in row}),
            "trace": trace,
            "stop_counts": dict(stop_counts),
            "has_wall_block": stop_counts.get("wall", 0) > 0,
            "has_emitter_block": stop_counts.get("emitter", 0) > 0,
            "has_edge_exit": stop_counts.get("edge", 0) > 0,
            "has_long_ray": any(len(ray["path"]) >= 3 for ray in trace["rays"]),
            "has_overlap": bool(trace["overlap_cells"]),
            "output": output,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task's structural input grammar without curriculum-only tests."""
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid) -> list[str]:
    """Recognize the canonical two-emitter/two-wall, non-overlap manifold."""
    analysis = _analysis(grid)
    reasons = list(analysis["errors"])
    if reasons:
        return reasons
    if (analysis["grid_h"], analysis["grid_w"]) not in _CANONICAL_SHAPES:
        reasons.append("dimensions are outside the five canonical shape profiles")
    if analysis["n_walls"] != 2:
        reasons.append("canonical inputs contain exactly two wall components")
    if analysis["palette_size"] != 4:
        reasons.append("canonical inputs use background, gray, and exactly two emitter colors")
    if analysis["has_emitter_block"]:
        reasons.append("canonical inputs do not place one emitter on the other's diagonal")
    if analysis["has_overlap"]:
        reasons.append("canonical inputs contain no ray/ray overlap")
    return reasons


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact declared axis from the returned input grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": analysis["grid_h"],
        "grid_w": analysis["grid_w"],
        "n_walls": analysis["n_walls"],
    }


def rule_mirror(grid) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [list(row) for row in analysis["output"]]


@lru_cache(maxsize=None)
def _wall_segments(height: int, width: int) -> tuple[tuple[tuple[int, int], ...], ...]:
    segments: list[tuple[tuple[int, int], ...]] = []
    for length in range(3, 6):
        if length <= width:
            for row in range(height):
                for left in range(width - length + 1):
                    segments.append(tuple((row, col) for col in range(left, left + length)))
        if length <= height:
            for col in range(width):
                for top in range(height - length + 1):
                    segments.append(tuple((row, col) for row in range(top, top + length)))
    return tuple(segments)


def _segments_touch(a: Iterable[tuple[int, int]], b: Iterable[tuple[int, int]]) -> bool:
    bset = set(b)
    for row, col in a:
        if (row, col) in bset:
            return True
        if any((row + drow, col + dcol) in bset for drow, dcol in _CARDINALS):
            return True
    return False


def _on_emitter_diagonal(cell: tuple[int, int], emitters: Iterable[tuple[int, int]]) -> bool:
    row, col = cell
    return any(abs(row - erow) == abs(col - ecol) and cell != (erow, ecol) for erow, ecol in emitters)


@lru_cache(maxsize=None)
def _opposite_parity_emitter_pairs(height: int, width: int) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    cells = [(row, col) for row in range(1, height - 1) for col in range(1, width - 1)]
    return tuple(
        (first, second)
        for index, first in enumerate(cells)
        for second in cells[index + 1 :]
        if (sum(first) - sum(second)) % 2 != 0
        and max(abs(first[0] - second[0]), abs(first[1] - second[1])) >= 3
    )


@lru_cache(maxsize=None)
def _aligned_emitter_pairs(height: int, width: int) -> tuple[tuple[tuple[int, int], tuple[int, int]], ...]:
    pairs: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            for drow, dcol in ((1, 1), (1, -1)):
                for distance in (1,):
                    other = (row + drow * distance, col + dcol * distance)
                    if not (1 <= other[0] < height - 1 and 1 <= other[1] < width - 1):
                        continue
                    # Leave a cell beyond both emitters so the transparent-emitter
                    # rival has a visible disagreement.
                    before = (row - drow, col - dcol)
                    after = (other[0] + drow, other[1] + dcol)
                    if not (
                        0 <= before[0] < height
                        and 0 <= before[1] < width
                        and 0 <= after[0] < height
                        and 0 <= after[1] < width
                    ):
                        continue
                    pair = tuple(sorted(((row, col), other)))
                    if pair not in pairs:
                        pairs.append(pair)
    return tuple(pairs)


def _choose_walls(
    height: int,
    width: int,
    emitters: tuple[tuple[int, int], tuple[int, int]],
    n_walls: int,
    profile: str,
    rng,
) -> list[tuple[tuple[int, int], ...]] | None:
    emitter_set = set(emitters)
    candidates = [
        segment
        for segment in _wall_segments(height, width)
        if emitter_set.isdisjoint(segment)
    ]
    rng.shuffle(candidates)

    if profile in (_PROFILE_CANONICAL_CLEAR, _PROFILE_EMITTER_BLOCKED):
        candidates = [
            segment
            for segment in candidates
            if not any(_on_emitter_diagonal(cell, emitters) for cell in segment)
        ]
        chosen: list[tuple[tuple[int, int], ...]] = []
    else:
        # Make the first wall cross a ray at least two cells away from an emitter.
        ray_targets = [
            (row + drow * distance, col + dcol * distance)
            for row, col in emitters
            for drow, dcol in _DIAGONALS
            for distance in range(2, max(height, width))
            if 0 <= row + drow * distance < height
            and 0 <= col + dcol * distance < width
            and (row + drow * distance, col + dcol * distance) not in emitter_set
        ]
        rng.shuffle(ray_targets)
        first = next(
            (
                segment
                for target in ray_targets
                for segment in candidates
                if target in segment
            ),
            None,
        )
        if first is None:
            return None
        chosen = [first]

    for segment in candidates:
        if len(chosen) >= n_walls:
            break
        if segment in chosen:
            continue
        if any(_segments_touch(segment, prior) for prior in chosen):
            continue
        chosen.append(segment)
    if len(chosen) != n_walls:
        return None
    return chosen


def _build_scene(
    height: int,
    width: int,
    n_walls: int,
    colors: tuple[int, int],
    profile: str,
    rng,
) -> list[list[int]]:
    pair_source = list(
        _aligned_emitter_pairs(height, width)
        if profile == _PROFILE_EMITTER_BLOCKED
        else _opposite_parity_emitter_pairs(height, width)
    )
    rng.shuffle(pair_source)

    for emitters in pair_source[:160]:
        walls = _choose_walls(height, width, emitters, n_walls, profile, rng)
        if walls is None:
            continue
        grid = full_grid(height, width, 0)
        for (row, col), color in zip(sorted(emitters), colors):
            grid[row][col] = color
        for segment in walls:
            for row, col in segment:
                grid[row][col] = 5

        analysis = _analysis(grid)
        if analysis["errors"] or analysis["has_overlap"]:
            continue
        if profile == _PROFILE_CANONICAL_BLOCKED:
            if not analysis["has_wall_block"] or rival_ignore_walls(grid) == analysis["output"]:
                continue
        if profile == _PROFILE_CANONICAL_CLEAR and analysis["has_wall_block"]:
            continue
        if profile == _PROFILE_EMITTER_BLOCKED:
            if not analysis["has_emitter_block"] or analysis["has_wall_block"]:
                continue
        if profile in (_PROFILE_WALL_VARIATION, "general_override"):
            if not analysis["has_wall_block"] or rival_ignore_walls(grid) == analysis["output"]:
                continue
        if not analysis["has_edge_exit"] or not analysis["has_long_ray"]:
            continue
        return grid
    raise ValueError(
        f"could not construct {profile} scene for {height}x{width} with {n_walls} wall(s)"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    band = _band(difficulty)
    profile = "general_override" if overrides else schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    height, width, n_walls = _draw_dimensions_and_walls(ctx, overrides, band, profile)
    colors = ctx.draw_distinct_colors("emitter_colors", n=2, exclude={0, 5})
    grid = _build_scene(height, width, n_walls, colors, profile, ctx.draw_rng("layout"))

    expected = {"grid_h": height, "grid_w": width, "n_walls": n_walls}
    observed = observe_overrides(grid)
    if observed != expected:
        raise AssertionError(f"realized axis drift: expected {expected}, observed {observed}")
    return grid


# ---------------------------------------------------------------------------
# Explicit wrong-rule competitors used by the semantic gate.
# ---------------------------------------------------------------------------


def _rival_output(
    grid,
    *,
    directions: tuple[tuple[int, int], ...] = _DIAGONALS,
    ignore_walls: bool = False,
    ignore_emitters: bool = False,
    walls_emit: bool = False,
    first_only: bool = False,
    one_step: bool = False,
    fixed_color: bool = False,
) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    emitters = sorted(
        (row, col, int(value))
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    )
    if walls_emit:
        emitters.extend(
            (row, col, 5)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 5
        )
        emitters.sort()
    if first_only:
        emitters = emitters[:1]
    paint_color = emitters[0][2] if emitters else 1
    out = [list(row) for row in grid]

    for row, col, color in emitters:
        for drow, dcol in directions:
            rr, cc = row + drow, col + dcol
            steps = 0
            while 0 <= rr < height and 0 <= cc < width:
                value = grid[rr][cc]
                if value == 0:
                    out[rr][cc] = paint_color if fixed_color else color
                    steps += 1
                    if one_step and steps >= 1:
                        break
                elif value == 5 and ignore_walls:
                    pass
                elif value not in (0, 5) and ignore_emitters:
                    pass
                else:
                    break
                rr += drow
                cc += dcol
    return out


def rival_ignore_walls(grid) -> list[list[int]]:
    return _rival_output(grid, ignore_walls=True)


def rival_ignore_emitters(grid) -> list[list[int]]:
    return _rival_output(grid, ignore_emitters=True)


def rival_walls_emit(grid) -> list[list[int]]:
    return _rival_output(grid, walls_emit=True)


def rival_cardinal_rays(grid) -> list[list[int]]:
    return _rival_output(grid, directions=_CARDINALS)


def rival_first_emitter_only(grid) -> list[list[int]]:
    return _rival_output(grid, first_only=True)


def rival_one_step(grid) -> list[list[int]]:
    return _rival_output(grid, one_step=True)


def rival_fixed_first_color(grid) -> list[list[int]]:
    return _rival_output(grid, fixed_color=True)


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "ignore_walls": rival_ignore_walls,
    "ignore_emitters": rival_ignore_emitters,
    "walls_emit": rival_walls_emit,
    "cardinal_rays": rival_cardinal_rays,
    "first_emitter_only": rival_first_emitter_only,
    "one_step_rays": rival_one_step,
    "fixed_first_color": rival_fixed_first_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    "ignore_emitters": rival_ignore_emitters,
    "first_emitter_only": rival_first_emitter_only,
    "one_step_rays": rival_one_step,
}


def _valid_analysis(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _witness_wall_block(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and analysis["has_wall_block"]
        and rival_ignore_walls(grid) != analysis["output"]
    )


def _witness_emitter_block(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and analysis["has_emitter_block"]
        and rival_ignore_emitters(grid) != analysis["output"]
    )


def _witness_walls_do_not_emit(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and rival_walls_emit(grid) != analysis["output"]


def _witness_diagonal_rays(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and rival_cardinal_rays(grid) != analysis["output"]


def _witness_both_emitters(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and rival_first_emitter_only(grid) != analysis["output"]


def _witness_long_rays(grid) -> bool:
    analysis = _valid_analysis(grid)
    return (
        analysis is not None
        and analysis["has_long_ray"]
        and rival_one_step(grid) != analysis["output"]
    )


def _witness_own_colors(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and rival_fixed_first_color(grid) != analysis["output"]


def _witness_irrelevant_walls(grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and not analysis["has_wall_block"]


SEMANTIC_WITNESSES = {
    "wall_stops_a_ray": _witness_wall_block,
    "emitter_stops_a_ray": _witness_emitter_block,
    "gray_walls_do_not_emit": _witness_walls_do_not_emit,
    "rays_are_diagonal": _witness_diagonal_rays,
    "both_emitters_cast": _witness_both_emitters,
    "rays_continue_beyond_one_cell": _witness_long_rays,
    "each_emitter_keeps_its_own_color": _witness_own_colors,
    "walls_can_be_irrelevant_distractors": _witness_irrelevant_walls,
}
BRANCH_WITNESSES = {"walls_can_be_irrelevant_distractors"}
WITNESS_RIVALS = {
    "wall_stops_a_ray": ["ignore_walls"],
    "emitter_stops_a_ray": ["ignore_emitters"],
    "gray_walls_do_not_emit": ["walls_emit"],
    "rays_are_diagonal": ["cardinal_rays"],
    "both_emitters_cast": ["first_emitter_only"],
    "rays_continue_beyond_one_cell": ["one_step_rays"],
    "each_emitter_keeps_its_own_color": ["fixed_first_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo lesson to eliminate all named shortcuts."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    for index, pair in enumerate(demos):
        analysis = _analysis(pair.get("input"))
        if analysis["errors"]:
            reasons.append(f"demo {index} input is outside the ray-casting grammar")
            continue
        if pair.get("output") != analysis["output"]:
            reasons.append(f"demo {index} output does not match diagonal ray casting")
        if analysis["has_overlap"]:
            reasons.append(f"demo {index} contains an excluded ray/ray overlap")

    for name, competitor in LESSON_COMPETITORS.items():
        if not any(competitor(pair["input"]) != pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} survives every demonstration")

    if not any(_witness_wall_block(pair["input"]) for pair in demos):
        reasons.append("no demonstration shows a gray wall stopping a ray")
    if not any(_witness_irrelevant_walls(pair["input"]) for pair in demos):
        reasons.append("no demonstration shows walls that are irrelevant distractors")
    if not any(_witness_emitter_block(pair["input"]) for pair in demos):
        reasons.append("no demonstration shows one emitter stopping the other")
    if not any(strict_canonical_like(pair["input"]) == [] for pair in demos):
        reasons.append("no demonstration anchors the canonical two-wall profile")

    query_analysis = _analysis(query.get("input"))
    if query_analysis["errors"]:
        reasons.append("query input is outside the ray-casting grammar")
    if query_analysis.get("has_overlap"):
        reasons.append("query contains an excluded ray/ray overlap")
    return reasons
