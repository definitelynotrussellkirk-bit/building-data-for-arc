"""Reusable bounded authoring audit for an unapproved public ARC family.

Run under the packet wrapper so protected Racket is available:
  python3 review.py run python3 generators/TASK/workspace/parametric/authoring.py \
      audit --preflight ../checks/TASK/preflight/preflight.json \
      --out ../checks/TASK/authoring --census-seeds 128

This tool verifies source binding, protected labels, finite declared rivals,
count-independent sampling, matched inputs, sequential public views, and a
bounded seed census.  It never grants owner acceptance or training admission.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import sys

HERE=Path(__file__).resolve().parent
HOME=HERE.parents[1]
ROOT=next(p for p in HERE.parents if (p/'src/arcpuzzles/parametric_worker.py').is_file())
TASK=HOME.name
spec=importlib.util.spec_from_file_location('_authoring_'+TASK,HERE/'family.py')
f=importlib.util.module_from_spec(spec);sys.modules[spec.name]=f;spec.loader.exec_module(f)


def raw(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def sha_bytes(value):return hashlib.sha256(value).hexdigest()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw(value))


def bind(preflight):
    preflight=Path(preflight);q=json.loads(preflight.read_bytes())
    if (q.get('schema')!='arcpuzzles-public-eval-authoring-preflight-v1'
        or q.get('status')!='passed' or q.get('owner_accepted') is not False
        or q.get('task_id')!=TASK):
        raise ValueError('Expected this task\'s passing unapproved authoring preflight')
    for row in q['source_binding']['files']:
        source=ROOT/row['path']
        if (source.is_symlink() or not source.is_file()
            or not source.resolve().is_relative_to(ROOT)
            or sha_bytes(source.read_bytes())!=row['sha256']):
            raise ValueError('Stale or escaping source: '+row['path'])
    for name,digest in q['evidence_sha256'].items():
        if sha_bytes((preflight.parent/name).read_bytes())!=digest:
            raise ValueError('Preflight evidence drift: '+name)
    return q,json.loads((preflight.parent/'execution.json').read_bytes())


def visible_projection(episodes,out,presentation_seed=73):
    out=Path(out);(out/'public').mkdir(parents=True);(out/'private').mkdir(parents=True)
    files=[];mapping=[]
    for episode_index,ep in enumerate(episodes):
        if len(ep['test'])!=4:raise ValueError('Exactly four private queries required')
        order=list(range(4));random.Random(f'{TASK}:{presentation_seed}:{episode_index}').shuffle(order)
        ids=[]
        for query_index in order:
            content=f.public_view(ep,query_index);digest=sha_bytes(content)
            path=out/'public'/(digest+'.json')
            if path.exists() and path.read_bytes()!=content:raise ValueError('View digest collision')
            path.write_bytes(content);ids.append(digest)
            files.append({'path':'public/'+digest+'.json','sha256':digest})
        mapping.append({'episode_index':episode_index,'source_indices':order,'view_ids':ids})
    if len({row['path'] for row in files})!=len(files):raise ValueError('Duplicate public views')
    manifest={'schema':'arcpuzzles-unapproved-public-authoring-projection-v1','task_id':TASK,
              'presentation_seed':presentation_seed,'episodes':mapping,
              'public_files':sorted(files,key=lambda x:x['path']),
              'owner_accepted':False,'training_admitted':False,
              'limits':'One-query serialized views only; not qualification or acceptance.'}
    save(out/'private/manifest.json',manifest)
    expected={row['path'] for row in files}|{'private/manifest.json'}
    actual={p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}
    if actual!=expected:raise ValueError('Unexpected projection files')
    for row in files:
        if sha_bytes((out/row['path']).read_bytes())!=row['sha256']:raise ValueError('Projection digest mismatch')
    return {'episodes':len(episodes),'views':len(files),'status':'verified_unapproved_projection'}


def privacy_checks(episodes):
    mutations=0;positive=0
    for ep in episodes:
        base=f.public_view(ep,0)
        changed=copy.deepcopy(ep)
        changed['program_solution']='private-program-mutation'
        changed['test'][0]['output']=[[9]]
        for row in changed['test'][1:]:
            row['input']=[[9]];row['output']=[[8]]
        if f.public_view(changed,0)!=base:raise ValueError('Private/future field leaked into first turn')
        mutations+=2+2*max(0,len(changed['test'])-1)
        visible=copy.deepcopy(ep)
        old=visible['test'][0]['input'][0][0];visible['test'][0]['input'][0][0]=(old+1)%10
        if f.public_view(visible,0)==base:raise ValueError('Visible query mutation did not change bytes')
        positive+=1
    return {'status':'passed','episodes':len(episodes),'mutations':mutations,'positive_controls':positive}


def audit(preflight,out,census_seeds):
    q,execution=bind(preflight);out=Path(out)
    if out.exists():raise FileExistsError('Choose a fresh audit output directory')
    out.mkdir(parents=True)
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    wrapped={};cache={};comparisons=0;jobs=[]
    def literal(g):return "'("+' '.join('('+' '.join(map(str,row))+')' for row in g)+')'
    bridge=RacketBridge()
    try:
        identity=bridge.runtime_identity
        def execute(program,g):
            key=(sha_bytes(program.encode()),sha_bytes(raw(g)))
            if key not in cache:
                wrapped.setdefault(program,wrap_rule(program))
                cache[key]=bridge.eval_text(f'({wrapped[program]} {literal(g)})')
            return cache[key]
        settings=list(f.a.SETTINGS)
        for seed in (0,17,97):
            for demos in (2,3,6):
                inputs_by_setting=[]
                for setting in settings:
                    ep=f.generate(seed,setting,demos,4)
                    base=f.generate(seed,setting,2,4);wide=f.generate(seed,setting,6,4)
                    if ep['train'][:2]!=base['train'] or ep['test']!=base['test']:
                        raise ValueError('Prefix/count-dependent RNG drift')
                    if wide['train'][:2]!=base['train'] or wide['test']!=base['test']:
                        raise ValueError('Wide-prefix drift')
                    pairs=ep['train']+ep['test'];inputs=[p['input'] for p in pairs]
                    if len({sha_bytes(raw(g)) for g in inputs})!=len(inputs):raise ValueError('Duplicate episode input')
                    if len(ep['test'])!=4 or len(ep['test'][-1]['input'])!=30 or len(ep['test'][-1]['input'][0])!=30:
                        raise ValueError('Missing four-query or exact-30 stress contract')
                    survivors=f.surviving_rivals(ep)
                    if survivors:raise ValueError('Declared rival survives: '+str((seed,demos,setting,survivors)))
                    for pair in pairs:
                        f.strict_grid(pair['input']);f.strict_grid(pair['output'])
                        if execute(ep['program_solution'],pair['input'])!=pair['output']:
                            raise ValueError('Protected-Racket label mismatch')
                        comparisons+=1
                    inputs_by_setting.append(inputs)
                    jobs.append({'seed':seed,'demos':demos,'settings':setting,
                                 'pairs':len(pairs),'rivals':len(f.engine.rivals(setting['finish'])),
                                 'status':'passed'})
                if inputs_by_setting[0]!=inputs_by_setting[1]:raise ValueError('Setting-dependent input generation')
    finally:
        bridge.close()

    census=[];size_profiles=set()
    for seed in range(census_seeds):
        matched=None
        for setting in f.a.SETTINGS:
            short=f.generate(seed,setting,2,4);wide=f.generate(seed,setting,6,4)
            if short['train']!=wide['train'][:2] or short['test']!=wide['test']:
                raise ValueError('Census prefix drift')
            if f.surviving_rivals(short):raise ValueError('Census rival survivor')
            inputs=[p['input'] for s in ('train','test') for p in short[s]]
            if matched is not None and matched!=inputs:raise ValueError('Census setting-dependent inputs')
            matched=inputs
            size_profiles.update((len(g),len(g[0])) for g in inputs)
        census.append({'seed':seed,'status':'passed'})
    save(out/'census.json',{'status':'passed','seeds':census_seeds,'episodes':2*census_seeds,
                            'size_profiles':sorted(size_profiles),'rows':census,
                            'limits':'Finite seed and declared-rival census; not universal uniqueness.'})
    projection=visible_projection(execution['episodes'],out/'preview')
    privacy=privacy_checks(execution['episodes']);save(out/'first-turn.json',privacy)
    result={'schema':'arcpuzzles-public-creation-bounded-audit-v1','task_id':TASK,'status':'passed',
            'source_binding':q['source_binding'],'jobs':jobs,'label_comparisons':comparisons,
            'protected_evaluations':len(cache),'racket':identity,'census_episodes':2*census_seeds,
            'projection':projection,'privacy':privacy,'owner_accepted':False,'training_admitted':False,
            'limits':'Finite generated support and declared rivals. Protected labels executed; no owner acceptance or universal rule uniqueness.'}
    save(out/'audit.json',result)
    return {k:v for k,v in result.items() if k not in ('source_binding','jobs','racket')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('audit');p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--census-seeds',type=int,default=128)
    args=parser.parse_args()
    if not 1<=args.census_seeds<=1024:parser.error('census-seeds must be 1..1024')
    print(json.dumps(audit(args.preflight,args.out,args.census_seeds),sort_keys=True))

if __name__=='__main__':main()
