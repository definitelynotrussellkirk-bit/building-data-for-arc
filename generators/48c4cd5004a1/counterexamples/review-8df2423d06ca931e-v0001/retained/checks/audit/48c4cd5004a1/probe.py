#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, importlib.util, json
from collections import Counter
from pathlib import Path

TASK='48c4cd5004a1'
ROOT=Path(__file__).resolve().parents[3]
GEN=ROOT/'repo/generators'/TASK/'generator.py'

def load_gen():
    spec=importlib.util.spec_from_file_location('audit_48_gen',GEN)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def icons_and_special(g):
    h,w=len(g),len(g[0]); icons=[]; special=set()
    for r in range(h-2):
        for c in range(w-2):
            ring=[g[r+dr][c+dc] for dr,dc in ((0,0),(0,1),(0,2),(1,0),(1,2),(2,0),(2,1),(2,2))]
            ctr=g[r+1][c+1]
            if ring[0] and ctr and ctr!=ring[0] and all(x==ring[0] for x in ring):
                icons.append((r,c,ring[0],ctr))
                special.update((r+dr,c+dc) for dr in range(3) for dc in range(3))
    return icons,special

def any_dot_rival(g):
    icons,special=icons_and_special(g); h,w=len(g),len(g[0])
    dots={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v and (r,c) not in special}
    for r,c,b,ctr in icons:
        cells=((r+dr,c+dc) for dr in range(3) for dc in range(3))
        if any((rr+dr,cc+dc) in dots for rr,cc in cells for dr,dc in ((-1,0),(1,0),(0,-1),(0,1))):
            return [[b,b,b],[b,ctr,b],[b,b,b]]
    raise AssertionError('no icon touched by any outside dot')

def frozen(g): return tuple(tuple(row) for row in g)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mode',choices=['prepare','finish'],required=True); ap.add_argument('--racket',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gen=load_gen(); base=a.out.parent
    if a.mode=='prepare':
        cases=[]
        for band in ('easy','medium','hard'):
            for seed in range(20):
                g=gen.generate(seed,0,difficulty=band)
                cases.append({'band':band,'seed':seed,'sample_index':0,'input':g,'rival_output':any_dot_rival(g),'self_check':gen.self_check(g,difficulty=band)})
        (base/'generated_inputs.json').write_text(json.dumps({'inputs':[c['input'] for c in cases]},indent=2)+'\n')
        a.out.write_text(json.dumps({'schema':'audit_48_prepare/1','generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),'cases':cases},indent=2)+'\n')
        print(json.dumps({'prepared':len(cases),'unique':len({frozen(c['input']) for c in cases}),'out':str(a.out)}))
        return
    prepared=json.loads((base/'generated_prepare.json').read_text()); racket=json.loads(a.racket.read_text())
    results=racket['results']; assert len(results)==len(prepared['cases'])
    matches=0; validator_pass=0; by_band=Counter(); disagreements=[]
    for case,res in zip(prepared['cases'],results):
        if not case['self_check']: validator_pass+=1
        if case['rival_output']==res['output']:
            matches+=1; by_band[case['band']]+=1
        else: disagreements.append({'band':case['band'],'seed':case['seed'],'actual':res['output'],'rival':case['rival_output']})
    counter_input=json.loads((base/'input.json').read_text()); counter_racket=json.loads((base/'racket.json').read_text())['results'][0]['output']
    counter_rival=any_dot_rival(counter_input)
    genmod=load_gen()
    report={
      'schema':'audit_48c4cd5004a1/1','task_id':TASK,
      'generator_sha256':prepared['generator_sha256'],'rule_hash':racket['executed_rule_hash'],'rule_text_sha256':racket['rule_text_sha256'],
      'generated_sample':{'denominator':len(results),'unique_inputs':len({frozen(c['input']) for c in prepared['cases']}),'validator_pass':validator_pass,'rival_matches_racket':matches,'matches_by_band':dict(by_band),'disagreements':disagreements},
      'counterexample':{'input':counter_input,'self_check':genmod.self_check(counter_input),'racket_output':counter_racket,'any_dot_rival_output':counter_rival,'disagrees':counter_racket!=counter_rival,'input_sha256':json.loads((base/'racket.json').read_text())['results'][0]['input_sha256'],'output_sha256':json.loads((base/'racket.json').read_text())['results'][0]['output_sha256']},
      'finding':'Minority dots are never adjacent to distractor icons, so any-dot adjacency is answer-equivalent on sampled ordinary support although majority frequency is semantically required.'
    }
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n'); print(json.dumps({'matches':matches,'total':len(results),'counterexample_disagrees':report['counterexample']['disagrees'],'out':str(a.out)}))
if __name__=='__main__': main()
