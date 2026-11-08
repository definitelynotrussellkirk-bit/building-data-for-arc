"""Bounded, source-pinned native-family audit. Run via review.py run.

Writes one compact private report; Python policy checks and actual protected
Racket evaluations are counted separately. This is not native acceptance.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HOME = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('ada76_native_audit', HOME/'prototype.py')
p = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(p)


def run(seeds: int) -> dict:
    if type(seeds) is not int or not 1 <= seeds <= 512:
        raise ValueError('seeds must be in [1,512]')
    source = {x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(HOME.iterdir())
              if x.is_file() and x.suffix in ('.py','.rkt','.json')}
    failures=[]; unique=set(); episodes=labels=0
    for seed in range(seeds):
        for demos in range(3,7):
            inputs=None
            for mode in p.MODES:
                e=p.generate(seed,{'mode':mode},demos,4)
                episodes+=1;labels+=demos+4
                grids=[repr(pair['input']) for pair in e['train']+e['test']]
                unique.update(grids)
                if inputs is not None and grids != inputs:
                    failures.append({'seed':seed,'demos':demos,'kind':'unmatched_inputs'})
                inputs=grids
                check=p.teaching_check(e)
                if check['failures']:
                    failures.append({'seed':seed,'demos':demos,'mode':mode,**check})
                stress=e['test'][3]['input']
                if (len(stress)!=30 or len(stress[0])!=30 or sum(v!=0 for row in stress for v in row)<90
                    or not all(any(row) for row in stress)):
                    failures.append({'seed':seed,'mode':mode,'kind':'boundary_content'})
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import find_root
    apply, identity, bridge = _real_evaluator(find_root(HOME)/'shared/runtime')
    evaluations=0; examples=[]; regressions=[]
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
                    if actual!=pair['output']:
                        failures.append({'kind':'racket_parity','seed':seed,'mode':mode,'pair':pair,'actual':actual})
                examples.append({'seed':seed,'settings':{'mode':mode},**e})
        before=json.loads((HOME/'evidence/current/teaching-before.json').read_text())
        for seed,selector in ((12,'first'),(14,'last'),(16,'min_color'),(17,'max_color')):
            old=before[str(seed)];new=p.generate(seed,{'mode':'filled_majority'},3,4)
            rival=p.racket_policy(selector=selector)
            old_results=[]
            for pair in old['train']:
                gold=execute(old['program_solution'],pair['input'])
                other=execute(rival,pair['input'])
                if gold != pair['output'] or other != gold:
                    failures.append({'kind':'old_counterexample_not_reproduced','seed':seed})
                old_results.append({'input':pair['input'],'gold':gold,'rival':other})
            qi=next(i for i,pair in enumerate(old['test']) if p.predict(pair['input'],f'exact/{selector}')!=pair['output'])
            pair=old['test'][qi]
            gold=execute(old['program_solution'],pair['input']);other=execute(rival,pair['input'])
            if gold==other or gold!=pair['output']:
                failures.append({'kind':'old_query_did_not_separate','seed':seed})
            repair=next(pair for pair in new['train'] if p.predict(pair['input'],f'exact/{selector}')!=pair['output'])
            rg=execute(new['program_solution'],repair['input']);rr=execute(rival,repair['input'])
            if rg==rr or rg!=repair['output']:
                failures.append({'kind':'repaired_demo_did_not_separate','seed':seed})
            regressions.append({'seed':seed,'policy':f'exact/{selector}','rival_program':rival,
                 'old_demos':old_results,'old_query':{'input':pair['input'],'gold':gold,'rival':other},
                 'new_demo':{'input':repair['input'],'gold':rg,'rival':rr}})
        # Execute representative gating rivals; each mistake must change a demo.
        for fill_mode,index in (('same_many',0),('endpoints',1),('any_two',2)):
            e=p.generate(0,{'mode':'filled_majority'},3,4)
            pair=e['train'][index]
            other=execute(p.racket_policy(fill_mode),pair['input'])
            if other==pair['output'] or other!=p.predict(pair['input'],fill_mode+'/post'):
                failures.append({'kind':'racket_gating_rival','policy':fill_mode})
        old=json.loads((HOME/'evidence/current/shortcut-before.json').read_text())
        new=p.generate(0,{'mode':'filled_majority'},3,4)
        rival=p.racket_policy(selector='row_frequency')
        qi=next(i for i,x in enumerate(old['test']) if p.predict(x['input'],'exact/row_frequency')!=x['output'])
        repaired=next(x for x in new['train'] if p.predict(x['input'],'exact/row_frequency')!=x['output'])
        records=[]
        for role,pair in [(f'old_demo_{i}',x) for i,x in enumerate(old['train'])]+[('heldout_query',old['test'][qi]),('repaired_demo',repaired)]:
            gold=execute(old['program_solution'],pair['input']);other=execute(rival,pair['input'])
            if gold!=pair['output'] or (gold==other)!=role.startswith('old_demo'):
                failures.append({'kind':'row_frequency_regression','role':role})
            records.append({'role':role,'input':pair['input'],'gold':gold,'rival':other})
        regressions.append({'policy':'exact/row_frequency','rival_program':rival,'cases':records})
    finally: bridge.close()
    return {'schema':'ada76-native-bounded-audit-v1','source_sha256':source,'seeds':seeds,
            'demo_counts':[3,4,5,6],'settings':list(p.MODES),'episodes':episodes,'labeled_pair_checks':labels,
            'distinct_inputs':len(unique),'declared_policies':list(p.POLICIES),
            'racket':identity,'racket_evaluations':evaluations,'examples':examples,'regressions':regressions,
            'failures':failures,'status':'passed' if not failures else 'failed',
            'limits':'Finite declared-policy and retained-seed checks. Python sweep, separately counted Racket labels. Not universal identifiability, owner acceptance or training admission.'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seeds',type=int,default=64)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists(): raise FileExistsError('choose a fresh audit output')
    report=run(args.seeds)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pair_checks','distinct_inputs','racket_evaluations')}))
    if report['failures']:
        print(json.dumps(report['failures'][:5],indent=2)); raise SystemExit(1)

if __name__=='__main__': main()
