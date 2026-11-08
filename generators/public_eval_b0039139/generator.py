"""Fresh instances of public parent b0039139; no source-grid or label lookups.

Four blue-separated panels provide template, connected repetition markers,
foreground color, and background color. Canonical repetition follows the panel
axis. The opt-in relay uses each marker's area parity to reflect that copy.
"""
from __future__ import annotations
RULE_TASK_ID = 'ee_b0039139'
from collections import deque
import hashlib
import random

GENERATOR_ID = TASK_ID = 'public_eval_b0039139'
VERSION = '1.0.0'
SUMMARY = 'Repeat a recolored cropped template once per green connected marker.'
EXAMPLES_NEEDED = 2
MODES = ('canonical', 'area_parity_relay')
INVARIANTS = ['Exactly three blue separator lines', 'Template colors 0/4',
              'Marker colors 0/3', 'Two distinct nonzero nonblue palette colors']
AXES = {'orientation': {'valid': 'horizontal|vertical'},
        'marker_count': {'valid': '1..6'}, 'template_shape': {'valid': 'asymmetric binary'},
        'marker_shape': {'valid': 'connected area 1..5'},
        'palette': {'valid': 'two distinct colors from 2..9'},
        'stress': {'valid': '30x30 with 30x29 or 29x30 output'}}
RIVALS = ('one_copy','eight_connected','no_gap','solid_template','swap_palette',
          'horizontal_only','global_parity','reverse_components','always_reflect','never_reflect')


def integer(value, name, low=0, high=2**63-1):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid(value):
    if (type(value) is not list or not 1 <= len(value) <= 30
        or type(value[0]) is not list or not 1 <= len(value[0]) <= 30
        or any(type(row) is not list or len(row)!=len(value[0])
               or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value)):
        raise ValueError('Expected rectangular 1..30 grid of exact integer colors 0..9')
    return [row[:] for row in value]


def transpose(g):
    return [list(row) for row in zip(*g)]


def components(g, color=3, diagonal=False):
    todo={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==color}
    result=[]
    deltas=[(-1,0),(1,0),(0,-1),(0,1)]
    if diagonal: deltas += [(-1,-1),(-1,1),(1,-1),(1,1)]
    while todo:
        first=min(todo);todo.remove(first);seen=[first];queue=deque([first])
        while queue:
            r,c=queue.popleft()
            for dr,dc in deltas:
                q=(r+dr,c+dc)
                if q in todo: todo.remove(q);seen.append(q);queue.append(q)
        result.append(sorted(seen))
    return result


def decode(value):
    g=grid(value)
    vertical=sum(all(v==1 for v in row) for row in g)==3
    t=transpose(g) if vertical else g
    lines=[c for c in range(len(t[0])) if all(row[c]==1 for row in t)]
    if len(lines)!=3: raise ValueError('Expected exactly three full blue separators')
    a,b,c=lines
    if not (0<a<a+1<b<b+1<c<len(t[0])-1):
        raise ValueError('Each panel must be nonempty')
    panels=[[row[lo:hi] for row in t] for lo,hi in [(0,a),(a+1,b),(b+1,c),(c+1,len(t[0]))]]
    template,markers,pf,pb=panels
    if any(v not in (0,4) for row in template for v in row): raise ValueError('Invalid template panel')
    if any(v not in (0,3) for row in markers for v in row): raise ValueError('Invalid marker panel')
    cells=[(r,k) for r,row in enumerate(template) for k,v in enumerate(row) if v==4]
    objs=components(markers)
    if not cells or not objs: raise ValueError('Empty motif or marker panel')
    fg,bg=pf[0][0],pb[0][0]
    if (fg in (0,1) or bg in (0,1) or fg==bg
        or any(v!=fg for row in pf for v in row) or any(v!=bg for row in pb for v in row)):
        raise ValueError('Palette panels must be uniform and distinct')
    r0=min(r for r,k in cells);r1=max(r for r,k in cells)
    c0=min(k for r,k in cells);c1=max(k for r,k in cells)
    motif=[row[c0:c1+1] for row in template[r0:r1+1]]
    if len(objs)*(len(motif[0])+1)-1>30: raise ValueError('Repeated output exceeds ARC bounds')
    return {'vertical':vertical,'motif':motif,'markers':markers,'components':objs,'fg':fg,'bg':bg}


def solve(value, mode='canonical', *, rival=None):
    if mode not in MODES: raise ValueError('Undeclared mode')
    if rival is not None and rival not in RIVALS: raise ValueError('Undeclared rival')
    d=decode(value);motif=d['motif'];objs=d['components'];fg,bg=d['fg'],d['bg']
    if rival=='eight_connected': objs=components(d['markers'],diagonal=True)
    if rival=='one_copy': objs=objs[:1]
    if rival=='reverse_components': objs=list(reversed(objs))
    if rival=='solid_template': motif=[[4]*len(motif[0]) for _ in motif]
    if rival=='swap_palette': fg,bg=bg,fg
    gap=0 if rival=='no_gap' else 1
    copies=[]
    for obj in objs:
        flip=mode=='area_parity_relay' and len(obj)%2==1
        if rival=='global_parity': flip=mode=='area_parity_relay' and sum(len(o) for o in objs)%2==1
        if rival=='always_reflect': flip=True
        if rival=='never_reflect': flip=False
        pattern=[row[::-1] for row in motif] if flip else motif
        copies.append([[fg if v==4 else bg for v in row] for row in pattern])
    out=[]
    for r in range(len(motif)):
        row=[]
        for i,copy in enumerate(copies):
            if i: row += [bg]*gap
            row += copy[r]
        out.append(row)
    return transpose(out) if d['vertical'] and rival!='horizontal_only' else out


def self_check(value, *, difficulty=None, meta=None):
    try: decode(value)
    except (ValueError,TypeError,IndexError) as e: return [str(e)]
    return []


SHAPES={
    1: (((0,0),),),
    2: (((0,0),(0,1)), ((0,0),(1,0))),
    3: (((0,0),(1,0),(1,1)), ((0,0),(0,1),(0,2)), ((0,0),(1,0),(2,0))),
    4: (((0,0),(0,1),(1,0),(1,1)), ((0,0),(1,0),(1,1),(2,1))),
    5: (((0,0),(1,0),(2,0),(2,1),(2,2)), ((0,1),(1,0),(1,1),(1,2),(2,1))),
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    integer(seed,'seed');integer(sample_index,'sample_index')
    if difficulty not in (None,'easy','medium','hard','mixed'): raise ValueError('Unknown difficulty')
    if overrides: raise ValueError('Unknown generation overrides: '+','.join(sorted(overrides)))
    rng=random.Random(f'{TASK_ID}:{VERSION}:{seed}:{sample_index}')
    profile=sample_index%10
    count = 3 if profile==0 else 2 if profile==1 else 5 if profile==9 else rng.randint(1,6)
    vertical = profile==1 if profile<2 else bool(rng.getrandbits(1))
    stress=profile==9
    mw=5 if stress else rng.randint(2,min(5,31//count-1))
    mh=30 if stress else rng.randint(2,7)
    nr=(count+1)//2
    height=30 if stress else max(mh+2,nr*4-1,7 if profile==0 else 4)
    p0=8 if stress else mw+2
    p1=9 if stress else (7 if count>1 else 3)
    p2,p3=(5,5) if stress else (rng.randint(1,4),rng.randint(1,4))
    width=p0+p1+p2+p3+3
    assert width<=30 and height<=30
    motif=[[4 if rng.random()<rng.uniform(.35,.8) else 0 for _ in range(mw)] for _ in range(mh)]
    # Exact crop bounds and a guaranteed orientation witness; not a stored template.
    motif[0][0]=4;motif[0][-1]=0;motif[-1][-1]=4
    template=[[0]*p0 for _ in range(height)]
    r0=0 if stress else rng.randrange(height-mh+1);c0=rng.randrange(p0-mw+1)
    for r in range(mh): template[r0+r][c0:c0+mw]=motif[r][:]
    markers=[[0]*p1 for _ in range(height)]
    areas=[1,2,3] if profile==0 else [3,4] if profile==1 else [rng.randint(1,5) for _ in range(count)]
    for i,area in enumerate(areas):
        shape=rng.choice(SHAPES[area])
        if profile==0:
            # Diagonal touch separates 4-connected counting from 8-connected counting.
            shape=(((0,0),),((0,0),(0,1)),((0,0),(1,0),(1,1)))[i]
            sr,sc=((0,0),(1,1),(4,4))[i]
        elif stress:
            sr=round((i//2)*(height-3)/(nr-1));sc=(i%2)*6
        else:
            sh=max(r for r,c in shape)+1;sw=max(c for r,c in shape)+1
            sr=(i//2)*4+rng.randrange(4-sh);sc=(i%2)*4+rng.randrange(4-sw)
        for r,c in shape: markers[sr+r][sc+c]=3
    fg,bg=rng.sample(range(2,10),2)
    out=[template[r]+[1]+markers[r]+[1]+[fg]*p2+[1]+[bg]*p3 for r in range(height)]
    if vertical: out=transpose(out)
    errors=self_check(out)
    if errors: raise RuntimeError('Constructed invalid scene: '+str(errors))
    if len(decode(out)['components'])!=count: raise RuntimeError('Constructed marker collision')
    return out


def teaching_failures(episode, mode):
    failures=[]
    for rival in RIVALS:
        if all(solve(p['input'],mode,rival=rival)==p['output'] for p in episode['train']):
            for index,p in enumerate(episode['test']):
                if solve(p['input'],mode,rival=rival)!=p['output']:
                    failures.append({'rival':rival,'query_index':index})
                    break
    return failures
