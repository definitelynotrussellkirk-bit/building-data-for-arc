"""Monochromatic marker inputs for the unchanged all-marker bbox authority.

The Racket rule draws a fresh rectangle outline, erasing interior markers.
One canonical-corner profile and two distributed-extrema profiles repeat every
three sample indices. The latter also contain a strictly interior marker, so
three demonstrations retain both distinctions under any one-of-four holdout.
Only Racket supplies labels; the Python predictions below are named rivals.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f68fe53c1702"
TASK_ID = "f68fe53c1702"
RULE_HASH = "ab8196a7d821"
VERSION = "3.0.0"
SUMMARY = (
    "Draw the outline of the bounding box of ALL same-color nonzero markers "
    "on a fresh same-size zero grid. Inputs have 2..7 distinct markers and a "
    "bbox at least 3x3. Default lessons mix three-corner canonical profiles "
    "with distributed extrema and interior markers; positions, aspect ratios, "
    "border contact and colors vary. Exact size, color and count overrides "
    "are honored in every band."
)
INVARIANTS = [
    "rectangular integer grid, height 4..24 and width 5..24, with zero background",
    "2..7 distinct marker cells share one color in 1..9",
    "all-marker bbox spans at least 3 rows and 3 columns",
    "ordinary three-corner profiles preserve the canonical input construction",
    "ordinary rich profiles contain interior markers and no opposite-corner pair",
]
AXES = {
    "grid_h": {"type": "int", "default": "canonical profile or band-sized", "valid": "4..24"},
    "grid_w": {"type": "int", "default": "canonical profile or band-sized", "valid": "5..24"},
    "color": {"type": "int", "default": "uniform 1..9", "valid": "1..9"},
    "num_cells": {"type": "int", "default": "3 canonical / 4..7 rich", "valid": "2..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 3
SCHEDULE_PROFILES = ("canonical_corners", "distributed_extrema")
_CANONICAL_SHAPES = ((7, 7), (8, 8), (6, 9), (7, 10), (9, 9))


def schedule_profile(seed, sample_index, difficulty=None):
    """Semantic profile only; geometry still uses the seed and full index."""
    return SCHEDULE_PROFILES[0 if sample_index % LESSON_SCHEDULE_PERIOD == 0 else 1]


def _axis(ctx, name, lo, hi, defaults):
    # Exact requests use the entire declared range, independent of curriculum.
    # Default choices still record keyed provenance under the same axis name.
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_choice(name, defaults)


@lru_cache(maxsize=512)
def _feasible_spans(h, w, count, rich):
    # Rich layouts avoid bbox corners (or allow only one). Reserving four
    # corners makes both constructions feasible without dropping any marker.
    reserve = 4 if rich else 0
    return tuple((bh, bw) for bh in range(3, h + 1) for bw in range(3, w + 1)
                 if bh * bw - reserve >= count)


def _corner_markers(rng, bh, bw, count):
    corners = ((0, 0), (0, bw - 1), (bh - 1, 0), (bh - 1, bw - 1))
    corner_count = 3 if count == 3 else rng.randint(2, min(4, count))
    if corner_count == 2:
        chosen = list(rng.choice(((corners[0], corners[3]), (corners[1], corners[2]))))
    else:
        chosen = rng.sample(corners, corner_count)
    if count > len(chosen):
        chosen.append((rng.randint(1, bh - 2), rng.randint(1, bw - 2)))
    available = [(r, c) for r in range(bh) for c in range(bw) if (r, c) not in chosen]
    chosen.extend(rng.sample(available, count - len(chosen)))
    return chosen


def _rich_markers(rng, bh, bw, count):
    corners = {(0, 0), (0, bw - 1), (bh - 1, 0), (bh - 1, bw - 1)}
    if count == 4 or rng.randrange(2) == 0:
        # Three extrema are enough; the fourth point witnesses interior erasure.
        chosen = [(0, 0), (rng.randint(1, bh - 2), bw - 1),
                  (bh - 1, rng.randint(1, bw - 2))]
        forbidden = corners - {(0, 0)}
    else:
        # Four independently located side markers; no occupied bbox corner.
        chosen = [(0, rng.randint(1, bw - 2)), (bh - 1, rng.randint(1, bw - 2)),
                  (rng.randint(1, bh - 2), 0), (rng.randint(1, bh - 2), bw - 1)]
        forbidden = corners
    chosen.append((rng.randint(1, bh - 2), rng.randint(1, bw - 2)))
    available = [(r, c) for r in range(bh) for c in range(bw)
                 if (r, c) not in forbidden and (r, c) not in chosen]
    chosen.extend(rng.sample(available, count - len(chosen)))
    flip_r, flip_c = rng.randrange(2), rng.randrange(2)
    return [(bh - 1 - r if flip_r else r, bw - 1 - c if flip_c else c) for r, c in chosen]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    core = schedule_profile(seed, sample_index, difficulty) == "canonical_corners"
    if core:
        ph, pw = ctx.draw_choice("canonical_shape", _CANONICAL_SHAPES)
        heights, widths = (ph,), (pw,)
    else:
        lo, hi = {"easy": (6, 9), "hard": (13, 22)}.get(difficulty, (9, 14))
        heights, widths = tuple(range(lo, hi + 1)), tuple(range(lo, hi + 1))
    h = _axis(ctx, "grid_h", 4, 24, heights)
    w = _axis(ctx, "grid_w", 5, 24, widths)
    color = ctx.draw_int_strict("color", 1, 9)
    count = _axis(ctx, "num_cells", 2, 7, (3,) if core else (4, 5, 6, 7))
    # Counts 2/3 cannot carry both rich witnesses, so exact requests use a
    # feasible corner construction. Lesson hooks score actual rival behavior.
    rich = not core and count >= 4
    bh, bw = ctx.draw_choice("bbox_span", _feasible_spans(h, w, count, rich))
    rng = ctx.draw_rng("placement")
    top, left = rng.randint(0, h - bh), rng.randint(0, w - bw)
    markers = (_rich_markers if rich else _corner_markers)(ctx.draw_rng("markers"), bh, bw, count)
    grid = full_grid(h, w, 0)
    for r, c in markers:
        grid[top + r][left + c] = color
    return grid


def _markers(grid):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]


def _bounds(points):
    return (min(r for r, _ in points), min(c for _, c in points),
            max(r for r, _ in points), max(c for _, c in points))


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, list) or not grid or any(not isinstance(row, list) or not row for row in grid):
        return ["expected a nonempty list of nonempty row lists"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if not (4 <= h <= 24 and 5 <= w <= 24):
        return ["canvas outside height 4..24 / width 5..24"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integers in 0..9; booleans are not colors"]
    points = _markers(grid)
    if not 2 <= len(points) <= 7:
        return ["expected 2..7 distinct nonzero markers"]
    if len({grid[r][c] for r, c in points}) != 1:
        return ["markers must share one nonzero color"]
    top, left, bottom, right = _bounds(points)
    if bottom - top < 2 or right - left < 2:
        return ["marker bbox must span at least 3 rows and 3 columns"]
    return []


def strict_canonical_like(grid):
    """The literal three-corner submanifold; rich examples are lawful extensions."""
    errors = self_check(grid)
    if errors:
        return errors
    points = _markers(grid)
    top, left, bottom, right = _bounds(points)
    corners = {(top, left), (top, right), (bottom, left), (bottom, right)}
    return [] if len(points) == 3 and set(points) <= corners else ["not the canonical three-corner construction"]


def observe_overrides(grid):
    points = _markers(grid)
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "color": grid[points[0][0]][points[0][1]], "num_cells": len(points)}


def _paint_rival_frame(grid, points, preserve):
    """Shared renderer for deliberately incorrect rivals, never a label source."""
    out = [row[:] for row in grid] if preserve else full_grid(len(grid), len(grid[0]), 0)
    top, left, bottom, right = _bounds(points)
    color = grid[points[0][0]][points[0][1]]
    for r in range(top, bottom + 1):
        out[r][left] = out[r][right] = color
    for c in range(left, right + 1):
        out[top][c] = out[bottom][c] = color
    return out


def _farthest_pair_frame(grid):
    """RIVAL: discard all but the Euclidean-farthest pair of markers."""
    points = _markers(grid)
    pair = max(combinations(points, 2),
               key=lambda ab: (ab[0][0] - ab[1][0]) ** 2 + (ab[0][1] - ab[1][1]) ** 2)
    return _paint_rival_frame(grid, pair, False)


def _preserve_markers_frame(grid):
    """RIVAL: add the frame without erasing strictly interior input markers."""
    return _paint_rival_frame(grid, _markers(grid), True)


def _distributed_extrema(grid):
    points = _markers(grid)
    bounds = _bounds(points)
    return not any(_bounds(pair) == bounds for pair in combinations(points, 2))


def _interior_marker(grid):
    points = _markers(grid)
    top, left, bottom, right = _bounds(points)
    return any(top < r < bottom and left < c < right for r, c in points)


SEMANTIC_WITNESSES = {"distributed_extrema": _distributed_extrema, "interior_erasure": _interior_marker}
SEMANTIC_RIVALS = {"farthest_pair_frame": _farthest_pair_frame, "preserve_markers_frame": _preserve_markers_frame}
WITNESS_RIVALS = {"distributed_extrema": ["farthest_pair_frame"], "interior_erasure": ["preserve_markers_frame"]}
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS
LESSON_COMPETITORS = SEMANTIC_RIVALS


def lesson_identifiable(demos, query):
    """Finite declared-rival check on supplied labels, not universal uniqueness."""
    return [f"{name} fits all demonstrations but changes the query answer"
            for name, rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
            and rival(query["input"]) != query["output"]]
