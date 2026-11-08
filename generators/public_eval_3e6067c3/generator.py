"""Construct framed-color route puzzles; no corpus or answer lookups."""
from __future__ import annotations
from collections import Counter, defaultdict


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}, not bool/coercible')
    return value


def check_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid dimensions must be 1..30')
    width=len(grid[0])
    if any(type(row) is not list or len(row)!=width or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('rectangular exact integer colors required')


def multicolor_components(grid, background):
    height,width=len(grid),len(grid[0])
    todo={(r,c) for r in range(height) for c in range(width) if grid[r][c]!=background}
    out=[]
    directions=((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1))
    while todo:
        first=min(todo);todo.remove(first);stack=[first];cells=[]
        while stack:
            r,c=stack.pop();cells.append((r,c))
            for dr,dc in directions:
                q=(r+dr,c+dc)
                if q in todo:
                    todo.remove(q);stack.append(q)
        out.append(sorted(cells))
    return out


def _bbox(cells):
    return (min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells))


def parse(grid):
    """Decode frame blocks, occurrence-matched legend, and ordered route."""
    check_grid(grid)
    counts=Counter(v for row in grid for v in row)
    maximum=max(counts.values())
    backgrounds=[v for v,n in counts.items() if n==maximum]
    if len(backgrounds)!=1:raise ValueError('background must be uniquely modal')
    background=backgrounds[0]
    foreground=[v for v in counts if v!=background]
    if len(foreground)<3:raise ValueError('frame, payloads and legend required')
    frame_count=max(counts[v] for v in foreground)
    frames=[v for v in foreground if counts[v]==frame_count]
    if len(frames)!=1:raise ValueError('frame color must be unique most-common non-background')
    frame=frames[0]
    blocks=[];legend=[]
    for cells in multicolor_components(grid,background):
        if len(cells)==1:
            r,c=cells[0];legend.append({'row':r,'col':c,'color':grid[r][c]});continue
        r1,c1,r2,c2=_bbox(cells)
        if len(cells)!=(r2-r1+1)*(c2-c1+1):
            raise ValueError('every non-singleton object must be a filled rectangular block')
        colors={grid[r][c] for r,c in cells}
        payloads=colors-{frame}
        if frame not in colors or len(payloads)!=1:
            raise ValueError('each block must contain frame color and one payload color')
        color=next(iter(payloads));payload=[p for p in cells if grid[p[0]][p[1]]==color]
        pr1,pc1,pr2,pc2=_bbox(payload)
        if len(payload)!=(pr2-pr1+1)*(pc2-pc1+1):raise ValueError('payload must be a solid rectangle')
        if pr1-r1 != r2-pr2 or pc1-c1 != c2-pc2:
            raise ValueError('payload must be centered in its frame block')
        blocks.append({'color':color,'bbox':[r1,c1,r2,c2],'payload_bbox':[pr1,pc1,pr2,pc2]})
    blocks.sort(key=lambda b:(b['bbox'][0],b['bbox'][1]))
    legend.sort(key=lambda x:(x['row'],x['col']))
    if len(blocks)<3 or len(legend)<2 or len(legend)>len(blocks):raise ValueError('legend must select two or more available blocks')
    if len({x['row'] for x in legend})!=1 or legend[0]['row']<=max(b['bbox'][2] for b in blocks):
        raise ValueError('legend must be one row below all blocks')
    sequence=[x['color'] for x in legend]
    by_color=defaultdict(list)
    for block in blocks:by_color[block['color']].append(block)
    available=Counter(b['color'] for b in blocks)
    if any(n>available[color] for color,n in Counter(sequence).items()):raise ValueError('legend requests unavailable block occurrence')
    seen=Counter();route=[]
    for color in sequence:
        route.append(by_color[color][seen[color]]);seen[color]+=1
    for a,b in zip(route,route[1:]):
        ar=a['payload_bbox'];br=b['payload_bbox']
        horizontal=ar[0]==br[0] and ar[2]==br[2]
        vertical=ar[1]==br[1] and ar[3]==br[3]
        if horizontal==vertical:raise ValueError('consecutive route blocks must align on exactly one axis')
    return {'background':background,'frame':frame,'blocks':blocks,'legend':legend,'sequence':sequence,'route':route}


def _bridge_cells(a,b):
    ar=a['payload_bbox'];br=b['payload_bbox'];ab=a['bbox'];bb=b['bbox']
    if ar[0]==br[0] and ar[2]==br[2]:
        lo,hi=(ab[3]+1,bb[1]) if ab[1]<bb[1] else (bb[3]+1,ab[1])
        return [(r,c) for r in range(ar[0],ar[2]+1) for c in range(lo,hi)]
    if ar[1]==br[1] and ar[3]==br[3]:
        lo,hi=(ab[2]+1,bb[0]) if ab[0]<bb[0] else (bb[2]+1,ab[0])
        return [(r,c) for r in range(lo,hi) for c in range(ar[1],ar[3]+1)]
    raise ValueError('unaligned route edge')


def render_route(grid, route, bridge_color):
    if bridge_color not in ('source','destination'):raise ValueError('bridge_color must be source or destination')
    out=[row[:] for row in grid]
    for a,b in zip(route,route[1:]):
        color=a['color'] if bridge_color=='source' else b['color']
        for r,c in _bridge_cells(a,b):out[r][c]=color
    return out


def solve(grid, bridge_color='source'):
    data=parse(grid)
    return render_route(grid,data['route'],bridge_color)


def intermediate(grid):
    data=parse(grid)
    return {'sequence':list(data['sequence']),
            'route':[{'color':b['color'],'bbox':list(b['bbox']),'payload_bbox':list(b['payload_bbox'])} for b in data['route']]}


_PROFILES=[
    ([(0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3)],[(0,0),(1,0),(1,1),(0,1),(0,2),(1,2),(1,3),(0,3)]),
    ([(0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2)],[(0,0),(0,1),(0,2),(1,2),(2,2),(2,1),(2,0),(1,0)]),
    ([(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1)],[(0,0),(1,0),(2,0),(2,1),(1,1),(0,1),(0,2),(1,2)]),
    ([(0,0),(0,1),(1,0),(1,1),(2,0),(2,1),(3,0),(3,1)],[(0,0),(0,1),(1,1),(1,0),(2,0),(2,1),(3,1),(3,0)]),
    ([(0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3)],[(0,3),(1,3),(1,2),(0,2),(0,1),(1,1),(1,0),(0,0)]),
    ([(0,0),(0,1),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)],[(0,0),(0,1),(1,1),(1,2),(2,2),(2,1),(2,0),(1,0)]),
]


def _transform(coords,route,transpose,flip_r,flip_c):
    maxr=max(r for r,c in coords);maxc=max(c for r,c in coords)
    def one(p):
        r,c=p
        if flip_r:r=maxr-r
        if flip_c:c=maxc-c
        if transpose:r,c=c,r
        return (r,c)
    return [one(p) for p in coords],[one(p) for p in route]


def make_scene(seed,index,height,width):
    """Construct one exact route puzzle and both endpoint-color labels."""
    from puzzle_generators.base import gen_ctx
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    integer(height,14,30,'height');integer(width,17,30,'width')
    rng=gen_ctx(seed=seed,sample_index=index,version='1.0.0',task_id='public_eval_3e6067c3').draw_rng('scene')
    base_coords,base_route=_PROFILES[index%len(_PROFILES)]
    transformed=[]
    for transpose in (False,True):
        for flip_r in (False,True):
            for flip_c in (False,True):
                cands,rte=_transform(base_coords,base_route,transpose,flip_r,flip_c)
                cands=sorted(cands);maxr=max(r for r,c in cands);maxc=max(c for r,c in cands)
                ordering={p:i for i,p in enumerate(cands)};indices=[ordering[p] for p in rte]
                has_duplicate_pair=any(indices[i]<indices[j] for i in range(6) for j in range(i+2,8))
                if has_duplicate_pair and (maxr+1)*3+maxr<=height-3 and (maxc+1)*3+maxc<=width:
                    transformed.append((cands,rte))
    if not transformed:raise ValueError('canvas too small for every route orientation')
    coords,route=rng.choice(transformed);coord_set=set(coords)
    if set(route)!=coord_set or any(abs(a[0]-b[0])+abs(a[1]-b[1])!=1 for a,b in zip(route,route[1:])):
        raise ValueError('invalid transformed route profile')
    maxr,maxc=max(r for r,c in coords),max(c for r,c in coords)
    fitting=[]
    for size in range(6,2,-1):
        for gap in range(3,0,-1):
            used_h=(maxr+1)*size+maxr*gap;used_w=(maxc+1)*size+maxc*gap
            if used_h<=height-3 and used_w<=width:fitting.append((size,gap,used_h,used_w))
    if not fitting:raise ValueError('canvas too small for route profile')
    if index==103:
        size,gap,used_h,used_w=fitting[0]
    elif index==1:
        # The minimum two-example lesson must visibly teach corridor thickness;
        # use an even block size so its centered payload is 2 cells thick.
        size,gap,used_h,used_w=next(row for row in fitting if row[0]%2==0)
    else:
        size,gap,used_h,used_w=fitting[rng.randrange(min(4,len(fitting)))]
    max_top=height-3-used_h;max_left=width-used_w
    if index==103:top,left=0,max_left
    else:top=rng.randint(0,max_top);left=rng.randint(0,max_left)
    palette=rng.sample(list(range(10)),9);background,frame=palette[:2];payload_palette=palette[2:]
    order_index={p:i for i,p in enumerate(coords)}
    route_indices=[order_index[p] for p in route]
    candidates=[(i,j) for i in range(6) for j in range(i+2,8) if route_indices[i]<route_indices[j]]
    if not candidates:raise ValueError('profile lacks lawful duplicate-color occurrence pair')
    dup_i,dup_j=rng.choice(candidates)
    colors=[None]*8;colors[dup_i]=colors[dup_j]=payload_palette[0]
    remaining=iter(payload_palette[1:])
    for i in range(8):
        if colors[i] is None:colors[i]=next(remaining)
    by_coord={p:colors[i] for i,p in enumerate(route)}
    grid=[[background]*width for _ in range(height)]
    payload=1 if size%2 else 2;border=(size-payload)//2
    blocks=[]
    for r,c in coords:
        r0=top+r*(size+gap);c0=left+c*(size+gap);color=by_coord[(r,c)]
        for dr in range(size):
            for dc in range(size):grid[r0+dr][c0+dc]=frame
        for dr in range(payload):
            for dc in range(payload):grid[r0+border+dr][c0+border+dc]=color
        blocks.append({'coord':[r,c],'color':color,'bbox':[r0,c0,r0+size-1,c0+size-1],
                       'payload_bbox':[r0+border,c0+border,r0+border+payload-1,c0+border+payload-1]})
    legend_row=height-2;legend_span=15;legend_start=rng.randint(0,width-legend_span)
    sequence=[by_coord[p] for p in route]
    for i,color in enumerate(sequence):grid[legend_row][legend_start+2*i]=color
    source=solve(grid,'source');destination=solve(grid,'destination')
    scene={'input':grid,'sequence':sequence,'blocks':blocks,'source_output':source,'destination_output':destination,
           'background':background,'frame':frame,'size':size,'gap':gap}
    problems=self_check_scene(scene)
    if problems:raise ValueError('; '.join(problems))
    return scene


def self_check_scene(scene):
    try:data=parse(scene['input'])
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    problems=[]
    if data['sequence']!=scene['sequence']:problems.append('sequence mismatch')
    if solve(scene['input'],'source')!=scene['source_output']:problems.append('source label mismatch')
    if solve(scene['input'],'destination')!=scene['destination_output']:problems.append('destination label mismatch')
    if scene['source_output']==scene['destination_output']:problems.append('settings do not separate')
    if len(set(scene['sequence']))==len(scene['sequence']):problems.append('duplicate color teaching case missing')
    if data['route']==data['blocks']:problems.append('legend route accidentally equals reading order')
    return problems


def sample(seed,index,height,width):return make_scene(seed,index,height,width)['input']


from puzzle_generators.base import gen_ctx
GENERATOR_ID=TASK_ID='public_eval_3e6067c3'
RULE_TASK_ID='ee_3e6067c3'
VERSION='1.0.0'
SUMMARY='Read the detached color sequence, occurrence-match framed blocks, and connect consecutive aligned blocks.'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
AXES={'height':{'type':'int','valid':'14..30'},'width':{'type':'int','valid':'17..30'}}
INVARIANTS=['unique modal background','one dominant frame color','eight framed payload blocks',
            'one detached occurrence legend','axis-aligned consecutive route blocks']
RULE_HASH='a1b9671047fc'


def generate(seed,sample_index,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('unknown override')
    for k,v in overrides.items():integer(v,14 if k=='height' else 17,30,k)
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    height=ctx.draw_int_strict('height',14,30);width=ctx.draw_int_strict('width',17,30)
    return sample(seed,sample_index,height,width)


def self_check(grid,*,difficulty=None,meta=None):
    try:parse(grid)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    if isinstance(meta,dict):
        observed=observe_overrides(grid)
        return [f'{k} override not realized' for k,v in meta.get('overrides',{}).items() if observed.get(k)!=v]
    return []


def observe_overrides(grid):
    check_grid(grid);return {'height':len(grid),'width':len(grid[0])}


def rule_mirror(grid):return solve(grid,'source')
