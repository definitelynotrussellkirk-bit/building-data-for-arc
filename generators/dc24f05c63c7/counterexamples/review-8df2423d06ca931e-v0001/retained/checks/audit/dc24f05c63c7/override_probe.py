#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, time
from pathlib import Path
TASK='dc24f05c63c7'
ROOT=Path(__file__).resolve().parents[3]
GEN=ROOT/'repo/generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_dc_gen',GEN); gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
fail=[]; checked=0; t=time.time()
for h,w in ((11,15),(16,24)):
  for sb in range(8):
    for tb in range(8):
      for q in gen._QUADRANTS:
        for kind in gen._MOTIF_KINDS:
          ov={'grid_h':h,'grid_w':w,'source_basis':sb,'target_basis':tb,'motif_quadrant':q,'motif_kind':kind}
          try:
            g=gen.generate(12345+checked, checked, difficulty='hard', **ov)
            obs=gen.observe_overrides(g); errs=gen.self_check(g)
            if obs!=ov or errs: fail.append({'overrides':ov,'observed':obs,'errors':errs})
          except Exception as e:
            fail.append({'overrides':ov,'exception':type(e).__name__+': '+str(e)})
          checked+=1
out={'schema':'audit_dc_overrides/1','task_id':TASK,'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),'checked':checked,'failures':fail,'elapsed_seconds':round(time.time()-t,3)}
path=ROOT/'checks/audit'/TASK/'override_probe.json'; path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps({'checked':checked,'failure_count':len(fail),'elapsed_seconds':out['elapsed_seconds'],'out':str(path)}))
raise SystemExit(1 if fail else 0)
