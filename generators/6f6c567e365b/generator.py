"""Asymmetric multicolor lessons for the cumulative transform-script gallery.

The exact canonical rule reads key colors 1..4 from row 0, crops the motif below
row 0, emits that initial crop, then emits every cumulative transform state:
1=rotate clockwise, 2=rotate 180, 3=flip left/right, 4=flip up/down.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID=TASK_ID="6f6c567e365b"
VERSION="3.0.0"
SUMMARY=("Read row-0 keys left-to-right and output the initial motif followed by "
         "every cumulative transform state, packed with one blank column. "
         "Keys 1/2/3/4 mean rotate-CW/rotate-180/flip-LR/flip-UD.")
PALETTE_KINDS=("default","warm","cool","varied")
HELPFUL_TEXTURES=PALETTE_KINDS
DEGENERATE_TEXTURES=("no_codes","no_motif","code_in_motif_row")
AXES={
 "grid_h":{"type":"int","default":"rng 8..10","valid":"7..14"},
 "grid_w":{"type":"int","default":"rng 11..14","valid":"10..16"},
 "n_codes":{"type":"int","default":"rng 2..4","valid":"1..5"},
 "palette_kind":{"type":"str","default":"default","valid":"|".join(PALETTE_KINDS),"aliases":["texture"]},
 "palette_size":{"type":"int","default":"rng 2..3","valid":"2..3","aliases":["n_distinct_colors"]},
 "n_distinct_colors":{"type":"int","default":"rng 2..3","valid":"2..3","aliases":["palette_size"]},
 "position_bias":{"type":"str","default":"codes_top_motif_below","valid":"codes_top_motif_below"},
 "density":{"type":"str","default":"sparse","valid":"sparse"},
 "texture":{"type":"str","default":"alias for palette_kind","valid":"|".join(HELPFUL_TEXTURES+DEGENERATE_TEXTURES),"aliases":["palette_kind"]},
}
INVARIANTS=["row 0 contains 1..5 keys in 1..4","row 1 is blank",
            "ordinary motif is connected, asymmetric and uses 2..3 colors"]
_SHAPES=(
 ((0,0),(1,0),(2,0),(2,1),(2,2)),
 ((0,0),(0,1),(1,1),(2,1),(2,2)),
 ((0,0),(1,0),(1,1),(1,2),(2,2)),
 ((0,1),(1,0),(1,1),(2,1),(2,2)),
)
_POOLS={"default":tuple(range(5,10)),"warm":(2,4,6,7,9),"cool":(1,3,5,8),"varied":tuple(range(1,10))}

def _components(cells):
    cells=set(cells); todo=set(cells); out=[]
    while todo:
        start=todo.pop(); comp={start}; stack=[start]
        while stack:
            r,c=stack.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in todo: todo.remove(p); comp.add(p); stack.append(p)
        out.append(comp)
    return out

def self_check(grid,*,difficulty=None,meta=None):
    if not grid or not grid[0]: return ["empty grid"]
    h,w=len(grid),len(grid[0])
    if any(len(row)!=w for row in grid): return ["ragged grid"]
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row): return ["invalid color"]
    texture=(meta or {}).get("texture","")
    if texture in DEGENERATE_TEXTURES: return []
    errs=[]; codes=[v for v in grid[0] if v]
    if not codes or any(v not in (1,2,3,4) for v in codes): errs.append("row 0 needs transform keys 1..4")
    if h<2 or any(grid[1]): errs.append("row 1 must be blank")
    cells={(r,c) for r in range(2,h) for c in range(w) if grid[r][c]}
    if not cells: errs.append("motif missing")
    elif len(_components(cells))!=1: errs.append("motif must be 4-connected")
    elif len({grid[r][c] for r,c in cells})<2: errs.append("motif must be multicolor")
    return errs

def observe_overrides(grid):
    colors={v for row in grid[2:] for v in row if v}
    return {"grid_h":len(grid),"grid_w":len(grid[0]),"n_codes":sum(v!=0 for v in grid[0]),
            "palette_size":len(colors),"n_distinct_colors":len(colors)}

def _strict_dim(ctx,name,default):
    return ctx.draw_int_strict(name,*((7,14) if name=="grid_h" else (10,16))) if ctx.overrides.get(name) is not None else ctx.draw_int_strict(name,*default)

def generate(seed,sample_index,*,difficulty=None,**overrides):
    unknown=set(overrides)-set(AXES)
    if unknown: raise ValueError(f"unknown override(s): {sorted(unknown)}")
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    hdef=(8,8) if difficulty=="easy" else ((10,13) if difficulty=="hard" else (8,10))
    wdef=(11,12) if difficulty=="easy" else ((14,16) if difficulty=="hard" else (11,14))
    h=_strict_dim(ctx,"grid_h",hdef); w=_strict_dim(ctx,"grid_w",wdef)
    texture=ctx.draw_choice("texture",HELPFUL_TEXTURES+DEGENERATE_TEXTURES) if overrides.get("texture") is not None else ctx.draw_choice("texture",("default",))
    kind=ctx.draw_choice("palette_kind",PALETTE_KINDS) if overrides.get("palette_kind") is not None else ctx.draw_choice("palette_kind",(texture if texture in HELPFUL_TEXTURES else "default",))
    if texture in HELPFUL_TEXTURES and overrides.get("palette_kind") not in (None,texture): raise ValueError("texture and palette_kind aliases conflict")
    ctx.draw_choice("position_bias",("codes_top_motif_below",)); ctx.draw_choice("density",("sparse",))
    rng=ctx.draw_rng("layout"); g=full_grid(h,w,0)
    if texture in DEGENERATE_TEXTURES:
        if texture=="no_codes":
            for r,c in ((3,3),(3,4),(4,3)): g[r][c]=8
        elif texture=="no_motif":
            for c,k in zip((1,w//2,w-2),(1,3,4)): g[0][c]=k
        else:
            g[0][1]=1; g[0][w-2]=3; g[3][3]=1
            for r,c in ((4,5),(4,6),(5,5)): g[r][c]=8
        return g
    nlo,nhi=(2,2) if difficulty=="easy" else ((4,5) if difficulty=="hard" else (2,4))
    n=ctx.draw_int_strict("n_codes",1,min(5,w)) if overrides.get("n_codes") is not None else ctx.draw_int_strict("n_codes",nlo,min(nhi,w))
    requested=[k for k in ("palette_size","n_distinct_colors") if overrides.get(k) is not None]
    if requested:
        vals=[ctx.draw_int_strict(k,2,3) for k in requested]
        if len(set(vals))!=1: raise ValueError("palette_size and n_distinct_colors aliases must agree")
        distinct=vals[0]
    else: distinct=ctx.draw_int_strict("palette_size",2,3)
    pool=_POOLS[kind]
    if len(pool)<distinct: raise ValueError("palette kind cannot supply requested distinct colors")
    palette=rng.sample(list(pool),distinct)
    cols=sorted(rng.sample(range(w),n))
    keys=[rng.randint(1,4) for _ in range(n)]
    for c,k in zip(cols,keys): g[0][c]=k
    shape=rng.choice(_SHAPES); colors=[palette[i%distinct] for i in range(len(shape))]; rng.shuffle(colors)
    # Guarantee every requested color appears.
    for i,color in enumerate(palette): colors[i]=color
    sh=max(r for r,c in shape)+1; sw=max(c for r,c in shape)+1
    r0=rng.randint(2,h-sh); c0=rng.randint(0,w-sw)
    for (r,c),color in zip(shape,colors): g[r0+r][c0+c]=color
    return g
