"""Semantic generator for ARC task 99601629ab88.

One color forms full horizontal and vertical divider lines.  Read the uniform
color in every resulting rectangular block, then reverse each extracted row.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx

GENERATOR_ID="99601629ab88"
TASK_ID=GENERATOR_ID
VERSION="4.0.0"
RULE_HASH="c856d06245d4"
SUMMARY="Extract the color matrix from divider-bounded blocks and flip that matrix left-to-right."
INVARIANTS=["one nonzero color forms every full divider row and column","divider lines are interior, single-cell, and nonadjacent","every divider-bounded block is nonempty and uniformly colored","the extracted matrix is visibly asymmetric left-to-right"]
PUBLIC_PROFILES=("public_1","public_2","public_3","public_4")
GENERAL_PROFILES=tuple(f"lattice_{r}x{c}" for r in range(2,5) for c in range(2,5))
SCENE_PROFILES=PUBLIC_PROFILES+GENERAL_PROFILES
HELPFUL_TEXTURES=();DEGENERATE_TEXTURES=()
AXES={"scene_profile":{"type":"str","default":"weighted exact-public and 2x2-through-4x4 lattices","valid":"public_1|public_2|public_3|public_4|lattice_2x2|lattice_2x3|lattice_2x4|lattice_3x2|lattice_3x3|lattice_3x4|lattice_4x2|lattice_4x3|lattice_4x4"}}

def _lattice(matrix,row_sizes,col_sizes,divider):
 h=sum(row_sizes)+len(row_sizes)-1;w=sum(col_sizes)+len(col_sizes)-1;g=[[divider]*w for _ in range(h)];r0=0
 for i,rh in enumerate(row_sizes):
  c0=0
  for j,cw in enumerate(col_sizes):
   for r in range(r0,r0+rh):g[r][c0:c0+cw]=[matrix[i][j]]*cw
   c0+=cw+1
  r0+=rh+1
 return g

_PUBLIC_SPECS={
 "public_1":([[0,2,0,0],[2,1,0,0],[0,0,1,0],[0,0,0,3]],[4]*4,[4]*4,8),
 "public_2":([[3,0,0,0],[0,3,0,0],[0,0,3,0],[3,3,3,0]],[4]*4,[4]*4,2),
 "public_3":([[0,8,0],[8,8,0],[0,0,4]],[3]*3,[3]*3,2),
 "public_4":([[1,3,1,1],[0,3,0,0],[2,3,0,2],[0,3,0,0]],[5]*4,[5]*4,8),
}
_PUBLIC_INPUTS={name:_lattice(*spec) for name,spec in _PUBLIC_SPECS.items()}
_PUBLIC_SIGNATURES={tuple(map(tuple,g)):name for name,g in _PUBLIC_INPUTS.items()}

def _valid(g):
 if not isinstance(g,(list,tuple)) or not g:return ["grid must be non-empty"]
 if not isinstance(g[0],(list,tuple)) or not g[0]:return ["rows must be non-empty"]
 w=len(g[0])
 if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in g):return ["grid must be rectangular"]
 if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for row in g for v in row):return ["cells must be ARC colors"]
 return []
def _ranges(n,lines):
 bounds=(-1,)+tuple(lines)+(n,);return [(bounds[i]+1,bounds[i+1]) for i in range(len(bounds)-1)]
def _analysis(g):
 errors=_valid(g);result={"errors":errors,"scene_profile":None}
 if errors:return result
 h=len(g);w=len(g[0]);candidates=[]
 for color in {v for row in g for v in row if v!=0}:
  rows=[r for r,row in enumerate(g) if all(v==color for v in row)];cols=[c for c in range(w) if all(g[r][c]==color for r in range(h))]
  if rows and cols:candidates.append((color,rows,cols))
 if len(candidates)!=1:errors.append("exactly one nonzero color must form full rows and columns");return result
 divider,rows,cols=candidates[0]
 if rows[0]==0 or rows[-1]==h-1 or cols[0]==0 or cols[-1]==w-1:errors.append("divider lines must be interior")
 if any(b-a<2 for a,b in zip(rows,rows[1:])) or any(b-a<2 for a,b in zip(cols,cols[1:])):errors.append("divider lines must be nonadjacent")
 rr=_ranges(h,rows);cc=_ranges(w,cols);matrix=[]
 for r0,r1 in rr:
  line=[]
  for c0,c1 in cc:
   value=g[r0][c0]
   if value==divider:errors.append("block values must differ from divider color")
   if any(g[r][c]!=value for r in range(r0,r1) for c in range(c0,c1)):errors.append("every block must be uniformly colored")
   line.append(0 if value in (0,divider) else value)
  matrix.append(line)
 if len({v for row in matrix for v in row})<2:errors.append("extracted matrix must use at least two values")
 if all(row==list(reversed(row)) for row in matrix):errors.append("left-right flip must be visible")
 output=[list(reversed(row)) for row in matrix];profile=_PUBLIC_SIGNATURES.get(tuple(map(tuple,g))) or f"lattice_{len(rr)}x{len(cc)}"
 if profile not in SCENE_PROFILES:errors.append("lattice shape does not match a declared profile")
 result.update({"divider_color":divider,"divider_rows":rows,"divider_cols":cols,"row_ranges":rr,"col_ranges":cc,"matrix":matrix,"output":output,"scene_profile":profile,"errors":errors});return result
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
 nr,nc=map(int,profile.removeprefix("lattice_").split("x"));ranges={"easy":(2,4),"medium":(3,5),"hard":(4,6)};lo,hi=ranges[band]
 row_sizes=[rng.randint(lo,hi) for _ in range(nr)];col_sizes=[rng.randint(lo,hi) for _ in range(nc)];colors=rng.sample(range(1,10),4);divider=colors[0];values=[0]+colors[1:];matrix=[[rng.choice(values) for _ in range(nc)] for _ in range(nr)]
 matrix[0][0]=values[1];matrix[0][-1]=values[2]
 if len({v for row in matrix for v in row})<3:matrix[-1][0]=values[3]
 return _lattice(matrix,row_sizes,col_sizes,divider)
def generate(seed,sample_index,*,difficulty=None,**overrides):
 unknown=set(overrides)-{"scene_profile"}
 if unknown:raise ValueError(f"unknown override(s): {sorted(unknown)}")
 requested=overrides.get("scene_profile")
 if requested is not None and requested not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {requested!r}")
 band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides);profile=requested or ctx.draw_choice("scene_profile",list(PUBLIC_PROFILES)+[p for p in GENERAL_PROFILES for _ in range(4)])
 return [row[:] for row in _PUBLIC_INPUTS[profile]] if profile in PUBLIC_PROFILES else _general(ctx.draw_rng("layout"),profile,band)
def self_check(g,*,difficulty=None,meta=None):return list(_analysis(g)["errors"])
