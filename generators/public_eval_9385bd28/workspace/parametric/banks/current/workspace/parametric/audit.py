"""Bounded protected-Racket audit for this unapproved public family.

This tool verifies exact preflight source binding, generated labels, finite
rivals, count stability, public first-turn privacy, and a source-bound causal
witness. It never grants owner qualification, acceptance, or training admission.
"""
from __future__ import annotations
import argparse,copy,hashlib,importlib.util,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
HOME=HERE.parents[1]
ROOT=next(p for p in HERE.parents if (p/'src/arcpuzzles/parametric_worker.py').is_file())
TASK=HOME.name
sys.path.insert(0,str(ROOT/'src'))


def load_adapter():
    path=HERE/'adapter.py';key='_audit_adapter_'+hashlib.sha256(str(path).encode()).hexdigest()[:16]
    spec=importlib.util.spec_from_file_location(key,path);m=importlib.util.module_from_spec(spec)
    sys.modules[key]=m;spec.loader.exec_module(m);return m


def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def sha_bytes(v):return hashlib.sha256(v).hexdigest()
def save(path,v):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw(v))


def bound(preflight):
    path=Path(preflight);q=json.loads(path.read_bytes())
    if (q.get('schema')!='arcpuzzles-public-eval-authoring-preflight-v1' or q.get('status')!='passed'
        or q.get('task_id')!=TASK or q.get('owner_accepted') is not False):
        raise ValueError('Expected this task\'s passing unapproved authoring preflight')
    for row in q['source_binding']['files']:
        source=ROOT/row['path']
        if not source.is_file() or source.is_symlink() or sha_bytes(source.read_bytes())!=row['sha256']:
            raise ValueError('Preflight source binding drift: '+row['path'])
    for name,digest in q['evidence_sha256'].items():
        if sha_bytes((path.parent/name).read_bytes())!=digest:raise ValueError('Preflight evidence drift: '+name)
    return q


def audit(preflight,out,census_seeds=128):
    from arcpuzzles.parametric_worker import _real_evaluator,_grid,_local_imports
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness
    q=bound(preflight);a=load_adapter();out=Path(out)
    if out.exists():raise FileExistsError('Choose a fresh audit directory')
    out.mkdir(parents=True)
    settings=[{next(iter(q['contract']['parameters'])):v} for v in next(iter(q['contract']['parameters'].values()))]
    jobs=[];cache={};comparisons=0
    with _local_imports(ROOT/'shared/runtime',HERE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            def execute(program,grid):
                key=sha_bytes(program.encode()+raw(grid))
                if key not in cache:cache[key]=_grid(apply(program,grid))
                return cache[key]
            for seed in (0,17,97):
                for demos in (2,3,6):
                    matched=None
                    for setting in settings:
                        ep=a.generate(seed,setting,demos,4)
                        inputs=[p['input'] for split in ('train','test') for p in ep[split]]
                        if matched is not None and matched!=inputs:raise ValueError('Setting-dependent inputs')
                        matched=inputs
                        if len({sha_bytes(raw(g)) for g in inputs})!=len(inputs):raise ValueError('Duplicate input')
                        survivors=[r for r in a.G.RIVALS if all(a.G.solve(p['input'],a.finish(setting),rival=r)==p['output'] for p in ep['train'])]
                        if survivors:raise ValueError(f'Rivals survive {seed}/{demos}/{setting}: {survivors}')
                        for split in ('train','test'):
                            for pair in ep[split]:
                                if execute(ep['program_solution'],pair['input'])!=pair['output']:
                                    raise ValueError('Protected Racket/Python label mismatch')
                                comparisons+=1
                        if not any(len(p['input'])==len(p['input'][0])==30 for p in ep['test']):
                            raise ValueError('Missing 30x30 query')
                        jobs.append({'seed':seed,'demos':demos,'queries':4,'settings':setting,'surviving_rivals':[]})
            alt=settings[1];ep=a.generate(17,alt,2,4);counter=a.counterfactual_program(alt)
            chosen=None
            for split in ('train','test'):
                for pair in ep[split]:
                    good=execute(ep['program_solution'],pair['input']);bad=execute(counter,pair['input'])
                    if good!=bad:chosen=(pair,good,bad);break
                if chosen:break
            if chosen is None:raise ValueError('No protected causal counterexample')
            pair,good,bad=chosen;dep=a.dependency()
            witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':q['source_binding'],
                     'racket':{'backend':'racket','protected':True},**dep,
                     'cases':[{'input':pair['input'],'settings':alt,
                               'intermediate_value':a.intermediate(pair['input'],alt),
                               'program':ep['program_solution'],'output':good,
                               'counterfactual_program':counter,'counterfactual_output':bad,
                               'ablation':'wrong_intermediate'}]}
            save(out/'causal/witness.json',witness)
            progress={'promotion_path':'repo/'+str((HOME/'workspace/parametric/promotion.json').relative_to(ROOT)).replace('\\','/'),
                      'sequential_dependency':{**dep,'witness_path':'checks/'+TASK+'/audit/causal/witness.json'}}
            static=validate_sequential_witness(progress,q,lambda _:raw(witness));save(out/'causal/static.json',static)
            replay=replay_witness(ROOT,witness,timeout=60);replay['status']='reviewer_replayed';replay['owner_accepted']=False
            save(out/'causal/replay.json',replay)
        finally:bridge.close()
    census=[]
    for seed in range(census_seeds):
        matched=None
        for setting in settings:
            small=a.generate(seed,setting,2,4);wide=a.generate(seed,setting,6,4)
            if small['train']!=wide['train'][:2] or small['test']!=wide['test']:raise ValueError('Count-dependent RNG drift')
            inputs=[p['input'] for split in ('train','test') for p in small[split]]
            if matched is not None and matched!=inputs:raise ValueError('Census setting-dependent inputs')
            matched=inputs
            if len({sha_bytes(raw(g)) for g in inputs})!=len(inputs):raise ValueError('Census duplicate input')
            for r in a.G.RIVALS:
                if all(a.G.solve(p['input'],a.finish(setting),rival=r)==p['output'] for p in small['train']):
                    raise ValueError(f'Census rival survives {seed}/{setting}/{r}')
            census.append({'seed':seed,'settings':setting,'status':'passed'})
    save(out/'census.json',{'status':'passed','seeds':census_seeds,'episodes':len(census),'rows':census})
    views=[];privacy=[]
    for seed in (0,17):
        for setting in settings:
            full=a.present(seed,setting,2,4,presentation_seed=41);one=a.present(seed,setting,2,1,presentation_seed=41)
            if full['public'][:1]!=one['public']:raise ValueError('First turn leaks total query count')
            for view in full['public']:
                if set(view)!= {'train','test'} or len(view['test'])!=1 or set(view['test'][0])!={'input'}:
                    raise ValueError('Public view leaks private fields')
                views.append({'sha256':sha_bytes(raw(view)),'train':len(view['train']),'queries':1})
            mutated=copy.deepcopy(full);mutated['private']['settings']={'private':'changed'}
            mutated['private']['source_pairs'][0]['output']=[[9]]
            if mutated['public']!=full['public']:raise ValueError('Private mutation changed visible view')
            privacy.append({'seed':seed,'settings':setting,'status':'passed'})
    save(out/'public-export.json',{'status':'passed','views':views,'privacy_cases':privacy,
                                  'limits':'Sequential one-query views only; settings, programs, answers and future queries remain private.'})
    report={'schema':'arcpuzzles-public-creation-bounded-audit-v1','task_id':TASK,'status':'passed',
            'owner_accepted':False,'training_admitted':False,'jobs':jobs,'label_comparisons':comparisons,
            'protected_evaluations':len(cache),'racket':identity,'census_episodes':len(census),
            'public_views':len(views),'causal_replay_evaluations':replay.get('evaluations'),
            'limits':'Finite declared rivals and bounded seeds; no universal uniqueness, owner acceptance, or training admission.'}
    save(out/'audit.json',report);return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--preflight',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--census-seeds',type=int,default=128)
    args=p.parse_args()
    if not 1<=args.census_seeds<=1024:p.error('census seeds must be 1..1024')
    result=audit(args.preflight,args.out,args.census_seeds)
    print(json.dumps({k:v for k,v in result.items() if k not in ('jobs','racket')},sort_keys=True))
if __name__=='__main__':main()
