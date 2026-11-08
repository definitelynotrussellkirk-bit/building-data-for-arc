from __future__ import annotations
import hashlib, importlib.util, json, pathlib
from collections import deque

ROOT=pathlib.Path('/mnt/data/arc_review_235908_work/repo')
PATH=ROOT/'generators/5dbe4bcb101c/generator.py'
spec=importlib.util.spec_from_file_location('audit_5d',PATH)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

def components(grid,color):
    rem={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color}
    out=[]
    while rem:
        start=min(rem); rem.remove(start); comp={start}; q=[start]
        while q:
            r,c=q.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in rem:
                    rem.remove(p); comp.add(p); q.append(p)
        out.append(comp)
    return out

def crop(grid,comp):
    rs=[r for r,c in comp]; cs=[c for r,c in comp]
    return [row[min(cs):max(cs)+1] for row in grid[min(rs):max(rs)+1]]

def candidates(grid):
    marker=next(v for v in grid[0] if v!=0)
    return [c for c in components(grid,marker) if len(c)>1]

def topmost(grid):
    cs=candidates(grid)
    comp=min(cs,key=lambda x:(min(r for r,c in x),min(c for r,c in x)))
    return crop(grid,comp)

def largest(grid):
    cs=candidates(grid)
    comp=min(cs,key=lambda x:(-len(x),min(r for r,c in x),min(c for r,c in x)))
    return crop(grid,comp)

def bottommost(grid):
    cs=candidates(grid)
    comp=min(cs,key=lambda x:(-min(r for r,c in x),min(c for r,c in x)))
    return crop(grid,comp)

result={
 'task_id':gen.TASK_ID,
 'source_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
 'rule_hash_declared':getattr(gen,'RULE_HASH',None),
}
base=gen.generate(917,13,difficulty='medium')
result['override_counterexamples']={}
for name,value in [('marker_color',9),('n_marker_blobs',3),('shape_size',7),('unknown_axis',123)]:
    try:
        changed=gen.generate(917,13,difficulty='medium',**{name:value})
        result['override_counterexamples'][name]={
            'accepted':True,
            'byte_identical_to_default':changed==base,
            'requested':value,
            'observed_marker':next(v for v in changed[0] if v!=0),
        }
    except Exception as exc:
        result['override_counterexamples'][name]={'accepted':False,'error':f'{type(exc).__name__}: {exc}'}

# Default single-instance semantic support by band.
for band in ('easy','medium','hard'):
    stats={'draws':0,'one_candidate':0,'multiple_candidates':0,'topmost_not_largest':0,'topmost_not_bottommost':0}
    for seed in range(1000):
        g=gen.generate(seed,seed*17+5,difficulty=band)
        cs=candidates(g)
        stats['draws']+=1
        stats['one_candidate']+=len(cs)==1
        stats['multiple_candidates']+=len(cs)>1
        stats['topmost_not_largest']+=topmost(g)!=largest(g)
        stats['topmost_not_bottommost']+=topmost(g)!=bottommost(g)
    result[f'{band}_semantic_support']=stats

# Search exact four-demo lessons where a plausible rival fits all demos but changes query.
ambiguities=[]
for band in ('easy','medium','hard'):
    for seed in range(400):
        for start in range(12):
            grids=[gen.generate(seed,start+i,difficulty=band) for i in range(gen.EXAMPLES_NEEDED+1)]
            labels=[topmost(g) for g in grids]
            for rival_name,rival in [('largest_marker_blob',largest),('bottommost_marker_blob',bottommost)]:
                preds=[rival(g) for g in grids]
                if preds[:-1]==labels[:-1] and preds[-1]!=labels[-1]:
                    ambiguities.append({
                      'band':band,'seed':seed,'start':start,'rival':rival_name,
                      'demo_match':[preds[i]==labels[i] for i in range(gen.EXAMPLES_NEEDED)],
                      'query_differs':True,
                      'query_input':grids[-1],
                      'query_truth':labels[-1],
                      'query_rival':preds[-1],
                    })
                    break
            if ambiguities and ambiguities[-1]['band']==band:
                break
        if ambiguities and ambiguities[-1]['band']==band:
            break
result['first_ambiguity_by_band']=ambiguities

out=pathlib.Path('/mnt/data/arc_review_235908_work/checks/audit/5dbe4bcb101c-probe.json')
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
