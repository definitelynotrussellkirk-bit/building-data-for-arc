#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

HERE=Path(__file__).resolve().parent
ROOT=find_root(__file__)
TASK='8d7d1364cf11'
module, source, digest=load_selected_generator(TASK, root=ROOT)
witness_path=ROOT/'generators'/TASK/'counterexamples'/'color5-shortcut.json'
witness=json.loads(witness_path.read_text())
grid=module.generate(70001,1,difficulty='hard')
retained=witness['generated_witness']['input']
if grid != retained:
    raise SystemExit('current generator no longer emits retained witness')
rival=module.SEMANTIC_RIVALS['ignore_productive_color5'](grid)
(HERE/'input.json').write_text(json.dumps(grid,indent=2)+'\n')
(HERE/'rival.json').write_text(json.dumps(rival,indent=2)+'\n')
canon=[]
for i,pair in enumerate(canonical_pairs(TASK, root=ROOT)):
    predicted=module.SEMANTIC_RIVALS['ignore_productive_color5'](pair['input'])
    canon.append({'index':i,'fits':predicted==pair['output']})
pre={
 'schema':'8d7d1364cf11-question-probe-v1',
 'task_id':TASK,
 'generator_sha256':digest,
 'generator_source':str(source.relative_to(ROOT)),
 'witness_seed':70001,
 'witness_sample_index':1,
 'witness_difficulty':'hard',
 'witness_matches_retained_input':True,
 'canonical_fit':canon,
 'canonical_fits_all':all(x['fits'] for x in canon),
 'rival_name':'ignore_productive_color5',
 'rival_output':rival,
 'input':grid,
 'retained_counterexample_sha256':hashlib.sha256(witness_path.read_bytes()).hexdigest(),
}
(HERE/'pre.json').write_text(json.dumps(pre,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:pre[k] for k in ('generator_sha256','canonical_fits_all','witness_matches_retained_input')},indent=2))
