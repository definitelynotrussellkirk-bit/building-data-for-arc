"""Bounded reusable lesson, prefix, Racket parity and public-byte audit.

Run through review.py run. The public directory contains individually hashed
one-query views; the directory listing and audit report are controller-private.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
ROOT=BASE.parents[3]
for p in (ROOT/'src',ROOT/'shared/runtime'):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
NAME='_audit_adapter_'+hashlib.sha256(str(BASE).encode()).hexdigest()
spec=importlib.util.spec_from_file_location(NAME,BASE/'adapter.py')
adapter=importlib.util.module_from_spec(spec);sys.modules[NAME]=adapter;spec.loader.exec_module(adapter)


def inventory():
    return [{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(HOME.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','rivals.json','public-parent.json'))]


def audit(seeds,output,*,racket_seeds=2):
    from reviewer_support import public_challenge_bytes,public_challenge_id
    from arcpuzzles.parametric_worker import _real_evaluator
    adapter.family.integer(seeds,1,256,'seeds');adapter.family.integer(racket_seeds,0,seeds,'racket seeds')
    output=Path(output)
    if output.exists():raise ValueError('Choose a fresh output directory')
    contract=json.loads((BASE/'promotion.json').read_text());key=next(iter(contract['parameters']))
    programs=json.loads((BASE/'rivals.json').read_text());before=inventory()
    counts={'episodes':0,'prefix_checks':0,'public_views':0,'rival_checks':0,'racket_evaluations':0}
    findings=[];public={};stress=[];first_shapes=set();bridge=None;identity=None
    if racket_seeds:apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        for seed in range(seeds):
            matched=None
            for setting in adapter.family.SETTINGS:
                settings={key:setting};full=adapter.generate(seed,settings,6,4);counts['episodes']+=1
                all_inputs=[p['input'] for sp in ('train','test') for p in full[sp]]
                if len({json.dumps(g) for g in all_inputs})!=10:findings.append({'kind':'duplicate_input','seed':seed,'settings':settings})
                if matched is not None and all_inputs!=matched:findings.append({'kind':'unmatched_settings','seed':seed})
                matched=all_inputs
                for d in range(2,7):
                    for q in range(1,5):
                        prefix=adapter.generate(seed,settings,d,q);counts['prefix_checks']+=1
                        if prefix['train']!=full['train'][:d] or prefix['test']!=full['test'][:q]:findings.append({'kind':'prefix','seed':seed,'demos':d,'queries':q})
                for rival in adapter.family.RIVALS:
                    counts['rival_checks']+=1
                    fits=all(adapter.family.rival(p['input'],setting,rival)==p['output'] for p in full['train'][:2])
                    if fits and any(adapter.family.rival(p['input'],setting,rival)!=p['output'] for p in full['test']):
                        findings.append({'kind':'dangerous_survivor','seed':seed,'settings':settings,'rival':rival})
                public_episode={'train':full['train'][:2],'test':full['test'],'program_solution':full['program_solution']}
                for j,pair in enumerate(full['test']):
                    view=adapter.public_view(public_episode,j);counts['public_views']+=1
                    changed=copy.deepcopy(public_episode)
                    changed.update(settings={'hidden':9},seed=-5,program_solution='REDACTED')
                    for p in changed['test']:p['output']=[[8]]
                    for k in range(len(changed['test'])):
                        if k!=j:changed['test'][k]['input']=[[9]]
                    if view!=adapter.public_view(changed,j):findings.append({'kind':'privacy','seed':seed,'query':j})
                    raw=public_challenge_bytes(view);identifier=public_challenge_id(view)
                    if seed<2:
                        if identifier in public:findings.append({'kind':'duplicate_public_payload','seed':seed})
                        public[identifier]=raw
                    if max(len(pair['input']),len(pair['input'][0]),len(pair['output']),len(pair['output'][0]))==30:
                        stress.append({'seed':seed,'settings':settings,'query':j,'input_shape':[len(pair['input']),len(pair['input'][0])],
                                       'output_shape':[len(pair['output']),len(pair['output'][0])],
                                       'foreground_input':sum(v!=7 for row in pair['input'] for v in row)})
                first_shapes.add((len(full['test'][0]['input']),len(full['test'][0]['input'][0])))
                if seed<racket_seeds:
                    for sp in ('train','test'):
                        for pair in full[sp]:
                            actual=apply(full['program_solution'],pair['input']);counts['racket_evaluations']+=1
                            if actual!=pair['output']:findings.append({'kind':'racket_label','seed':seed,'settings':settings,'split':sp})
                    for rival in adapter.family.RIVALS:
                        for pair in full['train'][:2]+full['test']:
                            actual=apply(programs[setting][rival],pair['input']);counts['racket_evaluations']+=1
                            if actual!=adapter.family.rival(pair['input'],setting,rival):findings.append({'kind':'rival_parity','seed':seed,'rival':rival,'settings':settings})
    finally:
        if bridge:bridge.close()
    if inventory()!=before:raise ValueError('Source changed during audit')
    if len(stress)!=seeds*len(adapter.family.SETTINGS):findings.append({'kind':'missing_stress'})
    result={'schema':'arcpuzzles-bounded-authoring-audit-v1','task_id':HOME.name,
            'status':'passed' if not findings else 'failed','source_binding':{'task_id':HOME.name,'files':before},
            'seed_range':[0,seeds-1],**counts,'rivals':list(adapter.family.RIVALS),'findings':findings,
            'first_query_shapes':sorted(first_shapes),'stress_cases':stress,'racket':identity,
            'limits':'Finite listed hypotheses only; not universal uniqueness, owner acceptance or training admission.'}
    output.mkdir(parents=True);(output/'public').mkdir()
    for identifier,raw in sorted(public.items()):(output/'public'/f'{identifier}.json').write_bytes(raw)
    (output/'audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds',type=int,default=32);parser.add_argument('--racket-seeds',type=int,default=2)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    result=audit(args.seeds,args.out,racket_seeds=args.racket_seeds)
    print(json.dumps({k:result[k] for k in ('task_id','status','episodes','prefix_checks','public_views','racket_evaluations','findings')}))
    if result['findings']:raise SystemExit(1)

if __name__=='__main__':main()
