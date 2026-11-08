"""Retain the supported four-demo color-specific majority failure before repair."""
import importlib.util
import json
from pathlib import Path
import sys

home=Path('generators/e971e0773705/workspace/parametric').resolve()
spec=importlib.util.spec_from_file_location('asymmetric_before_audit',home/'audit_native.py')
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
out=Path('../checks/e971e0773705/asymmetric-majority-before/reproduction.json')
settings={'count_mode':'cancel_opposites'}
binding=a.source_binding()
bridge=None
try:
    with a._local_imports(a.RUNTIME,a.HOME):
        adapter=a._load(home/'adapter.py')
        episode=adapter.generate(17,settings,4,4)
        apply,identity,bridge=a._real_evaluator(a.RUNTIME)
        assert identity['backend']=='racket' and identity['protected'] is True
        engine=a.CachedEvaluator(apply)
        programs={'cancel_opposites':adapter.program(settings)}
        programs.update({name:a.rival_program(settings,name) for name in ('blue_majority_four','green_majority_four')})
        rows=[]
        for name,program in programs.items():
            def execute(source,grid,name=name):
                actual=engine(source,grid)
                expected=a.reference(grid,settings) if name=='cancel_opposites' else a.rival_reference(grid,settings,name)
                assert actual==expected, name
                return actual
            rows.append(a.assess(name,program,episode['train'],episode['test'],execute))
        bad=next(r for r in rows if r['name']=='blue_majority_four')
        assert bad['survives_demonstrations'] and bad['query_disagreement_indices']==[2]
        assert binding==a.source_binding(),'Source changed during retained reproduction'
        report={'schema':'e971e0773705-asymmetric-majority-before-v1','status':'reproduced_supported_episode_ambiguity','visibility':'controller_private','training_admitted':False,'seed':17,'settings':settings,'demonstration_count':4,'query_count':4,'fit_frozen_before_query':True,'source_files_sha256':binding,'source_snapshot':'../asymmetric-majority-before-source','racket':identity,'programs':programs,'train':episode['train'],'test':episode['test'],'hypotheses':rows,'scene_facts':{key:[a.facts(p['input']) for p in episode[key]] for key in ('train','test')},'execution':{'requests':engine.requests,'racket_evaluations':engine.evaluations,'cache_hits':engine.cache_hits},'limits':'Source-bound pre-repair min4 sampler, seed17. Both channel-specific majority variants execute on all demonstrations before any of their query tests. Blue-only majority fits all4 demonstrations and differs at query2; no training admission or owner acceptance is claimed.'}
        out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'status':report['status'],'execution':report['execution'],'blue_majority_disagreement_indices':bad['query_disagreement_indices'],'train_counts':[a.facts(p['input'])['orientation_counts'] for p in episode['train']],'query2_counts':a.facts(episode['test'][2]['input'])['orientation_counts']},sort_keys=True))
finally:
    if bridge is not None: bridge.close()
