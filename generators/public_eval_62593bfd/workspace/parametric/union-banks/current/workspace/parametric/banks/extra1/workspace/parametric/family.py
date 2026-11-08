"""Size-frequency docking; labels are claims independently replayed by Racket."""
from collections import Counter
import hashlib
import random


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row)!=len(grid[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError("Expected a rectangular integer ARC grid, bounded by 30")
    return grid


def background(grid):
    counts=Counter(v for row in grid for v in row)
    return min(counts, key=lambda v:(-counts[v],v))


def components(grid, bg, connectivity=8):
    pending={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg}
    found=[]
    while pending:
        first=min(pending); pending.remove(first); color=grid[first[0]][first[1]]
        cells={first}; queue=[first]
        while queue:
            r,c=queue.pop()
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    if (not dr and not dc) or (connectivity==4 and abs(dr)+abs(dc)!=1): continue
                    p=r+dr,c+dc
                    if p in pending and grid[p[0]][p[1]]==color:
                        pending.remove(p); cells.add(p); queue.append(p)
        found.append((color,sorted(cells)))
    return found


def bridge_top(grid,bg):
    out=[row[:] for row in grid]
    cols=[c for c,v in enumerate(grid[0]) if v!=bg]
    if cols:
        color=0 if bg==9 else 9
        for c in range(min(cols),max(cols)+1):
            if out[0][c]==bg:out[0][c]=color
    return out


def solve(grid, finish="dock"):
    validate_grid(grid)
    if finish not in ("dock","bridge_top"): raise ValueError("Unknown finish")
    bg=background(grid); objs=components(grid,bg); counts=Counter(len(cells) for _,cells in objs)
    out=[[bg]*len(grid[0]) for _ in grid]
    for color,cells in objs:
        r0=min(r for r,c in cells); r1=max(r for r,c in cells)
        shift=-r0 if counts[len(cells)]>1 else len(grid)-1-r1
        for r,c in cells:
            if out[r+shift][c]!=bg:raise ValueError("Docking objects overlap")
            out[r+shift][c]=color
    return out if finish=="dock" else bridge_top(out,bg)


def stream(seed,tag):
    return random.Random(int.from_bytes(hashlib.sha256(f"{seed}:{tag}".encode()).digest(),"big"))


def animal(rng,size,width):
    """Eight-connected random animals, not rotations of a fixed object bank."""
    cells={(rng.randrange(5),rng.randrange(width))}
    while len(cells)<size:
        r,c=rng.choice(sorted(cells));dr,dc=rng.choice([(x,y) for x in [-1,0,1] for y in [-1,0,1] if x or y])
        q=r+dr,c+dc
        if 0<=q[0]<6 and 0<=q[1]<width:cells.add(q)
    r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    return sorted((r-r0,c-c0) for r,c in cells)


def scene(seed,index,query=False):
    rng=stream(seed,f"{'query' if query else 'demo'}:{index}")
    if query:
        height,width=[(20,24),(24,26),(28,28),(30,30)][index]
    else:
        height=13+index%6; width=23+index%4
    # A size is repeated in one demonstration and unique in the next.
    # Thus absolute area, color and position cannot stand in for multiplicity.
    base=stream(seed,"teaching")
    a=base.choice([4,5,6]); u=base.choice([7,8,9]); v=base.choice([11,12,13])
    if not query:
        sizes=[a,a,u,v] if index%2==0 else [u,u,a,v]
    elif index>=2:
        values=rng.sample(range(3,15),4);sizes=[values[0]]*2+[values[1]]*2+values[2:]
    else:
        values=rng.sample(range(3,15),3);sizes=[values[0]]*2+values[1:]
    bg=rng.randrange(10);palette=[x for x in range(9) if x!=bg];rng.shuffle(palette)
    shapes=[]
    for i,size in enumerate(sizes):
        for attempt in range(300):
            shape=animal(rng,size,3 if len(sizes)==6 else rng.choice([3,4]))
            if all(shape!=old for old in shapes):break
        else:raise ValueError("Could not sample distinct shapes")
        shapes.append(shape)
    if not query and index==0:
        # Equal occupied areas but unequal bounding boxes. The second animal
        # has a diagonal-only terminal, making 8-connectivity observable.
        shapes[0]=[(r,0) for r in range(a)]
        shapes[1]=[(0,0)]+[(1+i//2,1+i%2) for i in range(a-1)]
    # A unique-size object deliberately shares color with a repeated-size one.
    colors=palette[:len(sizes)]; colors[-1]=colors[0]
    records=list(zip(shapes,colors));rng.shuffle(records)
    used=sum(max(c for r,c in shape)+1 for shape,color in records)+len(records)-1
    if used>width:raise ValueError("Sampler packing bound exceeded")
    # Randomly distribute all remaining width, preserving a full separating column.
    spare=width-used;gaps=[0]*(len(records)+1)
    for _ in range(spare):gaps[rng.randrange(len(gaps))]+=1
    out=[[bg]*width for _ in range(height)]; col=gaps[0]
    for i,(shape,color) in enumerate(records):
        sh=max(r for r,c in shape)+1;sw=max(c for r,c in shape)+1
        top=rng.randrange(1,height-sh)  # neither edge initially touched
        if query and index==3:
            top=1 if i%2==0 else height-sh-1
        for r,c in shape:out[top+r][col+c]=color
        col+=sw+1+gaps[i+1]
    return out
