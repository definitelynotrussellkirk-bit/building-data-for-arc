"""Bounded sampler and demonstration-only rival audit; not owner acceptance.

Predictions are cached per input so all supported demonstration counts can be
checked without repeating the parser. Python predictions remain claims; the
separate protected-Racket preflight and causal replay supply executed labels.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

HERE=Path(__file__).resolve().parent

def load():
    s=importlib.util.spec_from_file_location('_edb_audit_family_'+str(HERE),HERE/'family.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def source_hashes():
    home=HERE.parents[1]
    return {p.relative_to(home).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(home.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and (p.suffix in ('.py','.rkt') or p.name=='promotion.json')}

def audit(seeds):
    if type(seeds) is not int or not 1<=seeds<=1024:raise ValueError('seeds must be 1..1024')
    m=load();hashes=source_hashes();failures=[];episodes=pairs=stress=differences=0
    for seed in range(seeds):
        full={v:m.generate(seed,{m.PARAMETER:v},6,4) for v in m.VALUES}
        inputs=[p['input'] for p in full[m.VALUES[0]]['train']+full[m.VALUES[0]]['test']]
        if len({json.dumps(g) for g in inputs})!=10:failures.append({'seed':seed,'finding':'duplicate input'})
        predictions={r:[m.predict(g,r) for g in inputs] for r in m.RIVALS}
        for demos in range(2,7):
            for mode in m.VALUES:
                ep=m.generate(seed,{m.PARAMETER:mode},demos,4);episodes+=1;pairs+=demos+4
                if ep['train']!=full[mode]['train'][:demos] or ep['test']!=full[mode]['test']:
                    failures.append({'seed':seed,'setting':mode,'demos':demos,'finding':'count-dependent prefix'})
                actual_inputs=[p['input'] for p in ep['train']+ep['test']]
                if actual_inputs!=inputs[:demos]+inputs[6:]:failures.append({'seed':seed,'finding':'setting-dependent inputs'})
                stress+=sum(len(g)==30 and len(g[0])==30 for g in actual_inputs[demos:])
                for rival,outputs in predictions.items():
                    if (rival!=mode and outputs[:demos]==predictions[mode][:demos]
                            and outputs[6:]!=predictions[mode][6:]):
                        failures.append({'seed':seed,'demos':demos,'setting':mode,'finding':'harmful rival','rival':rival})
                if [p['output'] for p in ep['train']+ep['test']]!=predictions[mode][:demos]+predictions[mode][6:]:
                    failures.append({'seed':seed,'finding':'incorrect claimed label'})
            differences+=sum(a!=b for a,b in zip(predictions['once'][:demos]+predictions['once'][6:],
                                                  predictions['terminal'][:demos]+predictions['terminal'][6:]))
    if hashes!=source_hashes():raise ValueError('source drift during audit')
    return {'schema':'bounded-public-family-audit-v1','task_id':m.TASK_ID,'status':'passed' if not failures else 'failed',
            'source_hashes':hashes,'seed_range':[0,seeds-1],'demonstration_counts':[2,3,4,5,6],'queries':4,
            'episodes':episodes,'pairs':pairs,'exact_30x30_pairs':stress,'setting_output_differences':differences,
            'rival_count':len(m.RIVALS),'rivals':list(m.RIVALS),'failures':failures,
            'limits':'Finite Python mirror audit. Protected Racket execution is separate; no uniqueness or training claim.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    r=audit(a.seeds);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:r[k] for k in ('status','episodes','pairs','exact_30x30_pairs','rival_count','failures')}))
    raise SystemExit(0 if r['status']=='passed' else 1)
