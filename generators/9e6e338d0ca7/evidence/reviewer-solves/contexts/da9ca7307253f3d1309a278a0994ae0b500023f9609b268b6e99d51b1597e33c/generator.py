"""Semantic generator for ARC task 9e6e338d0ca7.

Gray 5 walls partition the canvas into chambers.  If and only if a chamber
contains exactly one seed cell colored 1, 2, 3, or 4, fill all of its zero
cells with that seed color.  Empty and multi-seed chambers stay unchanged.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx

GENERATOR_ID="9e6e338d0ca7"
TASK_ID=GENERATOR_ID
VERSION="4.0.0"
RULE_HASH="81c0076a1d08"
SUMMARY="Fill each gray-wall chamber containing exactly one colored seed; leave zero- and multi-seed chambers unchanged."
INVARIANTS=["color 5 forms a closed outer frame and complete interior chamber walls","chamber cells use background 0 and seed colors 1 through 4","at least one chamber has exactly one seed and is fillable","at least one chamber has zero or multiple seed cells and remains unchanged"]
PUBLIC_PROFILES=("public_1","public_2","public_3","public_4","public_5")
GENERAL_SPECS={
 "grid_2x2":(2,2,(0,1,1,2),False),"grid_2x3":(2,3,(0,1,1,1,2,2),False),"grid_3x2":(3,2,(0,0,1,1,1,2),False),"grid_3x3":(3,3,(0,0,1,1,1,1,2,2,3),False),
 "positive_heavy":(2,3,(0,1,1,1,1,2),False),"negative_heavy":(2,3,(0,0,0,1,2,3),False),"same_color_conflict":(2,2,(0,1,2,2),True),"multi_seed_variety":(3,2,(0,1,2,2,3,3),False),
}
GENERAL_PROFILES=tuple(GENERAL_SPECS);SCENE_PROFILES=PUBLIC_PROFILES+GENERAL_PROFILES;HELPFUL_TEXTURES=();DEGENERATE_TEXTURES=()
AXES={"scene_profile":{"type":"str","default":"weighted exact-public and chamber/seed-count lessons","valid":"public_1|public_2|public_3|public_4|public_5|grid_2x2|grid_2x3|grid_3x2|grid_3x3|positive_heavy|negative_heavy|same_color_conflict|multi_seed_variety"}}
_PUBLIC_SPECS={
 "public_1":(12,12,(0,5,11),(0,4,11),((3,3,1),(7,3,3),(7,5,2),(8,3,4))),
 "public_2":(14,13,(0,6,13),(0,5,12),((2,11,1),(5,1,2),(7,9,4),(10,6,3))),
 "public_3":(11,14,(0,4,10),(0,5,13),((1,2,3),(1,9,1),(3,3,4),(9,2,2))),
 "public_4":(14,12,(0,3,13),(0,4,11),((1,1,3),(1,2,4),(5,10,2),(6,3,1))),
 "public_5":(11,15,(0,5,10),(0,6,14),((1,9,2),(4,2,1),(6,9,4),(8,8,3))),
}
_DIRS=((-1,0),(1,0),(0,-1),(0,1))
def _public(spec):
 h,w,rows,cols,seeds=spec;g=[[0]*w for _ in range(h)]
 for r in rows:g[r]=[5]*w
 for c in cols:
  for r in range(h):g[r][c]=5
 for r,c,v in seeds:g[r][c]=v
 return g
_PUBLIC_INPUTS={n:_public(s) for n,s in _PUBLIC_SPECS.items()};_PUBLIC_SIGNATURES={tuple(map(tuple,g)):n for n,g in _PUBLIC_INPUTS.items()}

def _valid(g):
 if not isinstance(g,(list,tuple)) or not g:return ["grid must be non-empty"]
 if not isinstance(g[0],(list,tuple)) or not g[0]:return ["rows must be non-empty"]
 w=len(g[0])
 if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in g):return ["grid must be rectangular"]
 if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for row in g for v in row):return ["cells must be ARC colors"]
 return []
def _chambers(g):
 h=len(g);w=len(g[0]);seen=set();out=[]
 for r in range(h):
  for c in range(w):
   if g[r][c]==5 or (r,c) in seen:continue
   todo=[(r,c)];cells=set()
   while todo:
    rr,cc=todo.pop()
    if not 0<=rr<h or not 0<=cc<w or (rr,cc) in seen or g[rr][cc]==5:continue
    seen.add((rr,cc));cells.add((rr,cc));todo.extend((rr+dr,cc+dc) for dr,dc in _DIRS)
   out.append(cells)
 return out
def _profile(nr,nc,counts):
 key=tuple(sorted(counts))
 return next((p for p,(r,c,signature,_) in GENERAL_SPECS.items() if (r,c,signature)==(nr,nc,key)),None)
def _analysis(g):
 errors=_valid(g);result={"errors":errors,"scene_profile":None}
 if errors:return result
 h=len(g);w=len(g[0])
 if any(v not in (0,1,2,3,4,5) for row in g for v in row):errors.append("only background 0, seeds 1-4, and walls 5 are allowed")
 rows=[r for r,row in enumerate(g) if all(v==5 for v in row)];cols=[c for c in range(w) if all(g[r][c]==5 for r in range(h))]
 if not rows or rows[0]!=0 or rows[-1]!=h-1 or not cols or cols[0]!=0 or cols[-1]!=w-1:errors.append("color-5 walls must form a closed outer frame")
 expected_walls={(r,c) for r in rows for c in range(w)}|{(r,c) for c in cols for r in range(h)};actual_walls={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==5}
 if actual_walls!=expected_walls:errors.append("calibrated walls must be complete horizontal or vertical partition lines")
 if any(b-a<2 for a,b in zip(rows,rows[1:])) or any(b-a<2 for a,b in zip(cols,cols[1:])):errors.append("every chamber must contain cells")
 chambers=_chambers(g);seed_cells=[[(r,c,g[r][c]) for r,c in cells if 1<=g[r][c]<=4] for cells in chambers];counts=[len(x) for x in seed_cells]
 if not any(n==1 for n in counts):errors.append("at least one chamber must contain exactly one seed")
 if not any(n!=1 for n in counts):errors.append("at least one empty or multi-seed chamber is required")
 output=[list(row) for row in g]
 for cells,seeds in zip(chambers,seed_cells):
  if len(seeds)==1:
   color=seeds[0][2]
   for r,c in cells:
    if g[r][c]==0:output[r][c]=color
 profile=_PUBLIC_SIGNATURES.get(tuple(map(tuple,g))) or _profile(max(0,len(rows)-1),max(0,len(cols)-1),counts)
 if profile not in SCENE_PROFILES:errors.append("wall/seed-count composition does not match a declared profile")
 result.update({"wall_rows":rows,"wall_cols":cols,"chambers":chambers,"seed_cells":seed_cells,"seed_counts":counts,"qualifying_count":sum(n==1 for n in counts),"empty_count":sum(n==0 for n in counts),"multi_count":sum(n>1 for n in counts),"output":output,"scene_profile":profile,"errors":errors});return result
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
 nr,nc,signature,same=GENERAL_SPECS[profile];ranges={"easy":(2,4),"medium":(3,6),"hard":(5,8)};lo,hi=ranges[band];rh=[rng.randint(lo,hi) for _ in range(nr)];cw=[rng.randint(lo,hi) for _ in range(nc)];h=sum(rh)+nr+1;w=sum(cw)+nc+1;rows=[0];cols=[0]
 for x in rh:rows.append(rows[-1]+x+1)
 for x in cw:cols.append(cols[-1]+x+1)
 g=[[0]*w for _ in range(h)]
 for r in rows:g[r]=[5]*w
 for c in cols:
  for r in range(h):g[r][c]=5
 chambers=_chambers(g);counts=list(signature);rng.shuffle(counts);colors=[1,2,3,4];rng.shuffle(colors)
 for index,(cells,n) in enumerate(zip(chambers,counts)):
  edge_cells=[(r,c) for r,c in sorted(cells) if any(0<=r+dr<h and 0<=c+dc<w and g[r+dr][c+dc]==5 for dr,dc in _DIRS)]
  choices=rng.sample(edge_cells,n)
  for j,(r,c) in enumerate(choices):g[r][c]=colors[index%4] if same and n>1 else colors[(index+j)%4]
 return g
def generate(seed,sample_index,*,difficulty=None,**overrides):
 unknown=set(overrides)-{"scene_profile"}
 if unknown:raise ValueError(f"unknown override(s): {sorted(unknown)}")
 requested=overrides.get("scene_profile")
 if requested is not None and requested not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {requested!r}")
 band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides);profile=requested or ctx.draw_choice("scene_profile",list(PUBLIC_PROFILES)+[p for p in GENERAL_PROFILES for _ in range(4)])
 return [row[:] for row in _PUBLIC_INPUTS[profile]] if profile in PUBLIC_PROFILES else _general(ctx.draw_rng("layout"),profile,band)
def self_check(g,*,difficulty=None,meta=None):return list(_analysis(g)["errors"])
