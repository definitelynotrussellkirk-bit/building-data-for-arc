#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID='5e31b63e58c8'
root=find_root(Path.cwd())
gen, source, source_hash=load_selected_generator(TASK_ID, root=root)
requested={'grid_h':9,'grid_w':20,'n_obj':6}
grid=gen.generate(271828, 11, difficulty='hard', **requested)
reds={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==2}
components=[]
while reds:
    start=min(reds); reds.remove(start); stack=[start]; cells=[]
    while stack:
        r,c=stack.pop(); cells.append((r,c))
        for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
            if q in reds:
                reds.remove(q); stack.append(q)
    components.append(cells)
components.sort(key=lambda cells:min(c for _,c in cells))
report={
  'schema':'audit-object-count-contract-v1','task_id':TASK_ID,
  'generator_path':str(source.relative_to(root)),
  'generator_sha256':source_hash,
  'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'seed':271828,'sample_index':11,'difficulty':'hard','requested':requested,
  'observed':{
      'grid_h':len(grid),'grid_w':len(grid[0]),
      'n_obj':len(components),
      'component_bboxes':[
          [min(r for r,_ in cells),min(c for _,c in cells),max(r for r,_ in cells),max(c for _,c in cells)]
          for cells in components
      ],
      'self_check':gen.self_check(grid,difficulty='hard'),
  },
  'object_count_contract_failed':len(components) != requested['n_obj'],
  'self_check_missed_failure':not gen.self_check(grid,difficulty='hard'),
  'input':grid,
}
out=Path('../checks/audit/5e31b63e58c8/object-count.json')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+'\n')
Path('../checks/audit/5e31b63e58c8/input.json').write_text(json.dumps(grid,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('generator_sha256','object_count_contract_failed','self_check_missed_failure')}))
raise SystemExit(0 if report['object_count_contract_failed'] and report['self_check_missed_failure'] else 1)
