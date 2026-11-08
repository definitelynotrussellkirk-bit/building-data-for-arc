"""Column gravity: preserve each column's nonzero order and compress downward.

Only grid dimensions and occupied-cell count are exact controls. Old palette,
texture, density and position aliases were inert and are deliberately rejected.
"""
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from reviewer_support import normalize_grid

GENERATOR_ID = TASK_ID = "e1e0e42362aa"
VERSION = "2.0.0"
RULE_HASH = "e51db089d1da"
SUMMARY = "Compress each column downward, preserving nonzero color order."
INVARIANTS = ["literal ARC grid", "at least one nonzero cell", "at least one cell falls"]
AXES = {
    "grid_h":{"type":"int","valid":"5..15","default":"band range within 7..15"},
    "grid_w":{"type":"int","valid":"5..15","default":"band range within 7..15"},
    "n_cells":{"type":"int","valid":"1..30","default":"rng 1..min(30, capacity-1)"},
}
HELPFUL_TEXTURES = DEGENERATE_TEXTURES = ()
# Every declared cross-product fits except n_cells >= grid_h*grid_w; reserve
# one empty bottom cell so ordinary inputs exhibit actual movement.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (("grid_h", "grid_w", "n_cells"),)


def rule_mirror(grid):
    grid=normalize_grid(grid)
    h,w=len(grid),len(grid[0]);out=full_grid(h,w,0)
    for c in range(w):
        values=[grid[r][c] for r in range(h) if grid[r][c]]
        for r,v in enumerate(values,h-len(values)): out[r][c]=v
    return out


def observe_overrides(grid):
    grid=normalize_grid(grid)
    return {"grid_h":len(grid),"grid_w":len(grid[0]),"n_cells":sum(v!=0 for row in grid for v in row)}


def self_check(grid,*,difficulty=None,meta=None):
    try:
        grid=normalize_grid(grid)
    except (ValueError,TypeError): return ["expected a literal rectangular ARC grid"]
    if len(grid)>30 or len(grid[0])>30: return ["grid exceeds ARC bounds"]
    errors=[]
    if rule_mirror(grid)==grid: errors.append("at least one cell must fall")
    observed=observe_overrides(grid)
    for key,value in (meta or {}).get("overrides",{}).items():
        if key in AXES and (type(value) is not int or observed[key]!=value): errors.append(f"override {key} does not match observed value")
    return errors


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if set(overrides)-set(AXES): raise ValueError("unknown override")
    if difficulty not in (None,"easy","medium","hard"): raise ValueError("unknown difficulty")
    if type(sample_index) is not int or sample_index<0: raise ValueError("invalid sample_index")
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    lo,hi={"easy":(7,8),"medium":(7,11),"hard":(11,15),None:(7,15)}[difficulty]
    h=ctx.draw_int_strict("grid_h",*((5,15) if "grid_h" in overrides else (lo,hi)))
    w=ctx.draw_int_strict("grid_w",*((5,15) if "grid_w" in overrides else (lo,hi)))
    n=ctx.draw_int_strict("n_cells",1,30 if "n_cells" in overrides else min(30,h*w-1))
    if n>=h*w:
        exc=ValueError("incompatible overrides: n_cells must be less than grid_h*grid_w")
        exc.incompatible_axes=("grid_h","grid_w","n_cells")
        raise exc
    rng=ctx.draw_rng("placements");color_rng=ctx.draw_rng("colors")
    # Keep the bottom of column zero empty and a cell above it occupied.
    # Remaining positions are sampled without replacement; no retry loop.
    available=[(r,c) for r in range(h) for c in range(w) if (r,c) not in ((0,0),(h-1,0))]
    positions=[(0,0)]+rng.sample(available,n-1)
    grid=full_grid(h,w,0)
    for r,c in positions: grid[r][c]=color_rng.randint(1,9)
    return grid
