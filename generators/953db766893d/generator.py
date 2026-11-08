"""Semantic generator for ARC task 953db766893d.

Single-color walls partition the zero cells into rooms.  Paint every room tied
for minimum area yellow 3 and every larger room yellow-gray 4, preserving walls.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx

GENERATOR_ID = "953db766893d"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "d815686e5b33"
SUMMARY="Color every minimum-size zero room 3 and every larger zero room 4 while preserving the wall lattice."
INVARIANTS=["background rooms are literal 0","all walls use one color other than 0, 3, and 4","at least two rooms tie for minimum size","at least one room is larger","wall cells are unchanged"]
PUBLIC_PROFILES=("public_1","public_2","public_3","public_4")
GENERAL_SPECS={
 "two_by_three":(2,3,1),"three_by_three":(3,3,1),"three_by_four":(3,4,2),"four_by_four":(4,4,2),
 "four_by_five":(4,5,3),"five_by_five":(5,5,4),"five_by_four":(5,4,2),"three_by_five":(3,5,3),
}
GENERAL_PROFILES=tuple(GENERAL_SPECS);SCENE_PROFILES=PUBLIC_PROFILES+GENERAL_PROFILES;HELPFUL_TEXTURES=();DEGENERATE_TEXTURES=()
AXES={"scene_profile":{"type":"str","default":"weighted exact-public and merged-room lattice lessons","valid":"public_1|public_2|public_3|public_4|two_by_three|three_by_three|three_by_four|four_by_four|four_by_five|five_by_five|five_by_four|three_by_five"}}
_PUBLIC_BLOBS={
"public_1":"00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000/11111111111111111111111111111/00000100000000000100000100000/00000000000100000100000100000/00000000000100000100000100000/00000100000100000100000100000/00000100000100000000000100000/11111111011111111111111101111/00000100000100000100000100000/00000000000000000100000100000/00000100000100000000000100000/00000100000100000100000100000/00000100000100000100000100000/11111111111111011111011110111/00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000/01111111111111111111111111111/00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000/00000100000100000100000100000",
"public_2":"000080000800008000080000/000080000800008000080000/000080000800008000080000/000080000800008000080000/888888888888888880888888/000080000800008000080000/000080000800008000080000/000000000800008000080000/000080000800008000000000/888888880888808888888888/000080000800000000080000/000080000800008000080000/000000000800008000080000/000080000000008000080000/888888888888888888880880/000080000800008000080000/000080000800008000080000/000080000000008000080000/000080000800008000080000/888888888888888888888888/000080000800008000080000/000080000800008000080000/000080000800008000080000/000080000800008000080000",
"public_3":"0000900009000090000/0000900009000090000/0000000000000090000/0000000009000090000/9999999099999999999/0000900009000090000/0000000009000090000/0000900009000090000/0000900009000090000/9999999999099999999/0000900009000090000/0000900009000090000/0000900009000090000/0000900009000090000/9999999999999999990/0000900009000000000/0000900009000090000/0000000009000090000/0000900009000090000",
"public_4":"000500050005000500050005000/000500050005000500050005000/000500000005000500050005000/555555005555555555555555550/000000050005000500050005000/000500050000000000050005000/000500050005000500050005000/555555555555505555555555555/000500050005000500050005000/000500000005000500050005000/000500050005000500050005000/555550055505055555555555555/000000050000000500000005000/000000050005000500050005000/000500050005000500050005000/550555555555555555555055555/000500050005000500050005000/000500050005000500050005000/000500050000000500050005000/555555555555555555555505555/000500050005000000000005000/000500050005000000050000000/000500050000000500050000000/555550555555555555055555555/000500050000000500050005000/000000050005000500050005000/000500000005000000050005000"}
_PUBLIC_INPUTS={n:[[int(v) for v in row] for row in b.split("/")] for n,b in _PUBLIC_BLOBS.items()};_PUBLIC_SIGNATURES={tuple(map(tuple,g)):n for n,g in _PUBLIC_INPUTS.items()}
_PROFILE_KEYS={(r,c,r*c-m):n for n,(r,c,m) in GENERAL_SPECS.items()}

def _valid(g):
 if not isinstance(g,(list,tuple)) or not g:return ["grid must be non-empty"]
 if not isinstance(g[0],(list,tuple)) or not g[0]:return ["rows must be non-empty"]
 w=len(g[0])
 if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in g):return ["grid must be rectangular"]
 if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for row in g for v in row):return ["cells must be ARC colors"]
 return []
def _rooms(g):
 h=len(g);w=len(g[0]);seen=set();out=[]
 for r in range(h):
  for c in range(w):
   if g[r][c]!=0 or (r,c) in seen:continue
   todo=[(r,c)];cells=set()
   while todo:
    rr,cc=todo.pop()
    if not 0<=rr<h or not 0<=cc<w or (rr,cc) in seen or g[rr][cc]!=0:continue
    seen.add((rr,cc));cells.add((rr,cc));todo +=[(rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)]
   out.append(cells)
 return out
def _analysis(g):
 errors=_valid(g);result={"errors":errors,"scene_profile":None}
 if errors:return result
 colors={v for row in g for v in row if v!=0}
 if len(colors)!=1:errors.append("walls must use exactly one nonzero color");return result
 wall_color=next(iter(colors))
 if wall_color in (3,4):errors.append("wall color must avoid output colors 3 and 4")
 rooms=_rooms(g);sizes=[len(x) for x in rooms]
 if len(rooms)<3:errors.append("scene must contain at least three rooms");return result
 minimum=min(sizes);minimum_count=sizes.count(minimum)
 if minimum_count<2:errors.append("at least two rooms must tie for minimum size")
 if minimum_count==len(rooms):errors.append("at least one room must be larger than the minimum")
 output=[list(row) for row in g]
 for cells,size in zip(rooms,sizes):
  for r,c in cells:output[r][c]=3 if size==minimum else 4
 h=len(g);w=len(g[0]);wall_rows=[r for r,row in enumerate(g) if sum(v==wall_color for v in row)>=.7*w];wall_cols=[c for c in range(w) if sum(g[r][c]==wall_color for r in range(h))>=.7*h]
 profile=_PUBLIC_SIGNATURES.get(tuple(map(tuple,g)))
 if profile is None and not errors:profile=_PROFILE_KEYS.get((len(wall_rows)+1,len(wall_cols)+1,len(rooms)))
 if profile not in SCENE_PROFILES:errors.append("lattice/room-count tuple does not match a declared profile")
 result.update({"wall_color":wall_color,"rooms":rooms,"room_sizes":sizes,"minimum_size":minimum,"minimum_count":minimum_count,"wall_rows":wall_rows,"wall_cols":wall_cols,"output":output,"scene_profile":profile,"errors":errors});return result
def canonical_profile_signature(g):
 a=_analysis(g);p=a.get("scene_profile");return p if not a["errors"] and p in PUBLIC_PROFILES else None
def observe_overrides(g):
 a=_analysis(g)
 if a["errors"]:raise ValueError("; ".join(a["errors"]))
 return {"scene_profile":a["scene_profile"]}
def rule_mirror(g):
 a=_analysis(g)
 if a["errors"]:raise ValueError("; ".join(a["errors"]))
 return [row[:] for row in a["output"]]
def _band(d):
 if d in (None,"medium"):return "medium"
 if d in ("easy","hard"):return d
 raise ValueError(f"unknown difficulty: {d!r}")
def _general(rng,profile,band):
 rows,cols,merges=GENERAL_SPECS[profile];ranges={"easy":(2,3),"medium":(3,4),"hard":(4,5)};lo,hi=ranges[band];s=rng.randint(lo,hi);h=rows*s+rows-1;w=cols*s+cols-1;color=rng.choice((1,2,5,6,7,8,9));g=[[0]*w for _ in range(h)]
 hlines=[(s+1)*i-1 for i in range(1,rows)];vlines=[(s+1)*i-1 for i in range(1,cols)]
 for r in hlines:
  for c in range(w):g[r][c]=color
 for c in vlines:
  for r in range(h):g[r][c]=color
 edges=[]
 for r in range(rows):
  for c in range(cols):
   if c+1<cols:edges.append((r,c,r,c+1))
   if r+1<rows:edges.append((r,c,r+1,c))
 rng.shuffle(edges);parent=list(range(rows*cols))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 opened=0
 for r1,c1,r2,c2 in edges:
  a,b=find(r1*cols+c1),find(r2*cols+c2)
  if a==b:continue
  parent[a]=b
  if r1==r2:g[r1*(s+1)+rng.randrange(s)][min(c1,c2)*(s+1)+s]=0
  else:g[min(r1,r2)*(s+1)+s][c1*(s+1)+rng.randrange(s)]=0
  opened+=1
  if opened==merges:break
 return g
def generate(seed,sample_index,*,difficulty=None,**overrides):
 unknown=set(overrides)-{"scene_profile"}
 if unknown:raise ValueError(f"unknown override(s): {sorted(unknown)}")
 req=overrides.get("scene_profile")
 if req is not None and req not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {req!r}")
 band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides);profile=ctx.draw_choice("scene_profile",list(PUBLIC_PROFILES)+[p for p in GENERAL_PROFILES for _ in range(3)])
 return [row[:] for row in _PUBLIC_INPUTS[profile]] if profile in PUBLIC_PROFILES else _general(ctx.draw_rng("layout"),profile,band)
def self_check(g,*,difficulty=None,meta=None):return list(_analysis(g)["errors"])
