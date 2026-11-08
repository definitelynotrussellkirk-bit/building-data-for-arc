from __future__ import annotations
import hashlib, importlib.util, json, sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]/'repo'
sys.path.insert(0,str(ROOT/'shared/runtime'))
TASK='bf8910eef99b'
path=ROOT/'generators'/TASK/'generator.py'
spec=importlib.util.spec_from_file_location('audit_bf',path)
gen=importlib.util.module_from_spec(spec); sys.modules[spec.name]=gen; spec.loader.exec_module(gen)

def bbox(grid):
    pts=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=0]
    return min(r for r,c in pts),min(c for r,c in pts),max(r for r,c in pts),max(c for r,c in pts)
def full_room(grid):
    r0,c0,r1,c1=bbox(grid); h=len(grid); w=len(grid[0])
    return r0>=2 and c0>=2 and h-1-r1>=2 and w-1-c1>=2

counts={}
examples=[]
for band in ('easy','medium','hard'):
    c=Counter()
    for i in range(100):
        g=gen.generate(20261008,i,difficulty=band)
        h,w=len(g),len(g[0]); c[f'{h}x{w}']+=1
        c['full_room' if full_room(g) else 'violates_room']+=1
        c['self_check_pass' if not gen.self_check(g) else 'self_check_fail']+=1
        if not full_room(g) and len(examples)<8:
            examples.append({'band':band,'seed':20261008,'sample_index':i,'input':g,'bbox':bbox(g),'self_check':gen.self_check(g)})
    counts[band]=dict(c)
# Deterministic declared-domain witness: valid advertised sizes/position/palette.
witness=gen.generate(314159,0,difficulty='easy',grid_h=4,grid_w=4,block_position='centered',palette_size=4,margin_size=2)
summary={
 'task_id':TASK,
 'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
 'rule_hash':'f45b7e9216b7',
 'sample':{'seed':20261008,'indices':'0..99','per_band':100,'counts':counts},
 'witness':{'seed':314159,'sample_index':0,'difficulty':'easy','overrides':{'grid_h':4,'grid_w':4,'block_position':'centered','palette_size':4,'margin_size':2},'input':witness,'bbox':bbox(witness),'full_two_cell_room':full_room(witness),'self_check':gen.self_check(witness)},
 'first_ordinary_violations':examples,
}
out=Path(__file__).resolve().parent
(out/'sampler_probe.json').write_text(json.dumps(summary,indent=2)+'\n')
(out/'input.json').write_text(json.dumps(witness,indent=2)+'\n')
print(json.dumps(summary['sample'],indent=2))
print('witness',json.dumps(summary['witness'],indent=2))
