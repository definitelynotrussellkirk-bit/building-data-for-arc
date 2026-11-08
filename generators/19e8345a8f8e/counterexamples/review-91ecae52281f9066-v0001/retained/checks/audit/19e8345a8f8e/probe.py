from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK_ID = '19e8345a8f8e'
ROOT = Path.cwd()
SOURCE = ROOT / 'generators' / TASK_ID / 'generator.py'
OUT = ROOT.parent / 'checks' / 'audit' / TASK_ID

spec = importlib.util.spec_from_file_location('audit_19e_generator', SOURCE)
assert spec and spec.loader
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)

def components(grid):
    h,w=len(grid),len(grid[0]); todo={(r,c) for r in range(h) for c in range(w) if grid[r][c]==1}; result=[]
    while todo:
        start=min(todo); todo.remove(start); stack=[start]; cells=[start]
        while stack:
            r,c=stack.pop()
            for n in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if n in todo: todo.remove(n); stack.append(n); cells.append(n)
        result.append(sorted(cells))
    return result

def describe(grid):
    h,w=len(grid),len(grid[0]); rows=[]
    for cells in components(grid):
        rs=[r for r,_ in cells]; cs=[c for _,c in cells]
        box=[min(rs),min(cs),max(rs),max(cs)]
        rows.append({'cells':cells,'bbox':box,'size':len(cells),
                     'nearest_border_distance':min(box[0],box[1],h-1-box[2],w-1-box[3])})
    return rows

grid=G.generate(190,0,difficulty='easy')
records=describe(grid)
report={
 'schema':'audit-19e8345a8f8e-partial-placement-v1', 'task_id':TASK_ID,
 'generator_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'generator_version':G.VERSION,
 'call':{'seed':190,'sample_index':0,'difficulty':'easy','overrides':{}},
 'input':grid, 'components':records, 'component_count':len(records),
 'documented_expected_component_count':3,
 'self_check_errors':G.self_check(grid,difficulty='easy'),
 'finding_reproduced':len(records)!=3 and G.self_check(grid,difficulty='easy')==[],
 'prior_lead':'generators/19e8345a8f8e/evidence/review_index.json (same pinned source)',
}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'input.json').write_text(json.dumps(grid,indent=2)+'\n')
(OUT/'probe.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'component_count':len(records),'self_check_errors':report['self_check_errors'],'finding_reproduced':report['finding_reproduced']}))
if not report['finding_reproduced']: raise SystemExit(1)
