#!/usr/bin/env python3
"""Source-bound finite learnability probe; no approval or training claim."""
import copy, hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'repo'
sys.path.insert(0,str(ROOT/'src'))
from arcpuzzles.catalog import Catalog
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid

def sha(data): return hashlib.sha256(data).hexdigest()
def main():
    task='8801696784e1'
    runtime=ROOT/'shared/runtime'
    variants=Catalog(ROOT)._variants()[task]
    assert len(variants)==1
    canonical=variants[0]['program_solution']
    needle='(mapped (cond ((= code 1) 2) ((= code 2) 3) (else 4)))'
    assert canonical.count(needle)==1
    rival=canonical.replace(needle,'(mapped 2)')
    bridge=None
    with _local_imports(runtime,HERE):
        from reviewer_support import load_selected_generator, canonical_pairs
        generator,path,source_hash=load_selected_generator(task,root=ROOT)
        pairs=canonical_pairs(task,root=ROOT,variant=0,labeled_only=True)
        train=[p for p in pairs if p['split']=='train']
        query=None
        for index in range(100):
            g=generator.generate(20261024,index)
            if generator.self_check(g) or g[-1][-1]!=2: continue
            comps=generator._same_color_components_without_code(g)
            cells=next(cells for color,cells in comps if generator._both_sym(cells))
            hh=max(r for r,c in cells)-min(r for r,c in cells)+1
            ww=max(c for r,c in cells)-min(c for r,c in cells)+1
            if hh!=ww:
                query={'seed':20261024,'sample_index':index,'input':g,'bbox':[hh,ww],'self_check':[]}
                break
        assert query is not None,'No finite query found'
        apply,identity,bridge=_real_evaluator(runtime)
        try:
            evidence=[]
            for p in train:
                expected=_grid(apply(canonical,copy.deepcopy(p['input'])))
                wrong=_grid(apply(rival,copy.deepcopy(p['input'])))
                assert expected==p['output'],'Canonical stored demo disagrees with protected rule'
                assert expected==wrong,'Rival does not fit every visible demo'
                evidence.append({'pair_index':p['pair_index'],'input':p['input'],'output':expected,'rival_output':wrong})
            query['output']=_grid(apply(canonical,copy.deepcopy(query['input'])))
            query['rival_output']=_grid(apply(rival,copy.deepcopy(query['input'])))
            assert query['output']!=query['rival_output']
            result={'schema':'8801696784e1-bounded-learnability-v1','status':'finding','task_id':task,
                'finding':'Always rotate the selected symmetric target clockwise fits every canonical visible demonstration but disagrees on a lawful generated code-2 rectangular target.',
                'rival':'Replace code-dependent mapped rotation with mapped=2 (always clockwise), preserving all selection/scaling logic.',
                'generator_path':str(path),'generator_sha256':source_hash,
                'canonical_program':canonical,'canonical_program_sha256':sha(canonical.encode()),
                'rival_program':rival,'rival_program_sha256':sha(rival.encode()),
                'probe_sha256':sha(Path(__file__).read_bytes()),
                'command':'WORK/.venv/bin/python review.py run --receipt checks/8801696784e1/command.json python3 ../checks/8801696784e1/probe.py',
                'racket':identity,'protected_executions':2*(len(train)+1),
                'demonstrations':evidence,'query':query,
                'scope':'Four canonical visible demonstrations and one deterministic generated query. This is a teaching ambiguity, not a canonical implementation error; it does not assert ambiguity of arbitrary generated episodes.',
                'approval_changed':False,'training_admitted':False,
                'suggested_repair':'Teach at least one code-2 target whose crop differs from its quarter turn; keep code-1/3 examples that differ from identity.'}
            (HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({'status':'finding','demos':len(train),'query_seed':query['seed'],'query_sample_index':query['sample_index'],'query_bbox':query['bbox'],'protected_executions':result['protected_executions'],'result':str(HERE/'result.json')}))
        finally:
            if bridge is not None: bridge.close()
if __name__=='__main__': main()
