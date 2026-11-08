"""Source-bound public-creation audit, public projection, and causal replay.

Run with this checkout's Racket wrapper after authoring preflight. This never
registers, approves, qualifies or accepts a family. Output directories are fresh.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
HOME=HERE.parents[1]
ROOT=HOME.parents[1]
DESCRIPTIONS={'step_a': 'Align the complete orange port patterns at unit cardinal distance, enforce reciprocal yellow coverage and no collision, then assemble the pieces.', 'intermediate': 'The collision-free joined yellow boundary and its 4-connected enclosed background regions.', 'step_b': 'Flood the complement of the assembled boundary and fill every enclosed blue pocket with cyan 8.', 'why_b_depends_on_a': 'Joining can close pockets that were open in both source pieces. Filling individual pieces before docking misses those new pockets; the assembled topology is required.'}
COUNTERFACTUAL='fill_before_join_counterfactual.rkt'


def raw(value):
    return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(raw(value))


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_binding(root,binding):
    root=Path(root).resolve()
    for row in binding['files']:
        relative=Path(row['path']);path=root/relative
        if (relative.is_absolute() or '..' in relative.parts or path.is_symlink()
            or not path.is_file() or not path.resolve().is_relative_to(root)
            or sha(path)!=row['sha256']):
            raise ValueError('Source binding differs: '+str(relative))


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def intermediate(source,g):
    d=source.decode(g)
    after=source.holes(d['solid'])
    before=source.holes(d['a'])|source.shift(source.holes(d['b']),d['delta'])
    return {'translation':list(d['delta']),'assembled_bbox':list(source.bbox(d['solid'])),
            'enclosed_cells_after_assembly':len(after),'enclosed_cells_before_assembly':len(before),
            'newly_enclosed_cells':len(after-before),'candidate_translations':d['candidate_count']}


def verify(preflight_path,out,seeds):
    from arcpuzzles.parametric_worker import _grid,_local_imports,_real_evaluator
    from arcpuzzles.review_witness import _validate_programs
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from reviewer_support import public_challenge_bytes
    preflight_path=Path(preflight_path).resolve();out=Path(out).resolve()
    if out.exists(): raise ValueError('Choose a fresh audit output directory')
    q=json.loads(preflight_path.read_bytes())
    if q.get('status')!='passed' or q.get('owner_accepted') is not False:
        raise ValueError('Expected a passing unapproved authoring preflight')
    check_binding(ROOT,q['source_binding'])
    for name,digest in q['evidence_sha256'].items():
        if sha(preflight_path.parent/name)!=digest: raise ValueError('Preflight evidence hash differs')
    source=load('_audit_source_'+HOME.name,HOME/'generator.py')
    adapter=load('_audit_adapter_'+HOME.name,HERE/'adapter.py')
    episodes=0;checks=0;failures=[];dimensions=set();orders=set();input_hashes=set();large=0
    for seed in range(seeds):
        for mode in source.MODES:
            for demos in (2,3,6):
                e=adapter.generate(seed,{'mode':mode},demos,4);episodes+=1
                violations=source.teaching_failures(e,mode);checks+=len(source.RIVALS)
                if violations:
                    failures.append({'seed':seed,'mode':mode,'demos':demos,'violations':violations,'episode':e})
                inputs=[p['input'] for split in ('train','test') for p in e[split]]
                fingerprints=[hashlib.sha256(raw(g)).hexdigest() for g in inputs]
                if len(set(fingerprints))!=len(fingerprints): raise ValueError('Duplicate episode input')
                input_hashes.update(fingerprints)
                orders.add(tuple(e['query_source_indices']))
                for g in inputs:
                    if source.self_check(g): raise ValueError('Generated scene violates grammar')
                    dimensions.add((len(g),len(g[0])))
                    if len(g)==len(g[0])==30: large+=1
    out.mkdir(parents=True)
    report={'schema':'arcpuzzles-task-authoring-audit-v1','task_id':HOME.name,
            'status':'failed' if failures else 'passed','source_binding':q['source_binding'],
            'preflight_sha256':sha(preflight_path),'finite_seeds':seeds,'episodes':episodes,
            'named_rival_checks':checks,'rivals':list(source.RIVALS),'failures':failures,
            'distinct_inputs':len(input_hashes),'input_dimensions':sorted(dimensions),
            'distinct_presentation_orders':len(orders),'large_30x30_instances':large,
            'limits':'Finite declared rivals only; not universal uniqueness, owner qualification, acceptance or training admission.'}
    write(out/'audit.json',report)
    if failures: raise ValueError(f'{len(failures)} ambiguous lessons; see audit.json')

    execution=json.loads((preflight_path.parent/'execution.json').read_bytes())
    public_rows=[];seen=set();mutations=0;positive=0
    for ei,e in enumerate(execution['episodes']):
        for qi in range(len(e['test'])):
            data=adapter.public_bytes(e,qi)
            visible=json.loads(data)
            if data!=public_challenge_bytes(visible): raise ValueError('Wrong canonical public encoding')
            if set(visible)!={'train','test'} or len(visible['test'])!=1 or set(visible['test'][0])!={'input'}:
                raise ValueError('Public field leak')
            identifier=hashlib.sha256(data).hexdigest()
            if identifier in seen: raise ValueError('Duplicate public view')
            seen.add(identifier);(out/'public').mkdir(exist_ok=True)
            (out/'public'/f'{identifier}.json').write_bytes(data)
            public_rows.append({'episode_index':ei,'query_index':qi,'source_index':e['query_source_indices'][qi],
                                'public_id':identifier})
        first=adapter.public_bytes(e,0)
        variants=[]
        v=copy.deepcopy(e);v['program_solution']='PRIVATE';v['settings']={'private':True};v['seed']=-9
        v['query_source_indices']=['private'];variants.append(v)
        v=copy.deepcopy(e)
        for p in v['test']:p['output']={'private':'not a grid'}
        variants.append(v)
        v=copy.deepcopy(e)
        for p in v['test']:p.pop('output',None)
        variants.append(v)
        v=copy.deepcopy(e);v['test'][1:]=[{'private':'invalid future'}];variants.append(v)
        v=copy.deepcopy(e);v['test']=v['test'][:1];variants.append(v)
        for v in variants:
            if adapter.public_bytes(v,0)!=first: raise ValueError('Private metadata changes visible bytes')
            mutations+=1
        v=copy.deepcopy(e);v['test'][0]['input'][0][0]=(v['test'][0]['input'][0][0]+1)%10
        if adapter.public_bytes(v,0)==first: raise ValueError('Visible-input positive control failed')
        positive+=1
    write(out/'public-projection.json',{'status':'passed','views':public_rows,'private_mutation_checks':mutations,
                                      'positive_controls':positive,'directory_is_controller_private':True})

    evaluated=0;counter=(HERE/COUNTERFACTUAL).read_text();case=None
    with _local_imports(ROOT/'shared/runtime',HERE):
        _validate_programs([{'program':adapter.program({'mode':m}),'counterfactual_program':counter} for m in source.MODES])
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for seed in (0,5,17,43):
                for mode in source.MODES:
                    e=adapter.generate(seed,{'mode':mode},6,4)
                    for split in ('train','test'):
                        for pair in e[split]:
                            actual=_grid(apply(e['program_solution'],pair['input']));evaluated+=1
                            if actual!=pair['output']:raise ValueError(f'Protected Racket parity failed: {seed} {mode} {split}')
            for e in execution['episodes']:
                if e['settings']['mode']==source.MODES[0]:continue
                for p in e['test']:
                    if len(p['input'])!=30 or len(p['input'][0])!=30:continue
                    alternate=_grid(apply(counter,p['input']));evaluated+=1
                    if alternate!=p['output']:
                        actual=_grid(apply(e['program_solution'],p['input']));evaluated+=1
                        if actual!=p['output']:raise ValueError('Witness original label differs')
                        case={'input':p['input'],'settings':e['settings'],'program':e['program_solution'],
                              'output':actual,'counterfactual_program':counter,'counterfactual_output':alternate,
                              'intermediate_value':intermediate(source,p['input']),'ablation':'wrong_intermediate'}
                        break
                if case:break
        finally:bridge.close()
    if case is None:raise ValueError('No substantive changing causal witness')
    witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':q['source_binding'],
             **DESCRIPTIONS,'racket':{'backend':'racket','protected':True},'cases':[case],
             'limits':'Authoring witness for an unregistered family; no owner qualification or acceptance.'}
    progress={'sequential_dependency':{**DESCRIPTIONS,'witness_path':'witness.json'}}
    static=validate_sequential_witness(progress,q,lambda _:raw(witness))
    replay=replay_witness(ROOT,witness,timeout=60)
    replay['status']='reviewer_replayed'
    changed=sum(a!=b for ra,rb in zip(case['output'],case['counterfactual_output']) for a,b in zip(ra,rb))
    write(out/'causal/witness.json',witness)
    write(out/'causal/replay.json',{'status':'reviewer_replayed','static_binding':static,'replay':replay,
                                  'changed_cells':changed,'preflight_sha256':sha(preflight_path),
                                  'owner_accepted':False,'training_admitted':False})
    check_binding(ROOT,q['source_binding'])
    report.update(protected_racket_evaluations=evaluated,racket=identity,
                  causal_replay_evaluations=replay['evaluations'],causal_changed_cells=changed,
                  public_views=len(public_rows),private_mutation_checks=mutations)
    write(out/'audit.json',report)
    return {k:v for k,v in report.items() if k not in ('source_binding','input_dimensions','racket')}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preflight',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--seeds',type=int,default=64);args=p.parse_args()
    if not 1<=args.seeds<=256:p.error('--seeds must be 1..256')
    print(json.dumps(verify(args.preflight,args.out,args.seeds),sort_keys=True))

if __name__=='__main__':main()
