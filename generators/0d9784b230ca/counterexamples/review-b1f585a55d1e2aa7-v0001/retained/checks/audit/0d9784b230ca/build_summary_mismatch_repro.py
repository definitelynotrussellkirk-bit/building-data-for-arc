from __future__ import annotations
import json, os, sys
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "0d9784b230ca"
root = find_root(__file__)
gen, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
pair = canonical_pairs(TASK_ID, root=root, labeled_only=True)[0]
grid = pair["input"]
# The generator SUMMARY says the 5/6/7 markers remain unchanged and only the
# missing fourth corner is painted.  Materialize exactly that documented rival.
pos = {}
for r,row in enumerate(grid):
    for c,value in enumerate(row):
        if value in (5,6,7): pos[value]=(r,c)
o,x,y=pos[5],pos[6],pos[7]
vx=(x[0]-o[0],x[1]-o[1]); vy=(y[0]-o[0],y[1]-o[1])
missing=(o[0]+vx[0]+vy[0],o[1]+vx[1]+vy[1])
rival=[list(row) for row in grid]
rival[missing[0]][missing[1]]=8
out_dir=Path(__file__).resolve().parent
(out_dir/'input.json').write_text(json.dumps(grid,indent=2)+'\n')
payload={
  'schema':'arc-audit-summary-rule-mismatch-v1',
  'task_id':TASK_ID,
  'generator_path':str(generator_path),
  'generator_sha256':generator_sha256,
  'canonical_identity':{k:pair[k] for k in ('variant','split','pair_index')},
  'input':grid,
  'self_check_errors':gen.self_check(grid),
  'documented_summary_rival_output':rival,
  'canonical_expected_output':pair['output'],
  'documented_rival_matches_canonical':rival==pair['output'],
  'missing_corner':list(missing),
  'finding':'Generator SUMMARY says markers stay unchanged and only the missing corner is painted, but canonical authority recolors all four local-block cells to 8.',
  'command':{'cwd':os.getcwd(),'argv':[sys.executable,*sys.argv]},
}
(out_dir/'summary-mismatch.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
print(json.dumps({'self_check_errors':payload['self_check_errors'],'documented_rival_matches_canonical':payload['documented_rival_matches_canonical'],'generator_sha256':generator_sha256}))
raise SystemExit(0 if not payload['self_check_errors'] and not payload['documented_rival_matches_canonical'] else 1)
