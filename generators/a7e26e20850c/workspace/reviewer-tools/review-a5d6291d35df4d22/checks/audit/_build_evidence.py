from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path.cwd()

def load(tid):
    path = ROOT / 'generators' / tid / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_'+tid, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod, path

def comps(grid):
    h,w=len(grid),len(grid[0]); seen=set(); out=[]
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r,c) in seen: continue
            stack=[(r,c)]; seen.add((r,c)); cells=[]
            while stack:
                rr,cc=stack.pop(); cells.append((rr,cc))
                for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
                    nr,nc=rr+dr,cc+dc
                    if 0<=nr<h and 0<=nc<w and grid[nr][nc] != 0 and (nr,nc) not in seen:
                        seen.add((nr,nc)); stack.append((nr,nc))
            rows={r for r,_ in cells}; cols={c for _,c in cells}
            kind='horizontal' if len(rows)==1 else ('vertical' if len(cols)==1 else 'other')
            out.append({'kind':kind,'size':len(cells),'color':grid[cells[0][0]][cells[0][1]],'cells':sorted([list(x) for x in cells])})
    return out

# cdc2954e8f80
m,p=load('cdc2954e8f80')
outdir=ROOT.parent/'checks'/'audit'/'cdc2954e8f80'; outdir.mkdir(parents=True,exist_ok=True)
semantic=[[0]*7 for _ in range(7)]
for r,c in [(1,1),(3,1),(3,5),(5,5)]: semantic[r][c]=2
cross=[[0]*7 for _ in range(7)]
cross[1][1]=2; cross[3][5]=2
base=m.generate(123,7)
alt=m.generate(123,7,palette_size=1,n_distinct_colors=1,palette_kind='warm',banana=7)
input_payload={'inputs':[semantic,cross]}
(outdir/'inputs.json').write_text(json.dumps(input_payload,indent=2)+'\n')
cdc={
  'task_id':'cdc2954e8f80',
  'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
  'semantic_witness':{
    'description':'one color supplies independent endpoint pairs in two columns; reference should fill each vertical interval only',
    'input':semantic,
    'self_check':m.self_check(semantic),
  },
  'validator_counterexample':{
    'description':'two same-color cells in different columns are not a vertical pair, yet self_check accepts them',
    'input':cross,
    'self_check':m.self_check(cross),
  },
  'override_probe':{
    'call':'generate(123, 7, palette_size=1, n_distinct_colors=1, palette_kind="warm", banana=7)',
    'unknown_override_accepted':True,
    'result_identical_to_no_overrides':base==alt,
    'base':base,
    'overridden':alt,
  },
  'source_observation':'generate only draws grid_h, grid_w, segments, and layout; palette_size, n_distinct_colors, palette_kind and unknown keys do not constrain output.',
}
(outdir/'probe.json').write_text(json.dumps(cdc,indent=2)+'\n')

# 508ae94c035c
m,p=load('508ae94c035c')
outdir=ROOT.parent/'checks'/'audit'/'508ae94c035c'; outdir.mkdir(parents=True,exist_ok=True)
g=m.generate(75,75,difficulty='hard',n_horiz=3,n_vert=3)
cs=comps(g); counts={k:sum(c['kind']==k for c in cs) for k in ('horizontal','vertical','other')}
(outdir/'input.json').write_text(json.dumps({'input':g},indent=2)+'\n')
record={
  'task_id':'508ae94c035c',
  'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
  'request':{'seed':75,'sample_index':75,'difficulty':'hard','overrides':{'n_horiz':3,'n_vert':3}},
  'advertised_expectation':{'horizontal':3,'vertical':3},
  'observed_counts':counts,
  'components':cs,
  'self_check':m.self_check(g,difficulty='hard'),
  'grid':g,
  'reproducible_failure':'the third vertical placement exhausts 40 attempts; generate silently continues with 2 vertical objects, and self_check does not check requested counts.',
}
(outdir/'silent-shortening.json').write_text(json.dumps(record,indent=2)+'\n')
