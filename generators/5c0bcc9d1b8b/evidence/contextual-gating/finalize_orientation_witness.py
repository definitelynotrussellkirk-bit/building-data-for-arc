from __future__ import annotations
import copy, hashlib, json
from pathlib import Path

def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()

def always_horizontal(grid):
    h,w=len(grid),len(grid[0]); cr=h//2; cc=w//2
    count=sum(x==5 for row in grid for x in row)
    out=[[7]*w for _ in range(h)]
    for c in range(w): out[cr-1][c]=out[cr+1][c]=0
    for r in range(h): out[r][cc]=0
    start=cc-count//2
    for c in range(start,start+count): out[cr][c]=5
    return out

def always_vertical(grid):
    h,w=len(grid),len(grid[0]); cr=h//2; cc=w//2
    count=sum(x==5 for row in grid for x in row)
    out=[[7]*w for _ in range(h)]
    for r in range(h): out[r][cc-1]=out[r][cc+1]=0
    for c in range(w): out[cr][c]=0
    start=cr-count//2
    for r in range(start,start+count): out[r][cc]=5
    return out

root=Path(__file__).resolve().parent
request=json.loads((root/'orientation-request.json').read_text())
receipt=json.loads((root/'orientation-racket.json').read_text())
rows=[]
for meta,result in zip(request['records'],receipt['results']):
    truth=result['output']; grid=meta['input']
    ah=always_horizontal(grid); av=always_vertical(grid)
    rows.append({
      'scene_profile':meta['scene_profile'],
      'input_sha256':result['input_sha256'],
      'racket_output_sha256':result['output_sha256'],
      'always_horizontal_matches':ah==truth,
      'always_vertical_matches':av==truth,
      'always_horizontal_sha256':grid_hash(ah),
      'always_vertical_sha256':grid_hash(av),
    })
report={
 'schema':'arcpuzzles-curriculum-witness-v1',
 'task_id':request['task_id'],
 'axis':'contextual_gating',
 'generator_sha256':request['generator_sha256'],
 'executed_rule_hash':receipt['executed_rule_hash'],
 'witness':'Parallel divider orientation gates whether reconstruction and the gray output line are vertical or horizontal.',
 'rival':'An always-horizontal rule fits the horizontal case but fails the vertical case; always-vertical has the converse failure.',
 'records':rows,
 'passed': rows[0]['always_vertical_matches'] and not rows[0]['always_horizontal_matches'] and rows[1]['always_horizontal_matches'] and not rows[1]['always_vertical_matches'],
 'limits':'Two exact production profiles demonstrate the gate; this is not an exhaustive semantic proof.'
}
(root/'orientation-gating.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(0 if report['passed'] else 1)
