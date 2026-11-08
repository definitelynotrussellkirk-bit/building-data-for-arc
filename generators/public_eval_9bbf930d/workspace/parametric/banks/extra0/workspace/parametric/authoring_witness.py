"""Build a source-bound causal witness from PUBLIC-CREATION PREFLIGHT only.

This complements, rather than bypasses, the native qualification witness tool.
The general parser, protected evaluator, structural validator and independent
replay come from the local repository. No owner approval is created or implied.
Use --preflight, --recipe and a fresh --out directory through review.py run.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys

ROOT=Path(__file__).resolve().parents[4]
for path in (ROOT/'src',ROOT/'shared/runtime'):
    if str(path) not in sys.path: sys.path.insert(0,str(path))
FIELDS=('step_a','intermediate','step_b','why_b_depends_on_a')
LIMITS=('Protected finite counterfactual execution and a second-process replay only. '
        'Intermediate interpretation is author-supplied. Authoring preflight is not native '
        'qualification, owner acceptance, universal depth proof, or training admission.')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked_preflight(root, path):
    from arcpuzzles.review_public_creation import PREFLIGHT
    root=Path(root).resolve(); path=Path(path).resolve()
    receipt=json.loads(path.read_bytes())
    if (receipt.get('schema')!=PREFLIGHT or receipt.get('status')!='passed' or
        receipt.get('verification_status')!='authoring_preflight_not_owner_qualification' or
        receipt.get('owner_accepted') is not False):
        raise ValueError('Expected an explicitly unaccepted authoring preflight')
    task=receipt.get('task_id','')
    if not isinstance(task,str) or not task.startswith('public_eval_') or '/' in task or '..' in task:
        raise ValueError('Invalid public task identity')
    home=root/'generators'/task
    binding=receipt.get('source_binding',{})
    if binding.get('task_id')!=task or not binding.get('files'):
        raise ValueError('Source binding missing or has wrong task')
    seen=set()
    for row in binding['files']:
        name=row['path']; relative=PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or name in seen:
            raise ValueError('Source binding has unsafe or duplicate path')
        source=root/name
        if (not source.is_file() or source.is_symlink() or source.resolve()!=source or
                sha(source)!=row.get('sha256')):
            raise ValueError('Source drift: '+name)
        seen.add(name)
    expected={p.relative_to(root).as_posix() for p in home.rglob('*')
              if p.is_file() and '__pycache__' not in p.parts and
              (p.suffix in {'.py','.rkt'} or p.name in {'promotion.json','public-parent.json'})}
    expected.add('shared/tools/comment_solutions.py')
    expected.update(p.relative_to(root).as_posix() for p in (root/'shared/runtime').rglob('*')
                    if p.is_file() and p.suffix in {'.py','.rkt'} and '__pycache__' not in p.parts)
    if seen!=expected:
        raise ValueError('Source binding is not the complete current preflight closure')
    for name in ('execution.json','original-pairs.json'):
        if sha(path.with_name(name))!=receipt['evidence_sha256'].get(name):
            raise ValueError('Preflight execution/original-label evidence changed')
    execution=json.loads(path.with_name('execution.json').read_bytes())
    originals=json.loads(path.with_name('original-pairs.json').read_bytes())
    if originals.get('status')!='passed' or not originals.get('pairs'):
        raise ValueError('Original labelled pairs have not passed')
    if execution.get('racket',{}).get('backend')!='racket' or execution.get('racket',{}).get('protected') is not True:
        raise ValueError('Preflight must record protected Racket execution')
    for episode in execution['episodes']:
        key=json.dumps(episode['settings'],sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
        if hashlib.sha256(episode['program_solution'].encode()).hexdigest()!=receipt['programs'].get(key):
            raise ValueError('Preflight episode program is not bound to its setting')
    return receipt,execution


def build(root, preflight_path, recipe, output, *, timeout=30):
    from arcpuzzles.review_witness import _execute
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    from arcpuzzles.review_sequential_replay import replay_witness
    root=Path(root).resolve(); output=Path(output)
    if output.exists() or output.is_symlink(): raise ValueError('Choose a fresh output directory')
    q,execution=checked_preflight(root,preflight_path)
    before=sha(preflight_path)
    if any(type(recipe.get(k)) is not str or not recipe[k].strip() for k in FIELDS):
        raise ValueError('Supply all four dependency descriptions')
    rows=recipe.get('cases')
    if type(rows) is not list or not 1<=len(rows)<=16:
        raise ValueError('Select 1..16 bounded preflight cases')
    cases=[]
    for row in rows:
        i,j,split=row.get('episode_index'),row.get('pair_index'),row.get('split')
        if type(i) is not int or not 0<=i<len(execution['episodes']): raise ValueError('Invalid episode index')
        episode=execution['episodes'][i]
        if split not in ('train','test') or type(j) is not int or not 0<=j<len(episode[split]):
            raise ValueError('Invalid split/pair index')
        if row.get('ablation') not in ('wrong_order','wrong_intermediate','skip_a') or row.get('intermediate_value') is None:
            raise ValueError('Supply intermediate value and a named ablation')
        pair=episode[split][j]
        cases.append({'input':copy.deepcopy(pair['input']),'output':copy.deepcopy(pair['output']),
            'settings':copy.deepcopy(episode['settings']),'program':episode['program_solution'],
            'counterfactual_program':row.get('counterfactual_program'),
            'intermediate_value':copy.deepcopy(row['intermediate_value']),'ablation':row['ablation'],
            'preflight_case':{'episode_index':i,'split':split,'pair_index':j}})
    constructed=_execute(root,cases,timeout)
    witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':q['source_binding'],
             **{k:recipe[k] for k in FIELDS},'racket':{'backend':'racket','protected':True},
             'cases':constructed['cases'],'limits':LIMITS}
    raw=(json.dumps(witness,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    structural=validate_sequential_witness(
        {'sequential_dependency':{**{k:recipe[k] for k in FIELDS},'witness_path':'witness.json'}},q,lambda _:raw)
    replay=replay_witness(root,witness,timeout=timeout)
    # The shared evaluator is also used by owners; this invocation is reviewer work.
    replay['status']='reviewer_replayed'
    if checked_preflight(root,preflight_path)[0]!=q or sha(preflight_path)!=before:
        raise ValueError('Source or preflight changed during causal replay')
    result={'schema':'arcpuzzles-public-authoring-witness-check-v1','status':'reviewer_replayed',
        'task_id':q['task_id'],'source_binding':q['source_binding'],'preflight_sha256':before,
        'witness_sha256':hashlib.sha256(raw).hexdigest(),'verification_status':q['verification_status'],
        'construction':{'racket':constructed['racket'],'evaluations':constructed['evaluations']},
        'structural_validation':structural,'replay':replay,
        'owner_accepted':False,'training_admitted':False,'limits':LIMITS}
    output.mkdir(parents=True,exist_ok=False)
    (output/'witness.json').write_bytes(raw)
    (output/'replay.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight',type=Path,required=True)
    parser.add_argument('--recipe',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--timeout',type=float,default=30)
    args=parser.parse_args()
    result=build(ROOT,args.preflight,json.loads(args.recipe.read_text()),args.out,timeout=args.timeout)
    print(json.dumps({k:result[k] for k in ('status','task_id','verification_status','owner_accepted','training_admitted')}))


if __name__=='__main__': main()
