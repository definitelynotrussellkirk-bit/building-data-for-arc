"""Native stamp-mask family. Claims are independently re-executed by qualification.

The retained prototype and exact Racket sources are reused. Input construction
is setting-neutral; the six-demo and four-query banks are independent, and query
presentation is shuffled before a requested prefix is selected.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve().parent
TASK = '0f5fbe0de38e'
PARAMETER = 'stamp_mask'
SETTINGS = ('fill_cells', 'template_holes')

def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

PROTO = _load(HERE/'prototype.py', 'stamp_retained_prototype')

@lru_cache(maxsize=1)
def generator():
    return load_selected_generator(TASK, root=find_root(__file__))[0]

def validate(settings):
    if not isinstance(settings, dict) or set(settings) != {PARAMETER} or settings[PARAMETER] not in SETTINGS:
        raise ValueError('settings must contain only stamp_mask=fill_cells|template_holes')
    return settings[PARAMETER]

def program(settings):
    setting = validate(settings)
    return PROTO.retained_rule_path(setting).read_text(encoding='utf-8')

def inspect(grid):
    facts, errors = generator()._analyze(grid)
    if errors:
        raise ValueError('; '.join(errors))
    return facts

def predict(grid, settings, rival=None):
    setting = validate(settings)
    if rival == 'other_setting':
        setting = SETTINGS[1 - SETTINGS.index(setting)]
    facts = inspect(grid); gen = generator()
    cells = facts['template_spec']['fill' if setting == 'fill_cells' else 'holes']
    if rival == 'bounding_box': cells = [(r,c) for r in range(3) for c in range(3)]
    pairs = list(facts['pairs'])
    if rival == 'first_pair': pairs = pairs[:1]
    if rival == 'first_two': pairs = pairs[:2]
    if rival == 'unit_only': pairs = [p for p in pairs if p['scale']==1]
    out = deepcopy(grid)
    for pair in pairs:
        p = pair['placement']; scale = pair['scale']
        for cell in cells:
            r,c = gen._xform(cell, 0 if rival == 'no_rotation' else p['transform'])
            for dr in range(scale):
                for dc in range(scale):
                    rr,cc = p['sr']+r*scale+dr, p['sc']+c*scale+dc
                    if 0<=rr<len(out) and 0<=cc<len(out[0]) and out[rr][cc]==facts['bg_color']:
                        out[rr][cc] = facts['fill_color']
    return out

def _stress(rng, colors):
    gen = generator(); bg,fill,a,b = colors
    profile = 'wedge5_main'; spec = gen._template_spec(profile)
    out = [[bg]*30 for _ in range(30)]
    for r,row in enumerate(gen.TEMPLATE_PROFILES[profile]):
        for c,s in enumerate(row):
            if s!='.': out[27+r][c]={'F':fill,'A':a,'B':b}[s]
    for top,left,scale,relation in [(0,0,3,'opposite'),(0,24,2,'same'),(27,27,1,'opposite')]:
        offsets = gen._marker_offsets(spec['marker_diag'],relation,scale)
        roles = [a,b]; rng.shuffle(roles)
        for (dr,dc),color in zip(offsets,roles):
            for r in range(top+dr,top+dr+scale):
                for c in range(left+dc,left+dc+scale): out[r][c]=color
    inspect(out)
    return out

@lru_cache(maxsize=32)
def _input_bank(seed):
    gen=generator()
    cases=[('wedge5_main',(1,2,3),'mixed'),('cross4_anti',(1,2),'same'),
           ('ring6_anti',(3,),'opposite'),('plus5_main',(1,1),'mixed'),
           ('wedge5_main',(2,),'same'),('cross4_anti',(1,),'opposite'),
           ('plus5_main',(1,2,3),'mixed'),('ring6_anti',(1,2),'opposite'),
           ('wedge5_main',(3,),'opposite')]
    grids=[]
    for i,(profile,scales,orientation) in enumerate(cases):
        rng=random.Random(f'{TASK}:scene:{seed}:{i}')
        colors=rng.sample(range(10),4)
        h,w=rng.randint(22,27),rng.randint(22,27)
        grid=gen._build_scene(h,w,*colors,profile,scales,orientation,rng)
        inspect(grid); grids.append(grid)
    rng=random.Random(f'{TASK}:stress:{seed}')
    grids.append(_stress(rng,rng.sample(range(10),4)))
    if len({json.dumps(g) for g in grids})!=10: raise ValueError('duplicate scene in bank')
    return tuple(tuple(tuple(row) for row in g) for g in grids)

@lru_cache(maxsize=64)
def _pair_bank(seed, setting):
    settings={PARAMETER:setting}
    pairs=[]
    for frozen in _input_bank(seed):
        grid=[list(r) for r in frozen]
        pairs.append({'input':grid,'output':predict(grid,settings)})
    return pairs

def generate(seed, settings, demos, queries):
    setting=validate(settings)
    if type(seed) is not int: raise ValueError('seed must be an exact integer')
    if type(demos) is not int or not 2<=demos<=6: raise ValueError('demos must be an integer in 2..6')
    if type(queries) is not int or not 1<=queries<=4: raise ValueError('queries must be an integer in 1..4')
    pairs=_pair_bank(seed,setting)
    order=list(range(4)); random.Random(f'{TASK}:presentation:{seed}').shuffle(order)
    return {'train':deepcopy(pairs[:demos]),'test':deepcopy([pairs[6+i] for i in order[:queries]]),
            'program_solution':program(settings),'settings':dict(settings),'seed':seed,
            'query_source_indices':order[:queries]}

def public_turn(episode, index):
    if type(index) is not int or not 0<=index<len(episode['test']): raise ValueError('query index out of range')
    return {'train':deepcopy(episode['train']), 'test':[{'input':deepcopy(episode['test'][index]['input'])}]}

def rival_programs(settings):
    source=program(settings)
    block=PROTO._CANONICAL_MASK_BLOCK if validate(settings)=='fill_cells' else PROTO._HOLE_MASK_BLOCK
    bbox='''     (define fill-cells
       (for*/list ((r (range 0 th)) (c (range 0 tw))) (list r c fill-color)))'''
    return {
        'other_setting':program({PARAMETER:SETTINGS[1-SETTINGS.index(validate(settings))]}),
        'first_pair':source.replace('((pair (in-list pairs)))','((pair (in-list (take pairs (min 1 (length pairs))))))'),
        'first_two':source.replace('((pair (in-list pairs)))','((pair (in-list (take pairs (min 2 (length pairs))))))'),
        'unit_only':source.replace('((pair (in-list pairs)))','((pair (in-list (filter (lambda (p) (= (obj-h (first p)) 1)) pairs))))'),
        'no_rotation':source.replace('(map (lambda (p) (xform p t)) fill-cells)', '(map (lambda (p) (list (first p) (second p))) fill-cells)'),
        'bounding_box':source.replace(block,bbox),
    }

def dump(path, data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')

def audit(out, seeds=20, execute=True):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    report={'task_id':TASK,'requests':0,'pair_instances':0,'matched_inputs':0,'public_turns':0,
            'unique_inputs':0,'failures':[],'rivals':[],'racket_evaluations':0,
            'scope':'finite seed/count/rival audit, not universal identifiability or training admission'}
    seen=set()
    for seed in range(seeds):
        full={s:generate(seed,{PARAMETER:s},6,4) for s in SETTINGS}
        for demos in range(2,7):
            for queries in range(1,5):
                episodes={s:generate(seed,{PARAMETER:s},demos,queries) for s in SETTINGS}
                a,b=(episodes[s] for s in SETTINGS)
                assert [p['input'] for p in a['train']+a['test']]==[p['input'] for p in b['train']+b['test']]
                report['matched_inputs']+=1
                for s,ep in episodes.items():
                    assert ep['train']==full[s]['train'][:demos] and ep['test']==full[s]['test'][:queries]
                    assert len({json.dumps(p['input']) for p in ep['train']+ep['test']})==demos+queries
                    for p in ep['train']+ep['test']: seen.add(json.dumps(p['input']))
                    for i in range(queries):
                        view=public_turn(ep,i)
                        assert set(view)=={'train','test'} and set(view['test'][0])=={'input'}
                        assert len(view['test'])==1
                        report['public_turns']+=1
                    report['requests']+=1; report['pair_instances']+=demos+queries
    report['unique_inputs']=len(seen)
    if execute:
        root=find_root(__file__)
        for setting in SETTINGS:
            settings={PARAMETER:setting}; ep=generate(0,settings,2,4)
            pairs=ep['train']+ep['test']; inputs=[p['input'] for p in pairs]
            receipt=PROTO.execute_program(program(settings),inputs,root=root)
            assert receipt['test_outputs']==[p['output'] for p in pairs]
            report['racket_evaluations']+=len(inputs)+1
            dump(out/'private'/f'{setting}-selected.json',{'episode':ep,'receipt':receipt})
            for i in range(4):
                public=public_turn(ep,i)
                blob=(json.dumps(public,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
                name=hashlib.sha256(blob).hexdigest()+'.json'
                (out/'public').mkdir(exist_ok=True); (out/'public'/name).write_bytes(blob)
            for name,rule in rival_programs(settings).items():
                receipt=PROTO.execute_program(rule,inputs,root=root)
                expected=[predict(g,settings,name) for g in inputs]
                assert receipt['test_outputs']==expected, f'Racket/Python disagreement: {name}'
                diffs=[i for i,(p,y) in enumerate(zip(pairs,expected)) if p['output']!=y]
                row={'setting':setting,'name':name,'demo_distinguished':any(i<2 for i in diffs),
                     'query_disagreements':[i-2 for i in diffs if i>=2]}
                report['rivals'].append(row)
                if not row['demo_distinguished']: report['failures'].append(row)
                report['racket_evaluations']+=len(inputs)+1
                dump(out/'private'/f'{setting}-{name}.json',{'program':rule,'receipt':receipt,'differences':diffs})
    dump(out/'report.json',report)
    if report['failures']: raise AssertionError(report['failures'])
    return report
