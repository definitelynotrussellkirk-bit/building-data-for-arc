"""Source-pinned finite-rival, Racket, privacy and causal audit.

From the repository (through review.py run):
 python generators/public_eval_7ed72f31/workspace/parametric/audit.py \
   --preflight ../checks/public_eval_7ed72f31/preflight/preflight.json \
   --out ../checks/public_eval_7ed72f31/audit --seeds 64
The output is private controller evidence, NOT a model-visible dataset.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

DEPENDENCY = {
 'step_a':'Recover the background, eight-connected marker/source groups, each red marker bounding box and its source-colored cells.',
 'intermediate':'Per-group marker geometry (point, horizontal or vertical), doubled midpoint coordinates and source-colored cell offsets.',
 'step_b':'Consume those records to copy each source by its marker axis or, for half_turn, by the marker midpoint.',
 'why_b_depends_on_a':'The destination of every copied pixel depends on its own marker location and geometry, not on its color or source bounding box.'}


def check_binding(root,binding):
    for row in binding['files']:
        p=(Path(root)/row['path']).resolve()
        if not p.is_relative_to(Path(root).resolve()) or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Source drift: '+row['path'])


def write(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def load_family():
    path=Path(__file__).resolve().with_name('family.py')
    spec=importlib.util.spec_from_file_location('audit_marker_exact',path)
    f=importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
    return f


def run(preflight,out,seeds):
    from arcpuzzles.parametric_worker import _real_evaluator, _grid
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from reviewer_support import public_challenge_bytes
    if type(seeds) is not int or not 1<=seeds<=1024: raise ValueError('seeds must be in 1..1024')
    root=next(p for p in Path(__file__).resolve().parents if (p/'shared/runtime').is_dir())
    receipt=json.loads(preflight.read_text()); binding=receipt['source_binding']
    if receipt['status']!='passed' or receipt['task_id']!='public_eval_7ed72f31': raise ValueError('Wrong or failed preflight')
    check_binding(root,binding)
    for name,digest in receipt['evidence_sha256'].items():
        if hashlib.sha256((preflight.parent/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Preflight evidence drift: '+name)
    out.mkdir(parents=True,exist_ok=False)
    f=load_family(); episodes=0; pair_exposures=0; unique_inputs=set(); survivors=0
    for seed in range(seeds):
        inputs=None
        for mode in f.MODES:
            ep=f.generate(seed,{'line_action':mode},6,4)
            curr=[p['input'] for sp in ('train','test') for p in ep[sp]]
            if inputs is not None and inputs!=curr: raise AssertionError('Input mismatch across settings')
            inputs=curr
            unique_inputs.update(json.dumps(g,separators=(',',':')) for g in curr)
            predictions={rv:[f.rival_solve(g,mode,rv) for g in curr] for rv in f.RIVALS}
            for n in range(2,7):
                episodes+=1; pair_exposures+=n+4
                for rv,labels in predictions.items():
                    fits=all(labels[i]==ep['train'][i]['output'] for i in range(n))
                    changes=any(labels[6+i]!=ep['test'][i]['output'] for i in range(4))
                    if fits and changes:
                        case={'seed':seed,'demos':n,'settings':{'line_action':mode},'rival':rv,
                              'train':ep['train'][:n],'test':ep['test'],'rival_outputs':labels[6:]}
                        write(out/'counterexample.json',case)
                        raise AssertionError(f'Query-changing surviving rival: {seed}/{n}/{mode}/{rv}')
                    survivors+=int(fits and changes)
    write(out/'finite-audit.json',{'status':'passed','source_binding':binding,'seeds':seeds,
          'demo_counts':list(range(2,7)),'settings':list(f.MODES),'rivals':list(f.RIVALS),
          'episodes':episodes,'pair_exposures':pair_exposures,'distinct_input_grids':len(unique_inputs),
          'query_changing_survivors':survivors,
          'limits':'Finite Python rival screen with nested demo prefixes and matched inputs, not universal identifiability or independent pair draws.'})

    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    checks=[]; evals=0
    execution=json.loads((preflight.parent/'execution.json').read_text())
    try:
        # Independent seeds with maximum demo count, including exact 30x30.
        for seed in (11,29):
            for mode in f.MODES:
                ep=f.generate(seed,{'line_action':mode},6,4)
                for sp in ('train','test'):
                    for i,pair in enumerate(ep[sp]):
                        actual=_grid(apply(ep['program_solution'],pair['input'])); evals+=1
                        if actual!=pair['output']: raise AssertionError((seed,mode,sp,i,'Racket mismatch'))
                checks.append({'seed':seed,'line_action':mode,'demos':6,'queries':4,'status':'passed'})
        ep=next(e for e in execution['episodes'] if e['settings']['line_action']=='half_turn')
        pair=ep['test'][3]; program=ep['program_solution']
        counter=program.replace('[center-r (+ r0 r1)] [center-c (+ c0 c1)]', '[center-r (+ (first (bbox-of-cells source)) (third (bbox-of-cells source)))] [center-c (+ (second (bbox-of-cells source)) (fourth (bbox-of-cells source)))]')
        if program==counter: raise ValueError('Counterfactual injection site changed')
        actual=_grid(apply(program,pair['input'])); alternative=_grid(apply(counter,pair['input'])); evals+=2
        if actual!=pair['output'] or actual==alternative: raise AssertionError('Noncausal counterfactual or stale label')
        facts=[{k:x[k] for k in ('kind','marker_bbox','doubled_center','source')} for x in f.analyze(pair['input'])]
        witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':binding,
                 **DEPENDENCY,'racket':{'backend':'racket','protected':True},
                 'cases':[{'input':pair['input'],'settings':ep['settings'],'intermediate_value':facts,
                           'program':program,'output':actual,'counterfactual_program':counter,
                           'counterfactual_output':alternative,'ablation':'wrong_intermediate'}]}
        changed=sum(x!=y for a,b in zip(actual,alternative) for x,y in zip(a,b))
        write(out/'witness.json',witness)
        progress={'sequential_dependency':{**DEPENDENCY,'witness_path':'witness.json'}}
        validate_sequential_witness(progress,receipt,lambda _: (out/'witness.json').read_bytes())
    finally:
        bridge.close()
    replay=replay_witness(root,witness)
    # The shared helper names its result owner_replayed; this invocation is by
    # the reviewer and grants no owner approval or acceptance.
    replay['status']='reviewer_replayed'; replay['owner_accepted']=False
    write(out/'witness-replay.json',replay)
    write(out/'racket-audit.json',{'status':'passed','source_binding':binding,'racket':identity,
          'checks':checks,'evaluations':evals,'separate_replay_evaluations':replay['evaluations'],
          'causal_changed_cells':changed})

    exports={}; mappings=[]; mutations=0
    for ei,ep in enumerate(execution['episodes']):
        presentation_seed=991+ep['seed']
        first=f.public_turn(ep,0,presentation_seed)
        selected=next(i for i,p in enumerate(ep['test']) if p['input']==first['test'][0]['input'])
        mutated=copy.deepcopy(ep); mutated['program_solution']='hidden'; mutated['settings']={'hidden':1}; mutated['seed']=-1
        for i,p in enumerate(mutated['test']):
            p['output']=[[9]]; p['private_note']='hidden'
            if i!=selected: p['input']=[[1]]
        for p in mutated['train']: p['private_note']='hidden'
        if f.public_turn(mutated,0,presentation_seed)!=first: raise AssertionError('Private field leaks into first turn')
        mutations+=1
        visible=copy.deepcopy(ep); visible['test'][selected]['input'][0][0]=(visible['test'][selected]['input'][0][0]+1)%10
        if public_challenge_bytes(f.public_turn(visible,0,presentation_seed))==public_challenge_bytes(first):
            raise AssertionError('Positive control failed')
        for turn in range(4):
            view=f.public_turn(ep,turn,presentation_seed); raw=public_challenge_bytes(view)
            key=hashlib.sha256(raw).hexdigest()
            if key in exports: raise AssertionError('Duplicate visible challenge')
            exports[key]=raw
            src=next(i for i,p in enumerate(ep['test']) if p['input']==view['test'][0]['input'])
            mappings.append({'episode':ei,'turn':turn,'source_index':src,'public_id':key,'presentation_seed':presentation_seed})
    (out/'public').mkdir()
    for key in sorted(exports): (out/'public'/f'{key}.json').write_bytes(exports[key])
    write(out/'public-private-audit.json',{'status':'passed','source_binding':binding,
          'public_files':len(exports),'private_mutation_batches':mutations,'positive_controls':mutations,
          'controller_only_mapping':mappings,'total_count_hint':False,
          'limits':'One view at a time. This report and directory listing are private controller state.'})
    check_binding(root,binding)
    summary={'status':'passed','episodes':episodes,'pair_exposures':pair_exposures,
             'query_changing_survivors':survivors,'racket_evaluations':evals,
             'replay_evaluations':replay['evaluations'],'public_files':len(exports),'causal_changed_cells':changed}
    write(out/'summary.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preflight',required=True,type=Path); p.add_argument('--out',required=True,type=Path)
    p.add_argument('--seeds',type=int,default=64); a=p.parse_args()
    print(json.dumps(run(a.preflight,a.out,a.seeds),sort_keys=True))

if __name__=='__main__': main()
