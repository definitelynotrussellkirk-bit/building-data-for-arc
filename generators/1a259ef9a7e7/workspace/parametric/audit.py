"""Source-pinned bounded mirror-family sweep plus protected-Racket regressions."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HOME=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('mirror_native_audit',HOME/'prototype.py')
p=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(p)


def run(seeds):
    if type(seeds) is not int or not 1<=seeds<=512:raise ValueError('seeds must be in [1,512]')
    source={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(HOME.iterdir())
            if x.is_file() and x.suffix in ('.py','.rkt','.json')}
    failures=[];unique=set();episodes=labels=0;colors=set();shapes=set()
    for seed in range(seeds):
        for demos in range(3,7):
            reference=None
            for mode in p.MODES:
                e=p.generate(seed,{'mode':mode},demos,4);episodes+=1;labels+=demos+4
                inputs=[repr(pair['input']) for pair in e['train']+e['test']]
                if reference is not None and reference!=inputs:failures.append({'seed':seed,'kind':'unmatched_settings'})
                reference=inputs;unique.update(inputs)
                for pair in e['train']+e['test']:
                    g=pair['input'];shapes.add((len(g),len(g[0])));colors.update(v for row in g for v in row if v)
                check=p.teaching_check(e)
                if check['failures']:failures.append({'seed':seed,'demos':demos,'mode':mode,**check})
                stress=e['test'][3];g,out=stress['input'],stress['output']
                if ((len(g),len(g[0]))!=(10,15) or (len(out),len(out[0]))!=(30,30)
                    or sum(v!=0 for row in g for v in row)<50 or sum(v!=0 for row in out for v in row)<200
                    or not all(any(row) for row in out)):
                    failures.append({'seed':seed,'mode':mode,'kind':'boundary_content'})
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import find_root
    apply,identity,bridge=_real_evaluator(find_root(HOME)/'shared/runtime')
    evaluations=0;examples=[];rivals=[]
    def execute(program,grid):
        nonlocal evaluations
        evaluations+=1
        return apply(program,grid)
    try:
        for seed in (0,17):
            for mode in p.MODES:
                e=p.generate(seed,{'mode':mode},3,4)
                for pair in e['train']+e['test']:
                    actual=execute(e['program_solution'],pair['input'])
                    if actual!=pair['output']:failures.append({'kind':'racket_parity','seed':seed,'mode':mode,'pair':pair,'actual':actual})
                examples.append({'seed':seed,'settings':{'mode':mode},**e})
        e=p.generate(0,{'mode':'largest_mirrored'},3,4)
        for policy,kwargs in [('before',{'order':'before'}),('before_then_after',{'order':'before_then_after'}),
                              ('all_max',{'selector':'all_max'}),('last_tie',{'selector':'last_tie'}),
                              ('bbox',{'selector':'bbox'}),('eight',{'selector':'eight'}),
                              ('stack_then_largest',{'order':'stack_then_largest'})]:
            program=p.racket_policy(**kwargs);observations=[]
            for pair in e['train']:
                actual=execute(program,pair['input'])
                if actual!=p.predict(pair['input'],policy):failures.append({'kind':'racket_rival_parity','policy':policy})
                observations.append({'input':pair['input'],'output':actual,'matches_gold':actual==pair['output']})
            if all(o['matches_gold'] for o in observations):failures.append({'kind':'rival_survived','policy':policy})
            rivals.append({'policy':policy,'program':program,'demo_results':observations})
        # Two-demo ambiguity and the third constructive repair; no failed
        # execution is counted as a refutation. Both programs run on every case.
        rival=p.racket_policy(selector='eight');regression=[]
        qi=next(i for i,x in enumerate(e['test']) if p.predict(x['input'],'eight')!=x['output'])
        for role,pair in [('old_demo_0',e['train'][0]),('old_demo_1',e['train'][1]),
                          ('heldout_query',e['test'][qi]),('third_demo',e['train'][2])]:
            gold=execute(e['program_solution'],pair['input']);other=execute(rival,pair['input'])
            same=role.startswith('old_demo')
            if (gold==other)!=same or gold!=pair['output']:failures.append({'kind':'demo_minimum_regression','role':role})
            regression.append({'role':role,'input':pair['input'],'gold':gold,'rival':other})
        old=json.loads((HOME/'evidence/current/shortcut-before.json').read_text())
        bottom_program=p.racket_policy(selector='bottommost')
        qi=next(i for i,x in enumerate(old['test']) if p.predict(x['input'],'bottommost')!=x['output'])
        repaired=e['train'][2];bottom_records=[]
        for role,pair in [(f'old_demo_{i}',x) for i,x in enumerate(old['train'])]+[('heldout_query',old['test'][qi]),('repaired_demo',repaired)]:
            gold=execute(old['program_solution'],pair['input']);other=execute(bottom_program,pair['input'])
            if gold!=pair['output'] or (gold==other)!=role.startswith('old_demo'):
                failures.append({'kind':'bottommost_regression','role':role})
            bottom_records.append({'role':role,'input':pair['input'],'gold':gold,'rival':other})
    finally:bridge.close()
    return {'schema':'mirror-native-bounded-audit-v1','source_sha256':source,'seeds':seeds,
            'demo_counts':[3,4,5,6],'settings':list(p.MODES),'episodes':episodes,'labeled_pair_checks':labels,
            'distinct_inputs':len(unique),'input_shapes':sorted(shapes),'foreground_colors':sorted(colors),
            'declared_policies':list(p.POLICIES),'racket':identity,'racket_evaluations':evaluations,
            'examples':examples,'rivals':rivals,'three_demo_regression':{'rival_program':rival,'cases':regression},
            'bottommost_regression':{'rival_program':bottom_program,'cases':bottom_records},
            'failures':failures,'status':'passed' if not failures else 'failed',
            'limits':'Finite named-policy and retained-seed checks. Separate Python claims and protected Racket execution. Input <=10x15 because canonical output is 3h by 2w; stress output 30x30. No owner acceptance or training admission.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--seeds',type=int,default=64);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():raise FileExistsError('choose a fresh report path')
    r=run(a.seeds);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps({k:r[k] for k in ('status','episodes','labeled_pair_checks','distinct_inputs','racket_evaluations')}))
    if r['failures']:print(json.dumps(r['failures'][:5],indent=2));raise SystemExit(1)

if __name__=='__main__':main()
