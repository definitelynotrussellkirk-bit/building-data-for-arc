"""Geometric docking family for public parent 20270e3b; no label lookups.

Two 8-connected yellow/orange pieces mate by translation: every orange port
lands on the other piece's yellow material and yellow cells never overlap.
The alternate rule fills 4-connected background pockets after assembly.
"""
from __future__ import annotations
RULE_TASK_ID = 'ee_20270e3b'
from collections import deque
import random

GENERATOR_ID = TASK_ID = 'public_eval_20270e3b'
VERSION = '1.0.0'
SUMMARY = 'Dock the two orange-port yellow pieces by collision-free translation.'
EXAMPLES_NEEDED=2
MODES=('canonical','enclosed_fill_relay')
RIVALS=('loose_port_overlap','no_assembly','marker_overlap','bbox_left','bbox_center','fill_before_join',
        'fill_all_background','eight_connected_fill','new_holes_only','never_fill')
AXES={'orientation':{'valid':'four rotations, optional reflection'},
      'ports':{'valid':'one to seven ports'},'topology':{'valid':'open, old and newly closed pockets'},
      'geometry':{'valid':'asymmetric tails, unequal bboxes, irregular cavities'},
      'stress':{'valid':'30x30 input, 27x30 or 30x27 assembled output'}}
INVARIANTS=['Background 1; yellow 4; orange ports 7',
            'Exactly two 8-connected nonbackground pieces',
            'Unique collision-free mutual-port translation (up to identical crop)',
            'No output dimension exceeds 30']


def integer(value,name,low=0,high=2**63-1):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid(value):
    if (type(value) is not list or not 1<=len(value)<=30 or type(value[0]) is not list
        or not 1<=len(value[0])<=30 or any(type(row) is not list or len(row)!=len(value[0])
        or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value)):
        raise ValueError('Expected rectangular 1..30 grid of exact integer colors 0..9')
    return [row[:] for row in value]


def pieces(g):
    remaining={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=1}
    objects=[]
    while remaining:
        first=min(remaining);remaining.remove(first);obj={first};queue=deque([first])
        while queue:
            r,c=queue.popleft()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    p=(r+dr,c+dc)
                    if p in remaining:remaining.remove(p);obj.add(p);queue.append(p)
        objects.append(obj)
    return objects


def shift(cells,delta):
    dr,dc=delta
    return {(r+dr,c+dc) for r,c in cells}


def bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def render(solid,filled=()):
    r0,c0,r1,c1=bbox(solid);filled=set(filled)
    return [[4 if (r,c) in solid else 8 if (r,c) in filled else 1
             for c in range(c0,c1+1)] for r in range(r0,r1+1)]


def holes(solid,diagonal=False):
    r0,c0,r1,c1=bbox(solid)
    empty={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1) if (r,c) not in solid}
    exterior={p for p in empty if p[0] in (r0,r1) or p[1] in (c0,c1)}
    queue=deque(exterior);deltas=[(-1,0),(1,0),(0,-1),(0,1)]
    if diagonal:deltas += [(-1,-1),(-1,1),(1,-1),(1,1)]
    while queue:
        r,c=queue.popleft()
        for dr,dc in deltas:
            p=(r+dr,c+dc)
            if p in empty and p not in exterior:exterior.add(p);queue.append(p)
    return empty-exterior


def decode(value):
    g=grid(value)
    if any(v not in (1,4,7) for row in g for v in row):raise ValueError('Colors must be 1,4,7')
    parts=pieces(g)
    if len(parts)!=2:raise ValueError('Expected exactly two 8-connected pieces')
    a,b=parts
    sa={p for p in a if g[p[0]][p[1]]==4};sb={p for p in b if g[p[0]][p[1]]==4}
    ma=a-sa;mb=b-sb
    if not sa or not sb or not ma or not mb:raise ValueError('Each piece needs yellow material and orange ports')
    anchor=min(ma);other=min(mb);candidates=[]
    for normal in ((-1,0),(1,0),(0,-1),(0,1)):
        delta=(anchor[0]-other[0]+normal[0],anchor[1]-other[1]+normal[1]);moved=shift(sb,delta)
        if shift(mb,delta)==shift(ma,normal) and ma<=moved and shift(mb,delta)<=sa and not sa&moved:
            solid=sa|moved;bounds=bbox(solid)
            if max(bounds[2]-bounds[0]+1,bounds[3]-bounds[1]+1)<=30:
                candidates.append((delta,solid))
    if not candidates:raise ValueError('No collision-free mutual-port alignment')
    signatures={tuple(map(tuple,render(solid))) for delta,solid in candidates}
    if len(signatures)!=1:raise ValueError('Ambiguous mutual-port alignment')
    delta,solid=candidates[0]
    return {'a':sa,'b':sb,'a_marks':ma,'b_marks':mb,'delta':delta,'solid':solid,
            'candidate_count':len(candidates),'input':g}


def solve(value,mode='canonical',*,rival=None):
    if mode not in MODES:raise ValueError('Undeclared mode')
    if rival is not None and rival not in RIVALS:raise ValueError('Undeclared rival')
    d=decode(value);sa,sb=d['a'],d['b'];delta=d['delta'];solid=d['solid']
    if rival=='loose_port_overlap':
        anchor=min(d['a_marks'])
        for cell in sorted(sb):
            test=(anchor[0]-cell[0],anchor[1]-cell[1]);moved=shift(sb,test)
            if d['a_marks']<=moved and shift(d['b_marks'],test)<=sa and not sa&moved:
                bounds=bbox(sa|moved)
                if max(bounds[2]-bounds[0]+1,bounds[3]-bounds[1]+1)<=30:
                    delta=test;solid=sa|moved;break
    if rival=='no_assembly':solid=sa|sb
    if rival=='marker_overlap':
        a,b=min(d['a_marks']),min(d['b_marks'])
        delta=(a[0]-b[0],a[1]-b[1]);solid=sa|shift(sb,delta)
    if rival in ('bbox_left','bbox_center'):
        # Retain docking-axis displacement but incorrectly align perpendicular
        # bounding boxes rather than the actual orange contact positions.
        a=bbox(sa);b=bbox(sb);am=min(d['a_marks']);bm=min(d['b_marks'])
        normal=(am[0]-(bm[0]+delta[0]),am[1]-(bm[1]+delta[1]))
        dr,dc=delta
        if normal[0]!=0:
            dc=(a[1]-b[1]) if rival=='bbox_left' else (a[1]+a[3]-b[1]-b[3])//2
        else:
            dr=(a[0]-b[0]) if rival=='bbox_left' else (a[0]+a[2]-b[0]-b[2])//2
        delta=(dr,dc);solid=sa|shift(sb,delta)
    filled=set()
    if mode=='enclosed_fill_relay':
        filled=holes(solid,diagonal=rival=='eight_connected_fill')
        if rival=='fill_all_background':
            r0,c0,r1,c1=bbox(solid)
            filled={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}-solid
        if rival=='fill_before_join':filled=holes(sa)|shift(holes(sb),delta)
        if rival=='new_holes_only':filled-=holes(sa)|shift(holes(sb),delta)
        if rival=='never_fill':filled=set()
    return render(solid,filled)


def self_check(value,*,difficulty=None,meta=None):
    try:decode(value)
    except (ValueError,TypeError,IndexError) as e:return [str(e)]
    return []


def teaching_failures(episode,mode):
    failures=[]
    for rival in RIVALS:
        if all(solve(p['input'],mode,rival=rival)==p['output'] for p in episode['train']):
            for i,p in enumerate(episode['test']):
                if solve(p['input'],mode,rival=rival)!=p['output']:
                    failures.append({'rival':rival,'query_index':i});break
    return failures


def rotate(g,turns=1):
    for _ in range(turns%4):g=[list(row) for row in zip(*g[::-1])]
    return g


def generate(seed,sample_index,*,difficulty=None,**overrides):
    integer(seed,'seed');integer(sample_index,'sample_index')
    if difficulty not in (None,'easy','medium','hard','mixed'):raise ValueError('Unknown difficulty')
    if overrides:raise ValueError('Unknown generation overrides: '+','.join(sorted(overrides)))
    rng=random.Random(f'{TASK_ID}:{VERSION}:{seed}:{sample_index}')
    profile=sample_index%10;stress=profile==9
    height=27 if stress else rng.randint(8,14)
    width=24 if stress else rng.randint(9,15)
    left=right=3 if stress else None
    if not stress:left,right=rng.randint(1,3),rng.randint(1,3)
    thickness=2 if stress else 3 if profile==0 else rng.randint(1,2)
    seam=13 if stress else rng.randint(4,height-3)
    walls=set(range(thickness))|set(range(width-thickness,width))
    if stress:walls.update((5,9,14,18))
    elif profile!=0:
        choices=list(range(thickness+2,width-thickness-1))
        rng.shuffle(choices)
        walls.update(choices[:rng.randint(0,min(2,len(choices)))])
    solid={(r,c) for r in range(height) for c in range(width)
           if r in (0,height-1) or c in walls}
    # Off-center appendages make correct docking disagree with bbox alignment.
    ar=rng.randint(1,seam-2);br=rng.randint(seam+1,height-2)
    solid.update((ar,c) for c in range(-left,0))
    solid.update((br,c) for c in range(width,width+right))
    if profile==1 or (profile>1 and rng.random()<.5):
        cross=rng.randint(2,seam-2)
        solid.update((cross,c) for c in range(width))
    if profile==0 or (profile>1 and rng.random()<.5):
        # A diagonal-only leak distinguishes 4- from 8-connected exterior flood.
        for i in range(thickness):solid.discard((i,i))
    if profile==0:ports=[1]
    elif stress:ports=sorted(walls)
    elif profile==1:ports=sorted(walls)
    else:ports=sorted(rng.sample(sorted(walls),rng.randint(1,len(walls))))
    a={p for p in solid if p[0]<seam};b=solid-a
    am={(seam,c) for c in ports};bm={(seam-1,c) for c in ports}
    ba=bbox(a|am);bb=bbox(b|bm)
    ah,aw=ba[2]-ba[0]+1,ba[3]-ba[1]+1
    bh,bw=bb[2]-bb[0]+1,bb[3]-bb[1]+1
    gap=1 if stress else rng.randint(1,3)
    ih=30 if stress else ah+bh+gap+rng.randint(0,2)
    iw=30 if stress else max(aw,bw)+rng.randint(0,3)
    top=0 if stress else rng.randrange(ih-ah-bh-gap+1)
    ac=0 if stress else rng.randrange(iw-aw+1)
    bc=iw-bw if stress else rng.randrange(iw-bw+1)
    g=[[1]*iw for _ in range(ih)]
    for material,marks,bounds,rr,cc in ((a,am,ba,top,ac),(b,bm,bb,top+ah+gap,bc)):
        for r,c in material:g[rr+r-bounds[0]][cc+c-bounds[1]]=4
        for r,c in marks:g[rr+r-bounds[0]][cc+c-bounds[1]]=7
    expected=render(solid)
    reflected=False if profile<2 else bool(rng.getrandbits(1))
    turns=profile if profile<2 else rng.randrange(4)
    if reflected:g=[row[::-1] for row in g];expected=[row[::-1] for row in expected]
    g=rotate(g,turns);expected=rotate(expected,turns)
    errors=self_check(g)
    if errors:raise RuntimeError('Constructed invalid scene: '+str(errors))
    if solve(g)!=expected:raise RuntimeError('Constructed docking differs from latent assembly')
    return g
