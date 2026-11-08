#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import find_root

TASK_ID='164c36937aa9'
repo=find_root(__file__)
path=repo/'generators'/TASK_ID/'generator.py'
spec=importlib.util.spec_from_file_location('audit_164',path)
module=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(module)
baseline=module.generate(17,0,difficulty='easy')
baseline_sha=hashlib.sha256(json.dumps(baseline,separators=(',',':')).encode()).hexdigest()
probes={
 'grid_h':8,
 'grid_w':9,
 'n_anchors':4,
 'palette_kind':'warm',
 'palette_size':6,
 'position_bias':'prototype_with_anchors',
 'n_distinct_colors':6,
 'density':'sparse',
 'texture':'cool',
 'texture_degenerate':'no_prototype',
}
rows=[]
for name,value in probes.items():
    kwargs={'texture':value} if name.startswith('texture') else {name:value}
    try:
        grid=module.generate(17,0,difficulty='easy',**kwargs)
        palette=sorted({v for row in grid for v in row})
        rows.append({
            'probe':name,'kwargs':kwargs,'status':'returned','shape':[len(grid),len(grid[0])],
            'palette':palette,'grid_sha256':hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest(),'equals_baseline':grid==baseline,'self_check_without_meta':module.self_check(grid),
            'self_check_with_requested_texture_meta':module.self_check(grid,meta={'texture':value}) if name.startswith('texture') else None,
        })
    except Exception as exc:
        rows.append({'probe':name,'kwargs':kwargs,'status':'raised','exception_type':type(exc).__name__,'message':str(exc)})
report={
 'schema':'164c36937aa9-advertised-axis-probe-v1',
 'task_id':TASK_ID,
 'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'seed':17,'sample_index':0,'difficulty':'easy','baseline_grid_sha256':baseline_sha,'results':rows,
}
out=Path(__file__).with_name('override_probe.json')
out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,sort_keys=True))
