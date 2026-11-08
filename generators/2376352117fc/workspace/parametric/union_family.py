"""Three exact translation rules; diverse post-clipping fragments."""
from pathlib import Path
import importlib.util, hashlib, sys, random
from copy import deepcopy
HERE=Path(__file__).resolve().parent
TASK_ID="2376352117fc"
PARAMETER="vector_direction"
VALUES=("blue_to_red","red_to_blue","largest_visible_fragment")
def load(name):
 p=HERE/(name+".py"); n="_union_"+hashlib.sha256(str(p).encode()).hexdigest();s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

old=load("prototype");incoming=load("fragment_family")
def setting(s):
 if type(s) is dict and set(s)=={"finish"} and s["finish"] in incoming.SETTINGS:return {"translate_only":"blue_to_red","largest_visible_fragment":"largest_visible_fragment"}[s["finish"]]
 if type(s) is not dict or set(s)!={PARAMETER} or s[PARAMETER] not in VALUES:raise ValueError("invalid disjoint translation rule")
 return s[PARAMETER]
def program(s):
 v=setting(s)
 return incoming.program({"finish":v}) if v==VALUES[-1] else old.program({PARAMETER:v})
def vector_rival(g,rule,policy):
 info=old.analyze(g,"red_to_blue" if rule=="red_to_blue" else "blue_to_red")
 dr,dc=info["applied_vector"]
 if policy=="drop_row":dr=0
 elif policy=="drop_col":dc=0
 elif policy=="unit_row":dr=(dr>0)-(dr<0)
 elif policy=="unit_col":dc=(dc>0)-(dc<0)
 elif policy=="flip_row":dr=-dr
 elif policy=="flip_col":dc=-dc
 elif policy=="abs_row":dr=abs(dr)
 elif policy=="abs_col":dc=abs(dc)
 else:raise ValueError(policy)
 out=[[0]*len(g[0]) for _ in g]
 for r,c in info["source_cells"]:
  if 0<=r+dr<len(g) and 0<=c+dc<len(g[0]):out[r+dr][c+dc]=8
 if rule=="largest_visible_fragment":
  parts=incoming._components_from_cells(incoming._positions(out,8))
  if parts:
   chosen=sorted(parts,key=lambda s:(-len(s),min(s)))[0]
   for r,c in chosen:out[r][c]=4
 return out
def predict(g,v):
 if ":" in v:
  rule,policy=v.split(":");return vector_rival(g,rule,policy)
 if v in old.CANDIDATE_NAMES:return old.solve(g,v)
 if v=="largest_visible_fragment":return incoming.solve(g,{"finish":v})
 if v=="select_before_clipping":return incoming.wrong_order_solve(g)
 if v.startswith("fragment_"):return incoming._fragment_rival(g,v.removeprefix("fragment_"))
 if v=="reverse_fragment":return incoming._reverse_vector(g,{"finish":"largest_visible_fragment"})
 raise ValueError(v)
RIVALS=old.CANDIDATE_NAMES+("largest_visible_fragment","select_before_clipping","fragment_first","fragment_last","fragment_smallest","reverse_fragment")
RIVALS+=tuple(f"{v}:{p}" for v in VALUES for p in ("drop_row","drop_col","unit_row","unit_col","flip_row","flip_col","abs_row","abs_col"))
def draw(seed,slot):
 rng=random.Random(f"{TASK_ID}:union:{seed}:{slot}")
 size=30 if slot==9 else 20+(seed+slot*3)%11
 offset=2+seed%3;long=size-offset-2;short=rng.randint(3,long-2)
 a,b=(short,long) if slot<2 else ((long,short) if slot%2==0 else (short,long))
 side_shift=1+(seed+slot)%3 if slot<2 or slot%2 else 0
 span=rng.randint(6,size-2*side_shift-4);start=rng.randint(side_shift+2,size-span-side_shift-2)
 g=[[0]*size for _ in range(size)]
 source={(offset,c) for c in range(start,start+span)}
 source|={(r,start) for r in range(offset+1,offset+a+1)}
 source|={(r,start+span-1) for r in range(offset+1,offset+b+1)}
 for r,c in source:g[r][c]=3
 g[size-1][0]=1;g[size-offset-2][side_shift]=2
 # Opposite diagonal vectors teach both signed components. The first
 # scene selects the later fragment; the opposite scene selects the first.
 # Queries mix axial and diagonal shifts with an independent shuffled order.
 rotations=seed%2+2*slot if slot<2 else rng.randrange(4)
 for _ in range(rotations):g=[list(row) for row in zip(*g[::-1])]
 return g
def generate(seed,settings,demos=3,queries=4):
 v=setting(settings)
 if type(seed) is not int or seed<0:raise ValueError("invalid seed")
 if type(demos) is not int or not 2<=demos<=6:raise ValueError("invalid demos")
 if type(queries) is not int or not 1<=queries<=4:raise ValueError("invalid queries")
 order=list(range(6,10));random.Random(f"query:{seed}").shuffle(order)
 def pair(i):
  g=draw(seed,i);return {"input":g,"output":predict(g,v)}
 return {"train":[pair(i) for i in range(demos)],"test":[pair(i) for i in order[:queries]],"program_solution":program(settings)}
def findings(e,v):
 return [r for r in RIVALS if r!=v and all(predict(p["input"],r)==p["output"] for p in e["train"]) and any(predict(p["input"],r)!=p["output"] for p in e["test"])]
