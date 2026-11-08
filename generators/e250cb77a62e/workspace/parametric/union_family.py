"""Exact disjoint stamping rules on matched connected-stamp scenes."""
from pathlib import Path
import importlib.util, hashlib, sys, random
from copy import deepcopy
HERE=Path(__file__).resolve().parent
TASK_ID="e250cb77a62e"
PARAMETER="stamp_policy"
VALUES=("all_stamps","largest_joined","quarter_turn")
def load(name):
 p=HERE/(name+".py"); n="_union_"+hashlib.sha256(str(p).encode()).hexdigest();s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
old=load("native"); incoming=load("rotated_family")
def setting(s):
 if type(s) is dict and set(s)=={"pattern_transform"} and s["pattern_transform"] in incoming.SETTINGS:return {"as_drawn":"all_stamps","quarter_turn":"quarter_turn"}[s["pattern_transform"]]
 if type(s) is not dict or set(s)!={PARAMETER} or s[PARAMETER] not in VALUES:raise ValueError("invalid disjoint stamp policy")
 return s[PARAMETER]
def program(s):
 v=setting(s)
 return incoming.program({"pattern_transform":"quarter_turn"}) if v=="quarter_turn" else old.program({PARAMETER:v})
def predict(g,v):
 if v in old.hypotheses():return old.predict(g,v)
 data=old.scene(g);r0,c0,r1,c1=data["frame"]
 info={"seeds":tuple(sorted(data["anchors"])),"pattern":tuple(sorted(data["pattern"])),"interior_height":r1-r0-1,"interior_width":c1-c0-1}
 seeds,offsets,clip=incoming._policy(info,v)
 out=deepcopy(g)
 for r,c in seeds:
  for dr,dc in offsets:
   if 0<=r+dr<len(g) and 0<=c+dc<len(g[0]):out[r+dr][c+dc]=8
   elif not clip:raise ValueError("rival escaped canvas")
 return out
RIVALS=tuple(dict.fromkeys(tuple(old.hypotheses())+incoming.RIVALS))
def draw(seed,slot):
 # Both teaching scenes and every query independently vary connected-region
 # sizes. Square footprints make every exact transform total on the old grammar.
 rng=random.Random(f"{TASK_ID}:union:{seed}")
 demos=[0,1,8,9,0,1];queries=[0,1,8,9];rng.shuffle(queries)
 profile=(demos+queries)[slot]
 return old._draw(seed*101+slot,profile)
def generate(seed,settings,demos=3,queries=4):
 v=setting(settings)
 if type(seed) is not int or seed<0:raise ValueError("invalid seed")
 if type(demos) is not int or not 2<=demos<=6:raise ValueError("invalid demos")
 if type(queries) is not int or not 1<=queries<=4:raise ValueError("invalid queries")
 def pair(i):
  g=draw(seed,i);return {"input":g,"output":predict(g,v)}
 return {"train":[pair(i) for i in range(demos)],"test":[pair(i+6) for i in range(queries)],"program_solution":program(settings)}
def findings(e,v):
 return [r for r in RIVALS if r!=v and all(predict(p["input"],r)==p["output"] for p in e["train"]) and any(predict(p["input"],r)!=p["output"] for p in e["test"])]
public_turn=old.public_turn
