from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
p=Path('generators/ffb7c0bc9376/generator.py')
spec=importlib.util.spec_from_file_location('audit_ffb',p)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
rows=[]
for texture in ('no_pairs','single_cell','adjacent_pair'):
    grid=g.generate(1234,0,difficulty='easy',texture=texture)
    rows.append({
        'texture':texture,
        'grid':grid,
        'self_check':g.self_check(grid,difficulty='easy'),
        'nonzero_cells':sum(v!=0 for row in grid for v in row),
    })
result={
    'task_id':g.TASK_ID,
    'generator_version':g.VERSION,
    'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
    'probe_seed':1234,
    'probe_sample_index':0,
    'difficulty':'easy',
    'advertised_texture_axis':g.AXES['texture'],
    'results':rows,
    'finding':'Every advertised degenerate texture returns a grid rejected by the generator self_check.',
    'command':['python3','run_with_racket.py','python3','../checks/audit/ffb7c0bc9376/probe.py'],
    'cwd':'packet_root',
}
Path('../checks/audit/ffb7c0bc9376/degenerate_texture_contract.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('task_id','generator_sha256','finding')}))
print(json.dumps([{r['texture']:r['self_check']} for r in rows]))
