"""Extract reproducible audit witnesses from the public source-bound census.

Authoring only; run after both solve episodes are frozen. Does not modify an
audit target and never imports a private runner. Racket outputs are obtained
separately through `arcpuzzles apply` and cross-checked in verification mode.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import find_root

TARGETS=('dd038eb3d459','e443791433ff')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def load(root,task):
    source=root/'generators'/task/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+task,source)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod,source


def extract(root,base):
    summary={}
    for task in TARGETS:
        mod,source=load(root,task);folder=base/task
        census=json.loads((folder/'census.json').read_text())
        assert sha(source)==census['generator_sha256']
        lesson=next(l for l in census['lessons'] if any(r['ambiguous'] for r in l['rotations']))
        rotation=next(r for r in lesson['rotations'] if r['ambiguous'])
        key=next(k for k,v in rotation['rivals'].items() if v=='ambiguous')
        namespace,name=key.split(':',1);rival=getattr(mod,namespace)[name]
        inst=lesson['instance'];pairs=inst['train']+inst['test'];q=rotation['query_index']
        query=pairs[q];train=[pairs[i] for i in rotation['train_indices']]
        assert all(rival(p['input'])==p['output'] for p in train)
        wrong=rival(query['input']);assert wrong!=query['output']
        accepted=inst['sampling']['accepted_pairs'][q]['sample_index']
        assert mod.generate(lesson['seed'],accepted,difficulty=lesson['band'])==query['input']
        witness={'task_id':task,'generator_sha256':sha(source),'declared_rule_hash':mod.RULE_HASH,
                 'census_rule_source_sha256':census['rule_source_sha256'],'seed':lesson['seed'],
                 'difficulty':lesson['band'],'lesson_index':lesson['index'],'lesson_start':lesson['sample_index'],
                 'query_pair_index':q,'sample_index':accepted,'overrides':{},'rival':key,
                 'rival_fits_all_demonstrations':True,'demonstrations':train,'input':query['input'],
                 'census_racket_output':query['output'],'rival_output':wrong,
                 'self_check_errors':mod.self_check(query['input']),'rotation':rotation,
                 'interpretation':'Real ambiguity under arbitrary pair holdout, not incorrect labels or a failure of the documented ordered production curriculum.'}
        inputs=[query['input']];typed=[]
        if task=='e443791433ff':
            for axis,value in [('grid_h',8.9),('grid_w','10'),('n_decoys',1.9),('n_decoys',True),('n_sources','6')]:
                g=mod.generate(37,0,difficulty='easy',**{axis:value})
                observed={'grid_h':len(g),'grid_w':len(g[0]),'n_sources':sum(v==3 for row in g for v in row),'n_decoys':sum(v==2 for row in g for v in row)}
                typed.append({'seed':37,'sample_index':0,'difficulty':'easy','overrides':{axis:value},'actual_observed_value':observed[axis],'self_check_errors':mod.self_check(g),'input_index':len(inputs),'input':g})
                inputs.append(g)
            none_case=None
            for seed in range(100):
                a=mod.generate(seed,0,difficulty='easy');b=mod.generate(seed,0,difficulty='easy',n_sources=None)
                if a!=b:
                    none_case={'seed':seed,'sample_index':0,'difficulty':'easy','without_override':a,'with_n_sources_none':b,'without_count':sum(v==3 for row in a for v in row),'with_count':sum(v==3 for row in b for v in row)};break
            (folder/'override-witnesses.json').write_text(json.dumps({'task_id':task,'generator_sha256':sha(source),'rule_hash':mod.RULE_HASH,'typed_cases':typed,'none_changes_default':none_case},indent=2)+'\n')
        (folder/'rotation-witness.json').write_text(json.dumps(witness,indent=2)+'\n')
        (folder/'input.json').write_text(json.dumps(inputs)+'\n')
        summary[task]={'generator_sha256':sha(source),'query_sample_index':accepted,'rotation_query_index':q,'rival':key,'typed_cases':len(typed),'summary':census['summary']}
    (base/'extraction-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


def verify(root,base):
    result={}
    for task in TARGETS:
        mod,source=load(root,task);folder=base/task
        record=json.loads((folder/'racket.json').read_text());witness=json.loads((folder/'rotation-witness.json').read_text())
        assert sha(source)==record['generator_sha256']==witness['generator_sha256']
        assert record['executed_rule_hash']==mod.RULE_HASH
        assert all(r['valid_output'] and r['error'] is None for r in record['results'])
        first=record['results'][0]
        assert first['input']==witness['input']
        assert first['output']==witness['census_racket_output']
        assert first['output']!=witness['rival_output']
        witness['actual_racket_output']=first['output'];witness['reference_command']=record['command'];witness['reference_cwd']=record['cwd'];witness['reference_report']='racket.json'
        witness['rule_text_sha256']=record['rule_text_sha256'];witness['reference_verified']=True
        (folder/'rotation-witness.json').write_text(json.dumps(witness,indent=2)+'\n')
        result[task]={'status':'verified','source_sha256':sha(source),'reference_results':len(record['results']),'reference_command':record['command'],'reference_cwd':record['cwd']}
    (base/'verification-summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('extract','verify'));p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    (extract if a.mode=='extract' else verify)(find_root(__file__),a.out)
