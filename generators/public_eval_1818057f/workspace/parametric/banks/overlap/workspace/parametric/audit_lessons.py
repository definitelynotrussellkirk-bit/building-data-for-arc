"""Bounded auditable lesson/rival sweep. Run via review.py run; no acceptance.

The Python mirror is a fast claim checker, not the label authority. Independent
protected-Racket execution is supplied by public-creation preflight and handoff.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

HERE=Path(__file__).resolve().parent

def load_adapter():
    spec=importlib.util.spec_from_file_location('_audit_adapter_'+str(HERE),HERE/'adapter.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def check_episode(adapter,episode,mode):
    issues=[];pairs=episode['train']+episode['test'];e=adapter.engine
    if len({json.dumps(p['input']) for p in pairs})!=len(pairs):issues.append('duplicate input')
    for i,p in enumerate(pairs):
        if e.solve(p['input'],mode)!=p['output']:issues.append(f'claim label mismatch at pair {i}')
        issues.extend(e.self_check(p['input']))
    predictions=[e.rivals(p['input'],mode) for p in pairs]
    d=len(episode['train'])
    for name in predictions[0]:
        if all(predictions[i][name]==p['output'] for i,p in enumerate(episode['train'])) and any(
            predictions[d+i][name]!=p['output'] for i,p in enumerate(episode['test'])):
            issues.append('harmful surviving rival: '+name)
    return issues

def source_hashes():
    home=HERE.parents[1]
    return {p.relative_to(home).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(home.rglob('*')) if p.is_file() and
            (p.suffix in ('.py','.rkt') or p.name=='promotion.json') and '__pycache__' not in p.parts}

def audit(seeds):
    if type(seeds) is not int or not 1<=seeds<=1024:raise ValueError('seeds must be 1..1024')
    a=load_adapter();key=next(iter(json.loads((HERE/'promotion.json').read_text())['parameters']))
    hashes=source_hashes();failures=[];episodes=0;pairs=0;stress=0;differences=0
    for seed in range(seeds):
        for demos in (2,3,6):
            baseline=None
            for mode in a.engine.SETTINGS:
                ep=a.generate(seed,{key:mode},demos,4);episodes+=1;pairs+=demos+4
                failures.extend({'seed':seed,'demos':demos,'setting':mode,'finding':f} for f in check_episode(a,ep,mode))
                inputs=[p['input'] for s in ('train','test') for p in ep[s]]
                g=ep['test'][3]['input']
                stress+=len(g)==30 and len(g[0])==30
                if baseline is not None:
                    if inputs!=[p['input'] for s in ('train','test') for p in baseline[s]]:
                        failures.append({'seed':seed,'finding':'setting-dependent input'})
                    differences+=sum(p['output']!=q['output'] for s in ('train','test') for p,q in zip(ep[s],baseline[s]))
                baseline=ep
                smaller=a.generate(seed,{key:mode},2,1)
                if smaller['train']!=ep['train'][:2] or smaller['test']!=ep['test'][:1]:
                    failures.append({'seed':seed,'finding':'count-dependent prefix'})
    if hashes!=source_hashes():raise ValueError('source changed during audit')
    return {'schema':'bounded-public-family-audit-v1','task_id':a.engine.TASK_ID,
            'status':'passed' if not failures else 'failed','seed_range':[0,seeds-1],
            'demonstration_counts':[2,3,6],'query_count':4,'episodes':episodes,'pairs':pairs,
            'exact_30x30_pairs':stress,'setting_answer_differences':differences,
            'declared_rivals':sorted(a.engine.rivals(a.engine.scene(0,0,'query'),a.engine.SETTINGS[0])),
            'failures':failures,'source_sha256':hashes,'racket_labels_checked':False,
            'limits':'Finite declared rivals/seeds only. Python claims; independent Racket preflight required. No acceptance or training admission.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=64);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();report=audit(args.seeds)
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','declared_rivals')},sort_keys=True))
    raise SystemExit(0 if report['status']=='passed' else 1)
if __name__=='__main__':main()
