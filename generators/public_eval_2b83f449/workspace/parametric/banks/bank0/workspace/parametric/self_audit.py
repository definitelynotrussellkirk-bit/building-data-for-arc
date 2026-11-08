"""Rerunnable protected-label audit, sequential public writer and causal replay.

All exports and reports are author-private bundles. Give a model just one file
from public/, never the directory listing, manifest, private/ or this program.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

from reviewer_support import find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[2]
ROOT = find_root(__file__)
TASK = HOME.name
DEPENDENCY = {
    'step_a': 'Rotate the orange gates and extract complete cyan track components.',
    'intermediate': 'Exact component membership, endpoints, and original green-token counts on the rotated tracks.',
    'step_b': 'Select each track\'s lower or upper endpoint and pack that track\'s green tokens along its path.',
    'why_b_depends_on_a': 'Gate rotation joins and splits horizontal rails, changing which tokens share a destination. An old-rail component partition yields different placements.'}


def load_adapter():
    path = HOME/'workspace/parametric/adapter.py'
    name = '_audit_adapter_'+hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def _int(value,lo,hi,name):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')


def project_episode(episode, *, source_seed, presentation_seed=0, turns=4):
    _int(source_seed,0,2**63-1,'source_seed');_int(presentation_seed,0,2**63-1,'presentation_seed');_int(turns,1,4,'turns')
    if type(episode) is not dict or type(episode.get('test')) is not list or len(episode['test']) != 4:
        raise ValueError('Project the complete four-query bank, then truncate public turns')
    order = list(range(4))
    material = json.dumps([TASK,source_seed,presentation_seed],separators=(',',':')).encode()
    random.Random(int.from_bytes(hashlib.sha256(material).digest(),'big')).shuffle(order)
    visible=[]
    for i in order[:turns]:
        public={'train':copy.deepcopy(episode['train']),'test':[{'input':copy.deepcopy(episode['test'][i]['input'])}]}
        # This canonical projection also strips unknown keys and rejects bools.
        visible.append(json.loads(public_challenge_bytes(public)))
    private={'source_seed':source_seed,'presentation_seed':presentation_seed,'source_indices':order[:turns],
             'answers':[copy.deepcopy(episode['test'][i]['output']) for i in order[:turns]]}
    return visible,private


def write_exports(records, destination: Path, *, presentation_seed=0):
    destination=Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    payloads={};private=[]
    # Preflight every byte and duplicate before creating any output directory.
    for record in records:
        views,meta=project_episode(record['episode'],source_seed=record['seed'],presentation_seed=presentation_seed)
        ids=[]
        for view in views:
            raw=public_challenge_bytes(view);key=hashlib.sha256(raw).hexdigest()
            if key in payloads:
                raise ValueError('Duplicate visible challenge in requested export')
            payloads[key]=raw;ids.append(key)
        private.append({**meta,'settings':record['settings'],'program':record['episode']['program_solution'],'view_ids':ids})
    (destination/'public').mkdir(parents=True)
    (destination/'private').mkdir()
    for key in sorted(payloads):
        (destination/'public'/f'{key}.json').write_bytes(payloads[key])
    private_raw=(json.dumps(private,sort_keys=True,indent=2)+'\n').encode()
    (destination/'private'/'episodes.json').write_bytes(private_raw)
    manifest={'schema':'public-eval-authoring-sequential-export-v1','task_id':TASK,
              'public_ids':sorted(payloads),'private_sha256':hashlib.sha256(private_raw).hexdigest(),
              'owner_accepted':False,'training_admitted':False,'controller_only':True}
    (destination/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest


def _write(path,value):
    Path(path).write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def audit(destination: Path, stress_seeds=32):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    if destination.exists():raise FileExistsError(destination)
    adapter=load_adapter();core=adapter.CORE
    contract=json.loads((HOME/'workspace/parametric/promotion.json').read_text())
    key=next(iter(contract['parameters']));settings=[{key:v} for v in contract['parameters'][key]]
    seeds=list(range(stress_seeds))+[2**63-1]
    stress=0;prefixes=0;large=[]
    for seed in seeds:
        baseline=None
        for setting in settings:
            lesson=adapter.generate(seed,setting,6,4)
            small=adapter.generate(seed,setting,2,1)
            assert small['train']==lesson['train'][:2] and small['test']==lesson['test'][:1]
            prefixes+=1
            inputs=[p['input'] for s in ('train','test') for p in lesson[s]]
            assert baseline is None or inputs==baseline
            baseline=inputs
            assert len({json.dumps(g) for g in inputs})==10
            assert adapter.surviving_rules(lesson['train'][:2],setting[key])==['intended']
            for g in inputs:assert core.self_check(g)==[]
            q=lesson['test'][-1]
            assert len(q['input'])==len(q['input'][0])==30
            large.append({'seed':seed,'settings':setting,'nonzero_input':sum(v!=0 for row in q['input'] for v in row),
                          'changed_cells':sum(a!=b for ra,rb in zip(q['input'],q['output']) for a,b in zip(ra,rb))})
            one,_=project_episode(lesson,source_seed=seed,presentation_seed=5,turns=1)
            four,_=project_episode(lesson,source_seed=seed,presentation_seed=5,turns=4)
            assert one==four[:1]
            stress+=1
    evaluations=0;jobs=[];exports=[]
    with _local_imports(ROOT/'shared/runtime',HOME/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for setting in settings:
                for seed in (17,43):
                    for demos in (2,6):
                        lesson=adapter.generate(seed,setting,demos,4)
                        for split in ('train','test'):
                            for pair in lesson[split]:
                                assert _grid(apply(lesson['program_solution'],pair['input']))==pair['output']
                                evaluations+=1
                        jobs.append({'settings':setting,'seed':seed,'demos':demos,'queries':4})
                        if demos==2:exports.append({'seed':seed,'settings':setting,'episode':lesson})
        finally:bridge.close()
    destination.mkdir(parents=True)
    exported=write_exports(exports,destination/'preview')
    # Record exact source hashes for this audit independently of later preflight.
    sources=[p for p in HOME.rglob('*') if p.is_file() and p.suffix in ('.py','.rkt') and '__pycache__' not in p.parts]
    report={'schema':'public-eval-family-self-audit-v1','status':'passed','task_id':TASK,'jobs':jobs,
            'protected_racket_evaluations':evaluations,'racket':identity,'stress_episodes':stress,'count_prefix_checks':prefixes,
            'public_views':len(exported['public_ids']),'large_queries':large,
            'finite_rivals':list(adapter.RIVALS),'rival_evaluation':'Python predictions against Racket-verified setting labels; not exhaustive uniqueness',
            'sources':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(sources)],
            'limits':'Finite sampled seeds and declared rivals only; no owner qualification, acceptance or training admission.'}
    _write(destination/'audit.json',report)
    print(json.dumps({k:report[k] for k in ('status','task_id','protected_racket_evaluations','stress_episodes','public_views')}))
    return report


def witness(preflight: Path, destination: Path):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    if destination.exists():raise FileExistsError(destination)
    receipt=json.loads(preflight.read_text())
    if receipt['task_id']!=TASK or receipt['status']!='passed':raise ValueError('Wrong or failed preflight')
    for row in receipt['source_binding']['files']:
        if hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('Source changed after preflight: '+row['path'])
    execution=json.loads((preflight.parent/'execution.json').read_text())
    episode=execution['episodes'][0];pair=episode['test'][0];program=episode['program_solution']
    counterfactual=program.replace('(define routing-grid rotated)','(define routing-grid initial)')
    if counterfactual==program:raise ValueError('Ablation site missing')
    adapter=load_adapter();_,records=adapter.CORE.tracks(pair['input'])
    intermediate=[{k:v for k,v in record.items() if k!='adjacency'} for record in records if record['tokens']]
    with _local_imports(ROOT/'shared/runtime',HOME/'workspace/parametric'):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            output=_grid(apply(program,pair['input']))
            wrong=_grid(apply(counterfactual,pair['input']))
        finally:bridge.close()
    assert output==pair['output'] and output!=wrong
    case={'settings':episode['settings'],'input':pair['input'],'program':program,'output':output,
          'intermediate_value':intermediate,'counterfactual_program':counterfactual,'counterfactual_output':wrong,
          'ablation':'wrong_intermediate'}
    report={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':TASK,
            'source_binding':receipt['source_binding'],**DEPENDENCY,
            'racket':{'backend':'racket','protected':True},'racket_identity':identity,'cases':[case]}
    destination.mkdir(parents=True);_write(destination/'witness.json',report)
    diff=sum(a!=b for ra,rb in zip(output,wrong) for a,b in zip(ra,rb))
    _write(destination/'replay.json',{'status':'author_protected_replayed','protected_racket_evaluations':2,
                                    'changed_cells':diff,'witness_sha256':hashlib.sha256((destination/'witness.json').read_bytes()).hexdigest(),
                                    'owner_accepted':False})
    print(json.dumps({'status':'author_protected_replayed','changed_cells':diff}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--preflight',type=Path)
    parser.add_argument('--stress-seeds',type=int,default=32)
    args=parser.parse_args()
    if args.preflight:witness(args.preflight,args.out)
    else:audit(args.out,args.stress_seeds)

if __name__=='__main__':main()
