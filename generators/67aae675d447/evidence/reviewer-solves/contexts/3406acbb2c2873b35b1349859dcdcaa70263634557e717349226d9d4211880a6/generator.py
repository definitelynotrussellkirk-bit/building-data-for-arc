"""Input sampler for local-frame motif bounding-box outlines.

Colors 2/3/4 define a source coordinate frame and 5/6/7 define an
independently oriented target frame.  Color-8 cells within source-local
Chebyshev radius 3 define a motif.  The unchanged Racket authority paints the
perimeter of that motif's local bounding box through the target frame while
preserving every other input cell.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "67aae675d447"
TASK_ID = GENERATOR_ID
RULE_HASH = "e0f86f3cb6ab"
VERSION = "2.0.0"
SUMMARY = (
    "Two orthogonal color tripods define independent source (2/3/4) and target "
    "(5/6/7) coordinates.  Take source-local color-8 cells within radius 3 and "
    "paint only their bounding-box perimeter in color 8 at the target frame."
)
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

INVARIANTS = [
    "exactly one marker of each frame color 2..7; both bases are cardinal and orthogonal",
    "source and target radius-3 squares fit in bounds and do not overlap",
    "the source-local motif contains 3..7 cells and has a 2..6 span on both axes",
    "0..3 optional color-8 distractors lie outside both radius-3 frame squares",
    "source and target orientations are independent across all eight orthogonal bases",
]

AXES = {
    "grid_h": {"type": "int", "default": "10..24; core favors 13", "valid": "10..24"},
    "grid_w": {"type": "int", "default": "14..24; core favors 19", "valid": "14..24"},
    "n_motif": {"type": "int", "default": "3..7; core favors 3", "valid": "3..7"},
    "bbox_u_span": {"type": "int", "default": "2..6; core favors 3", "valid": "2..6"},
    "bbox_v_span": {"type": "int", "default": "2..6; core favors 2", "valid": "2..6"},
    "n_distractors": {"type": "int", "default": "0..3; core favors 0", "valid": "0..3"},
    "source_orientation": {"type": "int", "default": "uniform 0..7", "valid": "0..7"},
    "target_orientation": {"type": "int", "default": "uniform 0..7", "valid": "0..7"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Four rotations followed by the rotations of one reflection.
_BASES = (
    ((0, 1), (1, 0)), ((1, 0), (0, -1)),
    ((0, -1), (-1, 0)), ((-1, 0), (0, 1)),
    ((0, -1), (1, 0)), ((-1, 0), (0, -1)),
    ((0, 1), (-1, 0)), ((1, 0), (0, 1)),
)
_BLOCKED = frozenset({(0, 0), (1, 0), (0, 1)})
_RADIUS = 3
_RANGES = {
    "grid_h": (10, 24),
    "grid_w": (14, 24),
    "n_motif": (3, 7),
    "bbox_u_span": (2, 6),
    "bbox_v_span": (2, 6),
    "n_distractors": (0, 3),
    "source_orientation": (0, 7),
    "target_orientation": (0, 7),
}



def _global(frame, u, v):
    origin, x, y = frame
    return origin[0] + u * x[0] + v * y[0], origin[1] + u * x[1] + v * y[1]


def _local(frame, r, c):
    origin, x, y = frame
    dr, dc = r - origin[0], c - origin[1]
    return dr * x[0] + dc * x[1], dr * y[0] + dc * y[1]


def _put_frame(grid, frame, colors):
    for (u, v), color in zip(((0, 0), (1, 0), (0, 1)), colors):
        r, c = _global(frame, u, v)
        grid[r][c] = color


def _outside_square(point, origin):
    return max(abs(point[0] - origin[0]), abs(point[1] - origin[1])) > _RADIUS


def _draw_weighted_int(ctx, name, lo, hi, *, core, anchor, favored=()):
    choices = list(range(lo, hi + 1))
    if core:
        choices.extend([anchor] * 100)
    else:
        choices.extend(favored)
    return ctx.draw_choice(name, choices)


@lru_cache(maxsize=165)
def _origin_sets(h, w):
    origins = tuple((r, c) for r in range(3, h - 3) for c in range(3, w - 3))
    feasible = tuple(
        source for source in origins
        if any(max(abs(source[0] - target[0]), abs(source[1] - target[1])) >= 7
               for target in origins)
    )
    return origins, feasible


@lru_cache(maxsize=2048)
def _target_origins(h, w, source):
    origins, _ = _origin_sets(h, w)
    return tuple(
        target for target in origins
        if max(abs(source[0] - target[0]), abs(source[1] - target[1])) >= 7
    )


def _frames(ctx, h, w, source_orientation, target_orientation):
    _, feasible = _origin_sets(h, w)
    if not feasible:
        raise ValueError("grid cannot fit two disjoint radius-3 frames")
    source_origin = ctx.draw_rng("source_position").choice(feasible)
    targets = _target_origins(h, w, source_origin)
    target_origin = ctx.draw_rng("target_position").choice(targets)
    return (
        (source_origin, *_BASES[source_orientation]),
        (target_origin, *_BASES[target_orientation]),
    )


@lru_cache(maxsize=175)
def _box_options(u_span, v_span, n_motif):
    """All lawful local boxes and opposite-corner seeds for exact spans."""
    options = []
    for u0 in range(-_RADIUS, _RADIUS - u_span + 1):
        u1 = u0 + u_span
        for v0 in range(-_RADIUS, _RADIUS - v_span + 1):
            v1 = v0 + v_span
            legal = tuple(
                (u, v)
                for u in range(u0, u1 + 1)
                for v in range(v0, v1 + 1)
                if (u, v) not in _BLOCKED
            )
            if len(legal) < n_motif:
                continue
            diagonals = []
            for pair in (((u0, v0), (u1, v1)), ((u0, v1), (u1, v0))):
                if pair[0] in legal and pair[1] in legal:
                    diagonals.append(pair)
            if not diagonals:
                for first in legal:
                    for second in legal:
                        if (min(first[0], second[0]) == u0
                                and max(first[0], second[0]) == u1
                                and min(first[1], second[1]) == v0
                                and max(first[1], second[1]) == v1):
                            diagonals.append((first, second))
            for seed_pair in diagonals:
                options.append((u0, u1, v0, v1, legal, seed_pair))
    return tuple(options)


def _motif_cells(ctx, n_motif, u_span, v_span):
    options = _box_options(u_span, v_span, n_motif)
    if not options:
        raise ValueError("requested motif geometry has no lawful realization")
    _, _, _, _, legal, seed_pair = ctx.draw_rng("bbox_position").choice(options)
    chosen = list(seed_pair)
    remaining = [cell for cell in legal if cell not in chosen]
    chosen.extend(ctx.draw_rng("motif_fill").sample(remaining, n_motif - len(chosen)))
    return tuple(chosen)


def _put_distractors(grid, source, target, count, rng):
    if not count:
        return
    candidates = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0
        and _outside_square((r, c), source[0])
        and _outside_square((r, c), target[0])
    ]
    if len(candidates) < count:
        raise ValueError("grid cannot fit requested exterior distractors")
    for r, c in rng.sample(candidates, count):
        grid[r][c] = 8


def _validate_call(seed, sample_index, overrides):
    if type(seed) is not int:
        raise ValueError("seed must be an integer, not bool/float/string")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer, not bool/float/string")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _RANGES[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name}={value} outside [{lo},{hi}]")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    core = ctx.draw_choice(
        "curriculum_profile", ("core", "core", "core", "broad", "broad")
    ) == "core"
    hard_favor = (20, 21, 22, 23, 24) if difficulty == "hard" else ()
    easy_h_favor = (10, 11, 12, 13, 14) if difficulty == "easy" else ()
    h = _draw_weighted_int(
        ctx, "grid_h", 10, 24, core=core, anchor=13,
        favored=hard_favor or easy_h_favor,
    )
    hard_w_favor = (20, 21, 22, 23, 24) if difficulty == "hard" else ()
    easy_w_favor = (14, 15, 16, 17, 18) if difficulty == "easy" else ()
    w = _draw_weighted_int(
        ctx, "grid_w", 14, 24, core=core, anchor=19,
        favored=hard_w_favor or easy_w_favor,
    )
    n_motif = _draw_weighted_int(
        ctx, "n_motif", 3, 7, core=core, anchor=3,
        favored=(6, 7) if difficulty == "hard" else ((3, 4) if difficulty == "easy" else ()),
    )
    u_span = _draw_weighted_int(
        ctx, "bbox_u_span", 2, 6, core=core, anchor=3,
        favored=(5, 6) if difficulty == "hard" else ((2, 3) if difficulty == "easy" else ()),
    )
    v_span = _draw_weighted_int(
        ctx, "bbox_v_span", 2, 6, core=core, anchor=2,
        favored=(5, 6) if difficulty == "hard" else ((2, 3) if difficulty == "easy" else ()),
    )
    n_distractors = _draw_weighted_int(
        ctx, "n_distractors", 0, 3, core=core, anchor=0,
        favored=(2, 3) if difficulty == "hard" else ((0, 1) if difficulty == "easy" else ()),
    )
    source_orientation = ctx.draw_int_strict("source_orientation", 0, 7)
    target_orientation = ctx.draw_int_strict("target_orientation", 0, 7)
    source, target = _frames(ctx, h, w, source_orientation, target_orientation)

    grid = full_grid(h, w, 0)
    _put_frame(grid, source, (2, 3, 4))
    _put_frame(grid, target, (5, 6, 7))
    for u, v in _motif_cells(ctx, n_motif, u_span, v_span):
        r, c = _global(source, u, v)
        if grid[r][c] != 0:
            raise RuntimeError("constructive motif collided with a source frame marker")
        grid[r][c] = 8
    _put_distractors(
        grid, source, target, n_distractors, ctx.draw_rng("exterior_distractors")
    )
    return grid


def _find_frame(grid, colors):
    positions = {color: [] for color in colors}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in positions:
                positions[value].append((r, c))
    points = []
    for color in colors:
        hits = positions[color]
        if len(hits) != 1:
            raise ValueError(f"expected exactly one color-{color} marker, found {len(hits)}")
        points.append(hits[0])
    origin = points[0]
    x, y = [tuple(point[i] - origin[i] for i in (0, 1)) for point in points[1:]]
    if (x, y) not in _BASES:
        raise ValueError(f"colors {colors} must form an orthogonal cardinal frame")
    return origin, x, y


def _motif(grid, source):
    all_markers = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    }
    near = {
        _local(source, r, c)
        for r, c in all_markers
        if max(abs(_local(source, r, c)[0]), abs(_local(source, r, c)[1])) <= _RADIUS
    }
    return near, all_markers


def _observed(grid, source, target):
    near, all_markers = _motif(grid, source)
    if not near:
        raise ValueError("source-local motif is empty")
    near_global = {_global(source, u, v) for u, v in near}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_motif": len(near),
        "bbox_u_span": max(u for u, _ in near) - min(u for u, _ in near),
        "bbox_v_span": max(v for _, v in near) - min(v for _, v in near),
        "n_distractors": len(all_markers - near_global),
        "source_orientation": _BASES.index(source[1:]),
        "target_orientation": _BASES.index(target[1:]),
    }


def observe_overrides(grid):
    """Recover every declared axis from returned pixels."""
    source = _find_frame(grid, (2, 3, 4))
    target = _find_frame(grid, (5, 6, 7))
    return _observed(grid, source, target)


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or value not in (0, 2, 3, 4, 5, 6, 7, 8)
           for row in grid for value in row):
        return ["cells must be integer colors from 0,2,3,4,5,6,7,8"]
    h, w = len(grid), width
    errors = []
    if not 10 <= h <= 24:
        errors.append(f"grid_h={h} outside [10,24]")
    if not 14 <= w <= 24:
        errors.append(f"grid_w={w} outside [14,24]")
    try:
        source = _find_frame(grid, (2, 3, 4))
        target = _find_frame(grid, (5, 6, 7))
    except ValueError as exc:
        return errors + [str(exc)]
    for name, frm in (("source", source), ("target", target)):
        r, c = frm[0]
        if not (3 <= r < h - 3 and 3 <= c < w - 3):
            errors.append(f"{name} radius-3 square must fit in bounds")
    if max(abs(source[0][i] - target[0][i]) for i in (0, 1)) < 7:
        errors.append("source and target radius-3 squares overlap")
    if any(
        value == 8 and not _outside_square((r, c), target[0])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
    ):
        errors.append("target radius-3 square must initially contain no color-8 marker")
    try:
        observed = _observed(grid, source, target)
    except ValueError as exc:
        return errors + [str(exc)]
    for name, lo, hi in (
        ("n_motif", 3, 7),
        ("bbox_u_span", 2, 6),
        ("bbox_v_span", 2, 6),
        ("n_distractors", 0, 3),
    ):
        if not lo <= observed[name] <= hi:
            errors.append(f"{name}={observed[name]} outside [{lo},{hi}]")
    return errors


def strict_canonical_like(grid):
    """The sampler's full lawful manifold; canonical inputs are a supported subset."""
    return self_check(grid)


def _bbox(grid):
    source = _find_frame(grid, (2, 3, 4))
    target = _find_frame(grid, (5, 6, 7))
    near, _ = _motif(grid, source)
    if not near:
        raise ValueError("source-local motif is empty")
    bounds = (
        min(u for u, _ in near), max(u for u, _ in near),
        min(v for _, v in near), max(v for _, v in near),
    )
    return source, target, near, bounds


def _render(grid, mode):
    source, target, near, (u0, u1, v0, v1) = _bbox(grid)
    out = deepcopy(grid)
    if mode == "copy_motif":
        cells = near
        target_frame = target
    elif mode == "corners_only":
        cells = {(u0, v0), (u0, v1), (u1, v0), (u1, v1)}
        target_frame = target
    elif mode == "solid_bbox":
        cells = {(u, v) for u in range(u0, u1 + 1) for v in range(v0, v1 + 1)}
        target_frame = target
    else:
        cells = {
            (u, v)
            for u in range(u0, u1 + 1)
            for v in range(v0, v1 + 1)
            if u in (u0, u1) or v in (v0, v1)
        }
        target_frame = (target[0], source[1], source[2]) if mode == "source_basis_at_target" else target
    for u, v in cells:
        r, c = _global(target_frame, u, v)
        out[r][c] = 8
    return out


def rule_mirror(grid):
    """Pure Python mirror used only by focused tests and semantic rivals."""
    return _render(grid, "perimeter")


def _copy_motif(grid):
    return _render(grid, "copy_motif")


def _corners_only(grid):
    return _render(grid, "corners_only")


def _solid_bbox(grid):
    return _render(grid, "solid_bbox")


def _source_basis_at_target(grid):
    return _render(grid, "source_basis_at_target")


def _differs_from(rival, grid):
    return rival(grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {
    "copy_motif": _copy_motif,
    "corners_only": _corners_only,
    "solid_bbox": _solid_bbox,
    "source_basis_at_target": _source_basis_at_target,
}
SEMANTIC_WITNESSES = {
    "outline_not_verbatim_motif": lambda grid: _differs_from(_copy_motif, grid),
    "outline_has_noncorner_edges": lambda grid: _differs_from(_corners_only, grid),
    "outline_not_solid_fill": lambda grid: _differs_from(_solid_bbox, grid),
    "independent_target_orientation": lambda grid: _differs_from(_source_basis_at_target, grid),
}
WITNESS_RIVALS = {
    "outline_not_verbatim_motif": ["copy_motif"],
    "outline_has_noncorner_edges": ["corners_only"],
    "outline_not_solid_fill": ["solid_bbox"],
    "independent_target_orientation": ["source_basis_at_target"],
}
# Each of these three is refuted by every lawful generated example, so lesson
# quality does not depend on a lucky orientation draw or a hidden schedule.
LESSON_COMPETITORS = {
    "copy_motif": _copy_motif,
    "corners_only": _corners_only,
    "solid_bbox": _solid_bbox,
}


def lesson_identifiable(demos, query):
    """Reject a lesson only when a declared competitor survives demos but changes query."""
    reasons = []
    if not demos:
        return ["lesson has no demonstrations"]
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demo but disagrees with query")
    return reasons
