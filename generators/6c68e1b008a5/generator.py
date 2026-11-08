"""Semantic generator for ARC task 6c68e1b008a5.

Learn an onion-depth palette from a plain/colored reference pair, apply it to
a different plain query shape, then select the matching colored candidate.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx

GENERATOR_ID = "6c68e1b008a5"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "392b20c1c503"
EXPECTED_OUTPUT_CODOMAIN = 3
SUMMARY="Infer an onion-depth palette from panels 1-2, recolor panel 3, and mark the matching candidate."
INVARIANTS=["six equal panels are separated by full maroon columns","reference panels share support while the plain query uses a different shape","the colored reference is uniform and distinct by onion depth","exactly one of three candidates equals the recolored query"]
PUBLIC_PROFILES=("public_train_1","public_train_2","public_test_1")
GENERAL_PROFILES=("match_0_single","match_1_single","match_2_single","match_0_compound","match_1_compound","match_2_compound")
SCENE_PROFILES=GENERAL_PROFILES;HELPFUL_TEXTURES=();DEGENERATE_TEXTURES=()
AXES={"scene_profile":{"type":"str","default":"weighted compressed analogy lessons","valid":"match_0_single|match_1_single|match_2_single|match_0_compound|match_1_compound|match_2_compound"}}
_PUBLIC_ROWS={
 "public_train_1":("00000009000000090000000900000009000000090000000","01111109022222090001000900020009000400090222220","01111109023332090011100900232009004340090233320","01111109023432090111110902343209043234090234320","01111109023332090011100900232009004340090233320","01111109022222090001000900020009000400090222220","00000009000000090000000900000009000000090000000"),
 "public_train_2":("00000000090000000009000000000900000000090000000009000000000","00011100090005550009000000000900000000090000000009000000000","00011100090005650009000000000900000000090000000009000050000","01111111090556765509000111000900088800090005550009000565000","01111111090567876509000111000900087800090005650009005676500","01111111090556765509000111000900088800090005550009000565000","00011100090005650009000000000900000000090000000009000050000","00011100090005550009000000000900000000090000000009000000000","00000000090000000009000000000900000000090000000009000000000"),
 "public_test_1":("00000000090000000009000000000900000000090000000009000000000","00001000090000200009000000000900000000090000000009000000000","00011100090002420009001111100900222220090066666009002222200","00111110090024642009001111100900244420090064446009002444200","01111111090246864209001111100900246420090064246009002464200","00111110090024642009000111000900024200090006460009002444200","00011100090002420009000111000900022200090006660009002222200","00001000090000200009000000000900000000090000000009000000000","00000000090000000009000000000900000000090000000009000000000")}
_PUBLIC_INPUTS={n:[[int(v) for v in z] for z in rows] for n,rows in _PUBLIC_ROWS.items()};_PUBLIC_SIGNATURES={tuple(map(tuple,g)):n for n,g in _PUBLIC_INPUTS.items()}

def _validate(g):
 if not isinstance(g,(list,tuple)) or not g:return ["grid must be non-empty"]
 if not isinstance(g[0],(list,tuple)) or not g[0]:return ["rows must be non-empty"]
 w=len(g[0])
 if any(not isinstance(z,(list,tuple)) or len(z)!=w for z in g):return ["grid must be rectangular"]
 if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for z in g for v in z):return ["cells must be ARC colors"]
 return []
def _split(g):
 h=len(g);w=len(g[0]);seps=[c for c in range(w) if all(g[r][c]==9 for r in range(h))];out=[];s=0
 for c in seps+[w]:
  if c>s:out.append([z[s:c] for z in g])
  s=c+1
 return out,seps
def _support(p):return {(r,c) for r,z in enumerate(p) for c,v in enumerate(z) if v not in (0,9)}
def _depths(cells):
 cur=set(cells);out={};d=1
 while cur:
  edge={p for p in cur if any((p[0]+dr,p[1]+dc) not in cur for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)))}
  for p in edge:out[p]=d
  cur-=edge;d+=1
 return out
def _recolor(panel,palette):
 out=[[0]*len(panel[0]) for _ in panel]
 for cell,d in _depths(_support(panel)).items():out[cell[0]][cell[1]]=palette[min(d-1,len(palette)-1)]
 return out
def _analysis(g):
 errors=_validate(g);result={"errors":errors,"scene_profile":None}
 if errors:return result
 panels,seps=_split(g)
 if len(panels)!=6:errors.append(f"expected six panels, found {len(panels)}")
 if len(seps)!=5:errors.append(f"expected five separators, found {len(seps)}")
 if errors:return result
 h=len(panels[0]);w=len(panels[0][0])
 if any(len(p)!=h or any(len(z)!=w for z in p) for p in panels):errors.append("panels must have equal dimensions");return result
 a,b,c=panels[:3];sa,sb,sc=_support(a),_support(b),_support(c)
 if not sa or sa!=sb:errors.append("plain and colored reference supports must match")
 if not sc or sc==sa:errors.append("query support must be nonempty and differ from reference")
 if len({a[r][x] for r,x in sa})!=1 or len({c[r][x] for r,x in sc})!=1:errors.append("reference and query must be plain")
 depths=_depths(sa);by={}
 for cell,d in depths.items():by.setdefault(d,set()).add(b[cell[0]][cell[1]])
 if any(len(v)!=1 or next(iter(v)) in (0,9) for v in by.values()):errors.append("colored reference must be uniform per depth")
 palette=[next(iter(by[d])) for d in sorted(by) if len(by[d])==1]
 if len(palette)!=len(set(palette)):errors.append("depth colors must be distinct")
 expected=_recolor(c,palette) if palette and sc else [[0]*w for _ in range(h)]
 matches=tuple(i for i,p in enumerate(panels[3:]) if p==expected)
 if len(matches)!=1:errors.append(f"expected one matching candidate, found {len(matches)}")
 profile=_PUBLIC_SIGNATURES.get(tuple(map(tuple,g)))
 if profile is None and not errors:
  remaining=set(sc);components=0
  while remaining:
   components+=1;stack=[remaining.pop()]
   while stack:
    r,cx=stack.pop()
    for q in ((r-1,cx),(r+1,cx),(r,cx-1),(r,cx+1)):
     if q in remaining:remaining.remove(q);stack.append(q)
  profile=f"match_{matches[0]}_{'compound' if components>1 else 'single'}"
 if profile not in PUBLIC_PROFILES+GENERAL_PROFILES:errors.append("scene does not match a declared profile")
 result.update({"panels":panels,"reference_support":sa,"query_support":sc,"palette":palette,"max_depth":max(depths.values()) if depths else 0,"expected":expected,"matches":matches,"output":[[8 if i in matches else 0 for i in range(3)]],"scene_profile":profile,"errors":errors});return result
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
def _paint(panel,cells,color,r0,c0):
 for r,c in cells:panel[r0+r][c0+c]=color if isinstance(color,int) else color(r,c)
def _assemble(panels):
 h=len(panels[0]);out=[]
 for r in range(h):
  z=[]
  for i,p in enumerate(panels):
   z.extend(p[r])
   if i<5:z.append(9)
  out.append(z)
 return out
def _general(rng,profile,band):
 match=int(profile[6]);compound=profile.endswith("compound");bounds=({"easy":(17,19),"medium":(20,22),"hard":(23,25)} if compound else {"easy":(9,11),"medium":(12,14),"hard":(15,17)});h=rng.randint(*bounds[band]);w=4;blank=lambda:[[0]*w for _ in range(h)]
 ref={(r,c) for r in range(rng.randint(5,7)) for c in range(4)}
 rr=rng.randint(0,h-max(r for r,c in ref)-1);rc=rng.randint(0,w-max(c for r,c in ref)-1);ref={(r+rr,c+rc) for r,c in ref}
 if compound:
  query={(base+r,c) for base in (0,4,8,12) for r in range(3) for c in range(3)}
 else:
  query={(r,c) for r in range(9) for c in range(3)};qr=rng.randint(0,h-9);qc=rng.randint(0,1);query={(r+qr,c+qc) for r,c in query}
 if query==ref:query={(r,c+1 if c<3 else c) for r,c in query}
 depths=_depths(ref);palette=rng.sample([1,2,3,4,5,6,7,8],max(depths.values()));plain_a=rng.choice([1,2,3,4,5,6,7,8]);plain_c=rng.choice([1,2,3,4,5,6,7,8])
 a=blank();b=blank();c=blank();_paint(a,ref,plain_a,0,0);_paint(b,ref,lambda r,x:palette[depths[(r,x)]-1],0,0);_paint(c,query,plain_c,0,0);expected=_recolor(c,palette)
 cands=[]
 for i in range(3):
  if i==match:cands.append([z[:] for z in expected]);continue
  d=[z[:] for z in expected];cells=sorted(query);cell=cells[(i*7+match)%len(cells)];d[cell[0]][cell[1]]=palette[(palette.index(d[cell[0]][cell[1]])+1)%len(palette)];cands.append(d)
 return _assemble([a,b,c]+cands)
def _band(d):
 if d in (None,"medium"):return "medium"
 if d in ("easy","hard"):return d
 raise ValueError(f"unknown difficulty: {d!r}")
def generate(seed,sample_index,*,difficulty=None,**overrides):
 if set(overrides)-{"scene_profile"}:raise ValueError(f"unknown override(s): {sorted(set(overrides)-{'scene_profile'})}")
 req=overrides.get("scene_profile")
 if req is not None and req not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {req!r}")
 band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides);profile=ctx.draw_choice("scene_profile",list(GENERAL_PROFILES))
 return _general(ctx.draw_rng("layout"),profile,band)
def self_check(g,*,difficulty=None,meta=None):
 i=_analysis(g)
 if i["errors"]:return list(i["errors"])
 return []
