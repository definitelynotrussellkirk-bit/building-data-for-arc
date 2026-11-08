from __future__ import annotations
import json, sys
from pathlib import Path
import types
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'repo'
for p in (REPO/'shared/tools', REPO/'shared/runtime', REPO/'src'):
    sys.path.insert(0,str(p))
scripts_pkg = types.ModuleType('scripts')
scripts_pkg.__path__ = [str(REPO/'shared/tools')]
sys.modules.setdefault('scripts', scripts_pkg)
from coder_synth_verify import ProgramVerifier

TASKS={'aa22818fb880','98e86aae9095'}
rows={}
for line in (REPO/'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
    row=json.loads(line)
    if row.get('task_id') in TASKS:
        rows[row['task_id']]=row

aa_grid=[[0]*7 for _ in range(7)]
aa_grid[0][0]=3
for r,c in ((3,3),(2,3),(4,3),(3,2)):
    aa_grid[r][c]=3

b_grid=[[0]*10 for _ in range(8)]
b_grid[0][0]=1
b_grid[2][1]=5
for r,c in ((3,5),(4,5),(4,6),(5,6)):
    b_grid[r][c]=5
b_grid[7][0]=5

with ProgramVerifier() as verifier:
    aa_out=verifier.apply(rows['aa22818fb880']['program_solution'],aa_grid)
    b_out=verifier.apply(rows['98e86aae9095']['program_solution'],b_grid)
report={
 'aa22818fb880': {'input':aa_grid,'authority_output':aa_out},
 '98e86aae9095': {'input':b_grid,'authority_output':b_out},
}
print(json.dumps(report,indent=2))
(ROOT/'checks/audit_counterexamples.json').write_text(json.dumps(report,indent=2)+'\n')
