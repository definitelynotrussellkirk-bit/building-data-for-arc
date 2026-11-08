"""Independent model and sampler for public ARC parent 7491f3cf.

The first panel contains a straight divider and one same-colour marker on one
side.  The marker-selected source panel supplies that half-plane and wins on
the divider; the other source panel supplies the opposite half-plane.
"""
from __future__ import annotations
import random
from collections import Counter

RIVALS=(
    'identity','opposite_mode','all_second','all_third','union_second',
    'union_third','marker_side_only','opposite_side_only','fixed_negative_side',
    'ignore_boundary_overlap',
)
PALETTE=tuple(range(10))


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in [{low}, {high}]')
    return value


def grid_copy(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list
            or not 1<=len(grid[0])<=30 or any(type(row) is not list
            or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row)
            for row in grid)):
        raise ValueError('Expected a rectangular integer-color grid within 30x30')
    return [row[:] for row in grid]


def _sign(x): return (x>0)-(x<0)


def _components(cells, deltas):
    remaining=set(cells);out=[]
    while remaining:
        seed=min(remaining);remaining.remove(seed);stack=[seed];comp={seed}
        while stack:
            r,c=stack.pop()
            for dr,dc in deltas:
                q=(r+dr,c+dc)
                if q in remaining:
                    remaining.remove(q);comp.add(q);stack.append(q)
        out.append(comp)
    return out


def analyze(grid):
    g=grid_copy(grid);H,W=len(g),len(g[0])
    if H<5 or (W-5)%4 or W<17:
        raise ValueError('Expected four equal panels inside a one-cell frame')
    ph=H-2;pw=(W-5)//4
    if not 3<=pw<=6: raise ValueError('Panel width must be 3..6')
    starts=[1+i*(pw+1) for i in range(4)]
    border=g[0][0]
    if any(v!=border for v in g[0]+g[-1]): raise ValueError('Top/bottom frame is not uniform')
    if any(row[0]!=border or row[-1]!=border for row in g): raise ValueError('Side frame is not uniform')
    for sep in (starts[1]-1,starts[2]-1,starts[3]-1):
        if any(g[r][sep]!=border for r in range(H)): raise ValueError('Panel separator is not uniform')
    panels=[[[g[r+1][s+c] for c in range(pw)] for r in range(ph)] for s in starts]
    bg=Counter(v for row in panels[3] for v in row).most_common(1)[0][0]
    if any(v!=bg for row in panels[3] for v in row): raise ValueError('Fourth panel must be blank')
    guide_colors=sorted({v for row in panels[0] for v in row if v!=bg})
    if len(guide_colors)!=1: raise ValueError('Guide panel must use one nonbackground color')
    guide=guide_colors[0]
    cells={(r,c) for r in range(ph) for c in range(pw) if panels[0][r][c]==guide}
    comps=_components(cells,tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc))
    if len(comps)<2: raise ValueError('Guide needs a divider and a detached marker')
    divider=max(comps,key=lambda x:(len(x),sorted(x)))
    marker_cells=set().union(*(x for x in comps if x is not divider))
    if not marker_cells: raise ValueError('Guide marker missing')
    open_cells={(r,c) for r in range(ph) for c in range(pw)}-divider
    regions=_components(open_cells,((1,0),(-1,0),(0,1),(0,-1)))
    marker_regions=[region for region in regions if region & marker_cells]
    if len(marker_regions)!=1: raise ValueError('Marker must identify exactly one region')
    marker_region=marker_regions[0]
    def side(r,c):
        return 0 if (r,c) in divider else (1 if (r,c) in marker_region else -1)
    return {'grid':g,'H':H,'W':W,'ph':ph,'pw':pw,'starts':starts,'border':border,
            'bg':bg,'panels':panels,'guide_color':guide,'divider':divider,
            'marker_cells':marker_cells,'marker_region':marker_region,'regions':regions,
            'marker_sign':1,'side':side}


def solve(grid,mode='second',rival=None):
    if mode not in ('second','third'): raise ValueError('Unknown marker source')
    if rival is not None and rival not in RIVALS: raise ValueError('Unknown rival')
    a=analyze(grid);out=grid_copy(grid);bg=a['bg'];p2,p3=a['panels'][1],a['panels'][2]
    if rival=='identity': return out
    if rival=='opposite_mode': mode='third' if mode=='second' else 'second'
    primary=p2 if mode=='second' else p3
    secondary=p3 if mode=='second' else p2
    target_start=a['starts'][3]
    for r in range(a['ph']):
        for c in range(a['pw']):
            side=a['side'](r,c)
            if rival=='fixed_negative_side': side=-1 if side else 0
            if rival=='all_second': value=p2[r][c]
            elif rival=='all_third': value=p3[r][c]
            elif rival in ('union_second','union_third'):
                first,second=(p2,p3) if rival=='union_second' else (p3,p2)
                value=first[r][c] if first[r][c]!=bg else second[r][c]
            elif rival=='marker_side_only' and side not in (0,a['marker_sign']): value=bg
            elif rival=='opposite_side_only' and side in (0,a['marker_sign']): value=bg
            elif side==0:
                if rival=='ignore_boundary_overlap': value=secondary[r][c]
                else: value=primary[r][c] if primary[r][c]!=bg else secondary[r][c]
            elif side==a['marker_sign']: value=primary[r][c]
            else: value=secondary[r][c]
            out[r+1][target_start+c]=value
    return out


def _guide(ph,pw,kind,marker_positive,color,bg):
    panel=[[bg]*pw for _ in range(ph)]
    if kind=='row':
        k=ph//2;line={(k,c) for c in range(pw)};marker=(ph-1 if marker_positive else 0,pw//2)
    elif kind=='col':
        k=pw//2;line={(r,k) for r in range(ph)};marker=(ph//2,pw-1 if marker_positive else 0)
    elif kind=='main':
        if ph!=pw: raise ValueError('Diagonal guide requires square panel')
        line={(i,i) for i in range(ph)};marker=(ph-1,0) if marker_positive else (0,pw-1)
    elif kind=='anti':
        if ph!=pw: raise ValueError('Diagonal guide requires square panel')
        line={(i,pw-1-i) for i in range(ph)};marker=(ph-1,pw-1) if marker_positive else (0,0)
    else: raise ValueError('Unknown guide kind')
    for r,c in line|{marker}: panel[r][c]=color
    return panel,line,marker


def _profile(kind,index,difficulty='medium'):
    if kind=='demo':
        profiles=[(5,5,'col'),(6,6,'anti'),(8,5,'row'),(6,6,'main'),(10,6,'col'),(12,6,'row')]
        return profiles[index]
    if kind=='query':
        return [(8,5,'col'),(12,6,'row'),(6,6,'main'),(28,6,'col')][index]
    profiles={'easy':(6,5,'row'),'medium':(10,6,'col'),'hard':(28,6,'col')}
    return profiles[difficulty]


def sample_input(seed,index,kind='demo',difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'sample_index')
    if kind not in ('demo','query','base'): raise ValueError('Unknown input stream')
    if difficulty not in ('easy','medium','hard'): raise ValueError('Unknown difficulty')
    if kind=='demo' and index>5: raise ValueError('Demo source index must be 0..5')
    if kind=='query' and index>3: raise ValueError('Query source index must be 0..3')
    ph,pw,guide_kind=_profile(kind,index,difficulty)
    rng=random.Random(f'7491f3cf:{seed}:{kind}:{index}:{difficulty}')
    colors=list(PALETTE);rng.shuffle(colors)
    border,bg,guide_color,c2,c3=colors[:5]
    marker_positive=bool(rng.randrange(2))
    guide,line,marker=_guide(ph,pw,guide_kind,marker_positive,guide_color,bg)
    def side(r,c):
        if guide_kind=='row': return _sign(r-ph//2)
        if guide_kind=='col': return _sign(c-pw//2)
        if guide_kind=='main': return _sign(r-c)
        return _sign(r+c-(pw-1))
    marker_sign=side(*marker)
    p2=[[bg]*pw for _ in range(ph)];p3=[[bg]*pw for _ in range(ph)]
    salt=rng.randrange(97)
    for r in range(ph):
        for c in range(pw):
            if (3*r+5*c+salt)%7 in (0,1): p2[r][c]=c2
            if (5*r+2*c+salt)%7 in (2,3): p3[r][c]=c3
    groups={s:sorted((r,c) for r in range(ph) for c in range(pw) if side(r,c)==s) for s in (-1,0,1)}
    for s in (-1,1):
        cells=groups[s]
        if cells:
            p2[cells[0][0]][cells[0][1]]=c2;p3[cells[0][0]][cells[0][1]]=bg
            p3[cells[-1][0]][cells[-1][1]]=c3;p2[cells[-1][0]][cells[-1][1]]=bg
    boundary=groups[0]
    if boundary:
        a=boundary[0];b=boundary[len(boundary)//2];d=boundary[-1]
        p2[a[0]][a[1]]=c2;p3[a[0]][a[1]]=bg
        p2[b[0]][b[1]]=c2;p3[b[0]][b[1]]=c3
        p2[d[0]][d[1]]=bg;p3[d[0]][d[1]]=c3
    # Make each source visibly occupy both semantic sides in every lesson.
    for source,color in ((p2,c2),(p3,c3)):
        for s in (marker_sign,-marker_sign):
            cell=groups[s][rng.randrange(len(groups[s]))]
            source[cell[0]][cell[1]]=color
    blank=[[bg]*pw for _ in range(ph)]
    H=ph+2;W=4*pw+5;g=[[border]*W for _ in range(H)]
    starts=[1+i*(pw+1) for i in range(4)]
    for panel,start in zip((guide,p2,p3,blank),starts):
        for r in range(ph): g[r+1][start:start+pw]=panel[r]
    return g
