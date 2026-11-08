"""Reusable unapproved-authoring audit: finite rivals, protected labels, public turns.

Run from the library through review.py run. This never grants owner acceptance.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME=Path(__file__).resolve().parents[2]
ROOT=HOME.parents[1]

def load_adapter():
    spec=importlib.util.spec_from_file_location('_audit_'+HOME.name,Path(__file__).with_name('adapter.py'))
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    return a

def raw(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()

def sha(value):return hashlib.sha256(value).hexdigest()

def turn_bytes(episode,index):
    from reviewer_support import public_challenge_bytes
    if type(index) is not int or not 0<=index<len(episode['test']):raise ValueError('invalid query index')
    return public_challenge_bytes({'train':episode['train'],'test':[episode['test'][index]]})

def check_binding(preflight):
    if preflight['status']!='passed' or preflight['owner_accepted'] is not False:
        raise ValueError('requires explicitly unapproved, passed authoring preflight')
    for row in preflight['source_binding']['files']:
        p=(ROOT/row['path']).resolve()
        if not p.is_relative_to(ROOT) or sha(p.read_bytes())!=row['sha256']:
            raise ValueError('stale or escaped source: '+row['path'])

def make_witness(preflight,identity,description,case):
    """Serialize the native witness schema without discarding runtime provenance."""
    if identity.get('backend')!='racket' or identity.get('protected')is not True:
        raise ValueError('a protected Racket runtime is required')
    return {'schema':'arcpuzzles-sequential-dependency-witness-v1',
            'source_binding':preflight['source_binding'],
            **{k:description[k]for k in ('step_a','intermediate','step_b','why_b_depends_on_a')},
            'racket':{'backend':'racket','protected':True},'racket_identity':identity,
            'verification_status':'authoring_preflight_not_owner_qualification','owner_accepted':False,
            'cases':[case]}

def run(preflight_path,out,seeds):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator
    from arcpuzzles.query_presentation import query_order
    if out.exists():raise ValueError('output exists; use a fresh directory')
    if not 1<=seeds<=128:raise ValueError('seeds must be 1..128')
    preflight=json.loads(preflight_path.read_text());check_binding(preflight)
    evidence=preflight_path.with_name('execution.json')
    if sha(evidence.read_bytes())!=preflight['evidence_sha256']['execution.json']:raise ValueError('execution evidence drift')
    execution=json.loads(evidence.read_text());a=load_adapter()
    report={'schema':'arcpuzzles-bounded-authoring-audit-v1','task_id':HOME.name,'status':'passed',
            'seeds':list(range(seeds)),'episodes':0,'labeled_pair_checks':0,'failures':[],
            'limits':'Finite Python-claim rival audit; protected Racket executions counted separately. No owner qualification/acceptance.'}
    distinct=set();demo_first=set();survivors={};sizes=set()
    low,high=preflight['contract']['limits']['demos']
    for seed in range(seeds):
        matched={}
        for mode in a.MODES:
            for n in range(low,high+1):
                ep=a.generate(seed,{'mode':mode},n,4);report['episodes']+=1
                audit=a.teaching_audit(ep,mode)
                if audit['query_disagreeing_survivors']:raise AssertionError((seed,mode,n,audit))
                survivors.setdefault(mode,set()).update(audit['survivors'])
                inputs=[p['input']for split in ('train','test')for p in ep[split]]
                if n in matched and matched[n]!=inputs:raise AssertionError('setting-dependent inputs')
                matched[n]=inputs
                if len({sha(raw(g))for g in inputs})!=len(inputs):raise AssertionError('duplicate inputs')
                for g in inputs:distinct.add(sha(raw(g)));sizes.add((len(g),len(g[0])))
                demo_first.add(sha(raw(ep['train'][0]['input'])))
                report['labeled_pair_checks']+=len(inputs)
    report.update(distinct_inputs=len(distinct),distinct_first_demonstrations=len(demo_first),
                  sizes=[list(x)for x in sorted(sizes)],declared_policies=a.teaching_audit(ep,mode)['policies'],
                  surviving_policies={k:sorted(v)for k,v in survivors.items()})
    out.mkdir(parents=True);pub=out/'public';pub.mkdir()
    private=[];nfiles=set();first_indices=[]
    for eidx,ep in enumerate(execution['episodes']):
        order=query_order(4,7919*ep['seed']+23);first_indices.append(order[0]);ids=[]
        for i in order:
            content=turn_bytes(ep,i);key=sha(content);(pub/(key+'.json')).write_bytes(content);nfiles.add(key);ids.append(key)
            dirty=copy.deepcopy(ep);dirty['settings']={'secret':99};dirty['program_solution']='hidden';dirty['train'][0]['secret']='hidden'
            dirty['test'][i]['output']=[[9]]
            for j in range(4):
                if j!=i:dirty['test'][j]={'input':[[9]],'output':[[9]]}
            if turn_bytes(dirty,i)!=content:raise AssertionError('private-data leak')
        private.append({'source_episode':eidx,'source_indices':order,'view_ids':ids,'settings':ep['settings']})
    write=lambda path,value:path.write_bytes(raw(value))
    write(out/'presentation.private.json',{'schema':'arcpuzzles-unapproved-authoring-presentation-v1','episodes':private,
          'note':'Controller-only manifest. Present one public file after each preceding answer. Never show this listing to the actor.'})
    # A negative public payload deliberately leaks an answer; the external checker must reject it.
    leaked=json.loads(turn_bytes(execution['episodes'][0],0));leaked['test'][0]['output']=[[1]]
    neg=out/'negative';neg.mkdir();b=raw(leaked);(neg/(sha(b)+'.json')).write_bytes(b)
    report.update(public_files=len(nfiles),first_source_query_indices=first_indices,private_invariance_checks=4*len(private))
    checks=[];count=0;witness=None
    with _local_imports(ROOT/'shared/runtime',Path(__file__).parent):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            # Independently execute all pairs of 6-demo episodes for two held seeds.
            for seed in (5,29):
                for mode in a.MODES:
                    ep=a.generate(seed,{'mode':mode},high,4)
                    for split in ('train','test'):
                        for i,p in enumerate(ep[split]):
                            actual=apply(ep['program_solution'],p['input']);count+=1
                            if actual!=p['output']:raise AssertionError(('Racket mismatch',seed,mode,split,i))
                            checks.append({'seed':seed,'mode':mode,'split':split,'index':i,'input_sha256':sha(raw(p['input'])),'output_sha256':sha(raw(actual))})
            regression=Path(__file__).with_name('regression-eight-connected.json')
            if regression.exists():
                reg=json.loads(regression.read_text());canonical=a.program({'mode':a.MODES[-1]})
                old_agree=[];query_diffs=[]
                for split in ('train','test'):
                    for pair in reg[split]:
                        actual=apply(canonical,pair['input']);rival=apply(reg['rival_program'],pair['input']);count+=2
                        if actual!=pair['output']:raise AssertionError('retained regression claim mismatch')
                        (old_agree if split=='train' else query_diffs).append(actual==rival if split=='train' else actual!=rival)
                new=a.generate(reg['seed'],{'mode':a.MODES[-1]},low,4)
                new_separates=[]
                for pair in new['train']:
                    actual=apply(canonical,pair['input']);rival=apply(reg['rival_program'],pair['input']);count+=2
                    new_separates.append(actual!=rival)
                if not all(old_agree) or not any(query_diffs) or not any(new_separates):raise AssertionError('regression did not reproduce')
                report['teaching_regression']={'seed':reg['seed'],'old_demos_all_match_rival':all(old_agree),
                    'old_query_separators':sum(query_diffs),'repaired_demo_separators':sum(new_separates),
                    'fixture_sha256':sha(regression.read_bytes()),'racket_executions':2*(len(reg['train'])+len(reg['test'])+len(new['train']))}
            cf=Path(__file__).with_name('wrong_order.rkt').read_text()
            for ep in execution['episodes']:
                if ep['settings']['mode']==a.MODES[0]:continue
                for p in ep['train']+ep['test']:
                    actual=apply(ep['program_solution'],p['input']);wrong=apply(cf,p['input']);count+=2
                    if actual!=p['output']:raise AssertionError('preflight case no longer matches')
                    if actual!=wrong:
                        # Independent replay, without reusing cached result values.
                        if apply(ep['program_solution'],p['input'])!=actual or apply(cf,p['input'])!=wrong:raise AssertionError('causal replay changed')
                        count+=2
                        description=a.sequential_description(p['input'])
                        witness=make_witness(preflight,identity,description,
                         {'input':p['input'],'settings':ep['settings'],'intermediate_value':description['value'],
                         'program':ep['program_solution'],'output':actual,'counterfactual_program':cf,'counterfactual_output':wrong,
                         'ablation':'wrong_order'})
                        break
                if witness:break
        finally:bridge.close()
    if witness is None:raise AssertionError('no causal counterexample in preflight episodes')
    check_binding(preflight)
    report.update(protected_racket_evaluations=count,protected_label_checks=len(checks),causal_replay='passed',
        causal_different_cells=sum(x!=y for r,s in zip(witness['cases'][0]['output'],witness['cases'][0]['counterfactual_output'])for x,y in zip(r,s)))
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    progress={'sequential_dependency':{**{k:witness[k]for k in ('step_a','intermediate','step_b','why_b_depends_on_a')},'witness_path':'witness.json'}}
    validate_sequential_witness(progress,preflight,lambda path:raw(witness))
    write(out/'racket-checks.json',{'racket':identity,'checks':checks,'executions_including_causal':count})
    write(out/'witness.json',witness);write(out/'audit.json',report)
    print(json.dumps({k:v for k,v in report.items()if k not in ('sizes','seeds','declared_policies','surviving_policies')},sort_keys=True))
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--seeds',type=int,default=32)
    args=p.parse_args();run(args.preflight,args.out,args.seeds)
