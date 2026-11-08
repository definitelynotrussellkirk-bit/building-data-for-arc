"""Constructive same-color diagonal-distance-two midpoint lessons."""
from __future__ import annotations
from collections import Counter
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
GENERATOR_ID=TASK_ID="69927005ac25"; VERSION="3.0.0"
SUMMARY="Fill the empty midpoint of every same-color pair separated by (2,+/-2); preserve all existing cells."
PALETTE_KINDS=("default","warm","cool","varied"); HELPFUL_TEXTURES=PALETTE_KINDS
DEGENERATE_TEXTURES=("no_pairs","midpoint_filled","axis_aligned")
AXES={
 "grid_h":{"type":"int","default":"rng 7..10","valid":"5..12"},
 "grid_w":{"type":"int","default":"rng 8..11","valid":"6..14"},
 "n_pairs":{"type":"int","default":"rng 2..3","valid":"1..4","aliases":["palette_size","n_distinct_colors"]},
 "palette_kind":{"type":"str","default":"default","valid":"|".join(PALETTE_KINDS),"aliases":["texture"]},
 "palette_size":{"type":"int","default":"same as n_pairs","valid":"1..4","aliases":["n_pairs","n_distinct_colors"]},
 "n_distinct_colors":{"type":"int","default":"same as n_pairs","valid":"1..4","aliases":["n_pairs","palette_size"]},
 "position_bias":{"type":"str","default":"diagonal_distance_2_pairs","valid":"diagonal_distance_2_pairs"},
 "density":{"type":"str","default":"sparse","valid":"sparse"},
 "texture":{"type":"str","default":"alias for palette_kind","valid":"|".join(HELPFUL_TEXTURES+DEGENERATE_TEXTURES),"aliases":["palette_kind"]},
}
_POOLS={"default":tuple(range(1,9)),"warm":(2,4,6,7,9),"cool":(1,3,5,8),"varied":tuple(range(1,10))}

def _pairs(grid):
    by={}
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v: by.setdefault(v,[]).append((r,c))
    return by

def self_check(grid,*,difficulty=None,meta=None):
    if not grid or not grid[0]: return ["empty grid"]
    h,w=len(grid),len(grid[0])
    if any(len(row)!=w for row in grid): return ["ragged grid"]
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row): return ["invalid color"]
    texture=(meta or {}).get("texture","")
    if texture in DEGENERATE_TEXTURES: return []
    by=_pairs(grid); errs=[]
    if not by: return ["no diagonal pairs"]
    for color,ps in by.items():
        if len(ps)!=2: errs.append(f"color {color} does not appear exactly twice"); continue
        (r,c),(rr,cc)=ps
        if abs(r-rr)!=2 or abs(c-cc)!=2: errs.append(f"color {color} is not a distance-two diagonal pair")
        elif grid[(r+rr)//2][(c+cc)//2]!=0: errs.append(f"color {color} midpoint is not empty")
    return errs

def observe_overrides(grid):
    n=len(_pairs(grid)); return {"grid_h":len(grid),"grid_w":len(grid[0]),"n_pairs":n,"palette_size":n,"n_distinct_colors":n}

def _dim(ctx,name,default,valid):
    return ctx.draw_int_strict(name,*valid) if ctx.overrides.get(name) is not None else ctx.draw_int_strict(name,*default)

def generate(seed,sample_index,*,difficulty=None,**overrides):
    unknown=set(overrides)-set(AXES)
    if unknown: raise ValueError(f"unknown override(s): {sorted(unknown)}")
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    h=_dim(ctx,"grid_h",(7,8) if difficulty=="easy" else ((9,10) if difficulty=="hard" else (7,10)),(5,12))
    w=_dim(ctx,"grid_w",(8,9) if difficulty=="easy" else ((10,11) if difficulty=="hard" else (8,11)),(6,14))
    texture=ctx.draw_choice("texture",HELPFUL_TEXTURES+DEGENERATE_TEXTURES) if overrides.get("texture") is not None else ctx.draw_choice("texture",("default",))
    kind=ctx.draw_choice("palette_kind",PALETTE_KINDS) if overrides.get("palette_kind") is not None else ctx.draw_choice("palette_kind",(texture if texture in HELPFUL_TEXTURES else "default",))
    if texture in HELPFUL_TEXTURES and overrides.get("palette_kind") not in (None,texture): raise ValueError("texture and palette_kind aliases conflict")
    ctx.draw_choice("position_bias",("diagonal_distance_2_pairs",)); ctx.draw_choice("density",("sparse",))
    g=full_grid(h,w,0); rng=ctx.draw_rng("layout")
    if texture in DEGENERATE_TEXTURES:
        if texture=="midpoint_filled": g[1][1]=g[2][2]=g[3][3]=4
        elif texture=="axis_aligned": g[3][1]=g[3][3]=4
        return g
    aliases=[k for k in ("n_pairs","palette_size","n_distinct_colors") if overrides.get(k) is not None]
    if aliases:
        vals=[ctx.draw_int_strict(k,1,4) for k in aliases]
        if len(set(vals))!=1: raise ValueError("n_pairs, palette_size and n_distinct_colors aliases must agree")
        n=vals[0]
    else:
        n=ctx.draw_int_strict("n_pairs",2,2 if difficulty=="easy" else (4 if difficulty=="hard" else 3))
    pool=_POOLS[kind]
    if len(pool)<n: raise ValueError("palette kind cannot supply requested colors")
    colors=rng.sample(list(pool),n)
    candidates=[]
    for r in range(h-2):
        for c in range(w):
            for dc in (-2,2):
                if 0<=c+dc<w: candidates.append(((r,c),(r+2,c+dc),(r+1,c+dc//2)))
    rng.shuffle(candidates); used=set(); chosen=[]
    for a,b,m in candidates:
        if {a,b,m}&used: continue
        chosen.append((a,b,m)); used|={a,b,m}
        if len(chosen)==n: break
    if len(chosen)!=n: raise ValueError("requested pair count exceeds separated layout capacity")
    for color,(a,b,m) in zip(colors,chosen):
        g[a[0]][a[1]]=color; g[b[0]][b[1]]=color
    return g
