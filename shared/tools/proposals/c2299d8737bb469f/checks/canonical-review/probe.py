import json,sys,importlib.util,hashlib
from pathlib import Path
root=Path('/workspace/scratch/b1624dafaa34/arc-review/WORK/repo')
sys.path.insert(0,str(root/'shared/runtime'))
p=root/'generators/c5f62271ea44/generator.py'
spec=importlib.util.spec_from_file_location('g',p);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
rows=[]
for line in (root/'shared/data/canonical/puzzles.jsonl').open():
 if 'c5f62271ea44' not in line: continue
 row=json.loads(line)
 if row['task_id']=='c5f62271ea44':rows.append(row)
print('row keys',list(rows[0]))
for row in rows:
 print('task keys',[(k,type(v).__name__) for k,v in row.items() if k!='program_solution'])
 task=row.get('task',row.get('puzzle',row))
 for split in ['train','test']:
  for pair in task.get(split,[]):
   a=g._analyze(pair['input']);print({k:a[k] for k in ['height','width','panel_h','panel_w','corners','signature','symmetry','key_side','profile_kind']})
