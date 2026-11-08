from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]/'repo'
sys.path.insert(0,str(ROOT/'shared/runtime'))
TASK='66b8f050cbf2'
path=ROOT/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_66',path)
gen=importlib.util.module_from_spec(spec); sys.modules[spec.name]=gen; spec.loader.exec_module(gen)

def norm(grid):
    if grid and isinstance(grid[0],str): return [[int(c) for c in row] for row in grid]
    return grid

def origin_rival(g):
    h,w=len(g),len(g[0]); out=[[0]*w for _ in range(h)]
    token=g[0][0]
    dirs={1:(-1,0),2:(0,1),3:(1,0),4:(0,-1)}
    if token not in dirs: return out
    dr,dc=dirs[token]
    for r,row in enumerate(g):
        for c,v in enumerate(row):
            if v!=0 and v not in (1,2,3,4):
                nr,nc=r+dr,c+dc
                if 0<=nr<h and 0<=nc<w: out[nr][nc]=v
    return out

inputs=[]; provenance=[]
for band in ('easy','medium','hard'):
    for i in range(16):
        g=gen.generate(20261008,i,difficulty=band)
        inputs.append(g)
        commands=[(r,c,v) for r,row in enumerate(g) for c,v in enumerate(row) if v in (1,2,3,4)]
        provenance.append({'band':band,'seed':20261008,'sample_index':i,'commands':commands,'self_check':gen.self_check(g)})
# Canonical training example with command at bottom-right.
canonical=None
for line in (ROOT/'shared/data/canonical/puzzles.jsonl').open():
    row=json.loads(line)
    if row.get('task_id')==TASK:
        canonical=norm(row['train'][1]['input']); break
assert canonical is not None
inputs.append(canonical)
out=Path(__file__).resolve().parent
(out/'generated_and_canonical_inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
summary={
 'task_id':TASK,
 'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'rule_hash':'72a5cad32ba5',
 'generated':{'seed':20261008,'indices':'0..15','per_band':16,'total':48,
              'command_at_origin':sum(p['commands']==[(0,0,p['commands'][0][2])] for p in provenance if len(p['commands'])==1),
              'self_check_pass':sum(not p['self_check'] for p in provenance)},
 'canonical_counterexample_index':48,
 'canonical_counterexample_input':canonical,
 'canonical_self_check':gen.self_check(canonical),
 'provenance':provenance,
}
(out/'sampler_probe.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'rival_outputs_preapply.json').write_text(json.dumps([origin_rival(g) for g in inputs],indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='provenance'},indent=2))
