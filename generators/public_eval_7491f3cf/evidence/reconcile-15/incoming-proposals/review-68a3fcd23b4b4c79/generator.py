"""Marker-selected region recombination, standalone for copied workers.

An eight-connected divider separates the first panel into two four-connected
open regions. Its isolated dot selects one region. The default takes that
region from source panel two and the other from three. On the divider, combine
both transparently with the selected-region source taking nonbackground priority.
The alternative swaps source roles. Only the fourth panel is overwritten.
"""
import random

RULE_TASK_ID = 'ee_7491f3cf'
TASK_ID = 'public_eval_7491f3cf'
VERSION = '1.0.0'
SETTINGS = ('marked_second', 'marked_third')


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30
            or any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected rectangular 1..30 grid of exact integer colors')


def groups(points,connectivity=4):
    points=set(points);out=[];steps=((-1,0),(1,0),(0,-1),(0,1))
    if connectivity==8:steps+=((-1,-1),(-1,1),(1,-1),(1,1))
    while points:
        first=min(points);points.remove(first);stack=[first];part={first}
        while stack:
            r,c=stack.pop()
            for dr,dc in steps:
                p=(r+dr,c+dc)
                if p in points:points.remove(p);part.add(p);stack.append(p)
        out.append(part)
    return out


def _runs(values):
    runs=[]
    for v in values:
        if runs and v==runs[-1][-1]+1:runs[-1].append(v)
        else:runs.append([v])
    return runs


def analyze(g):
    grid_check(g);frame=g[0][0];h,w=len(g),len(g[0])
    active_rows=[r for r,row in enumerate(g) if any(v!=frame for v in row)]
    active_cols=[c for c in range(w) if any(g[r][c]!=frame for r in range(h))]
    rr=_runs(active_rows);cc=_runs(active_cols)
    if len(rr)!=1 or len(cc)!=4 or len({len(x) for x in cc})!=1:
        raise ValueError('four equal horizontal panels separated by uniform frame required')
    top,bottom=rr[0][0],rr[0][-1];height=len(rr[0]);width=len(cc[0])
    if top==0 or bottom==h-1 or cc[0][0]==0 or cc[-1][-1]==w-1:
        raise ValueError('outer frame required')
    panels=[[[g[r][c] for c in run] for r in rr[0]] for run in cc]
    if any(v==frame for pane in panels for row in pane for v in row):raise ValueError('frame color cannot occur in panel content')
    bg=panels[3][0][0]
    if any(v!=bg for row in panels[3] for v in row):raise ValueError('fourth panel must initially be uniform background')
    ink={(r,c) for r,row in enumerate(panels[0]) for c,v in enumerate(row) if v!=bg}
    if len({panels[0][r][c] for r,c in ink})!=1:raise ValueError('selector requires one marker color')
    parts=groups(ink,8)
    if len(parts)!=2 or sorted(map(len,parts))[0]!=1 or sorted(map(len,parts))[1]<3:
        raise ValueError('one isolated singleton and a larger eight-connected divider required')
    marker=next(iter(min(parts,key=len)));boundary=max(parts,key=len)
    regions=groups({(r,c) for r in range(height) for c in range(width)}-boundary)
    if len(regions)!=2:raise ValueError('divider must separate exactly two four-connected open regions')
    selected=next(reg for reg in regions if marker in reg)
    return {'frame':frame,'background':bg,'top':top,'bottom':bottom,'starts':[run[0] for run in cc],
            'height':height,'width':width,'panels':panels,'marker':marker,'boundary':boundary,
            'regions':regions,'selected':selected}


def render(g, info, mode='marked_second', *, selected=None, include_boundary=True):
    chosen=set(info['selected'] if selected is None else selected)
    if include_boundary:chosen|=info['boundary']
    second,third=info['panels'][1:3];out=[row[:] for row in g]
    if mode=='marked_third':second,third=third,second
    for r in range(info['height']):
        for c in range(info['width']):
            value=(second if (r,c) in chosen else third)[r][c]
            if include_boundary and (r,c) in info['boundary']:
                value=second[r][c] if second[r][c]!=info['background'] else third[r][c]
            out[info['top']+r][info['starts'][3]+c]=value
    return out


def solve(g,mode='marked_second'):
    if type(mode) is not str or mode not in SETTINGS:raise ValueError('unknown source assignment')
    return render(g,analyze(g),mode)


def rule_mirror(g):return solve(g)


def _boundary(rng,ph,pw,profile):
    if profile=='vertical':return {(r,2) for r in range(ph)}
    if profile=='teaching_jog':return {(r,1+max(0,2-abs(r-ph//2))) for r in range(ph)}
    if profile=='horizontal':return {(3,c) for c in range(pw)}
    if profile=='corner':
        r=rng.randint(2,ph-3);c=2
        return {(y,c) for y in range(r+1)}|{(r,x) for x in range(c,pw)}
    if profile=='diagonal' and ph==pw:return {(r,r) for r in range(ph)}
    # An input-derived jagged barrier. Single-cell diagonal contacts still
    # block four-connected region travel, but do not block eight-connected travel.
    c=2;points=set()
    for r in range(ph):
        if pw>=6 and r%3==2:c=5-c
        points.add((r,c))
    return points


def _payload(rng,ph,pw,bg,ink,kind):
    pattern=[]
    for r in range(ph):
        row=[]
        for c in range(pw):
            if kind==0:on=(r+c)%2==0
            elif kind==1:on=(r%3==0 or c==pw//2)
            elif kind==2:on=(r%max(2,pw)==c or c==pw-1-(r%pw))
            elif kind==3:on=(r in (0,ph-1) or c in (0,pw-1))
            else:on=rng.random()<0.48
            row.append(ink if on else bg)
        pattern.append(row)
    return pattern


def _construct(rng,h,w,profile,region_index=None,flip=False):
    pw=(w-5)//4;ph=h-2
    borders=[1]*5
    for _ in range(w-(4*pw+5)):borders[rng.randrange(5)]+=1
    palette=rng.sample(range(10),5);frame,bg,mask_color,b_color,c_color=palette
    boundary=_boundary(rng,ph,pw,profile)
    if flip:
        if rng.randrange(2):boundary={(ph-1-r,c) for r,c in boundary}
        if rng.randrange(2):boundary={(r,pw-1-c) for r,c in boundary}
    regions=groups({(r,c) for r in range(ph) for c in range(pw)}-boundary)
    if len(regions)!=2:raise ValueError('construction did not divide panel into two regions')
    # A marker must remain an isolated eight-component, not attach to the line.
    safe=[[p for p in sorted(reg) if all(max(abs(p[0]-r),abs(p[1]-c))>1 for r,c in boundary)] for reg in regions]
    eligible=[i for i,pts in enumerate(safe) if pts]
    pick=rng.choice(eligible) if region_index is None else region_index
    if pick not in eligible:raise ValueError('no isolated marker site in requested region')
    marker=rng.choice(safe[pick]);selector=[[bg]*pw for _ in range(ph)]
    for r,c in boundary|{marker}:selector[r][c]=mask_color
    second=_payload(rng,ph,pw,bg,b_color,rng.randrange(5));third=_payload(rng,ph,pw,bg,c_color,rng.randrange(5))
    # Observable disagreements in both regions and on the boundary prevent a
    # demonstration from accidentally hiding source ownership or line inclusion.
    for zone in (regions[0],regions[1],boundary):
        r,c=rng.choice(sorted(zone));second[r][c]=b_color;third[r][c]=c_color
    # A nonrectangular marked region must not collapse to its bounding box.
    selected=regions[pick];rs=[r for r,c in selected];cs=[c for r,c in selected]
    leaks={(r,c) for r in range(min(rs),max(rs)+1) for c in range(min(cs),max(cs)+1)}-selected-boundary
    if leaks:
        r,c=rng.choice(sorted(leaks));second[r][c]=b_color;third[r][c]=c_color
    # Three distinct line sites exhibit conflict and transparency in both roles.
    sites=rng.sample(sorted(boundary),3)
    for (r,c),(left,right) in zip(sites,((b_color,c_color),(bg,c_color),(b_color,bg))):
        second[r][c]=left;third[r][c]=right
    panels=[selector,second,third,[[bg]*pw for _ in range(ph)]]
    g=[[frame]*w for _ in range(h)];x=borders[0]
    for i,pane in enumerate(panels):
        for r in range(ph):g[r+1][x:x+pw]=pane[r][:]
        x+=pw+borders[i+1]
    analyze(g)
    return g


def scene(seed,index,kind):
    integer(seed,0,2**63-1,'seed')
    if kind not in ('demo','query'):raise ValueError('unknown scene kind')
    integer(index,0,5 if kind=='demo' else 3,'index')
    dims=((8,29),(12,25),(10,25),(18,29),(20,25),(24,29)) if kind=='demo' else ((9,25),(16,29),(25,25),(30,30))
    h,w=dims[index];rng=random.Random(f'7491f3cf:v1:{seed}:{kind}:{index}')
    if kind=='demo' and index==0:return _construct(rng,h,w,'teaching_jog',region_index=0)
    if kind=='demo' and index==1:return _construct(rng,h,w,'horizontal',region_index=1)
    profile=rng.choice(('corner','jagged','horizontal','vertical'))
    return _construct(rng,h,w,profile,flip=True)


def generate(seed=0,sample_index=0,difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**63-1,'sample_index')
    if difficulty is None:difficulty='medium'
    if difficulty not in ('easy','medium','hard','mixed'):raise ValueError('unsupported difficulty')
    rng=random.Random(f'7491f3cf:base:{seed}:{sample_index}:{difficulty}')
    if difficulty=='mixed':difficulty=rng.choice(('easy','medium','hard'))
    h,w={'easy':(7,25),'medium':(16,29),'hard':(30,30)}[difficulty]
    profile=rng.choice(('vertical','corner','diagonal','jagged'))
    return _construct(rng,h,w,profile,flip=True)


def self_check(g,difficulty=None):
    try:analyze(g)
    except (ValueError,TypeError) as exc:return [str(exc)]
    return []
