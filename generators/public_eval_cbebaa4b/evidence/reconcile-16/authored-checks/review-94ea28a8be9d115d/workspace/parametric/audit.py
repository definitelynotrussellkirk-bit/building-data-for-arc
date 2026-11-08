"""Repeatable scoped authoring audit. This never grants owner acceptance.

Run with the packet's configured Python/RACKET_PATH. --out must be new. Counts
include repeated prefixes; distinct_inputs reports actual independent scenes.
"""
from pathlib import Path
from copy import deepcopy
import argparse
import hashlib
import importlib.util
import json
import sys

HERE=Path(__file__).resolve().parent

def load_adapter():
    spec=importlib.util.spec_from_file_location('_audit_cbebaa4b',HERE/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def root_path():
    return next(p for p in HERE.parents if (p/'src/arcpuzzles/parametric_worker.py').is_file() and (p/'shared/runtime/reviewer_support.py').is_file())

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

def run(out,seeds):
    if type(seeds) is not int or not 1<=seeds<=1000:raise ValueError('seeds must be in 1..1000')
    out=Path(out);out.mkdir(parents=True,exist_ok=False)
    (out/'public').mkdir();(out/'private').mkdir()
    root=root_path();sys.path[:0]=[str(root/'src'),str(root/'shared/runtime')]
    from reviewer_support import public_challenge_bytes
    from arcpuzzles.parametric_worker import _real_evaluator
    a=load_adapter();key=next(iter(a.PARAMETERS));values=a.PARAMETERS[key]
    report={'status':'passed','seed_count':seeds,'requests':0,'pair_instances':0,
            'matched_input_checks':0,'public_turn_checks':0,'distinct_inputs':0,
            'racket_evaluations':0,'finite_teaching':[],
            'limits':'Finite seeds and authored rivals only; no native acceptance or training admission.'}
    unique=set();first_sources=set()
    for seed in range(seeds):
        full={v:a.generate(seed,{key:v},6,4) for v in values}
        first_sources.add(full[values[0]]['private']['query_permutation'][0])
        for v in values:
            for split in ('train','test'):
                for pair in full[v][split]:unique.add(sha(json.dumps(pair['input']).encode()))
        for d in range(2,7):
            for q in range(1,5):
                episodes=[]
                for v in values:
                    episode=a.generate(seed,{key:v},d,q);episodes.append(episode)
                    assert episode['train']==full[v]['train'][:d]
                    assert episode['test']==full[v]['test'][:q]
                    assert len({json.dumps(p['input']) for sp in ('train','test') for p in episode[sp]})==d+q
                    report['requests']+=1;report['pair_instances']+=d+q
                    for index in range(q):
                        turn=a.public_turn(episode,index)
                        assert set(turn)=={'train','test'} and turn['test']==[{'input':episode['test'][index]['input']}]
                        altered=deepcopy(episode);altered['private']={'canary':'do not expose'}
                        altered['program_solution']='PRIVATE';altered['test'][index]['output']=[[9]]
                        for j in range(index+1,q):altered['test'][j]={'input':[[7]],'output':[[6]]}
                        assert a.public_turn(altered,index)==turn
                        assert public_challenge_bytes(turn)==public_challenge_bytes(a.public_turn(a.generate(seed,{key:v},d,1),0)) if index==0 else True
                        report['public_turn_checks']+=1
                assert [p['input'] for sp in ('train','test') for p in episodes[0][sp]]==[p['input'] for sp in ('train','test') for p in episodes[1][sp]]
                report['matched_input_checks']+=1
    report['distinct_inputs']=len(unique);report['first_source_indices_observed']=sorted(first_sources)
    apply,identity,bridge=_real_evaluator(root/'shared/runtime');report['racket']=identity
    executions=[];payloads={};private=[]
    try:
        for seed in (17,43):
            programs={**a.rival_programs(),values[1]:a.program({key:values[1]})}
            lesson=a.generate(seed,{key:values[1]},2,4)
            outputs={}
            for name,program in programs.items():
                outputs[name]=[]
                for split in ('train','test'):
                    for i,pair in enumerate(lesson[split]):
                        got=apply(program,pair['input']);expected=a.predict(pair['input'],name)
                        assert got==expected,(seed,name,split,i)
                        outputs[name].append(got);report['racket_evaluations']+=1
                        executions.append({'seed':seed,'name':name,'split':split,'index':i,
                            'program_sha256':sha(program.encode()),'input_sha256':sha(json.dumps(pair['input']).encode()),
                            'output_sha256':sha(json.dumps(got).encode())})
            for v in values:
                ep=a.generate(seed,{key:v},2,4)
                survivors=[name for name,labels in outputs.items() if labels[:2]==[p['output'] for p in ep['train']]]
                assert survivors==[v],(seed,v,survivors)
                report['finite_teaching'].append({'seed':seed,'settings':{key:v},'survivors':survivors,'hypotheses':list(programs)})
                for i in range(4):
                    raw=public_challenge_bytes(a.public_turn(ep,i));identity_key=sha(raw)
                    assert identity_key not in payloads
                    payloads[identity_key]=raw
                    private.append({'id':identity_key,'seed':seed,'settings':{key:v},'source_query':ep['private']['query_permutation'][i],'answer':ep['test'][i]['output']})
    finally:bridge.close()
    for identity_key,raw in sorted(payloads.items()):(out/'public'/f'{identity_key}.json').write_bytes(raw)
    dump(out/'private/queries.json',private);dump(out/'private/execution.json',executions)
    report['public_files']=len(payloads)
    report['source_sha256']={p.name:sha(p.read_bytes()) for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py','.rkt','.json')}
    dump(out/'audit.json',report)
    return report

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--seeds',type=int,default=20)
    args=parser.parse_args();r=run(args.out,args.seeds)
    print(json.dumps({k:r[k] for k in ('status','requests','pair_instances','distinct_inputs','racket_evaluations','public_files')}))
if __name__=='__main__':main()
