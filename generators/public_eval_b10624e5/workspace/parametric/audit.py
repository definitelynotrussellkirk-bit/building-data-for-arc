"""Reusable source-bound authoring audit and independent causal replay.

Run from the library via review.py run; --preflight is mandatory. No approval,
owner acceptance, universal uniqueness or training benefit is inferred here.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
HOME=BASE.parents[1]
ROOT=HOME.parents[1]


def raw(value) -> bytes:
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_adapter():
    spec=importlib.util.spec_from_file_location('_audit_'+HOME.name,BASE/'adapter.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    return a


def check_binding(preflight, *, root=None):
    root=ROOT if root is None else Path(root).resolve()
    if preflight.get('status')!='passed' or preflight.get('owner_accepted') is not False:
        raise ValueError('requires explicitly unapproved passed authoring preflight')
    for row in preflight['source_binding']['files']:
        p=root/row['path']
        if (not p.resolve().is_relative_to(root) or p.is_symlink() or not p.is_file() or
                sha(p.read_bytes())!=row['sha256']):
            raise ValueError('stale or escaped source: '+row['path'])


def make_witness(preflight,identity,description,case):
    if identity.get('backend')!='racket' or identity.get('protected') is not True:
        raise ValueError('requires protected Racket identity')
    return {'schema':'arcpuzzles-sequential-dependency-witness-v1',
            'source_binding':preflight['source_binding'],
            **{k:description[k] for k in ('step_a','intermediate','step_b','why_b_depends_on_a')},
            'racket':{'backend':'racket','protected':True},'racket_identity':identity,
            'verification_status':'authoring_preflight_not_owner_qualification',
            'owner_accepted':False,'cases':[case]}


def _evidence(preflight_path):
    preflight=json.loads(preflight_path.read_text());check_binding(preflight)
    for filename,digest in preflight['evidence_sha256'].items():
        if sha(preflight_path.with_name(filename).read_bytes())!=digest:
            raise ValueError('preflight evidence drift: '+filename)
    return preflight,json.loads(preflight_path.with_name('execution.json').read_text())


def _validate_witness(preflight,witness):
    from arcpuzzles.review_parametric_admission import validate_sequential_witness
    progress={'sequential_dependency':{**{k:witness[k] for k in ('step_a','intermediate','step_b','why_b_depends_on_a')},'witness_path':'witness.json'}}
    validate_sequential_witness(progress,preflight,lambda _:raw(witness))


def replay(preflight_path,witness_path,out):
    """Use a newly started protected bridge; never trust claimed output fields."""
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    preflight,execution=_evidence(preflight_path)
    witness=json.loads(witness_path.read_text());_validate_witness(preflight,witness)
    if out.exists():raise ValueError('replay output exists')
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for case in witness['cases']:
                if not any(ep['settings']==case['settings'] and ep['program_solution']==case['program'] and
                           any(p['input']==case['input'] and p['output']==case['output'] for sp in ('train','test') for p in ep[sp])
                           for ep in execution['episodes']):
                    raise ValueError('causal case is not an exact preflight pair')
                actual=_grid(apply(case['program'],case['input']))
                wrong=_grid(apply(case['counterfactual_program'],case['input']))
                if actual!=case['output'] or wrong!=case['counterfactual_output'] or actual==wrong:
                    raise ValueError('causal labels or output difference failed replay')
        finally:bridge.close()
    check_binding(preflight)
    report={'status':'passed','racket':identity,'cases':len(witness['cases']),
            'protected_racket_evaluations':2*len(witness['cases']),
            'witness_sha256':sha(witness_path.read_bytes()),'source_binding':preflight['source_binding'],
            'owner_accepted':False,'limits':'Final labels re-executed; intermediate interpretation remains authored.'}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(raw(report))
    print(json.dumps({'status':'passed','replayed_cases':report['cases']}))
    return report



def load_regression(path=None):
    path=BASE/'regression-fixed-source.json' if path is None else Path(path)
    content=path.read_bytes()
    if sha(content)!='308e1c99d2ad4b1a2941c92b67e04315b4c103a14d13655282998ce465835afa':
        raise ValueError('retained regression bytes changed')
    return json.loads(content)


def check_teaching_regression(apply,adapter):
    reg=load_regression();count=0;checks=[]
    for split in ('train','test'):
        for pair in reg[split]:
            actual=apply(reg['canonical_program'],pair['input'])
            wrong=apply(reg['rival_program'],pair['input']);count+=2
            if actual!=pair['output'] or (split=='train' and wrong!=actual) or (split=='test' and wrong==actual):
                raise AssertionError('retained teaching counterexample failed protected replay')
            checks.append({'split':split,'same':actual==wrong,
                           'different_cells':sum(x!=y for r,s in zip(actual,wrong) for x,y in zip(r,s))})
    repaired=adapter.generate(reg['seed'],reg['settings'],2,4)
    rejections=0
    for pair in repaired['train']:
        actual=apply(repaired['program_solution'],pair['input'])
        wrong=apply(reg['rival_program'],pair['input']);count+=2
        if actual!=pair['output']:raise AssertionError('repaired label mismatch')
        rejections+=actual!=wrong
    if not rejections:raise AssertionError('repair did not teach source selection')
    return {'status':'passed','seed':reg['seed'],'rival':reg['rival'],
             'fixture_sha256':'308e1c99d2ad4b1a2941c92b67e04315b4c103a14d13655282998ce465835afa','old_pair_checks':checks,
             'repaired_demonstration_rejections':rejections,'protected_racket_evaluations':count},count


def run(preflight_path,out,seeds):
    from arcpuzzles.parametric_worker import _local_imports,_real_evaluator,_grid
    from arcpuzzles.query_presentation import query_order
    from reviewer_support import public_challenge_bytes
    if out.exists():raise ValueError('output exists; choose a fresh directory')
    if type(seeds) is not int or not 1<=seeds<=128:raise ValueError('seeds must be 1..128')
    preflight,execution=_evidence(preflight_path);a=load_adapter()
    report={'schema':'arcpuzzles-bounded-authoring-audit-v1','task_id':HOME.name,'status':'passed',
            'seeds':list(range(seeds)),'episodes':0,'pair_exposures':0,'failures':[],
            'limits':'Finite Python-claim rivals, nested teaching prefixes and reused matched input streams. Protected executions counted separately. No owner acceptance or training admission.'}
    distinct=set();first_demos=set();surviving={};sizes=set()
    low,high=preflight['contract']['limits']['demos']
    for seed in range(seeds):
        matched={}
        for mode in a.MODES:
            full=a.generate(seed,{a.PARAMETER:mode},high,4)
            for n in range(low,high+1):
                ep=a.generate(seed,{a.PARAMETER:mode},n,4)
                if ep['train']!=full['train'][:n] or ep['test']!=full['test']:
                    raise AssertionError('demo count changes the query bank/prefix')
                audit=a.teaching_audit(ep,mode)
                if audit['query_disagreeing_survivors']:
                    raise AssertionError(('query-changing rival',seed,mode,n,audit))
                surviving.setdefault(mode,set()).update(audit['survivors'])
                inputs=[p['input'] for sp in ('train','test') for p in ep[sp]]
                if n in matched and matched[n]!=inputs:raise AssertionError('settings change inputs')
                matched[n]=inputs
                ids=[sha(raw(_grid(g))) for g in inputs]
                if len(ids)!=len(set(ids)):raise AssertionError('duplicate input within lesson')
                distinct.update(ids);first_demos.add(ids[0]);sizes.update((len(g),len(g[0])) for g in inputs)
                report['episodes']+=1;report['pair_exposures']+=len(inputs)
            for q in range(1,5):
                prefix=a.generate(seed,{a.PARAMETER:mode},low,q)
                if prefix['test']!=full['test'][:q]:raise AssertionError('query count changes prefix')
    report.update(distinct_inputs=len(distinct),distinct_first_demonstrations=len(first_demos),
                  sizes=[list(x) for x in sorted(sizes)],declared_policies=audit['policies'],
                  surviving_policies={m:sorted(s) for m,s in surviving.items()})
    out.mkdir(parents=True);pub=out/'public';pub.mkdir()
    view_ids=set();private=[];invariance=0;positive_controls=0
    for eidx,ep in enumerate(execution['episodes']):
        order=query_order(4,ep['seed']*7919+23);ids=[]
        for index in order:
            data=public_challenge_bytes(a.public_view(ep,index));digest=sha(data)
            if digest in view_ids:raise AssertionError('duplicate public view')
            view_ids.add(digest);ids.append(digest)
            (pub/(digest+'.json')).write_bytes(data)
            changed=copy.deepcopy(ep);changed['settings']={'secret':99};changed['seed']=-1
            changed['program_solution']='private';changed['train'][0]['hidden']='secret'
            changed['test'][index]['output']=[[9]];changed['test'][index]['hidden']='secret'
            for j in range(4):
                if j!=index:changed['test'][j]={'input':[[9]],'output':[[9]],'hidden':'secret'}
            if public_challenge_bytes(a.public_view(changed,index))!=data:raise AssertionError('private-field leak')
            invariance+=1
            changed=copy.deepcopy(ep)
            changed['test'][index]['input'][0][0]=(changed['test'][index]['input'][0][0]+1)%10
            if public_challenge_bytes(a.public_view(changed,index))==data:raise AssertionError('visible-change control failed')
            positive_controls+=1
        private.append({'source_episode':eidx,'source_indices':order,'view_ids':ids,'settings':ep['settings']})
    order_first=[query_order(4,s)[0] for s in range(128)]
    if set(order_first)!={0,1,2,3}:raise AssertionError('first-query order does not vary')
    (out/'presentation.private.json').write_bytes(raw({'schema':'arcpuzzles-unapproved-authoring-presentation-v1',
        'episodes':private,'note':'Controller only. Reveal one selected public file per turn; never expose listing, count, answers or future inputs.'}))
    report.update(public_files=len(view_ids),private_invariance_checks=invariance,
                  visible_change_positive_controls=positive_controls,
                  first_query_source_index_counts={str(i):order_first.count(i) for i in range(4)})
    labels=[];count=0
    with _local_imports(ROOT/'shared/runtime',BASE):
        apply,identity,bridge=_real_evaluator(ROOT/'shared/runtime')
        try:
            for seed in (5,29):
                for mode in a.MODES:
                    ep=a.generate(seed,{a.PARAMETER:mode},high,4)
                    for split in ('train','test'):
                        for i,p in enumerate(ep[split]):
                            actual=_grid(apply(ep['program_solution'],p['input']));count+=1
                            if actual!=p['output']:raise AssertionError(('Racket label mismatch',seed,mode,split,i))
                            labels.append({'seed':seed,'settings':ep['settings'],'split':split,'index':i,
                                           'input_sha256':sha(raw(p['input'])),'output_sha256':sha(raw(actual))})
            regression,extra=check_teaching_regression(apply,a);count+=extra
            report['teaching_regression']=regression
            (out/'teaching-regression.json').write_bytes(raw(regression))
            ep=next(ep for ep in execution['episodes'] if ep['settings'][a.PARAMETER]==a.MODES[-1])
            pair=ep['test'][3];cf=(BASE/'wrong_intermediate.rkt').read_text()
            actual=_grid(apply(ep['program_solution'],pair['input']))
            wrong=_grid(apply(cf,pair['input']));count+=2
            if actual!=pair['output'] or actual==wrong:raise AssertionError('causal intervention failed')
            description=a.sequential_description(pair['input'])
            witness=make_witness(preflight,identity,description,
                {'input':pair['input'],'settings':ep['settings'],'intermediate_value':description['value'],
                 'program':ep['program_solution'],'output':actual,'counterfactual_program':cf,
                 'counterfactual_output':wrong,'ablation':'wrong_intermediate'})
        finally:bridge.close()
    _validate_witness(preflight,witness);check_binding(preflight)
    (out/'witness.json').write_bytes(raw(witness))
    # Independent bridge and exact-pair membership check, not cached result reuse.
    replay(preflight_path,out/'witness.json',out/'causal-replay.json');count+=2
    report.update(protected_racket_evaluations=count,protected_label_checks=len(labels),causal_replay='passed',
                  causal_changed_cells=sum(x!=y for r,s in zip(actual,wrong) for x,y in zip(r,s)),
                  source_binding=preflight['source_binding'])
    (out/'racket-checks.json').write_bytes(raw({'racket':identity,'checks':labels,'executions_including_causal':count}))
    (out/'audit.json').write_bytes(raw(report))
    print(json.dumps({k:v for k,v in report.items() if k not in ('seeds','source_binding','sizes','declared_policies','surviving_policies')},sort_keys=True))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight',required=True,type=Path);parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--seeds',type=int,default=64);parser.add_argument('--witness',type=Path,help='Replay this witness only, in a new bridge.')
    args=parser.parse_args()
    if args.witness:replay(args.preflight,args.witness,args.out)
    else:run(args.preflight,args.out,args.seeds)
