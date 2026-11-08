"""Standalone border-directed bar reader and input-only generator."""
from collections import deque
import hashlib
import random

GENERATOR_ID=TASK_ID="public_eval_291dc1e1"
RULE_TASK_ID = 'ee_291dc1e1'
VERSION="1.0.0"
SUMMARY="Read two-thick bars using the1/2border axes, normalize vertical bars CCW and center their ordered stack."
INVARIANTS=["top corner0", "complete1/2border strips", "background8", "filled even-length two-thick components", "one to fifteen bars"]
AXES={}


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f"{name} must be an exact integer in{low}..{high}")


def stack_order(value):
    if type(value) is not str or value not in ("forward","reverse"):
        raise ValueError("stack_order must be forward or reverse")
    return value


def parse(g):
    if type(g) is not list or not 5<=len(g)<=30:
        raise ValueError("height must be5..30 with exact list rows")
    if type(g[0]) is not list or not 5<=len(g[0])<=30:raise ValueError("width must be5..30")
    h,w=len(g),len(g[0])
    if any(type(row) is not list or len(row)!=w for row in g):raise ValueError("rectangular exact list rows required")
    if any(type(v) is not int or not 0<=v<=9 for row in g for v in row):raise ValueError("exact integer colors0..9 required")
    origins=[c for c in (0,w-1) if g[0][c]==0]
    if len(origins)!=1:raise ValueError("exactly one top corner0 required")
    edge=origins[0];right=edge==w-1;top=g[0][0 if right else 1]
    if top not in(1,2) or any(g[0][c]!=top for c in range(w) if c!=edge):raise ValueError("top strip must be all1 or all2")
    if any(g[r][edge]!=3-top for r in range(1,h)):raise ValueError("side strip must carry the other axis color")
    horizontal=top==1
    unseen={(r,c) for r in range(1,h) for c in range(w) if c!=edge and g[r][c]!=8}
    bars=[]
    while unseen:
        start=min(unseen);unseen.remove(start);cells={start};todo=deque([start])
        while todo:
            r,c=todo.popleft()
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in unseen:unseen.remove(q);cells.add(q);todo.append(q)
        r0,c0=min(r for r,c in cells),min(c for r,c in cells)
        r1,c1=max(r for r,c in cells),max(c for r,c in cells)
        bh,bw=r1-r0+1,c1-c0+1;length=bw if horizontal else bh
        if len(cells)!=bh*bw or (bh if horizontal else bw)!=2 or length%2 or not 2<=length<=28:
            raise ValueError("components must be filled even-length bars with thickness2 on the declared axis")
        tile=[g[r][c0:c1+1] for r in range(r0,r1+1)]
        normalized=[row[:] for row in tile] if horizontal else [[g[r][c] for r in range(r0,r1+1)] for c in range(c1,c0-1,-1)]
        x=w-1-c1 if right else c0
        key=[r0,x] if horizontal else [x,r0]
        bars.append({"bounds":[r0,c0,r1,c1],"scan_key":key,"length":length,"tile":tile,"normalized":normalized})
    if not 1<=len(bars)<=15:raise ValueError("one to fifteen bars required")
    bars.sort(key=lambda b:b["scan_key"])
    return {"height":h,"width":w,"axis":"horizontal" if horizontal else "vertical",
            "start_side":"right" if right else "left","bars":bars,"packing_width":max(b["length"] for b in bars)}


def first_stage(g,order="forward"):
    stack_order(order);a=parse(g)
    return {**a,"ordered_bars":a["bars"][:] if order=="forward" else a["bars"][::-1]}


def analyze(g,order="forward"):
    a=first_stage(g,order);output=[]
    for b in a["ordered_bars"]:
        pad=(a["packing_width"]-b["length"])//2
        output.extend([[8]*pad+row[:]+[8]*pad for row in b["normalized"]])
    return {**a,"output":output}


def solve(g,order="forward"):return analyze(g,order)["output"]


def self_check(g):
    try:parse(g)
    except (ValueError,TypeError) as e:return [str(e)]
    return []


def rng_for(seed,label):
    return random.Random(int.from_bytes(hashlib.sha256(f"291dc1e1/{seed}/{label}".encode()).digest(),"big"))


def sample_profile(seed,label,profile):
    rng=rng_for(seed,label)
    configurations=[("horizontal",True,24,14),("vertical",False,24,14),("vertical",True,22,12),
                    ("horizontal",False,18,12),("horizontal",True,26,16),("vertical",False,28,18),
                    ("horizontal",False,10,8),("horizontal",True,28,20),("vertical",False,26,16),
                    ("vertical",True,30,30)]
    axis,right,primary,secondary=configurations[profile]
    if profile in(0,1):layout=[(2,2,4),(2,10,8),(6,4,2),(6,16,6),(10,1,6),(10,10,2),(10,16,4)]
    elif profile==2:layout=[(2,2,6),(2,12,4),(6,1,2),(6,8,8),(9,3,4),(9,13,6)]
    elif profile==3:layout=[(2,1,4),(2,10,6),(5,3,2),(8,1,6),(8,12,4)]
    elif profile==6:layout=[(2,2,2),(2,6,2),(5,1,2),(5,6,2)]
    elif profile==7:layout=[(s,p,rng.choice((2,4,6))) for s in(2,8,14) for p in(2,11,20)]
    elif profile==9:
        layout=[(1,1,28)]+[(s,p,rng.choice((6,8,10,12))) for s in(5,9,13,17,21,25) for p in(1,16)]
    else:
        layout=[(s,p,rng.choice((2,4,6,8))) for s in(2,6,10,secondary-3) for p in(1,14)]
    h,w=(secondary,primary) if axis=="horizontal" else (primary,secondary)
    g=[[8]*w for _ in range(h)]
    for c in range(w):g[0][c]=1 if axis=="horizontal" else 2
    for r in range(h):g[r][0]=2 if axis=="horizontal" else 1
    g[0][0]=0;tiles=[]
    palette=[v for v in range(10) if v!=8]
    for i,(s,p,length) in enumerate(layout):
        r,c=(s,p) if axis=="horizontal" else (p,s)
        bh,bw=(2,length) if axis=="horizontal" else (length,2)
        base=rng.choice((3,4,5,6,7,9));tile=[[base]*bw for _ in range(bh)]
        if i%3!=1 or length==2:
            colors=rng.sample(palette,4)
            for (y,x),v in zip(((0,0),(0,bw-1),(bh-1,0),(bh-1,bw-1)),colors):tile[y][x]=v
            for y in range(bh):
                for x in range(bw):
                    if (y,x) not in((0,0),(0,bw-1),(bh-1,0),(bh-1,bw-1)) and rng.random()<.15:tile[y][x]=rng.choice(palette)
        if profile in(0,1) and i==6:tile=[row[:] for row in tiles[0]]
        tiles.append(tile)
        for y,row in enumerate(tile):
            for x,v in enumerate(row):
                if g[r+y][c+x]!=8:raise ValueError("sampler overlap")
                g[r+y][c+x]=v
    if right:g=[row[::-1] for row in g]
    parse(g)
    return g


def lesson_inputs(seed):
    integer(seed,0,2**63-1,"seed")
    demos=[sample_profile(seed,f"demo-{i}",i) for i in range(6)]
    queries=[sample_profile(seed,f"query-{i}",i+6) for i in range(4)]
    rng_for(seed,"complete-query-order").shuffle(queries)
    return demos,queries


def generate(seed,sample_index=0,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,"seed");integer(sample_index,0,2**63-1,"sample_index")
    if overrides:raise ValueError("no caller overrides are supported")
    return sample_profile(seed,f"base-{sample_index}",sample_index%10)
