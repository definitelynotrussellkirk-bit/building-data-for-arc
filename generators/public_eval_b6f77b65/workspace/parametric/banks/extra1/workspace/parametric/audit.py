"""Bounded protected-Racket teaching audit, with no acceptance side effects."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles.parametric_worker import _grid, _real_evaluator


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--seeds',type=int,nargs='+',default=[0,9,17,43])
    args=parser.parse_args()
    if args.out.exists():raise ValueError('output must be fresh')
    root=Path.cwd().resolve();base=Path(__file__).resolve().parent;home=base.parents[1]
    paths=[p for p in home.rglob('*') if p.is_file() and '__pycache__' not in p.parts and (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json'))]
    snapshot={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    spec=importlib.util.spec_from_file_location('_arch_support_audit_adapter',base/'adapter.py')
    A=importlib.util.module_from_spec(spec);sys.modules[spec.name]=A;spec.loader.exec_module(A)
    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    cache={};executions=0;episodes=[];comparisons=[];errors=[];rivals_by_setting={}
    digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def execute(program,grid):
        nonlocal executions
        key=(hashlib.sha256(program.encode()).hexdigest(),digest(grid))
        if key not in cache:
            executions+=1;cache[key]=_grid(apply(program,grid))
        return cache[key]
    try:
        for order in ('both','either'):
            setting={'support_mode':order}
            rivals=A.family.rival_programs(setting)
            rivals_by_setting[order]=rivals
            for seed in args.seeds:
                lesson=A.generate(seed,setting,2,4)
                for split in ('train','test'):
                    for pair in lesson[split]:
                        if execute(lesson['program_solution'],pair['input'])!=pair['output']:
                            raise ValueError('chosen-program claim mismatch')
                episodes.append({'seed':seed,'settings':setting,'reference':'blocked_parent_candidate_audit',**lesson})
                for name,program in rivals.items():
                    row={'seed':seed,'settings':setting,'rival':name,'program_sha256':hashlib.sha256(program.encode()).hexdigest()}
                    try:
                        labels=[execute(program,p['input']) for p in lesson['train']]
                        bad=[i for i,(p,v) in enumerate(zip(lesson['train'],labels)) if p['output']!=v]
                        query_labels=[execute(program,p['input']) for p in lesson['test']]
                        differences=[i for i,(p,v) in enumerate(zip(lesson['test'],query_labels)) if p['output']!=v]
                        row.update(query_totality_checked=True,query_differences=differences)
                        if bad:
                            i=bad[0];row.update(status='demo_refuted',first_demo=i,input_sha256=digest(lesson['train'][i]['input']))
                        else:
                            labels=query_labels
                            conflicts=differences
                            row.update(status='query_conflict' if conflicts else 'finite_consistent',query_conflicts=conflicts)
                            if conflicts:
                                i=conflicts[0];row.update(input=lesson['test'][i]['input'],output=lesson['test'][i]['output'],rival_output=labels[i],program=program)
                    except Exception as exc:
                        row.update(status='execution_error',error=type(exc).__name__+': '+str(exc));errors.append(row)
                    comparisons.append(row)
    except Exception as exc:
        errors.append({'error':type(exc).__name__+': '+str(exc)})
    finally:bridge.close()
    unchanged=all(hashlib.sha256((root/p).read_bytes()).hexdigest()==v for p,v in snapshot.items())
    counts={s:sum(r['status']==s for r in comparisons) for s in ('demo_refuted','finite_consistent','query_conflict','execution_error')}
    passed=not errors and not counts['query_conflict'] and unchanged
    report={'schema':'b6f77b65-teaching-audit-v1','status':'passed' if passed else 'failed','source_sha256':snapshot,'sources_unchanged':unchanged,'racket':identity,'protected_executions':executions,'episodes':episodes,'rivals_by_setting':rivals_by_setting,'comparisons':comparisons,'counts':counts,'errors':errors,'limits':'Finite named rivals and retained seeds, two demos, four queries; every rival executes on the entire query bank even after demo refutation; no owner acceptance or training admission.'}
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'episodes':len(episodes),'comparisons':len(comparisons),'protected_executions':executions,**counts,'errors':errors}))
    if not passed:raise SystemExit(1)


if __name__=='__main__':main()
