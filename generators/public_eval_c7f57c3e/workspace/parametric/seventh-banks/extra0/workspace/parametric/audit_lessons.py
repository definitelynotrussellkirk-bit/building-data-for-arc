"""Bounded source-bound count, diversity and demonstration-only shortcut audit.

Python claims are checked here; independent protected-Racket evidence is emitted
by authoring preflight and handoff checks. No universal uniqueness claim.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

HERE=Path(__file__).resolve().parent

def load():
    s=importlib.util.spec_from_file_location('_c7_audit_adapter_'+str(HERE),HERE/'adapter.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def source_hashes():
    home=HERE.parents[1]
    return {p.relative_to(home).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(home.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and (p.suffix in ('.py','.rkt') or p.name=='promotion.json')}

def audit(seeds):
    if type(seeds) is not int or not 1<=seeds<=1024:raise ValueError('seeds must be 1..1024')
    a=load();hashes=source_hashes();failures=[];episodes=pairs=stress=differences=0;names=set();blue_masks=set();scales=set()
    for seed in range(seeds):
        baseline=None
        full={mode:a.generate(seed,{'replacement':mode},6,4) for mode in a.engine.SETTINGS}
        for mode,ep in full.items():
            inputs=[p['input'] for p in ep['train']+ep['test']]
            if baseline is not None and inputs!=baseline:failures.append({'seed':seed,'finding':'unmatched settings'})
            baseline=inputs
            if len({json.dumps(g) for g in inputs})!=10:failures.append({'seed':seed,'finding':'duplicate input'})
            predictions=[a.engine.rivals(g,mode) for g in inputs];names.update(predictions[0])
            for g in inputs:
                parsed=a.engine.parse(g);blue_masks.add(tuple(parsed['blue_mask']));scales.update(o['scale'] for o in parsed['objects'])
            for demos in range(2,7):
                e=a.generate(seed,{'replacement':mode},demos,4);episodes+=1;pairs+=demos+4
                if e['train']!=ep['train'][:demos] or e['test']!=ep['test']:
                    failures.append({'seed':seed,'demos':demos,'finding':'count-dependent prefix'})
                stress+=sum(len(g)==30 and len(g[0])==30 for g in inputs[6:])
                for r in predictions[0]:
                    if (all(predictions[i][r]==p['output'] for i,p in enumerate(e['train'])) and
                        any(predictions[6+i][r]!=p['output'] for i,p in enumerate(e['test']))):
                        failures.append({'seed':seed,'demos':demos,'setting':mode,'rival':r,'finding':'harmful survivor'})
                for p in e['train']+e['test']:
                    if a.engine.solve(p['input'],mode)!=p['output']:failures.append({'seed':seed,'finding':'claimed label mismatch'})
        differences+=sum(p['output']!=q['output'] for split in ('train','test') for p,q in zip(full['exchange'][split],full['minority'][split]))
    if hashes!=source_hashes():raise ValueError('source changed during audit')
    return {'schema':'bounded-public-family-audit-v1','task_id':a.engine.TASK_ID,'status':'passed' if not failures else 'failed',
            'source_hashes':hashes,'seed_range':[0,seeds-1],'demonstration_counts':[2,3,4,5,6],'queries':4,
            'episodes':episodes,'pairs':pairs,'exact_30x30_pairs':stress,'full_bank_output_differences':differences,
            'rival_count':len(names),'rivals':sorted(names),'primitive_blue_masks':len(blue_masks),'scales':sorted(scales),
            'failures':failures,'limits':'Finite Python-mirror audit, with independent Racket checks reported separately. No acceptance or training admission.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=64);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    r=audit(a.seeds);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:r[k] for k in ('status','episodes','pairs','exact_30x30_pairs','rival_count','primitive_blue_masks','scales','failures')}))
    raise SystemExit(0 if r['status']=='passed' else 1)
