from __future__ import annotations
import copy, hashlib, importlib.util, json
from collections import Counter
from pathlib import Path
from reviewer_support import canonical_pairs

TASK='1409f5f7af2e'
ROOT=Path(__file__).resolve().parents[3] / 'repo'
GEN=ROOT/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_1409', GEN); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def targets(grid):
    return [(r,c) for r in range(1,len(grid)-1) for c in range(len(grid[0]))
            if grid[r][c]==0 and grid[r-1][c]==3 and grid[r+1][c]==3]

def overlap_endpoints(grid):
    counts=Counter(ep for r,c in targets(grid) for ep in ((r-1,c),(r+1,c)))
    return sorted([list(ep) for ep,n in counts.items() if n>1])

def rival(grid):
    out=copy.deepcopy(grid)
    ts=targets(grid)
    counts=Counter(ep for r,c in ts for ep in ((r-1,c),(r+1,c)))
    for r,c in ts:
        if counts[(r-1,c)]==1 and counts[(r+1,c)]==1:
            out[r][c]=2
    return out

bands=[None,'easy','medium','hard']
samples=0; generated_overlap=0; generated_rival_mismatch=0
for band in bands:
    for seed in range(100):
        for index in range(20):
            grid=mod.generate(seed,index,difficulty=band)
            samples+=1
            generated_overlap += bool(overlap_endpoints(grid))
            generated_rival_mismatch += rival(grid)!=mod.rule_mirror(grid)

pairs=canonical_pairs(TASK, root=ROOT)
canon=[]; selected=None
for i,pair in enumerate(pairs):
    rec={'index':i,'overlap_endpoints':overlap_endpoints(pair['input']),
         'rival_disagrees':rival(pair['input'])!=pair['output'],
         'self_check':mod.self_check(pair['input'])}
    canon.append(rec)
    if selected is None and rec['overlap_endpoints']:
        selected=(i,pair)
assert selected is not None
idx,pair=selected
outdir=ROOT.parent/'checks'/'audit'/TASK
(outdir/'input.json').write_text(json.dumps(pair['input'],indent=2)+'\n')
(outdir/'rival.json').write_text(json.dumps(rival(pair['input']),indent=2)+'\n')
report={
 'schema':'arcpuzzles-audit-probe-v1','task_id':TASK,
 'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),
 'domain':{'bands':['default','easy','medium','hard'],'seeds':'0..99','sample_indices':'0..19'},
 'generated':{'samples':samples,'shared_endpoint_scenes':generated_overlap,'rival_mismatches':generated_rival_mismatch},
 'canonical':canon,'selected_canonical_index':idx,
 'rival':'recolor only green-black-green centers whose endpoint greens are not shared by another target',
 'finding':'The constructor requires each target triple to occupy three previously empty cells, so generated targets never share endpoints. The rival is exact on every sampled generated grid but fails lawful canonical overlapping chains.'
}
(outdir/'probe-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
