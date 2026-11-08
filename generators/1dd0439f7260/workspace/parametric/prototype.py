"""Row-column Cartesian-product with candidate-dependent beacon spokes.

Canonical `all` is preserved byte-for-byte. The two nearby variants first form
row-marker x column-marker intersections, remove 5-blocked candidates, select
an extreme-distance pivot relative to the interior 4 beacon, and paint only
candidate sites sharing that pivot's row/column. This is an input-dependent
set -> pivot -> spokes pipeline, not a fixed-location paint.
"""
from __future__ import annotations

import json
import random
from reviewer_support import canonical_path,find_root

TASK_ID = "1dd0439f7260"
ROOT = find_root(__file__)
MODES = ("all", "closest_spokes", "farthest_spokes")


def canonical_source(root=ROOT):
    matches = []
    with canonical_path(root).open(encoding='utf8') as f:
        for line in f:
            if line.strip():
                row=json.loads(line)
                if row.get('task_id')==TASK_ID:
                    matches.append(row.get('program_solution'))
    if len(set(matches))!=1 or not matches or not matches[0]:
        raise ValueError('unique canonical program not found')
    return matches[0]


def _extension(mode):
    operator = '<' if mode=='closest_spokes' else '>'
    return '''(let* ((all-hits (for*/list ([r rs] [c cs]) (list r c)))
           (eligible (filter (lambda (p) (not (= (at g (first p) (second p)) 5))) all-hits))
           (beacons (for*/list ([r (range 1 h)] [c (range 1 w)]
                                #:when (= (at g r c) 4)) (list r c)))
           (beacon (first beacons))
           (distance (lambda (p)
               (let* ((dr (- (first p) (first beacon)))
                      (dc (- (second p) (second beacon))))
                   (+ (* dr dr) (* dc dc)))))
           (pivot (for/fold ([best (first eligible)]) ([p (rest eligible)])
                    (if (%s (distance p) (distance best)) p best)))
           (spokes (filter (lambda (p)
                       (or (= (first p) (first pivot))
                           (= (second p) (second pivot)))) eligible)))
     (paint-cells g spokes 3))''' % operator


def program_for(mode,root=ROOT):
    if type(mode) is not str or mode not in MODES: raise ValueError('unsupported mode')
    canonical=canonical_source(root)
    if mode=='all': return canonical
    needle='(paint-cells g (for*/list ([r rs] [c cs]) (list r c)) 3)'
    if canonical.count(needle)!=1:raise ValueError('canonical Racket paint expression changed')
    return canonical.replace(needle,_extension(mode))


def _key(grid): return tuple(tuple(r) for r in grid)


def _labels(g,rows,cols,beacon):
    universe=[(r,c) for r in rows for c in cols]
    eligible=[p for p in universe if g[p[0]][p[1]]!=5]
    if not eligible:raise ValueError('all intersections blocked')
    dist=lambda p:(p[0]-beacon[0])**2+(p[1]-beacon[1])**2
    close=min(eligible,key=dist)
    far=max(eligible,key=dist)
    results={}
    for mode in MODES:
        output=[line[:] for line in g]
        if mode=='all':hits=universe
        else:
            pivot=close if mode=='closest_spokes' else far
            hits=[p for p in eligible if p[0]==pivot[0] or p[1]==pivot[1]]
        for r,c in hits:output[r][c]=3
        results[mode]=output
    return results,close,far,eligible


def _sample(seed,index,total,difficulty):
    rng=random.Random(f'cartesian-spokes:{seed}:{index}:{total}:{difficulty}')
    large=index==total-1
    if large:h,w=30,30
    elif difficulty=='easy':h,w=rng.randint(7,10),rng.randint(7,10)
    elif difficulty=='hard':h,w=rng.randint(10,19),rng.randint(9,19)
    else:h,w=rng.randint(8,15),rng.randint(8,15)
    for attempt in range(200):
        g=[[0]*w for _ in range(h)]
        nrs=rng.randint(3,min(h-1, 14 if large else 6))
        ncs=rng.randint(3,min(w-1, 14 if large else 6))
        rows=sorted(rng.sample(range(1,h),nrs))
        cols=sorted(rng.sample(range(1,w),ncs))
        for r in rows:g[r][0]=2
        for c in cols:g[0][c]=1
        intersections=[(r,c) for r in rows for c in cols]
        blockers=rng.sample(intersections, rng.randint(1,max(1,min(len(intersections)//5,24))))
        for r,c in blockers:g[r][c]=5
        free=[(r,c) for r in range(1,h) for c in range(1,w)
              if (r,c) not in intersections]
        if not free:continue
        rng.shuffle(free)
        for beacon in free[:min(len(free),150)]:
            candidate=[line[:] for line in g]
            candidate[beacon[0]][beacon[1]]=4
            results,nearest,farthest,eligible=_labels(candidate,rows,cols,beacon)
            # No distance ties, and the two pivots differ in both axes.
            distances=sorted((p[0]-beacon[0])**2+(p[1]-beacon[1])**2 for p in eligible)
            if len(distances)<2 or distances[0]==distances[1] or distances[-1]==distances[-2]:continue
            if nearest[0]==farthest[0] or nearest[1]==farthest[1]:continue
            if len({_key(v) for v in results.values()})!=3:continue
            # Distractors at non-candidate sites. They persist in all outputs.
            background=[p for p in free if p!=beacon]
            rng.shuffle(background)
            for j,(rr,cc) in enumerate(background[:min(len(background),2+(index%5) if not large else 45)]):
                candidate[rr][cc]=6 if j%2==0 else 7
            results,nearest,farthest,eligible=_labels(candidate,rows,cols,beacon)
            if len({_key(v) for v in results.values()})!=3:
                raise AssertionError('a distractor changed a candidate label')
            assert (len(candidate),len(candidate[0]))==(h,w)
            return candidate,results,nearest,farthest
    raise RuntimeError(f'cannot create a distinguishing row-column lesson {seed=} {index=}')


def generate_claims(seed,mode,*,demos=3,queries=4,difficulty='medium',root=ROOT):
    if type(seed) is not int or seed<0:raise ValueError('seed must be >=0 exact integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or queries!=4:raise ValueError('queries must equal 4')
    if type(mode) is not str or mode not in MODES:raise ValueError('invalid mode')
    if difficulty not in ('easy','medium','hard'):raise ValueError('invalid difficulty')
    examples=[]
    for i in range(demos+queries):
        grid,outputs,_,_=_sample(seed,i,demos+queries,difficulty)
        examples.append({'input':grid,'output':outputs[mode]})
    if len({json.dumps(p['input'],separators=(',',':')) for p in examples})!=len(examples):
        raise AssertionError('duplicate visible queries or demonstrations')
    return {'train':examples[:demos],'test':examples[demos:],
            'program_solution':program_for(mode,root)}


def self_audit(seed=11,demos=2,difficulty='medium'):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    bank={mode:generate_claims(seed,mode,demos=demos,difficulty=difficulty) for mode in MODES}
    with RacketBridge() as bridge:
        for mode,episode in bank.items():
            fn=wrap_rule(episode['program_solution'])
            for i,pair in enumerate(episode['train']+episode['test']):
                bridge.define_grid('g',pair['input'])
                actual=bridge.eval_text(f'({fn} g)')
                if actual!=pair['output']:
                    raise AssertionError(f'Racket disagreement mode={mode}, pair={i}')
    # Avoid confounding input markings and beacon presence with the episode mode:
    # all settings use exactly the same generated inputs for matching seed/count.
    return {'status':'passed','seed':seed,'demos':demos,'queries':4,
            'modes':list(MODES),'racket_evaluations':len(MODES)*(demos+4),
            'large_input':[30,30], 'input_mode_independent':True,
            'per_example_settings_distinguishable':True}

if __name__=='__main__':
    print(json.dumps(self_audit(),sort_keys=True))
