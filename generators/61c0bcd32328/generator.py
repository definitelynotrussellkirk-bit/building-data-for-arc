"""Semantic generator for ARC task 61c0bcd32328.

On a dominant nonzero background, copy every monochrome component whose
bounding box touches a canvas corner clockwise to the next corner.  Preserve
the entire input and paint copied cells in the component's color.
"""
from __future__ import annotations

from collections import Counter
from puzzle_generators.base import gen_ctx

GENERATOR_ID = "61c0bcd32328"
TASK_ID = GENERATOR_ID
VERSION = "2.1.0"
RULE_HASH = "e3835c9a174e"
SUMMARY = "Copy corner-anchored components clockwise while preserving all input cells."
INVARIANTS = [
    "the modal nonzero color is the canvas background",
    "same-color 4-connected components define objects",
    "at least one object bounding box touches a grid corner",
    "corner objects are copied TL-to-TR-to-BR-to-BL-to-TL without erasing originals",
    "non-corner objects remain unchanged",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_train_3", "public_test_1")
GENERAL_CORNERS = {
    "single_tl": ("tl",), "single_tr": ("tr",), "single_br": ("br",), "single_bl": ("bl",),
    "adjacent_top": ("tl", "tr"), "adjacent_right": ("tr", "br"),
    "adjacent_bottom": ("br", "bl"), "adjacent_left": ("tl", "bl"),
    "three_missing_tl": ("tr", "br", "bl"), "three_missing_br": ("tl", "tr", "bl"),
    "all_four_sparse": ("tl", "tr", "br", "bl"),
    "all_four_dense": ("tl", "tr", "br", "bl"),
}
GENERAL_PROFILES = tuple(GENERAL_CORNERS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "weighted rng over public and corner/clutter lessons",
         "valid": "public_train_1|public_train_2|public_train_3|public_test_1|single_tl|single_tr|single_br|single_bl|adjacent_top|adjacent_right|adjacent_bottom|adjacent_left|three_missing_tl|three_missing_br|all_four_sparse|all_four_dense"}}

_PUBLIC_ROWS = {
 "public_train_1": ("4477779766","4477779976","7777779986","7777577776","7777557777","7577777777","7557777777","7778777777","2788777797","2777777799"),
 "public_train_2": ("57377799","57377799","57777777","77755577","77773777","77773775","72273775","72277775"),
 "public_train_3": ("67337222","67337776","77757776","72775777","72227777","77766777","55777774","55777774"),
 "public_test_1": ("8877777776777755","8877777776777755","8877755576799778","7777779776797887","7777779776777887","7999779777777777","7797777777777777","7777777888877777","7777777787773333","7722777777777777","7722799777777777","6777799777777777","6777777777788777","1111777777788778","1111777777777778","1111667777777778"),
}
_PUBLIC_INPUTS = {name: [[int(x) for x in row] for row in rows] for name, rows in _PUBLIC_ROWS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}

_SHAPES = (
 ((0,0),), ((0,0),(0,1)), ((0,0),(1,0)), ((0,0),(0,1),(1,0)),
 ((0,0),(0,1),(1,1)), ((0,0),(1,0),(1,1)), ((0,0),(0,1),(1,0),(1,1)),
 ((0,0),(0,1),(0,2)), ((0,0),(0,1),(0,2),(1,1)),
)

def _validate_grid(grid):
    if not isinstance(grid,(list,tuple)) or not grid: return ["grid must be non-empty"],0,0
    if not isinstance(grid[0],(list,tuple)) or not grid[0]: return ["rows must be non-empty"],0,0
    h,w=len(grid),len(grid[0])
    if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in grid): return ["grid must be rectangular"],h,w
    if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for row in grid for v in row): return ["cells must be integer ARC colors"],h,w
    return [],h,w

def _background(grid):
    freq=Counter(v for row in grid for v in row if v!=0)
    return freq.most_common(1)[0][0] if freq else None

def _parts(grid,bg):
    h,w=len(grid),len(grid[0]); remaining={(r,c) for r in range(h) for c in range(w) if grid[r][c]!=bg}; result=[]
    while remaining:
        start=min(remaining); color=grid[start[0]][start[1]]; remaining.remove(start); cells={start}; stack=[start]
        while stack:
            r,c=stack.pop()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in remaining and grid[q[0]][q[1]]==color:
                    remaining.remove(q); cells.add(q); stack.append(q)
        result.append({"cells":frozenset(cells),"color":color,"bbox":(min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells))})
    return result

def _corner(part,h,w):
    r1,c1,r2,c2=part["bbox"]
    if r1==0 and c1==0:return "tl"
    if r1==0 and c2==w-1:return "tr"
    if r2==h-1 and c2==w-1:return "br"
    if r2==h-1 and c1==0:return "bl"
    return None

def _analysis(grid):
    errors,h,w=_validate_grid(grid); result={"errors":errors,"height":h,"width":w,"scene_profile":None}
    if errors:return result
    bg=_background(grid)
    if bg is None: errors.append("a dominant nonzero background is required"); return result
    parts=_parts(grid,bg); corner_parts=[(c,p) for p in parts if (c:=_corner(p,h,w))]
    if len(parts)<3: errors.append("at least three foreground components are required")
    if not corner_parts: errors.append("at least one corner-anchored component is required")
    corners=tuple(c for c in ("tl","tr","br","bl") if any(found==c for found,_ in corner_parts))
    output=[list(row) for row in grid]
    for corner,part in corner_parts:
        r1,c1,r2,c2=part["bbox"]
        dr={"tl":0,"tr":h-1-r2,"br":0,"bl":-r1}[corner]
        dc={"tl":w-1-c2,"tr":0,"br":-c1,"bl":0}[corner]
        for r,c in part["cells"]:
            nr,nc=r+dr,c+dc
            if 0<=nr<h and 0<=nc<w: output[nr][nc]=part["color"]
    signature=tuple(map(tuple,grid)); profile=_PUBLIC_SIGNATURES.get(signature)
    if profile is None:
        candidates=[name for name,value in GENERAL_CORNERS.items() if value==corners]
        if len(candidates)==2: profile="all_four_sparse" if len(parts)<=10 else "all_four_dense"
        elif candidates: profile=candidates[0]
    if profile not in SCENE_PROFILES: errors.append("corner/clutter structure does not match a declared lesson")
    result.update({"background":bg,"parts":parts,"corner_parts":corner_parts,"corners":corners,"output":output,"scene_profile":profile,"errors":errors})
    return result

def canonical_profile_signature(grid):
    info=_analysis(grid); p=info.get("scene_profile"); return p if not info["errors"] and p in PUBLIC_PROFILES else None

def observe_overrides(grid):
    info=_analysis(grid)
    if info["errors"]: raise ValueError("; ".join(info["errors"]))
    return {"scene_profile":info["scene_profile"]}

def rule_mirror(grid):
    info=_analysis(grid)
    if info["errors"]: raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]

def _band(difficulty):
    if difficulty in (None,"medium"):return "medium"
    if difficulty in ("easy","hard"):return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")

def _dims(rng,band):
    bounds={"easy":(8,10),"medium":(10,13),"hard":(14,16)}; lo,hi=bounds[band]; return rng.randint(lo,hi),rng.randint(lo,hi)

def _paint(grid,shape,color,r0,c0):
    for dr,dc in shape:grid[r0+dr][c0+dc]=color

def _general_grid(rng,profile,band):
    h,w=_dims(rng,band); bg=rng.choice(range(1,10)); grid=[[bg for _ in range(w)] for _ in range(h)]
    corners=GENERAL_CORNERS[profile]; colors=[c for c in range(1,10) if c!=bg]
    anchors={"tl":lambda sh,sw:(0,0),"tr":lambda sh,sw:(0,w-sw),"br":lambda sh,sw:(h-sh,w-sw),"bl":lambda sh,sw:(h-sh,0)}
    for index,corner in enumerate(corners):
        shape=rng.choice(_SHAPES); sh=max(r for r,c in shape)+1; sw=max(c for r,c in shape)+1
        r0,c0=anchors[corner](sh,sw); _paint(grid,shape,colors[index%len(colors)],r0,c0)
    if profile=="all_four_sparse": clutter=rng.randint(3,5)
    elif profile=="all_four_dense": clutter=rng.randint(7,12)
    else: clutter={"easy":rng.randint(3,5),"medium":rng.randint(6,9),"hard":rng.randint(10,14)}[band]
    placed=0
    for _ in range(2000):
        if placed>=clutter:break
        shape=rng.choice(_SHAPES[:3] if profile=="all_four_dense" else _SHAPES)
        sh=max(r for r,c in shape)+1; sw=max(c for r,c in shape)+1
        if h-sh<=2 or w-sw<=2:continue
        r0=rng.randint(1,h-sh-1);c0=rng.randint(1,w-sw-1);color=rng.choice(colors)
        cells={(r0+dr,c0+dc) for dr,dc in shape}
        if any(grid[r][c]!=bg for r,c in cells):continue
        if any(grid[nr][nc]==color for r,c in cells for nr,nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if 0<=nr<h and 0<=nc<w):continue
        _paint(grid,shape,color,r0,c0);placed+=1
    if placed<clutter: raise ValueError("could not place requested clutter")
    return grid

def generate(seed,sample_index,*,difficulty=None,**overrides):
    unknown=set(overrides)-{"scene_profile"}
    if unknown:raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested=overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {requested!r}")
    band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides)
    weighted=list(PUBLIC_PROFILES)+[p for p in GENERAL_PROFILES for _ in range(3)];profile=ctx.draw_choice("scene_profile",weighted);rng=ctx.draw_rng("layout")
    if profile in PUBLIC_PROFILES:return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_grid(rng,profile,band)

def self_check(grid,*,difficulty=None,meta=None):
    info=_analysis(grid)
    if info["errors"]:return list(info["errors"])
    if info["output"]==grid:return ["corner copying must change at least one cell"]
    if len(info["parts"])<1:return ["no foreground components"]
    return []
