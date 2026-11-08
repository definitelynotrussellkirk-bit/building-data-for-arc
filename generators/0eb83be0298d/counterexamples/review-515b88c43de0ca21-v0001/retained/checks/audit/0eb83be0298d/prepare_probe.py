#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

TASK='0eb83be0298d'; BANDS=('easy','medium','hard'); PER_BAND=20
ROOT=Path(__file__).resolve().parents[3]
GEN=ROOT/'repo'/'generators'/TASK/'generator.py'
OUT=ROOT/'checks'/'audit'/TASK

def seed_for(band,i):
    return int(hashlib.sha256(f'audit-template-free:v1:{TASK}:{band}:{i}'.encode()).hexdigest()[:8],16)

def sha(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def component_corner_rival(grid):
    h,w=len(grid),len(grid[0])
    divs=[c for c in range(w) if all(grid[r][c]==9 for r in range(h))]
    if not divs: raise ValueError('no full-9 divider')
    dc=divs[0]; board=[row[dc+1:] for row in grid]
    bh,bw=len(board),len(board[0]); out=[[0]*bw for _ in range(bh)]
    seen=set()
    for r in range(bh):
      for c in range(bw):
        if board[r][c] in (0,9) or (r,c) in seen: continue
        color=board[r][c]; todo=[(r,c)]; seen.add((r,c)); cells=[]
        while todo:
          x,y=todo.pop(); cells.append((x,y))
          for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if 0<=nx<bh and 0<=ny<bw and (nx,ny) not in seen and board[nx][ny]==color:
              seen.add((nx,ny)); todo.append((nx,ny))
        out[max(x for x,_ in cells)][max(y for _,y in cells)]=8
    return out

spec=importlib.util.spec_from_file_location('audit_target_'+TASK,GEN)
if spec is None or spec.loader is None: raise ImportError(GEN)
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
inputs=[]; rivals=[]; cases=[]; errors=[]
for band in BANDS:
  for i in range(PER_BAND):
    seed=seed_for(band,i); si=i
    try:
      grid=gen.generate(seed,si,difficulty=band)
      findings=gen.self_check(grid,difficulty=band)
      if findings: raise ValueError(f'self_check: {findings}')
      rival=component_corner_rival(grid)
      inputs.append(grid); rivals.append(rival)
      cases.append({'index':len(inputs)-1,'band':band,'lesson_index':i,'seed':seed,'sample_index':si,'input_sha256':sha(grid),'rival_output_sha256':sha(rival)})
    except Exception as exc:
      errors.append({'band':band,'lesson_index':i,'seed':seed,'sample_index':si,'error':f'{type(exc).__name__}: {exc}'})

canonical=None
for line in (ROOT/'repo'/'shared'/'data'/'canonical'/'puzzles.jsonl').read_text().splitlines():
    row=json.loads(line)
    if row.get('task_id')==TASK:
      canonical=row['train'][0]['input']; break
if canonical is None: raise RuntimeError('canonical row not found')
canonical=[[int(ch) for ch in row] if isinstance(row,str) else list(row) for row in canonical]
canonical_rival=component_corner_rival(canonical)
(OUT/'generated_inputs.json').write_text(json.dumps({'inputs':inputs},indent=2)+'\n')
(OUT/'generated_rivals.json').write_text(json.dumps({'outputs':rivals},indent=2)+'\n')
(OUT/'canonical_input.json').write_text(json.dumps({'input':canonical},indent=2)+'\n')
(OUT/'canonical_rival.json').write_text(json.dumps({'output':canonical_rival},indent=2)+'\n')
report={'schema':'arcpuzzles-template-free-shortcut-prep-v1','task_id':TASK,'generator_sha256':hashlib.sha256(GEN.read_bytes()).hexdigest(),'seed_recipe':"sha256('audit-template-free:v1:TASK:BAND:INDEX')[:8]",'rival':'ignore template; split board into same-colour 4-connected components; mark each component bounding-box bottom-right corner','counts':{'requested':len(BANDS)*PER_BAND,'prepared':len(inputs),'errors':len(errors)},'cases':cases,'errors':errors,'canonical_input_sha256':sha(canonical),'canonical_rival_sha256':sha(canonical_rival)}
(OUT/'probe_preparation.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(f"prepared={len(inputs)} errors={len(errors)} generator={report['generator_sha256']}")
raise SystemExit(2 if errors else 0)
