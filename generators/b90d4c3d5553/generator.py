"""Input sampler for local-frame reflection, arc_puzzle_bank_21_set22_s:S22_H5.

The unchanged Racket authority retains (u,v) iff (-u,v) is also a local marker,
including self-mirrors at u=0. Outputs are NOT generated here. See workspace/
for an independent test oracle, coverage probe, and reproducible counterexample.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "b90d4c3d5553"
TASK_ID = GENERATOR_ID
RULE_HASH = "a9a48a6b2948"
VERSION = "2.0.0"
SUMMARY = (
    "Two independently oriented color tripods define source (2/3/4) and target "
    "(5/6/7) coordinates. Copy source-local 8-markers within radius 3 exactly "
    "when their reflection (u,v)->(-u,v) exists, including axis self-mirrors. "
    "Other cells, including distant 8-distractors, remain unchanged."
)

INVARIANTS = [
    "exactly one marker of each frame color 2..7; both bases are cardinal and orthogonal",
    "source and target radius-3 squares fit and are disjoint; their relative positions vary",
    "source motif contains 1..6 distinct mirror pairs, 0..4 unpaired cells, and 0..5 axis cells",
    "0..4 exterior 8-distractors lie outside both frame squares",
    "all copied cells land on background; the full motif counts are realized without dropping cells",
]

AXES = {
    "grid_h": {"type": "int", "default": "10..24; core mode favors 12", "valid": "10..24"},
    "grid_w": {"type": "int", "default": "14..24; core mode favors 18", "valid": "14..24"},
    "n_pairs": {"type": "int", "default": "1..6; core mode favors 2", "valid": "1..6"},
    "n_noise": {"type": "int", "default": "0..4; core mode favors 1", "valid": "0..4"},
    "n_axis": {"type": "int", "default": "0..5; core mode favors 0", "valid": "0..5"},
    "n_distractors": {"type": "int", "default": "0..4; core mode favors 0", "valid": "0..4"},
    "source_orientation": {"type": "int", "default": "uniform 0..7", "valid": "0..7"},
    "target_orientation": {"type": "int", "default": "uniform 0..7", "valid": "0..7"},
}
# Every advertised combination is constructive, including the 10x14 boundary.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

# Clockwise rotations of (x=east,y=south), then rotations of its reflection.
_BASES = (
    ((0, 1), (1, 0)), ((1, 0), (0, -1)),
    ((0, -1), (-1, 0)), ((-1, 0), (0, 1)),
    ((0, -1), (1, 0)), ((-1, 0), (0, -1)),
    ((0, 1), (-1, 0)), ((1, 0), (0, 1)),
)
_BLOCKED = frozenset({(0, 0), (1, 0), (0, 1)})
_RADIUS = 3


def _global(frame, u, v):
    origin, x, y = frame
    return origin[0] + u*x[0] + v*y[0], origin[1] + u*x[1] + v*y[1]


def _local(frame, r, c):
    origin, x, y = frame
    dr, dc = r-origin[0], c-origin[1]
    return dr*x[0]+dc*x[1], dr*y[0]+dc*y[1]


def _put_frame(grid, frame, colors):
    for (u,v), color in zip(((0,0),(1,0),(0,1)), colors):
        r,c = _global(frame,u,v)
        grid[r][c] = color


def _outside(point, origin):
    return max(abs(point[0]-origin[0]), abs(point[1]-origin[1])) > _RADIUS


def _draw_count(ctx, name, lo, hi, *, core, anchor, favored=()):
    # Weighted choices keep the ENTIRE documented override domain in every band.
    # No post-draw clipping, discarded overrides, or falsely recorded values.
    choices = list(range(lo, hi+1))
    choices += [anchor]*100 if core else list(favored)
    return ctx.draw_choice(name, choices)


@lru_cache(maxsize=165)
def _origin_sets(h, w):
    """Cache only immutable geometry, never draws or generated grids."""
    origins = tuple((r,c) for r in range(3,h-3) for c in range(3,w-3))
    # Test feasibility before drawing a source: a central source in a small
    # canvas may admit no disjoint target. This avoids capped rejection loops.
    feasible = tuple(p for p in origins if max(p[0]-3,h-4-p[0],p[1]-3,w-4-p[1]) >= 7)
    return origins, feasible


@lru_cache(maxsize=2048)
def _target_origins(h, w, src):
    origins,_ = _origin_sets(h,w)
    return tuple(p for p in origins if max(abs(src[0]-p[0]),abs(src[1]-p[1])) >= 7)


def _frames(ctx, h, w, source_orientation, target_orientation):
    _,feasible = _origin_sets(h,w)
    if not feasible:
        raise ValueError("grid cannot fit two disjoint radius-3 frames")
    src = ctx.draw_rng("source_position").choice(feasible)
    targets = _target_origins(h,w,src)
    tgt = ctx.draw_rng("target_position").choice(targets)
    return ((src, *_BASES[source_orientation]), (tgt, *_BASES[target_orientation]))


def _gen_motif(ctx, n_pairs, n_noise, n_axis):
    # Each off-axis reflection orbit is represented exactly once by positive u.
    orbits = [(u,v) for u in range(1,4) for v in range(-3,4)]
    pair_slots = [(u,v) for u,v in orbits if (u,v) not in _BLOCKED and (-u,v) not in _BLOCKED]
    chosen = ctx.draw_rng("paired_orbits").sample(pair_slots,n_pairs)
    cells = [(sign*u,v) for u,v in chosen for sign in (-1,1)]
    # Noise is drawn from distinct remaining orbits, preventing accidental pairs.
    # The orbit containing marker 3 is also lawful: only its free side can be 8.
    noise_rng = ctx.draw_rng("unpaired_orbits")
    remaining = [uv for uv in orbits if uv not in chosen]
    for u,v in noise_rng.sample(remaining,n_noise):
        cells.append(noise_rng.choice([p for p in ((u,v),(-u,v)) if p not in _BLOCKED]))
    axes = [(0,v) for v in range(-3,4) if (0,v) not in _BLOCKED]
    cells.extend(ctx.draw_rng("axis_markers").sample(axes,n_axis))
    return cells


def _put_distractors(grid, src, tgt, count, rng):
    if not count:
        return
    candidates = [(r,c) for r in range(len(grid)) for c in range(len(grid[0]))
                  if grid[r][c] == 0 and _outside((r,c),src[0]) and _outside((r,c),tgt[0])]
    allowed = set(candidates)
    chosen = []
    if count >= 2:
        # Prefer an exterior mirrored pair, which distinguishes radius-bounded
        # filtering from a "copy every symmetric marker anywhere" rival.
        pairs = []
        for point in candidates:
            u,v = _local(src,*point)
            mirror = _global(src,-u,v)
            if u > 0 and mirror in allowed:
                pairs.append((point,mirror))
        if pairs:
            chosen.extend(rng.choice(pairs))
    remaining = [p for p in candidates if p not in chosen]
    chosen.extend(rng.sample(remaining,count-len(chosen)))
    for r,c in chosen:
        grid[r][c] = 8


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name,value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    # Preserve a sparse canonical-density component without replaying any grid.
    # Frame orientations and positions remain independent in BOTH components.
    core = ctx.draw_choice("curriculum_profile", ("core","broad")) == "core"
    favored_pairs = (1,2,3) if difficulty == "easy" else ((4,5,6) if difficulty == "hard" else ())
    favored_noise = (0,1,2) if difficulty == "easy" else ((2,3,4) if difficulty == "hard" else ())
    h = _draw_count(ctx,"grid_h",10,24,core=core,anchor=12)
    w = _draw_count(ctx,"grid_w",14,24,core=core,anchor=18)
    pairs = _draw_count(ctx,"n_pairs",1,6,core=core,anchor=2,favored=favored_pairs)
    noise = _draw_count(ctx,"n_noise",0,4,core=core,anchor=1,favored=favored_noise)
    axes = _draw_count(ctx,"n_axis",0,5,core=core,anchor=0)
    distractors = _draw_count(ctx,"n_distractors",0,4,core=core,anchor=0)
    so = ctx.draw_int("source_orientation",0,7)
    to = ctx.draw_int("target_orientation",0,7)
    src,tgt = _frames(ctx,h,w,so,to)
    grid = full_grid(h,w,0)
    _put_frame(grid,src,(2,3,4))
    _put_frame(grid,tgt,(5,6,7))
    for u,v in _gen_motif(ctx,pairs,noise,axes):
        r,c = _global(src,u,v)
        if grid[r][c] != 0:
            raise RuntimeError("constructive placement collided; refusing a shortened motif")
        grid[r][c] = 8
    _put_distractors(grid,src,tgt,distractors,ctx.draw_rng("exterior_markers"))
    return grid


def _find_frame(grid, colors):
    positions = {color: [] for color in colors}
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            if value in positions:
                positions[value].append((r,c))
    points = []
    for color in colors:
        hits = positions[color]
        if len(hits) != 1:
            raise ValueError(f"expected exactly one color-{color} marker, found {len(hits)}")
        points.append(hits[0])
    origin = points[0]
    x,y = [tuple(p[i]-origin[i] for i in (0,1)) for p in points[1:]]
    if (x,y) not in _BASES:
        raise ValueError(f"colors {colors} must form an orthogonal cardinal frame")
    return origin,x,y


def _motif(grid, src):
    markers = {_local(src,r,c) for r,row in enumerate(grid) for c,color in enumerate(row) if color == 8}
    return {p for p in markers if max(abs(p[0]),abs(p[1])) <= _RADIUS}, markers


def observe_overrides(grid):
    """Recover every exact axis from returned pixels, not RNG bookkeeping."""
    src,tgt = _find_frame(grid,(2,3,4)),_find_frame(grid,(5,6,7))
    return _observed_counts(grid,src,tgt)


def _observed_counts(grid,src,tgt):
    near,all_markers = _motif(grid,src)
    return {
        "grid_h":len(grid), "grid_w":len(grid[0]),
        "n_pairs":sum(u > 0 and (-u,v) in near for u,v in near),
        "n_noise":sum((-u,v) not in near for u,v in near),
        "n_axis":sum(u == 0 for u,v in near),
        "n_distractors":len(all_markers-near),
        "source_orientation":_BASES.index(src[1:]),
        "target_orientation":_BASES.index(tgt[1:]),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid,(list,tuple)) or not grid or not isinstance(grid[0],(list,tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row,(list,tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or v not in (0,2,3,4,5,6,7,8) for row in grid for v in row):
        return ["cells must be integer colors from 0,2,3,4,5,6,7,8"]
    try:
        src,tgt = _find_frame(grid,(2,3,4)),_find_frame(grid,(5,6,7))
    except ValueError as exc:
        return [str(exc)]
    h,w = len(grid),len(grid[0])
    errors = []
    for name,frame in (("source",src),("target",tgt)):
        r,c=frame[0]
        if not (3 <= r < h-3 and 3 <= c < w-3):
            errors.append(f"{name} radius-3 square must fit in bounds")
    if max(abs(src[0][i]-tgt[0][i]) for i in (0,1)) < 7:
        errors.append("source and target radius-3 squares overlap")
    if any(v == 8 and not _outside((r,c),tgt[0]) for r,row in enumerate(grid) for c,v in enumerate(row)):
        errors.append("target radius-3 square must initially contain no 8-marker")
    obs = _observed_counts(grid,src,tgt)
    for name,lo,hi in (("n_pairs",1,6),("n_noise",0,4),("n_axis",0,5),("n_distractors",0,4)):
        if not lo <= obs[name] <= hi:
            errors.append(f"{name}={obs[name]} outside [{lo},{hi}]")
    return errors


def strict_canonical_like(grid):
    """Lawful rule instances in this sampler's declared manifold, not a shape test."""
    return self_check(grid)


def _distinct_pairs_only(grid):
    """RIVAL, not label authority: incorrectly drops self-mirrors on the y-axis."""
    src,tgt = _find_frame(grid,(2,3,4)),_find_frame(grid,(5,6,7))
    near,_ = _motif(grid,src)
    out=[list(row) for row in grid]
    for u,v in sorted(near):
        if u != 0 and (-u,v) in near:
            r,c=_global(tgt,u,v)
            out[r][c]=8
    return out


def _has_axis_marker(grid):
    return observe_overrides(grid)["n_axis"] > 0


SEMANTIC_WITNESSES = {"self_mirror":_has_axis_marker}
SEMANTIC_RIVALS = {"distinct_pairs_only":_distinct_pairs_only}
WITNESS_RIVALS = {"self_mirror":["distinct_pairs_only"]}
CANONICAL_SHORTCUTS = {"distinct_pairs_only":_distinct_pairs_only}
LESSON_COMPETITORS = {"distinct_pairs_only":_distinct_pairs_only}
