"""Inward legend mapping and enclosed-region selection, with a standalone sampler.

The identical generator.py copy is relocatable without native resources. Python
outputs are claims; official/preflight/boundary labels are executed in Racket.
"""
from collections import Counter
import random
import hashlib

GENERATOR_ID=TASK_ID='public_eval_dbff022c'
RULE_TASK_ID='ee_dbff022c'
VERSION='1.0.0'
SUMMARY='Read an edge legend inward and fill enclosed regions with the mapped color.'
AXES={}
INVARIANTS=['modal background','one solid multicolor edge legend of thickness two',
            'unique directed legend keys','four-connected enclosed background regions']
D4=((-1,0),(0,-1),(0,1),(1,0))
D8=tuple((r,c) for r in (-1,0,1) for c in (-1,0,1) if r or c)


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def validate_grid(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('grid must be a 1..30 rectangle')
    if any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('exact integer colors 0..9 required')
    return grid


def bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def components(grid, accepted, connectivity=4, same_color=False):
    height,width=len(grid),len(grid[0]);seen=set();result=[]
    for r in range(height):
        for c in range(width):
            if (r,c) in seen or not accepted(grid[r][c]):continue
            stack=[(r,c)];seen.add((r,c));cells=[];color=grid[r][c]
            while stack:
                a,b=stack.pop();cells.append((a,b))
                for dr,dc in D4 if connectivity==4 else D8:
                    rr,cc=a+dr,b+dc
                    if (0<=rr<height and 0<=cc<width and (rr,cc) not in seen
                            and accepted(grid[rr][cc]) and (not same_color or grid[rr][cc]==color)):
                        seen.add((rr,cc));stack.append((rr,cc))
            result.append(sorted(cells))
    return result


def read_legend(grid,bg,direction='inward'):
    height,width=len(grid),len(grid[0]);candidates=[]
    for cells in components(grid,lambda v:v!=bg,8):
        r0,c0,r1,c1=bbox(cells);hh=r1-r0+1;ww=c1-c0+1
        colors={grid[r][c] for r,c in cells}
        if len(colors)<2 or len(cells)!=hh*ww:continue
        if hh==2 and (r0==0 or r1==height-1):horizontal=True
        elif ww==2 and (c0==0 or c1==width-1):horizontal=False
        else:continue
        candidates.append((cells,(r0,c0,r1,c1),horizontal))
    if len(candidates)!=1:raise ValueError('exactly one solid multicolor edge legend required')
    cells,(r0,c0,r1,c1),horizontal=candidates[0]
    first_is_source=r0==0 if horizontal else c0==0
    if direction=='reverse':first_is_source=not first_is_source
    elif direction=='forward':first_is_source=True
    elif direction=='backward':first_is_source=False
    elif direction!='inward':raise ValueError('unknown legend direction')
    if horizontal:
        first=[grid[r0][c] for c in range(c0,c1+1)];second=[grid[r1][c] for c in range(c0,c1+1)]
    else:
        first=[grid[r][c0] for r in range(r0,r1+1)];second=[grid[r][c1] for r in range(r0,r1+1)]
    pairs=list(zip(first,second)) if first_is_source else list(zip(second,first))
    mapping={}
    for key,value in pairs:
        if key in mapping and mapping[key]!=value:raise ValueError('conflicting legend key')
        mapping[key]=value
    return {'cells':cells,'bbox':(r0,c0,r1,c1),'horizontal':horizontal,'pairs':pairs,'mapping':mapping}


def analyze(grid, *, connectivity=4, legend_direction='inward'):
    validate_grid(grid)
    if connectivity not in (4,8):raise ValueError('unknown connectivity')
    height,width=len(grid),len(grid[0])
    bg=Counter(v for row in grid for v in row).most_common(1)[0][0]
    legend=read_legend(grid,bg,legend_direction)
    owner_by_cell={}
    for index,cells in enumerate(components(grid,lambda v:v!=bg,8,same_color=True)):
        for cell in cells:owner_by_cell[cell]=(index,len(cells))
    regions=[]
    for cells in components(grid,lambda v:v==bg,connectivity):
        if any(r in (0,height-1) or c in (0,width-1) for r,c in cells):continue
        boundary={(r+dr,c+dc) for r,c in cells for dr,dc in D4
                  if 0<=r+dr<height and 0<=c+dc<width and grid[r+dr][c+dc]!=bg}
        colors={grid[r][c] for r,c in boundary}
        if len(colors)!=1:continue
        color=next(iter(colors));r0,c0,r1,c1=bbox(cells)
        owners={owner_by_cell[cell][0] for cell in boundary}
        regions.append({'cells':cells,'color':color,'area':len(cells),'bbox':(r0,c0,r1,c1),
                        'bbox_area':(r1-r0+1)*(c1-c0+1),'owner':min(owners),
                        'owner_size':max(owner_by_cell[cell][1] for cell in boundary)})
    return {'background':bg,'legend':legend,'regions':regions}


def solve(grid, fill_scope='all', *, connectivity=4, legend_direction='inward', size_measure='area', mapping_mode='one_step'):
    data=analyze(grid,connectivity=connectivity,legend_direction=legend_direction)
    mapping=dict(data['legend']['mapping']);regions=data['regions']
    if mapping_mode=='bidirectional':
        for key,value in data['legend']['pairs']:
            if value not in mapping:mapping[value]=key
    out=[row[:] for row in grid]
    for region in regions:
        color=region['color']
        if color not in mapping:continue
        peers=[p for p in regions if p['color']==color]
        score=region[size_measure]
        if fill_scope=='all':selected=True
        elif fill_scope=='largest_per_color':selected=score==max(p[size_measure] for p in peers)
        elif fill_scope=='smallest_per_color':selected=score==min(p[size_measure] for p in peers)
        elif fill_scope=='global_largest':selected=score==max(p[size_measure] for p in regions if p['color'] in mapping)
        elif fill_scope=='largest_per_object':selected=score==max(p[size_measure] for p in peers if p['owner']==region['owner'])
        elif fill_scope=='first_per_color':selected=region is peers[0]
        elif fill_scope=='last_per_color':selected=region is peers[-1]
        elif fill_scope=='single_largest':selected=region is max(peers,key=lambda p:p[size_measure])
        elif fill_scope=='unique_largest':selected=score==max(p[size_measure] for p in peers) and sum(p[size_measure]==score for p in peers)==1
        else:raise ValueError('unknown fill scope')
        if not selected:continue
        value=mapping[color]
        if mapping_mode=='self':value=color
        elif mapping_mode=='transitive':
            seen={color}
            while value in mapping and value not in seen:
                seen.add(value);value=mapping[value]
        elif mapping_mode not in ('one_step','bidirectional'):raise ValueError('unknown mapping mode')
        for r,c in region['cells']:out[r][c]=value
    return out


def rotate(grid,k):
    for _ in range(k%4):grid=[list(row) for row in zip(*grid[::-1])]
    return grid


def tile(kind,hh,ww,color,bg):
    if kind=='diamond':
        radius=(min(hh,ww)-1)//2;n=2*radius+1
        return [[color if abs(r-radius)+abs(c-radius)==radius else bg for c in range(n)] for r in range(n)]
    grid=[[color]*ww for _ in range(hh)]
    if kind=='compact':
        # A large compact hole and an unrelated two-cell hole.
        depth=max(2,hh-3);span=max(3,ww-4)
        holes=[(r,c) for r in range(1,depth+1) for c in range(1,span+1)]
        holes += [(r,ww-2) for r in (1,2)]
    elif kind=='elbow':
        # Fewer occupied hole cells than compact, but a larger bounding box.
        depth=hh-2;span=ww-2
        holes=[(1,c) for c in range(1,span+1)]+[(r,1) for r in range(2,depth+1)]
    elif kind=='ties':
        split=(ww-3)//2
        holes=[(r,c) for r in range(1,hh-1) for c in range(1,split+1)]
        holes += [(r,c) for r in range(1,hh-1) for c in range(split+2,2*split+2)]
    elif kind in ('unmapped','open'):
        holes=[(r,c) for r in range(1,hh-1) for c in range(1,ww-1)]
        if kind=='open':holes.append((hh//2,0))
    else:raise ValueError('unknown tile')
    for r,c in holes:grid[r][c]=bg
    return grid


def scene(seed,index,*,query=False):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    rng=random.Random(f'inward-holes-v1|{seed}|{index}|{query}')
    if query:
        if index not in range(4):raise ValueError('query index must be 0..3')
        height,width=[(22,25),(26,27),(30,30),(24,29)][index]
        turn=(seed+index)%4
    else:
        height,width=[(22,25),(24,27),(26,28),(28,29),(23,26),(30,30)][index%6]
        turn=(2*(seed%2)+index)%4
    bg=rng.randrange(10);A,B,C,D,E=rng.sample([v for v in range(10) if v!=bg],5)
    # Teach exact region cells, not their boxes, even in the two-demo lesson.
    # On alternating scenes the nonrectangular diamond maps to a distinct color;
    # the other scenes retain a genuine self-map. This schedule uses no queries.
    pairs=[(A,B),(B,D),(C,E if index%2==0 else C),(E,A)];rng.shuffle(pairs)
    grid=[[bg]*width for _ in range(height)];column=rng.randrange(2,width-5)
    grid[0][column:column+4]=[p[0] for p in pairs]
    grid[1][column:column+4]=[p[1] for p in pairs]
    band=(height-3)//3;hh=band-1
    # The two A components deliberately invert area versus bounding-box size.
    compact_h=hh;compact_w=min((width-1)//2,hh+3)
    elbow_h=hh;elbow_w=hh
    entries=[('compact',compact_h,compact_w,A),('elbow',elbow_h,elbow_w,A),
             ('ties',hh,max(7,hh+2),B),('diamond',hh,hh,C),
             ('unmapped',hh,hh+1,D),('open',hh,hh+1,A)]
    rng.shuffle(entries)
    # Keep full-canvas geometry, not padded versions of a tiny scene.
    for slot,(kind,th,tw,color) in enumerate(entries):
        image=tile(kind,th,tw,color,bg)
        if rng.randrange(2):image=[row[::-1] for row in image]
        if rng.randrange(2):image=image[::-1]
        th,tw=len(image),len(image[0]);row=3+(slot//2)*band
        if slot//2==2:row=height-th
        column=0 if slot%2==0 else width-tw
        for r,values in enumerate(image):
            for c,value in enumerate(values):grid[row+r][column+c]=value
    return rotate(grid,turn)


def generate(seed,sample_index=0,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard') or overrides:raise ValueError('unsupported request')
    stream_seed=seed if sample_index<4 else int.from_bytes(hashlib.sha256(f'{TASK_ID}|ordinary|{seed}|{sample_index//4}'.encode()).digest()[:8],'big')%(2**63)
    return scene(stream_seed,sample_index%4,query=True)


def self_check(grid,*,difficulty=None,meta=None):
    try:
        data=analyze(grid)
        if not data['regions']:return ['no enclosed region']
        for scope in ('all','largest_per_color'):validate_grid(solve(grid,scope))
    except (ValueError,TypeError,KeyError,IndexError) as exc:return [str(exc)]
    return []
