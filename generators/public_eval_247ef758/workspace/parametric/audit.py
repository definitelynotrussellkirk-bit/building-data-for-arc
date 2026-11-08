"""Executable finite-rival audit of matched-marker placement lessons."""
from pathlib import Path
import importlib.util
import hashlib
import json
import sys
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_placement_audit_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:16],BASE/'adapter.py')
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)

def audit(seeds=range(16),demo_counts=(2,3,6)):
    counts=dict(episodes=0,labeled_pairs=0,maximum_size_episodes=0)
    rivals=a.sampler.RIVALS;failures=[];rejected={n:0 for n in rivals};equivalent={n:0 for n in rivals};attempts=[]
    for seed in seeds:
        attempts.append({'seed':seed,'rejected_demo_draws':a.sampler.teaching_seed(seed)[1]})
        for demos in demo_counts:
            previous=None
            for mode in ('source_order','largest_first'):
                e=a.generate(seed,{'overlap_priority':mode},demos,4)
                inputs=[p['input'] for sp in ('train','test') for p in e[sp]]
                if previous is not None and inputs!=previous:failures.append(dict(seed=seed,error='input drift'))
                previous=inputs;counts['episodes']+=1;counts['labeled_pairs']+=demos+4
                q=next(p for p in e['test'] if len(p['input'])==len(p['input'][0])==30);sep,_=a.sampler.records(q['input'])
                assert len(q['input'])==len(q['input'][0])==30
                substantive=sum(q['output'][r][c]!=0 for r in range(1,29) for c in range(sep+2,29))
                if substantive<75:failures.append(dict(seed=seed,error='weak maximum case',occupied_interior=substantive))
                counts['maximum_size_episodes']+=1
                for name in rivals:
                    survives=all(a.sampler.predict(p['input'],mode,name)==p['output'] for p in e['train'])
                    if survives:
                        bad=[i for i,p in enumerate(e['test']) if a.sampler.predict(p['input'],mode,name)!=p['output']]
                        if bad:failures.append(dict(seed=seed,demos=demos,mode=mode,rival=name,queries=bad))
                        else:equivalent[name]+=1
                    else:rejected[name]+=1
    return dict(schema='task-finite-rival-audit-v1',**counts,rivals=list(rivals),failures=failures,
                rejected_by_demos=rejected,query_equivalent_survivals=equivalent,teaching_draws=attempts,
                limits='Finite Python rival hypotheses; protected label parity is separate. Teaching selection uses demonstrations only, not any query. No universal uniqueness claim.')

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=16);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();result=audit(range(args.seeds));args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));raise SystemExit(bool(result['failures']))
