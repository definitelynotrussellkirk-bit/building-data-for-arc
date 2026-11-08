"""Vertical Mirror Add: collision-free seeds, exact controls and teaching support.

Racket owns labels. The canonical rule mirrors every ORIGINAL nonzero cell,
retaining originals when mirror destinations are empty or the same color.
Different-color reflected collisions have swap semantics and are outside this
completion grammar. See notes.md for the finite curriculum and explicit edges.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f8b3586f1d58"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "26d859cbdb3e"
SUMMARY = "Complete every colored seed across the vertical center line, preserving its color and original cell; left, right, mixed and centerline seeds are supported without conflicting mirrored colors."
INVARIANTS = [
    "rectangular integer-color grid with background zero",
    "reflected occupied endpoints never have different colors",
    "ordinary samples use distinct mirror orbits; explicit identity endpoints are opt-in",
    "exact requested dimensions, occupied-cell count, color count and side profile are realized",
]
PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
HELPFUL_TEXTURES = ("sparse", "dense", "varied_palette")
EDGE_TEXTURES = ("no_cells", "all_on_centerline", "full_right_half")
DEGENERATE_TEXTURES = ()  # The legacy named endpoints are lawful, not negative fixtures.
AXES = {
    "grid_h": {"type":"int", "default":"canonical or 6..9 easy / 9..14 medium / 13..20 hard", "valid":"4..22"},
    "grid_w": {"type":"int", "default":"canonical or banded width; center profiles round upward to odd", "valid":"5..26"},
    "n_cells": {"type":"int", "default":"3 canonical / 5..8 easy / 6..12 medium / 9..20 hard", "valid":"1..20"},
    "n_distinct_colors": {"type":"int", "default":"3 canonical; repeated colors in rich profiles", "valid":"1..9"},
    "position_bias": {"type":"str", "default":"scheduled left, right or mixed", "valid":"left_half|right_half|mixed"},
    "texture": {"type":"str", "default":"alias for palette_kind; edges opt-in", "valid":"|".join(PALETTE_KINDS+EDGE_TEXTURES), "probe":"diagnostic"},
}
# Compatibility spellings remain validated, but are not independent sampling axes.
COMPATIBILITY_ALIASES = {"palette_size":"n_distinct_colors", "palette_kind":"texture"}
COMPATIBILITY_MARKERS = {"density":"mixed"}
# Value-dependent conflicts carry exact overridden axes on OverrideConflict.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    ("n_cells","n_distinct_colors"), ("n_cells","palette_size"),
    ("palette_size","n_distinct_colors"), ("palette_kind","texture"),
    ("texture","position_bias"), ("texture","grid_w"),
    ("texture","n_cells"), ("texture","palette_size"),
    ("texture","n_distinct_colors"), ("n_cells","position_bias"),
    ("grid_h","grid_w","n_cells"),
]
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
SCHEDULE_PROFILES = ("canonical", "broad_side", "mixed_center_a", "mixed_center_b")
MIN_STRICT_FRAC = 0.20
_CANONICAL_SHAPES = ((6,8),(7,9),(8,10),(8,12),(9,11))
_INT_RANGES = {"grid_h":(4,22), "grid_w":(5,26), "n_cells":(1,20),
               "n_distinct_colors":(1,9), "palette_size":(1,9)}


class OverrideConflict(ValueError):
    def __init__(self, message, overrides):
        super().__init__("incompatible overrides: " + message)
        self.incompatible_axes = tuple(sorted(overrides))


def _normalize(overrides):
    unknown = set(overrides)-set(AXES)-set(COMPATIBILITY_ALIASES)-set(COMPATIBILITY_MARKERS)
    if unknown:
        raise ValueError("unknown override keys: " + ", ".join(sorted(unknown)))
    clean = {k:v for k,v in overrides.items() if v is not None}
    for name,(lo,hi) in _INT_RANGES.items():
        if name in clean and (type(clean[name]) is not int or not lo <= clean[name] <= hi):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
    for name,choices in (("position_bias",("left_half","right_half","mixed")),
                         ("texture",PALETTE_KINDS+EDGE_TEXTURES),
                         ("palette_kind",PALETTE_KINDS), ("density",("mixed",))):
        if name in clean and (not isinstance(clean[name],str) or clean[name] not in choices):
            raise ValueError(f"{name} must be one of {choices}")
    if "palette_size" in clean and "n_distinct_colors" in clean and clean["palette_size"] != clean["n_distinct_colors"]:
        raise OverrideConflict("palette_size and n_distinct_colors must agree",clean)
    if "texture" in clean and "palette_kind" in clean and clean["texture"] != clean["palette_kind"]:
        raise OverrideConflict("texture and palette_kind must agree",clean)
    # Normalize aliases before deriving RNG streams so synonymous calls are identical.
    if "palette_size" in clean:
        clean["n_distinct_colors"] = clean["palette_size"]
    if "palette_kind" in clean:
        clean["texture"] = clean["palette_kind"]
    return clean


def schedule_profile(seed, sample_index, difficulty=None):
    return SCHEDULE_PROFILES[sample_index % LESSON_SCHEDULE_PERIOD]


def _cells(grid):
    return [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v != 0]


def _unmatched(grid):
    w=len(grid[0])
    return [(r,c,v) for r,c,v in _cells(grid) if grid[r][w-1-c] == 0]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None,"easy","medium","hard"):
        raise ValueError("difficulty must be easy, medium, hard or None")
    clean=_normalize(overrides)
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,
                difficulty=difficulty,overrides=clean)
    profile=sample_index % LESSON_SCHEDULE_PERIOD
    mode=clean.get("texture","default")
    rng=ctx.draw_rng("layout:"+mode)
    ranges={"easy":((6,9),(7,10),(5,8)), "medium":((9,14),(11,16),(6,12)),
            "hard":((13,20),(15,24),(9,20))}[difficulty or "medium"]
    canonical=profile==0 and mode not in EDGE_TEXTURES
    if canonical:
        h,w=rng.choice(_CANONICAL_SHAPES); n=3
    else:
        h=rng.randint(*ranges[0]); w=rng.randint(*ranges[1])
        lo,hi=ranges[2]
        if mode=="sparse": hi=min(hi,lo+1)
        if mode=="dense": lo=max(lo,hi-2)
        n=rng.randint(lo,hi)
    h=clean.get("grid_h",h); w=clean.get("grid_w",w)
    if (profile in (2,3) or mode=="all_on_centerline") and "grid_w" not in clean and w%2==0:
        w=w+1 if w<26 else w-1
    if mode=="all_on_centerline" and w%2==0:
        raise OverrideConflict("all_on_centerline needs odd grid_w",clean)
    if mode=="no_cells":
        if any(k in clean for k in ("n_cells","n_distinct_colors","palette_size","position_bias")):
            raise OverrideConflict("no_cells cannot realize a positive count or side profile",clean)
        # Exact dimensions are still recorded and honored on this endpoint.
        h=ctx.draw_int("grid_h",h,h); w=ctx.draw_int("grid_w",w,w)
        ctx.draw_choice("texture",[mode]); ctx.draw_choice("density",["mixed"])
        return full_grid(h,w,0)
    if mode=="all_on_centerline" and "position_bias" in clean:
        raise OverrideConflict("a center-only input has no left/right side profile",clean)
    default_side="left_half" if canonical else (rng.choice(("left_half","right_half")) if profile==1 else "mixed")
    side=clean.get("position_bias",default_side)
    if mode=="full_right_half":
        if "position_bias" in clean and side!="right_half":
            raise OverrideConflict("full_right_half requires right_half position_bias",clean)
        side="right_half"
    n=clean.get("n_cells",n)
    requested_k=clean.get("n_distinct_colors")
    if requested_k is not None:
        if "n_cells" in clean and requested_k>n:
            raise OverrideConflict("color count exceeds n_cells",clean)
        if "n_cells" not in clean:
            n=max(n,requested_k+(0 if canonical or mode=="all_on_centerline" else 1))
    if side=="mixed" and n<2:
        if "position_bias" in clean:
            if "n_cells" in clean:
                raise OverrideConflict("mixed position_bias needs at least two seeds",clean)
            n=2
        else:
            side=rng.choice(("left_half","right_half"))
    if mode=="all_on_centerline":
        if "n_cells" not in clean:
            n=min(n,h) if requested_k is None else max(requested_k,min(n,h))
        if n>h and "grid_h" not in clean:
            h=max(h,n)
        if n>h:
            raise OverrideConflict("centerline capacity is grid_h",clean)
    else:
        capacity=h*(w//2)
        center_slot=int(profile in (2,3) and w%2==1 and n>=5 and mode not in EDGE_TEXTURES)
        needed=n-center_slot
        if needed>capacity:
            if "n_cells" not in clean and (requested_k is None or requested_k<=capacity+center_slot):
                n=capacity+center_slot
            elif "grid_h" not in clean and (needed+w//2-1)//(w//2)<=22:
                h=max(h,(needed+w//2-1)//(w//2))
            elif "grid_w" not in clean and 2*((needed+h-1)//h)+center_slot<=26:
                w=max(w,2*((needed+h-1)//h)+center_slot)
            else:
                raise OverrideConflict("n_cells exceeds available distinct mirror orbits",clean)
    n=min(n,20) if "n_cells" not in clean else n
    center=(profile in (2,3) and w%2==1 and n>=5 and mode not in EDGE_TEXTURES)
    off_count=n-int(center)
    rich=(not canonical and mode not in EDGE_TEXTURES and off_count>=4 and
          (requested_k is None or requested_k<n))
    max_k=n-1 if rich else n
    if requested_k is not None:
        k=requested_k
    elif canonical:
        k=min(3,n)
    elif mode=="varied_palette":
        k=min(9,max_k)
    else:
        k=rng.randint(1,min(6,max_k))
    if k>n:
        raise OverrideConflict("color count exceeds available occupied cells",clean)
    # Every advertised exact axis is recorded after feasible defaults adapt.
    h=ctx.draw_int("grid_h",h,h); w=ctx.draw_int("grid_w",w,w)
    n=ctx.draw_int("n_cells",n,n)
    k=ctx.draw_int("n_distinct_colors",k,k)
    ctx.draw_int("palette_size",k,k)
    ctx.draw_choice("position_bias",[side])
    ctx.draw_choice("texture",[mode]); ctx.draw_choice("density",["mixed"])
    if mode in PALETTE_KINDS:
        ctx.draw_choice("palette_kind",[mode])
    colors=list(ctx.draw_distinct_colors("pigments",n=k,exclude={0}))
    g=full_grid(h,w,0)
    if mode=="all_on_centerline":
        positions=[(r,w//2) for r in rng.sample(range(h),n)]
    elif canonical and n==3 and k==3 and side=="left_half" and h>=5:
        parity=rng.randrange(2) if h>=6 else 0
        rows=rng.sample(list(range(parity,h,2)),3)
        positions=[(r,rng.randrange(w//2)) for r in rows]
    else:
        orbits=[(r,c) for r in range(h) for c in range(w//2)]
        reserved=[]
        if rich:
            row=rng.randrange(h); col=rng.randrange(w//2-1)
            reserved=[(row,col),(row,col+1)]
        remaining=[p for p in orbits if p not in reserved]
        rng.shuffle(remaining)
        selected=reserved+remaining[:off_count-len(reserved)]
        if side=="mixed":
            sides=[rng.randrange(2) for _ in selected]
            if rich:
                sides[0]=sides[1]=rng.randrange(2)
                sides[2]=1-sides[0]
            elif len(sides)>=2:
                sides[0],sides[1]=0,1
        else:
            sides=[int(side=="right_half")]*len(selected)
        positions=[(r,w-1-c if s else c) for (r,c),s in zip(selected,sides)]
        if center:
            positions.append((rng.randrange(h),w//2))
    # Repeat an off-axis pigment, independently of which same-row pair was reserved.
    if rich:
        a,b=rng.sample(range(off_count),2)
        values=[None]*n
        values[a]=values[b]=colors[0]
        rest=[i for i in range(n) if i not in (a,b)]
        rng.shuffle(rest)
        for i,color in zip(rest,colors[1:]): values[i]=color
        for i in rest:
            if values[i] is None: values[i]=rng.choice(colors)
    else:
        values=colors+[rng.choice(colors) for _ in range(n-k)]
        rng.shuffle(values)
    for (r,c),value in zip(positions,values):
        g[r][c]=value
    return g


def observe_overrides(grid):
    cells=_cells(grid); w=len(grid[0])
    left=any(2*c<w-1 for r,c,v in cells)
    right=any(2*c>w-1 for r,c,v in cells)
    side="mixed" if left and right else "left_half" if left else "right_half" if right else "centerline" if cells else "empty"
    k=len({v for r,c,v in cells})
    return {"grid_h":len(grid),"grid_w":w,"n_cells":len(cells),
            "n_distinct_colors":k,"palette_size":k,"position_bias":side}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid,(list,tuple)) or not grid or not isinstance(grid[0],(list,tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    w=len(grid[0])
    if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in grid):
        return ["ragged grid"]
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row):
        return ["cells must be integer colors 0..9"]
    if any(v and grid[r][w-1-c] not in (0,v) for r,c,v in _cells(grid)):
        return ["different-color reflected endpoints conflict with completion grammar"]
    return []


def strict_canonical_like(grid):
    reasons=self_check(grid)
    if reasons: return reasons
    cells=_cells(grid); h,w=len(grid),len(grid[0])
    if (h,w) not in _CANONICAL_SHAPES or len(cells)!=3 or len({v for r,c,v in cells})!=3:
        return ["expected canonical shape and three distinct colored seeds"]
    if any(2*c>=w-1 for r,c,v in cells) or len({r for r,c,v in cells})!=3:
        return ["canonical seeds occupy distinct rows strictly left of center"]
    return []


def _copy_selected(grid,cells):
    out=[list(row) for row in grid]; w=len(grid[0])
    for r,c,v in cells: out[r][w-1-c]=v
    return out


def _first_color(grid):
    seen=set(); selected=[]
    for r,c,v in _cells(grid):
        if v not in seen: selected.append((r,c,v)); seen.add(v)
    return _copy_selected(grid,selected)


def _first_row(grid):
    seen=set(); selected=[]
    for r,c,v in _cells(grid):
        if r not in seen: selected.append((r,c,v)); seen.add(r)
    return _copy_selected(grid,selected)


def _first_three(grid):
    return _copy_selected(grid,_cells(grid)[:3])


def _isolated(grid):
    h,w=len(grid),len(grid[0])
    cells=[(r,c,v) for r,c,v in _cells(grid) if not any(
        0<=r+dr<h and 0<=c+dc<w and grid[r+dr][c+dc]
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)))]
    return _copy_selected(grid,cells)


def _left_only(grid):
    return _copy_selected(grid,[(r,c,v) for r,c,v in _cells(grid) if 2*c<len(grid[0])-1])


def _right_only(grid):
    return _copy_selected(grid,[(r,c,v) for r,c,v in _cells(grid) if 2*c>len(grid[0])-1])


def _reflect_only(grid):
    return [list(reversed(row)) for row in grid]


def _drop_center(grid):
    out=_copy_selected(grid,_cells(grid))
    if len(grid[0])%2:
        for row in out: row[len(row)//2]=0
    return out


def _has_repeat(grid):
    cells=_unmatched(grid)
    return len({v for r,c,v in cells})<len(cells)


def _has_row_repeat(grid):
    counts=Counter(r for r,c,v in _unmatched(grid))
    return any(n>1 for n in counts.values())


def _has_adjacent(grid):
    h,w=len(grid),len(grid[0])
    return any(any(0<=r+dr<h and 0<=c+dc<w and grid[r+dr][c+dc]!=0
                   for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)))
               for r,c,v in _unmatched(grid))


SEMANTIC_RIVALS={"first_color":_first_color,"first_row":_first_row,
    "first_three":_first_three,"isolated":_isolated,"left_only":_left_only,
    "right_only":_right_only,"reflect_only":_reflect_only,"drop_center":_drop_center}
SEMANTIC_WITNESSES={
    "repeated_color":_has_repeat, "same_row":_has_row_repeat,
    "adjacent_seeds":_has_adjacent,
    "right_source":lambda g:any(2*c>len(g[0])-1 for r,c,v in _unmatched(g)),
    "center_seed":lambda g:len(g[0])%2==1 and any(row[len(row)//2]!=0 for row in g),
    "four_unmatched":lambda g:len(_unmatched(g))>=4,
}
WITNESS_RIVALS={"repeated_color":["first_color"],"same_row":["first_row"],
    "adjacent_seeds":["isolated"],"right_source":["left_only"],
    "center_seed":["drop_center"],"four_unmatched":["first_three"]}
CANONICAL_SHORTCUTS={name:SEMANTIC_RIVALS[name] for name in
    ("first_color","first_row","first_three","isolated","left_only","drop_center")}
LESSON_COMPETITORS=SEMANTIC_RIVALS


def lesson_identifiable(demos,query):
    return [f"{name} fits every demo and disagrees on the query"
            for name,rival in LESSON_COMPETITORS.items()
            if all(rival(pair["input"])==pair["output"] for pair in demos)
            and rival(query["input"])!=query["output"]]
