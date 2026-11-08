#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID='3faff4c1f734'
root=find_root(Path.cwd())
gen, source, source_hash=load_selected_generator(TASK_ID, root=root)
requested={
    'grid_h': 9,
    'grid_w': 10,
    'row_markers': 3,
    'col_markers': 3,
    'palette_size': 2,
    'n_distinct_colors': 2,
    'palette_kind': 'warm',
    'position_bias': 'border_markers',
    'density': 'sparse',
    'texture': 'warm',
}
grid=gen.generate(314159, 7, difficulty='hard', **requested)
nonzero=sorted({v for row in grid for v in row if v != 0})
row_markers=[(r,grid[r][0]) for r in range(1,len(grid)) if grid[r][0] != 0]
col_markers=[(c,grid[0][c]) for c in range(1,len(grid[0])) if grid[0][c] != 0]
# Show the advertised palette controls have no construction effect at all.
small=gen.generate(314159, 7, difficulty='hard', grid_h=9, grid_w=10,
                   row_markers=3, col_markers=3, palette_size=2,
                   n_distinct_colors=2, palette_kind='warm', texture='warm',
                   position_bias='border_markers', density='sparse')
large=gen.generate(314159, 7, difficulty='hard', grid_h=9, grid_w=10,
                   row_markers=3, col_markers=3, palette_size=9,
                   n_distinct_colors=9, palette_kind='cool', texture='cool',
                   position_bias='border_markers', density='sparse')
report={
  'schema':'audit-axis-contract-v1','task_id':TASK_ID,
  'generator_path':str(source.relative_to(root)),
  'generator_sha256':source_hash,
  'probe_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'seed':314159,'sample_index':7,'difficulty':'hard','requested':requested,
  'observed':{
      'grid_h':len(grid),'grid_w':len(grid[0]),
      'row_markers':len(row_markers),'col_markers':len(col_markers),
      'nonzero_colors':nonzero,'n_distinct_colors':len(nonzero),
      'self_check':gen.self_check(grid,difficulty='hard'),
  },
  'palette_contract_failed': len(nonzero) != requested['n_distinct_colors'] or len(nonzero) > requested['palette_size'],
  'opposite_palette_requests_identical': small == large,
  'row_markers':row_markers,'col_markers':col_markers,'input':grid,
}
out=Path('../checks/audit/3faff4c1f734/axis-contract.json')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,indent=2)+'\n')
Path('../checks/audit/3faff4c1f734/input.json').write_text(json.dumps(grid,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('generator_sha256','palette_contract_failed','opposite_palette_requests_identical')}))
raise SystemExit(0 if report['palette_contract_failed'] and report['opposite_palette_requests_identical'] else 1)
