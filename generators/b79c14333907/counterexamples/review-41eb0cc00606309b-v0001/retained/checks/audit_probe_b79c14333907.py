from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator, canonical_pairs
TASK='b79c14333907'
root=find_root(__file__)
gen, source_path, source_sha=load_selected_generator(TASK, root=root)
per_band={}
examples=[]
for band in ('easy','medium','hard'):
    rows=[]
    all_border_five=True
    valid=0
    for i in range(100):
        grid=gen.generate(20261022, i, difficulty=band)
        errs=gen.self_check(grid, difficulty=band)
        if not errs: valid += 1
        h,w=len(grid),len(grid[0])
        border=[grid[0][c] for c in range(w)] + [grid[h-1][c] for c in range(w)] + [grid[r][0] for r in range(1,h-1)] + [grid[r][w-1] for r in range(1,h-1)]
        hit=all(v==5 for v in border)
        all_border_five &= hit
        rows.append({'sample_index':i,'shape':[h,w],'all_border_five':hit,'self_check':errs})
        if i==0: examples.append({'band':band,'input':grid,'shape':[h,w]})
    per_band[band]={'draws':100,'self_check_passed':valid,'all_border_five':all_border_five,'rows':rows}

pairs=canonical_pairs(TASK, root=root, labeled_only=True)
witness=None
for idx,pair in enumerate(pairs):
    grid=pair['input']; output=pair['output']; h,w=len(grid),len(grid[0])
    changed=[]
    for r,c in [(0,c) for c in range(w)]+[(h-1,c) for c in range(w)]+[(r,0) for r in range(1,h-1)]+[(r,w-1) for r in range(1,h-1)]:
        if grid[r][c] != output[r][c]: changed.append([r,c,grid[r][c],output[r][c]])
    if changed:
        rival=[row[:] for row in output]
        for r,c,_,_ in changed:
            rival[r][c]=grid[r][c]
        witness={'canonical_pair_index':idx,'input':grid,'canonical_output':output,'preserve_border_rival_output':rival,'changed_border_cells':changed,'self_check':gen.self_check(grid)}
        break
assert witness is not None
out=Path('/mnt/data/arc_review_20261022_112101/WORK/checks/audit/b79c14333907-border')
(out/'input.json').write_text(json.dumps(witness['input'],indent=2)+'\n')
report={
 'schema':'arcpuzzles-peer-audit-probe-v1','task_id':TASK,'generator_sha256':source_sha,
 'generator_version':getattr(gen,'VERSION',None),'rule_hash':getattr(gen,'RULE_HASH',None),
 'sample_plan':{'seed':20261022,'per_band':100,'sample_indices':'0..99'},
 'per_band':per_band,
 'all_300_generated_borders_are_five':all(x['all_border_five'] for x in per_band.values()),
 'canonical_pairs_checked':len(pairs),'canonical_open_border_witness':witness,
 'conclusion':'Generated support fixes the entire border to 5, so preserve-border remains a plausible generated-domain shortcut; a canonical input refutes it.'
}
(out/'probe.pre-racket.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'generator_sha256':source_sha,'all_300_generated_borders_are_five':report['all_300_generated_borders_are_five'],'canonical_pairs':len(pairs),'witness_index':witness['canonical_pair_index']},indent=2))
