"""Two normalized monochrome objects overlaid; overlap is cyan (8).

The canonical Racket rule owns labels. No operation marker or color-4 mask is
part of this task. Ordinary pairs contain overlap and both exclusive regions.
"""
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from reviewer_support import normalize_grid

GENERATOR_ID = TASK_ID = "afa7a3af9331"
VERSION = "2.0.0"
RULE_HASH = "a235c2b1bb6c"
SUMMARY = "Normalize exactly two objects, preserve their colors, paint overlap 8."
INVARIANTS = ["zero background", "exactly two monochrome 4-connected objects",
              "normalize each object to its own top-left bbox corner"]
AXES = {name: {"type": "int", "valid": "2..6", "default": "band range within 2..6"}
        for name in ("shape_h", "shape_w")}
HELPFUL_TEXTURES = DEGENERATE_TEXTURES = ()
EXAMPLES_NEEDED = 3


def _objects(grid):
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    result = []
    while remaining:
        first = min(remaining)
        color = grid[first[0]][first[1]]
        cells, todo = {first}, [first]
        remaining.remove(first)
        while todo:
            r,c = todo.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining and grid[p[0]][p[1]] == color:
                    remaining.remove(p); cells.add(p); todo.append(p)
        result.append((color,cells))
    return result


def _normalize(cells):
    r0=min(r for r,c in cells); c0=min(c for r,c in cells)
    return {(r-r0,c-c0) for r,c in cells}


def self_check(grid, *, difficulty=None, meta=None):
    try:
        grid=normalize_grid(grid)
    except (ValueError,TypeError):
        return ["expected a literal rectangular ARC grid"]
    if len(grid)>30 or len(grid[0])>30: return ["grid exceeds ARC bounds"]
    if len(_objects(grid)) != 2: return ["expected exactly two monochrome objects"]
    return []


def rule_mirror(grid):
    if self_check(grid): raise ValueError("expected two objects")
    (ca,a),(cb,b)=_objects(grid)
    a,b=_normalize(a),_normalize(b)
    out=full_grid(max(r for r,c in a|b)+1,max(c for r,c in a|b)+1,0)
    for r,c in a|b: out[r][c]=8 if (r,c) in a&b else ca if (r,c) in a else cb
    return out


def generate(seed,sample_index,*,difficulty=None,**overrides):
    if type(sample_index) is not int or sample_index<0: raise ValueError("sample_index must be nonnegative integer")
    if difficulty not in (None,"easy","medium","hard"): raise ValueError("unknown difficulty")
    if set(overrides)-set(AXES): raise ValueError("unknown override")
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    lo,hi={"easy":(2,3),"medium":(3,5),"hard":(4,6),None:(2,6)}[difficulty]
    sh=ctx.draw_int_strict("shape_h",*( (2,6) if "shape_h" in overrides else (lo,hi)))
    sw=ctx.draw_int_strict("shape_w",*( (2,6) if "shape_w" in overrides else (lo,hi)))
    rng=ctx.draw_rng("objects")
    # Full connected top/left versus top/right spines. Protected opposite bottom
    # corners ensure overlap and both exclusive regions in every ordinary draw.
    a={(0,c) for c in range(sw)}|{(r,0) for r in range(sh)}
    b={(0,c) for c in range(sw)}|{(r,sw-1) for r in range(sh)}
    for cells,protected in ((a,(sh-1,sw-1)),(b,(sh-1,0))):
        for _ in range(sh*sw):
            r,c=rng.choice(sorted(cells)); dr,dc=rng.choice(((1,0),(-1,0),(0,1),(0,-1)))
            p=(r+dr,c+dc)
            if 0<=p[0]<sh and 0<=p[1]<sw and p!=protected and rng.random()<0.5: cells.add(p)
    colors=rng.sample([1,2,3,4,5,6,7,9],2)
    out=full_grid(sh+2,2*sw+5,0)
    if rng.randrange(2): a,b=b,a
    for cells,color,left in ((a,colors[0],1),(b,colors[1],sw+4)):
        for r,c in cells: out[r+1][c+left]=color
    return out


def _all_eight(grid):
    return [[8 if v else 0 for v in row] for row in rule_mirror(grid)]

SEMANTIC_RIVALS = LESSON_COMPETITORS = {"discard_object_colors":_all_eight}
CANONICAL_SHORTCUTS = {}
SEMANTIC_WITNESSES = {"preserved_exclusive_colors":lambda g: any(v not in (0,8) for row in rule_mirror(g) for v in row)}
WITNESS_RIVALS = {"preserved_exclusive_colors":["discard_object_colors"]}

def lesson_identifiable(demos,query):
    return ["object-color rival survives demonstrations"] if all(_all_eight(p["input"])==p["output"] for p in demos) else []
