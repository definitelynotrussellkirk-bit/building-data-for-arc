"""Bounded teaching audit with separately counted protected-Racket executions.

Run using review.py run; returned labels are private, and no approval is granted.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from collections import Counter

HOME = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_cross_audit_native_'+str(HOME), HOME/'native.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def run(seeds=32, racket_seeds=(0,17)):
    native._integer(seeds,1,256,'seeds')
    seen, failures, coverage = set(), [], Counter()
    episodes = pairs = 0
    for seed in range(seeds):
        for mode in native.MODES:
            for demos in range(2,7):
                episode = native.generate(seed,{'rule':mode},demos,4)
                episodes += 1
                pairs += len(episode['train'])+4
                check = native.teaching_check(episode)
                if check['ambiguous']:
                    failures.append({'seed':seed,'mode':mode,'demos':demos,'rivals':check['ambiguous']})
                for p in episode['train']+episode['test']:
                    g=p['input']; seen.add(json.dumps(g,separators=(',',':')))
                    r,c,v,z=native.facts(g)
                    coverage[f'size:{len(g)}x{len(g[0])}']+=1
                    coverage[f'line_color:{v}']+=1; coverage[f'line_color:{z}']+=1
                if episode['test'] != native.generate(seed,{'rule':mode},2,4)['test']:
                    failures.append({'seed':seed,'error':'query bank depends on demo count'})
    old = json.loads((HOME/'regressions/tie_lesson_before.json').read_bytes())
    new = native.generate(old['seed'],old['settings'],2,4)
    rival = 'column_major_tie'
    regression = {
        'old_rival_fits_demos':all(native.predict(p['input'],rival)==p['output'] for p in old['train']),
        'old_rival_differs_query':native.predict(old['test'][0]['input'],rival)!=old['test'][0]['output'],
        'new_refuting_demos':[i for i,p in enumerate(new['train']) if native.predict(p['input'],rival)!=p['output']],
        'before_fixture':'regressions/tie_lesson_before.json',
        'protected_labels':[],
    }
    report = {'schema':'cross-native-audit-v1','seeds':seeds,'demo_counts':[2,3,4,5,6],
        'settings':list(native.MODES),'policies':list(native.RIVALS), 'episodes':episodes,
        'labeled_pair_checks':pairs,'distinct_inputs':len(seen),'coverage':dict(coverage),
        'failures':failures,'regression':regression,'protected_racket_evaluations':0,
        'limits':'Finite sampler/rival checks. Most checks use independent Python claims; the separately counted subset is executed in protected Racket. No acceptance or training admission.'}
    if racket_seeds:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule
        def execute(bridge,program,g):
            datum="'("+' '.join('('+' '.join(map(str,row))+')' for row in g)+')'
            value=bridge.eval_text(f'({wrap_rule(program)} {datum})')
            report['protected_racket_evaluations']+=1
            return value
        with RacketBridge() as bridge:
            identity=bridge.runtime_identity
            if identity.get('protected') is not True or identity.get('backend')!='racket':
                raise RuntimeError('protected Racket required')
            report['racket']={k:v for k,v in identity.items() if k.endswith('sha256') or k in ('schema','backend','protected')}
            for seed in racket_seeds:
                for mode in native.MODES:
                    e=native.generate(seed,{'rule':mode},6,4)
                    for i,p in enumerate(e['train']+e['test']):
                        actual=execute(bridge,e['program_solution'],p['input'])
                        if actual!=p['output']:
                            failures.append({'seed':seed,'mode':mode,'pair':i,'error':'Racket/Python mismatch'})
            good=native.program({'rule':'largest_fragment'})
            bad=native._relay_program(tie='column')
            for phase, examples in (('before',old['train']+old['test']),('after',new['train'])):
                for i,p in enumerate(examples):
                    a,b=execute(bridge,good,p['input']), execute(bridge,bad,p['input'])
                    if a!=p['output'] or b!=native.predict(p['input'],rival):
                        failures.append({'phase':phase,'pair':i,'error':'regression label mismatch'})
                    regression['protected_labels'].append({'phase':phase,'index':i,'input':p['input'],'output':a,'rival_output':b})
            regression['program']=good; regression['rival_program']=bad
    report['sources']={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(HOME.iterdir()) if p.suffix in ('.py','.rkt')}
    report['status']='passed' if not failures else 'failed'
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,default=32)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():
        parser.error('refusing to overwrite evidence')
    report=run(args.seeds)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pair_checks','distinct_inputs','protected_racket_evaluations','failures')}))
    return 0 if report['status']=='passed' else 1


if __name__=='__main__':
    raise SystemExit(main())
