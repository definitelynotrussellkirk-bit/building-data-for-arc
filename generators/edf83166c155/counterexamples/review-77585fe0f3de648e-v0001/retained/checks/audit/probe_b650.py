from __future__ import annotations
import collections
import importlib.util
import json
from pathlib import Path

PATH=Path('generators/b650a355848c/generator.py')
spec=importlib.util.spec_from_file_location('audit_b650',PATH)
g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)

def analyze(grid):
    comps=g._components(grid)
    shapes=[]; markers=[]
    for cells in comps:
        r,c=next(iter(cells)); v=grid[r][c]
        if v==6:
            rs=[x for x,_ in cells]; cs=[y for _,y in cells]
            shapes.append({'cells':sorted(cells),'bbox':[min(rs),max(rs),min(cs),max(cs)]})
        elif len(cells)==1:
            r,c=next(iter(cells)); markers.append({'row':r,'col':c,'color':v})
    rows=[]
    for si,shape in enumerate(shapes):
        r1,r2,c1,c2=shape['bbox']; ds=[]
        for mi,m in enumerate(markers):
            mr,mc=m['row'],m['col']
            dr=0 if r1<=mr<=r2 else min(abs(mr-r1),abs(mr-r2))
            dc=0 if c1<=mc<=c2 else min(abs(mc-c1),abs(mc-c2))
            ds.append({'distance':dr+dc,'marker_index':mi,**m})
        best=min(x['distance'] for x in ds)
        winners=[x for x in ds if x['distance']==best]
        rows.append({'shape_index':si,'bbox':shape['bbox'],'distances':ds,'nearest':winners})
    chosen=[row['nearest'][0]['marker_index'] for row in rows]
    return shapes,markers,rows,chosen

counts=collections.Counter(); first={}
for band in [None,'easy','medium','hard']:
  for seed in range(100):
    for idx in range(20):
      try:
        grid=g.generate(seed,idx,difficulty=band)
      except Exception as exc:
        counts['generation_error']+=1
        first.setdefault('generation_error',{'band':band,'seed':seed,'sample_index':idx,'error':repr(exc)})
        continue
      shapes,markers,rows,chosen=analyze(grid)
      counts['samples']+=1
      if any(len(row['nearest'])>1 for row in rows):
        counts['nearest_tie']+=1
        first.setdefault('nearest_tie',{'band':band,'seed':seed,'sample_index':idx,'input':grid,'self_check':g.self_check(grid),'markers':markers,'shape_distances':rows,'chosen_marker_indices':chosen})
      if len(set(chosen))<len(chosen):
        counts['duplicate_marker_choice']+=1
        first.setdefault('duplicate_marker_choice',{'band':band,'seed':seed,'sample_index':idx,'input':grid,'self_check':g.self_check(grid),'markers':markers,'shape_distances':rows,'chosen_marker_indices':chosen})
      if set(chosen)!=set(range(len(markers))):
        counts['non_bijection']+=1
        first.setdefault('non_bijection',{'band':band,'seed':seed,'sample_index':idx,'input':grid,'self_check':g.self_check(grid),'markers':markers,'shape_distances':rows,'chosen_marker_indices':chosen})
result={'task_id':'b650a355848c','domain':{'bands':['default','easy','medium','hard'],'seeds':'0..99','sample_indices':'0..19'},'counts':dict(counts),'first':first}
print(json.dumps(result,indent=2))
