#!/usr/bin/env python3
"""Reproduce the bounded bridge/border audit using protected Racket labels."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('border_audit_adapter',HERE/'adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)

def run(seeds=16):
    from reviewer_support import find_root
    from arcpuzzles.parametric_worker import _real_evaluator
    if type(seeds) is not int or not 1<=seeds<=64:raise ValueError('seeds must be 1..64')
    root=find_root(__file__);failures=[];episodes=0;pairs=0;unique=set();sizes=set();before_after=set();survivors={}
    for seed in range(seeds):
        for demos in range(2,7):
            for setting in A.SETTINGS:
                ep=A.generate(seed,{'preprocess':setting},demos,4);check=A.teaching(ep);episodes+=1
                survivors.setdefault(setting,set()).update(check['survivors'])
                if not check['passed']:failures.append({'seed':seed,'demos':demos,'setting':setting,'teaching':check})
                for split in ('train','test'):
                    for p in ep[split]:
                        g=p['input'];pairs+=1;unique.add(hashlib.sha256(json.dumps(g).encode()).hexdigest());sizes.add((len(g),len(g[0])))
                        before_after.add((len(A.components(g)),len(A.components(A.recolor(g)))))
                for i in range(4):
                    v=A.public_turn(ep,i)
                    if set(v)!= {'train','test'} or len(v['test'])!=1 or set(v['test'][0])!= {'input'}:
                        failures.append({'kind':'public projection'})
    apply,identity,bridge=_real_evaluator(root/'shared/runtime');executions=[];causal=[];contact=[]
    try:
        for setting in A.SETTINGS:
            # Include minimum and maximum demo counts and all four query shapes.
            ep=A.generate(17,{'preprocess':setting},6,4)
            for split in ('train','test'):
                for i,p in enumerate(ep[split]):
                    actual=apply(ep['program_solution'],p['input'])
                    if actual!=p['output']:failures.append({'kind':'racket_parity','setting':setting,'split':split,'pair':i})
                    executions.append({'setting':setting,'split':split,'index':i,'input':p['input'],'output':actual})
        ep=A.generate(0,{'preprocess':'gray_to_blue'},2,4)
        for i,p in enumerate(ep['test']):
            before=apply(ep['program_solution'],p['input']);wrong=apply(A.counterfactual_program(),p['input'])
            if before==wrong:failures.append({'kind':'causal','query':i})
            causal.append({'input':p['input'],'output':before,'counterfactual_output':wrong,
                           'changed_cells':sum(a!=b for ra,rb in zip(before,wrong) for a,b in zip(ra,rb)),
                           'before_components':len(A.components(p['input'])),
                           'after_components':len(A.components(A.recolor(p['input'])))})
        # Before/after evidence for the newly repaired color-boundary lesson.
        canonical_body=A.program({'preprocess':'none'})[len('(rule! '):-1]
        binary_program='(rule! (lambda (g) (let* ((after (recolor g 5 1)) (mono (build-grid (rows g) (cols g) (r c) (if (= (at after r c) 0) 0 1))) (mask (let ((g mono)) '+canonical_body+'))) (build-grid (rows g) (cols g) (r c) (if (= (at mask r c) 0) 0 (at after r c))))))'
        old=json.loads((HERE/'fixtures/color-contact-before.json').read_text())['input']
        new=A.generate(17,{'preprocess':'gray_to_blue'},2,4)['train'][0]['input']
        for phase,g in [('before',old),('after',new)]:
            actual=apply(A.program({'preprocess':'gray_to_blue'}),g)
            wrong=apply(binary_program,g)
            if wrong!=A.rival(g,'ignore_colors_after'):failures.append({'kind':'binary_rival_parity'})
            contact.append({'phase':phase,'input':g,'output':actual,'rival_output':wrong,'equal':actual==wrong})
        if not contact[0]['equal'] or contact[1]['equal']:failures.append({'kind':'color_contact_regression'})
    finally:bridge.close()
    return {'schema':'task-native-border-audit-v1','task_id':A.TASK,'seeds':seeds,'demo_counts':list(range(2,7)),
            'episodes':episodes,'labeled_pair_claims':pairs,'distinct_input_grids':len(unique),'policies':len(A.POLICIES),
            'survivors':{k:sorted(v) for k,v in survivors.items()},'sizes':sorted(sizes),'component_counts_before_after':sorted(before_after),
            'failures':failures,'passed':not failures,'racket':identity,'racket_evaluations':len(executions)+2*len(causal)+2*len(contact),
            'executions':executions,'causal_cases':causal,'color_contact_regression':contact,'color_contact_rival_program':binary_program,
            'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'adapter.py',HERE/'canonical.rkt',HERE/'promotion.json']},
            'limits':'Finite declared policies and sampled seeds only. Recolor changes connectivity before border filtering. No owner acceptance or training admission.'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seeds',type=int,default=16);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    r=run(a.seeds);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('passed','episodes','labeled_pair_claims','distinct_input_grids','policies','racket_evaluations','failures')}))
    return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
