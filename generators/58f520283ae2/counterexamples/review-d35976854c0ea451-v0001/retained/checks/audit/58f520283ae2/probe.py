from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'repo'
TASK = '58f520283ae2'
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_58', SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)

grid = module.generate(17, 4, texture='square_motif')
nonzero = [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v and (r,c)!=(0,0)]
rows = [r for r,_,_ in nonzero]
cols = [c for _,c,_ in nonzero]
bbox = [min(rows), min(cols), max(rows), max(cols)]
record = {
  'schema':'arcpuzzles-audit-probe-v1',
  'task_id':TASK,
  'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
  'finding':'named square_motif degenerate is accepted by self_check',
  'seed':17,
  'sample_index':4,
  'overrides':{'texture':'square_motif'},
  'input':grid,
  'self_check_errors':module.self_check(grid),
  'motif_bbox':bbox,
  'motif_bbox_shape':[bbox[2]-bbox[0]+1,bbox[3]-bbox[1]+1],
  'declared_invariant':'the motif has a non-square bounding box so transforms are visible',
  'reproduced':module.self_check(grid)==[] and (bbox[2]-bbox[0])==(bbox[3]-bbox[1]),
}
Path(__file__).with_name('probe.json').write_text(json.dumps(record,indent=2)+'\n')
Path(__file__).with_name('input.json').write_text(json.dumps(grid,indent=2)+'\n')
print(json.dumps({k:record[k] for k in ('generator_sha256','self_check_errors','motif_bbox_shape','reproduced')},indent=2))
raise SystemExit(0 if record['reproduced'] else 1)
