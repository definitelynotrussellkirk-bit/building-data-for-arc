#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK='017f1406edaf'

def components(grid):
    h,w=len(grid),len(grid[0]);seen=set();out=[]
    for r in range(h):
      for c in range(w):
        if grid[r][c]==0 or (r,c) in seen: continue
        color=grid[r][c]; stack=[(r,c)];seen.add((r,c));cells=[]
        while stack:
          rr,cc=stack.pop();cells.append((rr,cc))
          for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)):
            nr,nc=rr+dr,cc+dc
            if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
              seen.add((nr,nc));stack.append((nr,nc))
        out.append({'color':color,'cells':tuple(sorted(cells))})
    return out

def eligible(grid):
    return [x for x in components(grid) if x['color']!=1 and all(r!=0 for r,c in x['cells'])]

def paint(grid,obj):
    out=[[0 for _ in row] for row in grid]
    if obj:
      for r,c in obj['cells']: out[r][c]=8
    return out

def intended(grid):
    k=sum(v==1 for v in grid[0])
    return paint(grid,next((x for x in eligible(grid) if len(x['cells'])==k),None))

def bbox(x):
    rs=[r for r,c in x['cells']]; cs=[c for r,c in x['cells']]
    return min(rs),min(cs),max(rs),max(cs)

def choose(grid,key,reverse=False,index=0):
    xs=sorted(eligible(grid), key=key, reverse=reverse)
    return paint(grid, xs[index] if xs else None)

RIVALS={
 'first_row_major': lambda g: paint(g, eligible(g)[0] if eligible(g) else None),
 'last_row_major': lambda g: paint(g, eligible(g)[-1] if eligible(g) else None),
 'min_color': lambda g: choose(g,lambda x:(x['color'],bbox(x))),
 'max_color': lambda g: choose(g,lambda x:(x['color'],bbox(x)),reverse=True),
 'smallest_area': lambda g: choose(g,lambda x:(len(x['cells']),bbox(x))),
 'largest_area': lambda g: choose(g,lambda x:(len(x['cells']),bbox(x)),reverse=True),
 'topmost': lambda g: choose(g,lambda x:(bbox(x)[0],bbox(x)[1])),
 'bottommost': lambda g: choose(g,lambda x:(bbox(x)[2],bbox(x)[1]),reverse=True),
 'leftmost': lambda g: choose(g,lambda x:(bbox(x)[1],bbox(x)[0])),
 'rightmost': lambda g: choose(g,lambda x:(bbox(x)[3],bbox(x)[0]),reverse=True),
}

def main():
 root=find_root(__file__);gen,source,digest=load_selected_generator(TASK,root=root)
 canon=canonical_pairs(TASK,root=root,labeled_only=True)
 trains=[p for p in canon if p.get('split')=='train']
 canonical={name:{'train_fit':sum(fn(p['input'])==p['output'] for p in trains),'train_total':len(trains),
                  'all_fit':sum(fn(p['input'])==p['output'] for p in canon),'all_total':len(canon)} for name,fn in RIVALS.items()}
 survivors=[]; counts={name:0 for name in RIVALS}; checked=0
 for band in ('easy','medium','hard'):
  for seed in range(300):
   grids=[gen.generate(seed,i,difficulty=band) for i in range(12)]
   pairs=[{'input':g,'output':intended(g)} for g in grids]
   for start in range(8):
    checked+=1; demos=pairs[start:start+4]; query=pairs[start+4]
    for name,fn in RIVALS.items():
      if all(fn(p['input'])==p['output'] for p in demos) and fn(query['input'])!=query['output']:
       counts[name]+=1
       if len(survivors)<1:
        survivors.append({'rival':name,'difficulty':band,'seed':seed,'start_index':start,
          'query_index':start+4,'demos':demos,'input':query['input'],'python_intended_output':query['output'],
          'rival_output':fn(query['input']),'self_check':gen.self_check(query['input'])})
 payload={'schema':'017f-candidate-selector-audit-v1','task_id':TASK,'generator_path':str(source.relative_to(root)),
 'generator_sha256':digest,'rule_hash':gen.RULE_HASH,'canonical':canonical,'windows_checked':checked,
 'surviving_window_counts':counts,'first_survivors':survivors}
 out=Path(__file__).with_name('candidate-selectors.json');out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 if survivors:
  w=survivors[0];Path(__file__).with_name('input.json').write_text(json.dumps(w['input'])+'\n');Path(__file__).with_name('rival-output.json').write_text(json.dumps(w['rival_output'])+'\n')
 print(json.dumps({'canonical':canonical,'windows_checked':checked,'counts':counts,'first':survivors[:1]},indent=2))
 return 0
if __name__=='__main__': raise SystemExit(main())
