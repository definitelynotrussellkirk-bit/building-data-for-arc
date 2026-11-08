from __future__ import annotations
import importlib.util, json
from pathlib import Path
PACKET=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
path=PACKET/'repo/generators/fb1e79984e59/generator.py'
spec=importlib.util.spec_from_file_location('g',path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
seed=1; start=2; difficulty='easy'
grids=[m.generate(seed,start+i,difficulty=difficulty) for i in range(4)]
meta=[]
for i,g in enumerate(grids):
    meta.append({'role':'demo' if i<3 else 'query','seed':seed,'sample_index':start+i,'difficulty':difficulty,'observed':m.observe_overrides(g),'self_check':m.self_check(g,difficulty=difficulty),'ring_colors':m._extract_ring_colors(g)[0]})
(OUT/'lesson_inputs.json').write_text(json.dumps(grids,indent=2)+'\n')
(OUT/'lesson_meta.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(meta,indent=2))
