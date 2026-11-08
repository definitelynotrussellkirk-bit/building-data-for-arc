from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_audit6f',HERE/'family.py'); m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m)
rows=[]; failures=[]
for seed in range(24):
  for demos in (2,3,6):
    for setting in m.SETTINGS:
      try:
        ep=m.generate(seed,setting,demos,4); cert=ep['certificate']
        rows.append({'seed':seed,'demos':demos,'setting':setting,'certificate':cert,
                     'query_setting_differences':sum(m.label(p['input'],'cumulative')!=m.label(p['input'],'final_cue_projection') for p in ep['test'])})
        if cert['surviving_settings']!=[setting] or cert['surviving_rivals'] or rows[-1]['query_setting_differences']!=4: failures.append(rows[-1])
      except Exception as e: failures.append({'seed':seed,'demos':demos,'setting':setting,'error':repr(e)})
out={'schema':'bounded-parametric-self-audit-v1','task_id':'6f6c567e365b','jobs':len(rows),'failures':failures,'rows':rows}
print(json.dumps(out,indent=2)); raise SystemExit(bool(failures))
