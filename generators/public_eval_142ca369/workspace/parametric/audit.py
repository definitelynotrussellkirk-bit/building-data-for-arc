"""Task-local executable audit. Run inside this packet's protected runtime.

python review.py run python3 generators/TASK/workspace/parametric/audit.py --out ../checks/TASK/audit --seeds 20
Add --preflight ../checks/TASK/preflight/preflight.json to build/replay only the causal witness.
No source acceptance or training admission is performed.
"""
from pathlib import Path
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
ROOT=next(p for p in BASE.parents if (p/'shared/runtime/arc_repl').is_dir())
TASK=HOME.name

def load_adapter():
    spec=importlib.util.spec_from_file_location('_audit_'+TASK, BASE/'adapter.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    return a

def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def source_files():
    return [{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(HOME.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and (p.suffix in ('.py','.rkt') or p.name=='promotion.json')]

def audit(out,seeds):
    from reviewer_support import public_challenge_bytes
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    if type(seeds) is not int or seeds<1:raise ValueError('seeds must be positive')
    if out.exists():raise FileExistsError(out)
    a=load_adapter();contract=json.loads((BASE/'promotion.json').read_text())
    key,options=next(iter(contract['parameters'].items()))
    count=0;pairs=0;matched=0;turns=0;unique=set();first_queries=set();sources=source_files()
    for seed in range(seeds):
        full={opt:a.generate(seed,{key:opt},6,4) for opt in options}
        first_queries.add(digest(full[options[0]]['test'][0]['input']))
        for opt in options:
            for p in full[opt]['train']+full[opt]['test']:
                _grid(p['input']);_grid(p['output']);unique.add(digest(p['input']))
            assert len({digest(p['input']) for p in full[opt]['train']+full[opt]['test']})==10
        for demos in range(2,7):
            for queries in range(1,5):
                requests=[a.generate(seed,{key:opt},demos,queries) for opt in options]
                seq=lambda e:[p['input'] for split in ('train','test') for p in e[split]]
                assert seq(requests[0])==seq(requests[1]);matched+=1
                for opt,e in zip(options,requests):
                    assert e['train']==full[opt]['train'][:demos]
                    assert e['test']==full[opt]['test'][:queries]
                    for p in e['train']+e['test']:assert p['output']==a.solve(p['input'],opt)
                    for index in range(queries):
                        v=a.public_turn(e,index)
                        assert v=={'train':e['train'],'test':[{'input':e['test'][index]['input']}]}
                        alt=deepcopy(e);alt['settings']={};alt['program_solution']='not public'
                        alt['private']={'forbidden':True};alt['test'][index]['output']=[[9]];alt['test']=alt['test'][:index+1]
                        assert a.public_turn(alt,index)==v
                        public_challenge_bytes(v);turns+=1
                    pairs+=demos+queries;count+=1
    run,identity,bridge=_real_evaluator(ROOT/'shared/runtime');evaluations=0;lessons=[];payloads={}
    try:
        for seed in (0,17,43):
            for opt in options:
                settings={key:opt};e=a.generate(seed,settings,2,4)
                for p in e['train']+e['test']:
                    assert _grid(run(e['program_solution'],p['input']))==p['output'];evaluations+=1
                rejected=[]
                for name,rp in a.rival_programs(settings).items():
                    labels=[]
                    for p in e['train']:
                        y=_grid(run(rp,p['input']));evaluations+=1
                        assert y==a.rival_predict(p['input'],opt,name),name
                        labels.append(y)
                    indices=[i for i,(p,y) in enumerate(zip(e['train'],labels)) if p['output']!=y]
                    assert indices, f'{name} fits all demos at {seed}/{opt}'
                    i=indices[0]
                    rejected.append({'name':name,'program':rp,'demo_index':i,'input':e['train'][i]['input'],'correct':e['train'][i]['output'],'rival':labels[i]})
                lessons.append({'seed':seed,'settings':settings,'rejected':rejected})
                if seed==17:
                    for i in range(4):
                        blob=public_challenge_bytes(a.public_turn(e,i));pid=hashlib.sha256(blob).hexdigest()
                        assert pid not in payloads;payloads[pid]=blob
    finally:bridge.close()
    assert sources==source_files(),'Source changed during audit'
    out.mkdir(parents=True)
    for pid in sorted(payloads):
        (out/'public').mkdir(exist_ok=True);(out/'public'/f'{pid}.json').write_bytes(payloads[pid])
    report={'schema':'public-family-self-audit-v1','task_id':TASK,'status':'passed','sources':sources,
            'sweep':{'seeds':seeds,'requests':count,'pair_instances':pairs,'matched_inputs':matched,'public_turns':turns,
                     'distinct_inputs':len(unique),'distinct_first_queries':len(first_queries)},
            'racket':identity,'racket_evaluations':evaluations,'finite_lessons':lessons,'public_views':len(payloads),
            'limits':'Count sweep uses repeated prefixes; Python labels outside the bounded protected execution are claims. Finite rival bank is not universal uniqueness. No owner acceptance or training admission.'}
    write(out/'audit.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('sources','finite_lessons','racket')},sort_keys=True))
    return report

def witness(out,preflight):
    from arcpuzzles.parametric_worker import _real_evaluator,_grid
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness
    a=load_adapter();q=json.loads(preflight.read_text());execution=json.loads(preflight.with_name('execution.json').read_text())
    assert q['status']=='passed' and q['owner_accepted'] is False
    for row in q['source_binding']['files']:
        assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    episode=next(e for e in execution['episodes'] if e['settings']!=q['contract']['default'])
    case=a.causal_case(episode)
    assert any(p['input']==case['input'] and p['output']==case['output'] for p in episode['test'])
    run,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
    try:
        assert _grid(run(case['program'],case['input']))==case['output']
        case['counterfactual_output']=_grid(run(case['counterfactual_program'],case['input']))
        assert case['output']!=case['counterfactual_output']
    finally:bridge.close()
    w={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':q['source_binding'],
       **a.DEPENDENCY,'racket':{'backend':'racket','protected':True},'cases':[case]}
    if out.exists():raise FileExistsError(out)
    blob=(json.dumps(w,sort_keys=True,indent=2)+'\n').encode()
    validate_sequential_witness({'sequential_dependency':{**a.DEPENDENCY,'witness_path':'witness.json'}},q,lambda _:blob)
    replay=replay_witness(ROOT,w,timeout=60)
    # The replay helper is also used by owners; executing it here is only reviewer evidence.
    replay['status']='reviewer_replayed';replay['owner_accepted']=False
    out.mkdir(parents=True);(out/'witness.json').write_bytes(blob);write(out/'replay.json',replay)
    print(json.dumps({'status':'reviewer_replayed','cases':1,'evaluations':4,'owner_accepted':False}))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--seeds',type=int,default=20);p.add_argument('--preflight',type=Path)
    args=p.parse_args()
    if args.preflight:witness(args.out,args.preflight)
    else:audit(args.out,args.seeds)

if __name__=='__main__':main()
