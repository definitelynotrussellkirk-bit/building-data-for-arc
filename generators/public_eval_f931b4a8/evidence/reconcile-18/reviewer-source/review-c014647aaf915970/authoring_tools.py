"""Reproducible bounded audit and source-bound single-query authoring export.

Run through review.py run. Public files are individual turns; directory listings
and private/ remain controller-only. No command accepts a source or admits data.
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
ROOT=HOME.parents[1]
TASK=HOME.name

def local(name):
    path=BASE/(name+'.py')
    spec=importlib.util.spec_from_file_location('_authoring_'+TASK+'_'+name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

adapter=local('adapter')

def raw(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()

def visible_bytes(episode,index):
    view=adapter.public_view(episode,index)
    for p in view['train']:
        adapter.model.grid_check(p['input']);adapter.model.grid_check(p['output'])
    adapter.model.grid_check(view['test'][0]['input'])
    return raw(view)

def collect_views(episodes):
    views={};mapping=[]
    for i,e in enumerate(episodes):
        ids=[]
        for q in range(len(e['test'])):
            payload=visible_bytes(e,q);identifier=hashlib.sha256(payload).hexdigest()
            if identifier in views:raise ValueError('Duplicate visible query; nothing published')
            views[identifier]=payload;ids.append(identifier)
        mapping.append({'episode_index':i,'view_ids':ids})
    return views,mapping

def _manifest(views,mapping,provenance):
    return {'schema':'task-local-authoring-single-query-v1','task_id':TASK,
              'verification_status':'authoring_projection_not_acceptance','training_admitted':False,
              'public_files':[{'path':f'public/{k}.json','sha256':k} for k in sorted(views)],
              'private_order':mapping,'source':provenance or {},
              'limits':'One selected public file is a model turn. Bundle/listing/private metadata remain hidden. No Racket re-execution or acceptance.'}

def write_views(episodes,destination,provenance=None):
    destination=Path(destination)
    if destination.exists():raise FileExistsError(destination)
    views,mapping=collect_views(episodes)  # Validate the complete write set first.
    destination.mkdir(parents=True,exist_ok=False)
    (destination/'public').mkdir();(destination/'private').mkdir()
    for identifier in sorted(views):
        (destination/'public'/f'{identifier}.json').write_bytes(views[identifier])
    manifest=_manifest(views,mapping,provenance)
    (destination/'private/manifest.json').write_bytes(raw(manifest))
    return manifest

def _imports():
    for p in (ROOT/'src',ROOT/'shared/runtime'):
        if str(p) not in sys.path:sys.path.insert(0,str(p))

def verified(preflight):
    _imports()
    from arcpuzzles.review_witness import _public_preflight
    receipt,execution=_public_preflight(ROOT,Path(preflight).resolve())
    if receipt['task_id']!=TASK:raise ValueError('Receipt belongs to a different task')
    return receipt,execution

def export(preflight,destination):
    receipt,execution=verified(preflight)
    return write_views(execution['episodes'],destination,
                       {'preflight_sha256':hashlib.sha256(Path(preflight).read_bytes()).hexdigest(),
                        'source_binding':receipt['source_binding']})

def verify_export(preflight,bundle):
    receipt,execution=verified(preflight);views,mapping=collect_views(execution['episodes']);bundle=Path(bundle)
    paths=list(bundle.rglob('*'))
    if bundle.is_symlink() or any(p.is_symlink() for p in paths):raise ValueError('Symlink in export')
    expected={f'public/{k}.json' for k in views}|{'private/manifest.json'}
    actual={p.relative_to(bundle).as_posix() for p in paths if p.is_file()}
    if actual!=expected:raise ValueError('Unexpected or missing export files')
    for k,payload in views.items():
        if (bundle/'public'/f'{k}.json').read_bytes()!=payload:raise ValueError('Public bytes changed')
    expected_manifest=_manifest(views,mapping,{'preflight_sha256':hashlib.sha256(Path(preflight).read_bytes()).hexdigest(),
                                             'source_binding':receipt['source_binding']})
    if (bundle/'private/manifest.json').read_bytes()!=raw(expected_manifest):
        raise ValueError('Private manifest changed; expected exact current serialized bytes')
    return {'status':'passed','public_views':len(views),'source_files':len(receipt['source_binding']['files']),
            'owner_accepted':False,'racket_replayed':False}

def source_files():
    return [{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(HOME.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and 'evidence' not in p.relative_to(HOME).parts
            and (p.suffix in {'.py','.rkt'} or p.name in {'promotion.json','public-parent.json'})]

def audit(seeds):
    adapter.model.integer(seeds,1,128,'seeds');rivals=local('rivals');before=source_files()
    findings=[];episodes=0;prefix_checks=0;views=0;rejections={name:0 for name in rivals.NAMES}
    for seed in range(seeds):
        by_setting=[]
        for setting in adapter.SETTINGS:
            full=adapter.generate(seed,setting,6,4);by_setting.append(full);episodes+=1
            inputs=[p['input'] for sp in ('train','test') for p in full[sp]]
            if len({raw(g) for g in inputs})!=10:findings.append([seed,setting,'duplicate_input'])
            for d in range(2,7):
                for q in range(1,5):
                    e=adapter.generate(seed,setting,d,q);prefix_checks+=1
                    if e['train']!=full['train'][:d] or e['test']!=full['test'][:q]:findings.append([seed,setting,'prefix'])
            for name in rivals.NAMES:
                fit=all(rivals.solve(p['input'],setting,name)==p['output'] for p in full['train'][:2])
                if not fit:rejections[name]+=1
                if fit and any(rivals.solve(p['input'],setting,name)!=p['output'] for p in full['test']):
                    findings.append([seed,setting,'dangerous_survivor',name])
            for i in range(4):
                e=copy.deepcopy(full);e['program_solution']='private';e['settings']={'private':True};e['seed']=-1
                for j,p in enumerate(e['test']):
                    p['output']=[[9]]
                    if j!=i:p['input']=[[0]]
                if visible_bytes(e,i)!=visible_bytes(full,i):findings.append([seed,setting,'private_leak'])
                views+=1
        if [p['input'] for sp in ('train','test') for p in by_setting[0][sp]] != [p['input'] for sp in ('train','test') for p in by_setting[1][sp]]:
            findings.append([seed,'unmatched_inputs'])
    _imports()
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_programs import strict_programs
    all_programs=[adapter.program(s) for s in adapter.SETTINGS]+[rivals.program(s,n) for s in adapter.SETTINGS for n in rivals.NAMES]
    strict_programs(ROOT,all_programs)
    apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime');evaluations=0
    try:
        for seed in (0,17):
            for setting in adapter.SETTINGS:
                e=adapter.generate(seed,setting,2,4)
                for p in e['train']+e['test']:
                    actual=apply(e['program_solution'],p['input']);evaluations+=1
                    if actual!=p['output']:findings.append([seed,setting,'racket_label'])
                if seed==0:
                    for name in rivals.NAMES:
                        for p in e['train']+e['test']:
                            actual=apply(rivals.program(setting,name),p['input']);evaluations+=1
                            if actual!=rivals.solve(p['input'],setting,name):findings.append([seed,setting,'rival_implementation',name])
    finally:bridge.close()
    if source_files()!=before:raise ValueError('Source changed during audit')
    return {'task_id':TASK,'status':'passed' if not findings else 'failed','source_files':before,
            'seeds':seeds,'episodes':episodes,'prefix_checks':prefix_checks,'public_invariance_checks':views,
            'rivals':list(rivals.NAMES),'demo_rejections':rejections,'racket':identity,
            'racket_evaluations':evaluations,'findings':findings,'owner_accepted':False,'training_admitted':False,
            'limits':'Finite named rivals and seeds only; Python checks on the full census, protected Racket on seeds 0 and 17 and rivals on seed 0. No universal uniqueness claim.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['audit','export','verify','verify-export'])
    parser.add_argument('--seeds',type=int,default=32)
    parser.add_argument('--preflight',type=Path);parser.add_argument('--bundle',type=Path);parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.command=='audit':result=audit(args.seeds)
    elif args.command=='export':
        if args.preflight is None or args.out is None:parser.error('export needs --preflight and --out')
        result=export(args.preflight,args.out);print(json.dumps({'status':'exported','public_views':len(result['public_files'])}));return
    elif args.command=='verify-export':result=verify_export(args.preflight,args.bundle)
    else:
        receipt,_=verified(args.preflight);result={'status':'passed','source_files':len(receipt['source_binding']['files']),'owner_accepted':False}
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        with args.out.open('xb') as f:f.write(raw(result))
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_files','racket','rivals','demo_rejections')}))
    if result.get('status')=='failed':raise SystemExit(1)
if __name__=='__main__':main()
