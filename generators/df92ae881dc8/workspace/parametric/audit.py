"""Bounded native period/coverage audit; no owner acceptance or training admission."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

HOME=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_periodic_audit_'+str(HOME),HOME/'native.py')
native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)


def run(seeds=32,racket_seeds=(0,1,17)):
    native.integer(seeds,1,256,'seeds')
    seen,failures,coverage=set(),[],Counter()
    episodes=pairs=0
    for seed in range(seeds):
        reference=native.generate(seed,{'spacing':'observed'},6,4)
        for mode in native.MODES:
            for count in range(4,7):
                e=native.generate(seed,{'spacing':mode},count,4)
                episodes+=1;pairs+=count+4
                check=native.teaching_check(e,mode)
                if check['ambiguous']:failures.append({'seed':seed,'mode':mode,'demos':count,'rivals':check['ambiguous']})
                grids=[p['input'] for p in e['train']+e['test']]
                if grids!=[p['input'] for p in reference['train'][:count]+reference['test']]:
                    failures.append({'seed':seed,'error':'count/setting-dependent input bank'})
                for g in grids:
                    seen.add(json.dumps(g,separators=(',',':')))
                    f=native.analyze(g,mode)
                    coverage[f'branch:{f["branch"]}']+=1
                    coverage[f'observed_period:{f["observed_period"]}']+=1
                    coverage[f'effective_period:{f["effective_period"]}']+=1
                    coverage[f'color:{f["foreground"]}']+=1
                    if f['winner']:coverage['winner:'+json.dumps(f['winner'])]+=1
                    coverage[f'size:{len(g)}x{len(g[0])}']+=1
    old=json.loads((HOME/'regressions/coverage_lesson_before.json').read_bytes())
    mode=old['settings']['spacing'];rival=old['rival']
    new=native.generate(old['seed'],old['settings'],4,4)
    reg={'old_demo_count':len(old['train']),'new_demo_count':4,
         'old_rival_fits_demos':all(native.predict(p['input'],mode,rival)==p['output'] for p in old['train']),
         'old_rival_differs_query':native.predict(old['test'][0]['input'],mode,rival)!=old['test'][0]['output'],
         'new_refuting_demos':[i for i,p in enumerate(new['train']) if native.predict(p['input'],mode,rival)!=p['output']],
         'before_fixture':'regressions/coverage_lesson_before.json','protected_labels':[]}
    report={'schema':'periodic-native-audit-v1','seeds':seeds,'demo_counts':[4,5,6],
            'settings':list(native.MODES),'policies_per_setting':len(native.POLICIES)+1,
            'policies':list(native.POLICIES),'episodes':episodes,'labeled_pair_checks':pairs,
            'distinct_inputs':len(seen),'coverage':dict(coverage),'regression':reg,
            'failures':failures,'protected_racket_evaluations':0,
            'limits':'Finite tested seeds and policies only. Python claim checks and protected Racket evaluations are separate counts. Three-demo authoring attempts left held-out ambiguities; native contract is 4..6, not 2..3.'}
    if racket_seeds:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        def execute(b,program,g):
            datum="'("+' '.join('('+' '.join(map(str,row))+')' for row in g)+')'
            value=b.eval_text(f'({wrap_rule(program)} {datum})')
            report['protected_racket_evaluations']+=1
            return value
        with RacketBridge() as bridge:
            identity=bridge.runtime_identity
            if identity.get('protected') is not True or identity.get('backend')!='racket':
                raise RuntimeError('protected Racket required')
            report['racket']={k:v for k,v in identity.items() if k.endswith('sha256') or k in ('schema','backend','protected')}
            for seed in racket_seeds:
                for setting in native.MODES:
                    e=native.generate(seed,{'spacing':setting},6,4)
                    for i,p in enumerate(e['train']+e['test']):
                        if execute(bridge,e['program_solution'],p['input'])!=p['output']:
                            failures.append({'seed':seed,'spacing':setting,'pair':i,'error':'Racket/Python mismatch'})
            for phase, examples in (('before',old['train']+old['test']),('after',new['train'])):
                for i,p in enumerate(examples):
                    good=native.program(old['settings']);bad=native.program(old['settings'],policy=rival)
                    a=execute(bridge,good,p['input']);b=execute(bridge,bad,p['input'])
                    if a!=p['output'] or b!=native.predict(p['input'],mode,rival):
                        failures.append({'phase':phase,'pair':i,'error':'regression label mismatch'})
                    reg['protected_labels'].append({'phase':phase,'index':i,'input':p['input'],'output':a,'rival_output':b})
            reg['program']=native.program(old['settings']);reg['rival_program']=native.program(old['settings'],policy=rival)
            # Tie execution is separately verified; reversed candidate order must not
            # stand in for an unexecuted Python-only interpretation.
            for setting,index in (('observed',3),('doubled',1)):
                p=native.generate(0,{'spacing':setting},4,4)['train'][index]
                correct=execute(bridge,native.program({'spacing':setting}),p['input'])
                alternate=execute(bridge,native.program({'spacing':setting},policy='last_coverage_tie'),p['input'])
                if correct!=p['output'] or alternate!=native.predict(p['input'],setting,'last_coverage_tie') or correct==alternate:
                    failures.append({'spacing':setting,'error':'coverage tie regression failed'})
                reg['protected_labels'].append({'phase':'coverage_tie','spacing':setting,'input':p['input'],'output':correct,'rival_output':alternate})
    report['sources']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(HOME.iterdir()) if p.suffix in ('.py','.rkt')}
    report['status']='passed' if not failures else 'failed'
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.out.exists():p.error('refusing to overwrite evidence')
    report=run(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pair_checks','distinct_inputs','protected_racket_evaluations','failures')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
