"""Standalone wall-keyed arrow decoder, collision interpreter and input sampler."""
from collections import deque
import hashlib
import random

GENERATOR_ID = TASK_ID = "public_eval_88e364bc"
RULE_TASK_ID = 'ee_88e364bc'
VERSION = "1.0.0"
SUMMARY = "Decode each wall-colored legend and slide its enclosed tokens without cutting wall corners."
INVARIANTS = ["background0/head2/token4", "isolated solid arrow legends", "enclosed monochrome-wall regions", "distinct token motion lines", "simultaneous independent motion"]
AXES = {}
CARDINAL = ((-1,0),(1,0),(0,-1),(0,1))
DIRECTIONS = tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if (r,c)!=(0,0))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def motion(value):
    if type(value) is not str or value not in ("toward_head","toward_tail"):
        raise ValueError("motion must be toward_head or toward_tail")
    return value


def components(cells, deltas=CARDINAL):
    unseen=set(cells);result=[]
    while unseen:
        start=min(unseen);unseen.remove(start);part={start};todo=deque([start])
        while todo:
            r,c=todo.popleft()
            for dr,dc in deltas:
                q=r+dr,c+dc
                if q in unseen: unseen.remove(q);part.add(q);todo.append(q)
        result.append(part)
    return result


def endpoint(cells, start, direction, *, corners=True):
    r,c=start;dr,dc=direction
    while ((r+dr,c+dc) in cells and
           (not corners or not dr or not dc or ((r+dr,c) in cells and (r,c+dc) in cells))):
        r+=dr;c+=dc
    return r,c


def parse(g):
    if type(g) is not list or not 10<=len(g)<=30:
        raise ValueError("height must be10..30 with exact list rows")
    if type(g[0]) is not list or not 10<=len(g[0])<=30:
        raise ValueError("width must be10..30")
    h,w=len(g),len(g[0])
    if any(type(row) is not list or len(row)!=w for row in g):
        raise ValueError("rectangular exact list rows required")
    if any(type(v) is not int or not 0<=v<=9 for row in g for v in row):
        raise ValueError("exact integer colors0..9 required")
    allcells={(r,c) for r in range(h) for c in range(w)}
    nonzero={p for p in allcells if g[p[0]][p[1]]!=0}
    legends=[];legend_cells=set();bywall={}
    for cells in components(nonzero,DIRECTIONS):
        heads={p for p in cells if g[p[0]][p[1]]==2}
        if not heads: continue
        r0,c0=min(r for r,c in cells),min(c for r,c in cells)
        r1,c1=max(r for r,c in cells),max(c for r,c in cells)
        wall=g[r0][c0]
        if len(cells)!=(r1-r0+1)*(c1-c0+1) or wall in (0,2,4):
            raise ValueError("legend must be an isolated solid rectangle with a wall-colored border")
        if any(g[r][c]!=wall for r,c in cells if r in (r0,r1) or c in (c0,c1)):
            raise ValueError("legend border must have one wall color")
        palette={g[r][c] for r,c in cells}
        tails=cells-heads-{p for p in cells if g[p[0]][p[1]]==wall}
        if len(heads)!=2 or len(tails)!=4 or len(palette)!=3 or 4 in palette:
            raise ValueError("legend requires two heads and four same-color tail cells")
        candidates=[]
        for dr,dc in DIRECTIONS:
            expected={(r-k*dr,c-k*dc) for r,c in heads for k in (1,2)}
            if expected==tails: candidates.append((dr,dc))
        if len(candidates)!=1 or wall in bywall:
            raise ValueError("unique direction and one legend per wall color required")
        record={"wall":wall,"tail":next(iter(palette-{wall,2})),"direction":list(candidates[0]),
                "bounds":[r0,c0,r1,c1],"heads":[list(p) for p in sorted(heads)]}
        bywall[wall]=record;legends.append(record);legend_cells.update(cells)
    if not 1<=len(legends)<=3:
        raise ValueError("one to three wall-keyed legends required")
    if any(g[r][c] not in ({0,4}|set(bywall)) for r,c in allcells-legend_cells):
        raise ValueError("all nonlegend walls must have a legend")
    tokens={p for p in allcells if g[p[0]][p[1]]==4}
    if not tokens: raise ValueError("at least one token required")
    free={p for p in allcells if g[p[0]][p[1]] in (0,4)}
    regions=[]
    for cells in components(free):
        local=tokens&cells
        if not local:continue
        if any(r in (0,h-1) or c in(0,w-1) for r,c in cells):
            raise ValueError("token region must be enclosed")
        boundary={g[r+dr][c+dc] for r,c in cells for dr,dc in CARDINAL
                  if (r+dr,c+dc) not in cells}
        if len(boundary)!=1 or not boundary.issubset(bywall):
            raise ValueError("token region must have one keyed boundary wall color")
        wall=next(iter(boundary));dr,dc=bywall[wall]["direction"]
        if len({dr*c-dc*r for r,c in local})!=len(local):
            raise ValueError("tokens may not share a motion line inside one region")
        regions.append({"wall":wall,"direction":[dr,dc],"cells":[list(p) for p in sorted(cells)],
                        "tokens":[list(p) for p in sorted(local)]})
    if {r["wall"] for r in regions}!=set(bywall):
        raise ValueError("every legend must control a token-containing region")
    return {"height":h,"width":w,"legends":legends,"regions":regions,
            "tokens":[list(p) for p in sorted(tokens)]}


def analyze(g,mode="toward_head"):
    motion(mode);a=parse(g);out=[row[:] for row in g];moves=[]
    for r,c in a["tokens"]:out[r][c]=0
    for region in a["regions"]:
        dr,dc=region["direction"]
        direction=(dr,dc) if mode=="toward_head" else (-dr,-dc)
        cells={tuple(p) for p in region["cells"]}
        for start in region["tokens"]:
            end=endpoint(cells,tuple(start),direction);out[end[0]][end[1]]=4
            moves.append({"wall":region["wall"],"start":start[:],"direction":list(direction),"end":list(end)})
    return {**a,"moves":moves,"output":out}


def solve(g,mode="toward_head"):
    return analyze(g,mode)["output"]


def self_check(g):
    try:parse(g)
    except (ValueError,TypeError) as error:return [str(error)]
    return []


def rng_for(seed,label):
    return random.Random(int.from_bytes(hashlib.sha256(f"88e364bc/{seed}/{label}".encode()).digest(),"big"))


def rotate(g,turns):
    out=[row[:] for row in g]
    for _ in range(turns):out=[list(row) for row in zip(*out[::-1])]
    return out


def panel(wall,tail,direction):
    diagonal=bool(direction[0] and direction[1]);h,w=(6,7) if diagonal else (5,5)
    g=[[wall]*w for _ in range(h)]
    tails=[(1,3),(2,4),(2,1),(3,2)] if diagonal else [(1,1),(1,2),(3,1),(3,2)]
    heads=[(3,5),(4,3)] if diagonal else [(1,3),(3,3)]
    for r,c in tails:g[r][c]=tail
    for r,c in heads:g[r][c]=2
    d=(1,1) if diagonal else (0,1);turns=0
    while d!=direction:d=(d[1],-d[0]);turns+=1
    return rotate(g,turns)


def choose_tokens(cells,direction,rng,quota,*,teach_clear=False):
    r0,r1=min(r for r,c in cells),max(r for r,c in cells)
    c0,c1=min(c for r,c in cells),max(c for r,c in cells)
    box={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}
    candidates=list(sorted(cells));rng.shuffle(candidates);features={}
    for p in candidates:
        f=set()
        for label,d in (("head",direction),("tail",(-direction[0],-direction[1]))):
            end=endpoint(cells,p,d);distance=max(abs(end[0]-p[0]),abs(end[1]-p[1]))
            if end!=endpoint(cells,p,d,corners=False):f.add(label+"_corner")
            if end!=endpoint(box,p,d):f.add(label+"_local")
            if distance>=3:f.add(label+"_long")
            if distance==1:f.add(label+"_one")
            if distance==0:f.add(label+"_still")
            if distance and any((p[0]+dr,p[1]+dc) not in cells for dr,dc in CARDINAL):f.add(label+"_side_contact")
        features[p]=f
    chosen=[];lines=set();covered=set();dr,dc=direction
    if teach_clear:
        pairs=[(p,(p[0]+dr,p[1])) for p in candidates
               if dr and dc and all((p[0]+rr,p[1]+cc) in cells for rr in (0,dr) for cc in (-1,0,1))]
        if not pairs:raise ValueError("core diagonal chamber cannot teach simultaneous clearing")
        chosen=list(pairs[0])
        lines={dr*c-dc*r for r,c in chosen}
        covered=set().union(*(features[p] for p in chosen))
    while len(chosen)<quota:
        available=[p for p in candidates if dr*p[1]-dc*p[0] not in lines]
        if not available:break
        def score(p):
            return sum(3 if f.endswith("corner") else 2 if f.endswith(("local","long")) else 1 for f in features[p]-covered)
        p=max(available,key=score);chosen.append(p);covered.update(features[p]);lines.add(dr*p[1]-dc*p[0])
    return chosen


def sample_profile(seed,label,profile):
    rng=rng_for(seed,label)
    h,w=[(24,28),(26,28),(20,24),(22,26),(28,28),(30,26),(14,14),(22,28),(25,29),(30,30)][profile]
    count=1 if profile==6 else 2
    walls=rng.sample([1,3,5,6,7,8,9],count)
    directions=[(0,1),(1,1)] if profile==0 else [(-1,0),(1,-1)] if profile==1 else rng.sample(list(DIRECTIONS),count)
    tails=[rng.choice([v for v in (1,3,5,6,7,8,9) if v!=wall]) for wall in walls]
    g=[[0]*w for _ in range(h)]
    zones=[(i*w//count,(i+1)*w//count) for i in range(count)]
    order=list(range(count))
    if profile==0 or (profile>=2 and rng.choice((False,True))):order.reverse()
    for zone,(left,right) in enumerate(zones):
        k=order[zone];p=panel(walls[k],tails[k],directions[k]);start=left+rng.randrange(1,right-left-len(p[0]))
        for r,row in enumerate(p):
            for c,v in enumerate(row):g[r][start+c]=v
    for k,(left,right) in enumerate(zones):
        width=right-left;first,last=9,h-3
        split=(profile in (0,9) and k==0) or (profile==3 and k==1)
        middle=(first+last)//2
        spans=[(first,middle-2),(middle+2,last)] if split and last-first>=9 else [(first,last)]
        for low,high in spans:
            phase=rng.randrange(3);interior=set()
            for i,r in enumerate(range(low,high+1)):
                a=2+(i//2+phase)%3;b=width-3-((i+phase)//3)%2
                interior.update((r,left+c) for c in range(a,b+1))
            if high-low>=8 and width>=13:
                rr=(low+high)//2;cc=left+width//2
                interior-={(rr,cc),(rr+1,cc)}
            for r,c in interior:
                for dr,dc in DIRECTIONS:
                    q=(r+dr,c+dc)
                    if q not in interior:g[q[0]][q[1]]=walls[k]
            for cells in components(interior):
                teach_clear=profile in (0,1) and all(directions[k])
                quota=9 if profile==9 else 8 if teach_clear else 6 if profile in (0,1) else 4
                for r,c in choose_tokens(cells,directions[k],rng,quota,teach_clear=teach_clear):g[r][c]=4
    if profile>=2:
        if rng.choice((False,True)):g=g[::-1]
        if rng.choice((False,True)):g=[row[::-1] for row in g]
    g=rotate(g,rng_for(seed,"lesson-rotation").randrange(4))
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
