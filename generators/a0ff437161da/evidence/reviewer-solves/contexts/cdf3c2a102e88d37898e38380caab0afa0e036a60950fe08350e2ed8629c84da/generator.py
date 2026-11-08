"""Semantic generator for ARC task a0ff437161da.

On an 8 background, find the first non-8 cell in row-major order and fill the
axis-aligned rectangle from it to the nearest corner with its color.  Manhattan
distance ties follow corner order UL, UR, LL, LR.
"""
from __future__ import annotations
from puzzle_generators.base import gen_ctx

GENERATOR_ID="a0ff437161da"
TASK_ID=GENERATOR_ID
VERSION="4.0.0"
RULE_HASH="c70fab479c5e"
SUMMARY="Fill the rectangle from the lone colored cell to its nearest corner, resolving ties in UL/UR/LL/LR order."
INVARIANTS=["background is literal color 8","calibrated scenes contain exactly one non-8 marker","the marker is not itself at a corner","the output rectangle includes both the marker and the selected nearest corner"]
PUBLIC_PROFILES=("public_1","public_2","public_3","public_4","public_5")
GENERAL_PROFILES=("nearest_ul","nearest_ur","nearest_ll","nearest_lr","top_tie","bottom_tie","left_tie","right_tie","four_way_tie")
SCENE_PROFILES=PUBLIC_PROFILES+GENERAL_PROFILES;HELPFUL_TEXTURES=();DEGENERATE_TEXTURES=()
AXES={"scene_profile":{"type":"str","default":"weighted exact-public, unique-corner, and tie lessons","valid":"public_1|public_2|public_3|public_4|public_5|nearest_ul|nearest_ur|nearest_ll|nearest_lr|top_tie|bottom_tie|left_tie|right_tie|four_way_tie"}}
_PUBLIC_SPECS={"public_1":(6,8,3,2,4),"public_2":(6,6,2,4,9),"public_3":(10,8,4,2,6),"public_4":(4,4,0,2,6),"public_5":(10,10,7,8,4)}
def _single(spec):
 h,w,r,c,color=spec;g=[[8]*w for _ in range(h)];g[r][c]=color;return g
_PUBLIC_INPUTS={n:_single(s) for n,s in _PUBLIC_SPECS.items()};_PUBLIC_SIGNATURES={tuple(map(tuple,g)):n for n,g in _PUBLIC_INPUTS.items()}
_CORNERS=("ul","ur","ll","lr")
def _valid(g):
 if not isinstance(g,(list,tuple)) or not g:return ["grid must be non-empty"]
 if not isinstance(g[0],(list,tuple)) or not g[0]:return ["rows must be non-empty"]
 w=len(g[0])
 if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in g):return ["grid must be rectangular"]
 if any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=9 for row in g for v in row):return ["cells must be ARC colors"]
 return []
def _solve(g):
 h=len(g);w=len(g[0]);markers=[(r,c,g[r][c]) for r,row in enumerate(g) for c in range(w) if g[r][c]!=8]
 if not markers:raise ValueError("grid has no non-8 marker")
 r,c,color=markers[0];corners=((0,0),(0,w-1),(h-1,0),(h-1,w-1));dist=[abs(r-rr)+abs(c-cc) for rr,cc in corners];index=dist.index(min(dist));rr,cc=corners[index];out=[list(row) for row in g]
 for y in range(min(r,rr),max(r,rr)+1):
  for x in range(min(c,cc),max(c,cc)+1):out[y][x]=color
 return out,markers,(r,c),_CORNERS[index],tuple(dist)
def _relation(r,c,h,w):
 d=(r+c,r+w-1-c,h-1-r+c,h-1-r+w-1-c);minimum=min(d);nearest=tuple(i for i,x in enumerate(d) if x==minimum)
 if nearest==(0,):return "nearest_ul"
 if nearest==(1,):return "nearest_ur"
 if nearest==(2,):return "nearest_ll"
 if nearest==(3,):return "nearest_lr"
 if nearest==(0,1):return "top_tie"
 if nearest==(2,3):return "bottom_tie"
 if nearest==(0,2):return "left_tie"
 if nearest==(1,3):return "right_tie"
 if nearest==(0,1,2,3):return "four_way_tie"
 return None
def _analysis(g):
 errors=_valid(g);result={"errors":errors,"scene_profile":None}
 if errors:return result
 h=len(g);w=len(g[0]);markers=[(r,c,g[r][c]) for r,row in enumerate(g) for c in range(w) if g[r][c]!=8]
 if len(markers)!=1:errors.append("calibrated scene must contain exactly one non-8 marker")
 if not markers:return result
 r,c,color=markers[0]
 if color==8:errors.append("marker color must differ from background 8")
 if (r,c) in ((0,0),(0,w-1),(h-1,0),(h-1,w-1)):errors.append("marker must not lie at a corner")
 output,_,marker,corner,distances=_solve(g);profile=_PUBLIC_SIGNATURES.get(tuple(map(tuple,g))) or _relation(r,c,h,w)
 if profile not in SCENE_PROFILES:errors.append("marker/corner relation does not match a declared profile")
 result.update({"marker":marker,"marker_color":color,"nearest_corner":corner,"corner_distances":distances,"rectangle_area":sum(v==color for row in output for v in row),"output":output,"scene_profile":profile,"errors":errors});return result
def canonical_profile_signature(g):
 a=_analysis(g);p=a.get("scene_profile");return p if not a["errors"] and p in PUBLIC_PROFILES else None
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
def _odd(rng,lo,hi):
 choices=[x for x in range(lo,hi+1) if x%2];return rng.choice(choices)
def _position(rng,profile,h,w):
 hm=(h-1)//2;wm=(w-1)//2
 if profile=="nearest_ul":return rng.randint(0,hm),rng.randint(0,wm) if (hm,wm)!=(0,0) else (0,1)
 if profile=="nearest_ur":return rng.randint(0,hm),rng.randint(wm+1,w-1)
 if profile=="nearest_ll":return rng.randint(hm+1,h-1),rng.randint(0,wm)
 if profile=="nearest_lr":return rng.randint(hm+1,h-1),rng.randint(wm+1,w-1)
 if profile=="top_tie":return rng.randint(0,hm-1),wm
 if profile=="bottom_tie":return rng.randint(hm+1,h-1),wm
 if profile=="left_tie":return hm,rng.randint(0,wm-1)
 if profile=="right_tie":return hm,rng.randint(wm+1,w-1)
 return hm,wm
def _general(rng,profile,band):
 ranges={"easy":(4,12),"medium":(8,18),"hard":(16,29)};lo,hi=ranges[band]
 if profile in ("top_tie","bottom_tie","four_way_tie"):w=_odd(rng,max(5,lo),hi)
 else:w=rng.randint(lo,hi)
 if profile in ("left_tie","right_tie","four_way_tie"):h=_odd(rng,max(5,lo),hi)
 else:h=rng.randint(lo,hi)
 for _ in range(100):
  r,c=_position(rng,profile,h,w)
  if (r,c) not in ((0,0),(0,w-1),(h-1,0),(h-1,w-1)) and _relation(r,c,h,w)==profile:break
 else:raise RuntimeError(f"could not choose position for {profile!r}")
 color=rng.choice((0,1,2,3,4,5,6,7,9));return _single((h,w,r,c,color))
def generate(seed,sample_index,*,difficulty=None,**overrides):
 unknown=set(overrides)-{"scene_profile"}
 if unknown:raise ValueError(f"unknown override(s): {sorted(unknown)}")
 requested=overrides.get("scene_profile")
 if requested is not None and requested not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {requested!r}")
 band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides);profile=requested or ctx.draw_choice("scene_profile",list(PUBLIC_PROFILES)+[p for p in GENERAL_PROFILES for _ in range(4)])
 return [row[:] for row in _PUBLIC_INPUTS[profile]] if profile in PUBLIC_PROFILES else _general(ctx.draw_rng("layout"),profile,band)
def self_check(g,*,difficulty=None,meta=None):return list(_analysis(g)["errors"])
