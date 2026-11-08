"""Reusable bounded adversarial audit and private single-query exporter."""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[3]
for path in (ROOT/'src',ROOT/'shared/runtime'):
    if str(path) not in sys.path: sys.path.insert(0,str(path))
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
adapter=load('_audit_adapter_e87109e9',BASE/'adapter.py')
def dump(path,value): Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def sha(data): return hashlib.sha256(data).hexdigest()
def source_files():
    home=BASE.parents[1]
    return {p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in sorted(home.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.rkt','.json')}

def run_audit(seeds):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    from reviewer_support import public_challenge_bytes
    before=source_files();findings=[];racket_evaluations=0;rival_checks=0;public_checks=0;episodes=0;chain_cases=0
    settings=[{'turn_policy':'legend'},{'turn_policy':'opposite'}]
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for seed in range(seeds):
                matched=None
                for setting in settings:
                    mode=setting['turn_policy'];full=adapter.generate(seed,setting,6,4)
                    inputs=[p['input'] for p in full['train']+full['test']]
                    if matched is not None and inputs!=matched: findings.append({'seed':seed,'setting':setting,'issue':'setting-dependent inputs'})
                    matched=inputs
                    if len({json.dumps(x) for x in inputs})!=10: findings.append({'seed':seed,'setting':setting,'issue':'duplicate input'})
                    if any(len(adapter.model.trace(p['input'],mode)[2])>=2 for p in full['train'][:2]+full['test']): chain_cases+=1
                    for rival in adapter.model.RIVALS:
                        fits=all(adapter.model.solve(p['input'],mode,rival)==p['output'] for p in full['train'][:2])
                        fails=any(adapter.model.solve(p['input'],mode,rival)!=p['output'] for p in full['test'])
                        if fits and fails: findings.append({'seed':seed,'setting':setting,'issue':'harmful rival survivor','rival':rival})
                        rival_checks+=1
                    for qi in range(4):
                        view=adapter.public_view(full,qi);raw=public_challenge_bytes(view)
                        changed=copy.deepcopy(full);changed['settings']={'hidden':'changed'};changed['seed']=-1;changed['program_solution']='secret'
                        for j,p in enumerate(changed['test']):
                            p['output']=[[9]]
                            if j!=qi:p['input']=[[9]]
                        if public_challenge_bytes(adapter.public_view(changed,qi))!=raw:
                            findings.append({'seed':seed,'setting':setting,'query':qi,'issue':'private data affects public bytes'})
                        public_checks+=1
                    if seed in (0,17,43):
                        for p in full['train'][:2]+full['test']:
                            racket_evaluations+=1
                            if apply(full['program_solution'],p['input'])!=p['output']:
                                findings.append({'seed':seed,'setting':setting,'issue':'Racket/Python mismatch'})
                    episodes+=1
        finally: bridge.close()
    if source_files()!=before: findings.append({'issue':'source drift during audit'})
    if chain_cases<episodes: findings.append({'issue':'not every audited episode exposed a multi-collision case','chain_cases':chain_cases,'episodes':episodes})
    return {'schema':'public-e87109e9-bounded-audit-v1','task_id':'public_eval_e87109e9',
            'status':'failed' if findings else 'passed','seed_count':seeds,'episodes':episodes,
            'rivals':list(adapter.model.RIVALS),'rival_checks':rival_checks,'multi_collision_episodes':chain_cases,
            'public_projection_checks':public_checks,'racket_evaluations':racket_evaluations,
            'racket':identity,'source_files':before,'findings':findings,
            'limits':'Finite named rivals and seeds only; no owner acceptance or universal uniqueness.'}

def export_views(out):
    from reviewer_support import public_challenge_bytes,public_challenge_id
    if out.exists(): raise ValueError('Choose a fresh export directory')
    public=out/'public';private=out/'private';public.mkdir(parents=True);private.mkdir()
    rows=[];seen=set();episodes=[adapter.generate(seed,{'turn_policy':mode},2,4) for seed in (0,17) for mode in ('legend','opposite')]
    for episode_index,ep in enumerate(episodes):
        for query_index in range(4):
            view=adapter.public_view(ep,query_index);raw=public_challenge_bytes(view);vid=public_challenge_id(view)
            if vid in seen: raise ValueError('duplicate visible public challenge')
            seen.add(vid);(public/f'{vid}.json').write_bytes(raw)
            rows.append({'view_id':vid,'episode_index':episode_index,'query_index':query_index,
                         'visible_sha256':sha(raw),'settings':ep['settings'],'seed':ep['seed'],
                         'answer':ep['test'][query_index]['output']})
    rows.sort(key=lambda x:x['view_id'])
    manifest={'schema':'public-e87109e9-single-query-export-v1','status':'passed','files_written':len(rows),
              'view_ids':[x['view_id'] for x in rows],'source_files':source_files(),'private_rows':rows,
              'limits':'Directory and private manifest are controller-only; each public file is one model turn.'}
    dump(private/'manifest.json',manifest);return manifest

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('audit');p.add_argument('--seeds',type=int,default=32);p.add_argument('--out',type=Path,required=True)
    p=sub.add_parser('export');p.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.cmd=='audit':
        if args.out.exists(): raise ValueError('Choose a fresh output file')
        args.out.parent.mkdir(parents=True,exist_ok=True);result=run_audit(args.seeds);dump(args.out,result)
        print(json.dumps({k:result[k] for k in ('status','episodes','multi_collision_episodes','rival_checks','public_projection_checks','racket_evaluations','findings')}))
        if result['status']!='passed': raise SystemExit(1)
    else:
        result=export_views(args.out);print(json.dumps({k:result[k] for k in ('status','files_written')}))
if __name__=='__main__':main()
