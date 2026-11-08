"""Semantic generator for ARC task 7b088f161470.

Three colored floors carry small ladder glyphs.  Count the full three-cell
rungs for each floor, encode those counts as left-aligned output bars, place a
maroon separator in column three, and put gray beside the smallest positive
count (breaking ties toward the later floor).
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx

GENERATOR_ID = "7b088f161470"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "5cb6f6518f37"
SUMMARY="Count full ladder rungs per floor and encode three colored bars with maroon and one gray minimum marker."
INVARIANTS=["exactly three non-maroon uniform floors precede one maroon floor","each ladder alternates two side cells with contiguous three-cell rungs in its floor color","one gray input marker enables an output gray marker at the smallest positive rung count with later-index tie break","output is always three rows by five columns"]
PUBLIC_PROFILES=("public_train_1","public_train_2","public_train_3","public_test_1")
GENERAL_COUNTS={"counts_023":(0,2,3),"counts_123":(1,2,3),"counts_222":(2,2,2),"counts_213":(2,1,3),"counts_321":(3,2,1),"counts_132":(1,3,2),"counts_101":(1,0,1),"counts_000":(0,0,0)}
GENERAL_PROFILES=tuple(GENERAL_COUNTS);SCENE_PROFILES=PUBLIC_PROFILES+GENERAL_PROFILES;HELPFUL_TEXTURES=();DEGENERATE_TEXTURES=()
AXES={"scene_profile":{"type":"str","default":"weighted exact-public and generalized ladder-count lessons","valid":"public_train_1|public_train_2|public_train_3|public_test_1|counts_023|counts_123|counts_222|counts_213|counts_321|counts_132|counts_101|counts_000"}}
_PUBLIC_ROWS={
 "public_train_1":("000000000000000000000","444444444444444444444","000000000000000000000","000000000000000000000","000000000000000000000","888888888888888888888","000000000000808000000","000000000000888000000","000000000000808000000","000000000000888000000","000000000000808000000","333333333333333333333","000303000000000000000","000333000000000000000","000303000000000000000","000333000000000000000","000303000000000000000","000333000000000000000","000303000000050000000","999999999999999999999","000000000000000000000"),
 "public_train_2":("000000000000000000000","000000000000000000000","444444444444444444444","000000000404000000000","000000000444000000000","000000000404000000000","777777777777777777777","000000000707000000000","000000000777000000000","000000000707000000000","000000000777000000000","000000000707000000000","111111111111111111111","000000000101000000000","000000000111000000000","000000000101000000000","000000000111000000000","000000000101000000000","000000000111000000000","000000000101000050000","999999999999999999999"),
 "public_train_3":("000000000000000000000","888888888888888888888","000000000080800000000","000000000088800000000","000000000080800000000","000000000088800000000","000000000080800000000","666666666666666666666","000606000000000000000","000666000000000000000","000606000000000000000","000666000000000000000","000606000000000000000","000000000000000000000","444444444444444444444","000000000000000404000","000000000000000444000","000000000000000404000","000000000000000444000","000000000050000404000","999999999999999999999"),
 "public_test_1":("000000000000000000000","333333333333333333333","000000000003030000000","000000000003330000000","000000000003030000000","000000000003330000000","000000000003030000000","000000000000000000000","444444444444444444444","004040000000000000000","004440000000000000000","004040000000000000000","222222222222222222222","000000020200000000000","000000022200000000000","000000020200000000000","000000022200000000000","000000020200000000000","000000022200000000000","000005020200000000000","999999999999999999999")}
_PUBLIC_INPUTS={n:[[int(v) for v in z] for z in rows] for n,rows in _PUBLIC_ROWS.items()};_PUBLIC_SIGNATURES={tuple(map(tuple,g)):n for n,g in _PUBLIC_INPUTS.items()}
def _valid(g):
 if not isinstance(g,(list,tuple)) or not g:return ["grid must be non-empty"]
 if not isinstance(g[0],(list,tuple)) or not g[0]:return ["rows must be non-empty"]
 w=len(g[0])
 if any(not isinstance(z,(list,tuple)) or len(z)!=w for z in g):return ["grid must be rectangular"]
 if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for z in g for v in z):return ["cells must be ARC colors"]
 return []
def _analysis(g):
 errors=_valid(g);result={"errors":errors,"scene_profile":None}
 if errors:return result
 h,w=len(g),len(g[0]);floors=[]
 for r,z in enumerate(g):
  if z[0]!=0 and all(v==z[0] for v in z):floors.append((r,z[0]))
 if len(floors)!=4:errors.append(f"expected four uniform floors, found {len(floors)}");return result
 rows=tuple(r for r,c in floors);colors=tuple(c for r,c in floors)
 if colors[-1]!=9:errors.append("last floor must be maroon 9")
 if len(set(colors))!=4 or any(c in (0,5,9) for c in colors[:3]):errors.append("three floor colors must be distinct and exclude 0,5,9")
 counts=[]
 for i,(r,color) in enumerate(floors[:3]):
  next_r=floors[i+1][0];count=0
  for rr in range(r+1,next_r):
   cells=[c for c in range(w) if g[rr][c]==color]
   if len(cells)>=3 and cells[-1]-cells[0]==len(cells)-1:count+=1
  counts.append(count)
 gray=[(r,c) for r,z in enumerate(g) for c,v in enumerate(z) if v==5]
 if len(gray)!=1:errors.append(f"expected exactly one gray marker, found {len(gray)}")
 allowed={0,5,9,*colors[:3]}
 if any(v not in allowed for z in g for v in z):errors.append("unexpected color outside floor palette")
 positive=[(cnt,i) for i,cnt in enumerate(counts) if cnt>0];gray_idx=min(positive,key=lambda p:(p[0],-p[1]))[1] if positive else 0
 out=[[colors[r] if c<counts[r] else 9 if c==3 else 5 if c==4 and r==gray_idx else 0 for c in range(5)] for r in range(3)]
 profile=_PUBLIC_SIGNATURES.get(tuple(map(tuple,g)))
 if profile is None and not errors:profile=next((n for n,v in GENERAL_COUNTS.items() if v==tuple(counts)),None)
 if profile not in SCENE_PROFILES:errors.append("rung-count tuple does not match a declared profile")
 result.update({"floor_rows":rows,"floor_colors":colors,"rung_counts":tuple(counts),"gray":gray,"gray_floor_idx":gray_idx,"output":out,"scene_profile":profile,"errors":errors});return result
def canonical_profile_signature(g):
 i=_analysis(g);p=i.get("scene_profile");return p if not i["errors"] and p in PUBLIC_PROFILES else None
def observe_overrides(g):
 i=_analysis(g)
 if i["errors"]:raise ValueError("; ".join(i["errors"]))
 return {"scene_profile":i["scene_profile"]}
def rule_mirror(g):
 i=_analysis(g)
 if i["errors"]:raise ValueError("; ".join(i["errors"]))
 return [z[:] for z in i["output"]]
def _general(rng,profile,band):
 counts=GENERAL_COUNTS[profile];w=rng.randint(*{"easy":(12,16),"medium":(17,22),"hard":(21,26)}[band]);colors=rng.sample([1,2,3,4,6,7,8],3);top=rng.randint(0,2);g=[[0]*w for _ in range(top)];floor_rows=[]
 for color,count in zip(colors,counts):
  floor_rows.append(len(g));g.append([color]*w);gap=max(2,2*count+1)+rng.randint(0,2);block=[[0]*w for _ in range(gap)]
  if count:
   start_row=rng.randint(0,gap-(2*count+1));start_col=rng.randint(0,w-3)
   for k in range(2*count+1):
    rr=start_row+k;block[rr][start_col]=color;block[rr][start_col+2]=color
    if k%2==1:block[rr][start_col+1]=color
  g.extend(block)
 floor_rows.append(len(g));g.append([9]*w);g.extend([[0]*w for _ in range(rng.randint(0,2))])
 empties=[(r,c) for r,z in enumerate(g) for c,v in enumerate(z) if v==0];r,c=rng.choice(empties);g[r][c]=5;return g
def _band(d):
 if d in (None,"medium"):return "medium"
 if d in ("easy","hard"):return d
 raise ValueError(f"unknown difficulty: {d!r}")
def generate(seed,sample_index,*,difficulty=None,**overrides):
 if set(overrides)-{"scene_profile"}:raise ValueError(f"unknown override(s): {sorted(set(overrides)-{'scene_profile'})}")
 req=overrides.get("scene_profile")
 if req is not None and req not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {req!r}")
 band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides);weighted=list(PUBLIC_PROFILES)+[p for p in GENERAL_PROFILES for _ in range(3)];profile=ctx.draw_choice("scene_profile",weighted)
 if profile in PUBLIC_PROFILES:return [z[:] for z in _PUBLIC_INPUTS[profile]]
 return _general(ctx.draw_rng("layout"),profile,band)
def self_check(g,*,difficulty=None,meta=None):
 i=_analysis(g)
 if i["errors"]:return list(i["errors"])
 return []
