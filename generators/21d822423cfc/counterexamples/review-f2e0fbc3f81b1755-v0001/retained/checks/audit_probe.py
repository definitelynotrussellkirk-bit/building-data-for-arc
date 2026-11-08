"""Findings-only audit reproduction; never edits either audit target."""
from collections import deque
from pathlib import Path
import hashlib, importlib.util, json

ROOT=Path.cwd()  # wrapper runs from repo
OUT=ROOT.parent/'checks/audit';OUT.mkdir(exist_ok=True)

def load(task):
    path=ROOT/'generators'/task/'generator.py'
    spec=importlib.util.spec_from_file_location('audit_'+task,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod,hashlib.sha256(path.read_bytes()).hexdigest()

def flood(grid,distinct):
    out=[row[:] for row in grid];h=len(grid);w=len(grid[0]);seen=set()
    for r in range(h):
        for c in range(w):
            if grid[r][c]==5 or (r,c) in seen:continue
            todo=deque([(r,c)]);seen.add((r,c));cells=[]
            while todo:
                p=todo.popleft();cells.append(p)
                for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1)):
                    y,x=q
                    if 0<=y<h and 0<=x<w and grid[y][x]!=5 and q not in seen:
                        seen.add(q);todo.append(q)
            seeds=[grid[y][x] for y,x in cells if grid[y][x] in (1,2,3)]
            decision=set(seeds) if distinct else seeds
            if len(decision)==1:
                for y,x in cells:
                    if out[y][x]==0:out[y][x]=seeds[0]
    return out

a,sha=load('21d822423cfc')
found=None
for seed in range(1000):
    grids=[a.generate(seed,i,difficulty='medium') for i in range(4)]
    true=[flood(g,True) for g in grids];rival=[flood(g,False) for g in grids]
    if all(true[i]==rival[i] for i in range(3)) and true[3]!=rival[3]:
        found={'task_id':a.TASK_ID,'generator_sha256':sha,'seed':seed,'sample_indices':[0,1,2,3],
               'difficulty':'medium','overrides':{},'assembly':'three consecutive demos, then one query',
               'rival':'fill only when a chamber has exactly one seed CELL, rather than one distinct seed color',
               'self_check':[a.self_check(g) for g in grids],
               'profiles':[a.observe_overrides(g) for g in grids],
               'input_grids':grids,'python_expected':true,'rival_outputs':rival,
               'authority_status':'pending public Racket apply verification'}
        break
if found is None: raise RuntimeError('no ambiguity in bounded search')
p=OUT/a.TASK_ID;p.mkdir(exist_ok=True)
(p/'input.json').write_text(json.dumps(found['input_grids'])+'\n')
(p/'probe.json').write_text(json.dumps(found,indent=2)+'\n')
print('Audit A found:',seed,found['profiles'])

b,sha=load('f7ad176a9a24')
controls=dict(grid_h=28,grid_w=28,n_match=5,n_other=6)
g=b.generate(0,0,difficulty='medium',**controls)
p=OUT/b.TASK_ID;p.mkdir(exist_ok=True)
(p/'input.json').write_text(json.dumps(g)+'\n')
(p/'probe.json').write_text(json.dumps({'task_id':b.TASK_ID,'generator_sha256':sha,
    'seed':0,'sample_index':0,'difficulty':'medium','overrides':controls,
    'returned_shape':[len(g),len(g[0])],'self_check':b.self_check(g),
    'input_grid':g,'rival_output':[[2 if v==1 else v for v in row] for row in g],
    'finding':'advertised exact dimensions and object counts ignored',
    'authority_status':'pending public Racket apply verification'},indent=2)+'\n')
print('Audit B requested 28x28, got:',len(g),len(g[0]),'validator',b.self_check(g))
