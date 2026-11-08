"""Boolean intersection followed by connected-overlap-guided top-object recovery.

Input grammar: equal aligned panels, background zero, distinct panel colors,
one full-width divider (5), all four occupancy states. The alternative picks
the unique largest FOUR-connected overlap, then recovers its containing top
object. Claims are independently re-executed through protected Racket.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

HERE=Path(__file__).resolve().parent
TASK='ba5056d6102e'
PARAMETER='overlap_policy'
SETTINGS=('intersection','recover_top')
COLORS=(1,2,3,4,6,7,9)
DIR4=((-1,0),(0,-1),(0,1),(1,0))

def validate(settings):
    if not isinstance(settings,dict) or set(settings)!={PARAMETER} or settings[PARAMETER] not in SETTINGS:
        raise ValueError('settings must contain only overlap_policy=intersection|recover_top')
    return settings[PARAMETER]

def canonical():
    return (HERE/'canonical.rkt').read_text(encoding='utf-8')

def _body():
    from puzzle_generators.rule_wrap import strip_rule_wrapper
    return strip_rule_wrapper(canonical())

def _recovery_rule(mode=None):
    parts='(objects-8 overlap 0)' if mode=='eight_connected' else '(objects overlap 0)'
    score='(* (obj-h o) (obj-w o))' if mode=='bbox_overlap' else '(obj-size o)'
    target='(find-first (lambda (o) (member seed (obj-cells o))) (objects top 0))'
    if mode=='largest_top':target='(first (sort-by (objects top 0) (lambda (o) (- 0 (obj-size o)))))'
    elif mode=='smallest_top':target='(first (sort-by (objects top 0) obj-size))'
    elif mode=='first_top':target='(first (objects top 0))'
    elif mode=='last_top':target='(last (objects top 0))'
    elif mode=='total_overlap':target='''(first (sort-by (objects top 0)
      (lambda (o) (- 0 (for/sum ((p (obj-cells o)))
        (if (not (= (at overlap (first p) (second p)) 0)) 1 0))))))'''
    elif mode=='largest_overlap_only':target='winner'
    return f'''(rule!
 ;; First compute the exact canonical intersection. Its largest connected
 ;; overlap selects a whole TOP object; recover that object's missing cells.
 (lambda (g)
   (let* ((overlap {_body()})
          (top (take g (rows overlap)))
          (parts {parts})
          (winner (first (sort-by parts (lambda (o) (- 0 {score})))))
          (seed (first (obj-cells winner)))
          (target {target}))
     (grid-from-fn (rows overlap) (cols overlap)
       (lambda (r c) (if (member (list r c) (obj-cells target)) 8 0))))))'''

def program(settings):
    return canonical() if validate(settings)=='intersection' else _recovery_rule()

def _boolean_rule(mode):
    expr={'union':'(or a b)','xor':'(not (equal? a b))','top_only':'a','bottom_only':'b'}[mode]
    return f'''(rule! (lambda (g)
      (let* ((half (/ (- (rows g) 1) 2)) (top (take g half))
             (bottom (drop g (+ half 1))))
        (grid-from-fn half (cols g) (lambda (r c)
          (let ((a (not (= (at top r c) 0))) (b (not (= (at bottom r c) 0))))
            (if {expr} 8 0)))))))'''

def rival_programs(settings):
    setting=validate(settings)
    rivals={'other_setting':program({PARAMETER:SETTINGS[1-SETTINGS.index(setting)]})}
    names=('union','xor','top_only','bottom_only') if setting=='intersection' else (
        'largest_top','smallest_top','first_top','last_top','total_overlap',
        'eight_connected','bbox_overlap','largest_overlap_only')
    for name in names:rivals[name]=_boolean_rule(name) if setting=='intersection' else _recovery_rule(name)
    # Bounded total rivals for the two teaching defects reproduced in review.
    if setting=='recover_top':
        rivals['first_three']=program(settings).replace('(parts (objects overlap 0))',
            "(parts (filter (lambda (o) (for/or ((parent (take (objects top 0) (min 3 (length (objects top 0)))))) (member (first (obj-cells o)) (obj-cells parent)))) (objects overlap 0)))")
    else:
        rivals['first_three']=f'''(rule! (lambda (g)
          (let* ((overlap {_body()}) (top (take g (rows overlap))))
            (grid-from-fn (rows overlap) (cols overlap) (lambda (r c)
              (if (and (= (at overlap r c) 8)
                  (for/or ((o (take (objects top 0) (min 3 (length (objects top 0))))))
                    (member (list r c) (obj-cells o)))) 8 0))))))'''
    from puzzle_generators.rule_wrap import wrap_rule
    chosen=wrap_rule(program(settings))
    rivals['six_guard']=f'''(rule! (lambda (g) (let ((overlap {_body()}))
      (if (any? (lambda (o) (= (obj-size o) 6)) (objects overlap 0))
          ({chosen} g)
          (grid-from-fn (rows overlap) (cols overlap) (lambda (r c) 0))))))''' 
    rivals['color3_guard']=f'''(rule! (lambda (g)
      (let* ((half (/ (- (rows g) 1) 2)) (top (take g half)))
        (if (any? (lambda (v) (= v 3)) (flatten top))
            (grid-from-fn half (cols g) (lambda (r c) 0))
            ({chosen} g)))))'''
    return rivals

def components(cells, diagonal=False):
    remaining=set(cells); result=[]
    dirs=DIR4+((-1,-1),(-1,1),(1,-1),(1,1)) if diagonal else DIR4
    while remaining:
        first=min(remaining);remaining.remove(first);queue=[first];part={first}
        while queue:
            r,c=queue.pop()
            for dr,dc in dirs:
                p=(r+dr,c+dc)
                if p in remaining:remaining.remove(p);part.add(p);queue.append(p)
        result.append(part)
    return result

def _parts(grid):
    if not isinstance(grid,list) or not grid or not isinstance(grid[0],list) or not grid[0]:raise ValueError('empty grid')
    w=len(grid[0]);h=(len(grid)-1)//2
    if len(grid)!=2*h+1 or h<1 or any(not isinstance(row,list) or len(row)!=w for row in grid):raise ValueError('unequal panels or ragged grid')
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row):raise ValueError('invalid colors')
    if grid[h]!=[5]*w:raise ValueError('missing divider')
    top={(r,c) for r in range(h) for c in range(w) if grid[r][c]!=0}
    bottom={(r,c) for r in range(h) for c in range(w) if grid[r+h+1][c]!=0}
    return h,w,top,bottom

def inspect(grid):
    h,w,top,bottom=_parts(grid); overlap=top&bottom;parts=components(overlap)
    sizes=sorted((len(p) for p in parts),reverse=True)
    if not sizes or (len(sizes)>1 and sizes[0]==sizes[1]):raise ValueError('overlap winner must be unique')
    winner=max(parts,key=len);parents=components(top)
    target=next(p for p in parents if winner<=p)
    return {'half_h':h,'width':w,'winning_overlap_size':len(winner),
        'overlap_sizes':sizes,'top_sizes':[len(p) for p in parents],
        'top_overlap_totals':[len(p&overlap) for p in parents],
        'winning_overlap':sorted(winner),'target_cells':sorted(target),
        'truth_table':{'00':h*w-len(top|bottom),'10':len(top-bottom),'01':len(bottom-top),'11':len(overlap)}}

def predict(grid, settings, rival=None):
    setting=validate(settings);h,w,top,bottom=_parts(grid);overlap=top&bottom
    if rival=='other_setting':setting=SETTINGS[1-SETTINGS.index(setting)];rival=None
    if rival=='first_three':overlap &= set().union(*components(top)[:3])
    if rival=='six_guard' and not any(len(p)==6 for p in components(overlap)):cells=set()
    elif rival=='color3_guard' and any(grid[r][c]==3 for r,c in top):cells=set()
    elif rival=='union':cells=top|bottom
    elif rival=='xor':cells=top^bottom
    elif rival=='top_only':cells=top
    elif rival=='bottom_only':cells=bottom
    elif setting=='intersection':cells=overlap
    else:
        parts=components(overlap,diagonal=rival=='eight_connected');parents=components(top)
        def score(p):
            if rival=='bbox_overlap':return (max(r for r,c in p)-min(r for r,c in p)+1)*(max(c for r,c in p)-min(c for r,c in p)+1)
            return len(p)
        winner=max(parts,key=score)
        if rival=='largest_top':cells=max(parents,key=len)
        elif rival=='smallest_top':cells=min(parents,key=len)
        elif rival=='first_top':cells=parents[0]
        elif rival=='last_top':cells=parents[-1]
        elif rival=='total_overlap':cells=max(parents,key=lambda p:len(p&overlap))
        elif rival=='largest_overlap_only':cells=winner
        else:cells=next(p for p in parents if min(winner) in p)
    return [[8 if (r,c) in cells else 0 for c in range(w)] for r in range(h)]

def _transform(top, overlap, code):
    def move(p):
        r,c=p
        if code>=4:c=3-c
        for _ in range(code%4):r,c=c,3-r
        return r,c
    mapped={move(p) for p in top};r0=min(r for r,c in mapped);c0=min(c for r,c in mapped)
    def norm(p):r,c=move(p);return r-r0,c-c0
    return {norm(p) for p in top},{norm(p) for p in overlap}

def _patterns(kind):
    overlap={(r,c) for r in range(2) for c in range(3)}
    if kind%4==0:target={(r,c) for r in range(3) for c in range(3)}-{(2,2)}
    elif kind%4==1:target=overlap|{(2,1)}
    elif kind%4==2:target={(r,c) for r in range(3) for c in range(4)}-{(2,3)}
    else:target={(r,c) for r in range(4) for c in range(4)}-{(3,3),(3,2),(2,3)}
    decoy={(r,c) for r in range(4) for c in range(4)}
    fragmented={(r,c) for r,c in decoy if (r+c)%2==0}
    elbow={(0,0),(1,0),(2,0),(2,1),(2,2)}
    other={(r,c) for r in range(3) for c in range(3)} if kind==1 else elbow|{(0,1),(1,1)}
    if kind==1:overlap=set(target)  # Seven connected overlaps, not a constant six-cell selector.
    return {'winner':(target,overlap),'decoy':(decoy,fragmented),'third':(other,elbow)}

def _scene(seed,index):
    rng=random.Random(f'{TASK}:scene:{seed}:{index}')
    stress=index==9;kind=0 if stress else index%4;patterns=_patterns(kind)
    h,w=(14,30) if stress else ((4,14) if index==0 else (rng.randint(4,9),rng.choice((14,19,24))))
    if index==1:h,w=4,24  # A fifth-parent winner must be visible by demo two.
    top=set();bottom=set();placements=[]
    if stress:
        plan=[('decoy',0,0,2),('winner',8,12,2),('third',0,24,2),('extra',10,0,1),('extra',10,26,1)]
    else:
        roles=['decoy','winner','third']+['extra']*((w+1)//5-3)
        if index==1:roles=['decoy','third','extra','extra','winner']
        elif index>1:rng.shuffle(roles)
        plan=[(role,0 if index in (0,1) else rng.randint(0,h-4),5*i,1) for i,role in enumerate(roles)]
    for role,r0,c0,scale in plan:
        if role=='extra':a={(r,c) for r in range(4) for c in range(4)}-{(0,3),(3,0)};b={(0,0),(0,1)}
        else:a,b=patterns[role]
        a,b=_transform(a,b,rng.randrange(8))
        def expand(cells):return {(r0+r*scale+dr,c0+c*scale+dc) for r,c in cells for dr in range(scale) for dc in range(scale)}
        a,b=expand(a),expand(b)
        assert all(0<=r<h and 0<=c<w for r,c in a)
        top.update(a);bottom.update(b);placements.append((role,a))
    free=sorted({(r,c) for r in range(h) for c in range(w)}-top)
    # Bottom-only distractions are restricted to original top zeros; they cannot
    # alter the overlap topology. Keep at least one 00 cell as well.
    bottom.update(rng.sample(free,max(1,len(free)//3)))
    top_color=3 if index==0 else (2 if index==1 else rng.choice(COLORS))
    bottom_color=3 if index==1 else rng.choice([c for c in COLORS if c!=top_color])
    grid=[[top_color if (r,c) in top else 0 for c in range(w)] for r in range(h)]+[[5]*w]+[[bottom_color if (r,c) in bottom else 0 for c in range(w)] for r in range(h)]
    info=inspect(grid)
    expected=next(a for role,a in placements if role=='winner')
    assert set(map(tuple,info['target_cells']))==expected
    assert all(info['truth_table'].values())
    return grid

@lru_cache(maxsize=32)
def _input_bank(seed):
    grids=[_scene(seed,i) for i in range(10)]
    if len({json.dumps(g) for g in grids})!=10:raise ValueError('duplicate input bank')
    return tuple(tuple(tuple(row) for row in g) for g in grids)

@lru_cache(maxsize=64)
def _pair_bank(seed,setting):
    result=[]
    for frozen in _input_bank(seed):
        g=[list(r) for r in frozen];result.append({'input':g,'output':predict(g,{PARAMETER:setting})})
    return result

def generate(seed,settings,demos,queries):
    setting=validate(settings)
    if type(seed) is not int:raise ValueError('seed must be an exact integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be an integer in 2..6')
    if type(queries) is not int or not 1<=queries<=4:raise ValueError('queries must be an integer in 1..4')
    bank=_pair_bank(seed,setting);order=list(range(4));random.Random(f'{TASK}:presentation:{seed}').shuffle(order)
    return {'train':deepcopy(bank[:demos]),'test':deepcopy([bank[6+i] for i in order[:queries]]),
            'program_solution':program(settings),'settings':dict(settings),'seed':seed,'query_source_indices':order[:queries]}

def public_turn(episode,index):
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('query index out of range')
    return {'train':deepcopy(episode['train']),'test':[{'input':deepcopy(episode['test'][index]['input'])}]}

def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def audit(out,seeds=20,execute=True):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    report={'task_id':TASK,'requests':0,'pair_instances':0,'matched_inputs':0,'public_turns':0,'unique_inputs':0,
            'failures':[],'rivals':[],'racket_evaluations':0,'scope':'finite seeds/counts/authored rivals; no owner acceptance or training admission'}
    seen=set()
    for seed in range(seeds):
        full={s:generate(seed,{PARAMETER:s},6,4) for s in SETTINGS}
        for demos in range(2,7):
            for queries in range(1,5):
                ep={s:generate(seed,{PARAMETER:s},demos,queries) for s in SETTINGS}
                a,b=(ep[s] for s in SETTINGS)
                assert [p['input'] for p in a['train']+a['test']]==[p['input'] for p in b['train']+b['test']]
                report['matched_inputs']+=1
                for setting,e in ep.items():
                    assert e['train']==full[setting]['train'][:demos] and e['test']==full[setting]['test'][:queries]
                    assert len({json.dumps(p['input']) for p in e['train']+e['test']})==demos+queries
                    for p in e['train']+e['test']:seen.add(json.dumps(p['input']))
                    for i in range(queries):
                        view=public_turn(e,i);assert set(view)=={'train','test'} and set(view['test'][0])=={'input'}
                        report['public_turns']+=1
                    report['requests']+=1;report['pair_instances']+=demos+queries
    report['unique_inputs']=len(seen)
    if execute:
        from arcpuzzles.parametric_worker import _real_evaluator
        from reviewer_support import find_root,public_challenge_bytes
        root=find_root(__file__)
        # Native libraries and isolated task-test runtimes have different layouts.
        runtime=root if (root/'arc_repl/racket_bridge.py').is_file() else root/'shared/runtime'
        apply,identity,bridge=_real_evaluator(runtime)
        report['racket']=identity;publics={}
        try:
            for setting in SETTINGS:
                settings={PARAMETER:setting};ep=generate(0,settings,2,4);pairs=ep['train']+ep['test']
                actual=[apply(program(settings),p['input']) for p in pairs]
                assert actual==[p['output'] for p in pairs]
                report['racket_evaluations']+=len(pairs)
                dump(out/'private'/f'{setting}-selected.json',{'episode':ep,'outputs':actual,'racket':identity})
                for i in range(4):
                    blob=public_challenge_bytes(public_turn(ep,i));publics[hashlib.sha256(blob).hexdigest()]=blob
                for name,rule in rival_programs(settings).items():
                    actual=[apply(rule,p['input']) for p in pairs]
                    expected=[predict(p['input'],settings,name) for p in pairs]
                    assert actual==expected, f'Racket/Python disagreement: {setting}/{name}'
                    diffs=[i for i,(p,y) in enumerate(zip(pairs,actual)) if p['output']!=y]
                    row={'setting':setting,'name':name,'demo_distinguished':any(i<2 for i in diffs),'query_disagreements':[i-2 for i in diffs if i>=2]}
                    report['rivals'].append(row)
                    if not row['demo_distinguished']:report['failures'].append(row)
                    report['racket_evaluations']+=len(pairs)
                    dump(out/'private'/f'{setting}-{name}.json',{'program':rule,'outputs':actual,'differences':diffs,'racket':identity})
        finally:bridge.close()
        (out/'public').mkdir(exist_ok=True)
        for digest,blob in sorted(publics.items()):(out/'public'/f'{digest}.json').write_bytes(blob)
    dump(out/'report.json',report)
    if report['failures']:raise AssertionError(report['failures'])
    return report
