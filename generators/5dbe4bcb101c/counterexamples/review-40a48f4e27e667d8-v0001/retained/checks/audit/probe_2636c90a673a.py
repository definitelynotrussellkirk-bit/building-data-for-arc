from __future__ import annotations
import hashlib, importlib.util, json, pathlib
from collections import Counter

ROOT=pathlib.Path('/mnt/data/arc_review_235908_work/repo')
PATH=ROOT/'generators/2636c90a673a/generator.py'
spec=importlib.util.spec_from_file_location('audit_2636',PATH)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

def truth(grid):
    keep=[i for i,v in enumerate(grid[0]) if v==1]
    return [[row[i] for i in keep] for row in grid[1:]]

def schedule_frequency_rival(grid):
    counts=Counter(v for v in grid[0] if v!=0)
    modal=max(counts.values())
    if modal==3:
        candidates=[v for v,n in counts.items() if n==2]
        marker=min(candidates) if candidates else min(counts,key=lambda v:(-counts[v],v))
    else:
        marker=min(counts,key=lambda v:(-counts[v],v))
    keep=[i for i,v in enumerate(grid[0]) if v==marker]
    return [[row[i] for i in keep] for row in grid[1:]]

def minimum_nonzero_rival(grid):
    marker=min(v for v in grid[0] if v!=0)
    keep=[i for i,v in enumerate(grid[0]) if v==marker]
    return [[row[i] for i in keep] for row in grid[1:]]

result={
 'task_id':gen.TASK_ID,
 'source_sha256':hashlib.sha256(PATH.read_bytes()).hexdigest(),
 'rule_hash_declared':gen.RULE_HASH,
 'default_draws':0,
 'schedule_frequency_matches':0,
 'minimum_nonzero_matches':0,
 'by_band':{},
}
for band in ('easy','medium','hard'):
    stats={'draws':0,'schedule_frequency_matches':0,'minimum_nonzero_matches':0,'header_histograms':{}}
    for seed in range(1000):
        sample_index=seed*11+5
        g=gen.generate(seed,sample_index,difficulty=band)
        target=truth(g)
        stats['draws']+=1
        stats['schedule_frequency_matches']+=schedule_frequency_rival(g)==target
        stats['minimum_nonzero_matches']+=minimum_nonzero_rival(g)==target
        hist=tuple(sorted(Counter(v for v in g[0] if v!=0).values()))
        stats['header_histograms'][str(hist)]=stats['header_histograms'].get(str(hist),0)+1
    result['by_band'][band]=stats
    result['default_draws']+=stats['draws']
    result['schedule_frequency_matches']+=stats['schedule_frequency_matches']
    result['minimum_nonzero_matches']+=stats['minimum_nonzero_matches']

# A legal exact override outside the default 2/4/5 selector schedule separates
# the schedule-frequency rival from the selected literal-blue rule.
case=None
for seed in range(100):
    g=gen.generate(seed,2,difficulty='medium',n_keep=3)
    if schedule_frequency_rival(g)!=truth(g):
        case={
          'seed':seed,'sample_index':2,'difficulty':'medium','overrides':{'n_keep':3},
          'input':g,'self_check':gen.self_check(g),
          'truth':truth(g),'schedule_frequency_rival':schedule_frequency_rival(g),
          'header_counts':dict(Counter(v for v in g[0] if v!=0)),
        }
        break
result['counterexample']=case
out=pathlib.Path('/mnt/data/arc_review_235908_work/checks/audit/2636c90a673a-probe.json')
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
