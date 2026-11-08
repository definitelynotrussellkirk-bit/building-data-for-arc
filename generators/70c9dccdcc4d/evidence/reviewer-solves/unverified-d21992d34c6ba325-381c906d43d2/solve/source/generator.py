"""Input sampler for diagonal reflection between two local L-frames.

The unchanged Racket authority reads color-8 markers within source-local
Chebyshev radius 3, swaps each local coordinate ``(u, v) -> (v, u)``, and
paints the transformed markers in the target frame.  Distant 8-markers are
ignored.  Outputs are never generated here.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "70c9dccdcc4d"
TASK_ID = GENERATOR_ID
RULE_HASH = "06513d532f1c"
VERSION = "2.0.0"
SUMMARY = (
    "Colors 2/3/4 and 5/6/7 form independently oriented local coordinate "
    "frames, with 2 and 5 at their origins.  Only color-8 markers within "
    "source-local Chebyshev radius 3 are copied; their coordinates are "
    "transposed (u,v)->(v,u) into the target frame.  Exterior 8-distractors "
    "remain unchanged."
)

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "exactly one marker of each frame color 2..7, forming two cardinal orthogonal frames",
    "source and target radius-3 neighborhoods fit in bounds and do not overlap",
    "1..6 near source markers map to distinct blank target cells under (u,v)->(v,u)",
    "0..4 exterior color-8 distractors are outside both frame neighborhoods",
    "every ordinary draw includes a radius-filter witness and a non-symmetric near motif",
]

AXES = {
    "grid_h": {"type": "int", "default": "10..24; weighted toward 12", "valid": "10..24"},
    "grid_w": {"type": "int", "default": "14..24; weighted toward 18", "valid": "14..24"},
    "n_marks": {"type": "int", "default": "1..6; weighted toward 3", "valid": "1..6"},
    "n_distractors": {"type": "int", "default": "1..4; exact override also permits 0", "valid": "0..4"},
    "source_orientation": {"type": "int", "default": "uniform 0..7", "valid": "0..7"},
    "target_orientation": {"type": "int", "default": "uniform 0..7", "valid": "0..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Clockwise rotations of (x=east,y=south), then rotations of its reflection.
_BASES = (
    ((0, 1), (1, 0)), ((1, 0), (0, -1)),
    ((0, -1), (-1, 0)), ((-1, 0), (0, 1)),
    ((0, -1), (1, 0)), ((-1, 0), (0, -1)),
    ((0, 1), (-1, 0)), ((1, 0), (0, 1)),
)
_RADIUS = 3
_FRAME_LOCAL = frozenset({(0, 0), (1, 0), (0, 1)})
_TEMPLATE_H = 10
_TEMPLATE_W = 14


def _global(frame, u, v):
    origin, x_axis, y_axis = frame
    return (
        origin[0] + u * x_axis[0] + v * y_axis[0],
        origin[1] + u * x_axis[1] + v * y_axis[1],
    )


def _local(frame, row, col):
    origin, x_axis, y_axis = frame
    dr, dc = row - origin[0], col - origin[1]
    return (
        dr * x_axis[0] + dc * x_axis[1],
        dr * y_axis[0] + dc * y_axis[1],
    )


def _outside_radius(point, origin):
    return max(abs(point[0] - origin[0]), abs(point[1] - origin[1])) > _RADIUS


def _put_frame(grid, frame, colors):
    for point, color in zip(((0, 0), (1, 0), (0, 1)), colors):
        row, col = _global(frame, *point)
        grid[row][col] = color


def _draw_weighted_int(ctx, name, lo, hi, *, anchor, favored=()):
    """Exact keyed choice with a weighted curriculum but a full legal domain."""
    choices = list(range(lo, hi + 1))
    choices.extend([anchor] * 12)
    choices.extend(favored)
    return ctx.draw_choice(name, choices)


def _candidate_distractors(source, target):
    """Distant source-local points whose unbounded-rival targets stay blankable."""
    candidates = []
    for row in range(_TEMPLATE_H):
        for col in range(_TEMPLATE_W):
            source_point = (row, col)
            if not _outside_radius(source_point, source[0]):
                continue
            if not _outside_radius(source_point, target[0]):
                continue
            u, v = _local(source, row, col)
            rival_point = _global(target, v, u)
            if not (0 <= rival_point[0] < _TEMPLATE_H and 0 <= rival_point[1] < _TEMPLATE_W):
                continue
            if not _outside_radius(rival_point, source[0]):
                continue
            if not _outside_radius(rival_point, target[0]):
                continue
            if source_point == rival_point:
                continue
            candidates.append(((u, v), source_point, rival_point))
    return tuple(candidates)


def _choose_disjoint_distractors(candidates, count=4):
    """Return one deterministic endpoint-disjoint witness set, or None."""
    ordered = sorted(candidates, key=lambda item: (item[1], item[2], item[0]))

    def search(start, chosen, occupied):
        if len(chosen) == count:
            return tuple(item[0] for item in chosen)
        remaining = count - len(chosen)
        if len(ordered) - start < remaining:
            return None
        for index in range(start, len(ordered)):
            item = ordered[index]
            _, source_point, rival_point = item
            if source_point in occupied or rival_point in occupied:
                continue
            result = search(
                index + 1,
                chosen + (item,),
                occupied | {source_point, rival_point},
            )
            if result is not None:
                return result
        return None

    return search(0, (), frozenset())


@lru_cache(maxsize=64)
def _base_layouts(source_orientation, target_orientation):
    """Constructive 10x14 templates supporting all four distant witnesses."""
    source_basis = _BASES[source_orientation]
    target_basis = _BASES[target_orientation]
    origins = tuple(
        (row, col)
        for row in range(3, _TEMPLATE_H - 3)
        for col in range(3, _TEMPLATE_W - 3)
    )
    layouts = []
    for source_origin in origins:
        for target_origin in origins:
            if max(
                abs(source_origin[0] - target_origin[0]),
                abs(source_origin[1] - target_origin[1]),
            ) < 7:
                continue
            source = (source_origin, *source_basis)
            target = (target_origin, *target_basis)
            distant = _choose_disjoint_distractors(_candidate_distractors(source, target))
            if distant is not None:
                layouts.append((source_origin, target_origin, distant))
    if not layouts:
        raise RuntimeError(
            f"no constructive template for orientations {source_orientation}/{target_orientation}"
        )
    return tuple(layouts)


def _near_motif(ctx, count):
    """Choose a motif that necessarily distinguishes transpose from no-swap."""
    candidates = [
        (u, v)
        for u in range(-_RADIUS, _RADIUS + 1)
        for v in range(-_RADIUS, _RADIUS + 1)
        if (u, v) not in _FRAME_LOCAL
        and (u, v) not in {(0, 0)}
        and (u, v) not in _FRAME_LOCAL  # copy-without-swap target stays off the frame
        and (v, u) not in _FRAME_LOCAL  # intended target stays off the frame
    ]
    asymmetric = [(u, v) for u, v in candidates if u != v and (v, u) in candidates]
    rng = ctx.draw_rng("near_motif")
    witness = rng.choice(asymmetric)
    forbidden = (witness[1], witness[0])
    remaining = [point for point in candidates if point not in {witness, forbidden}]
    return (witness, *rng.sample(remaining, count - 1))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if difficulty == "easy":
        favored_marks = (1, 2, 3)
    elif difficulty == "hard":
        favored_marks = (4, 5, 6)
    else:
        favored_marks = ()

    height = _draw_weighted_int(ctx, "grid_h", 10, 24, anchor=12)
    width = _draw_weighted_int(ctx, "grid_w", 14, 24, anchor=18)
    n_marks = _draw_weighted_int(
        ctx, "n_marks", 1, 6, anchor=3, favored=favored_marks
    )
    # Ordinary lessons always teach the radius bound.  Exact callers may request 0.
    if "n_distractors" in overrides and overrides["n_distractors"] is not None:
        n_distractors = ctx.draw_int_strict("n_distractors", 0, 4)
    else:
        n_distractors = ctx.draw_choice("n_distractors", (1, 1, 1, 2, 3, 4))
    source_orientation = ctx.draw_int_strict("source_orientation", 0, 7)
    target_orientation = ctx.draw_int_strict("target_orientation", 0, 7)

    layouts = _base_layouts(source_orientation, target_orientation)
    base_source, base_target, distant_pool = ctx.draw_rng("frame_layout").choice(layouts)
    row_shift = ctx.draw_int("layout_row_shift", 0, height - _TEMPLATE_H)
    col_shift = ctx.draw_int("layout_col_shift", 0, width - _TEMPLATE_W)
    source_origin = (base_source[0] + row_shift, base_source[1] + col_shift)
    target_origin = (base_target[0] + row_shift, base_target[1] + col_shift)
    source = (source_origin, *_BASES[source_orientation])
    target = (target_origin, *_BASES[target_orientation])

    grid = full_grid(height, width, 0)
    _put_frame(grid, source, (2, 3, 4))
    _put_frame(grid, target, (5, 6, 7))

    for u, v in _near_motif(ctx, n_marks):
        row, col = _global(source, u, v)
        if grid[row][col] != 0:
            raise RuntimeError("near-motif construction collided with a frame")
        grid[row][col] = 8

    for u, v in ctx.draw_rng("distant_markers").sample(list(distant_pool), n_distractors):
        row, col = _global(source, u, v)
        if grid[row][col] != 0:
            raise RuntimeError("distant-marker construction collided")
        grid[row][col] = 8
    return grid


def _find_frame(grid, colors):
    positions = {color: [] for color in colors}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in positions:
                positions[value].append((row, col))
    points = []
    for color in colors:
        hits = positions[color]
        if len(hits) != 1:
            raise ValueError(f"expected exactly one color-{color} marker, found {len(hits)}")
        points.append(hits[0])
    origin = points[0]
    x_axis, y_axis = [
        tuple(point[index] - origin[index] for index in (0, 1))
        for point in points[1:]
    ]
    if (x_axis, y_axis) not in _BASES:
        raise ValueError(f"colors {colors} must form an orthogonal cardinal frame")
    return origin, x_axis, y_axis


def _marker_sets(grid, source):
    all_markers = {
        _local(source, row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 8
    }
    near = {
        point
        for point in all_markers
        if max(abs(point[0]), abs(point[1])) <= _RADIUS
    }
    return near, all_markers - near


def observe_overrides(grid):
    """Recover every advertised exact axis from returned pixels."""
    source = _find_frame(grid, (2, 3, 4))
    target = _find_frame(grid, (5, 6, 7))
    near, distant = _marker_sets(grid, source)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_marks": len(near),
        "n_distractors": len(distant),
        "source_orientation": _BASES.index(source[1:]),
        "target_orientation": _BASES.index(target[1:]),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not isinstance(grid[0], (list, tuple))
        or not grid[0]
    ):
        return ["expected a nonempty rectangular grid"]
    if any(
        not isinstance(row, (list, tuple)) or len(row) != len(grid[0])
        for row in grid
    ):
        return ["grid must be rectangular"]
    if any(
        type(value) is not int or value not in (0, 2, 3, 4, 5, 6, 7, 8)
        for row in grid
        for value in row
    ):
        return ["cells must be integer colors from 0,2,3,4,5,6,7,8"]

    try:
        source = _find_frame(grid, (2, 3, 4))
        target = _find_frame(grid, (5, 6, 7))
    except ValueError as exc:
        return [str(exc)]

    height, width = len(grid), len(grid[0])
    errors = []
    for name, local_frame in (("source", source), ("target", target)):
        row, col = local_frame[0]
        if not (3 <= row < height - 3 and 3 <= col < width - 3):
            errors.append(f"{name} radius-3 neighborhood must fit in bounds")
    if max(
        abs(source[0][0] - target[0][0]),
        abs(source[0][1] - target[0][1]),
    ) < 7:
        errors.append("source and target radius-3 neighborhoods must be disjoint")

    near, distant = _marker_sets(grid, source)
    if not 1 <= len(near) <= 6:
        errors.append(f"n_marks={len(near)} outside [1,6]")
    if not 0 <= len(distant) <= 4:
        errors.append(f"n_distractors={len(distant)} outside [0,4]")
    if near == {(v, u) for u, v in near}:
        errors.append("near motif must distinguish diagonal transpose from no-swap copying")

    target_cells = set()
    for u, v in near:
        row, col = _global(target, v, u)
        if not (0 <= row < height and 0 <= col < width):
            errors.append("a transposed near marker lands out of bounds")
            continue
        if grid[row][col] != 0:
            errors.append("a transposed near marker does not land on background")
        target_cells.add((row, col))
    if len(target_cells) != len(near):
        errors.append("two near markers collide after diagonal transpose")

    for u, v in distant:
        source_point = _global(source, u, v)
        if not _outside_radius(source_point, target[0]):
            errors.append("distant markers must also lie outside the target neighborhood")
        rival_point = _global(target, v, u)
        if not (0 <= rival_point[0] < height and 0 <= rival_point[1] < width):
            errors.append("a distant rival target lands out of bounds")
            continue
        if grid[rival_point[0]][rival_point[1]] != 0:
            errors.append("a distant rival target does not land on background")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


def _solve(grid, *, radius_bounded, swap):
    source = _find_frame(grid, (2, 3, 4))
    target = _find_frame(grid, (5, 6, 7))
    height, width = len(grid), len(grid[0])
    output = deepcopy(grid)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 8:
                continue
            u, v = _local(source, row, col)
            if radius_bounded and max(abs(u), abs(v)) > _RADIUS:
                continue
            target_point = _global(target, v, u) if swap else _global(target, u, v)
            if 0 <= target_point[0] < height and 0 <= target_point[1] < width:
                output[target_point[0]][target_point[1]] = 8
    return output


def _apply_rule(grid):
    """Supplementary Python mirror; the canonical Racket program remains authority."""
    return _solve(grid, radius_bounded=True, swap=True)


def _transpose_all_eights(grid):
    """RIVAL: omit the source-local radius-3 filter."""
    return _solve(grid, radius_bounded=False, swap=True)


def _copy_without_swap(grid):
    """RIVAL: copy local coordinates without the diagonal transpose."""
    return _solve(grid, radius_bounded=True, swap=False)


def _has_radius_counterexample(grid):
    return _apply_rule(grid) != _transpose_all_eights(grid)


def _has_diagonal_counterexample(grid):
    return _apply_rule(grid) != _copy_without_swap(grid)


SEMANTIC_WITNESSES = {
    "radius_filter": _has_radius_counterexample,
    "diagonal_swap": _has_diagonal_counterexample,
}
SEMANTIC_RIVALS = {
    "transpose_all_eights": _transpose_all_eights,
    "copy_without_swap": _copy_without_swap,
}
WITNESS_RIVALS = {
    "radius_filter": ["transpose_all_eights"],
    "diagonal_swap": ["copy_without_swap"],
}
CANONICAL_SHORTCUTS = {"transpose_all_eights": _transpose_all_eights}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Report any declared rival that fits the demonstrations but flips query."""
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons
