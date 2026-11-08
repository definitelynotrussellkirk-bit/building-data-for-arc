"""Native opt-in area/perimeter ranking with matched-input teaching lessons."""
import copy
import hashlib
import math
from pathlib import Path
import random


HERE=Path(__file__).resolve().parent
METRICS=("area","perimeter")
CARDINAL=((-1,0),(1,0),(0,-1),(0,1))


def _integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")


def _metric(settings):
    if (type(settings) is not dict or set(settings)!={"rank_by"}
            or type(settings["rank_by"]) is not str or settings["rank_by"] not in METRICS):
        raise ValueError("settings must contain only rank_by='area' or 'perimeter'")
    return settings["rank_by"]


def program(settings):
    return (HERE/(_metric(settings)+".rkt")).read_text()


def perimeter(cells):
    cells=set(cells)
    return sum((r+dr,c+dc) not in cells for r,c in cells for dr,dc in CARDINAL)


def components(grid):
    unseen={(r,c) for r in range(1,len(grid)) for c,v in enumerate(grid[r]) if v!=0}
    found=[]
    while unseen:
        origin=min(unseen);unseen.remove(origin)
        cells={origin};stack=[origin]
        while stack:
            r,c=stack.pop()
            for dr,dc in CARDINAL:
                cell=(r+dr,c+dc)
                if cell in unseen:
                    unseen.remove(cell);cells.add(cell);stack.append(cell)
        found.append(cells)
    return found


def analyze(grid):
    if (type(grid) is not list or not 5<=len(grid)<=30 or type(grid[0]) is not list
            or not 5<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
            or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError("expected a rectangular 5..30 grid of exact integer colors")
    colors=[v for v in grid[0] if v]
    if (not 2<=len(colors)<=8 or len(set(colors))!=len(colors)
            or grid[0][:len(colors)]!=colors or any(grid[0][len(colors):])):
        raise ValueError("legend must be a contiguous prefix of 2..8 distinct nonzero colors")
    if any(v not in (0,8) for row in grid[1:] for v in row):
        raise ValueError("body may contain only background 0 and component color 8")
    comps=components(grid)
    if len(comps)!=len(colors):
        raise ValueError("cardinal component count must equal legend length")
    return colors,comps


def solve(grid,metric="area"):
    if type(metric) is not str or metric not in METRICS:raise ValueError("unknown metric")
    colors,comps=analyze(grid)
    measure=len if metric=="area" else perimeter
    # Canonical Racket cons-builds comps before its stable sort. Preserve
    # that final fallback when measure, top and left all coincide.
    ranked=sorted(reversed(comps),key=lambda cells:(-measure(cells),min(r for r,c in cells),min(c for r,c in cells)))
    out=copy.deepcopy(grid)
    for color,cells in zip(colors,ranked):
        for r,c in cells:out[r][c]=color
    return out


def _rng(seed,split,index,attempt=0):
    raw=f"41a5c2fcf25a-input-v1:{seed}:{split}:{index}:{attempt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest(),"big"))


def _legend(n,rng,include_source):
    colors=rng.sample([c for c in range(1,10) if c!=8],n-int(include_source))
    if include_source:colors.append(8)
    rng.shuffle(colors)
    if include_source and n>2:
        colors.remove(8);colors.insert(rng.randrange(1,n-1),8)
    if colors==sorted(colors):colors.reverse()
    return colors


def _paint(grid,cells,top,left):
    for r,c in cells:grid[top+r][left+c]=8


def _teaching(index,rng):
    if index==0:
        grid=[[0]*16 for _ in range(12)]
        shapes=[({(0,c) for c in range(5)},2,1),
                ({(r,c) for r in range(2) for c in range(3)},2,9),
                ({(0,c) for c in range(4)},7,1),
                ({(r,c) for r in range(2) for c in range(2)},8,5)]
        # The last two components touch only diagonally. The earlier area-5
        # bar must lose to the later area-6 rectangle under area ranking.
    else:
        grid=[[0]*20 for _ in range(15)]
        shapes=[({(0,c) for c in range(3)},2,1),
                ({(0,0),(0,1),(1,0)},2,9),
                ({(r,0) for r in range(3)},6,1),
                ({(r,c) for r in range(3) for c in range(3)}-{(1,1)},6,8),
                ({(r,c) for r in range(3) for c in range(3)},6,15),
                ({(0,c) for c in range(7)},11,5)]
        # Equal area/perimeter ties expose both top-before-left and the
        # left-column secondary key. A ring, later solid square and bar
        # distinguish actual cells, filled holes and inner boundary edges.
    dr,dc=rng.randrange(2),rng.randrange(2)
    for cells,r,c in shapes:_paint(grid,cells,r+dr,c+dc)
    grid[0][:len(shapes)]=_legend(len(shapes),rng,index==0)
    return grid


def _bands(total,count,start=0):
    space=total-(count-1)
    if space<2*count:raise ValueError("canvas too small for separated component slots")
    lengths=[space//count+int(i<space%count) for i in range(count)]
    out=[]
    for size in lengths:
        out.append((start,size));start+=size+1
    return out


def _shape(height,width,kind):
    if kind=="solid":return {(r,c) for r in range(height) for c in range(width)}
    if kind=="frame":return {(r,c) for r in range(height) for c in range(width) if r in (0,height-1) or c in (0,width-1)}
    if kind=="comb":return {(r,c) for r in range(height) for c in range(width) if c==0 or r%2==0}
    if kind=="elbow":return {(r,c) for r in range(height) for c in range(width) if r==0 or c==0}
    if kind=="notched":return {(r,c) for r in range(height) for c in range(width) if not (r<height//2 and c>=width//2)}
    raise ValueError("unknown shape")


def scene(height,width,count,rng,*,full=False,include_source=True):
    """Construct separated connected shapes; large cases fill their slots."""
    _integer(height,8,30,"height");_integer(width,8,30,"width");_integer(count,2,8,"count")
    nr=1 if count<=3 else 2 if count<=6 else 3
    nc=math.ceil(count/nr)
    slots=[(r,c,h,w) for r,h in _bands(height-2,nr,start=2) for c,w in _bands(width,nc)]
    kinds=["solid","frame","comb","elbow","notched"]
    rng.shuffle(kinds)
    grid=[[0]*width for _ in range(height)]
    for i,(r,c,h,w) in enumerate(slots[:count]):
        sh=h if full else rng.randint(2,h)
        sw=w if full else rng.randint(2,w)
        shape=_shape(sh,sw,kinds[i%len(kinds)])
        if rng.randrange(2):shape={(sh-1-a,b) for a,b in shape}
        if rng.randrange(2):shape={(a,sw-1-b) for a,b in shape}
        _paint(grid,shape,r+rng.randint(0,h-sh),c+rng.randint(0,w-sw))
    grid[0][:count]=_legend(count,rng,include_source)
    return grid


def _input(seed,split,index,attempt):
    rng=_rng(seed,split,index,attempt)
    if split=="train" and index<2:return _teaching(index,rng)
    if split=="train":return scene(12+index,16+index,4+index%3,rng,include_source=index%2==0)
    h,w,n=((16,19,5),(22,25,6),(30,30,8),(24,30,7))[index]
    return scene(h,w,n,rng,full=index>=1,include_source=index%2==0)


def generate(seed,settings,demos,queries):
    metric=_metric(settings)
    _integer(seed,0,2**63-1,"seed");_integer(demos,2,6,"demos");_integer(queries,1,4,"queries")
    seen=set();out={}
    for split,count in (("train",demos),("test",queries)):
        pairs=[]
        for index in range(count):
            for attempt in range(16):
                grid=_input(seed,split,index,attempt);signature=tuple(map(tuple,grid))
                if signature not in seen:
                    seen.add(signature);pairs.append({"input":grid,"output":solve(grid,metric)});break
            else:raise ValueError("distinct-input generation budget exhausted")
        out[split]=pairs
    return {**out,"program_solution":program(settings),"seed":seed,"settings":copy.deepcopy(settings)}


def public_turn(episode,query_index):
    _integer(query_index,0,len(episode["test"])-1,"query_index")
    return {"train":copy.deepcopy(episode["train"]),"test":[{"input":copy.deepcopy(episode["test"][query_index]["input"])}]}
