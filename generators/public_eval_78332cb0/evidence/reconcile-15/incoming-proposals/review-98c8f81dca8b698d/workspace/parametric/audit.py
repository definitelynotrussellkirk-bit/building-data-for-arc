"""Source-bound finite-rival, protected-Racket and public-view audit.

Run from the packet with::
  python3 run_with_racket.py python3 generators/public_eval_78332cb0/workspace/parametric/audit.py --preflight ../checks/public_eval_78332cb0/preflight/preflight.json --out ../checks/public_eval_78332cb0/audit --seeds 64

The output is private controller evidence.  It grants neither owner acceptance
nor training admission.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json
from pathlib import Path

TASK_ID='public_eval_78332cb0'
PARAMETER='traversal'
VALUES=('forward', 'reverse')


def write(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def root_dir():
    return next(p for p in Path(__file__).resolve().parents if (p/'shared/runtime').is_dir())


def load_adapter():
    path=Path(__file__).resolve().with_name('adapter.py')
    spec=importlib.util.spec_from_file_location('_audit_adapter_'+TASK_ID,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def check_binding(root,binding):
    root=root.resolve()
    for row in binding['files']:
        path=(root/row['path']).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('source drift: '+row['path'])


def run(preflight,out,seeds):
    from arcpuzzles.parametric_worker import _real_evaluator,_grid,_local_imports
    from reviewer_support import public_challenge_bytes
    if type(seeds) is not int or not 1<=seeds<=512:raise ValueError('seeds must be 1..512')
    root=root_dir();receipt=json.loads(preflight.read_text());binding=receipt['source_binding']
    if receipt.get('status')!='passed' or receipt.get('task_id')!=TASK_ID:raise ValueError('wrong/failed preflight')
    check_binding(root,binding)
    for name,digest in receipt['evidence_sha256'].items():
        if hashlib.sha256((preflight.parent/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('preflight evidence drift: '+name)
    out.mkdir(parents=True,exist_ok=False);adapter=load_adapter();engine=adapter.engine
    episodes=0;pair_exposures=0;distinct=set();stress=[]
    for seed in range(seeds):
        matched=None
        for mode in VALUES:
            setting={PARAMETER:mode};episode=adapter.generate(seed,setting,6,4)
            grids=[p['input'] for split in ('train','test') for p in episode[split]]
            if matched is not None and grids!=matched:raise AssertionError('settings changed input stream')
            matched=grids
            if len({json.dumps(g,separators=(',',':')) for g in grids})!=len(grids):raise AssertionError('duplicate episode input')
            distinct.update(json.dumps(g,separators=(',',':')) for g in grids)
            for demos in range(2,7):
                episodes+=1;pair_exposures+=demos+4
                survivors=engine.surviving_rivals(episode['train'][:demos],episode['test'],mode)
                if survivors:
                    write(out/'finite-counterexample.json',{'seed':seed,'settings':setting,'demos':demos,'survivors':survivors,
                          'train':episode['train'][:demos],'test':episode['test']})
                    raise AssertionError('query-changing finite rival survived: '+str(survivors))
            g=episode['test'][3]['input']
            stress.append({'seed':seed,'settings':setting,'shape':[len(g),len(g[0])],
                           'nonbackground':engine.stress_content(g)})
    write(out/'finite-audit.json',{'status':'passed','source_binding':binding,'seeds':seeds,
          'settings':list(VALUES),'demo_counts':list(range(2,7)),'rivals':list(engine.RIVALS),
          'episodes':episodes,'pair_exposures':pair_exposures,'distinct_input_grids':len(distinct),
          'query_changing_survivors':0,'stress':stress,
          'limits':'Finite executable Python rival screen; not universal rule uniqueness or owner qualification.'})

    checks=[];evaluations=0
    with _local_imports(root/'shared/runtime',Path(__file__).resolve().parent):
        apply,identity,bridge=_real_evaluator(root/'shared/runtime')
        try:
            for seed in (11,29):
                for mode in VALUES:
                    setting={PARAMETER:mode};episode=adapter.generate(seed,setting,6,4)
                    for split in ('train','test'):
                        for index,pair in enumerate(episode[split]):
                            actual=_grid(apply(episode['program_solution'],pair['input']));evaluations+=1
                            if actual!=pair['output']:raise AssertionError((seed,mode,split,index,'Racket mismatch'))
                    checks.append({'seed':seed,'settings':setting,'demos':6,'queries':4,'status':'passed'})
        finally:bridge.close()
    write(out/'racket-audit.json',{'status':'passed','source_binding':binding,'racket':identity,
          'checks':checks,'evaluations':evaluations})

    execution=json.loads((preflight.parent/'execution.json').read_text());public_dir=out/'public';public_dir.mkdir()
    ids={};mappings=[];mutation_batches=0
    for episode_index,episode in enumerate(execution['episodes']):
        presentation_seed=991+episode['seed']
        order=adapter.presentation_order(presentation_seed)
        for turn in range(4):
            view=adapter.public_turn(episode,turn,presentation_seed);raw=public_challenge_bytes(view)
            ident=hashlib.sha256(raw).hexdigest()
            if ident in ids:raise AssertionError('duplicate public payload')
            ids[ident]=raw;mappings.append({'episode':episode_index,'turn':turn,'source_index':order[turn],'public_id':ident})
        first=adapter.public_turn(episode,0,presentation_seed);selected=order[0]
        hidden=copy.deepcopy(episode);hidden['program_solution']='hidden';hidden['settings']={'hidden':True};hidden['private']={'hidden':True}
        for i,pair in enumerate(hidden['test']):
            pair['output']=[[9]]
            if i!=selected:pair['input']=[[1]]
        for pair in hidden['train']:pair['private_note']='hidden'
        if adapter.public_turn(hidden,0,presentation_seed)!=first:raise AssertionError('private/future data leaked')
        if adapter.public_turns(episode['seed'],episode['settings'],len(episode['train']),presentation_seed,1)[0] != adapter.public_turns(episode['seed'],episode['settings'],len(episode['train']),presentation_seed,4)[0]:
            raise AssertionError('first-turn bytes depend on requested turn count')
        changed=copy.deepcopy(episode);changed['test'][selected]['input'][0][0]=(changed['test'][selected]['input'][0][0]+1)%10
        if public_challenge_bytes(adapter.public_turn(changed,0,presentation_seed))==public_challenge_bytes(first):raise AssertionError('visible positive control failed')
        mutation_batches+=1
    for ident in sorted(ids):(public_dir/(ident+'.json')).write_bytes(ids[ident])
    write(out/'public-private-audit.json',{'status':'passed','source_binding':binding,'public_files':len(ids),
          'private_mutation_batches':mutation_batches,'positive_controls':mutation_batches,
          'total_count_hint':False,'controller_only_mapping':mappings,
          'limits':'Each saved file contains one query only; directory and mapping remain private controller state.'})
    check_binding(root,binding)
    summary={'status':'passed','episodes':episodes,'pair_exposures':pair_exposures,'distinct_input_grids':len(distinct),
             'racket_evaluations':evaluations,'public_files':len(ids),'finite_rivals':len(engine.RIVALS)}
    write(out/'summary.json',summary);return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--preflight',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--seeds',type=int,default=64)
    args=parser.parse_args();print(json.dumps(run(args.preflight,args.out,args.seeds),sort_keys=True))

if __name__=='__main__':main()
