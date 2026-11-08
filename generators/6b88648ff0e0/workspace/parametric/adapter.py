"""Native promotion of strip stacking plus an input-derived color-frequency order.
The retained strip_stack module supplies the exact two existing Racket programs.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
TASK = '6b88648ff0e0'
PARAMETER = 'stack_order'
SETTINGS = ('top_to_bottom','bottom_to_top','key_frequency')
NONCYAN = tuple(c for c in range(10) if c != 8)
spec = importlib.util.spec_from_file_location('_native_retained_strip_stack',HERE/'strip_stack.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)
RIVALS = SETTINGS + ('global_mode','first_cell','toprow_mode','smallest_color','largest_color','key_ascending',
                    'reverse_ties','row_sum','lexicographic','largest_frequency',
                    'marker_left','reverse_rows','full_rows','include_markers') + tuple(f'fixed_{c}' for c in NONCYAN)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {PARAMETER}
            or type(settings[PARAMETER]) is not str or settings[PARAMETER] not in SETTINGS):
        raise ValueError('settings must contain only a declared stack_order')
    return settings[PARAMETER]


def program(settings):
    mode = _setting(settings)
    if mode in legacy.SETTINGS: return legacy.render_program(mode)
    source = legacy.render_program('top_to_bottom')
    anchor = '(all-rows (apply append strips))'
    replacement = '''(key-values (apply append (first strips)))
                  (key (first (sort (remove-duplicates key-values)
                         (lambda (a b)
                           (let ((na (count-if (lambda (v) (= v a)) key-values))
                                 (nb (count-if (lambda (v) (= v b)) key-values)))
                             (if (= na nb) (< a b) (> na nb)))))))
                  (ordered-strips (sort strips
                       (lambda (a b)
                         (> (count-if (lambda (v) (= v key)) (apply append a))
                            (count-if (lambda (v) (= v key)) (apply append b))))))
                  (all-rows (apply append ordered-strips))'''
    if source.count(anchor) != 1: raise ValueError('canonical extraction anchor changed')
    return source.replace(anchor,replacement)


def counterfactual_program():
    # Wrong intermediate: take a cue from the full noisy field instead of the crop.
    return program({PARAMETER:'key_frequency'}).replace('(key-values (apply append (first strips)))',
                                                         '(key-values (apply append g))')


def _mode(values):
    counts=Counter(values)
    return min(counts,key=lambda v:(-counts[v],v))


def analyze(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30): raise ValueError('grid must be rectangular 1..30')
    h,w=len(grid),len(grid[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('grid requires exact ARC integers')
    by_row={}
    for r in range(h-1):
        for c in range(w-1):
            if all(grid[y][x]==8 for y in (r,r+1) for x in (c,c+1)):
                by_row.setdefault(r,[]).append(c)
    groups=sorted(by_row.items())
    if not 1 <= len(groups) <= 10 or any(len(cs)!=2 for _,cs in groups):
        raise ValueError('need 1..10 rows of exactly two cyan markers')
    if any(b[0]-a[0]<3 for a,b in zip(groups,groups[1:])):
        raise ValueError('marker groups must have a separating row')
    markers={(r+dr,c+dc) for r,cs in groups for c in cs for dr in (0,1) for dc in (0,1)}
    if markers != {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==8}:
        raise ValueError('cyan is reserved for exact 2x2 markers')
    widths={cs[1]-cs[0]-2 for _,cs in groups}
    if len(widths)!=1 or not 1 <= next(iter(widths)) <= 26: raise ValueError('uniform positive crop width required')
    strips=[[grid[r][:][cs[0]+2:cs[1]] for r in (top,top+1)] for top,cs in groups]
    key=_mode(strips[0][0]+strips[0][1])
    return {'groups':groups,'strips':strips,'key':key,
            'key_counts':[sum(v==key for row in s for v in row) for s in strips]}


def claim(grid, mode, *, intended='key_frequency'):
    info=analyze(grid);strips=info['strips'];key=info['key']
    ids=list(range(len(strips)))
    if mode not in RIVALS: raise ValueError('unknown claim policy')
    effective = intended if mode=='reverse_rows' else mode
    if effective=='bottom_to_top': ids.reverse()
    elif effective=='top_to_bottom': pass
    elif effective=='marker_left': ids.sort(key=lambda i:info['groups'][i][1][0])
    elif effective=='row_sum': ids.sort(key=lambda i:-sum(sum(r) for r in strips[i]))
    elif effective=='lexicographic': ids.sort(key=lambda i:tuple(v for r in strips[i] for v in r))
    elif effective=='largest_frequency': ids.sort(key=lambda i:-max(Counter(v for r in strips[i] for v in r).values()))
    elif effective in ('full_rows','include_markers'):
        if effective=='full_rows':return [grid[r][:] for top,_ in info['groups'] for r in (top,top+1)]
        return [grid[r][cs[0]:cs[1]+2] for top,cs in info['groups'] for r in (top,top+1)]
    else:
        if effective=='global_mode':key=_mode(v for row in grid for v in row)
        elif effective=='first_cell':key=strips[0][0][0]
        elif effective=='toprow_mode':key=_mode(strips[0][0])
        elif effective=='smallest_color':key=min(v for row in strips[0] for v in row if v != 0)
        elif effective=='largest_color':key=max(v for row in strips[0] for v in row)
        elif effective.startswith('fixed_'):key=int(effective.split('_')[1])
        counts=[sum(v==key for row in s for v in row) for s in strips]
        ids.sort(key=lambda i:(counts[i] if effective=='key_ascending' else -counts[i],
                               -i if effective=='reverse_ties' else i))
    out=[row[:] for i in ids for row in strips[i]]
    return out[::-1] if mode=='reverse_rows' else out


def _rng(seed,stream):
    return random.Random(int.from_bytes(hashlib.sha256(f'{TASK}:native-v1:{seed}:{stream}'.encode()).digest(),'big'))


def _strip(rng,width,key,decoy,k,d,first=False,other_order=None):
    n=2*width
    if not (0<=k<=n and 0<=d<=n-k): raise ValueError('impossible content counts')
    other=list(other_order) if other_order is not None else [v for v in NONCYAN if v not in (key,decoy)]
    remaining=[other[i%len(other)] for i in range(n-k-d)];rng.shuffle(remaining)
    if first:
        # The top row and its first cell suggest the WRONG cue; both rows matter.
        if k>width or d>width:raise ValueError('first strip role allocation must fit')
        top=[decoy]*d+remaining[:width-d]
        bottom=[key]*k+remaining[width-d:]
        rng.shuffle(top);rng.shuffle(bottom)
        j=top.index(decoy);top[0],top[j]=top[j],top[0]
        result=[top,bottom]
        if _mode(top+bottom)!=key:raise ValueError('first-strip key must be uniquely dominant')
        return result
    values=[key]*k+[decoy]*d+remaining;rng.shuffle(values)
    return [values[:width],values[width:]]


# (height,width,interior_width,key counts,decoy counts). Counts are input facts,
# not episode parameters. The first two lessons expose order changes and ties.
DEMO_SPECS=(
    (11,16,5,(4,1,8),(2,7,1)),
    (14,19,7,(6,10,0,6),(3,2,1,5)),
    (8,8,3,(2,),(1,)),
    (12,17,6,(4,9),(2,1)),
    (17,22,8,(5,2,11,5,0),(2,10,1,3,14)),
    (21,25,9,(6,11,1,6,16,0),(3,2,15,4,1,16)),
)
QUERY_SPECS=(
    (8,8,3,(2,4),(1,0)),
    (16,23,9,(6,14,2,6),(3,2,14,5)),
    (25,21,11,(7,12,1,7,20,0),(3,2,19,4,1,20)),
    (30,30,26,(17,46,1,33,17,0,24,8),(8,1,45,2,6,50,0,35)),
)


def _scene(seed,index,spec,stream):
    rng=_rng(seed,stream)
    h,w,width,ks,ds=spec;n=len(ks)
    palette=[1,2,3,4,5,6,7,9];_rng(seed,'cue-palette').shuffle(palette)
    key,decoy=palette[index%8],palette[(index+1)%8]
    if stream=='demo:1':
        # Low-valued cue / high-valued decoy separates count order from row sums.
        key=_rng(seed,'teaching-cue').choice([v for v in (1,2,3) if v != palette[0]])
        decoy=9
    grid=[[rng.choice((decoy,)*10+NONCYAN) for _ in range(w)] for _ in range(h)]
    if stream=='query:3':tops=[i*4 for i in range(8)]
    else:
        gaps=[0]*(n+1)
        for _ in range(h-(3*n-1)):gaps[rng.randrange(n+1)]+=1
        tops=[3*i+sum(gaps[:i+1]) for i in range(n)]
    lefts=[rng.randrange(w-width-3) for _ in range(n)]
    if stream=='demo:0':lefts=[w-width-4,0,(w-width-4)//2]
    other_order=[v for v in NONCYAN if v not in (key,decoy)];rng.shuffle(other_order)
    if stream.startswith('demo:') and key != 1 and 1 in other_order:
        other_order.remove(1);other_order.insert(0,1)
    occupied=set()
    for i,(top,left) in enumerate(zip(tops,lefts)):
        strip=_strip(rng,width,key,decoy,ks[i],ds[i],i==0,other_order)
        if stream=='demo:1':
            # Only strip 2 begins with zero: lexical order starts there and
            # cannot equal top, bottom, or key-frequency order. Counts stay fixed.
            flat=strip[0]+strip[1]
            wanted=(lambda v: v==0) if i==2 else (lambda v: v!=0)
            j=next(j for j,v in enumerate(flat) if wanted(v))
            flat[0],flat[j]=flat[j],flat[0]
            strip=[flat[:width],flat[width:]]
        right=left+2+width
        for dr in (0,1):
            for c in range(left,right+2):occupied.add((top+dr,c))
            grid[top+dr][left:left+2]=[8,8]
            grid[top+dr][left+2:right]=strip[dr]
            grid[top+dr][right:right+2]=[8,8]
    noise=[(r,c) for r in range(h) for c in range(w) if (r,c) not in occupied];rng.shuffle(noise)
    for value,(r,c) in zip(NONCYAN,noise):grid[r][c]=value
    info=analyze(grid)
    if info['key']!=key or info['key_counts']!=list(ks):raise ValueError('constructed cue/count mismatch')
    return grid


def generate(seed,settings,demos=3,queries=4):
    mode=_setting(settings)
    if type(seed) is not int or seed<0:raise ValueError('seed must be a nonnegative exact integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be 1..4')
    def pair(spec,index,stream):
        g=_scene(seed,index,spec,stream)
        return {'input':g,'output':claim(g,mode)}
    return {'train':[pair(s,i,f'demo:{i}') for i,s in enumerate(DEMO_SPECS[:demos])],
            'test':[pair(s,i+6,f'query:{i}') for i,s in enumerate(QUERY_SPECS[:queries])],
            'program_solution':program(settings),'settings':dict(settings)}


def teaching_check(episode):
    mode=_setting(episode['settings']);findings=[]
    for rival in RIVALS:
        if rival==mode:continue
        fits=all(claim(p['input'],rival,intended=mode)==p['output'] for p in episode['train'])
        if fits:
            bad=[i for i,p in enumerate(episode['test']) if claim(p['input'],rival,intended=mode)!=p['output']]
            if bad:findings.append({'rival':rival,'queries':bad})
    return findings


def public_turn(episode,index=0):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return deepcopy({'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
                     'test':[{'input':episode['test'][index]['input']}]})
