"""Portable bounded audits, exact-source authoring witnesses and private exports.

Run with this packet's review.py run. Nothing here approves or admits a family.
Editable local receipts are hash checked, not authenticated as owner evidence.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import sys
import time

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
ROOT=HOME.parents[1]

def load(name):
    path=BASE/(name+'.py')
    spec=importlib.util.spec_from_file_location('_authoring_'+hashlib.sha256(str(path).encode()).hexdigest(),path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as handle:json.dump(value,handle,sort_keys=True,indent=2,allow_nan=False);handle.write('\n')

def check_binding(root,binding):
    root=Path(root).resolve();rows=binding.get('files',[])
    if not rows:raise ValueError('Empty source binding')
    seen=set()
    for row in rows:
        name=row.get('path');p=PurePosixPath(name or '')
        if (not isinstance(name,str) or not name or p.is_absolute() or '..' in p.parts
                or '\\' in name or name in seen):raise ValueError('Unsafe or duplicate source binding path')
        seen.add(name);path=root/name
        if (not path.is_file() or path.is_symlink() or path.resolve()!=path
                or not path.resolve().is_relative_to(root) or sha(path)!=row.get('sha256')):
            raise ValueError('Source drift or missing file: '+name)
    return len(rows)

def current_sources():
    return {'task_id':HOME.name,'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
            for p in sorted(HOME.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json'))]}

def preflight(path):
    path=Path(path);q=json.loads(path.read_text())
    if (q.get('schema')!='arcpuzzles-public-eval-authoring-preflight-v1' or q.get('status')!='passed'
            or q.get('task_id')!=HOME.name or q.get('owner_accepted') is not False):
        raise ValueError('Expected this task\'s unapproved authoring preflight')
    check_binding(ROOT,q['source_binding'])
    by_path={row['path']:row['sha256'] for row in q['source_binding']['files']}
    if any(by_path.get(row['path'])!=row['sha256'] for row in current_sources()['files']):
        raise ValueError('Preflight omits a current task source')
    for name in ('execution.json','original-pairs.json'):
        if sha(path.with_name(name))!=q['evidence_sha256'].get(name):raise ValueError('Preflight evidence drift')
    execution=json.loads(path.with_name('execution.json').read_text())
    a=load('adapter')
    for e in execution['episodes']:
        code=a.program(e['settings']);key=json.dumps(e['settings'],sort_keys=True,separators=(',',':'))
        if e['program_solution']!=code or hashlib.sha256(code.encode()).hexdigest()!=q['programs'].get(key):
            raise ValueError('Program differs from current setting')
    return q,execution

def public_view(episode,index):
    from reviewer_support import public_challenge_bytes
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('Invalid visible query')
    value={'train':[{'input':p['input'],'output':p['output']} for p in episode['train']],
           'test':[{'input':episode['test'][index]['input']}]}
    return json.loads(public_challenge_bytes(value))

def write_exports(episodes,out):
    from reviewer_support import public_challenge_bytes
    out=Path(out)
    if out.exists() or out.is_symlink():raise FileExistsError(out)
    payloads={};mapping=[]
    for e in episodes:
        ids=[]
        for i in range(len(e['test'])):
            raw=public_challenge_bytes(public_view(e,i));key=hashlib.sha256(raw).hexdigest()
            if key in payloads:raise ValueError('Duplicate visible challenge; no output written')
            payloads[key]=raw;ids.append(key)
        mapping.append({'seed':e.get('seed'),'settings':e.get('settings'),'visible_ids_in_private_presentation_order':ids})
    if not payloads:raise ValueError('No public views')
    (out/'public').mkdir(parents=True)
    for key,raw in sorted(payloads.items()):(out/'public'/f'{key}.json').write_bytes(raw)
    write_new(out/'private.json',{'schema':'authoring-private-public-export-v1','episodes':mapping,
        'controller_only':True,'public_write_order':sorted(payloads),'files':len(payloads),
        'owner_accepted':False,'training_admitted':False})
    return {'status':'passed','views':len(payloads),'owner_accepted':False,'training_admitted':False}

def audit(seeds):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    if type(seeds) is not int or not 1<=seeds<=256:raise ValueError('Use 1..256 seeds')
    start=time.monotonic();a=load('adapter');rv=load('rivals')
    contract=json.loads((BASE/'promotion.json').read_text());key=next(iter(contract['parameters']))
    options=contract['parameters'][key]
    report={'schema':'bounded-native-authoring-audit-v1','task_id':HOME.name,'status':'passed',
            'source_binding':current_sources(),'seeds':seeds,'settings':len(options),'episodes':0,
            'prefix_checks':0,'full_prefix_seeds':list(range(min(4,seeds))),'public_views':0,'rivals':list(rv.RIVALS),'racket_evaluations':0,'findings':[],
            'limits':'Finite named rivals and bounded seeds, not universal lesson uniqueness. No acceptance or training admission.'}
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime');report['racket']=identity
        try:
            for seed in range(seeds):
                matched=None
                for setting in options:
                    e=a.generate(seed,{key:setting},6,4);report['episodes']+=1
                    inputs=[p['input'] for sp in ('train','test') for p in e[sp]]
                    if matched is not None and inputs!=matched:raise ValueError('Setting-dependent input stream')
                    matched=inputs
                    if len({json.dumps(g) for g in inputs})!=10:raise ValueError('Duplicate episode input')
                    requests=([(d,q) for d in range(2,7) for q in range(1,5)] if seed<4
                              else [(2,1),(3+seed%4,1+seed%4)])
                    for d,q in requests:
                        small=a.generate(seed,{key:setting},d,q)
                        if small['train']!=e['train'][:d] or small['test']!=e['test'][:q]:raise ValueError('Prefix drift')
                        report['prefix_checks']+=1
                    for i in range(4):
                        view=public_view(e,i);altered=copy.deepcopy(e)
                        altered.update(seed=-999,settings={'private':True},program_solution='not-a-rule')
                        altered['test'][i]['output']=[[9]]
                        for j in range(4):
                            if j!=i:altered['test'][j]={'input':[[9]],'output':[[8]]}
                        if public_view(altered,i)!=view:raise ValueError('Private-field projection leak')
                        report['public_views']+=1
                    for name in rv.RIVALS:
                        demo_match=[rv.rival(p['input'],setting,name)==p['output'] for p in e['train'][:2]]
                        if all(demo_match):
                            report['findings'].append({'seed':seed,'setting':setting,'rival':name,'kind':'minimum_lesson_survivor'})
                    if seed in (0,17):
                        for pair in e['train']+e['test']:
                            actual=apply(e['program_solution'],pair['input']);report['racket_evaluations']+=1
                            if actual!=pair['output']:raise ValueError('Python/Racket label mismatch')
                        for name in rv.RIVALS:
                            # Execute every minimum demonstration and a query for each rival.
                            for pair in e['train'][:2]+e['test'][:1]:
                                actual=apply(rv.program(setting,name),pair['input']);report['racket_evaluations']+=1
                                if actual!=rv.rival(pair['input'],setting,name):raise ValueError('Rival implementation mismatch: '+name)
                if seed%4==3:print(f'audited seeds 0..{seed}',file=sys.stderr,flush=True)
        finally:bridge.close()
    check_binding(ROOT,report['source_binding'])
    report['seconds']=round(time.monotonic()-start,3)
    if report['findings']:report['status']='failed'
    return report

def witness(preflight_path,out):
    from arcpuzzles.review_witness import _execute
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    q,execution=preflight(preflight_path);c=load('causal')
    episode=next(e for e in execution['episodes'] if e['settings']!=q['contract']['default'])
    descriptions=c.descriptions();case=c.make_case(episode)
    evaluated=_execute(ROOT,[case],60)
    w={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':q['source_binding'],
       **descriptions,'racket':{'backend':'racket','protected':True},'cases':evaluated['cases'],
       'verification_status':'authoring_preflight_not_owner_qualification','owner_accepted':False,'training_admitted':False}
    dependency={**descriptions,'witness_path':'witness.json'}
    validate_sequential_witness({'sequential_dependency':dependency},q,lambda _:json.dumps(w).encode())
    replay=replay_witness(ROOT,w,timeout=60)
    replay['status']='reviewer_replayed'
    replay.update(owner_accepted=False,training_admitted=False,verification_status='authoring_replay_only')
    preflight(preflight_path)
    out=Path(out)
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True)
    write_new(out/'witness.json',w);write_new(out/'replay.json',replay)
    return {'status':'reviewer_replayed','evaluations':evaluated['evaluations']+replay['evaluations'],
            'source_files':len(q['source_binding']['files']),'owner_accepted':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['audit','export','witness','verify'])
    p.add_argument('--preflight',type=Path);p.add_argument('--out',type=Path);p.add_argument('--seeds',type=int,default=32)
    args=p.parse_args()
    if args.command=='audit':
        result=audit(args.seeds)
        if args.out is None:p.error('--out required')
        write_new(args.out,result)
    else:
        if args.preflight is None:p.error('--preflight required')
        q,e=preflight(args.preflight)
        if args.command=='verify':result={'status':'passed','source_files':len(q['source_binding']['files'])}
        elif args.out is None:p.error('--out required')
        elif args.command=='export':result=write_exports(e['episodes'],args.out)
        else:result=witness(args.preflight,args.out)
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_binding','racket','files')},sort_keys=True))
    return int(result.get('status')=='failed')

if __name__=='__main__':raise SystemExit(main())
