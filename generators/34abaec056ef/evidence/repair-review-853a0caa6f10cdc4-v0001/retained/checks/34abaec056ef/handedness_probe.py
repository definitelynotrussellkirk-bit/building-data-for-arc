"""Bounded visible-demo probe for a fixed-handedness local-frame rival.

Run through review.py run. Output is private and never overwritten.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import load_selected_generator


TASK = '34abaec056ef'
EXPECTED_SOURCE = 'bc8a2d1e37c1551c3f666c4b572f2a06fd3aafbb99f60dbb6de277388b7b9c2c'
ROOT = Path.cwd().resolve()
RUNTIME = ROOT/'shared/runtime'
RIVAL = '''(rule! (lambda (g)
  (let* ((origin (first (find-color g 2)))
         (tip (first (find-color g 3)))
         (dr (- (first tip) (first origin)))
         (dc (- (second tip) (second origin))))
    (grid-from-fn 3 3 (lambda (r c)
      (let* ((u (- c 1)) (v (- r 1))
             (rr (+ (first origin) (* u dr) (* v dc)))
             (cc (+ (second origin) (* u dc) (* v (- dr)))))
        (if (= (at g rr cc) 8) 8 0)))))))'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def locate(grid, color):
    points = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color]
    assert len(points)==1
    return points[0]


def mirror(grid, *, fixed_clockwise):
    origin, tip_x, tip_y = (locate(grid,c) for c in (2,3,4))
    dx = tuple(tip_x[i]-origin[i] for i in (0,1))
    dy = (dx[1],-dx[0]) if fixed_clockwise else tuple(tip_y[i]-origin[i] for i in (0,1))
    return [[8 if grid[origin[0]+(c-1)*dx[0]+(r-1)*dy[0]][origin[1]+(c-1)*dx[1]+(r-1)*dy[1]]==8 else 0
             for c in range(3)] for r in range(3)]


def run(out):
    if out.exists():
        raise FileExistsError(out)
    gen, source_path, source_hash = load_selected_generator(TASK)
    assert source_hash==EXPECTED_SOURCE
    programs = {v['program_solution'] for v in Catalog(ROOT).get(TASK)['variants']
                if isinstance(v.get('program_solution'),str)}
    assert len(programs)==1
    canonical=next(iter(programs))
    candidate_count = generated = 0
    selected = None
    for seed in range(410000,410256):
        candidate_count += 1
        train=[]
        for index in range(4):
            grid=gen.generate(seed,index,difficulty='easy')
            generated+=1
            assert gen.self_check(grid)==[]
            expected=mirror(grid,fixed_clockwise=False)
            assert expected==gen.rule_mirror(grid)
            if mirror(grid,fixed_clockwise=True)!=expected:
                break
            train.append({'input':grid,'output':expected,'sample_index':index})
        if len(train)!=4:
            continue
        grid=gen.generate(seed,4,difficulty='easy')
        generated+=1
        assert gen.self_check(grid)==[]
        expected=mirror(grid,fixed_clockwise=False)
        if mirror(grid,fixed_clockwise=True)==expected:
            continue
        query={'input':grid,'output':expected,'sample_index':4}
        selected=(seed,train,query)
        break
    assert selected is not None,'No counterexample within the explicit 256-seed bound'
    seed,train,query=selected
    hook=gen.lesson_identifiable(train,query)
    assert hook==[],hook
    record={'schema':'34abaec056ef-handedness-probe-v1','task_id':TASK,
            'generator_sha256':source_hash,'canonical_rule_hash':gen.RULE_HASH,
            'canonical_program':canonical,'canonical_program_sha256':sha(canonical.encode()),
            'rival_program':RIVAL,'rival_program_sha256':sha(RIVAL.encode()),
            'probe_sha256':sha(Path(__file__).read_bytes()),
            'rival':'Use the 2-to-3 vector as local x, assume local y is its clockwise quarter-turn, and ignore the actual color-4 tip.',
            'recipe':{'seed':seed,'difficulty':'easy','demo_sample_indices':[0,1,2,3],'query_sample_index':4,'overrides':{}},
            'search':{'seed_start':410000,'maximum_candidate_episodes':256,
                      'candidate_episodes':candidate_count,'generated_grids':generated},
            'train':deepcopy(train),'test':[deepcopy(query)],'lesson_identifiable_reasons':hook,
            'training_admitted':False,
            'limits':'One deliberately searched five-call episode assembled from the unmodified public generator. This probe does not replay the shared production lesson assembler or estimate ambiguity prevalence. Production and selected canonical authority are unchanged.'}
    with _local_imports(RUNTIME,source_path.parent):
        apply,identity,bridge=_real_evaluator(RUNTIME)
        assert identity['backend']=='racket' and identity['protected'] is True
        record['racket']=identity
        count=0
        try:
            for split in ('train','test'):
                for pair in record[split]:
                    grid=pair['input']
                    actual=_grid(apply(canonical,grid))
                    alternative=_grid(apply(RIVAL,grid))
                    count+=2
                    assert actual==pair['output']==mirror(grid,fixed_clockwise=False)
                    assert alternative==mirror(grid,fixed_clockwise=True)
                    pair['rival_output']=alternative
                    pair['different_cells']=[[r,c] for r,row in enumerate(actual) for c,v in enumerate(row) if alternative[r][c]!=v]
                    pair['observed_axes']=gen.observe_overrides(grid)
                    pair['declared_color_rival_refuted']=gen.LESSON_COMPETITORS['any_nonframe_local_color'](grid)!=actual
        finally:
            bridge.close()
    assert all(not p['different_cells'] for p in record['train'])
    assert record['test'][0]['different_cells']
    assert sha(source_path.read_bytes())==source_hash
    record['racket_evaluations']=count
    record['finding_confirmed']=True
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'out':str(out),'seed':seed,'finding_confirmed':True,
                      'different_cells':record['test'][0]['different_cells'],
                      'racket_evaluations':count,'candidate_episodes':candidate_count,'generated_grids':generated,
                      'orientations':[p['observed_axes']['orientation'] for p in record['train']+record['test']]}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
