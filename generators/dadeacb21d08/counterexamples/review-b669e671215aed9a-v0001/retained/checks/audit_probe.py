from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path
ROOT=Path.cwd()

def load(t):
 p=ROOT/'generators'/t/'generator.py'
 spec=importlib.util.spec_from_file_location('g_'+t,p)
 m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
 return m,p

def freeze(g): return tuple(tuple(r) for r in g)

def canonical(t):
 for line in (ROOT/'shared/data/canonical/puzzles.jsonl').open():
  row=json.loads(line)
  if row.get('task_id')==t: return row
 raise KeyError(t)

# c813 override/validator evidence
m,p=load('c8138b7e476c')
g3=m.generate(123,4,grid_h=3)
g19=m.generate(123,4,grid_h=19)
unknown=m.generate(123,4,__typo_axis__='ignored')
asym=[[1,0,0],[9,9,9],[0,0,0],[0,0,0],[0,0,0]]
out={
 'task_id':'c8138b7e476c',
 'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'declared_axes':m.AXES,
 'override_probe':{
   'seed':123,'sample_index':4,
   'grid_h_3_returned_shape':[len(g3),len(g3[0])],
   'grid_h_19_returned_shape':[len(g19),len(g19[0])],
   'grids_equal':g3==g19,
   'unknown_key_accepted':bool(unknown),
 },
 'validator_probe':{
   'input':asym,
   'self_check':m.self_check(asym),
   'equal_rows_around_separator':False,
 },
}
Path('../checks/audit/c8138b7e476c/probe.json').write_text(json.dumps(out,indent=2)+'\n')

# dade canonical acceptance + generated branch evidence
m,p=load('dadeacb21d08'); row=canonical('dadeacb21d08')
pairs=list(row['train'])+(row['test'] if isinstance(row['test'],list) else [row['test']])
canon_checks=[m.self_check(pair['input']) for pair in pairs]

def red_components(grid):
 h,w=len(grid),len(grid[0]); seen=set(); comps=[]
 for r in range(h):
  for c in range(w):
   if grid[r][c]!=2 or (r,c) in seen: continue
   stack=[(r,c)];seen.add((r,c)); cells=[]
   while stack:
    rr,cc=stack.pop();cells.append((rr,cc))
    for nr,nc in ((rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)):
     if 0<=nr<h and 0<=nc<w and grid[nr][nc]==2 and (nr,nc) not in seen:
      seen.add((nr,nc));stack.append((nr,nc))
   comps.append(cells)
 return comps

def is_l(comp):
 rs=[r for r,c in comp];cs=[c for r,c in comp]
 return len(comp)==3 and max(rs)-min(rs)+1==2 and max(cs)-min(cs)+1==2
counts={'draws':0,'red_components':0,'target_l':0,'non_l_red':0,'failed_self_check':0}
examples=[]
for band in (None,'easy','medium','hard'):
 for i in range(100):
  try:
   g=m.generate(7000+i,i,difficulty=band)
  except Exception as e:
   examples.append({'band':band,'i':i,'generation_error':f'{type(e).__name__}: {e}'})
   continue
  counts['draws']+=1
  cs=red_components(g)
  counts['red_components']+=len(cs)
  counts['target_l']+=sum(is_l(c) for c in cs)
  counts['non_l_red']+=sum(not is_l(c) for c in cs)
  counts['failed_self_check']+=bool(m.self_check(g))
out={
 'task_id':'dadeacb21d08',
 'generator_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'canonical_pairs':len(pairs),
 'canonical_self_check_results':canon_checks,
 'canonical_rejected':sum(bool(x) for x in canon_checks),
 'default_census':counts,
 'generation_errors':examples[:20],
}
Path('../checks/audit/dadeacb21d08/probe.json').write_text(json.dumps(out,indent=2)+'\n')
