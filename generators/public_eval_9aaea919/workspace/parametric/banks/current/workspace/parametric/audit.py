"""Reusable protected-label, finite-shortcut and sequential-public audit.

Run through review.py run. Source programs/answers and the export directory
listing remain controller-private. A bounded rival check is not rule uniqueness.
"""
from pathlib import Path
from copy import deepcopy
import argparse, hashlib, importlib.util, json, random, sys


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def run(preflight,out,seeds=(0,1,17,43,97,999)):
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes,public_challenge_id
    base=Path(__file__).resolve().parent;root=base.parents[3]
    spec=importlib.util.spec_from_file_location('_audited_'+hashlib.sha256(str(base).encode()).hexdigest(),base/'adapter.py')
    adapter=importlib.util.module_from_spec(spec);sys.modules[spec.name]=adapter;spec.loader.exec_module(adapter)
    receipt=json.loads(preflight.read_text());binding=receipt['source_binding']
    for row in binding['files']:
        if hashlib.sha256((root/row['path']).read_bytes()).hexdigest()!=row['sha256']:
            raise ValueError('preflight source drift: '+row['path'])
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True)
    apply,identity,bridge=_real_evaluator(root/'shared/runtime')
    cache={};nexecutions=0;findings=[];episodes=labels=rival_checks=0;visible={};private=[]
    def execute(program,grid):
        nonlocal nexecutions
        key=hashlib.sha256((program+json.dumps(grid)).encode()).hexdigest()
        if key not in cache: cache[key]=apply(program,grid);nexecutions+=1
        return cache[key]
    try:
        for seed in seeds:
            for policy in adapter.family.POLICIES:
                setting={adapter.PARAMETER:policy}
                for demos in (2,3,6):
                    e=adapter.generate(seed,setting,demos,4);episodes+=1
                    for split in ('train','test'):
                        for pair in e[split]:
                            labels+=1
                            if seed in (0,17,43):
                                if execute(e['program_solution'],pair['input'])!=pair['output']:
                                    findings.append({'kind':'racket_parity','seed':seed,'policy':policy,'split':split})
                            if adapter.family.self_check(pair['input']):findings.append({'kind':'input_grammar','seed':seed,'policy':policy})
                    for name in adapter.family.RIVALS:
                        rival_checks+=1
                        fits=all(adapter.family.rival(p['input'],policy,name)==p['output'] for p in e['train'])
                        if fits and any(adapter.family.rival(p['input'],policy,name)!=p['output'] for p in e['test']):
                            findings.append({'kind':'harmful_rival','seed':seed,'policy':policy,'rival':name,'demos':demos})
                    if seed in (17,43) and demos==2:
                        presentation_seed=101+seed
                        views=adapter.public_views(e,presentation_seed)
                        changed=deepcopy(e);changed['program_solution']='secret';changed['seed']='secret';changed['settings']='secret'
                        for pair in changed['test']:pair['output']=[[9]]
                        if adapter.public_views(changed,presentation_seed)!=views:findings.append({'kind':'private_field_leak'})
                        ids=[];order=list(range(4));random.Random(presentation_seed).shuffle(order)
                        for view in views:
                            data=public_challenge_bytes(view);vid=public_challenge_id(view)
                            if vid in visible:raise ValueError('duplicate visible challenge')
                            visible[vid]=data;ids.append(vid)
                        private.append({'seed':seed,'settings':setting,'presentation_seed':presentation_seed,
                                        'source_indices':order,'view_ids':ids,'answers':[e['test'][i]['output'] for i in order]})
        case=adapter.causal_case()
        fields=('step_a','intermediate','step_b','why_b_depends_on_a')
        descriptions={k:case.pop(k) for k in fields}
        case['output']=execute(case['program'],case['input'])
        case['counterfactual_output']=execute(case['counterfactual_program'],case['input'])
        if case['output']==case['counterfactual_output']:findings.append({'kind':'causal_no_change'})
        witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','task_id':binding['task_id'],
                 'source_binding':binding,**descriptions,'racket':{'backend':'racket','protected':True},
                 'execution_runtime':identity,'cases':[case],
                 'verification_status':'reviewer_replayed_authoring_preflight','owner_accepted':False}
        write(out/'causal.json',witness)
        (out/'public').mkdir()
        for vid,data in sorted(visible.items()): (out/'public'/f'{vid}.json').write_bytes(data)
        write(out/'private-presentation.json',{'controller_only':True,'source_binding':binding,'episodes':private})
        report={'status':'passed' if not findings else 'failed','source_binding':binding,'racket':identity,
                'seeds':list(seeds),'demo_counts':[2,3,6],'episodes':episodes,'label_claims':labels,
                'protected_evaluations':nexecutions,'rivals':list(adapter.family.RIVALS),'rival_checks':rival_checks,
                'public_views':len(visible),'findings':findings,
                'limits':'Finite named-rival checks and sampled exact labels, not universal uniqueness, owner acceptance, or training admission.'}
        write(out/'report.json',report)
        print(json.dumps({k:v for k,v in report.items() if k not in ('source_binding','racket','rivals')},sort_keys=True))
        if findings:raise AssertionError(findings)
    finally:bridge.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();run(a.preflight.resolve(),a.out.resolve())
