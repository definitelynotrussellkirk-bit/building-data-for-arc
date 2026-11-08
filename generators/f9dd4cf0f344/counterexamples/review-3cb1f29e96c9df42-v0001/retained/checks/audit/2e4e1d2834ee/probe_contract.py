from __future__ import annotations
import hashlib, json, os, sys
from pathlib import Path
from reviewer_support import find_root, load_selected_generator

TASK_ID='2e4e1d2834ee'
root=find_root(__file__)
gen,path,sha=load_selected_generator(TASK_ID,root=root)
probes=[]
for label,args,kwargs in [
    ('control',(17,0),{}),
    ('grid_h_4',(17,0),{'grid_h':4}),
    ('grid_w_4',(17,0),{'grid_w':4}),
    ('both_10',(17,0),{'grid_h':10,'grid_w':10}),
    ('n_panels_invalid',(17,0),{'n_panels':99}),
    ('unknown_axis',(17,0),{'unknown_axis':1}),
    ('bool_seed',(True,0),{}),
    ('negative_sample',(17,-1),{}),
]:
    try:
        grid=gen.generate(*args,**kwargs)
        compact=json.dumps(grid,separators=(',',':'))
        probes.append({'label':label,'args':list(args),'kwargs':kwargs,'status':'accepted',
          'shape':[len(grid),len(grid[0])],
          'grid_sha256':hashlib.sha256(compact.encode()).hexdigest(),
          'grid':grid,
          'dividers':[c for c in range(len(grid[0])) if all(row[c]==9 for row in grid)],
          'self_check':gen.self_check(grid)})
    except Exception as exc:
        probes.append({'label':label,'args':list(args),'kwargs':kwargs,'status':'rejected',
          'error':f'{type(exc).__name__}: {exc}'})
control=next(row for row in probes if row['label']=='control')
for row in probes:
    if row.get('status')=='accepted':
        row['same_grid_as_control']=row['grid_sha256']==control['grid_sha256']
print(json.dumps({'schema':'audit-generator-contract-probe-v2','task_id':TASK_ID,
 'generator_path':path.relative_to(root).as_posix(),'generator_sha256':sha,
 'version':getattr(gen,'VERSION',None),'axes':getattr(gen,'AXES',None),
 'command':[sys.executable,*sys.argv],'cwd':str(Path.cwd()),
 'pythonhashseed':os.environ.get('PYTHONHASHSEED'),'probes':probes},indent=2,sort_keys=True))
