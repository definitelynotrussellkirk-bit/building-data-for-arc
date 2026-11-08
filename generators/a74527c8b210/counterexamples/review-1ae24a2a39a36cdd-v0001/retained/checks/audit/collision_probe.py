"""Reproduce the audit-only distractor overwrite; run from the library cwd."""
import importlib.util, json, hashlib
from pathlib import Path
root=Path.cwd();tid='a74527c8b210';source=root/'generators'/tid/'generator.py'
spec=importlib.util.spec_from_file_location('collision_target',source)
gen=importlib.util.module_from_spec(spec);spec.loader.exec_module(gen)
grid=gen.generate(4,0,difficulty='hard',n_pairs=5)
p=json.loads((root.parent/'checks/audit'/tid/'probe.json').read_text())
r=json.loads((root.parent/'checks/audit'/tid/'racket.json').read_text())
assert grid==p['cases'][17]['input']  # Same fully retained canonical-Racket case.
blue=sum(v==1 for row in grid for v in row)
pairs=[]
for i in range(len(grid)-1):
 for j in range(len(grid[0])-1):
  a,b,c,d=grid[i][j]==1,grid[i][j+1]==1,grid[i+1][j]==1,grid[i+1][j+1]==1
  if (a and d and not b and not c) or (b and c and not a and not d):pairs.append([i,j])
report=dict(task_id=tid,generator_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 rule_hash=r['executed_rule_hash'],seed=4,sample_index=0,difficulty='hard',overrides={'n_pairs':5},
 requested_pairs=5,observed_blue_cells=blue,observed_complete_diagonal_pairs=len(pairs),pair_origins=pairs,
 overwritten_location=[len(grid)-2,len(grid[0])-2], overwritten_value=grid[-2][-2],
 input=grid,racket_output=r['results'][17]['output'],racket_receipt='a74527c8b210/racket.json results[17]',
 validator_findings=gen.self_check(grid),
 finding='Final fixed-corner distractor placement overwrites a previously placed blue cell; one blue singleton remains.')
assert blue==9 and len(pairs)==4 and grid[-2][-2]==7
(root.parent/'checks/audit'/tid/'collision.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ('requested_pairs','observed_blue_cells','observed_complete_diagonal_pairs','overwritten_location','validator_findings')}))
