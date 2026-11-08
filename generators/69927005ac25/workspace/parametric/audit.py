from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_audit699',HERE/'family.py'); m=importlib.util.module_from_spec(s); sys.modules[s.name]=m; s.loader.exec_module(m)
rows=[]; failures=[]
for seed in range(24):
  for demos in (2,3,6):
    for setting in m.SETTINGS:
      try:
        ep=m.generate(seed,setting,demos,4); cert=ep['certificate']
        second_unique=sum(m.label(p['input'],1)!=m.label(p['input'],2) for p in ep['test'])
        closure_unique=sum(m.label(p['input'],2)!=m.closure(p['input']) for p in ep['test'])
        row={'seed':seed,'demos':demos,'setting':setting,'certificate':cert,'query_second_unique':second_unique,'query_closure_unique':closure_unique}
        rows.append(row)
        if cert['surviving_settings']!=[setting] or cert['surviving_rivals'] or second_unique!=4 or closure_unique!=4: failures.append(row)
      except Exception as e: failures.append({'seed':seed,'demos':demos,'setting':setting,'error':repr(e)})
out={'schema':'bounded-parametric-self-audit-v1','task_id':'69927005ac25','jobs':len(rows),'failures':failures,'rows':rows}
print(json.dumps(out,indent=2)); raise SystemExit(bool(failures))
