from __future__ import annotations
import importlib.util, json
from pathlib import Path
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[2] / 'repo'


def load(task):
    path = ROOT / 'generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + task, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def comps(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r0 in range(h):
        for c0 in range(w):
            color=grid[r0][c0]
            if color==0 or (r0,c0) in seen: continue
            st=[(r0,c0)]; seen.add((r0,c0)); cells=[]
            while st:
                r,c=st.pop(); cells.append((r,c))
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    rr,cc=r+dr,c+dc
                    if 0<=rr<h and 0<=cc<w and (rr,cc) not in seen and grid[rr][cc]==color:
                        seen.add((rr,cc)); st.append((rr,cc))
            out.append({'color':color,'cells':cells})
    return out

report={}
# Contract counterexample: most advertised overrides are ignored.
g=load('9339b47bb5d5')
requested={'grid_h':18,'grid_w':20,'seed_count':1,'palette_size':1,'n_distinct_colors':1}
grid=g.generate(117,5,difficulty='easy',**requested)
seeds=[(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,5)]
report['9339b47bb5d5']={
    'seed':117,'sample_index':5,'difficulty':'easy','requested':requested,
    'observed':{'grid_h':len(grid),'grid_w':len(grid[0]),'seed_count':len(seeds),'n_distinct_colors':len({v for _,_,v in seeds})},
    'self_check':g.self_check(deepcopy(grid)),'input':grid,
}

# Semantic counterexample: generated motifs collide in a quadrant; selected rule keeps only first.
g=load('9c0ccdf0d414')
found=None
for seed in range(100):
  for index in range(20):
    grid=g.generate(seed,index,difficulty=None)
    h,w=len(grid),len(grid[0]); groups={q:[] for q in ('tl','tr','bl','br')}
    for comp in comps(grid):
        cells=comp['cells']; top=2*sum(r for r,_ in cells)<len(cells)*(h-1); left=2*sum(c for _,c in cells)<len(cells)*(w-1)
        q=('t' if top else 'b')+('l' if left else 'r')
        groups[q].append(comp['color'])
    collisions={q:cs for q,cs in groups.items() if len(cs)>1}
    if collisions:
        found=(seed,index,grid,groups,collisions,g.self_check(deepcopy(grid)))
        break
  if found: break
assert found
seed,index,grid,groups,collisions,check=found
report['9c0ccdf0d414']={'seed':seed,'sample_index':index,'difficulty':None,'quadrant_colors':groups,'collisions':collisions,'self_check':check,'input':grid}

out=Path(__file__).with_name('audit_probe_inputs.json')
out.write_text(json.dumps(report,indent=2)+'\n')
print(out)
print(json.dumps({k:{x:v for x,v in d.items() if x!='input'} for k,d in report.items()},indent=2))
