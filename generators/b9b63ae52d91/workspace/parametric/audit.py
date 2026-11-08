#!/usr/bin/env python3
"""Bounded finite-teaching census plus independent protected-Racket labels.

Run via review.py run python3 generators/b9b63ae52d91/workspace/parametric/audit.py
--out ../checks/b9b63ae52d91/audit.json. No owner acceptance is performed.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HOME = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('b9_audit_adapter',HOME/'adapter.py')
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
f = a.family


def run(seeds=32):
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator, _local_imports
    root = find_root(__file__)
    unique, failures, rows = set(), [], []
    episodes = pairs = 0
    boundary_counts, selected_sizes = [], set()
    for seed in range(seeds):
        try:
            bank,queries,meta = f.input_bank(seed)
            for g in bank+queries: unique.add(json.dumps(g))
            boundary_counts.append(sum(v==8 for row in queries[-1] for v in row))
            selected_sizes.update(f.intermediate(g)['size'] for g in bank+queries)
            for mode in f.MODES:
                for demos in range(2,7):
                    e = a.generate(seed,{'mode':mode},demos,4)
                    check = f.teaching_check(e)
                    episodes += 1; pairs += demos+4
                    if check['query_disagreeing_survivors']:
                        failures.append({'seed':seed,'mode':mode,'demos':demos,**check})
            rows.append({'seed':seed,**meta})
        except Exception as error:
            failures.append({'seed':seed,'error':str(error)})
    execution,regression = [], {}
    runtime = root/'shared/runtime'
    with _local_imports(runtime,HOME):
        apply,identity,bridge = _real_evaluator(runtime)
        try:
            for seed in (0,17):
                for mode in f.MODES:
                    e = a.generate(seed,{'mode':mode},2,4)
                    for split in ('train','test'):
                        for i,pair in enumerate(e[split]):
                            actual = apply(e['program_solution'],pair['input'])
                            assert actual == pair['output'], (seed,mode,split,i)
                            execution.append({'seed':seed,'mode':mode,'split':split,'pair_index':i,
                                              'input_sha256':hashlib.sha256(json.dumps(pair['input']).encode()).hexdigest(),
                                              'input':pair['input'],'output':actual})
            old=json.loads((HOME/'regression/bbox-before.json').read_text())
            good=a.program({'mode':'paired_rows'}); rival=(HOME/'rules/rival_bbox.rkt').read_text()
            regression={'train':[]}
            for g in old['train_inputs']:
                correct,wrong=apply(good,g),apply(rival,g)
                assert correct==wrong
                regression['train'].append({'input':g,'output':correct,'rival_output':wrong})
            g=old['query_input']; correct,wrong=apply(good,g),apply(rival,g)
            assert correct!=wrong
            regression['query']={'input':g,'output':correct,'rival_output':wrong}
            repaired=a.generate(17,{'mode':'paired_rows'},2,4)['train']
            differences=[]
            for p in repaired:
                correct,wrong=apply(good,p['input']),apply(rival,p['input'])
                assert correct==p['output']
                differences.append(correct!=wrong)
            assert any(differences)
            regression['repaired_demo_distinguishes']=differences
            regression['program']=good;regression['rival_program']=rival
            # Boundary/no-component cases are legal under the rule, not sampler claims.
            for g in ([[0]],[[8]],[[8,0],[0,0]]):
                actual=apply(good,g);assert actual==f.solve(g,'paired_rows')
                execution.append({'input':g,'output':actual,'edge_case':True})
        finally:
            bridge.close()
    return {'schema':'b9-native-bounded-audit-v1','seeds':seeds,'episodes':episodes,
            'labeled_pair_checks':pairs,'unique_inputs':len(unique),'policies':list(f.POLICIES),
            'demo_counts':[2,3,4,5,6],'boundary_cyan_count_minmax':[min(boundary_counts),max(boundary_counts)],
            'selected_component_sizes':sorted(selected_sizes),'construction':rows,'failures':failures,
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HOME/'adapter.py',HOME/'family.py',HOME/'prototype.py')},
            'racket':identity,'protected_racket_evaluations':len(execution)+10,
            'execution':execution,'bbox_regression':regression,
            'limitations':'Finite rival class and bounded seeds only. Most census labels are Python claims. No owner acceptance or training admission.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seeds',type=int,default=32);parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    if not 1<=args.seeds<=256: parser.error('--seeds must be 1..256')
    if args.out.exists(): parser.error('output already exists')
    report=run(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('episodes','labeled_pair_checks','unique_inputs','protected_racket_evaluations','failures')}))
    return bool(report['failures'])

if __name__=='__main__': raise SystemExit(main())
