"""Reusable unapproved-public-family audit/export tool; never grants acceptance.

Run with this packet's `review.py run python3 <this-file> audit --preflight ...
--out ...`. The owner-only native preview/witness helpers require registration;
this tool binds to the deliberately weaker public authoring preflight instead.
All reference labels and both causal labels are executed with protected Racket.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import sys
import tempfile

HERE=Path(__file__).resolve().parent
HOME=HERE.parents[1]
ROOT=next(p for p in HERE.parents if (p/'src/arcpuzzles/parametric_worker.py').is_file())
TASK=HOME.name
sys.path.insert(0,str(ROOT/'src'))
spec=importlib.util.spec_from_file_location('_authoring_'+TASK,HERE/'family.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)


def raw(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw(value))


def bound(preflight):
    path=Path(preflight);q=json.loads(path.read_bytes())
    if (q.get('schema')!='arcpuzzles-public-eval-authoring-preflight-v1'
        or q.get('status')!='passed' or q.get('owner_accepted') is not False
        or q.get('task_id')!=TASK):
        raise ValueError('Expected this family\'s passing UNAPPROVED authoring preflight')
    for row in q['source_binding']['files']:
        source=ROOT/row['path']
        if source.is_symlink() or not source.resolve().is_relative_to(ROOT) or sha(source.read_bytes())!=row['sha256']:
            raise ValueError('Stale or escaping source: '+row['path'])
    for name,digest in q['evidence_sha256'].items():
        if sha((path.parent/name).read_bytes())!=digest:raise ValueError('Preflight evidence has drifted')
    return q,json.loads((path.parent/'execution.json').read_bytes())


def projection(episodes,presentation_seed):
    if type(presentation_seed) is not int:raise ValueError('Exact integer presentation seed required')
    views={};mapping=[]
    for i,ep in enumerate(episodes):
        if len(ep['test'])!=4:raise ValueError('Exactly four private queries required')
        all_inputs=[raw(f.strict_grid(p['input'])) for s in ('train','test') for p in ep[s]]
        if len(set(all_inputs))!=len(all_inputs):raise ValueError('Duplicate episode input')
        order=list(range(4))
        random.Random(f'public-authoring-presentation-v2:{i}:{presentation_seed}').shuffle(order)
        ids=[]
        for index in order:
            content=f.public_view(ep,index);key=sha(content)
            if key in views:raise ValueError('Duplicate visible view')
            views[key]=content;ids.append(key)
        mapping.append({'episode_index':i,'source_indices':order,'view_ids':ids})
    return views,mapping


def check_public_files(public,views):
    public=Path(public)
    if public.is_symlink() or not public.is_dir():raise ValueError('Public path must be a real directory')
    if any(p.is_symlink() or not p.is_file() for p in public.iterdir()):raise ValueError('Unexpected public entry')
    if {p.name for p in public.iterdir()}!={key+'.json' for key in views}:raise ValueError('Unexpected/missing public view')
    for key,content in views.items():
        if (public/(key+'.json')).read_bytes()!=content:raise ValueError('Visible bytes/hash mismatch')


def export_projection(preflight,output,presentation_seed=41):
    q,ex=bound(preflight);views,mapping=projection(ex['episodes'],presentation_seed)
    output=Path(output)
    if output.exists():raise FileExistsError('Choose a fresh export directory')
    output.mkdir(parents=True);(output/'public').mkdir();(output/'private').mkdir(mode=0o700)
    for key,content in views.items():(output/'public'/(key+'.json')).write_bytes(content)
    for name in ('preflight.json','execution.json','original-pairs.json'):
        shutil.copyfile(Path(preflight).parent/name,output/'private'/name)
    manifest={'schema':'arcpuzzles-unapproved-public-authoring-projection-v1','task_id':TASK,
              'source_binding':q['source_binding'],'preflight_sha256':sha(Path(preflight).read_bytes()),
              'presentation_seed':presentation_seed,'episodes':mapping,
              'public_files':[{'path':'public/'+key+'.json','sha256':key} for key in sorted(views)],
              'owner_accepted':False,'training_admitted':False,
              'limits':'Serialized projection of protected authoring labels; NOT native qualification or acceptance. Reveal one file only.'}
    save(output/'private/manifest.json',manifest)
    return verify_export(output)


def verify_export(output):
    output=Path(output)
    if output.is_symlink():raise ValueError('Symlink bundle rejected')
    q,ex=bound(output/'private/preflight.json')
    m=json.loads((output/'private/manifest.json').read_bytes())
    if (m.get('schema')!='arcpuzzles-unapproved-public-authoring-projection-v1'
        or m.get('source_binding')!=q['source_binding'] or m.get('task_id')!=TASK
        or m.get('preflight_sha256')!=sha((output/'private/preflight.json').read_bytes())
        or m.get('owner_accepted') is not False or m.get('training_admitted') is not False):
        raise ValueError('Invalid public-authoring projection binding')
    views,mapping=projection(ex['episodes'],m['presentation_seed'])
    expected_files=[{'path':'public/'+key+'.json','sha256':key} for key in sorted(views)]
    if mapping!=m['episodes'] or expected_files!=m['public_files']:raise ValueError('Private mapping changed')
    expected={'private/preflight.json','private/execution.json','private/original-pairs.json','private/manifest.json'}|{v['path'] for v in expected_files}
    if any(p.is_symlink() for p in output.rglob('*')):raise ValueError('Bundle symlink rejected')
    if {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}!=expected:raise ValueError('Unexpected bundle files')
    check_public_files(output/'public',views)
    return {'status':'verified_unapproved_projection','episodes':len(mapping),'views':len(views),
            'owner_accepted':False,'training_admitted':False}


def privacy_checks(episodes,presentation_seed=41):
    _,mapping=projection(episodes,presentation_seed);checks=[]
    for row,ep in zip(mapping,episodes):
        shown=deepcopy(ep);shown['test']=[deepcopy(ep['test'][i]) for i in row['source_indices']]
        baseline=f.public_view(shown,0);variants=[]
        v=deepcopy(shown);v['test']=v['test'][:1];variants.append(('one_query_only',v))
        v=deepcopy(shown)
        for key in list(v):
            if key not in ('train','test'):v[key]={'private':'rewritten'}
        variants.append(('all_private_metadata',v))
        v=deepcopy(shown)
        for p in v['test']:p['output']={'private':'not a grid'}
        variants.append(('answers_rewritten',v))
        v=deepcopy(shown)
        for p in v['test']:p.pop('output',None)
        variants.append(('answers_removed',v))
        v=deepcopy(shown);v['test'][1:]=[{'private':'future'}, {'input':'not visible'},{}]
        variants.append(('future_queries_invalid',v))
        v=deepcopy(shown);v['test'][1:]=list(reversed(v['test'][1:]))+[{'input':[[9]]}]
        variants.append(('future_order_and_count',v))
        for name,value in variants:
            if f.public_view(value,0)!=baseline:raise ValueError('Private-field leak: '+name)
        positive=deepcopy(shown);positive['test'][0]['input'][0][0]=(positive['test'][0]['input'][0][0]+1)%10
        if f.public_view(positive,0)==baseline:raise ValueError('Visible positive control failed')
        checks.append({'episode_index':row['episode_index'],'first_source_index':row['source_indices'][0],
                       'invariance_checks':[name for name,_ in variants],'positive_control':'passed'})
    return {'status':'passed','cases':checks,'mutations':6*len(checks),'positive_controls':len(checks)}


def select_causal_pair(episode,program,counter,executed):
    """Prefer an executed 30x30 query over an incidental first demonstration.

    Candidate labels must differ successfully; interpreter exceptions propagate
    rather than counting as evidence of a causal effect. Return None if no case
    differs, leaving the caller to report the missing witness honestly.
    """
    candidates=list(episode['test'])+list(episode['train'])
    candidates.sort(key=lambda p: (len(p['input'])==30 and len(p['input'][0])==30), reverse=True)
    return next((p for p in candidates
                 if executed(program,p['input'])!=executed(counter,p['input'])),None)


def audit(preflight,output,census_seeds=128):
    from arcpuzzles.parametric_promotion import settings_space
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness
    q,ex=bound(preflight);output=Path(output)
    if output.exists():raise FileExistsError('Choose a fresh audit directory')
    output.mkdir(parents=True)
    settings=settings_space(q['contract']);jobs=[];cache={};comparisons=0
    with _local_imports(ROOT/'shared/runtime',HERE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            def executed(text,grid):
                key=sha(text.encode()+raw(grid))
                if key not in cache:cache[key]=_grid(apply(text,grid))
                return cache[key]
            for seed in (0,17,97):
                for demos in (2,3,6):
                    matched=None
                    for setting in settings:
                        ep=f.generate(seed,setting,demos,4)
                        inputs=[p['input'] for s in ('train','test') for p in ep[s]]
                        if matched is not None and matched!=inputs:raise ValueError('Setting-dependent input leakage')
                        matched=inputs
                        if len({sha(raw(g)) for g in inputs})!=len(inputs):raise ValueError('Duplicate input')
                        survivors=f.surviving_rivals(ep)
                        if survivors:raise ValueError('Wrong rule survives teaching: '+str((seed,demos,setting,survivors)))
                        for split in ('train','test'):
                            for p in ep[split]:
                                if executed(ep['program_solution'],p['input'])!=p['output']:raise ValueError('Racket/Python disagreement')
                                comparisons+=1
                        stress=sum(len(p['input'])==len(p['input'][0])==30 or len(p['output'])==len(p['output'][0])==30 for p in ep['test'])
                        if not stress:raise ValueError('Missing 30x30 stress')
                        jobs.append({'seed':seed,'demos':demos,'queries':4,'settings':setting,'surviving_rivals':survivors,'stress_pairs':stress})
            # Select a preflight-admitted alternate episode, not a hand-picked external grid.
            ep=next(e for e in ex['episodes'] if e['settings']!=q['contract']['default'])
            program=ep['program_solution'];counter=(HERE/f.COUNTERFACTUAL_FILE).read_text()
            pair=select_causal_pair(ep,program,counter,executed)
            if pair is None:raise ValueError('No retained causal counterexample')
            actual=executed(program,pair['input']);alternative=executed(counter,pair['input'])
            if actual!=pair['output'] or actual==alternative:raise ValueError('Causal ablation fails')
            desc=f.dependency()
            witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':q['source_binding'],
                     'racket':{'backend':'racket','protected':True},**desc,
                     'cases':[{'input':pair['input'],'settings':ep['settings'],'intermediate_value':f.causal_value(pair['input']),
                               'program':program,'output':actual,'counterfactual_program':counter,
                               'counterfactual_output':alternative,'ablation':'wrong_intermediate'}]}
            save(output/'causal/witness.json',witness)
            static=validate_sequential_witness({'sequential_dependency':{**desc,'witness_path':'witness.json'}},q,lambda _:raw(witness))
            save(output/'causal/static.json',static)
        finally:bridge.close()
    replay=replay_witness(ROOT,witness,timeout=60)
    # The shared helper's literal status says owner_replayed; this invocation is
    # an author/reviewer run, so do not misrepresent it as owner acceptance.
    replay['status']='reviewer_replayed';replay['owner_accepted']=False
    save(output/'causal/replay.json',replay)
    census=[];sizes=set();colors=set();first_queries=set()
    for seed in range(census_seeds):
        matched=None
        for setting in settings:
            ep=f.generate(seed,setting,2,4);wide=f.generate(seed,setting,6,4)
            if ep['train']!=wide['train'][:2] or ep['test']!=wide['test']:raise ValueError('Count-dependent RNG drift')
            for query_count in (1,2,3):
                short=f.generate(seed,setting,2,query_count)
                if short['test']!=ep['test'][:query_count] or short['private_query_bank']!=ep['test']:
                    raise ValueError('Query prefix depends on requested count')
                if f.public_view(short,0)!=f.public_view(ep,0):raise ValueError('First-turn drift')
            if f.surviving_rivals(ep):raise ValueError('Census rival survives: '+str((seed,setting)))
            inputs=[p['input'] for s in ('train','test') for p in ep[s]]
            if matched is not None and matched!=inputs:raise ValueError('Census setting-dependent inputs')
            matched=inputs
            for s in ('train','test'):
                for p in wide[s]:
                    f.strict_grid(p['input']);f.strict_grid(p['output']);f.analyze(p['input'])
                    sizes.add((len(p['output']),len(p['output'][0])))
                    colors.update(v for row in p['input'] for v in row)
            first_queries.add((len(ep['test'][0]['input']),len(ep['test'][0]['output'])))
            census.append({'seed':seed,'settings':setting,'status':'passed'})
    save(output/'census.json',{'status':'passed','episodes':len(census),'seeds':census_seeds,
                            'counts_checked':[2,6],'query_counts_checked':[1,2,3,4],'output_sizes':sorted(sizes),'source_colors':sorted(colors),
                            'first_query_size_profiles':sorted(first_queries),'rows':census})
    exported=export_projection(preflight,output/'preview')
    private=privacy_checks(ex['episodes']);save(output/'first-turn.json',private)
    negatives=[]
    with tempfile.TemporaryDirectory() as temp:
        copy=Path(temp)/'bundle';shutil.copytree(output/'preview',copy)
        public=next((copy/'public').iterdir());original=public.read_bytes()
        public.write_bytes(original+b' ')
        try:verify_export(copy)
        except ValueError:negatives.append('changed_visible_bytes')
        else:raise ValueError('Corrupt visible bytes accepted')
        public.write_bytes(original);(copy/'public'/'extra.json').write_text('{}')
        try:verify_export(copy)
        except ValueError:negatives.append('extra_public_file')
        else:raise ValueError('Extra public file accepted')
        (copy/'public'/'extra.json').unlink()
        manifest=copy/'private/manifest.json';value=json.loads(manifest.read_bytes());value['episodes'][0]['source_indices'].reverse();save(manifest,value)
        try:verify_export(copy)
        except ValueError:negatives.append('changed_presentation_mapping')
        else:raise ValueError('Wrong private mapping accepted')
    bound(preflight)
    result={'schema':'arcpuzzles-public-creation-bounded-audit-v1','task_id':TASK,'status':'passed',
            'source_binding':q['source_binding'],'jobs':jobs,'label_comparisons':comparisons,
            'protected_evaluations':len(cache),'racket':identity,'census_episodes':len(census),
            'rivals':list(f.a.model.RIVALS), 'rival_checks':(len(jobs)+len(census))*len(f.a.model.RIVALS),
            'causal_replay_evaluations':replay['evaluations'],'projection':exported,
            'privacy_mutations':private['mutations'],'negative_export_checks':negatives,
            'limits':'Finite declared Python rivals; all checked gold labels and causal labels executed in protected Racket. No universal rule uniqueness, owner acceptance or training admission.'}
    save(output/'audit.json',result)
    return {k:v for k,v in result.items() if k not in ('jobs','source_binding','racket')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('audit');a.add_argument('--preflight',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--census-seeds',type=int,default=128)
    v=sub.add_parser('verify-export');v.add_argument('--bundle',type=Path,required=True)
    args=parser.parse_args()
    if args.cmd=='audit':
        if not 1<=args.census_seeds<=1024:parser.error('census seeds must be 1..1024')
        result=audit(args.preflight,args.out,args.census_seeds)
    else:result=verify_export(args.bundle)
    print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
