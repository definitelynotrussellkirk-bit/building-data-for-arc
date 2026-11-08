from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]/'repo'
TASK='8114be8704cc'
path=ROOT/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audited_generator',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
seed=1; sample_index=0; difficulty=None
grid=module.generate(seed,sample_index,difficulty=difficulty)
variants={
    'baseline':grid,
    'palette_kind_warm':module.generate(seed,sample_index,difficulty=difficulty,palette_kind='warm'),
    'palette_kind_cool':module.generate(seed,sample_index,difficulty=difficulty,palette_kind='cool'),
    'anchor_corner_true':module.generate(seed,sample_index,difficulty=difficulty,anchor_corner=True),
    'asymmetry_force_true':module.generate(seed,sample_index,difficulty=difficulty,asymmetry_force=True),
    'n_distinct_colors_varied':module.generate(seed,sample_index,difficulty=difficulty,n_distinct_colors='varied'),
}
report={
 'task_id':TASK,'seed':seed,'sample_index':sample_index,'difficulty':difficulty,
 'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'shape':[len(grid),len(grid[0])],
 'colors':sorted({v for row in grid for v in row}),
 'counts':{str(c):sum(v==c for row in grid for v in row) for c in sorted({v for row in grid for v in row})},
 'self_check':module.self_check(grid),
 'variant_equal_to_baseline':{name:(value==grid) for name,value in variants.items()},
 'input':grid,
 'claim':'Generator samples 7 and 9 from its seed palette, but the canonical rule classifies 1,7,9 as walls.',
}
out=Path(__file__).with_name('probe.json')
out.write_text(json.dumps(report,indent=2)+'\n')
Path(__file__).with_name('input.json').write_text(json.dumps(grid,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('task_id','seed','shape','colors','counts','self_check','variant_equal_to_baseline')},indent=2))
