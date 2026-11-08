"""Semantic generator for ARC task bdb419bbf286.

Select the first color-2 object and the first row-major color-3 and color-4
cells.  Their displacement is a translation vector.  Return an empty grid
with the selected shape painted color 8 at offsets zero, one, and two times
that vector.
"""
from __future__ import annotations

from bisect import bisect_left

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "bdb419bbf286"
TASK_ID = GENERATOR_ID
VERSION = "4.1.0"
RULE_HASH = "6669efb7af1c"
SUMMARY = "Paint three color-8 copies of the first color-2 object along the vector from the first color-3 cell to the first color-4 cell."
INVARIANTS = [
    "literal color 0 is the background",
    "the first color-2 component is a connected source shape",
    "the first row-major color-3 and color-4 cells define a nonzero vector",
    "every generalized scene contains later marker decoys whose last-marker vector predicts a different output",
    "translated cells outside the canvas are clipped by paint-cells",
    "the output clears every input marker and decoy and paints only the union of the three copies color 8",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "down_right",
    "up_right",
    "up_left",
    "down_left",
    "axis_aligned",
    "overlapping_copies",
    "clipped_copies",
    "marker_decoys",
    "irrelevant_colors",
    "large_shape",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "ten discriminating ordinary profiles; five exact-public profiles by explicit override", "valid": "|".join(SCENE_PROFILES)}}

_PUBLIC_ROWS = {
    "public_1": "300000000000/020000000000/022400000000/000000000000/000000000000/000000000000/000000000000/000000000000/000000000006",
    "public_2": "0000000000077/0000000000000/0000220000000/0000022000000/0000000000000/0000000000000/0000000000000/0040000000000/0000000000000/3000000000000",
    "public_3": "500000200000/000000200000/000000222000/000000000000/000000000000/000000000400/000000000000/000000000003",
    "public_4": "000000000030/000000000000/000000004000/002000000000/022200000000/002000000000/000000000000/400000000000/400000000000/400000000000",
    "public_5": "6000000000000/0020000000000/0020200000000/0022200000000/0000000000000/0000000000000/0000000000000/0000000004000/0000000000000/0000000000003",
}


def _decode(rows): return [[int(value) for value in row] for row in rows.split("/")]
_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid: return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]: return ["rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid): return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30: return ["grid dimensions must not exceed 30"]
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 or v == 8 for row in grid for v in row): return ["input cells must be ARC colors excluding reserved output color 8"]
    return []


def _components(grid, color):
    h, w = len(grid), len(grid[0]); unseen = {(r,c) for r in range(h) for c in range(w) if grid[r][c] == color}; result=[]
    while unseen:
        stack=[min(unseen)]; cells=set()
        while stack:
            r,c=stack.pop()
            if (r,c) not in unseen: continue
            unseen.remove((r,c)); cells.add((r,c)); stack.extend((rr,cc) for rr,cc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if (rr,cc) in unseen)
        result.append(cells)
    return result


def _translated(shape, dr, dc):
    return [{(r+k*dr,c+k*dc) for r,c in shape} for k in range(3)]


def _paint_output(h, w, copies):
    output=[[0 for _ in range(w)] for _ in range(h)]
    for cells in copies:
        for r,c in cells:
            if 0 <= r < h and 0 <= c < w: output[r][c]=8
    return output


def rule_mirror(grid):
    errors=_valid(grid)
    if errors: raise ValueError("; ".join(errors))
    shapes=_components(grid,2); threes=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3]; fours=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==4]
    if not shapes or not threes or not fours: raise ValueError("expected a color-2 object and color-3/color-4 markers")
    dr,dc=fours[0][0]-threes[0][0],fours[0][1]-threes[0][1]
    return _paint_output(len(grid),len(grid[0]),_translated(shapes[0],dr,dc))


def _general_profile(shape, dr, dc, copies, threes, fours, grid):
    h,w=len(grid),len(grid[0])
    # Every generalized scene now carries one later 3 and one later 4 so the
    # row-major "first marker" lesson is always observable.  The dedicated
    # marker-decoy profile has an additional color-4 decoy.
    if len(threes) != 2 or len(fours) != 2: return "marker_decoys"
    if any(v not in (0,2,3,4) for row in grid for v in row): return "irrelevant_colors"
    if any(not (0<=r<h and 0<=c<w) for cells in copies for r,c in cells): return "clipped_copies"
    if len(set().union(*copies)) < 3*len(shape): return "overlapping_copies"
    if len(shape)>=7: return "large_shape"
    if dr==0 or dc==0: return "axis_aligned"
    return ("down_" if dr>0 else "up_")+("right" if dc>0 else "left")


def _analysis(grid):
    errors=_valid(grid); result={"errors":errors,"scene_profile":None}
    if errors: return result
    shapes=_components(grid,2); threes=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==3]; fours=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==4]
    if len(shapes)!=1: errors.append(f"expected exactly one color-2 component; got {len(shapes)}")
    if not 1<=len(threes)<=4 or not 1<=len(fours)<=4: errors.append("expected 1..4 cells of each marker color")
    if errors: return result
    shape=shapes[0]; a,b=threes[0],fours[0]; dr,dc=b[0]-a[0],b[1]-a[1]
    if (dr,dc)==(0,0): errors.append("translation vector must be nonzero")
    copies=_translated(shape,dr,dc); h,w=len(grid),len(grid[0])
    profile=_PUBLIC_SIGNATURES.get(tuple(map(tuple,grid))) or _general_profile(shape,dr,dc,copies,threes,fours,grid)
    if profile not in SCENE_PROFILES: errors.append("translation geometry does not match a declared profile")
    output=_paint_output(h,w,copies)
    result.update({"shape":shape,"shape_size":len(shape),"marker_3":threes,"marker_4":fours,"first_3":a,"first_4":b,"dr":dr,"dc":dc,"copies":copies,"copy_union":set().union(*copies),"copies_overlap":len(set().union(*copies))<3*len(shape),"output":output,"scene_profile":profile,"errors":errors})
    return result


def self_check(grid, *, difficulty=None, meta=None): return list(_analysis(grid)["errors"])
def canonical_profile_signature(grid): return _PUBLIC_SIGNATURES.get(tuple(map(tuple,grid)))
def observe_overrides(grid):
    analysis=_analysis(grid)
    if analysis["errors"]: raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile":analysis["scene_profile"]}


def _poly(rng, size):
    cells={(0,0)}
    while len(cells)<size:
        frontier={(r+dr,c+dc) for r,c in cells for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)) if (r+dr,c+dc) not in cells}
        cells.add(rng.choice(sorted(frontier)))
    r0=min(r for r,_ in cells); c0=min(c for _,c in cells)
    return {(r-r0,c-c0) for r,c in cells}


def _place_shape(rng,h,w,shape,dr,dc):
    sh=max(r for r,_ in shape)+1; sw=max(c for _,c in shape)+1
    rlo=max(0,-2*dr); rhi=h-sh-max(0,2*dr); clo=max(0,-2*dc); chi=w-sw-max(0,2*dc)
    if rlo>rhi or clo>chi: return None
    top,left=rng.randint(rlo,rhi),rng.randint(clo,chi)
    return {(top+r,left+c) for r,c in shape}


def _marker_pair(rng,h,w,dr,dc,occupied,reserve_after=0):
    pairs=[]; occupied_indices={r*w+c for r,c in occupied}; total=h*w
    for r in range(h):
        for c in range(w):
            other=(r+dr,c+dc)
            if not (0<=other[0]<h and 0<=other[1]<w): continue
            if (r,c) in occupied or other in occupied: continue
            cutoff=max(r*w+c,other[0]*w+other[1])
            free_after=total-1-cutoff-sum(index>cutoff for index in occupied_indices)
            if free_after>=reserve_after: pairs.append(((r,c),other))
    if not pairs: raise AssertionError("cannot place first marker pair with requested later-decoy reserve")
    return rng.choice(pairs)


def _add_later_marker_decoys(rng,grid,shape,a,b,dr,dc,extra_fours):
    h,w=len(grid),len(grid[0]); cutoff=max(a[0]*w+a[1],b[0]*w+b[1])
    free=[(r,c) for r in range(h) for c in range(w) if r*w+c>cutoff and grid[r][c]==0]
    free_indices=[r*w+c for r,c in free]
    canonical={
        (r+k*dr,c+k*dc)
        for r,c in shape for k in range(3)
        if 0<=r+k*dr<h and 0<=c+k*dc<w
    }
    # Try a bounded row-major tail.  Comparing clipped cell sets avoids
    # allocating hundreds of temporary grids per generated scene.
    pairs=[(later_three,last_four) for later_three in free[-24:] for last_four in free[-24:] if later_three!=last_four]
    rng.shuffle(pairs)
    selected=None
    for later_three,last_four in pairs:
        last_index=last_four[0]*w+last_four[1]
        prior_count=bisect_left(free_indices,last_index)-(1 if later_three[0]*w+later_three[1]<last_index else 0)
        if prior_count<extra_fours-1: continue
        rival_dr=last_four[0]-later_three[0]; rival_dc=last_four[1]-later_three[1]
        if (rival_dr,rival_dc)==(dr,dc): continue
        rival={
            (r+k*rival_dr,c+k*rival_dc)
            for r,c in shape for k in range(3)
            if 0<=r+k*rival_dr<h and 0<=c+k*rival_dc<w
        }
        if rival!=canonical:
            selected=(later_three,last_four)
            break
    if selected is None: raise AssertionError("cannot construct a discriminating later-marker lesson")
    later_three,last_four=selected
    prior_fours=[p for p in free if p not in {later_three,last_four} and p[0]*w+p[1] < last_four[0]*w+last_four[1]]
    grid[later_three[0]][later_three[1]]=3
    if extra_fours>1:
        for r,c in rng.sample(prior_fours,extra_fours-1): grid[r][c]=4
    grid[last_four[0]][last_four[1]]=4


def _general_scene(ctx,profile):
    ranges={None:(9,20),"easy":(8,12),"medium":(11,18),"hard":(17,26)}; lo,hi=ranges[ctx.difficulty]
    h=ctx.draw_int("canvas_height",lo,hi); w=ctx.draw_int("canvas_width",lo+1,min(30,hi+3)); rng=ctx.draw_rng("geometry")
    if profile=="overlapping_copies":
        shape={(r,0) for r in range(rng.randint(4,min(7,h-2)))}; dr,dc=(1,0); placed=_place_shape(rng,h,w,shape,dr,dc)
    elif profile=="clipped_copies":
        shape={(0,0),(1,0),(1,1)}; dr,dc=(2,2); placed={(h-4+r,w-4+c) for r,c in shape}
    else:
        placed=None
        for _ in range(120):
            size=rng.randint(7,10) if profile=="large_shape" else rng.randint(3,6); shape=_poly(rng,size)
            if profile=="axis_aligned": dr,dc=rng.choice(((0,2),(0,-2),(2,0),(-2,0)))
            else:
                signs={"down_right":(1,1),"up_right":(-1,1),"up_left":(-1,-1),"down_left":(1,-1)}.get(profile,rng.choice(((1,1),(-1,1),(-1,-1),(1,-1))))
                dr,dc=signs[0]*rng.randint(1,3),signs[1]*rng.randint(1,3)
            if len(set().union(*_translated(shape,dr,dc))) != 3*len(shape): continue
            placed=_place_shape(rng,h,w,shape,dr,dc)
            if placed is not None: break
    if placed is None: raise AssertionError("canvas cannot fit requested translation")
    extra_fours=2 if profile=="marker_decoys" else 1
    a,b=_marker_pair(rng,h,w,dr,dc,placed,extra_fours+1); grid=[[0 for _ in range(w)] for _ in range(h)]
    for r,c in placed: grid[r][c]=2
    grid[a[0]][a[1]]=3; grid[b[0]][b[1]]=4
    _add_later_marker_decoys(rng,grid,placed,a,b,dr,dc,extra_fours)
    if profile=="irrelevant_colors":
        free=[(r,c) for r in range(h) for c in range(w) if grid[r][c]==0]; rng.shuffle(free)
        for color in rng.sample([1,5,6,7,9],rng.randint(2,5)):
            r,c=free.pop(); grid[r][c]=color
    return grid


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if difficulty not in (None,"easy","medium","hard"): raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown=sorted(set(overrides)-{"scene_profile"})
    if unknown: raise ValueError("unknown override(s): "+", ".join(unknown))
    # Preserve the keyed choice indices while replacing automatic public slots
    # with discriminating profiles. Record the actual emitted profile in ctx.
    public_slots = GENERAL_PROFILES[:len(PUBLIC_PROFILES)] if overrides.get("scene_profile") is None else PUBLIC_PROFILES
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    profile=ctx.draw_choice("scene_profile",public_slots+GENERAL_PROFILES+GENERAL_PROFILES)
    if profile in PUBLIC_PROFILES: return [row[:] for row in _PUBLIC_INPUTS[profile]]
    grid=_general_scene(ctx,profile); analysis=_analysis(grid)
    if analysis["errors"]: raise AssertionError(f"internal invalid scene: {analysis['errors']}")
    if analysis["scene_profile"]!=profile: raise AssertionError(f"profile drift: {profile} -> {analysis['scene_profile']}")
    return grid
