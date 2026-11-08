"""Reusable finite-rival / protected-label / public-turn / causal audit runner.

All outputs are author-private except individually selected public/<hash>.json
files. The directory listing and private index are controller-only. This runner
never registers, approves, qualifies or accepts source, and never admits training.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
TASK=HOME.name


def _load(name):
    key='_audit_'+TASK+'_'+name+'_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:12]
    spec=importlib.util.spec_from_file_location(key,BASE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[key]=module;spec.loader.exec_module(module)
    return module


def _write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def _digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _root():
    from reviewer_support import find_root
    return find_root(__file__)


def _sources():
    root=_root()
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(HOME.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json'))}


def _settings():
    params=json.loads((BASE/'promotion.json').read_text())['parameters']
    keys=sorted(params)
    return [dict(zip(keys,values)) for values in itertools.product(*(params[k] for k in keys))]


def validate_public_view(view, identifier=None):
    """Validate one actor-visible turn, not the private episode or file listing.

    Return its canonical content ID. Reject metadata, query answers, future
    queries, malformed integer grids, duplicate inputs and stale content IDs.
    This checks serialization/privacy, not semantic correctness of labels.
    """
    from reviewer_support import public_challenge_id
    f=_load('family')
    if type(view) is not dict or set(view)!={'train','test'}:
        raise ValueError('public fields must be exactly train/test')
    if type(view['train']) is not list or not 2 <= len(view['train']) <= 6:
        raise ValueError('public train must have 2..6 demonstrations')
    if type(view['test']) is not list or len(view['test']) != 1:
        raise ValueError('exactly one visible query is required')
    inputs=[]
    for split in ('train','test'):
        for pair in view[split]:
            expected={'input','output'} if split=='train' else {'input'}
            if type(pair) is not dict or set(pair)!=expected:
                raise ValueError('public pair keys expose hidden data or omit a grid')
            for grid in pair.values(): f.check_grid(grid)
            inputs.append(_digest(pair['input']))
    if len(set(inputs)) != len(inputs): raise ValueError('duplicate visible input')
    actual=public_challenge_id(view)
    if identifier is not None and identifier != actual:
        raise ValueError('public filename/content identity mismatch')
    return actual


def run_audit(out, *, seeds, racket_seeds):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    from arcpuzzles.parametric_worker import _real_evaluator
    out=Path(out)
    if out.exists():raise FileExistsError('choose a fresh audit directory')
    if not seeds or len(set(seeds))!=len(seeds):raise ValueError('seeds must be nonempty and unique')
    a,rivals=_load('adapter'),_load('rivals')
    source=_sources();findings=[];exports={};index=[];cache={};runtime=None
    report={'task_id':TASK,'status':'running','episodes':0,'pair_claims':0,'racket_evaluations':0,
            'rival_checks':0,'public_turns':0,'findings':findings,'source_sha256':source,
            'seeds':list(seeds),'racket_seeds':list(racket_seeds),'demo_counts':[2,3,6],
            'limits':'Finite named rivals and sampled sources, not universal uniqueness or learning benefit; no owner acceptance.'}
    bridge=None
    try:
        if racket_seeds:apply,runtime,bridge=_real_evaluator(_root()/'shared/runtime')
        matched={}
        for setting in _settings():
            value=next(iter(setting.values()))
            for seed in seeds:
                for demos in (2,3,6):
                    e=a.generate(seed,setting,demos,4)
                    report['episodes']+=1
                    pairs=e['train']+e['test'];report['pair_claims']+=len(pairs)
                    grids=[p['input'] for p in pairs]
                    if len({_digest(g) for g in grids})!=len(grids):findings.append({'kind':'duplicate_input','seed':seed,'demos':demos})
                    key=(seed,demos)
                    if key in matched and matched[key]!=grids:findings.append({'kind':'unmatched_settings','seed':seed})
                    matched[key]=grids
                    candidates=set(rivals.predict(e['train'][0]['input'],value))
                    report['rival_checks']+=len(candidates)
                    for p in e['train']:
                        predicted=rivals.predict(p['input'],value)
                        candidates={n for n in candidates if predicted[n]==p['output']}
                    for name in sorted(candidates):
                        for qi,p in enumerate(e['test']):
                            if rivals.predict(p['input'],value)[name]!=p['output']:
                                findings.append({'kind':'harmful_survivor','rival':name,'seed':seed,'settings':setting,'demos':demos,'query':qi})
                                break
                    if seed in racket_seeds:
                        for p in pairs:
                            token=(_digest(e['program_solution']),_digest(p['input']))
                            if token not in cache:
                                cache[token]=apply(e['program_solution'],p['input']);report['racket_evaluations']+=1
                            if cache[token]!=p['output']:findings.append({'kind':'racket_parity','seed':seed,'settings':setting})
                    if demos==2 and (seed in (17,43) or seed==seeds[0]):
                        order=a.presentation_order(seed ^ 0x9e3779b9)
                        short=a.generate(seed,setting,2,1)
                        views=[]
                        for i in order:
                            view=a.public_view(e,i)
                            validate_public_view(view)
                            if a.public_view(short,i)!=view:findings.append({'kind':'first_turn_prefix','seed':seed})
                            poisoned=copy.deepcopy(e)
                            poisoned.update(seed='secret',settings={'poison':True},program_solution='hidden')
                            for j,p in enumerate(poisoned['private_query_bank']):
                                p['output']=[[9]]
                                if j!=i:p['input']=[[7]]
                            if a.public_view(poisoned,i)!=view:findings.append({'kind':'private_leak','seed':seed})
                            payload=public_challenge_bytes(view);identifier=public_challenge_id(view)
                            if identifier in exports:findings.append({'kind':'duplicate_public_payload','id':identifier})
                            exports[identifier]=payload;views.append(identifier);report['public_turns']+=1
                        index.append({'settings':setting,'seed':seed,'source_indices':order,'view_ids':views,
                                      'answers':[e['test'][i]['output'] for i in order]})
        report['first_query_indices']=sorted({a.presentation_order(s)[0] for s in range(32)})
        if report['first_query_indices']!=[0,1,2,3]:findings.append({'kind':'presentation_not_varied'})
        if _sources()!=source:raise ValueError('source changed during audit')
    finally:
        if bridge:bridge.close()
    report['status']='passed' if not findings else 'failed';report['racket']=runtime
    out.mkdir(parents=True)
    (out/'public').mkdir()
    for identifier,payload in sorted(exports.items()):
        (out/'public'/f'{identifier}.json').write_bytes(payload)
    _write(out/'private/index.json',{'controller_only':True,'episodes':index})
    _write(out/'report.json',report)
    return report


def build_causal(preflight, out):
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness
    preflight=Path(preflight);out=Path(out)
    if out.exists():raise FileExistsError('choose a fresh causal directory')
    q=json.loads(preflight.read_text())
    if q['task_id']!=TASK or q['status']!='passed' or q.get('owner_accepted') is not False:
        raise ValueError('expected this task authoring preflight, not approval')
    root=_root()
    for row in q['source_binding']['files']:
        if hashlib.sha256((root/row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('source changed since preflight: '+row['path'])
    execution_path=preflight.with_name('execution.json')
    if hashlib.sha256(execution_path.read_bytes()).hexdigest()!=q['evidence_sha256']['execution.json']:
        raise ValueError('preflight execution evidence changed')
    a=_load('adapter');execution=json.loads(execution_path.read_text())
    episode=next(e for e in execution['episodes'] if e['settings']==a.causal_settings())
    p=next(p for p in episode['test'] if len(p['input'])==30 and len(p['input'][0])==30)
    apply,runtime,bridge=_real_evaluator(root/'shared/runtime')
    try:
        actual=apply(episode['program_solution'],p['input'])
        wrong=apply(a.counterfactual_program(),p['input'])
        if actual!=p['output'] or actual==wrong:raise ValueError('causal output mismatch/no effect')
    finally:bridge.close()
    witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':q['source_binding'],
             'racket':{'backend':'racket','protected':True},**a.CAUSAL_DESCRIPTIONS,
             'cases':[{'input':p['input'],'settings':episode['settings'],
                       'intermediate_value':a.causal_intermediate(p['input']),
                       'program':episode['program_solution'],'output':actual,
                       'counterfactual_program':a.counterfactual_program(),'counterfactual_output':wrong,
                       'ablation':'wrong_intermediate'}]}
    raw=(json.dumps(witness,sort_keys=True,indent=2)+'\n').encode()
    validate_sequential_witness({'sequential_dependency':{**a.CAUSAL_DESCRIPTIONS,'witness_path':'witness.json'}},q,lambda p:raw)
    replay=replay_witness(root,witness)
    replay.update(status='reviewer_replayed',owner_accepted=False,
                  caller_scope='Reviewer authoring replay, not owner acceptance')
    out.mkdir(parents=True)
    (out/'witness.json').write_bytes(raw);_write(out/'replay.json',replay)
    return {'status':'reviewer_replayed','evaluations':4,'changed_cells':sum(x!=y for ar,br in zip(actual,wrong) for x,y in zip(ar,br)),
            'racket':runtime,'owner_accepted':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,nargs='+',default=[0,1,17,43])
    p.add_argument('--racket-seeds',type=int,nargs='*',default=[0,17,43])
    p.add_argument('--causal-preflight',type=Path)
    args=p.parse_args()
    report=(build_causal(args.causal_preflight,args.out) if args.causal_preflight else
            run_audit(args.out,seeds=args.seeds,racket_seeds=args.racket_seeds))
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_sha256','racket')},sort_keys=True))
    return 0 if report['status'] in ('passed','reviewer_replayed') else 1

if __name__=='__main__':raise SystemExit(main())
