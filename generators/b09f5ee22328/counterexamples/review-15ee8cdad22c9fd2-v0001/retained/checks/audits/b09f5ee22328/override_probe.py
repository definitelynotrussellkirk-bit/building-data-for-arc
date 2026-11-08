#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, pathlib
from collections import Counter
ROOT=pathlib.Path(__file__).resolve().parents[3]
PATH=ROOT/'repo/generators/b09f5ee22328/generator.py'
EXPECTED='ba01ba2ce4e55bcfd063a0b804bbd417331fe17af7a393412a9af75f19a5e3d0'
actual=hashlib.sha256(PATH.read_bytes()).hexdigest()
assert actual==EXPECTED
spec=importlib.util.spec_from_file_location('b09_audit',PATH); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
def mode(g):
 c=Counter(v for row in g for v in row); return max(c,key=c.get)
rows=[]
for band in ('easy','medium','hard'):
 for requested in (3,4,5):
  for seed in range(10):
   g=m.generate(5000+seed,40+seed,difficulty=band,grid_size=requested)
   rows.append({'axis':'grid_size','band':band,'requested':requested,'seed':seed,'observed':len(g),'match':len(g)==requested})
 for requested in range(10):
  for seed in range(10):
   g=m.generate(6000+seed,60+seed,difficulty=band,mode_color=requested)
   observed=mode(g)
   rows.append({'axis':'mode_color','band':band,'requested':requested,'seed':seed,'observed':observed,'match':observed==requested})
unknown_accepted=True
try: m.generate(1,1,not_an_axis=7)
except Exception: unknown_accepted=False
summary={}
for axis in ('grid_size','mode_color'):
 subset=[r for r in rows if r['axis']==axis]
 summary[axis]={'cases':len(subset),'exact':sum(r['match'] for r in subset),'mismatches':[r for r in subset if not r['match']][:12]}
report={'schema':'b09f5ee22328-override-audit-v1','task_id':m.TASK_ID,'generator_sha256':actual,'summary':summary,'unknown_override_accepted':unknown_accepted,'source_observation':'minority_layout and helpful texture values are declared but the ordinary generate path never calls _layout_positions or reads those values.'}
out=pathlib.Path(__file__).with_name('override_probe.json');out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps(report,indent=2))
