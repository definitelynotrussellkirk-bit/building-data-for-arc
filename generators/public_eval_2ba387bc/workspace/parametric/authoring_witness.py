"""Replay unapproved authoring witnesses without impersonating native acceptance.

Checks the complete current preflight source closure and original/execution hashes.
Runs the shipped protected constructor and an independent protected replay process.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;HOME=HERE.parents[1];ROOT=HOME.parents[1]
_spec=importlib.util.spec_from_file_location('_2ba387bc_witness_adapter',HERE/'adapter.py')
adapter=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=adapter;_spec.loader.exec_module(adapter)
FIELDS={
 'step_a':'Extract same-size square components, classify each as a frame or solid, then independently order the two classes by the selected spatial axis.',
 'intermediate':'Two ordered lists of input block crops: frames and solids, with their top-left positions and colors.',
 'step_b':'Use those lists to size the output and place frames on the left and solids on the right, padding the shorter class with background.',
 'why_b_depends_on_a':'Class membership determines the output column; measured list lengths determine output height; input-derived within-class ranks determine row slots.'}

def _sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def _closure(root,home):
    paths=[p for p in home.rglob('*') if p.is_file() and (p.suffix in ('.py','.rkt') or p.name in ('promotion.json','public-parent.json')) and '__pycache__' not in p.parts]
    paths.append(root/'shared/tools/comment_solutions.py')
    paths.extend(p for p in (root/'shared/runtime').rglob('*') if p.is_file() and p.suffix in ('.py','.rkt') and '__pycache__' not in p.parts)
    return {p.relative_to(root).as_posix() for p in paths}

def verify_preflight(root, path):
    root=Path(root).resolve();path=Path(path).resolve();q=json.loads(path.read_text())
    if q.get('schema')!='arcpuzzles-public-eval-authoring-preflight-v1' or q.get('status')!='passed' or q.get('owner_accepted') is not False or q.get('verification_status')!='authoring_preflight_not_owner_qualification' or q.get('task_id')!=HOME.name:
        raise ValueError('expected this task\'s unapproved authoring preflight, not an acceptance flag')
    for name in ('execution.json','original-pairs.json'):
        p=path.with_name(name)
        if p.is_symlink() or not p.is_file() or _sha(p)!=q.get('evidence_sha256',{}).get(name):
            raise ValueError('preflight execution/original evidence drift')
    binding=q.get('source_binding',{})
    rows=binding.get('files',[])
    if binding.get('task_id')!=HOME.name or not rows:
        raise ValueError('missing source binding')
    names=[r.get('path') for r in rows]
    if len(names)!=len(set(names)) or set(names)!=_closure(root,root/'generators'/HOME.name):
        raise ValueError('preflight source closure differs from current source')
    for row in rows:
        p=root/row['path']
        if '..' in Path(row['path']).parts or Path(row['path']).is_absolute() or p.is_symlink() or not p.resolve().is_relative_to(root) or any(a.is_symlink() for a in p.parents if a.is_relative_to(root)) or not p.is_file() or _sha(p)!=row['sha256']:
            raise ValueError('source changed or unsafe path: '+str(row['path']))
    return q,json.loads(path.with_name('execution.json').read_text())

def build(preflight, output):
    from arcpuzzles.review_witness import _execute
    from arcpuzzles.review_sequential_replay import replay_witness
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from reviewer_support import public_challenge_bytes
    preflight=Path(preflight).resolve();output=Path(output)
    if output.exists():raise FileExistsError('choose fresh output after any source changes')
    q,execution=verify_preflight(ROOT,preflight)
    e=next(e for e in execution['episodes'] if e['settings']=={'order_axis':'column'})
    p=e['train'][0];state=adapter.model.infer(p['input'])
    program=e['program_solution']
    cf=program.replace('(list frames solids)','(list solids frames)')
    if cf==program:raise ValueError('counterfactual anchor drift')
    buckets=adapter.model.ordered_buckets(state,'column')
    values=[[{k:b[k] for k in ('kind','row','column','color','size')} for b in bucket] for bucket in buckets]
    case=dict(input=p['input'],output=p['output'],settings=e['settings'],program=program,
        intermediate_value=values,counterfactual_program=cf,ablation='wrong_intermediate')
    constructed=_execute(ROOT,[case],30)
    witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':HOME.name,
        'source_binding':q['source_binding'],'racket':{'backend':'racket','protected':True},**FIELDS,
        'cases':constructed['cases'],'verification_status':'unapproved_authoring_preflight',
        'owner_accepted':False,'training_admitted':False}
    payload=(json.dumps(witness,sort_keys=True,indent=2)+'\n').encode()
    validate_sequential_witness({'sequential_dependency':{**FIELDS,'witness_path':'witness.json'}},q,lambda _:payload)
    replay=replay_witness(ROOT,witness,timeout=30)
    replay={**replay,'status':'reviewer_replayed','owner_acceptance':'not_performed','training_admitted':False}
    if verify_preflight(ROOT,preflight)[0]!=q:raise ValueError('source or preflight changed during replay')
    output.mkdir(parents=True);(output/'witness.json').write_bytes(payload)
    record={'schema':'arcpuzzles-public-authoring-witness-check-v1','status':'reviewer_replayed',
        'task_id':HOME.name,'preflight_sha256':_sha(preflight),'source_binding':q['source_binding'],
        'witness_sha256':hashlib.sha256(payload).hexdigest(),'construction':constructed,'replay':replay,
        'owner_accepted':False,'training_admitted':False}
    (output/'replay.json').write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
    public_dir=output.parent/'public';public_dir.mkdir(exist_ok=False);names=[]
    for episode in execution['episodes']:
        for i in range(4):
            raw=public_challenge_bytes(adapter.public_view(episode,i));name=hashlib.sha256(raw).hexdigest()+'.json'
            if (public_dir/name).exists():raise ValueError('duplicate public ID')
            names.append((name,raw))
    for name,raw in sorted(names):(public_dir/name).write_bytes(raw)
    return {'status':'reviewer_replayed','cases':len(witness['cases']),'public_views':len(names),
        'source_files':len(q['source_binding']['files']),'owner_accepted':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.preflight,a.out),sort_keys=True))
if __name__=='__main__':main()
