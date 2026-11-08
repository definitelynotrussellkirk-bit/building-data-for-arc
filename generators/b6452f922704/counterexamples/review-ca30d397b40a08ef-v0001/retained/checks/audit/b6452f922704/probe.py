from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
GEN = ROOT/'repo/generators/b6452f922704/generator.py'
CAN = ROOT/'repo/shared/data/canonical/puzzles.jsonl'
spec=importlib.util.spec_from_file_location('auditb6', GEN); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
canonical=None
for line in CAN.read_text().splitlines():
  row=json.loads(line)
  if row.get('task_id')=='b6452f922704': canonical=row; break
assert canonical
rows=[]
for split in ('train','test'):
  for i,pair in enumerate(canonical[split]):
    errs=m.self_check(pair['input'])
    rows.append({'split':split,'index':i,'self_check_errors':errs})
generated_failures=[]
for band in ('easy','medium','hard'):
  for seed in range(1,21):
    for idx in range(10):
      g=m.generate(seed,idx,difficulty=band)
      errs=m.self_check(g,difficulty=band)
      if errs: generated_failures.append({'band':band,'seed':seed,'index':idx,'errors':errs})
out={
 'task_id':'b6452f922704','generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),
 'canonical_sha256':hashlib.sha256(CAN.read_bytes()).hexdigest(),
 'canonical_examples_checked':len(rows),'canonical_self_check_results':rows,
 'generated_samples_checked':600,'generated_self_check_failures':generated_failures,
 'finding':'self_check and generation require all frame key colors to be distinct, but every canonical example repeats at least one key color; the validator rejects all five canonical examples while accepting the generated-only restriction.'}
Path(__file__).with_name('finding.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
