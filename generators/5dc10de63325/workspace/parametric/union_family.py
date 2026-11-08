"""Five disjoint exact cyan-count rules with independent marker colors."""
from pathlib import Path
import importlib.util, hashlib, sys, random
from copy import deepcopy
HERE=Path(__file__).resolve().parent
TASK_ID="5dc10de63325"
PARAMETER="fill_order"
MIN_DEMOS=4
VALUES=("bottom_row_first","right_column_first","top_row_first","largest_component_count","bucket_color_relay")
NOTES="Five exact disjoint rules preserve the prior four-program family and four-demo minimum. Matched inputs vary total counts, component sizes, marker colors and order across seeds; queries are independently shuffled. Sparse 30x30 scenes span the canvas under the relay's lawful 4..19-cyan and exactly-four-marker grammar. Original samplers remain task-local."
def load(name):
 p=HERE/(name+".py"); n="_union_"+hashlib.sha256(str(p).encode()).hexdigest();s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

old=load("retained_family");incoming=load("relay_family")
def setting(s):
 if type(s) is dict and set(s)=={"mode"} and s["mode"] in incoming.MODES:return {"canonical":"bottom_row_first","bucket_color_relay":"bucket_color_relay"}[s["mode"]]
 if type(s) is not dict or set(s)!={PARAMETER} or s[PARAMETER] not in VALUES:raise ValueError("invalid disjoint count rule")
 return s[PARAMETER]
def program(s):
 v=setting(s)
 return incoming.program_for(v) if v==VALUES[-1] else old.program({PARAMETER:v})
def predict(g,v):
 return old.predict(g,v) if v in old.SETTINGS else incoming.transform(g,v)
RIVALS=VALUES+incoming.HYPOTHESES
def draw(seed,slot):
 rng=random.Random(f"{TASK_ID}:union:{seed}:{slot}")
 if slot<3:
  largest=4*(slot+1)+1+(seed+slot)%2
  sizes=(largest,1,1) if largest%4==1 else (largest,1)
 elif slot==3:sizes=(7,6,6)
 else:
  # Full quotient and remainder variation, including exact multiples.
  profiles=((4,1,1),(7,2,1),(10,3,1),(13,3,3),(6,1),(9,2))
  sizes=profiles[(slot-4+seed)%len(profiles)]
 h=w=30 if slot==9 else 14+(seed+2*slot)%13
 g=[[0]*w for _ in range(h)]
 corners=[(False,False),(False,True),(True,False),(True,True)];rng.shuffle(corners)
 for n,(bottom,right) in zip(sizes,corners):
  for r,c in old._polyomino(rng,n):g[h-3-r if bottom else r+2][w-3-c if right else c+2]=8
 positions=[(0,w//2),(1,w-1),(h-2,0),(h-1,w//2)]
 colors=list(range(1,8));random.Random(f"marker-targets:{seed}").shuffle(colors)
 chosen=colors[slot%7];others=[c for c in colors if c!=chosen];rng.shuffle(others)
 palette=others[:4];bucket=sum(sizes)//4;palette[bucket-1]=chosen
 for (r,c),color in zip(positions,palette):g[r][c]=color
 incoming._validate_scene(g,expected_count=sum(sizes))
 return g
def generate(seed,settings,demos=4,queries=4):
 v=setting(settings)
 if type(seed) is not int or seed<0:raise ValueError("invalid seed")
 if type(demos) is not int or not 4<=demos<=6:raise ValueError("invalid demos")
 if type(queries) is not int or not 1<=queries<=4:raise ValueError("invalid queries")
 order=list(range(6,10));random.Random(f"query:{seed}").shuffle(order)
 def pair(i):
  g=draw(seed,i);return {"input":g,"output":predict(g,v)}
 return {"train":[pair(i) for i in range(demos)],"test":[pair(i) for i in order[:queries]],"program_solution":program(settings)}
def findings(e,v):
 result=[r for r in RIVALS if r!=v and all(predict(p["input"],r)==p["output"] for p in e["train"]) and any(predict(p["input"],r)!=p["output"] for p in e["test"])]
 result += [x["policy"] for x in old.teaching(e)["query_disagreements"]]
 return result
