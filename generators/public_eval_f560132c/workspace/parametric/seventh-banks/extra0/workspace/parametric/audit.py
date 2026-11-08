"""Replayable scoped structural, protected-label, rival, public-view and causal audit.

Run from this packet with review.py run python3 generators/TASK/workspace/parametric/audit.py
--out ../checks/TASK/audit. Add --preflight PATH --witness-out DIR after preflight.
All outputs are controller-private, except individual content-addressed public files.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
HOME=HERE.parents[1]
ROOT=HOME.parents[1]

def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

a=load('_jigsaw_audit_adapter','adapter.py')
pub=load('_jigsaw_audit_public','public_views.py')

def digest(value):
    return hashlib.sha256(pub.encoded(value)).hexdigest()

def write(path,value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def source_binding():
    paths=[p for p in HOME.rglob('*') if p.is_file() and '__pycache__' not in p.parts
           and (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json'))]
    return {'task_id':HOME.name,'files':[{'path':p.relative_to(ROOT).as_posix(),
      'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]}

def verify_binding(binding):
    for row in binding['files']:
        p=(ROOT/row['path']).resolve()
        if not p.is_relative_to(ROOT) or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Bound source drift: '+row['path'])

def structural(seeds):
    report={'episodes':0,'pairs':0,'public_turns':0,'stress_30x30':0,'failures':[],
            'seeds':list(seeds),'scope':'Finite declared grammar, not universal induction'}
    for seed in report['seeds']:
        matched=None
        for finish in a.SETTINGS:
            setting={'finish':finish};e=a.generate(seed,setting,6,4)
            inputs=[p['input'] for sp in ('train','test') for p in e[sp]]
            assert len(inputs)==10 and len({digest(g) for g in inputs})==10
            if matched is not None:assert matched==inputs
            matched=inputs
            assert all(len(a.family.arrangements(g,2))==1 for g in inputs)
            for sp in ('train','test'):
                assert all(p['output']==a.family.solve(p['input'],finish) for p in e[sp])
            assert any(len(g)==30 and len(g[0])==30 for g in inputs)
            views,order=pub.project(e,seed,4)
            one,first=pub.project(e,seed,1)
            assert one==views[:1] and first==order[:1]
            mutant=copy.deepcopy(e);mutant['program_solution']='PRIVATE CANARY'
            for pair in mutant['test']:pair['output']=[[9]]
            assert pub.project(mutant,seed,4)==(views,order)
            assert all(set(v)=={'train','test'} and len(v['test'])==1 and set(v['test'][0])=={'input'} for v in views)
            report['episodes']+=1;report['pairs']+=10;report['public_turns']+=4;report['stress_30x30']+=1
    return report

def audit(out,seeds):
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    binding=source_binding();report=structural(seeds)
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    report.update(source_binding=binding,racket=identity,racket_evaluations=0,rival_checks=[],exports=[])
    try:
        for seed in (17,43):
            for finish in a.SETTINGS:
                settings={'finish':finish};e=a.generate(seed,settings,2,4)
                pairs=e['train']+e['test']
                for pair in pairs:
                    actual=_grid(apply(e['program_solution'],pair['input']));report['racket_evaluations']+=1
                    assert actual==pair['output'],('selected label mismatch',seed,settings)
                for name,program in a.rival_programs(settings).items():
                    labels=[_grid(apply(program,p['input'])) for p in pairs]
                    report['racket_evaluations']+=len(pairs)
                    fits=all(x==p['output'] for x,p in zip(labels[:2],e['train']))
                    harms=any(x!=p['output'] for x,p in zip(labels[2:],e['test']))
                    report['rival_checks'].append({'seed':seed,'settings':settings,'rival':name,
                       'program_sha256':hashlib.sha256(program.encode()).hexdigest(),
                       'fits_all_demonstrations':fits,'differs_on_query':harms,'all_executions_valid':True})
                    assert not (fits and harms),('Harmful rival survives',seed,settings,name)
                mapping=pub.export(e,out/f'public-{seed}-{finish}',seed)
                pub.verify(out/f'public-{seed}-{finish}')
                report['exports'].append(mapping)
    finally:bridge.close()
    verify_binding(binding)
    report['status']='passed';report['harmful_survivors']=sum(x['fits_all_demonstrations'] and x['differs_on_query'] for x in report['rival_checks'])
    write(out/'audit.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_binding','racket','rival_checks','exports')}))
    return report

def witness(preflight,out):
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    receipt=json.loads(Path(preflight).read_text());verify_binding(receipt['source_binding'])
    execution=json.loads(Path(preflight).with_name('execution.json').read_text())
    episode=next(e for e in execution['episodes'] if e['settings']['finish']=='mark_junctions')
    pair=next(p for p in episode['test'] if len(p['input'])==30 and len(p['input'][0])==30);settings=episode['settings']
    selected=a.program(settings);counter=a.rival_programs(settings)['regular_blocks']
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        output=apply(selected,pair['input']);alternative=apply(counter,pair['input'])
    finally:bridge.close()
    assert output==pair['output'] and output!=alternative
    descriptions={
      'step_a':'Recover the square guide and solve the rotated-piece exact-cover jigsaw, then recolor every assembled piece by its spatial key entry.',
      'intermediate':'The completed piece mosaic with its actual staggered and interlocking colored seams.',
      'step_b':'Mark cells whose closed four-neighborhood contains at least three distinct colors.',
      'why_b_depends_on_a':'Separate source pieces do not expose assembled contacts. An enlarged regular-block guide has different junctions from the solved jigsaw, so it cannot replace the reconstructed spatial intermediate.'}
    result={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':receipt['source_binding'],
      'racket':{'backend':'racket','protected':True},**descriptions,
      'cases':[{'input':pair['input'],'settings':settings,
         'intermediate_value':{'assembled':a.family.solve(pair['input']),'key':a.family.parse(pair['input'])[1]},
         'program':selected,'output':output,'counterfactual_program':counter,
         'counterfactual_output':alternative,'ablation':'wrong_intermediate'}],
      'authority':'reviewer-authored causal interpretation; no owner acceptance'}
    validate_sequential_witness({'sequential_dependency':{**descriptions,'witness_path':'witness.json'}},receipt,
                                lambda _:json.dumps(result).encode())
    replay=replay_witness(ROOT,result)
    replay['engine_status']=replay['status'];replay['status']='reviewer_replayed'
    replay['authority']='Executed by reviewer; helper naming does not grant owner acceptance.'
    verify_binding(receipt['source_binding'])
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    write(out/'witness.json',result);write(out/'replay.json',replay)
    print(json.dumps({'status':'reviewer_replayed','cells_changed':sum(x!=y for r,s in zip(output,alternative) for x,y in zip(r,s))}))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path)
    p.add_argument('--seed-count',type=int,default=16);p.add_argument('--preflight',type=Path)
    p.add_argument('--witness-out',type=Path);args=p.parse_args()
    if args.preflight:
        if args.witness_out is None:p.error('--witness-out is required')
        witness(args.preflight,args.witness_out)
    else:
        if args.out is None or not 1<=args.seed_count<=256:p.error('Need --out and seed-count 1..256')
        audit(args.out,list(range(args.seed_count)))
