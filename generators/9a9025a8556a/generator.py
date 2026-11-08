"""Semantic generator for ARC task 9a9025a8556a.

For each 4-connected nonzero object, recolor every cell red 2 when its
bounding box is taller than wide, cyan 8 when wider than tall, and otherwise
preserve it.  Calibrated training scenes use the task's stated magenta 6.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx

GENERATOR_ID="9a9025a8556a"
TASK_ID=GENERATOR_ID
VERSION="4.0.0"
RULE_HASH="3cda6c1c7f6d"
SUMMARY="Recolor nonzero objects by bounding-box aspect: tall to 2, wide to 8, square unchanged."
INVARIANTS=["calibrated objects are color 6 on background 0","objects are 4-connected and mutually nonadjacent","every scene contains tall, wide, and square bounding boxes","object cells are recolored as wholes according to bounding-box height versus width"]
PUBLIC_PROFILES=()
PROFILE_COUNTS={"balanced":(1,1,1),"dense":(2,2,2),"tall_heavy":(3,1,1),"wide_heavy":(1,3,1),"square_heavy":(1,1,3),"tall_pair":(2,1,1),"wide_pair":(1,2,1),"square_pair":(1,1,2)}
GENERAL_PROFILES=tuple(PROFILE_COUNTS);SCENE_PROFILES=GENERAL_PROFILES;HELPFUL_TEXTURES=();DEGENERATE_TEXTURES=()
AXES={"scene_profile":{"type":"str","default":"weighted aspect-count lessons","valid":"balanced|dense|tall_heavy|wide_heavy|square_heavy|tall_pair|wide_pair|square_pair"}}
TALL_PATTERNS=(((1,), (1,)),((1,), (1,), (1,)),((1,), (1,), (1,), (1,)),((1,1),(1,0),(1,0)),((1,0),(1,1),(0,1),(0,1)),((1,1),(1,0),(1,1),(1,0)))
WIDE_PATTERNS=tuple(tuple(zip(*p)) for p in TALL_PATTERNS)
SQUARE_PATTERNS=(((1,),),((1,1),(1,1)),((1,1),(1,0)),((1,1,1),(1,0,1),(1,1,1)),((1,1,0),(0,1,0),(0,1,1)),((1,1,1),(1,1,1),(1,1,1)))
_DIRS=((-1,0),(1,0),(0,-1),(0,1))

def _valid(g):
 if not isinstance(g,(list,tuple)) or not g:return ["grid must be non-empty"]
 if not isinstance(g[0],(list,tuple)) or not g[0]:return ["rows must be non-empty"]
 w=len(g[0])
 if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in g):return ["grid must be rectangular"]
 if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for row in g for v in row):return ["cells must be ARC colors"]
 return []
def _components(g):
 h=len(g);w=len(g[0]);seen=set();out=[]
 for r in range(h):
  for c in range(w):
   if g[r][c]==0 or (r,c) in seen:continue
   color=g[r][c];todo=[(r,c)];cells=set()
   while todo:
    rr,cc=todo.pop()
    if not 0<=rr<h or not 0<=cc<w or (rr,cc) in seen or g[rr][cc]!=color:continue
    seen.add((rr,cc));cells.add((rr,cc));todo.extend((rr+dr,cc+dc) for dr,dc in _DIRS)
   out.append(cells)
 return out
def _record(cells):
 rs=[r for r,_ in cells];cs=[c for _,c in cells];bh=max(rs)-min(rs)+1;bw=max(cs)-min(cs)+1;aspect="tall" if bh>bw else "wide" if bw>bh else "square"
 return {"cells":cells,"bbox_height":bh,"bbox_width":bw,"area":len(cells),"aspect":aspect,"touches_boundary":None}
def _solve(g):
 out=[list(row) for row in g];records=[]
 for cells in _components(g):
  record=_record(cells);records.append(record);color=2 if record["aspect"]=="tall" else 8 if record["aspect"]=="wide" else None
  if color is not None:
   for r,c in cells:out[r][c]=color
 return out,records
def _analysis(g):
 errors=_valid(g);result={"errors":errors,"scene_profile":None}
 if errors:return result
 h=len(g);w=len(g[0]);output,records=_solve(g)
 if any(v not in (0,6) for row in g for v in row):errors.append("calibrated scenes may contain only background 0 and object color 6")
 for x in records:x["touches_boundary"]=any(r in (0,h-1) or c in (0,w-1) for r,c in x["cells"])
 counts=tuple(sum(x["aspect"]==a for x in records) for a in ("tall","wide","square"));profile=next((p for p,v in PROFILE_COUNTS.items() if v==counts),None)
 if not all(counts):errors.append("scene must exercise tall, wide, and square branches")
 if profile is None:errors.append("aspect-count tuple does not match a declared profile")
 result.update({"objects":[x["cells"] for x in records],"records":records,"aspect_counts":{"tall":counts[0],"wide":counts[1],"square":counts[2]},"output":output,"scene_profile":profile,"errors":errors});return result
def canonical_profile_signature(g):return None
def observe_overrides(g):
 a=_analysis(g)
 if a["errors"]:raise ValueError("; ".join(a["errors"]))
 return {"scene_profile":a["scene_profile"]}
def rule_mirror(g):
 errors=_valid(g)
 if errors:raise ValueError("; ".join(errors))
 return _solve(g)[0]
def _band(d):
 if d in (None,"medium"):return "medium"
 if d in ("easy","hard"):return d
 raise ValueError(f"unknown difficulty: {d!r}")
def _can_place(occupied,pattern,top,left,h,w):
 cells={(top+r,left+c) for r,row in enumerate(pattern) for c,v in enumerate(row) if v}
 if any(not 0<=r<h or not 0<=c<w for r,c in cells):return None
 if cells&occupied:return None
 if any((r+dr,c+dc) in occupied for r,c in cells for dr,dc in _DIRS):return None
 return cells
def _general(rng,profile,band):
 counts=PROFILE_COUNTS[profile];ranges={"easy":(10,14),"medium":(14,20),"hard":(20,28)};lo,hi=ranges[band];families=(TALL_PATTERNS,WIDE_PATTERNS,SQUARE_PATTERNS)
 for _ in range(100):
  h=rng.randint(lo,hi);w=rng.randint(lo,hi);plan=[]
  for family,n in zip(families,counts):plan.extend(rng.choice(family) for _ in range(n))
  rng.shuffle(plan);occupied=set();placed=[]
  for pattern in plan:
   ph=len(pattern);pw=len(pattern[0]);spots=[]
   for r in range(0,h-ph+1):
    for c in range(0,w-pw+1):
     cells=_can_place(occupied,pattern,r,c,h,w)
     if cells is not None:spots.append(cells)
   if not spots:break
   cells=rng.choice(spots);placed.append(cells);occupied|=cells
  if len(placed)!=sum(counts):continue
  g=[[0]*w for _ in range(h)]
  for cells in placed:
   for r,c in cells:g[r][c]=6
  a=_analysis(g)
  if not a["errors"]:return g
 raise RuntimeError(f"could not place profile {profile!r}")
def generate(seed,sample_index,*,difficulty=None,**overrides):
 unknown=set(overrides)-{"scene_profile"}
 if unknown:raise ValueError(f"unknown override(s): {sorted(unknown)}")
 requested=overrides.get("scene_profile")
 if requested is not None and requested not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {requested!r}")
 band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides);profile=requested or ctx.draw_choice("scene_profile",list(SCENE_PROFILES));return _general(ctx.draw_rng("layout"),profile,band)
def self_check(g,*,difficulty=None,meta=None):return list(_analysis(g)["errors"])
