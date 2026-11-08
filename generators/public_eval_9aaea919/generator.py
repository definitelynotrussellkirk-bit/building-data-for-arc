"""Count donor objects, gray the donors and extend a receiver stack.

Self-contained source: ordinary runtime staging may copy this file alone.
The Racket reference, not this independent mirror, supplies trusted labels.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import random

GENERATOR_ID = TASK_ID = 'public_eval_9aaea919'
RULE_TASK_ID = 'ee_9aaea919'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
SUMMARY = 'Red-footed stacks donate their object counts to a green-footed receiver; donors turn gray and bars disappear.'
INVARIANTS = ['one background', 'upright aligned connected-object stacks', 'one green receiver and red donors', 'one-row bottom command bars', 'all added copies fit']
AXES = {}
POLICIES = ('sum','maximum')


def integer(value, lo, hi, name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid_check(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError('grid must have 1..30 rows and columns')
    w = len(grid[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('grid must be rectangular with exact ARC integer colors')


def components(grid, bg):
    unseen={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg}
    result=[]
    while unseen:
        p=min(unseen); unseen.remove(p); todo=[p]; cells=[]; color=grid[p[0]][p[1]]
        while todo:
            r,c=todo.pop();cells.append((r,c))
            for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if q in unseen and grid[q[0]][q[1]]==color:
                    unseen.remove(q);todo.append(q)
        cells.sort();rs,cs=zip(*cells)
        result.append(dict(cells=cells,color=color,r1=min(rs),r2=max(rs),c1=min(cs),c2=max(cs)))
    return result


def parse(grid):
    grid_check(grid)
    counts=Counter(v for row in grid for v in row)
    bg=counts.most_common(1)[0][0]
    if sum(n==counts[bg] for n in counts.values())!=1:
        raise ValueError('background must be the unique mode')
    objs=components(grid,bg)
    if not objs: raise ValueError('no stacks')
    marker_y=max(o['r2'] for o in objs)
    markers=[o for o in objs if o['r1']==o['r2']==marker_y and o['color'] in (2,3)]
    donors=[o for o in markers if o['color']==2];receivers=[o for o in markers if o['color']==3]
    if not donors or len(receivers)!=1: raise ValueError('requires donors and one receiver')
    bodies=[o for o in objs if o not in markers]
    if not bodies or any(o['r1']==o['r2'] for o in bodies): raise ValueError('bodies must have height at least two')
    def stack(marker):
        group=[o for o in bodies if (o['c1'],o['c2'])==(marker['c1'],marker['c2'])]
        if not group: raise ValueError('each marker must align with a stack')
        return sorted(group,key=lambda o:o['r1'])
    donor_stacks=[stack(m) for m in donors]
    receiver=stack(receivers[0]);base=receiver[-1];top=receiver[0]
    gap=marker_y-base['r2']-1
    if gap<1: raise ValueError('marker must be separated below stack')
    pitch=base['r2']-base['r1']+1+gap
    for group in donor_stacks+[receiver]:
        if group[-1]['r2']!=base['r2']: raise ValueError('inconsistent stack baseline')
        normalized=[]
        for o in group:
            normalized.append((o['color'],tuple((r-o['r1'],c-o['c1']) for r,c in o['cells'])))
        if len(set(normalized))!=1: raise ValueError('stack copies must be congruent with one color')
        if any(b['r1']-a['r1']!=pitch for a,b in zip(group,group[1:])): raise ValueError('inconsistent pitch')
    donor_counts=[len(g) for g in donor_stacks]
    if top['r1']-sum(donor_counts)*pitch<0: raise ValueError('insufficient headroom')
    return dict(background=bg,marker_row=marker_y,markers=markers,donor_stacks=donor_stacks,
                donor_counts=donor_counts,receiver=receiver,top=top,pitch=pitch,bodies=bodies)


def render(grid, state, count, *, gray=True, erase=True, pitch=None):
    out=deepcopy(grid)
    if erase:
        for m in state['markers']:
            for r,c in m['cells']:out[r][c]=state['background']
    if gray:
        for group in state['donor_stacks']:
            for obj in group:
                for r,c in obj['cells']:out[r][c]=5
    step=state['pitch'] if pitch is None else pitch
    for k in range(1,count+1):
        for r,c in state['top']['cells']:
            target=r-k*step
            if 0<=target<len(out): out[target][c]=state['top']['color']
    return out


def solve(grid, aggregation='sum'):
    if aggregation not in POLICIES: raise ValueError('unknown aggregation')
    state=parse(grid)
    count=sum(state['donor_counts']) if aggregation=='sum' else max(state['donor_counts'])
    return render(grid,state,count)


rule_mirror = solve


def self_check(grid, *, difficulty=None, meta=None):
    try: parse(grid)
    except (ValueError,TypeError,IndexError) as exc:return [str(exc)]
    return []


# Shape masks all span the same bbox and stay four-connected. Areas vary so
# counting donor pixels is not equivalent to counting donor objects.
def mask(h,w,kind):
    if kind==0:
        return [(r,c) for r in range(h) for c in range(w) if r==h//2 or 0<c<w-1]
    if kind==1:
        return [(r,c) for r in range(h) for c in range(w) if r==h-1 or c==0]
    if kind==2:
        return [(r,c) for r in range(h) for c in range(w) if r in (0,h-1) or c in (0,w-1)]
    return [(r,c) for r in range(h) for c in range(w)]


# h,w,mask_h,mask_w,donor counts,receiver count,neutral counts,gap
PROFILES=(
 (24,25,3,4,(2,1),1,(2,),1),
 (26,28,3,5,(1,3),1,(2,),2),
 (24,25,2,4,(2,2),2,(3,),1),
 (28,27,3,4,(3,1),2,(1,),1),
 (29,29,2,5,(1,2),2,(3,),2),
 (30,27,3,4,(2,3),1,(3,),1),
 (18,19,2,3,(1,2),1,(2,),1),
 (24,23,3,4,(2,1),2,(1,),1),
 (28,28,3,5,(1,3),2,(3,),1),
 (30,30,3,5,(2,2),2,(5,2),1),
)


def make_scene(seed,profile):
    integer(seed,0,2**63-1,'seed');integer(profile,0,9,'profile')
    rng=random.Random(int.from_bytes(hashlib.sha256(f'donor:{seed}:{profile}'.encode()).digest(),'big'))
    h,w,mh,mw,dc,rc,nc,gap=PROFILES[profile]
    bg=rng.choice((0,1,4,6,7,8,9))
    palette=[x for x in range(10) if x not in (bg,5)];rng.shuffle(palette)
    specs=[(2,n) for n in dc]+[(3,rc)]+[(None,n) for n in nc];rng.shuffle(specs)
    # The two minimal teaching examples place the larger donor on opposite
    # sides, so neither first- nor last-donor selection fits both lessons.
    if profile in (0,1):
        ordered=iter(sorted(dc,reverse=(profile==1)))
        specs=[(command,next(ordered) if command==2 else count) for command,count in specs]
    n=len(specs);span=n*mw+n-1;left=rng.randrange(w-span+1)
    marker_y=h-1;bottom=marker_y-gap-mh;pitch=mh+gap
    out=[[bg]*w for _ in range(h)]
    for j,(command,count) in enumerate(specs):
        col=left+j*(mw+1);color=palette[j%len(palette)];cells=mask(mh,mw,rng.randrange(4))
        for k in range(count):
            top=bottom-k*pitch
            for r,c in cells:out[top+r][col+c]=color
        if command:
            for c in range(col,col+mw):out[marker_y][c]=command
    # Defensive check rejects a construction defect rather than returning labels
    # from a lossy/clipped grid.
    parse(out)
    return out


def generate(seed=0,sample_index=0,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if overrides:raise ValueError('unknown overrides: '+','.join(sorted(overrides)))
    return make_scene(seed,sample_index%10)


RIVALS=('identity','maximum_instead','sum_instead','one_per_donor','first_donor',
        'last_donor','add_one','no_gray','keep_bars','fixed_pitch_four','double_count','all_stacks')


def rival(grid,policy,name):
    s=parse(grid);counts=s['donor_counts'];n=sum(counts) if policy=='sum' else max(counts)
    if name=='identity':return deepcopy(grid)
    if name=='maximum_instead':n=max(counts)
    elif name=='sum_instead':n=sum(counts)
    elif name=='one_per_donor':n=len(counts)
    elif name=='first_donor':n=counts[0]
    elif name=='last_donor':n=counts[-1]
    elif name=='add_one':n=1
    elif name=='double_count':n*=2
    elif name=='all_stacks':n=len(s['bodies'])
    elif name not in ('no_gray','keep_bars','fixed_pitch_four'):raise ValueError(name)
    return render(grid,s,n,gray=name!='no_gray',erase=name!='keep_bars',pitch=4 if name=='fixed_pitch_four' else None)
