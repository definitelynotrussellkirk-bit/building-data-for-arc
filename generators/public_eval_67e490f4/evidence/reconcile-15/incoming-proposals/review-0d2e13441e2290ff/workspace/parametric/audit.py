"""Finite demonstration-only audit, with executable total alternative policies."""
from pathlib import Path
import importlib.util,json,argparse
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_67_audit_adapter',P/'adapter.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
RIVALS=['most_frequent','least_frequent','global_frequency','area_only','bbox_only','orientation_exact','rotations_only','pixel_frequency','smallest_color','largest_color','largest_tie','first_source','last_source']
def predict(g,name,value):
    return a.model.solve(g,name) if name in a.VALUES else a.model.solve(g,value,name)
def audit(seeds=range(32),demo_counts=(2,3,6)):
    seeds=list(seeds);demo_counts=list(demo_counts);failures=[];episodes=0;pairs=0;harmless=0
    for seed in seeds:
        for demos in demo_counts:
            for value in a.VALUES:
                e=a.generate(seed,{'vote_rule':value},demos,4);episodes+=1;pairs+=demos+4
                for name in RIVALS:
                    if name==value:continue
                    if all(predict(p['input'],name,value)==p['output'] for p in e['train']):
                        bad=[i for i,p in enumerate(e['test']) if predict(p['input'],name,value)!=p['output']]
                        if bad:failures.append({'seed':seed,'demos':demos,'setting':value,'rival':name,'queries':bad})
                        else:harmless+=1
    return {'status':'passed' if not failures else 'failed','seeds':seeds,'demo_counts':demo_counts,'episodes':episodes,'pairs':pairs,'rivals':RIVALS,'harmless_equivalent_survivors':harmless,'failures':failures,'backend':'python finite-rival predictions; protected Racket is separate'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--seeds',type=int,default=32);args=p.parse_args();r=audit(range(args.seeds));args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(bool(r['failures']))
