"""Dock black glyphs and project exposed pocket rows through the divider."""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
PARAMETERS={'signal_policy':['all_exposed','largest_exposed']}
DEFAULT={'signal_policy':'all_exposed'}

def _settings(settings):
    if type(settings) is not dict or set(settings)!=set(PARAMETERS) or type(settings['signal_policy']) is not str or settings['signal_policy'] not in PARAMETERS['signal_policy']:
        raise ValueError('settings must name a declared signal_policy')
    return settings['signal_policy']

def program(settings):
    policy=_settings(settings);source=(HERE/'canonical.rkt').read_text()
    return source if policy=='all_exposed' else source.replace('(define signal-policy "all_exposed")',f'(define signal-policy "{policy}")',1)

def rival_programs():
    source=program(DEFAULT)
    return {p:source.replace('(define signal-policy "all_exposed")',f'(define signal-policy "{p}")',1)
            for p in ('all_exposed','smallest_exposed','largest_bbox','tallest','widest','first_exposed','last_exposed','median_exposed','all_holes','largest_any','before_docking','open_column','largest_body')}

def d4(grid,pose):
    if type(pose) is not int or not 0<=pose<8:raise ValueError('pose must be in 0..7')
    result=deepcopy(grid)
    if pose>=4:result=[row[::-1] for row in result]
    for _ in range(pose%4):result=[list(row) for row in zip(*result[::-1])]
    return result

def _components(points):
    remaining=set(points);out=[]
    while remaining:
        start=min(remaining);remaining.remove(start);todo=[start];component=[]
        while todo:
            r,c=todo.pop();component.append((r,c))
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining:remaining.remove(p);todo.append(p)
        out.append(sorted(component))
    return out

def _normalize(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30 or any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or v not in (0,5,6) for v in row) for row in grid):
        raise ValueError('expected rectangular 0/5/6 input grid')
    h,w=len(grid),len(grid[0]);vertical=[c for c in range(w) if all(row[c]==5 for row in grid)]
    horizontal=[r for r in range(h) if all(v==5 for v in grid[r])]
    if len(vertical)+len(horizontal)!=1:raise ValueError('one full straight divider is required')
    turned=bool(horizontal);g=[list(row) for row in zip(*grid)] if turned else deepcopy(grid)
    wall=horizontal[0] if turned else vertical[0]
    zeros=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==0]
    if not zeros:raise ValueError('at least one black glyph is required')
    right=all(c>wall for r,c in zeros);left=all(c<wall for r,c in zeros)
    if not right and not left:raise ValueError('black glyphs must lie on one side')
    if right:g=[row[::-1] for row in g];wall=len(g[0])-1-wall
    if not 2<=wall<len(g[0])-1:raise ValueError('both panels need usable space')
    return g,wall,turned,right

def _holes(cells,owner):
    r0=min(r for r,c in cells);r1=max(r for r,c in cells)
    c0=min(c for r,c in cells);c1=max(c for r,c in cells)
    inside={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}-set(cells)
    holes=[]
    for pocket in _components(inside):
        if not any(r in (r0,r1) or c in (c0,c1) for r,c in pocket):
            holes.append({'cells':[list(p) for p in pocket],'owner':owner,'body_area':len(cells)})
    return holes

def analyze(grid):
    g,wall,turned,flipped=_normalize(grid)
    objects=_components((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==0)
    docked=[[6 if v==0 else v for v in row] for row in g]
    moved=[];shifts=[];holes=[];raw_holes=[]
    for i,obj in enumerate(objects):
        dc=wall-1-max(c for r,c in obj);cells=[(r,c+dc) for r,c in obj]
        shifts.append(dc);moved.append(cells)
        for r,c in cells:docked[r][c]=0
        holes.extend(_holes(cells,i));raw_holes.extend(_holes(obj,i))
    # Per-object detection excludes gray-wall closures and open cavities.
    exposed=[p for p in holes if any(c==wall-2 for r,c in p['cells'])]
    return {'docked':docked,'wall':wall,'turned':turned,'flipped':flipped,
            'objects':[[list(p) for p in obj] for obj in objects],
            'moved':[[list(p) for p in obj] for obj in moved],'shifts':shifts,
            'holes':holes,'raw_holes':raw_holes,'exposed':exposed}

def _extent(pocket,k):
    values=[p[k] for p in pocket['cells']];return max(values)-min(values)+1

def predict(grid,policy='all_exposed'):
    cert=analyze(grid);exposed=cert['exposed'];holes=cert['holes'];wall=cert['wall']
    if policy=='before_docking':exposed=[p for p in cert['raw_holes'] if any(c==wall-2 for r,c in p['cells'])]
    if policy=='all_exposed':chosen=exposed
    elif policy=='all_holes':chosen=holes
    elif policy=='largest_any':chosen=[max(holes,key=lambda p:len(p['cells']))] if holes else []
    elif not exposed:chosen=[]
    elif policy in ('largest_exposed','before_docking','open_column'):chosen=[max(exposed,key=lambda p:len(p['cells']))]
    elif policy=='smallest_exposed':chosen=[min(exposed,key=lambda p:len(p['cells']))]
    elif policy=='largest_bbox':chosen=[max(exposed,key=lambda p:_extent(p,0)*_extent(p,1))]
    elif policy=='tallest':chosen=[max(exposed,key=lambda p:_extent(p,0))]
    elif policy=='widest':chosen=[max(exposed,key=lambda p:_extent(p,1))]
    elif policy=='largest_body':chosen=[max(exposed,key=lambda p:p['body_area'])]
    elif policy=='first_exposed':chosen=exposed[:1]
    elif policy=='last_exposed':chosen=exposed[-1:]
    elif policy=='median_exposed':chosen=[exposed[len(exposed)//2]]
    else:raise ValueError('unknown prediction policy')
    rows={r for p in chosen for r,c in p['cells'] if policy=='all_holes' or c==wall-2}
    out=deepcopy(cert['docked'])
    if policy=='open_column':rows={r for r,row in enumerate(out) if row[wall-1]==0 and row[wall-2]==6}
    for r in rows:
        for c in range(wall+1,len(out[0])):out[r][c]=2
    if cert['flipped']:out=[row[::-1] for row in out]
    if cert['turned']:out=[list(row) for row in zip(*out)]
    return out

def _hole(height,width,kind='rect'):
    if kind=='L':return {(r,c) for r in range(height) for c in range(width) if r==0 or c==0}
    return {(r,c) for r in range(height) for c in range(width)}

def _glyph(height,width,holes):
    empty=set().union(*holes) if holes else set()
    return {'height':height,'width':width,
            'cells':{(r,c) for r in range(height) for c in range(width)}-empty,
            'holes':holes}

def _scene(seed,index,attempt=0):
    rng=random.Random(f'6e453dd6:scene:{seed}:{index}:{attempt}')
    if index in (0,9):ah,aw,ak,bh,bw=3,5 if index==9 else 4,'L',2,5 if index==9 else 4
    elif index==1:ah,aw,ak,bh,bw=4,2,'rect',1,7
    else:
        ah,aw,ak,bh,bw=rng.choice([(3,4,'rect',2,5),(4,5,'L',3,3),(3,3,'rect',2,6),(2,5,'rect',4,2),(4,6,'L',2,6)])
    pocket_a={(r+1,c+1) for r,c in _hole(ah,aw,ak)}
    a=_glyph(ah+2,aw+2,[pocket_a])
    pocket_b={(r+1,c+1) for r,c in _hole(bh,bw)}
    tiny={(bh+2,bw)}
    b=_glyph(bh+4,bw+2,[pocket_b,tiny])
    max_area=max(len(pocket_a),len(pocket_b))
    buried_w=max_area//3+2
    buried={(r+1,c+1) for r in range(3) for c in range(buried_w)}
    hidden=_glyph(5,buried_w+5,[buried])
    open_c={'height':3,'width':4,'cells':{(r,c) for r in range(3) for c in range(4) if r in (0,2) or c==3},'holes':[]}
    glyphs=[a,b,hidden,open_c]
    if index==9:glyphs.append(_glyph(3,6,[]))
    if index>=2:rng.shuffle(glyphs)
    needed=sum(x['height'] for x in glyphs)+len(glyphs)-1
    height=30 if index==9 else max(needed,rng.randint(27,29))
    width=30 if index==9 else rng.randint(25,29)
    wall=rng.randint(max(x['width'] for x in glyphs)+2,width-4)
    gaps=[0]*(len(glyphs)+1)
    for _ in range(height-needed):gaps[rng.randrange(len(gaps))]+=1
    grid=[[6]*width for _ in range(height)]
    final=[[6]*width for _ in range(height)]
    for r in range(height):grid[r][wall]=final[r][wall]=5
    top=gaps[0];exposed=[];all_pockets=[];shifts=[]
    for i,glyph in enumerate(glyphs):
        max_left=wall-glyph['width']-(1 if index<2 else 0)
        left=rng.randint(0,max_left)
        if index==9 and glyph is b:left=wall-glyph['width']
        landing=wall-glyph['width'];shifts.append(landing-left)
        for r,c in glyph['cells']:
            grid[top+r][left+c]=0;final[top+r][landing+c]=0
        for pocket in glyph['holes']:
            shifted={(top+r,landing+c) for r,c in pocket}
            all_pockets.append(shifted)
            if any(c==wall-2 for r,c in shifted):exposed.append(shifted)
        top+=glyph['height']+1+gaps[i+1]
    areas=[len(p) for p in exposed]
    if len(exposed)<3 or areas.count(max(areas))!=1:raise ValueError('nonunique largest exposed pocket')
    default=deepcopy(final);alternate=deepcopy(final)
    for dest,chosen in ((default,exposed),(alternate,[max(exposed,key=len)])):
        rows={r for p in chosen for r,c in p if c==wall-2}
        for r in rows:
            for c in range(wall+1,width):dest[r][c]=2
    pose=rng.randrange(8)
    grid=d4(grid,pose);default=d4(default,pose);alternate=d4(alternate,pose)
    # Independent flood-based solver checks the constructive geometry labels.
    if predict(grid,'all_exposed')!=default or predict(grid,'largest_exposed')!=alternate:
        raise ValueError('constructed cavities disagree with independent topology')
    return grid,default,alternate,{'pose':pose,'exposed_areas':areas,'all_pocket_areas':[len(p) for p in all_pockets],
                                  'shifts':shifts,'glyph_count':len(glyphs)}

@lru_cache(maxsize=128)
def _bank(seed):
    bank=[]
    for index in range(10):
        for attempt in range(30):
            scene=_scene(seed,index,attempt)
            if all(scene[0]!=old[0] for old in bank):bank.append(scene);break
        else:raise ValueError('distinct scene budget exhausted')
    return bank

def generate(seed,settings,demos=2,queries=4):
    policy=_settings(settings)
    if type(seed) is not int or seed<0:raise ValueError('seed must be a nonnegative integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be an integer in 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be an integer in 1..4')
    scenes=_bank(seed);order=list(range(4));random.Random(f'6e453dd6:presentation:{seed}').shuffle(order)
    def pair(s):return {'input':deepcopy(s[0]),'output':deepcopy(s[1 if policy=='all_exposed' else 2])}
    return {'train':[pair(s) for s in scenes[:demos]],'test':[pair(scenes[6+i]) for i in order[:queries]],
            'program_solution':program(settings),'private':{'seed':seed,'settings':dict(settings),'query_permutation':order,
            'scene_certificates':[s[3] for s in scenes]}}

def public_turn(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],'test':[{'input':deepcopy(episode['test'][index]['input'])}]}
