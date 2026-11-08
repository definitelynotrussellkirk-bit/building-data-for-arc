"""Reusable finite lesson and protected-Racket audit."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

def load(path, name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--root',default='.')
    args=ap.parse_args();root=Path(args.root).resolve();base=Path(__file__).resolve().parent
    a=load(base/'adapter.py','_audit8a');f=load(base/'family.py','_audit8f')
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,ident,bridge=_real_evaluator(root/'shared/runtime')
    report={'schema':'8f3a5a89-audit-v1','backend':ident,'episodes':0,'labels':0,'rival_checks':0,'findings':[]}
    try:
      for seed in range(12):
       for setting in f.SETTINGS:
        e=a.generate(seed,{'contour':setting},2,4);report['episodes']+=1
        survivors=set(f.RIVALS)
        for p in e['train']:
         survivors={n for n in survivors if f.solve_rival(p['input'],setting,n)==p['output']}
        if survivors:report['findings'].append({'seed':seed,'setting':setting,'survivors':sorted(survivors)})
        report['rival_checks']+=len(f.RIVALS)*len(e['train'])
        for p in e['train']+e['test']:
         report['labels']+=1
         if apply(a.program({'contour':setting}),p['input'])!=p['output']:
          report['findings'].append({'seed':seed,'setting':setting,'kind':'racket_mismatch'})
    finally:bridge.close()
    Path(args.out).write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    if report['findings']:raise SystemExit(1)
if __name__=='__main__':main()
