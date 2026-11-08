"""Source-bound authoring audit, public export negatives and protected causal replay.

Run after public-creation preflight. This is reviewer evidence, NOT qualification
or owner acceptance. It refuses existing output directories and stale bindings.
The same task-local tool is portable between native families exposing the adapter
API (program/generate/predict/rivals/public_turn/causal_metadata/DEPENDENCY).
"""
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def verify_binding(root,receipt):
    root=Path(root).resolve()
    if receipt.get('status')!='passed':raise ValueError('passing authoring preflight required')
    rows=receipt.get('source_binding',{}).get('files',[])
    if not rows:raise ValueError('empty source binding')
    for row in rows:
        p=root/row['path']
        if not p.is_file() or p.is_symlink() or not p.resolve().is_relative_to(root) or sha(p.read_bytes())!=row['sha256']:
            raise ValueError('stale or invalid source binding: '+row['path'])

def differences(a,b):
    overlap=sum(x!=y for ra,rb in zip(a,b) for x,y in zip(ra,rb))
    shared=sum(min(len(ra),len(rb)) for ra,rb in zip(a,b))
    extra=sum(map(len,a))+sum(map(len,b))-2*shared
    return {'overlap_changed':overlap,'shape_extra_cells':extra,'changed_cells':overlap+extra}

def run(preflight,out,seeds=32):
    if type(seeds) is not int or not 1<=seeds<=256:raise ValueError('seed count outside 1..256')
    root=next(p for p in HERE.parents if (p/'src/arcpuzzles/parametric_worker.py').is_file())
    receipt=json.loads(Path(preflight).read_text());verify_binding(root,receipt)
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    a=load(HERE/'adapter.py','_audit_adapter_'+HERE.parent.parent.name)
    io=load(HERE/'public_io.py','_audit_public_io')
    sys.path[:0]=[str(root/'src'),str(root/'shared/runtime')]
    from reviewer_support import public_challenge_bytes
    from arcpuzzles.parametric_worker import _real_evaluator
    from arcpuzzles.review_witness import _validate_programs
    from arcpuzzles.review_sequential_replay import replay_witness
    key=next(iter(a.PARAMETERS));modes=a.PARAMETERS[key]
    report={'status':'passed','source_binding':receipt['source_binding'],'seeds':seeds,'episodes':0,'rival_checks':0,
            'distinct_inputs':0,'input_shapes':[],'matched_settings_checks':0,'boundary_count_checks':0,
            'privacy_checks':0,'positive_controls':0,'negative_exports_rejected':0,'public_files':0,
            'racket_evaluations':0,'failures':[],
            'limits':'Bounded authored hypotheses/seeds only. No universal uniqueness, owner qualification, acceptance or training admission.'}
    seen=set();shapes=set();firsts=set();profiles=set()
    for seed in range(seeds):
        fulls={m:a.generate(seed,{key:m},6,4) for m in modes}
        firsts.add(fulls[modes[0]]['private']['query_permutation'][0])
        inputs=lambda e:[p['input'] for sp in ('train','test') for p in e[sp]]
        assert inputs(fulls[modes[0]])==inputs(fulls[modes[1]])
        report['matched_settings_checks']+=1
        for g in inputs(fulls[modes[0]]):
            seen.add(sha(json.dumps(g).encode()));shapes.add((len(g),len(g[0])))
        for m in modes:
            e=fulls[m]
            for d in (2,3,6):
                ep=a.generate(seed,{key:m},d,4);report['episodes']+=1
                assert ep['train']==e['train'][:d] and ep['test']==e['test']
                for rival in a.rivals():
                    report['rival_checks']+=1
                    if all(a.predict(p['input'],rival)==p['output'] for p in ep['train']):
                        if any(a.predict(p['input'],rival)!=p['output'] for p in ep['test']):
                            report['failures'].append({'seed':seed,'mode':m,'demos':d,'rival':rival})
            if seed<2:
                for d in range(2,7):
                    for q in range(1,5):
                        ep=a.generate(seed,{key:m},d,q)
                        assert ep['train']==e['train'][:d] and ep['test']==e['test'][:q]
                        assert len(set(map(str,inputs(ep))))==d+q
                        assert a.public_turn(ep,0)==a.public_turn(a.generate(seed,{key:m},d,1),0)
                        report['boundary_count_checks']+=1
    report['distinct_inputs']=len(seen);report['input_shapes']=sorted(map(list,shapes));report['first_source_indices_observed']=sorted(firsts)
    if report['failures']:
        report['status']='failed';dump(out/'audit.json',report);raise ValueError('demo-fitting, query-changing rivals: '+str(report['failures'][:8]))
    if seeds>=16 and len(firsts)<2:raise ValueError('presentation order did not vary')
    apply,identity,bridge=_real_evaluator(root/'shared/runtime');execution=[]
    def execute(program,g):
        _validate_programs([{'program':program,'counterfactual_program':program}])
        result=apply(program,deepcopy(g));report['racket_evaluations']+=1
        execution.append({'program_sha256':sha(program.encode()),'input_sha256':sha(json.dumps(g,sort_keys=True).encode()),
                          'output_sha256':sha(json.dumps(result,sort_keys=True).encode())})
        return result
    private=[]
    try:
        for seed in (17,43):
            for m in modes:
                ep=a.generate(seed,{key:m},6,4);program=a.program({key:m})
                for pair in ep['train']+ep['test']:
                    if execute(program,pair['input'])!=pair['output']:raise ValueError('Python/Racket disagreement')
                for i in range(4):
                    view=a.public_turn(ep,i);raw=io.encode(view)
                    assert raw==public_challenge_bytes(view)
                    identity_key=sha(raw);io.validate(raw,identity_key)
                    p=out/'public'/f'{identity_key}.json';p.parent.mkdir(exist_ok=True)
                    if p.exists():raise ValueError('duplicate public bytes')
                    p.write_bytes(raw);report['public_files']+=1
                    private.append({'id':identity_key,'seed':seed,'mode':m,'source_query':ep['private']['query_permutation'][i],'answer':ep['test'][i]['output']})
                    altered=deepcopy(ep);altered['private']={'CANARY':'private'};altered['program_solution']='CANARY';altered['settings']={'CANARY':'private'}
                    altered['test'][i]['output']=[[9]]
                    for j in range(i+1,4):altered['test'][j]={'input':[[8]],'output':[[9]]}
                    assert io.encode(a.public_turn(altered,i))==raw;report['privacy_checks']+=1
                positive=deepcopy(ep);positive['train'][0]['output'][0][0]=(positive['train'][0]['output'][0][0]+1)%10
                assert a.public_turn(positive,0)!=a.public_turn(ep,0);report['positive_controls']+=1
        good=a.public_turn(a.generate(17,{key:modes[0]},2,4),0);raw=io.encode(good)
        negative=[]
        x=deepcopy(good);x['settings']={'private':True};negative.append(x)
        x=deepcopy(good);x['test'][0]['output']=[[1]];negative.append(x)
        x=deepcopy(good);x['test'].append({'input':[[2]]});negative.append(x)
        x=deepcopy(good);x['test'][0]['input']=[[True]];negative.append(x)
        x=deepcopy(good);x['test'][0]['input']=x['train'][0]['input'];negative.append(x)
        for view in negative:
            try:io.encode(view)
            except ValueError:report['negative_exports_rejected']+=1
            else:raise AssertionError('negative public export accepted')
        for data,ident in ((raw,'0'*64),(raw+b'\n',sha(raw+b'\n'))):
            try:io.validate(data,ident)
            except ValueError:report['negative_exports_rejected']+=1
            else:raise AssertionError('negative identity accepted')
        alt=modes[1];episode=a.generate(17,{key:alt},2,4)
        pair=next(p for p in episode['test'] if len(p['input'])==len(p['input'][0])==30)
        program=a.program({key:alt});counter=a.counterfactual_program()
        actual=execute(program,pair['input']);wrong=execute(counter,pair['input'])
        if actual!=pair['output'] or actual==wrong:raise ValueError('causal witness invalid')
        witness={'schema':'arcpuzzles-sequential-dependency-witness-v1','source_binding':receipt['source_binding'],
                 **a.DEPENDENCY,'racket':{'backend':'racket','protected':True},
                 'cases':[{'input':pair['input'],'settings':{key:alt},'intermediate_value':a.causal_metadata(pair['input']),
                           'program':program,'output':actual,'counterfactual_program':counter,'counterfactual_output':wrong,
                           'ablation':a.ABLATION,'difference':differences(actual,wrong)}]}
        dump(out/'causal/witness.json',witness)
        report['causal_difference']=differences(actual,wrong)
    finally:bridge.close()
    replay=replay_witness(root,witness);replay['status']='reviewer_replayed'
    replay['verification_scope']='Author replay via protected repository helper; not owner acceptance.'
    dump(out/'causal/replay.json',replay)
    report['causal_replay_evaluations']=replay['evaluations'];report['racket']=identity
    dump(out/'private/execution.json',execution);dump(out/'private/queries.json',private)
    verify_binding(root,receipt)
    dump(out/'audit.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preflight',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--seeds',type=int,default=32)
    args=parser.parse_args();report=run(args.preflight,args.out,args.seeds)
    print(json.dumps({k:report[k] for k in ('status','episodes','rival_checks','distinct_inputs','racket_evaluations','public_files','causal_difference')}))
if __name__=='__main__':main()
