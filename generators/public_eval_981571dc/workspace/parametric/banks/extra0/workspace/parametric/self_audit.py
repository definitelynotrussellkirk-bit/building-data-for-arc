"""Rerunnable stress, protected-Racket, public-export and causal audit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

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

HOME=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
ROOT=find_root(__file__)
TASK=HOME.name
SETTINGS=({'completion_depth':'closure'},{'completion_depth':'transpose_only'})


def load_adapter():
    path=BASE/'adapter.py';name='_audit_981_'+hashlib.sha256(str(path).encode()).hexdigest()
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod;spec.loader.exec_module(mod);return mod


def write(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def write_exports(adapter, records, destination):
    destination=Path(destination)
    if destination.exists(): raise FileExistsError(destination)
    payloads={};private=[]
    for seed,setting,episode in records:
        projected=adapter.present(seed,setting,2,4,presentation_seed=11)
        ids=[]
        for view in projected['public']:
            raw=public_challenge_bytes(view);key=hashlib.sha256(raw).hexdigest()
            if key in payloads: raise ValueError('Duplicate public view')
            payloads[key]=raw;ids.append(key)
        private.append({'seed':seed,'settings':setting,'program':episode['program_solution'],
                        'source_indices':projected['private']['source_indices'],'view_ids':ids,
                        'answers':[p['output'] for p in projected['private']['source_pairs']]})
    (destination/'public').mkdir(parents=True);(destination/'private').mkdir()
    for key in sorted(payloads):(destination/'public'/f'{key}.json').write_bytes(payloads[key])
    private_raw=(json.dumps(private,sort_keys=True,indent=2)+'\n').encode()
    (destination/'private/episodes.json').write_bytes(private_raw)
    manifest={'schema':'public-eval-authoring-sequential-export-v1','task_id':TASK,
              'public_ids':sorted(payloads),'private_sha256':hashlib.sha256(private_raw).hexdigest(),
              'owner_accepted':False,'training_admitted':False,'controller_only':True}
    write(destination/'manifest.json',manifest);return manifest


def audit(destination, stress_seeds=64):
    from arcpuzzles.parametric_worker import _grid,_local_imports,_real_evaluator
    destination=Path(destination)
    if destination.exists(): raise FileExistsError(destination)
    adapter=load_adapter();engine=adapter.G
    stress=0;prefixes=0;large=[];first_indices=set()
    seeds=list(range(stress_seeds))+[2**63-1]
    for seed in seeds:
        baseline=None
        for setting in SETTINGS:
            lesson=adapter.generate(seed,setting,6,4);small=adapter.generate(seed,setting,2,1)
            assert small['train']==lesson['train'][:2] and small['test']==lesson['test'][:1]
            inputs=[p['input'] for split in ('train','test') for p in lesson[split]]
            assert baseline is None or inputs==baseline;baseline=inputs
            assert len({json.dumps(g,separators=(',',':')) for g in inputs})==10
            for rival in engine.RIVALS:
                assert any(engine.solve(p['input'],setting['completion_depth'],rival)!=p['output'] for p in lesson['train'][:2])
            for g in inputs: assert engine.self_check(g)==[]
            one=adapter.present(seed,setting,2,1,presentation_seed=19)
            full=adapter.present(seed,setting,2,4,presentation_seed=19)
            assert one['public']==full['public'][:1]
            first_indices.add(full['private']['source_indices'][0]);prefixes+=1;stress+=1
            q=lesson['test'][-1]
            large.append({'seed':seed,'settings':setting,'zeros':sum(v==0 for row in q['input'] for v in row),
                          'changed_cells':sum(a!=b for ra,rb in zip(q['input'],q['output']) for a,b in zip(ra,rb))})
    assert len(first_indices)>1
    jobs=[];evaluations=0;records=[]
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for setting in SETTINGS:
                for seed in (17,43):
                    for demos in (2,6):
                        lesson=adapter.generate(seed,setting,demos,4)
                        for split in ('train','test'):
                            for pair in lesson[split]:
                                assert _grid(apply(lesson['program_solution'],pair['input']))==pair['output'];evaluations+=1
                        jobs.append({'settings':setting,'seed':seed,'demos':demos,'queries':4})
                        if demos==2:records.append((seed,setting,lesson))
        finally: bridge.close()
    destination.mkdir(parents=True)
    manifest=write_exports(adapter,records,destination/'preview')
    sources=[p for p in HOME.rglob('*') if p.is_file() and p.suffix in ('.py','.rkt') and '__pycache__' not in p.parts]
    report={'schema':'public-eval-family-self-audit-v1','status':'passed','task_id':TASK,
            'protected_racket_evaluations':evaluations,'racket':identity,'jobs':jobs,
            'stress_episodes':stress,'count_prefix_checks':prefixes,'public_views':len(manifest['public_ids']),
            'presentation_first_indices':sorted(first_indices),'large_queries':large,
            'finite_rivals':list(engine.RIVALS),
            'rival_evaluation':'Python executable predictions against protected-Racket-verified labels; finite, not universal uniqueness.',
            'sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(sources)],
            'owner_accepted':False,'training_admitted':False}
    write(destination/'audit.json',report)
    print(json.dumps({k:report[k] for k in ('status','protected_racket_evaluations','stress_episodes','public_views')}))
    return report


def witness(preflight,destination):
    from arcpuzzles.parametric_worker import _grid,_local_imports,_real_evaluator
    destination=Path(destination)
    if destination.exists(): raise FileExistsError(destination)
    receipt=json.loads(Path(preflight).read_text())
    if receipt.get('task_id')!=TASK or receipt.get('status')!='passed': raise ValueError('Wrong preflight')
    for row in receipt['source_binding']['files']:
        if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Source changed after preflight: '+row['path'])
    adapter=load_adapter();settings={'completion_depth':'closure'}
    pair=adapter.generate(17,settings,2,4)['test'][0]
    program=adapter.program(settings);counter=adapter.counterfactual_program(settings)
    intermediate=adapter.intermediate(pair['input'],settings)
    assert intermediate['stage_b_from_stage_a_only']
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try: output=_grid(apply(program,pair['input']));wrong=_grid(apply(counter,pair['input']))
        finally: bridge.close()
    assert output==pair['output'] and output!=wrong
    dependency=adapter.dependency()
    case={'settings':settings,'input':pair['input'],'intermediate_value':intermediate,
          'program':program,'output':output,'counterfactual_program':counter,
          'counterfactual_output':wrong,'ablation':'wrong_intermediate'}
    report={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':TASK,
            'source_binding':receipt['source_binding'],**dependency,
            'racket':{'backend':'racket','protected':True},'racket_identity':identity,'cases':[case]}
    destination.mkdir(parents=True);write(destination/'witness.json',report)
    changed=sum(a!=b for ra,rb in zip(output,wrong) for a,b in zip(ra,rb))
    replay={'status':'author_protected_replayed','protected_racket_evaluations':2,'changed_cells':changed,
            'witness_sha256':hashlib.sha256((destination/'witness.json').read_bytes()).hexdigest(),
            'owner_accepted':False,'training_admitted':False}
    write(destination/'replay.json',replay);print(json.dumps(replay))


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--preflight',type=Path)
    p.add_argument('--stress-seeds',type=int,default=64);a=p.parse_args()
    witness(a.preflight,a.out) if a.preflight else audit(a.out,a.stress_seeds)

if __name__=='__main__':main()
