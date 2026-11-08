"""Complete rectangle outlines from color-specific corner markers.

Input-only sampler. Racket remains the label authority. Default consecutive
three-example windows include canonical, multicolor, and two-corner boundary
profiles; exact overrides intentionally supersede that curriculum. Bboxes are
nondegenerate and area-disjoint, avoiding arbitrary overlap-paint precedence.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a452b4b4f04a"
TASK_ID = GENERATOR_ID
RULE_HASH = "f54dbee03c8b"
VERSION = "3.0.0"
SUMMARY = (
    "Zero-background 6..20 grids with 1..3 distinct colors from 1..9, each "
    "marked at 2 opposite, 3 arbitrary, or all 4 corners of an area-disjoint "
    "bbox at least 3x3. Complete each color's hollow rectangle outline. "
    "Canonical single-color three-corner inputs remain a default component."
)
INVARIANTS = [
    "integer ARC palette 0..9; zero background; 1..3 foreground colors",
    "each color has 2..4 bbox corners, spanning at least 3 rows and 3 columns",
    "different colors' entire bounding boxes are area-disjoint",
    "all requested colors and corner counts are realized without rejection sampling",
]
AXES = {
    "grid_h": {"type": "int", "default": "6..20; canonical profile mix", "valid": "6..20"},
    "grid_w": {"type": "int", "default": "6..20; canonical profile mix", "valid": "6..20"},
    "n_colors": {"type": "int", "default": "1..3; profile dependent", "valid": "1..3"},
    "corner_count": {"type": "int", "default": "2..4; profile dependent", "valid": "2..4"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = ("canonical", "multicolor", "two_corner_boundary")
_CANONICAL_SHAPES = ((8,8), (9,9), (7,10), (10,10), (8,11))


def schedule_profile(seed, sample_index, difficulty=None):
    """Any three consecutive unoverridden draws contain all three profiles."""
    offset = stable_rng(seed, f"{TASK_ID}:profile", VERSION).randrange(len(SCHEDULE_PROFILES))
    return SCHEDULE_PROFILES[(offset + sample_index) % len(SCHEDULE_PROFILES)]


def _weighted(ctx, name, lo, hi, favorites):
    # Keep the whole exact override domain in EVERY draw's provenance.
    return ctx.draw_choice(name, tuple(range(lo, hi+1)) + tuple(favorites))


def _capacity(rect):
    r0,c0,r1,c1 = rect
    return ((r1-r0+1)//3) * ((c1-c0+1)//3)


def _partition(rect, count, rng):
    """Constructive guillotine packing with a capacity-checked split.

    A 6x6 canvas always fits three 3x3 rectangles. Regions need not be equal,
    are shuffled before assigning colors, and do not constrain bbox orientation.
    """
    if count == 1:
        return [rect]
    r0,c0,r1,c1 = rect
    choices = []
    for cut in range(r0+3, r1-1):
        a,b = (r0,c0,cut-1,c1), (cut,c0,r1,c1)
        for left in range(1,count):
            if _capacity(a) >= left and _capacity(b) >= count-left:
                choices.append((a,b,left))
    for cut in range(c0+3, c1-1):
        a,b = (r0,c0,r1,cut-1), (r0,cut,r1,c1)
        for left in range(1,count):
            if _capacity(a) >= left and _capacity(b) >= count-left:
                choices.append((a,b,left))
    if not choices:
        raise ValueError("canvas cannot construct the requested disjoint rectangles")
    a,b,left = rng.choice(choices)
    return _partition(a,left,rng) + _partition(b,count-left,rng)


def _box(region, h, w, rng, force_boundary=False):
    r0,c0,r1,c1 = region
    bh,bw = rng.randint(3,r1-r0+1), rng.randint(3,c1-c0+1)
    top,left = rng.randint(r0,r1-bh+1), rng.randint(c0,c1-bw+1)
    if force_boundary:
        sides = [s for s,ok in (("top",r0==0),("left",c0==0),
                               ("bottom",r1==h-1),("right",c1==w-1)) if ok]
        if not sides:
            raise RuntimeError("boundary profile has no canvas-adjacent region")
        side = rng.choice(sides)
        if side == "top": top=0
        elif side == "left": left=0
        elif side == "bottom": top=h-bh
        else: left=w-bw
    return top,left,top+bh-1,left+bw-1


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for key,value in overrides.items():
        if value is not None and type(value) is not int:
            raise ValueError(f"{key} must be an integer, not {type(value).__name__}")
    profile = schedule_profile(seed,sample_index,difficulty)
    canonical = profile == "canonical"
    boundary = profile == "two_corner_boundary"
    # Scheduled defaults are explicit effective pins. The single GenCtx records
    # all final axis values with their entire declared domains; caller pins win.
    rng = stable_rng(seed, f"{TASK_ID}|{sample_index}|profile_counts", VERSION)
    defaults = {
        "n_colors": 1 if canonical else rng.choice((1,2,3) if boundary else (2,3)),
        "corner_count": 3 if canonical else (2 if boundary else rng.choice((2,3,4))),
    }
    effective = dict(overrides)
    for name,value in defaults.items():
        if effective.get(name) is None:
            effective[name] = value
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    shape = ctx.draw_rng("canonical_scale").choice(_CANONICAL_SHAPES)
    favored = {"easy":tuple(range(6,11)), "hard":tuple(range(12,21))}.get(difficulty,tuple(range(8,15)))
    # Sample dimensions, never stored inputs. Keep canonical scale in each band.
    h = _weighted(ctx,"grid_h",6,20, (shape[0],)*240 if canonical else favored*3)
    w = _weighted(ctx,"grid_w",6,20, (shape[1],)*240 if canonical else favored*3)
    n = ctx.draw_choice("n_colors",(1,2,3))
    k = ctx.draw_choice("corner_count",(2,3,4))
    palette = ctx.draw_rng("palette").sample(list(range(1,10)),n)
    region = (0,0,h-1,w-1)
    if canonical and _capacity((1,1,h-2,w-2)) >= n:
        region = (1,1,h-2,w-2)
    regions = _partition(region,n,ctx.draw_rng("partition"))
    ctx.draw_rng("color_regions").shuffle(regions)
    grid = full_grid(h,w,0)
    for i,(color,area) in enumerate(zip(palette,regions)):
        top,left,bottom,right = _box(area,h,w,ctx.draw_rng(f"box_{i}"),boundary and i==0)
        corners = [(top,left),(top,right),(bottom,left),(bottom,right)]
        rng = ctx.draw_rng(f"markers_{i}")
        selected = (rng.choice((corners[::3],corners[1:3])) if k==2 else rng.sample(corners,k))
        for r,c in selected:
            grid[r][c] = color
    return grid


def _points(grid):
    result = {}
    for r,row in enumerate(grid):
        for c,color in enumerate(row):
            if color != 0:
                result.setdefault(color,[]).append((r,c))
    return result


def _bounds(cells):
    rows,cols = zip(*cells)
    return min(rows),min(cols),max(rows),max(cols)


def observe_overrides(grid):
    by_color = _points(grid)
    counts = {len(cells) for cells in by_color.values()}
    return {"grid_h":len(grid), "grid_w":len(grid[0]), "n_colors":len(by_color),
            "corner_count":next(iter(counts)) if len(counts)==1 else None}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid,(list,tuple)) or not grid or not isinstance(grid[0],(list,tuple)) or not grid[0]:
        return ["expected nonempty rectangular grid"]
    if any(not isinstance(row,(list,tuple)) or len(row)!=len(grid[0]) for row in grid):
        return ["ragged grid"]
    if len(grid)>30 or len(grid[0])>30 or any(type(v) is not int or not 0<=v<=9 for row in grid for v in row):
        return ["expected at most 30x30 integer ARC palette 0..9"]
    errors=[]; boxes=[]
    by_color = _points(grid)
    if not 1<=len(by_color)<=3:
        errors.append(f"expected 1..3 colors, found {len(by_color)}")
    for color,cells in by_color.items():
        r0,c0,r1,c1 = _bounds(cells)
        corners={(r0,c0),(r0,c1),(r1,c0),(r1,c1)}
        if not 2<=len(cells)<=4 or not set(cells)<=corners:
            errors.append(f"color {color}: expected 2..4 bbox-corner markers")
        if r1-r0<2 or c1-c0<2:
            errors.append(f"color {color}: bbox must span at least 3 rows and 3 columns")
        boxes.append((r0,c0,r1,c1,color))
    for i,a in enumerate(boxes):
        for b in boxes[i+1:]:
            if not (a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1]):
                errors.append(f"bboxes for colors {a[4]} and {b[4]} overlap")
    return errors


def strict_canonical_like(grid):
    errors=self_check(grid)
    if errors:
        return errors
    pts=_points(grid)
    return [] if len(pts)==1 and len(next(iter(pts.values())))==3 else ["strict profile requires one color and three corners"]


def _rival(grid, mode):
    """Deliberately incomplete competitors; NEVER training label generators."""
    pts=_points(grid)
    if mode=="global_bbox" and pts:
        pts={min(pts):[p for cells in pts.values() for p in cells]}
    out=full_grid(len(grid),len(grid[0]),0)
    for color,cells in pts.items():
        r0,c0,r1,c1=_bounds(cells)
        if mode=="three_markers_only" and len(cells)!=3:
            for r,c in cells:out[r][c]=color
            continue
        if mode=="interior_boxes_only" and (r0==0 or c0==0 or r1==len(grid)-1 or c1==len(grid[0])-1):
            for r,c in cells:out[r][c]=color
            continue
        for r in range(r0,r1+1):
            for c in range(c0,c1+1):
                if r in (r0,r1) or c in (c0,c1):out[r][c]=color
    return out


def _global_bbox(grid):return _rival(grid,"global_bbox")
def _three_markers_only(grid):return _rival(grid,"three_markers_only")
def _interior_boxes_only(grid):return _rival(grid,"interior_boxes_only")
def _multiple_colors(grid):return len(_points(grid))>1
def _nonthree_markers(grid):return any(len(cells)!=3 for cells in _points(grid).values())
def _touches_boundary(grid):
    return any(r in (0,len(grid)-1) or c in (0,len(grid[0])-1) for cells in _points(grid).values() for r,c in cells)

SEMANTIC_WITNESSES={"multiple_colors":_multiple_colors,"nonthree_markers":_nonthree_markers,"boundary":_touches_boundary}
SEMANTIC_RIVALS={"global_bbox":_global_bbox,"three_markers_only":_three_markers_only,"interior_boxes_only":_interior_boxes_only}
WITNESS_RIVALS={"multiple_colors":["global_bbox"],"nonthree_markers":["three_markers_only"],"boundary":["interior_boxes_only"]}
CANONICAL_SHORTCUTS=dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS=dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Finite-rival certificate only; never claim universal rule identification.

    Checks use supplied demonstration labels. Query labels are neither needed
    nor consulted, so an answer-hidden challenge gets the same certificate.
    """
    if not isinstance(demos,(list,tuple)) or len(demos)<EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    errors=[]
    for i,pair in enumerate(demos):
        if not isinstance(pair,dict) or "input" not in pair or "output" not in pair:
            errors.append(f"demo {i} must contain input and output")
        else:
            errors.extend(f"demo {i}: {e}" for e in self_check(pair["input"]))
    if not isinstance(query,dict) or "input" not in query:
        errors.append("query must contain an input")
    else:
        errors.extend(f"query: {e}" for e in self_check(query["input"]))
    if errors:
        return errors
    for name,rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"])==pair["output"] for pair in demos):
            errors.append(f"demonstrations do not refute {name}")
    return errors
