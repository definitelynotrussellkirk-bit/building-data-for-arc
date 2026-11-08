from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
TASK='7017b91a367d'
spec=importlib.util.spec_from_file_location(f'audit_generator_{TASK}', Path(f'generators/{TASK}/generator.py'))
assert spec and spec.loader
gen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
base_kwargs={'seed':731,'sample_index':4,'difficulty':'medium'}
cases={
 'base':{},
 'variant_0':{'variant':0},'variant_3':{'variant':3},
 'palette_default':{'palette_kind':'default'},'palette_warm':{'palette_kind':'warm'},
 'texture_default':{'texture':'default'},'texture_warm':{'texture':'warm'},
 'unknown_key':{'not_an_axis':'accepted'},
}
outputs={name:gen.generate(**base_kwargs,**ov) for name,ov in cases.items()}
source=Path(f'generators/{TASK}/generator.py')
report={
 'schema':'arc-audit-override-probe-v1','task_id':TASK,
 'generator_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'seed':731,'sample_index':4,'difficulty':'medium',
 'equalities':{
   'variant_0_equals_variant_3':outputs['variant_0']==outputs['variant_3'],
   'palette_default_equals_palette_warm':outputs['palette_default']==outputs['palette_warm'],
   'texture_default_equals_texture_warm':outputs['texture_default']==outputs['texture_warm'],
   'unknown_key_accepted':True,
 },
 'self_check_all_zero':gen.self_check([[0]*17 for _ in range(5)]),
 'all_zero_grid_accepted':gen.self_check([[0]*17 for _ in range(5)])==[],
 'output_hashes':{name:hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest() for name,grid in outputs.items()},
}
Path('../checks/audit/7017b91a367d/override-probe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2,sort_keys=True))
