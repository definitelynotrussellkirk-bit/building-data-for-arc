"""Forward/inverse relation transfer, with setting-neutral input generation.

Canonical geometry helpers are imported from this task's exact generator path.
No production source is changed; labels are claims re-executed by qualification.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import random

TASK='155cf6b30713'
HOME=Path(__file__).resolve().parent
DIRECTIONS=('forward','inverse')
CODES=('id','r1','r2','r3','fh','fv','tr','atr')
INVERSE={'id':'id','r1':'r3','r2':'r2','r3':'r1','fh':'fh','fv':'fv','tr':'tr','atr':'atr'}
_spec=importlib.util.spec_from_file_location('_native_analogy_base_'+TASK,HOME.parents[1]/'generator.py')
base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(base)
transform=base._xform_grid
support=base._support


def _integer(value,name,low,high):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in [{low}, {high}]')
    return value


def _settings(settings):
    if type(settings) is not dict or set(settings)!={'direction'}:
        raise ValueError('settings must contain exactly direction')
    direction=settings['direction']
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError(f'direction must be one of {DIRECTIONS}')
    return direction


def program(settings):
    direction=_settings(settings)
    canonical=(HOME/'canonical.rkt').read_text()
    if direction=='forward':return canonical
    anchor='(tq (apply-transform-name name query))'
    replacement="""(tq (apply-transform-name
      (cond ((equal? name 'rot90) 'rot270)
            ((equal? name 'rot270) 'rot90) (else name)) query))"""
    if canonical.count(anchor)!=1 or canonical.count('(list a b)')!=1:
        raise ValueError('canonical transfer bindings changed; review required')
    return canonical.replace(anchor,replacement).replace('(list a b)','(list b a)')


def counterfactual_program():
    source=program({'direction':'inverse'})
    anchor='(tex (apply-transform-name name ex-in))'
    if source.count(anchor)!=1:raise ValueError('alignment binding changed')
    return source.replace(anchor,'(tex ex-in)')


def execute(bridge,source,grid):
    # Public runtime wrapper; no private worker entry point or surrogate labels.
    from puzzle_generators.rule_wrap import wrap_rule
    from reviewer_support import normalize_grid
    bridge.define_grid('__analogy_input__',grid)
    return normalize_grid(bridge.eval_text(f'({wrap_rule(source)} __analogy_input__)'))


def split_panels(grid):
    width=(len(grid[0])-2)//3
    return [[row[i*(width+1):i*(width+1)+width] for row in grid] for i in range(3)]


def infer(grid):
    ex_in,ex_out,_=split_panels(grid)
    wanted=support(ex_out)
    matches=[code for code in CODES if support(transform(ex_in,code))==wanted]
    if not matches:raise ValueError('no exact-position support relation')
    code=matches[0]
    return code,base._mapping_for(ex_in,ex_out,code)


def input_errors(grid):
    if type(grid) is not list or not grid or any(type(row) is not list for row in grid):
        return ['expected nonempty list rows']
    if not grid[0] or any(len(row)!=len(grid[0]) for row in grid):
        return ['ragged or empty grid']
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row):
        return ['expected exact integer colors 0..9']
    h,total=len(grid),len(grid[0]);w=(total-2)//3
    if not 4<=h<=30 or not 4<=w<=9 or total not in (3*w+2,3*w+3):
        return ['expected three 4..9-wide panels, height 4..30, optional closing divider']
    dividers=[w,2*w+1]+([3*w+2] if total==3*w+3 else [])
    if any(grid[r][c]!=5 for r in range(h) for c in dividers):
        return ['separator columns must be color 5']
    ex_in,ex_out,query=split_panels(grid)
    if any(v==5 for panel in (ex_in,ex_out,query) for row in panel for v in row):
        return ['color 5 is reserved for dividers in this native grammar']
    matches=[c for c in CODES if support(transform(ex_in,c))==support(ex_out)]
    if len(matches)!=1:return ['example support does not identify a unique transform']
    try:
        _,mapping=infer(grid)
    except ValueError as error:return [str(error)]
    if len(mapping)<3 or set(mapping)!=set(mapping.values()):
        return ['example must demonstrate a permutation of at least three colors']
    if len(set(mapping.values()))!=len(mapping):return ['map not invertible']
    qcolors={v for row in query for v in row if v}
    if not (qcolors & set(mapping)) or not (qcolors-set(mapping)):
        return ['query must mix mapped and unmapped colors']
    return []


def _map(grid,mapping,drop=False):
    return [[mapping.get(v,0 if drop and v else v) for v in row] for row in grid]


def predict(grid,direction):
    if direction not in DIRECTIONS:raise ValueError('unknown direction')
    code,mapping=infer(grid)
    if direction=='inverse':
        code=INVERSE[code];mapping={b:a for a,b in mapping.items()}
    return _map(transform(split_panels(grid)[2],code),mapping)


def _rng(seed,split,index):
    raw=hashlib.sha256(f'{TASK}:native-v1:{seed}:{split}:{index}'.encode()).digest()
    return random.Random(int.from_bytes(raw,'big'))


def _panel(rng,h,w,colors,count,*,corners=False):
    positions=[(r,c) for r in range(h) for c in range(w)]
    forced={(0,0),(0,w-1),(h-1,0),(h-1,w-1)} if corners else set()
    allowed=[p for p in positions if p not in forced]
    # Finite local geometry search only. The deterministic fallback also has
    # full exact-position D4 uniqueness; a missed bound fails rather than loops.
    for attempt in range(32):
        cells=sorted(forced|set(rng.sample(allowed,count-len(forced))))
        if attempt==31 and not corners:
            cells=[(0,0),(1,0),(1,1),(2,1),(3,1),(3,2)]
        palette=[colors[i%len(colors)] for i in range(len(cells))]
        rng.shuffle(palette)
        panel=[[0]*w for _ in range(h)]
        for (r,c),color in zip(cells,palette):panel[r][c]=color
        if len({support(transform(panel,c)) for c in CODES})==8:
            return panel
    raise ValueError('bounded asymmetric-panel construction exhausted')


def scene(seed,split,index):
    rng=_rng(seed,split,index)
    if split=='train' and index<2:
        h=w=(4 if index==0 else 6);closing=False
        code=('r1','fh')[index];num_colors=3;offset=(1,2)[index]
    elif split=='test':
        h,w=((4,4),(7,7),(9,9),(30,9))[index]
        closing=index==3;num_colors=rng.choice((3,4));offset=rng.randrange(1,num_colors)
        code=rng.choice(('r2','fh','fv') if h!=w else CODES)
    else:
        h=w=rng.randint(4,9);closing=False
        num_colors=rng.choice((3,4));offset=rng.randrange(1,num_colors);code=rng.choice(CODES)
    available=[1,2,3,4,6,7,8,9]
    palette=rng.sample(available,num_colors+1)
    colors=sorted(palette[:-1]);unmapped=palette[-1]
    mapping={c:colors[(i+offset)%num_colors] for i,c in enumerate(colors)}
    stress=(h==30)
    if split=='train' and index==0:
        ex_in=[[0]*w for _ in range(h)]
        # Full-source alignment is essential: this support and its clockwise
        # image are disjoint. Histogram counts tie across all three colors.
        for (r,c),v in zip(((0,0),(1,0),(1,1)),rng.sample(colors,3)):ex_in[r][c]=v
    else:
        n=(108 if stress else rng.randint(max(num_colors,6),max(6,h*w//2)))
        ex_in=_panel(rng,h,w,colors,n,corners=stress)
    ex_out=_map(transform(ex_in,code),mapping)
    qcount=94 if stress else rng.randint(max(6,num_colors+1),max(6,h*w//2))
    query=_panel(rng,h,w,colors+[unmapped],qcount,corners=stress)
    grid=[a+[5]+b+[5]+q+([5] if closing else []) for a,b,q in zip(ex_in,ex_out,query)]
    errors=input_errors(grid)
    if errors:raise RuntimeError('constructed grammar failure: '+str(errors))
    return grid


def generate(seed,settings,demos,queries):
    direction=_settings(settings)
    _integer(seed,'seed',0,2**63-1);_integer(demos,'demos',2,6);_integer(queries,'queries',1,4)
    ep={'settings':dict(settings),'program_solution':program(settings)}
    for split,count in (('train',demos),('test',queries)):
        ep[split]=[]
        for i in range(count):
            g=scene(seed,split,i);ep[split].append({'input':g,'output':predict(g,direction)})
    return ep


def public_turn(episode,index):
    _integer(index,'query index',0,len(episode['test'])-1)
    return {'train':[{'input':deepcopy(p['input']),'output':deepcopy(p['output'])} for p in episode['train']],
            'test':[{'input':deepcopy(episode['test'][index]['input'])}]}


def _unaligned_map(grid,inverse):
    source,target,_=split_panels(grid)
    result={}
    for row_a,row_b in zip(source,target):
        for a,b in zip(row_a,row_b):
            if a and b:
                x,y=(b,a) if inverse else (a,b)
                result.setdefault(x,y)
    return result


def rival_predictions(grid,direction):
    inverse=direction=='inverse'
    code,mapping=infer(grid);a,b,q=split_panels(grid)
    selected=INVERSE[code] if inverse else code
    selected_map={b:a for a,b in mapping.items()} if inverse else mapping
    results={f'setting:{d}':predict(grid,d) for d in DIRECTIONS}
    for fixed in CODES:results['fixed_geometry:'+fixed]=_map(transform(q,fixed),selected_map)
    transformed=transform(q,selected)
    results['geometry_only']=transformed
    results['recolor_only']=_map(q,selected_map)
    results['query_unchanged']=deepcopy(q)
    results['drop_unmapped']=_map(transformed,selected_map,drop=True)
    results['map_before_alignment']=_map(transformed,_unaligned_map(grid,inverse))
    results['forward_geometry']=_map(transform(q,code),selected_map)
    results['forward_palette']=_map(transformed,mapping)
    for delta in (-1,1):
        colors=sorted(mapping)
        by_rank={c:colors[(i+delta)%len(colors)] for i,c in enumerate(colors)}
        results['numeric_cycle:'+str(delta)]=_map(transformed,by_rank)
    ca,cb=(Counter(v for row in panel for v in row if v) for panel in (a,b))
    by_frequency=dict(zip(sorted(ca,key=lambda v:(ca[v],v)),sorted(cb,key=lambda v:(cb[v],v))))
    if inverse:by_frequency={v:k for k,v in by_frequency.items()}
    results['frequency_rank_mapping']=_map(transformed,by_frequency)
    # A conditional rule that never changes mixed mapped/unmapped queries.
    results['unmixed_only']=deepcopy(q)
    return results


def teaching_failures(episode):
    direction=episode['settings']['direction']
    train=[rival_predictions(p['input'],direction) for p in episode['train']]
    survivors=[name for name in train[0] if all(pred[name]==pair['output'] for pred,pair in zip(train,episode['train']))]
    failures=[]
    for i,pair in enumerate(episode['test']):
        predictions=rival_predictions(pair['input'],direction)
        for name in survivors:
            if predictions[name]!=pair['output']:failures.append({'rival':name,'query_index':i})
    return failures
