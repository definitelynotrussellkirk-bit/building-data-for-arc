"""Semantic generator for ARC task b0087e6a72e9.

Use the modal color as background and extract monochrome 4-connected objects.
Keep objects whose bounding box is at least 3x3, at most 25 cells, and contains
at least one background hole.  Rank by bbox area, tall/wide/square orientation,
top-bottom symmetry, then top row and left column; crop the winner's bbox.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "b0087e6a72e9"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "7b8bf7c732a8"
SUMMARY = "Crop the lexicographically smallest qualifying patterned object by area, orientation, symmetry, row, and column."
INVARIANTS = [
    "background is the modal grid color",
    "qualifying objects have bbox dimensions at least 3x3 and area at most 25",
    "qualifying objects leave at least one background hole in their bbox",
    "the output is the exact input crop of the minimum-ranked object",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4", "public_5")
GENERAL_PROFILES = (
    "area_smallest",
    "tall_over_wide",
    "symmetric_over_asymmetric",
    "top_over_bottom",
    "left_over_right",
    "filter_decoys",
    "many_candidates",
    "mixed_candidates",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "exact-public and full ranking-chain lessons", "valid": "|".join(SCENE_PROFILES)}}

_PUBLIC_ROWS = {
 "public_1":"22222222222222222/22222222222222222/22228882222222222/22228222222222222/22228882222222222/22222282222222222/22228882222222222/22222222222222222/22222222222222222/22222222222222222/22222222323232222/22222222333332222/22222222223222222/11112222222222222/11112222222222222/22222222222222222/22222222222222222/11112222222222222/11112222222222222",
 "public_2":"888888888888888888/888888888888888888/888888888888888888/888888888888888888/888838388888888888/888333338888888888/888838388888888888/888888888888888888/888888888888488888/888888888884448888/866888888888488888/866888888884448888/666668888888488888/666668888888888888/866888888888888888/866888888888888888/666668888888888888/666668888888888888",
 "public_3":"11111111111111111/11111111111111111/11111811811111111/11111888811111111/11111811811111111/11111888811111111/11111111111111111/11111111111111111/11111111111111111/22222111133311111/22222111331331111/21122221133311111/21122221111111111/22222111111111111/22222111111111111",
 "public_4":"11111111111111111/11111111111111111/11111111111331331/11122222111311131/11121212111333331/11111112111113111/11121212111333331/11122222111111111/11111111111111111/11188888888881111/11188888888881111/11188118811881111/11188118811881111/11111111111881111/11111111111881111/11188118811881111/11188118811881111",
 "public_5":"333333333333333333/333333333333333333/333333333131133333/333333333113133333/333333333131133333/333633333333333333/336663333333333333/333633333333333333/336663333333333333/333333333333333333/333333333333333333/333333333333333333/333333338833333333/333333338833333333/333333888888333333/333333888888333333/333333338833333333/333333338833333333"}
def _decode(s): return [[int(v) for v in row] for row in s.split("/")]
_PUBLIC_INPUTS={k:_decode(v) for k,v in _PUBLIC_ROWS.items()};_PUBLIC_SIGNATURES={tuple(map(tuple,g)):k for k,g in _PUBLIC_INPUTS.items()}

def _valid(grid):
 if not isinstance(grid,(list,tuple)) or not grid:return ["grid must be non-empty"]
 if not isinstance(grid[0],(list,tuple)) or not grid[0]:return ["rows must be non-empty"]
 w=len(grid[0])
 if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in grid):return ["grid must be rectangular"]
 if len(grid)>30 or w>30:return ["grid dimensions must not exceed 30"]
 if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for row in grid for v in row):return ["cells must be ARC colors"]
 return []

def _mode(grid):
 counts={c:sum(v==c for row in grid for v in row) for c in range(10)}
 return min(counts,key=lambda c:(-counts[c],c))

def _objects(grid,bg):
 h,w=len(grid),len(grid[0]);unseen={(r,c) for r in range(h) for c in range(w) if grid[r][c]!=bg};out=[]
 while unseen:
  seed=min(unseen);color=grid[seed[0]][seed[1]];todo=[seed];cells=set()
  while todo:
   cell=todo.pop()
   if cell not in unseen or grid[cell[0]][cell[1]]!=color:continue
   unseen.remove(cell);cells.add(cell);r,c=cell
   todo.extend(p for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)) if p in unseen)
  out.append({"color":color,"cells":cells})
 return out

def _bbox(cells):
 rs=[r for r,_ in cells];cs=[c for _,c in cells];return min(rs),min(cs),max(rs),max(cs)
def _crop(grid,bb):
 r1,c1,r2,c2=bb;return [list(row[c1:c2+1]) for row in grid[r1:r2+1]]
def _features(grid,obj):
 bb=_bbox(obj["cells"]);h=bb[2]-bb[0]+1;w=bb[3]-bb[1]+1;area=h*w;crop=_crop(grid,bb)
 return {"bbox":bb,"height":h,"width":w,"area":area,"holes":area-len(obj["cells"]),"symmetric":crop==crop[::-1],"crop":crop}
def _candidate(f):return f["holes"]>0 and f["height"]>=3 and f["width"]>=3 and f["area"]<=25
def _rank(f):
 orient=0 if f["height"]>f["width"] else 1 if f["width"]>f["height"] else 2
 return f["area"],orient,0 if f["symmetric"] else 1,f["bbox"][0],f["bbox"][1]

def rule_mirror(grid):
 errs=_valid(grid)
 if errs:raise ValueError("; ".join(errs))
 bg=_mode(grid);features=[_features(grid,o) for o in _objects(grid,bg)];cands=[f for f in features if _candidate(f)]
 if not cands:raise ValueError("no qualifying patterned object")
 return [row[:] for row in min(cands,key=_rank)["crop"]]

def _profile(features,cands):
 sig=sorted((f["height"],f["width"],0 if f["symmetric"] else 1) for f in cands)
 if sig==[(3,3,0),(3,4,0),(4,4,0)]:return "area_smallest"
 if sig==[(3,4,0),(4,3,0)]:return "tall_over_wide"
 if sig==[(4,3,0),(4,3,1)]:return "symmetric_over_asymmetric"
 if sig==[(4,4,0),(4,4,0)]:return "top_over_bottom"
 if sig==[(3,5,0),(3,5,0)]:return "left_over_right"
 if sig==[(4,3,0)] and len(features)>=4:return "filter_decoys"
 if sig==[(3,3,0),(3,4,0),(4,3,0),(4,4,0),(5,5,0)]:return "many_candidates"
 return "mixed_candidates"

def _analysis(grid):
 errors=_valid(grid);result={"errors":errors,"scene_profile":None}
 if errors:return result
 bg=_mode(grid);object_list=_objects(grid,bg);features=[_features(grid,o) for o in object_list];cands=[f for f in features if _candidate(f)]
 if not cands:errors.append("expected at least one qualifying patterned object");return result
 selected=min(cands,key=_rank);public=_PUBLIC_SIGNATURES.get(tuple(map(tuple,grid)));profile=public or _profile(features,cands)
 if profile not in SCENE_PROFILES:errors.append("ranking lesson does not match a declared profile")
 result.update({"background":bg,"objects":object_list,"features":features,"candidates":cands,"candidate_count":len(cands),"selected":selected,"selected_rank":_rank(selected),"output":[row[:] for row in selected["crop"]],"scene_profile":profile,"errors":errors});return result

def canonical_profile_signature(grid):
 a=_analysis(grid);p=a.get("scene_profile");return p if not a["errors"] and p in PUBLIC_PROFILES else None
def observe_overrides(grid):
 a=_analysis(grid)
 if a["errors"]:raise ValueError("; ".join(a["errors"]))
 return {"scene_profile":a["scene_profile"]}

def _frame(h,w,rng,symmetric=True):
 cells={(r,c) for r in range(h) for c in range(w) if r in (0,h-1) or c in (0,w-1)}
 interior=[(r,c) for r in range(1,h-1) for c in range(1,w-1)];rng.shuffle(interior)
 if symmetric:
  pairs=[]
  for cell in interior:
   pair=(h-1-cell[0],cell[1]);group=frozenset((cell,pair))
   if group not in pairs:pairs.append(group)
  for group in pairs[:-1]:
   if rng.random()<.45:cells.update(group)
 else:
  if h>=4:cells.add((1,1))
 return cells
def _solid(h,w):return {(r,c) for r in range(h) for c in range(w)}
def _place(grid,cells,top,left,color):
 for r,c in cells:grid[top+r][left+c]=color

def _build(rng,profile,band):
 ranges={"easy":(22,24),"medium":(24,27),"hard":(27,30)};lo,hi=ranges[band];h=rng.randint(lo,hi);w=rng.randint(lo,hi)
 colors=list(range(10));rng.shuffle(colors);bg=colors.pop();grid=[[bg]*w for _ in range(h)];specs=[]
 if profile=="area_smallest":specs=[(3,3,True,"cand"),(3,4,True,"cand"),(4,4,True,"cand")]
 elif profile=="tall_over_wide":specs=[(4,3,True,"cand"),(3,4,True,"cand")]
 elif profile=="symmetric_over_asymmetric":specs=[(4,3,True,"cand"),(4,3,False,"cand")]
 elif profile=="top_over_bottom":specs=[(4,4,True,"cand"),(4,4,True,"cand")]
 elif profile=="left_over_right":specs=[(3,5,True,"cand"),(3,5,True,"cand")]
 elif profile=="filter_decoys":specs=[(4,3,True,"cand"),(3,3,True,"solid"),(1,5,True,"solid"),(6,5,True,"cand")]
 elif profile=="many_candidates":specs=[(3,3,True,"cand"),(4,3,True,"cand"),(3,4,True,"cand"),(4,4,True,"cand"),(5,5,True,"cand")]
 else:
  extras=[(4,5),(5,4),(5,5)];rng.shuffle(extras);pool=[(3,5),(5,3),(4,4)]+extras[:rng.randint(0,3)];specs=[(a,b,True,"cand") for a,b in pool]
 placements=[];base_top=rng.randint(1,2);base_left=rng.randint(1,2)
 for index,(oh,ow,sym,kind) in enumerate(specs):
  if profile=="top_over_bottom":top=2+index*7;left=2
  elif profile=="left_over_right":top=2;left=2+index*7
  else:
   top=base_top+(index//3)*7;left=base_left+(index%3)*7
  cells=_solid(oh,ow) if kind=="solid" else _frame(oh,ow,rng,sym)
  _place(grid,cells,top,left,colors[index%len(colors)]);placements.append((top,left,oh,ow))
 return grid

def _band(d):
 if d in (None,"medium"):return "medium"
 if d in ("easy","hard"):return d
 raise ValueError(f"unknown difficulty: {d!r}")
def generate(seed,sample_index,*,difficulty=None,**overrides):
 unknown=set(overrides)-{"scene_profile"}
 if unknown:raise ValueError(f"unknown override(s): {sorted(unknown)}")
 requested=overrides.get("scene_profile")
 if requested is not None and requested not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {requested!r}")
 band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides)
 profile=requested or ctx.draw_choice("scene_profile",list(PUBLIC_PROFILES)+[p for p in GENERAL_PROFILES for _ in range(4)])
 return [row[:] for row in _PUBLIC_INPUTS[profile]] if profile in PUBLIC_PROFILES else _build(ctx.draw_rng("layout"),profile,band)
def self_check(grid,*,difficulty=None,meta=None):return list(_analysis(grid)["errors"])
