#!/usr/bin/env python3
"""Bounded native lessons and protected-Racket regressions, no owner acceptance."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HOME=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('audit_adapter_142',HOME/'adapter.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
f=a.family


def run(seeds=32):
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    root=find_root(__file__)
    unique,failures,sizes,shapes=set(),[],set(),set()
    first=set();boundary_counts=[];episodes=pairs=0
    for seed in range(seeds):
        try:
            bank,queries=f.input_bank(seed)
            first.add(json.dumps(bank[0]))
            for g in bank+queries:
                unique.add(json.dumps(g));shapes.add((len(g),len(g[0])));sizes.add(f.intermediate(g)['size'])
            boundary_counts.append(sum(v!=0 for row in queries[-1] for v in row))
            for mode in f.MODES:
                for demos in range(2,7):
                    e=a.generate(seed,{'mode':mode},demos,4);check=f.teaching_check(e)
                    episodes+=1;pairs+=demos+4
                    if check['query_disagreeing_survivors']:failures.append({'seed':seed,'mode':mode,'demos':demos,**check})
        except Exception as error:
            failures.append({'seed':seed,'error':str(error)})
    count=0;executions=[]
    with _local_imports(root/'shared/runtime',HOME):
        raw,identity,bridge=_real_evaluator(root/'shared/runtime')
        def apply(program,grid):
            nonlocal count
            result=raw(program,grid);count+=1;return result
        try:
            for seed in (0,17):
                for mode in f.MODES:
                    e=a.generate(seed,{'mode':mode},2,4)
                    for split in ('train','test'):
                        for i,p in enumerate(e[split]):
                            actual=apply(e['program_solution'],p['input']);assert actual==p['output'],(seed,mode,split,i)
                            executions.append({'seed':seed,'mode':mode,'split':split,'pair_index':i,'input':p['input'],'output':actual})
            canonical=a.program({'mode':'caps'});horizontal=(HOME/'rules/horizontal_only.rkt').read_text();vertical=(HOME/'rules/vertical_only.rkt').read_text()
            # Existing source-bound production finding is reproduced, not falsely closed.
            old=[f.gen.generate(0,i,difficulty='easy') for i in range(4)]
            orientation={'production_generator_sha256':hashlib.sha256(Path(f.gen.__file__).read_bytes()).hexdigest(),'train':[],'query':None,
                         'canonical_program':canonical,'horizontal_only_program':horizontal,'production_changed':False}
            for i,g in enumerate(old):
                correct,wrong=apply(canonical,g),apply(horizontal,g)
                assert correct==f.gen.rule_mirror(g)
                if i<3:
                    assert correct==wrong;orientation['train'].append({'input':g,'output':correct,'rival_output':wrong})
                else:
                    assert correct!=wrong;orientation['query']={'input':g,'output':correct,'rival_output':wrong}
            orientation['native_demo_refutations']=[]
            for p in a.generate(0,{'mode':'caps'},2,4)['train']:
                correct=apply(canonical,p['input']);oh=apply(horizontal,p['input']);ov=apply(vertical,p['input'])
                assert correct==p['output'] and correct!=oh and correct!=ov
                orientation['native_demo_refutations'].append({'horizontal_only':True,'vertical_only':True})
            before=json.loads((HOME/'regression/allcolor-before.json').read_text())
            rival=(HOME/'rules/allcolor_remaining.rkt').read_text();regression={'train':[],'canonical_program':canonical,'rival_program':rival}
            for g in before['train_inputs']:
                good,bad=apply(canonical,g),apply(rival,g);assert good==bad
                regression['train'].append({'input':g,'output':good,'rival_output':bad})
            g=before['query_input'];good,bad=apply(canonical,g),apply(rival,g);assert good!=bad
            regression['query']={'input':g,'output':good,'rival_output':bad};regression['repaired_demo_refutations']={}
            for mode in f.MODES:
                diffs=[]
                for p in a.generate(0,{'mode':mode},2,4)['train']:
                    good,bad=apply(a.program({'mode':mode}),p['input']),apply(rival,p['input'])
                    assert good==p['output'];diffs.append(good!=bad)
                assert any(diffs);regression['repaired_demo_refutations'][mode]=diffs
            for g in ([[0]],[[2]],[[2,2]],[[2],[2],[2]],[[3,3,3]],[[2,2,0,2,2],[2,0,0,0,2]],[[2,2,0,2,2,2,2,2],[2,2,0,0,0,0,0,0]]):
                for mode in f.MODES:
                    actual=apply(a.program({'mode':mode}),g);assert actual==f.solve(g,mode)
                    executions.append({'input':g,'output':actual,'mode':mode,'edge_case':True})
        finally:bridge.close()
    return {'schema':'142-native-bounded-audit-v1','seeds':seeds,'episodes':episodes,'labeled_pair_checks':pairs,
            'unique_inputs':len(unique),'unique_first_demos':len(first),'dimensions':sorted([list(x) for x in shapes]),
            'residual_sizes':sorted(sizes),'boundary_nonzero_count_minmax':[min(boundary_counts),max(boundary_counts)],
            'policies':list(f.POLICIES),'demo_counts':[2,3,4,5,6],'failures':failures,
            'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HOME/'adapter.py',HOME/'family.py')},
            'racket':identity,'protected_racket_evaluations':count,'execution':executions,
            'allcolor_regression':regression,'orientation_regression':orientation,
            'limits':'Finite policies and seeds. Most census labels are Python claims. Production orientation defect remains open; repaired in the separate native curriculum. No owner acceptance or training admission.'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    if not 1<=args.seeds<=256:p.error('--seeds must be 1..256')
    if args.out.exists():p.error('output already exists')
    report=run(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:report[k] for k in ('episodes','labeled_pair_checks','unique_inputs','unique_first_demos','protected_racket_evaluations','failures')}))
    return bool(report['failures'])

if __name__=='__main__':raise SystemExit(main())
