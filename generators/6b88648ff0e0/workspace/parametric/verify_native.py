#!/usr/bin/env python3
"""Bounded strip curriculum audit, protected labels and one-query exports.
Run from library root through review.py run. Only the adjacent adapter is used.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('_local_strip_frequency_adapter',HERE/'adapter.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def run(out, seeds=64):
    from reviewer_support import find_root, public_challenge_bytes
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    if type(seeds) is not int or not 1 <= seeds <= 256: raise ValueError('seeds must be 1..256')
    out = Path(out)
    if out.exists(): raise FileExistsError('choose a new audit directory')
    root = find_root(HERE)
    failures, unique, sizes, boundaries = [],set(),set(),0
    episodes = pairs = 0
    for seed in range(seeds):
        for mode in a.SETTINGS:
            for demos in range(2,7):
                e = a.generate(seed,{'stack_order':mode},demos,4)
                episodes += 1
                pairs += demos+4
                findings = a.teaching_check(e)
                if findings: failures.append({'seed':seed,'mode':mode,'demos':demos,'teaching':findings})
                inputs = [p['input'] for p in e['train']+e['test']]
                ids = [hashlib.sha256(json.dumps(g,separators=(',',':')).encode()).hexdigest() for g in inputs]
                unique.update(ids)
                if len(set(ids)) != len(ids): failures.append({'seed':seed,'mode':mode,'duplicate_input':True})
                for g in inputs: sizes.add((len(g),len(g[0])))
                g = e['test'][-1]['input']
                count = sum(v != 0 for row in g for v in row)
                if len(g) != 30 or len(g[0]) != 30 or count < 600: failures.append({'seed':seed,'boundary_cells':count})
                boundaries += 1
    protected, private, evaluations = [],[],0
    runtime = root/'shared/runtime'
    with _local_imports(runtime,HERE):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            for seed in (0,17):
                for mode in a.SETTINGS:
                    e = a.generate(seed,{'stack_order':mode},3,4)
                    for split in ('train','test'):
                        for i,p in enumerate(e[split]):
                            actual = apply(e['program_solution'],p['input']); evaluations += 1
                            if actual != p['output']: failures.append({'seed':seed,'mode':mode,'split':split,'pair':i,'racket_mismatch':True})
                            p['output'] = actual
                    if a.teaching_check(e): failures.append({'seed':seed,'mode':mode,'executed_teaching':a.teaching_check(e)})
                    private.append({'seed':seed,**e})
                    if mode == 'key_frequency':
                        p = e['test'][0]
                        counter = apply(a.counterfactual_program(),p['input']); evaluations += 1
                        if counter == p['output']: failures.append({'seed':seed,'causal_unchanged':True})
                        protected.append({'seed':seed,'settings':e['settings'],'program':e['program_solution'],
                                          'input':p['input'],'output':p['output'],
                                          'intermediate_value':a.analyze(p['input'])['key'],
                                          'counterfactual_program':a.counterfactual_program(),'counterfactual_output':counter})
        finally: bridge.close()
    out.mkdir(parents=True)
    public = out/'public'; public.mkdir()
    for e in private:
        for i in range(4):
            view = a.public_turn(e,i)
            raw = public_challenge_bytes(view)
            (public/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)
            changed = deepcopy(e)
            changed['settings']={'secret':'changed'}; changed['program_solution']='changed'
            for q in changed['test']: q['output']=[[9]]
            if public_challenge_bytes(a.public_turn(changed,i)) != raw: failures.append({'privacy_invariance':False})
    (out/'examples.private.json').write_text(json.dumps(private,sort_keys=True)+'\n')
    (out/'causal.private.json').write_text(json.dumps(protected,sort_keys=True)+'\n')
    # Deliberately leak one answer: the external public checker must reject it.
    negative = out/'negative'; negative.mkdir()
    bad = a.public_turn(private[0],0); bad['test'][0]['output']=private[0]['test'][0]['output']
    raw=(json.dumps(bad,sort_keys=True,separators=(',',':'))+'\n').encode()
    (negative/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)
    report={'task_id':a.TASK,'status':'passed' if not failures else 'failed','seeds':seeds,
            'episodes':episodes,'labeled_pairs_claims':pairs,'distinct_inputs':len(unique),
            'demo_counts':list(range(2,7)),'sizes':sorted(sizes),'boundary_cases':boundaries,
            'rivals':list(a.RIVALS),'racket':identity,'racket_evaluations':evaluations,
            'public_files':len(list(public.glob('*.json'))),'failures':failures,
            'limits':'Finite rivals and bounded seeds, not universal uniqueness; Python sweep claims separately checked on 42 protected labels plus two ablations. No owner acceptance or training admission.'}
    (out/'audit.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',required=True);parser.add_argument('--seeds',type=int,default=64)
    args=parser.parse_args()
    result=run(args.out,args.seeds)
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(result['status']!='passed')
