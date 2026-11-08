"""Bounded, reusable finite-rival audit and private preflight-to-public writer.

Run through review.py run. All output bundles are controller-private except an
individual selected public/<visible-byte-sha256>.json. A passed audit/preflight
is not owner acceptance, universal identifiability, or training admission.
"""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, itertools, json, sys
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
for path in (ROOT/'src',ROOT/'shared/runtime'):
    if str(path) not in sys.path:sys.path.insert(0,str(path))

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def dump(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def source_files():
    home=BASE.parents[1]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(home.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and (p.suffix in {'.py','.rkt'} or p.name in {'promotion.json','public-parent.json'})}

def materialize_views(episodes,out):
    """Validate a full batch before writing, sort by public bytes, fail on reuse."""
    from reviewer_support import public_challenge_bytes
    a=load('_audit_writer_adapter_'+str(BASE),BASE/'adapter.py')
    out=Path(out)
    if out.exists() or out.is_symlink():raise ValueError('Choose a fresh output directory')
    blobs={};private=[]
    for ei,episode in enumerate(episodes):
        ids=[]
        for qi in range(len(episode['test'])):
            visible=a.public_view(episode,qi);raw=public_challenge_bytes(visible)
            name=hashlib.sha256(raw).hexdigest()
            if name in blobs:raise ValueError('Refusing duplicate public visible payload')
            mutated=copy.deepcopy(episode)
            mutated.update(settings={'hidden':'changed'},seed=-123,program_solution='hidden program')
            for j,pair in enumerate(mutated['test']):
                pair['output']=[[9]]
                if j!=qi:pair['input']=[[9]]
            if public_challenge_bytes(a.public_view(mutated,qi))!=raw:
                raise ValueError('Private metadata/future-query leak')
            blobs[name]=raw;ids.append(name)
        private.append({'episode_index':ei,'view_ids':ids,'settings':episode.get('settings'),
                        'seed':episode.get('seed'),'answers':[p['output'] for p in episode['test']]})
    (out/'public').mkdir(parents=True)
    for name in sorted(blobs):(out/'public'/f'{name}.json').write_bytes(blobs[name])
    result={'schema':'task-private-single-query-export-v1','status':'passed',
            'files_written':len(blobs),'view_ids':sorted(blobs),'private_field_invariance':True,
            'future_query_invariance':True,'public_order':'visible-byte-sha256',
            'owner_accepted':False,'training_admitted':False,
            'warning':'Bundle, manifest and listing are private; expose exactly one public file at a time.'}
    dump(out/'manifest.private.json',{'summary':result,'presentation':private})
    return result

def audit(seeds=32,racket_seeds=(0,17,31)):
    from reviewer_support import public_challenge_bytes
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    before=source_files();a=load('_audit_adapter_'+str(BASE),BASE/'adapter.py')
    contract=json.loads((BASE/'promotion.json').read_text())
    keys=sorted(contract['parameters']);settings=[dict(zip(keys,v)) for v in itertools.product(*(contract['parameters'][k] for k in keys))]
    if type(seeds) is not int or seeds<1:raise ValueError('seeds must be positive')
    report={'schema':'task-native-bounded-audit-v1','task_id':BASE.parents[1].name,'status':'passed',
            'source_files':before,'seed_count':seeds,'settings':settings,'episodes':0,
            'prefix_checks':0,'public_views':0,'rival_checks':0,'racket_evaluations':0,
            'rivals':list(a.model.RIVALS),'racket_seed_values':list(racket_seeds),
            'findings':[],'limits':'Finite named rivals and seeds only; no owner acceptance or universal uniqueness.'}
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime');report['racket']=identity
        def execute(program,grid):
            report['racket_evaluations']+=1;return apply(program,grid)
        try:
            for seed in range(seeds):
                matched=None
                for setting in settings:
                    mode=next(iter(setting.values()))
                    full=a.generate(seed,setting,6,4)
                    inputs=[p['input'] for p in full['train']+full['test']]
                    assert len({json.dumps(g) for g in inputs})==10, ('duplicate input',seed,setting)
                    assert matched is None or inputs==matched, ('setting-dependent inputs',seed)
                    matched=inputs
                    for demos in range(2,7):
                        for queries in range(1,5):
                            part=a.generate(seed,setting,demos,queries)
                            assert part['train']==full['train'][:demos] and part['test']==full['test'][:queries],('prefix instability',seed,setting,demos,queries)
                            report['prefix_checks']+=1
                    for qi in range(4):
                        view=a.public_view(full,qi);raw=public_challenge_bytes(view)
                        changed=copy.deepcopy(full)
                        changed.update(settings={},seed=-5,program_solution='private')
                        for j,p in enumerate(changed['test']):
                            p['output']=[[0]]
                            if j!=qi:p['input']=[[0]]
                        assert public_challenge_bytes(a.public_view(changed,qi))==raw
                        assert len(view['test'])==1 and set(view['test'][0])=={'input'}
                        report['public_views']+=1
                    for rival in a.model.RIVALS:
                        fits=all(a.model.solve(p['input'],mode,rival)==p['output'] for p in full['train'][:2])
                        if fits and any(a.model.solve(p['input'],mode,rival)!=p['output'] for p in full['test']):
                            report['findings'].append({'seed':seed,'settings':setting,'rival':rival})
                        report['rival_checks']+=1
                        if seed==17:
                            rp=a.rival_program(setting,rival)
                            for p in full['train'][:2]:
                                assert execute(rp,p['input'])==a.model.solve(p['input'],mode,rival),('rival Racket mismatch',rival,setting)
                    if seed in racket_seeds:
                        for p in full['train'][:2]+full['test']:
                            assert execute(full['program_solution'],p['input'])==p['output'],('Racket label mismatch',seed,setting)
                    report['episodes']+=1
        finally:bridge.close()
    assert source_files()==before,'Sources changed during audit'
    report['status']='failed' if report['findings'] else 'passed'
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('audit');p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('export');p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='audit':
        if args.out.exists():raise ValueError('Choose a fresh output file')
        result=audit(args.seeds);args.out.parent.mkdir(parents=True,exist_ok=True);dump(args.out,result)
        print(json.dumps({k:result[k] for k in ('status','episodes','prefix_checks','public_views','rival_checks','racket_evaluations','findings')}))
        if result['status']!='passed':raise SystemExit(1)
    else:
        helper=load('_checked_authoring_'+str(BASE),BASE/'authoring_witness.py')
        q,execution=helper.checked_preflight(ROOT,args.preflight)
        result=materialize_views(execution['episodes'],args.out)
        result['preflight_sha256']=hashlib.sha256(args.preflight.read_bytes()).hexdigest()
        result['source_binding']=q['source_binding'];dump(args.out/'verification.private.json',result)
        print(json.dumps({k:result[k] for k in ('status','files_written','private_field_invariance','future_query_invariance')}))

if __name__=='__main__':main()
