from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import canonical_pairs, load_selected_generator

TASK='1713e09a3132'
ROOT=Path(__file__).resolve().parents[3] / 'repo'
OUT=Path(__file__).resolve().parent
G, source, sha = load_selected_generator(TASK, root=ROOT)
input_grid=json.loads((OUT/'input.json').read_text())

def border_output(grid, *, overwrite: bool):
    h,w=len(grid),len(grid[0])
    colors=[]
    for row in grid:
        for v in row:
            if v and v not in colors: colors.append(v)
    out=[[0]*w for _ in range(h)]
    for color in colors:
        pts=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color]
        if len(pts)!=2: continue
        (ra,ca),(rb,cb)=pts
        r0,r1=sorted((ra,rb)); c0,c1=sorted((ca,cb))
        for r in range(r0,r1+1):
            for c in range(c0,c1+1):
                if r in (r0,r1) or c in (c0,c1):
                    if overwrite or out[r][c]==0:
                        out[r][c]=color
    return out

selected_mirror=border_output(input_grid, overwrite=True)
first_wins=border_output(input_grid, overwrite=False)
(OUT/'selected_mirror.json').write_text(json.dumps(selected_mirror,indent=2)+'\n')
(OUT/'rival_first_wins.json').write_text(json.dumps(first_wins,indent=2)+'\n')

def boxes(grid):
    by={}
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v: by.setdefault(v,[]).append((r,c))
    out={}
    for color,pts in by.items():
        (r1,c1),(r2,c2)=pts
        r0,rr=sorted((r1,r2)); c0,cc=sorted((c1,c2))
        out[color]=set((r,c) for r in range(r0,rr+1) for c in range(c0,cc+1))
    return out

# Finite support check: this generator deliberately reserves whole bboxes, so all
# sampled outputs should be disjoint. Record it independently rather than infer it.
sampled=0; overlapping=0; invalid=0; short_pair=0
for band in ('easy','medium','hard'):
    for seed in range(100):
        grid=G.generate(seed,0,difficulty=band)
        sampled += 1
        errs=G.self_check(grid,difficulty=band,meta=None)
        if errs: invalid += 1
        bs=boxes(grid)
        vals=list(bs)
        if any(bs[vals[i]] & bs[vals[j]] for i in range(len(vals)) for j in range(i+1,len(vals))): overlapping += 1
        if len(vals) < (2 if band!='hard' else 3): short_pair += 1

canonical=list(canonical_pairs(TASK, root=ROOT))
canonical_validator=[]
for i,pair in enumerate(canonical):
    errs=G.self_check(pair['input'],meta=None)
    canonical_validator.append({'pair_index':i,'accepted':not errs,'errors':errs})

# Exact-control reproductions.
override_cases=[]
for overrides in (
    {'palette_kind':'warm'}, {'palette_kind':'cool'}, {'palette_size':9},
    {'n_distinct_colors':9}, {'position_bias':'diagonal_corner_pairs'},
    {'density':'sparse'}, {'texture':'warm'},
):
    base=G.generate(0,0,difficulty='medium')
    altered=G.generate(0,0,difficulty='medium',**overrides)
    override_cases.append({'overrides':overrides,'returned':True,'same_as_baseline':altered==base})
for overrides in ({'n_pairs':1},{'n_pairs':4},{'grid_h':8},{'grid_h':14},{'grid_w':9},{'grid_w':14}):
    try:
        G.generate(0,0,difficulty='medium',**overrides)
    except Exception as exc:
        override_cases.append({'overrides':overrides,'returned':False,'error_type':type(exc).__name__,'error':str(exc)})
    else:
        override_cases.append({'overrides':overrides,'returned':True})

payload={
 'schema':'audit-1713e09a3132-overlap-and-overrides-v1',
 'task_id':TASK,
 'generator_path':str(source.relative_to(ROOT)),
 'generator_sha256':sha,
 'rule_hash':getattr(G,'RULE_HASH',None),
 'input':'input.json',
 'self_check_errors':G.self_check(input_grid,meta=None),
 'selected_mirror':'selected_mirror.json',
 'rival':'rival_first_wins.json',
 'differing_cells':sum(a!=b for ra,rb in zip(selected_mirror,first_wins) for a,b in zip(ra,rb)),
 'support_probe':{'bands':['easy','medium','hard'],'seeds':'0..99','sample_index':0,'draws':sampled,'overlapping_bbox_inputs':overlapping,'self_check_failures':invalid,'too_few_pairs':short_pair},
 'canonical_validator':canonical_validator,
 'override_cases':override_cases,
 'command':'PYTHONPATH=src:shared/runtime python3 ../checks/audit/1713e09a3132-overlap-shortcut/build_probe.py',
 'cwd':'repo',
}
(OUT/'probe.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
print(json.dumps({'generator_sha256':sha,'draws':sampled,'overlaps':overlapping,'canonical_rejected':sum(not x['accepted'] for x in canonical_validator),'diff_cells':payload['differing_cells']},sort_keys=True))
