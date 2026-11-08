"""Rerunnable protected-label, rival, public-export and causal audit."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json
from pathlib import Path
import sys
import os
REPO_ROOT=Path(__file__).resolve().parents[4]
RUNTIME_ROOT=REPO_ROOT/'shared/runtime'
SOURCE_ROOT=REPO_ROOT/'src'
for bootstrap_path in (RUNTIME_ROOT,SOURCE_ROOT):
    if str(bootstrap_path) not in sys.path:
        sys.path.insert(0,str(bootstrap_path))
PACKET_RACKET=REPO_ROOT.parent/'.review/racket-runtime/racket/bin/racket'
if 'RACKET_PATH' not in os.environ and PACKET_RACKET.is_file():
    os.environ['RACKET_PATH']=str(PACKET_RACKET)

from reviewer_support import find_root, public_challenge_bytes

HOME=Path(__file__).resolve().parents[2];BASE=Path(__file__).resolve().parent;ROOT=find_root(__file__);TASK=HOME.name
SETTINGS=({'docking':'matching'},{'docking':'opposite'})

def load_adapter():
    p=BASE/'adapter.py';n='_audit_2c_'+hashlib.sha256(str(p).encode()).hexdigest();s=importlib.util.spec_from_file_location(n,p)
    m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m

def write(p,v):Path(p).write_text(json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n')

def exports(adapter,records,dest):
    dest=Path(dest)
    if dest.exists():raise FileExistsError(dest)
    payloads={};private=[]
    for seed,setting,episode in records:
        projected=adapter.present(seed,setting,2,4,presentation_seed=11);ids=[]
        for view in projected['public']:
            raw=public_challenge_bytes(view);key=hashlib.sha256(raw).hexdigest()
            if key in payloads:raise ValueError('Duplicate public view')
            payloads[key]=raw;ids.append(key)
        private.append({'seed':seed,'settings':setting,'program':episode['program_solution'],'view_ids':ids,
                        'source_indices':projected['private']['source_indices'],
                        'answers':[p['output'] for p in projected['private']['source_pairs']]})
    (dest/'public').mkdir(parents=True);(dest/'private').mkdir()
    for key in sorted(payloads):(dest/'public'/f'{key}.json').write_bytes(payloads[key])
    raw=(json.dumps(private,sort_keys=True,indent=2)+'\n').encode();(dest/'private/episodes.json').write_bytes(raw)
    m={'schema':'public-eval-authoring-sequential-export-v1','task_id':TASK,'public_ids':sorted(payloads),
       'private_sha256':hashlib.sha256(raw).hexdigest(),'owner_accepted':False,'training_admitted':False,'controller_only':True}
    write(dest/'manifest.json',m);return m

def audit(dest,stress_seeds=64):
    from arcpuzzles.parametric_worker import _grid,_local_imports,_real_evaluator
    dest=Path(dest)
    if dest.exists():raise FileExistsError(dest)
    a=load_adapter();g=a.G;first=set();stress=prefixes=0;large=[]
    for seed in list(range(stress_seeds))+[2**63-1]:
        baseline=None
        for setting in SETTINGS:
            ep=a.generate(seed,setting,6,4);small=a.generate(seed,setting,2,1)
            assert small['train']==ep['train'][:2] and small['test']==ep['test'][:1]
            inputs=[p['input'] for split in ('train','test') for p in ep[split]]
            assert baseline is None or inputs==baseline;baseline=inputs
            assert len({json.dumps(x,separators=(',',':')) for x in inputs})==10
            for rival in g.RIVALS:assert any(g.solve(p['input'],setting['docking'],rival)!=p['output'] for p in ep['train'][:2])
            one=a.present(seed,setting,2,1,19);full=a.present(seed,setting,2,4,19)
            assert one['public']==full['public'][:1];first.add(full['private']['source_indices'][0]);stress+=1;prefixes+=1
            q=ep['test'][-1];bg=g.parse(q['input'])['background']
            large.append({'seed':seed,'settings':setting,'foreground':sum(v!=bg for row in q['input'] for v in row),
                          'changed_cells':sum(x!=y for ra,rb in zip(q['input'],q['output']) for x,y in zip(ra,rb))})
    assert len(first)>1
    jobs=[];evaluations=0;records=[]
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for setting in SETTINGS:
                for seed in (17,43):
                    for demos in (2,6):
                        ep=a.generate(seed,setting,demos,4)
                        for split in ('train','test'):
                            for pair in ep[split]:assert _grid(apply(ep['program_solution'],pair['input']))==pair['output'];evaluations+=1
                        jobs.append({'settings':setting,'seed':seed,'demos':demos,'queries':4})
                        if demos==2:records.append((seed,setting,ep))
        finally:bridge.close()
    dest.mkdir(parents=True);manifest=exports(a,records,dest/'preview')
    sources=[p for p in HOME.rglob('*') if p.is_file() and p.suffix in ('.py','.rkt') and '__pycache__' not in p.parts]
    report={'schema':'public-eval-family-self-audit-v1','status':'passed','task_id':TASK,'racket':identity,
            'protected_racket_evaluations':evaluations,'jobs':jobs,'stress_episodes':stress,'count_prefix_checks':prefixes,
            'public_views':len(manifest['public_ids']),'presentation_first_indices':sorted(first),'large_queries':large,
            'finite_rivals':list(g.RIVALS),'rival_evaluation':'Python executable predictions against protected-Racket-verified labels; finite only.',
            'sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(sources)],
            'owner_accepted':False,'training_admitted':False}
    write(dest/'audit.json',report);print(json.dumps({k:report[k] for k in ('status','protected_racket_evaluations','stress_episodes','public_views')}));return report

def witness(preflight,dest):
    from arcpuzzles.parametric_worker import _grid,_local_imports,_real_evaluator
    dest=Path(dest)
    if dest.exists():raise FileExistsError(dest)
    receipt=json.loads(Path(preflight).read_text())
    if receipt.get('task_id')!=TASK or receipt.get('status')!='passed':raise ValueError('Wrong preflight')
    for row in receipt['source_binding']['files']:
        if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Source changed after preflight: '+row['path'])
    a=load_adapter();settings={'docking':'opposite'};pair=a.generate(17,settings,2,4)['test'][0]
    program=a.program(settings);counter=a.counterfactual_program(settings);inter=a.intermediate(pair['input'],settings)
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:out=_grid(apply(program,pair['input']));wrong=_grid(apply(counter,pair['input']))
        finally:bridge.close()
    assert out==pair['output'] and out!=wrong
    report={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':TASK,'source_binding':receipt['source_binding'],
            **a.dependency(),'racket':{'backend':'racket','protected':True},'racket_identity':identity,
            'cases':[{'settings':settings,'input':pair['input'],'intermediate_value':inter,'program':program,'output':out,
                      'counterfactual_program':counter,'counterfactual_output':wrong,'ablation':'wrong_intermediate'}]}
    dest.mkdir(parents=True);write(dest/'witness.json',report)
    changed=sum(x!=y for ra,rb in zip(out,wrong) for x,y in zip(ra,rb));replay={'status':'author_protected_replayed',
            'protected_racket_evaluations':2,'changed_cells':changed,'witness_sha256':hashlib.sha256((dest/'witness.json').read_bytes()).hexdigest(),
            'owner_accepted':False,'training_admitted':False}
    write(dest/'replay.json',replay);print(json.dumps(replay))

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--preflight',type=Path);p.add_argument('--stress-seeds',type=int,default=64);a=p.parse_args()
    witness(a.preflight,a.out) if a.preflight else audit(a.out,a.stress_seeds)
if __name__=='__main__':main()
