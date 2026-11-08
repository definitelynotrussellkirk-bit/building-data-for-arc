"""Reusable finite lesson and protected-Racket audit."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--root',default='.');x=ap.parse_args();root=Path(x.root).resolve();b=Path(__file__).resolve().parent
 a=load(b/'adapter.py','_a581');f=load(b/'family.py','_f581')
 from arcpuzzles.parametric_worker import _real_evaluator
 run,ident,bridge=_real_evaluator(root/'shared/runtime');rep={'schema':'581f7754-audit-v1','backend':ident,'episodes':0,'labels':0,'rival_checks':0,'findings':[]}
 try:
  for seed in range(12):
   for setting in f.SETTINGS:
    e=a.generate(seed,{'assignment':setting},2,4);rep['episodes']+=1;sur=set(f.RIVALS)
    for p in e['train']:sur={n for n in sur if f.solve_rival(p['input'],setting,n)==p['output']}
    rep['rival_checks']+=len(f.RIVALS)*len(e['train'])
    if sur:rep['findings'].append({'seed':seed,'setting':setting,'survivors':sorted(sur)})
    for p in e['train']+e['test']:
     rep['labels']+=1
     if run(a.program({'assignment':setting}),p['input'])!=p['output']:rep['findings'].append({'seed':seed,'setting':setting,'kind':'racket_mismatch'})
 finally:bridge.close()
 Path(x.out).write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
 if rep['findings']:raise SystemExit(1)
if __name__=='__main__':main()
