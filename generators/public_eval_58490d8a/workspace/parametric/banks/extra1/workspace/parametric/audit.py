"""Finite demonstration-only rival audit. No universal uniqueness claim."""
import argparse
import importlib.util
import json
from pathlib import Path
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_58490_audit_adapter',BASE/'adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)

def audit(seeds,demo_counts):
    failures=[];lessons=0;pairs=0;equivalences=[]
    for seed in seeds:
        for demos in demo_counts:
            for scope in A.CORE.SCOPES:
                e=A.generate(seed,{'count_scope':scope},demos,4);lessons+=1;pairs+=demos+4
                for rival in A.CORE.RIVALS:
                    if rival==scope:continue
                    # Fit depends only on observed demonstration labels.
                    if all(A.CORE.solve(p['input'],scope,rival)==p['output'] for p in e['train']):
                        changed=[i for i,p in enumerate(e['test']) if A.CORE.solve(p['input'],scope,rival)!=p['output']]
                        row={'seed':seed,'demos':demos,'scope':scope,'rival':rival,'changed_queries':changed}
                        (failures if changed else equivalences).append(row)
    return {'status':'failed' if failures else 'passed','seeds':list(seeds),'demo_counts':list(demo_counts),
            'lessons':lessons,'pairs':pairs,'rivals':list(A.CORE.RIVALS),'failures':failures,
            'equivalent_survivors':equivalences,'execution':'finite Python claim/rival audit; protected Racket checked separately'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=32);a=p.parse_args()
    report=audit(list(range(a.seeds)),[2,3,6]);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('failures','equivalent_survivors','seeds')}));raise SystemExit(bool(report['failures']))
