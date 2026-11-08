"""Bounded, rerunnable structural/Racket/public and source-bound causal audit.

Run through the packet's review.py run wrapper. Output directories must be new.
This tool supplies author evidence, never owner acceptance or training admission.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
ROOT=HOME.parents[1]
TASK=HOME.name

def local(name):
    spec=importlib.util.spec_from_file_location('_'+TASK+'_'+name,BASE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def write(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def source_hashes():
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(HOME.rglob('*')) if p.is_file() and p.suffix in ('.py','.rkt') and '__pycache__' not in p.parts}

def audit(out,seeds):
    f=local('family'); pub=local('publication');out=Path(out);out.mkdir(parents=True,exist_ok=False)
    before=source_hashes(); episodes=pairs=turns=0;view_batch=[];records=[]
    for seed in range(seeds):
        matched=None
        for finish in f.SETTINGS:
            ep=f.generate(seed,{'finish':finish},6,4)
            ins=[p['input'] for s in ('train','test') for p in ep[s]]
            assert len({json.dumps(g) for g in ins})==10
            if matched is not None:assert ins==matched
            matched=ins
            for n in range(2,7):
                for q in (1,4):
                    small=f.generate(seed,{'finish':finish},n,q)
                    assert small['train']==ep['train'][:n] and small['test']==ep['test'][:q]
            for name in f.rival_names(finish):
                assert any(f.rival(p['input'],finish,name)!=p['output'] for p in ep['train'][:2]),(seed,finish,name)
            for i in range(4):
                view=f.public_turn(ep,i);pub.encode(view);turns+=1
            assert f.public_turn(f.generate(seed,{'finish':finish},2,1))==f.public_turn(f.generate(seed,{'finish':finish},2,4))
            assert any(len(p['input'])==len(p['input'][0])==30 for p in ep['test'])
            episodes+=1;pairs+=10
    from arcpuzzles.parametric_worker import _real_evaluator
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime');evals=0;cache={}
    def run(program,g):
        nonlocal evals
        key=(program,json.dumps(g))
        if key not in cache:
            cache[key]=apply(program,g);evals+=1
        return cache[key]
    try:
        for seed in (17,43):
            for finish in f.SETTINGS:
                ep=f.generate(seed,{'finish':finish},2,4)
                for split in ('train','test'):
                    for pair in ep[split]:
                        assert run(ep['program_solution'],pair['input'])==pair['output'],(seed,finish,split)
                rival_rows=[]
                for name in f.rival_names(finish):
                    rp=f.rival_program(finish,name);outputs=[run(rp,p['input']) for p in ep['train']]
                    assert outputs==[f.rival(p['input'],finish,name) for p in ep['train']],('rival parity',seed,finish,name)
                    killed=[i for i,(p,o) in enumerate(zip(ep['train'],outputs)) if o!=p['output']]
                    assert killed,(seed,finish,name)
                    rival_rows.append({'name':name,'program_sha256':hashlib.sha256(rp.encode()).hexdigest(),'refuting_demo_indices':killed})
                records.append({'seed':seed,'settings':{'finish':finish},'rivals':rival_rows})
                view_batch += [f.public_turn(ep,i) for i in range(4)]
    finally:bridge.close()
    public_ids=pub.publish(view_batch,out/'public');assert pub.verify(out/'public')==16
    assert before==source_hashes(),'source drift'
    report={'schema':'public-family-adversarial-audit-v1','task_id':TASK,'status':'passed','source_sha256':before,
      'structural_seeds':list(range(seeds)),'episodes':episodes,'labeled_pairs':pairs,'public_turns_checked':turns,
      'protected_racket_evaluations':evals,'racket':identity,'jobs':records,'harmful_declared_rival_survivors':0,
      'saved_public_files':public_ids,'limits':'Finite generated grammar and named rivals only; no unseen evaluation, owner acceptance or training admission.'}
    write(out/'audit.json',report);print(json.dumps({k:report[k] for k in ('status','episodes','labeled_pairs','public_turns_checked','protected_racket_evaluations')}))

DEPENDENCY={
 'step_a':'Recover the guide-edge dihedral map, crop the payload, and orient it to the outer frame.',
 'intermediate':'The oriented payload and its newly designated top boundary.',
 'step_b':'Flood-fill only zero components connected orthogonally to that top boundary with the dominant payload color.',
 'why_b_depends_on_a':'The frame-derived transform changes which source boundary is top. Sealing source-top notches before orientation selects a different connected region.'}

def witness(out,preflight):
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    f=local('family');out=Path(out);out.mkdir(parents=True,exist_ok=False)
    q=json.loads(Path(preflight).read_text());execution=json.loads(Path(preflight).with_name('execution.json').read_text())
    for row in q['source_binding']['files']:
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256']
    candidates=[(e,p) for e in execution['episodes'] if e['settings']['finish']=='seal_top' for s in ('train','test') for p in e[s]]
    candidates.sort(key=lambda ep:-len(ep[1]['input'])*len(ep[1]['input'][0]))
    e,p=next((e,p) for e,p in candidates if f.rival(p['input'],'seal_top','wrong_order')!=p['output'])
    cp=f.rival_program('seal_top','wrong_order');apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        actual=apply(e['program_solution'],p['input']);wrong=apply(cp,p['input'])
        assert actual==p['output'] and wrong!=actual
    finally:bridge.close()
    case={'input':p['input'],'settings':e['settings'],'intermediate_value':f.solve(p['input']),
      'program':e['program_solution'],'output':actual,'counterfactual_program':cp,'counterfactual_output':wrong,'ablation':'wrong_order'}
    value={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':q['source_binding'],
      'racket':{'backend':'racket','protected':True},**DEPENDENCY,'cases':[case]}
    raw=json.dumps(value).encode()
    validate_sequential_witness({'sequential_dependency':{**DEPENDENCY,'witness_path':'witness.json'}},q,lambda _:raw)
    replay=replay_witness(ROOT,value,timeout=60);replay['status']='reviewer_replayed';replay['authority']='author replay, not owner acceptance'
    write(out/'witness.json',value);write(out/'replay.json',replay)
    print(json.dumps({'status':replay['status'],'changed_cells':sum(a!=b for ra,rb in zip(actual,wrong) for a,b in zip(ra,rb)),'input_size':[len(p['input']),len(p['input'][0])]}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['audit','witness']);parser.add_argument('--out',required=True);parser.add_argument('--seeds',type=int,default=32);parser.add_argument('--preflight')
    args=parser.parse_args()
    if args.mode=='audit':
        if not 1<=args.seeds<=256:parser.error('seeds must be 1..256')
        audit(args.out,args.seeds)
    else:
        if not args.preflight:parser.error('--preflight required')
        witness(args.out,args.preflight)
