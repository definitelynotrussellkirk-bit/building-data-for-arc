"""Reusable bounded audit for this unapproved public-evaluation family.

Run through ``review.py run``. It checks deterministic count prefixes, matched
setting-neutral inputs, finite declared rivals, protected-Racket labels, strict
single-query public projection, private/future-query invariance, and creates a
source-bound causal case for the shared witness builder. Passing is authoring
evidence only: it is not owner qualification, acceptance, or universal rule
uniqueness.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
ROOT=BASE.parents[3]
TASK=HOME.name
for path in (ROOT/'src',ROOT/'shared/runtime'):
    if str(path) not in sys.path:sys.path.insert(0,str(path))


def load_adapter():
    path=BASE/'adapter.py'
    name='_bounded_audit_'+TASK+'_'+hashlib.sha256(str(path).encode()).hexdigest()
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def source_hashes():
    allowed=[]
    for p in HOME.rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        if p.suffix in {'.py','.rkt'} or p.name in {'promotion.json','public-parent.json'}:
            allowed.append(p)
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(allowed)}


def changed_cells(a,b):
    h=max(len(a),len(b));w=max(max(map(len,a),default=0),max(map(len,b),default=0))
    return sum((a[r][c] if r<len(a) and c<len(a[r]) else None) !=
               (b[r][c] if r<len(b) and c<len(b[r]) else None)
               for r in range(h) for c in range(w))


def audit(destination,seeds):
    from reviewer_support import public_challenge_bytes
    from arcpuzzles.parametric_worker import _grid,_local_imports,_real_evaluator
    destination=Path(destination)
    if destination.exists():raise FileExistsError('Choose a fresh audit directory')
    if type(seeds) is not int or not 1<=seeds<=256:raise ValueError('seeds must be 1..256')
    before=source_hashes();a=load_adapter();settings=[{a.PARAMETER:v} for v in a.VALUES]
    prefix_checks=0;episodes=0;rival_checks=0;public_checks=0;stress=[];findings=[]
    first_indices=set();records=[];racket_evaluations=0;audited_case=None
    # Broad deterministic Python audit: the full family surface, not just preflight seeds.
    for seed in [*range(seeds),2**63-1]:
        matched=None
        for setting in settings:
            full=a.generate(seed,setting,6,4)
            inputs=[p['input'] for split in ('train','test') for p in full[split]]
            if matched is not None and inputs!=matched:
                findings.append({'kind':'setting_dependent_inputs','seed':seed,'settings':setting})
            matched=inputs
            if len({json.dumps(g,separators=(',',':')) for g in inputs})!=10:
                findings.append({'kind':'duplicate_inputs','seed':seed,'settings':setting})
            for demos in range(2,7):
                for queries in range(1,5):
                    part=a.generate(seed,setting,demos,queries)
                    if part['train']!=full['train'][:demos] or part['test']!=full['test'][:queries]:
                        findings.append({'kind':'count_prefix_instability','seed':seed,'settings':setting,
                                         'demos':demos,'queries':queries})
                    prefix_checks+=1
            survivors=a.survivors(full['train'][:2],setting)
            rival_checks+=len(a.RIVALS)
            if survivors!=['intended']:
                findings.append({'kind':'teaching_survivors','seed':seed,'settings':setting,'survivors':survivors})
            one=a.public_turns(seed,setting,2,19,1)
            all_turns=a.public_turns(seed,setting,2,19,4)
            if one!=all_turns[:1]:
                findings.append({'kind':'first_turn_instability','seed':seed,'settings':setting})
            source_index=next(i for i,p in enumerate(full['test']) if p['input']==one[0]['test'][0]['input'])
            first_indices.add(source_index)
            for qi in range(4):
                view=a.public_view(full,qi);raw=public_challenge_bytes(view)
                mutated=copy.deepcopy(full);mutated['program_solution']='PRIVATE';mutated['settings']={'PRIVATE':True}
                for j,p in enumerate(mutated['test']):
                    p['output']=[[9]]
                    if j!=qi:p['input']=[[8]]
                if public_challenge_bytes(a.public_view(mutated,qi))!=raw:
                    findings.append({'kind':'private_or_future_query_leak','seed':seed,'settings':setting,'query':qi})
                if set(view)!= {'train','test'} or len(view['test'])!=1 or set(view['test'][0])!={'input'}:
                    findings.append({'kind':'public_schema','seed':seed,'settings':setting,'query':qi})
                public_checks+=1
            q=full['test'][3]
            stress.append({'seed':seed,'settings':setting,'input_shape':[len(q['input']),len(q['input'][0])],
                           'output_shape':[len(q['output']),len(q['output'][0])],
                           'input_nonzero':sum(v!=0 for row in q['input'] for v in row),
                           'changed_cells':changed_cells(q['input'],q['output'])})
            episodes+=1
    if len(first_indices)<2:
        findings.append({'kind':'presentation_order_not_varied','first_indices':sorted(first_indices)})

    # Protected-Racket parity for count boundaries and two independent seeds.
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for seed in (0,17):
                for setting in settings:
                    for demos in (2,6):
                        episode=a.generate(seed,setting,demos,4)
                        for split in ('train','test'):
                            for pair in episode[split]:
                                actual=_grid(apply(episode['program_solution'],pair['input']));racket_evaluations+=1
                                if actual!=pair['output']:
                                    findings.append({'kind':'protected_racket_label_mismatch','seed':seed,
                                                     'settings':setting,'demos':demos,'split':split})
                        if demos==2:records.append((seed,copy.deepcopy(setting),episode))
            # Find a real generated pair whose authored counterfactual changes the final label.
            for seed,setting,episode in records:
                for split in ('train','test'):
                    for pair_index,pair in enumerate(episode[split]):
                        counter=a.counterfactual_program(setting)
                        alternative=_grid(apply(counter,pair['input']));racket_evaluations+=1
                        if alternative!=pair['output']:
                            audited_case={'settings':setting,'program':episode['program_solution'],
                                'input':pair['input'],'output':pair['output'],
                                'counterfactual_program':counter,
                                'intermediate_value':a.intermediate(pair['input'],setting),
                                'ablation':'wrong_intermediate','split':split,'pair_index':pair_index,
                                'seed':seed,'changed_cells':changed_cells(pair['output'],alternative)}
                            break
                    if audited_case:break
                if audited_case:break
        finally:bridge.close()
    if not audited_case:findings.append({'kind':'counterfactual_has_no_effect'})

    # Materialize a guarded controller-private export from four audited episodes.
    blobs={};private=[]
    for seed,setting,episode in records:
        ids=[];indices=[]
        order=a.presentation_order(seed^11)
        for qi in order:
            view=a.public_view(episode,qi);raw=public_challenge_bytes(view)
            identifier=hashlib.sha256(raw).hexdigest()
            if identifier in blobs:findings.append({'kind':'duplicate_public_visible_payload','id':identifier})
            blobs[identifier]=raw;ids.append(identifier);indices.append(qi)
        private.append({'seed':seed,'settings':setting,'presentation_seed':11,
                        'view_ids':ids,'source_indices':indices,
                        'answers':[episode['test'][i]['output'] for i in indices]})
    preview=destination/'preview';(preview/'public').mkdir(parents=True)
    for identifier in sorted(blobs):(preview/'public'/f'{identifier}.json').write_bytes(blobs[identifier])
    write(preview/'private.json',{'controller_only':True,'episodes':private,
          'warning':'Never expose this file, settings, answers, source indices, or directory listing.'})
    export={'schema':'public-eval-authoring-sequential-export-v1','status':'passed' if not findings else 'failed',
            'task_id':TASK,'files_written':len(blobs),'view_ids':sorted(blobs),
            'queries_per_public_file':1,'public_order':'visible-byte-sha256',
            'private_field_invariance':True,'future_query_invariance':True,
            'owner_accepted':False,'training_admitted':False}
    write(preview/'manifest.json',export)
    if audited_case:write(destination/'audited-case.json',audited_case)
    after=source_hashes()
    if after!=before:findings.append({'kind':'source_changed_during_audit'})
    report={'schema':'public-eval-family-bounded-audit-v1','status':'passed' if not findings else 'failed',
            'task_id':TASK,'seed_values':[0,seeds-1,2**63-1],'python_episode_count':episodes,
            'count_prefix_checks':prefix_checks,'finite_rival_checks':rival_checks,
            'public_projection_checks':public_checks,'protected_racket_evaluations':racket_evaluations,
            'racket':identity,'presentation_first_indices':sorted(first_indices),
            'preview_public_files':len(blobs),'stress_queries':stress,'finite_rivals':list(a.RIVALS),
            'causal_case_changed_cells':audited_case['changed_cells'] if audited_case else 0,
            'source_sha256':before,'findings':findings,'owner_accepted':False,'training_admitted':False,
            'limits':'Finite named rivals and sampled seeds only; no universal uniqueness, owner qualification, acceptance, or training admission.'}
    destination.mkdir(parents=True,exist_ok=True);write(destination/'audit.json',report)
    if findings:raise ValueError(f'{len(findings)} audit findings; see {destination}/audit.json')
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,default=32);args=p.parse_args()
    result=audit(args.out,args.seeds)
    print(json.dumps({k:result[k] for k in ('status','python_episode_count','count_prefix_checks',
          'finite_rival_checks','public_projection_checks','protected_racket_evaluations',
          'preview_public_files','causal_case_changed_cells')},sort_keys=True))

if __name__=='__main__':main()
