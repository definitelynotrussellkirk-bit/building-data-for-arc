"""Reusable source-bound audit/preflight-witness driver for an assigned home.

Run from the library root through review.py run. No training or acceptance side
 effects. Labels and controller manifests are private; public/ contains one
current query per content-addressed file, never the bank or query answers.
"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,sys

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
ROOT=HOME.parents[1]
TASK=HOME.name


def load(name):
    spec=importlib.util.spec_from_file_location('_audit_'+TASK+'_'+name,BASE/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def audit(out,seeds):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    from reviewer_support import public_challenge_bytes
    adapter=load('adapter'); rivals=load('rivals');counts={'episodes':0,'label_checks':0,'rival_checks':0,'racket_evaluations':0,'public_views':0}
    outcomes=[]; harmful=[];errors=[];cache={};public_manifest=[]
    out.mkdir(parents=True,exist_ok=False)
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        def execute(program,grid):
            key=(program,json.dumps(grid,separators=(',',':')))
            if key not in cache:
                cache[key]=_grid(apply(program,grid));counts['racket_evaluations']+=1
            return cache[key]
        try:
            for setting in adapter.SETTINGS:
                for seed in seeds:
                    episode=adapter.generate(seed,setting,2,4);program=adapter.program(setting);counts['episodes']+=1
                    for split in ('train','test'):
                        for p in episode[split]:
                            if execute(program,p['input'])!=p['output']:raise ValueError('false Python label')
                            counts['label_checks']+=1
                    for name,rival in rivals.programs(adapter,setting).items():
                        counts['rival_checks']+=1
                        try:
                            demo=[execute(rival,p['input'])==p['output'] for p in episode['train']]
                            if not all(demo): status='refuted_by_demonstrations'
                            else:
                                query=[execute(rival,p['input'])==p['output'] for p in episode['test']]
                                status='bounded_equivalent' if all(query) else 'harmful_survivor'
                                if not all(query):
                                    k=query.index(False)
                                    harmful.append({'settings':setting,'seed':seed,'rival':name,'rival_program':rival,
                                                    'train':episode['train'],'query':episode['test'][k],
                                                    'counterfactual_output':execute(rival,episode['test'][k]['input'])})
                            outcomes.append({'settings':setting,'seed':seed,'rival':name,'status':status})
                        except Exception as exc:
                            errors.append({'settings':setting,'seed':seed,'rival':name,'error':repr(exc)})
                    views=adapter.public_views(episode,seed+113,4)
                    if adapter.public_views(episode,seed+113,1)!=views[:1]:raise ValueError('first-turn count leak')
                    altered=copy.deepcopy(episode);altered['program_solution']='PRIVATE';altered['settings']={'PRIVATE':True}
                    for p in altered['test']:p['output']=[[9]]
                    if adapter.public_views(altered,seed+113,4)!=views:raise ValueError('private-field leak')
                    for turn,view in enumerate(views):
                        if set(view)!={'train','test'} or len(view['test'])!=1 or set(view['test'][0])!={'input'}:raise ValueError('public field leak')
                        raw=public_challenge_bytes(view);name=hashlib.sha256(raw).hexdigest()+'.json'
                        (out/'public').mkdir(exist_ok=True);(out/'public'/name).write_bytes(raw)
                        public_manifest.append({'setting':setting,'seed':seed,'turn':turn,'path':'public/'+name})
                        counts['public_views']+=1
        finally:bridge.close()
    report={'status':'passed' if not harmful and not errors else 'failed','task_id':TASK,'racket':identity,
            'sources_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HOME/'generator.py',HOME/'reference.rkt',BASE/'adapter.py',BASE/'prototype.py',BASE/'rivals.py',Path(__file__).resolve()]},
            'counts':counts,'outcomes':outcomes,'harmful_survivors':harmful,'errors':errors,
            'limits':'Finite declared competitors and seeds only; bounded equivalence is not universal uniqueness. No owner qualification or acceptance.'}
    write(out/'audit.json',report);write(out/'presentation.private.json',public_manifest)
    print(json.dumps({'status':report['status'],**counts,'harmful_survivors':len(harmful),'errors':errors},indent=2))
    return not harmful and not errors


def witness(preflight,out):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness
    receipt=json.loads(preflight.read_text());execution=json.loads(preflight.with_name('execution.json').read_text())
    for row in receipt['source_binding']['files']:
        if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('preflight source drift: '+row['path'])
    adapter=load('adapter');rivals=load('rivals')
    episode=next(ep for ep in execution['episodes'] if ep['settings']==rivals.WITNESS_SETTING)
    pair=episode['test'][3];program=adapter.program(episode['settings']);cf=rivals.counterfactual(program)
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try: output=_grid(apply(program,pair['input']));alternative=_grid(apply(cf,pair['input']))
        finally:bridge.close()
    if output!=pair['output'] or output==alternative:raise ValueError('causal intervention did not change the validated output')
    value={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':receipt['source_binding'],
           'racket':{'backend':'racket','protected':True},**rivals.DEPENDENCY,
           'cases':[{'input':pair['input'],'settings':episode['settings'],'program':program,'output':output,
                     'counterfactual_program':cf,'counterfactual_output':alternative,'ablation':'wrong_intermediate',
                     'intermediate_value':rivals.intermediate(adapter,pair)}]}
    payload=json.dumps(value).encode();progress={'sequential_dependency':{**rivals.DEPENDENCY,'witness_path':'witness.json'}}
    validate_sequential_witness(progress,receipt,lambda p:payload)
    negatives=[]
    for field in ('source_binding','program','output'):
        bad=copy.deepcopy(value)
        if field=='source_binding':bad[field]={}
        elif field=='program':bad['cases'][0][field]='(rule! g)'
        else:bad['cases'][0]['counterfactual_output']=bad['cases'][0]['output']
        try:validate_sequential_witness(progress,receipt,lambda p:json.dumps(bad).encode())
        except ValueError:negatives.append(field)
        else:raise ValueError('negative witness unexpectedly admitted: '+field)
    replay=replay_witness(ROOT,value,timeout=60)
    replay['status']='reviewer_replayed';replay['owner_accepted']=False;replay['training_admitted']=False
    replay['negative_static_checks_rejected']=negatives
    out.mkdir(parents=True,exist_ok=False);write(out/'witness.json',value);write(out/'replay.json',replay)
    changed=sum(a!=b for x,y in zip(output,alternative) for a,b in zip(x,y)) if (len(output),len(output[0]))==(len(alternative),len(alternative[0])) else None
    print(json.dumps({'status':'reviewer_replayed','changed_cells':changed,'evaluations':replay['evaluations'],'negative_static_checks_rejected':negatives,'owner_accepted':False}))
    return True


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=['audit','witness'])
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--seed',type=int,action='append')
    parser.add_argument('--preflight',type=Path)
    args=parser.parse_args()
    if args.mode=='witness':
        if args.preflight is None:parser.error('--preflight required')
        ok=witness(args.preflight,args.out)
    else:ok=audit(args.out,args.seed or [0,17,43,101])
    return 0 if ok else 1

if __name__=='__main__':raise SystemExit(main())
