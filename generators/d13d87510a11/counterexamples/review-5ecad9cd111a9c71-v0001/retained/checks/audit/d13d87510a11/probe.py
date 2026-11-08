import importlib.util,json,sys,hashlib
from pathlib import Path
repo=Path(__file__).resolve().parents[3]/'repo'
sys.path.insert(0,str(repo/'shared/runtime'))
spec=importlib.util.spec_from_file_location('audit_target',repo/'generators/d13d87510a11/generator.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
rows=[]; failure=None
for seed in range(256):
 g=m.generate(seed,0,difficulty='easy',grid_h=6,grid_w=7)
 errs=m.self_check(g)
 counts={v:sum(row.count(v) for row in g) for v in (1,2,3)}
 rows.append({'seed':seed,'sample_index':0,'difficulty':'easy','overrides':{'grid_h':6,'grid_w':7},'counts':counts,'self_check':errs})
 if errs:
  failure={'seed':seed,'sample_index':0,'difficulty':'easy','overrides':{'grid_h':6,'grid_w':7},'input':g,'self_check':errs};break
out={'checked':len(rows),'failure':failure,'counts':rows}
Path(__file__).with_name('probe.json').write_text(json.dumps(out,indent=2)+'\n')
if failure: Path(__file__).with_name('input.json').write_text(json.dumps(failure['input'])+'\n')
print(json.dumps({'checked':len(rows),'failure':failure}))
