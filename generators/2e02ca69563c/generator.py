"""Lawful input sampler for Per-Frame Endpoint Routing (bank H55).

Racket is the unchanged output authority. Pair counts are LOCAL to each frame;
the row-major first endpoint routes horizontally and then vertically. Default
three-draw lessons mix canonical-scale, broad, and containment-contrast inputs.
See workspace/ for independent reference comparisons and complete-lesson probes.
"""
from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from itertools import combinations, product

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "2e02ca69563c"
TASK_ID = GENERATOR_ID
RULE_HASH = "024c6f6dd0fa"
VERSION = "3.0.0"
SUMMARY = (
    "One to three disjoint rectangular frames on background 0. Each frame has "
    "one or two endpoint colors occurring exactly twice locally; colors may "
    "recur in other frames. Connect each pair horizontally from the row-major "
    "first endpoint, then vertically. Optional singleton/triple colors stay "
    "unchanged. Full routed paths are reserved, so no endpoint is overwritten."
)
EXAMPLES_NEEDED = 3
INVARIANTS = [
    "background 0, integer colors 0..9, disjoint solid rectangular frame borders",
    "each frame has one or two routed colors, each occurring exactly twice locally",
    "routed paths lie inside their frame and do not intersect other paths or markers",
    "optional ignored interior color has exactly one or three cells per frame",
    "all exact axes are recovered from pixels; impossible combinations raise explicitly",
]
AXES = {
    "grid_h": {"type":"int", "default":"9..30; canonical component 12", "valid":"9..30"},
    "grid_w": {"type":"int", "default":"9..30; canonical component 14", "valid":"9..30"},
    "n_frames": {"type":"int", "default":"1..3; core/contrast 2", "valid":"1..3"},
    "frame_h": {"type":"int", "default":"4..10, subject to packing", "valid":"4..10"},
    "frame_w": {"type":"int", "default":"4..10, subject to packing", "valid":"4..10"},
    "pairs_per_frame": {"type":"int", "default":"1..2; contrast 2", "valid":"1..2"},
    "frame_color": {"type":"int", "default":"1..9; core 8, contrast not 8", "valid":"1..9"},
    "shared_pairs": {"type":"int", "default":"0..1; 1 reuses pair colors across frames", "valid":"0..1"},
    "n_ignored": {"type":"int", "default":"0|1|3; count of the ignored color in each frame", "valid":"0|1|3"},
}
# Structured exceptions below name the actual requested axes. No blanket waiver.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
_GEOMETRY_FIELDS = ("n_frames","pairs_per_frame","n_ignored","frame_h","frame_w")
_DOMAINS = {
    "grid_h": tuple(range(9,31)), "grid_w": tuple(range(9,31)),
    "n_frames": (1,2,3), "frame_h": tuple(range(4,11)),
    "frame_w": tuple(range(4,11)), "pairs_per_frame": (1,2),
    "frame_color": tuple(range(1,10)), "shared_pairs": (0,1), "n_ignored": (0,1,3),
}


class IncompatibleOverrides(ValueError):
    """A valid individual control cannot be combined with the other controls."""
    def __init__(self, axes, message):
        self.incompatible_axes = tuple(sorted(axes))
        super().__init__(f"incompatible axes {self.incompatible_axes}: {message}")


@lru_cache(maxsize=1)
def _geometries():
    """Immutable feasible geometry, never random draws or generated examples."""
    choices = []
    for n,p,noise,fh,fw in product((1,2,3),(1,2),(0,1,3),range(4,11),range(4,11)):
        ih,iw = fh-2,fw-2
        # p disjoint strips with a 2x2 minimum each, plus reserved ignored cells.
        if not (ih >= 2*p or iw >= 2*p) or ih*iw < 3*p+noise:
            continue
        packings = {(1,n),(n,1)}
        if n > 1:
            packings.add((2,2))  # includes diagonal layouts, not just a row
        for rows,cols in sorted(packings):
            mh,mw = rows*fh+rows-1,cols*fw+cols-1
            if mh <= 30 and mw <= 30:
                choices.append((n,p,noise,fh,fw,rows,cols,mh,mw))
    return tuple(choices)


def _pick(ctx, name, options, preferred=(), *, component=False):
    options = sorted(set(options))
    # Exact controls override the curriculum, but not geometric feasibility.
    if name not in ctx.overrides:
        favored = [x for x in preferred if x in options]
        if favored:
            options = favored if component else options + favored*3
    return ctx.draw_choice(name,options)


def _composition(total, parts, rng):
    cuts = [0] + sorted(rng.randrange(total+1) for _ in range(parts-1)) + [total]
    return [b-a for a,b in zip(cuts,cuts[1:])]


def _origins(h,w,fh,fw,rows,cols,n,rng):
    row_gaps = _composition(h-rows*fh-(rows-1),rows+1,rng)
    col_gaps = _composition(w-cols*fw-(cols-1),cols+1,rng)
    rs,cs = [],[]
    pos = row_gaps[0]
    for i in range(rows):
        rs.append(pos)
        pos += fh+1+row_gaps[i+1]
    pos = col_gaps[0]
    for i in range(cols):
        cs.append(pos)
        pos += fw+1+col_gaps[i+1]
    return sorted(rng.sample([(r,c) for r in rs for c in cs],n))


def _path(a,b):
    (r0,c0),(r1,c1) = sorted((a,b))
    step = 1 if c1 >= c0 else -1
    return tuple((r0,c) for c in range(c0,c1+step,step)) + tuple((r,c1) for r in range(r0+1,r1+1))


@lru_cache(maxsize=64)
def _route_candidates(h,w):
    candidates = []
    for a,b in combinations(product(range(h),range(w)),2):
        path = _path(a,b)
        if len(path) >= 3:  # a real observable extension, not adjacent endpoints
            candidates.append((a,b,path))
    return tuple(candidates)


def _put_interior(grid,r0,c0,fh,fw,colors,ignored_color,noise,rng):
    ih,iw,p = fh-2,fw-2,len(colors)
    orientations = [axis for axis,extent in ((0,ih),(1,iw)) if extent >= 2*p]
    axis = rng.choice(orientations)
    sizes = [2+x for x in _composition((ih if axis == 0 else iw)-2*p,p,rng)]
    used,offset = set(),0
    for index,(color,size) in enumerate(zip(colors,sizes)):
        sh,sw = (size,iw) if axis == 0 else (ih,size)
        top,left = (offset,0) if axis == 0 else (0,offset)
        cap = ih*iw-len(used)-noise-3*(p-index-1)
        choices = [item for item in _route_candidates(sh,sw) if len(item[2]) <= cap]
        if not choices:
            raise RuntimeError("constructive strip unexpectedly has no lawful route")
        a,b,path = rng.choice(choices)
        for r,c in (a,b):
            grid[r0+1+top+r][c0+1+left+c] = color
        used.update((top+r,left+c) for r,c in path)
        offset += size
    free = [(r,c) for r in range(ih) for c in range(iw) if (r,c) not in used]
    for r,c in rng.sample(free,noise):
        grid[r0+1+r][c0+1+c] = ignored_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown or retired override axes: {sorted(unknown)}")
    if difficulty not in (None,"easy","medium","hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    for name,value in overrides.items():
        if type(value) is not int or value not in _DOMAINS[name]:
            raise ValueError(f"{name} must be an integer in {_DOMAINS[name]}")
    ctx = gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,
                  task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    # Rotating curriculum: every consecutive 3 unoverridden draws contains
    # each component, including at every cyclic start used by lesson assembly.
    role = (seed+sample_index) % 3
    core,contrast = role == 0,role == 2
    preferences = ({"n_frames":(2,),"pairs_per_frame":(1,),"n_ignored":(0,),
                    "frame_h":(5,),"frame_w":(5,),"grid_h":(12,),"grid_w":(14,)} if core else
                   {"n_frames":(2,),"pairs_per_frame":(2,),"n_ignored":(3,),
                    "frame_h":(7,),"frame_w":(7,),"grid_h":(18,),"grid_w":(18,)} if contrast else
                   {"n_frames":(1,) if difficulty == "easy" else (3,) if difficulty == "hard" else (2,),
                    "frame_h":(4,5,6) if difficulty == "easy" else (7,8,9),
                    "frame_w":(4,5,6) if difficulty == "easy" else (7,8,9)})
    max_h,max_w = overrides.get("grid_h",30),overrides.get("grid_w",30)
    configs = [g for g in _geometries()
               if g[7] <= max_h and g[8] <= max_w
               and not (overrides.get("shared_pairs") == 1 and g[0] == 1)
               and all(name not in overrides or g[i] == overrides[name]
                       for i,name in enumerate(_GEOMETRY_FIELDS))]
    if not configs:
        raise IncompatibleOverrides(overrides,"frames/strips/ignored markers cannot fit without dropping requested content")
    values = {}
    for index,name in enumerate(_GEOMETRY_FIELDS):
        values[name] = _pick(ctx,name,[g[index] for g in configs],preferences.get(name,()),component=core or contrast)
        configs = [g for g in configs if g[index] == values[name]]
    h_options = [h for h in _DOMAINS['grid_h'] if any(g[7] <= h and g[8] <= max_w for g in configs)]
    h = _pick(ctx,'grid_h',h_options,preferences.get('grid_h',()),component=core or contrast)
    w_options = [w for w in _DOMAINS['grid_w'] if any(g[7] <= h and g[8] <= w for g in configs)]
    w = _pick(ctx,'grid_w',w_options,preferences.get('grid_w',()),component=core or contrast)
    configs = [g for g in configs if g[7] <= h and g[8] <= w]
    packing = ctx.draw_rng('packing').choice(configs)
    n,p,noise,fh,fw,rows,cols,_,_ = packing
    frame_color = _pick(ctx,'frame_color',_DOMAINS['frame_color'],
                        (8,) if core else tuple(c for c in range(1,10) if c != 8) if contrast else (),
                        component=core or contrast)
    shared = _pick(ctx,'shared_pairs',(0,1) if n > 1 else (0,),
                   (0,) if core else (1,) if contrast else (),component=core or contrast)
    count = p if shared else n*p
    pool = ctx.draw_rng('palette').sample([c for c in range(1,10) if c != frame_color],count+bool(noise))
    ignored_color = pool[-1] if noise else None
    grid = full_grid(h,w,0)
    origins = _origins(h,w,fh,fw,rows,cols,n,ctx.draw_rng('positions'))
    for index,(r0,c0) in enumerate(origins):
        draw_frame(grid,r0,c0,r0+fh-1,c0+fw-1,frame_color)
        colors = pool[:p] if shared else pool[index*p:(index+1)*p]
        _put_interior(grid,r0,c0,fh,fw,colors,ignored_color,noise,ctx.draw_rng(f'interior:{index}'))
    return grid


def _frames(grid):
    """Recognize same-color 4-connected rectangular border objects."""
    h,w = len(grid),len(grid[0])
    seen,found = set(),[]
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r,c) in seen:
                continue
            stack,cells = [(r,c)],[]
            seen.add((r,c))
            while stack:
                rr,cc = stack.pop()
                cells.append((rr,cc))
                for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
                    if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr,nc)); stack.append((nr,nc))
            top,bottom = min(p[0] for p in cells),max(p[0] for p in cells)
            left,right = min(p[1] for p in cells),max(p[1] for p in cells)
            if (bottom-top >= 2 and right-left >= 2
                and len(cells) == 2*(bottom-top+right-left)
                and all(rr in (top,bottom) or cc in (left,right) for rr,cc in cells)):
                found.append((top,left,bottom,right,color))
    return sorted(found)


def _groups(grid,frame):
    top,left,bottom,right,fc = frame
    groups = defaultdict(list)
    for r in range(top+1,bottom):
        for c in range(left+1,right):
            color = grid[r][c]
            if color not in (0,fc):
                groups[color].append((r,c))
    return dict(groups)


def observe_overrides(grid):
    frames = _frames(grid)
    groups = [_groups(grid,f) for f in frames]
    def common(seq):
        values = set(seq)
        return next(iter(values)) if len(values) == 1 else tuple(sorted(values))
    pair_colors = [[c for c,pts in group.items() if len(pts) == 2] for group in groups]
    repeated = len([c for row in pair_colors for c in row]) > len({c for row in pair_colors for c in row})
    return {
        'grid_h':len(grid),'grid_w':len(grid[0]),'n_frames':len(frames),
        'frame_h':common(f[2]-f[0]+1 for f in frames),
        'frame_w':common(f[3]-f[1]+1 for f in frames),
        'frame_color':common(f[4] for f in frames),
        'pairs_per_frame':common(len(row) for row in pair_colors),
        'shared_pairs':int(repeated),
        'n_ignored':common(sum(len(pts) for pts in group.values() if len(pts) != 2) for group in groups),
    }


def self_check(grid, *, difficulty=None, meta=None):
    if (not isinstance(grid,(list,tuple)) or not grid
        or not isinstance(grid[0],(list,tuple)) or not grid[0]):
        return ['expected a nonempty rectangular grid']
    if any(not isinstance(row,(list,tuple)) or len(row) != len(grid[0]) for row in grid):
        return ['ragged grid']
    if len(grid) > 30 or len(grid[0]) > 30:
        return ['grid dimensions must not exceed 30']
    if any(type(c) is not int or not 0 <= c <= 9 for row in grid for c in row):
        return ['cells must be integer colors 0..9']
    frames = _frames(grid)
    if not 1 <= len(frames) <= 3:
        return ['expected one to three complete rectangular frames']
    covered,errors = set(),[]
    for frame in frames:
        top,left,bottom,right,fc = frame
        footprint = {(r,c) for r in range(top,bottom+1) for c in range(left,right+1)}
        if covered & footprint:
            errors.append('frame rectangles overlap or nest')
        covered.update(footprint)
        groups = _groups(grid,frame)
        pairs = [(color,pts) for color,pts in groups.items() if len(pts) == 2]
        others = [pts for pts in groups.values() if len(pts) != 2]
        if not 1 <= len(pairs) <= 2:
            errors.append('each frame must contain one or two local endpoint pairs')
        if len(others) > 1 or any(len(pts) not in (1,3) for pts in others):
            errors.append('only one optional singleton/triple color is in the sampled domain')
        reserved = set()
        for color,pts in pairs:
            route = set(_path(*pts))
            if route & reserved:
                errors.append('routed paths intersect')
            if any(grid[r][c] not in (0,color) for r,c in route):
                errors.append('routed path would overwrite another endpoint/marker')
            reserved.update(route)
    if any(color and (r,c) not in covered for r,row in enumerate(grid) for c,color in enumerate(row)):
        errors.append('nonbackground cells outside complete frames')
    return errors


def strict_canonical_like(grid):
    """Lawful local-routing domain; accepts all canonical inputs, not just sizes."""
    return self_check(grid)


def _rival_global_pairs(grid):
    """Incorrectly count endpoints over the entire canvas, ignoring containers."""
    groups = defaultdict(list)
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if color:
                groups[color].append((r,c))
    out = [list(row) for row in grid]
    for color,pts in groups.items():
        if len(pts) == 2:
            for r,c in _path(*pts):
                out[r][c] = color
    return out


def _rival_frame_policy(grid, *, eight_only=False, first_only=False):
    out = [list(row) for row in grid]
    for frame in _frames(grid):
        if eight_only and frame[4] != 8:
            continue
        pairs = [(c,p) for c,p in _groups(grid,frame).items() if len(p) == 2]
        for color,pts in (pairs[:1] if first_only else pairs):
            for r,c in _path(*pts):
                out[r][c] = color
    return out


def _rival_eight_only(grid):
    return _rival_frame_policy(grid,eight_only=True)


def _rival_first_pair(grid):
    return _rival_frame_policy(grid,first_only=True)


def _reused_pair(grid):
    seen = set()
    for frame in _frames(grid):
        for color,pts in _groups(grid,frame).items():
            if len(pts) == 2 and len(_path(*pts)) >= 3:
                if color in seen:
                    return True
                seen.add(color)
    return False


def _non8_frame(grid):
    return any(f[4] != 8 and any(len(p) == 2 and len(_path(*p)) >= 3 for p in _groups(grid,f).values())
               for f in _frames(grid))


def _multiple_pairs(grid):
    for f in _frames(grid):
        pairs = [p for p in _groups(grid,f).values() if len(p) == 2]
        if any(len(_path(*p)) >= 3 for p in pairs[1:]):
            return True
    return False


SEMANTIC_WITNESSES = {
    'reused_pair_color':_reused_pair, 'non8_frame':_non8_frame, 'multiple_pairs':_multiple_pairs,
}
SEMANTIC_RIVALS = {
    'global_color_pairs':_rival_global_pairs,
    'only_color8_frames':_rival_eight_only,
    'first_pair_per_frame':_rival_first_pair,
}
WITNESS_RIVALS = {
    'reused_pair_color':['global_color_pairs'],
    'non8_frame':['only_color8_frames'],
    'multiple_pairs':['first_pair_per_frame'],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
