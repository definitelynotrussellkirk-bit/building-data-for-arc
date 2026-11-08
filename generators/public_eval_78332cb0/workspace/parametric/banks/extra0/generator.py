"""Connector-chain panel ordering for public parent 78332cb0.

Color-6 separator lines divide equal square panels on a color-7 background.
Each panel's foreground path touches either top/bottom or left/right edges at
one coordinate.  Matching exit/entry coordinates define one unique chain.
The canonical rule lays panels out in forward chain order without rotating
panels.  The alternative traverses the chain backward and rotates every panel
180 degrees so all connectors still match.
"""
import random

RULE_TASK_ID='ee_78332cb0'
TASK_ID='public_eval_78332cb0'
VERSION='1.0.0'
SETTINGS=('forward','reverse')
RIVALS=('opposite_traversal','input_order','reverse_without_rotation',
        'rotate_without_reversal','connector_sort','start_only','end_only',
        'axis_flip','identity')
BG=7; SEP=6


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
        or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected rectangular 1..30 grid with exact integer colors')


def stress_content(grid):
    return sum(v!=BG for row in grid for v in row)


def rotate180(grid): return [row[::-1] for row in grid[::-1]]


def _split_input(grid):
    grid_check(grid);h,w=len(grid),len(grid[0])
    rc=[sum(v==SEP for v in row) for row in grid]
    cc=[sum(grid[r][c]==SEP for r in range(h)) for c in range(w)]
    mr=max(rc);mc=max(cc)
    if max(mr,mc)==0: raise ValueError('missing color-6 panel separators')
    if mr>mc:
        sep_rows=[r for r,n in enumerate(rc) if n==mr];sep_cols=[]
    elif mc>mr:
        sep_rows=[];sep_cols=[c for c,n in enumerate(cc) if n==mc]
    else:
        sep_rows=[r for r,n in enumerate(rc) if n==mr]
        sep_cols=[c for c,n in enumerate(cc) if n==mc]
    firsts=[x for xs in (sep_rows,sep_cols) for x in xs]
    side=min(firsts)
    if side<3: raise ValueError('panel side must be at least three')
    bh=(sep_rows[-1]+side+1) if sep_rows else side
    bw=(sep_cols[-1]+side+1) if sep_cols else side
    if bh>h or bw>w: raise ValueError('separator geometry exceeds input')
    # Any optional stress padding is background only and lies below/right.
    if any(grid[r][c]!=BG for r in range(h) for c in range(w) if r>=bh or c>=bw):
        raise ValueError('cells outside the inferred panel board must be background')
    row_breaks=sep_rows+[bh];col_breaks=sep_cols+[bw]
    rr=[];start=0
    for x in row_breaks: rr.append((start,x));start=x+1
    cr=[];start=0
    for x in col_breaks: cr.append((start,x));start=x+1
    if any(b-a!=side for a,b in rr+cr): raise ValueError('all panels must be equal squares')
    panels=[]
    for r0,r1 in rr:
        for c0,c1 in cr:
            panel=[row[c0:c1] for row in grid[r0:r1]]
            if any(v==SEP for row in panel for v in row): raise ValueError('separator leaked inside panel')
            panels.append(panel)
    return panels,side,len(rr),len(cr),bh,bw


def _contact(panel,side_name):
    n=len(panel)
    if side_name=='top': vals=[c for c in range(n) if panel[0][c]!=BG]
    elif side_name=='bottom': vals=[c for c in range(n) if panel[n-1][c]!=BG]
    elif side_name=='left': vals=[r for r in range(n) if panel[r][0]!=BG]
    else: vals=[r for r in range(n) if panel[r][n-1]!=BG]
    if len(vals)>1: raise ValueError('each used panel edge must have one connector')
    return vals[0] if vals else None


def analyze(grid):
    panels,side,layout_rows,layout_cols,bh,bw=_split_input(grid)
    records=[]
    for p in panels:
        rec={k:_contact(p,k) for k in ('top','bottom','left','right')}
        records.append(rec)
    vertical=all(r['left'] is None and r['right'] is None and
                 (r['top'] is not None or r['bottom'] is not None) for r in records)
    horizontal=all(r['top'] is None and r['bottom'] is None and
                   (r['left'] is not None or r['right'] is not None) for r in records)
    if vertical==horizontal: raise ValueError('panels must define exactly one connector axis')
    axis='vertical' if vertical else 'horizontal'
    incoming='top' if vertical else 'left';outgoing='bottom' if vertical else 'right'
    starts=[i for i,r in enumerate(records) if r[incoming] is None and r[outgoing] is not None]
    ends=[i for i,r in enumerate(records) if r[incoming] is not None and r[outgoing] is None]
    if len(starts)!=1 or len(ends)!=1: raise ValueError('chain needs one start and one end panel')
    # A connector value may repeat (the official three-panel example uses
    # the same coordinate at every join), so local greedy continuation is
    # insufficient.  Resolve the unique complete Hamiltonian chain instead.
    start=starts[0];end=ends[0];solutions=[]
    def extend(path,unused):
        if not unused:
            if path[-1]==end: solutions.append(path[:])
            return
        current=records[path[-1]][outgoing]
        if current is None:return
        for i in sorted(unused):
            if records[i][incoming]==current:
                extend(path+[i],unused-{i})
    extend([start],set(range(len(panels)))-{start})
    if len(solutions)!=1: raise ValueError('connector graph must define one unique complete chain')
    order=solutions[0]
    links=[records[i][outgoing] for i in order[:-1]]
    return {'panels':panels,'side':side,'axis':axis,'order':order,'links':links,
            'layout':[layout_rows,layout_cols],'board':[bh,bw]}


def _compose(panels,axis):
    side=len(panels[0]);n=len(panels)
    if axis=='vertical':
        out=[]
        for i,p in enumerate(panels):
            if i: out.append([SEP]*side)
            out.extend([row[:] for row in p])
        return out
    width=n*side+n-1;out=[[BG]*width for _ in range(side)]
    for i,p in enumerate(panels):
        c0=i*(side+1)
        if i:
            for r in range(side):out[r][c0-1]=SEP
        for r in range(side):out[r][c0:c0+side]=p[r][:]
    return out


def render(plan,mode='forward'):
    if type(mode) is not str or mode not in SETTINGS: raise ValueError('invalid traversal')
    ordered=[plan['panels'][i] for i in plan['order']]
    if mode=='reverse': ordered=[rotate180(p) for p in ordered[::-1]]
    return _compose(ordered,plan['axis'])


def solve(grid,mode='forward'): return render(analyze(grid),mode)

def rival_solve(grid,mode,rival):
    if mode not in SETTINGS or rival not in RIVALS: raise ValueError('unknown finite rival')
    plan=analyze(grid);forward=[plan['panels'][i] for i in plan['order']]
    intended=forward if mode=='forward' else [rotate180(p) for p in forward[::-1]]
    axis=plan['axis']
    if rival=='opposite_traversal': panels=forward if mode=='reverse' else [rotate180(p) for p in forward[::-1]]
    elif rival=='input_order': panels=plan['panels']
    elif rival=='reverse_without_rotation': panels=forward[::-1]
    elif rival=='rotate_without_reversal': panels=[rotate180(p) for p in forward]
    elif rival=='connector_sort':
        def key(panel):
            values=[_contact(panel,k) for k in ('top','bottom','left','right')]
            return tuple(plan['side'] if v is None else v for v in values)
        panels=sorted(plan['panels'],key=key)
    elif rival=='start_only': panels=intended[:1]
    elif rival=='end_only': panels=intended[-1:]
    elif rival=='axis_flip': return _compose(intended,'horizontal' if axis=='vertical' else 'vertical')
    else: return [row[:] for row in grid]
    return _compose(panels,axis)

def surviving_rivals(train,test,mode):
    survivors=[]
    for rival in RIVALS:
        if all(rival_solve(p['input'],mode,rival)==p['output'] for p in train) and any(
                rival_solve(p['input'],mode,rival)!=p['output'] for p in test):
            survivors.append(rival)
    return survivors

def rule_mirror(grid): return solve(grid,'forward')


def _path_panel(side,axis,entry,exit,color,rng,dense=False):
    g=[[BG]*side for _ in range(side)]
    if axis=='horizontal':
        # Build vertically then transpose: top/bottom become left/right.
        v=_path_panel(side,'vertical',entry,exit,color,rng,dense)
        return [list(row) for row in zip(*v)]
    mid=side//2
    if entry is not None:
        for r in range(0,mid+1):g[r][entry]=color
    if exit is not None:
        for r in range(mid,side):g[r][exit]=color
    if entry is not None and exit is not None:
        for c in range(min(entry,exit),max(entry,exit)+1):g[mid][c]=color
    elif entry is None:
        # Start panel: a compact head feeding the sole bottom connector.
        for c in range(max(1,exit-1),min(side-1,exit+2)):g[mid][c]=color
        if mid-1>0:g[mid-1][exit]=color
    else:
        for c in range(max(1,entry-1),min(side-1,entry+2)):g[mid][c]=color
        if mid+1<side-1:g[mid+1][entry]=color
    if dense:
        for r in range(1,side-1):
            for c in range(1,side-1):
                if (r+c+color)%3!=0:g[r][c]=color
        # Restore a guaranteed connector path after densification.
        if entry is not None:
            for r in range(0,mid+1):g[r][entry]=color
        if exit is not None:
            for r in range(mid,side):g[r][exit]=color
    return g


def _board(panels,rows,cols,side):
    h=rows*side+rows-1;w=cols*side+cols-1
    out=[[BG]*w for _ in range(h)]
    for r in range(rows):
        if r:
            rr=r*(side+1)-1
            for c in range(w):out[rr][c]=SEP
    for c in range(cols):
        if c:
            cc=c*(side+1)-1
            for r in range(h):out[r][cc]=SEP
    for i,p in enumerate(panels):
        r=i//cols;c=i%cols;r0=r*(side+1);c0=c*(side+1)
        for dr in range(side):out[r0+dr][c0:c0+side]=p[dr][:]
    return out


def _make(rng,stress=False,index=0):
    side=6 if stress or index%2 else 5
    n=4
    coords=list(range(1,side-1));rng.shuffle(coords);links=coords[:n-1]
    axis=rng.choice(('vertical','horizontal'))
    palette=[x for x in range(10) if x not in (BG,SEP)];rng.shuffle(palette)
    panels=[]
    for i in range(n):
        entry=None if i==0 else links[i-1]
        exit=None if i==n-1 else links[i]
        color=palette[i]
        panels.append(_path_panel(side,axis,entry,exit,color,rng,dense=stress))
    layout=((1,4),(4,1),(2,2))[index%3]
    perm=list(range(n));rng.shuffle(perm)
    scrambled=[panels[i] for i in perm]
    g=_board(scrambled,layout[0],layout[1],side)
    if stress:
        padded=[[BG]*30 for _ in range(30)]
        for r,row in enumerate(g):padded[r][:len(row)]=row
        g=padded
    plan=analyze(g)
    if len(plan['order'])!=n or solve(g,'forward')==solve(g,'reverse'):
        raise ValueError('constructor produced ambiguous or symmetric chain')
    return g


def scene(seed,index,kind):
    integer(seed,0,2**63-1,'seed')
    if kind not in ('demo','query'):raise ValueError('kind must be demo/query')
    integer(index,0,5 if kind=='demo' else 3,'index')
    rng=random.Random(f'78332cb0:v1:{seed}:{kind}:{index}')
    return _make(rng,stress=kind=='query' and index==3,index=index+(0 if kind=='demo' else 2))


def generate(seed=0,sample_index=0,difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**63-1,'sample_index')
    if difficulty is None:difficulty='medium'
    if difficulty not in ('easy','medium','hard','mixed'):raise ValueError('unsupported difficulty')
    rng=random.Random(f'78332cb0:base:{seed}:{sample_index}:{difficulty}')
    if difficulty=='mixed':difficulty=rng.choice(('easy','medium','hard'))
    return _make(rng,stress=difficulty=='hard',index={'easy':0,'medium':1,'hard':3}[difficulty])


def self_check(grid,difficulty=None):
    try:analyze(grid)
    except (TypeError,ValueError) as exc:return [str(exc)]
    return []
