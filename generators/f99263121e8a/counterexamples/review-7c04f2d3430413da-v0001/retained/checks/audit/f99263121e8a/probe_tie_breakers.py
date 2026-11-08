#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK='f99263121e8a'
CARD=((1,0),(-1,0),(0,1),(0,-1))

def components(grid):
    h,w=len(grid),len(grid[0]);seen=set();out=[]
    for r in range(h):
      for c in range(w):
        if grid[r][c]==0 or (r,c) in seen: continue
        color=grid[r][c];st=[(r,c)];seen.add((r,c));cells=[]
        while st:
          rr,cc=st.pop();cells.append((rr,cc))
          for dr,dc in CARD:
            nr,nc=rr+dr,cc+dc
            if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
              seen.add((nr,nc));st.append((nr,nc))
        out.append((color,tuple(cells)))
    return out

def bbox(comp):
    _,cells=comp; rs=[r for r,c in cells];cs=[c for r,c in cells]
    return min(rs),min(cs),max(rs),max(cs)

def render(grid,key):
    comps=sorted(components(grid),key=key)
    pieces=[]
    for _,cells in comps:
      r0,c0,r1,c1=bbox((0,cells)); pieces.append([list(row[c0:c1+1]) for row in grid[r0:r1+1]])
    if not pieces: return [[]]
    width=max(len(p[0]) for p in pieces);out=[]
    for i,p in enumerate(pieces):
      if i: out.append([0]*width)
      d=width-len(p[0]);left=d//2
      out.extend([[0]*left+row+[0]*(d-left) for row in p])
    return out

def intended(grid): return render(grid,lambda x:(bbox(x)[1],bbox(x)[0]))

def tie_color(grid): return render(grid,lambda x:(bbox(x)[1],x[0],bbox(x)[0]))
def tie_size(grid): return render(grid,lambda x:(bbox(x)[1],len(x[1]),bbox(x)[0]))
def tie_centroid(grid):
    return render(grid,lambda x:(bbox(x)[1],sum(c for r,c in x[1])/len(x[1]),bbox(x)[0]))
RIVALS={'left_then_color':tie_color,'left_then_size':tie_size,'left_then_centroid_x':tie_centroid}

def main():
 root=find_root(__file__);gen,source,digest=load_selected_generator(TASK,root=root)
 canon=canonical_pairs(TASK,root=root,labeled_only=True)
 canonical={n:[fn(p['input'])==p['output'] for p in canon] for n,fn in RIVALS.items()}
 counts={n:0 for n in RIVALS};first=[];checked=0
 for band in ('easy','medium','hard'):
  for seed in range(500):
   grids=[gen.generate(seed,i,difficulty=band) for i in range(11)]
   pairs=[{'input':g,'output':intended(g)} for g in grids]
   for start in range(6):
    demos=pairs[start:start+5];q=pairs[start+5];checked+=1
    for n,fn in RIVALS.items():
      fits=[fn(p['input'])==p['output'] for p in demos]
      changes=fn(q['input'])!=q['output']
      if all(fits) and changes:
       counts[n]+=1
       if len(first)<20:
        first.append({'rival':n,'difficulty':band,'seed':seed,'start_index':start,
          'demo_indices':list(range(start,start+5)),'query_index':start+5,
          'demos':demos,'input':q['input'],'python_intended_output':q['output'],
          'rival_output':fn(q['input']),'self_check':gen.self_check(q['input']),
          'schedule_profiles':[gen.schedule_profile(seed,i,band) for i in range(start,start+6)]})
 payload={'schema':'f992-tie-breaker-audit-v1','task_id':TASK,'generator_path':str(source.relative_to(root)),
  'generator_sha256':digest,'rule_hash':gen.RULE_HASH,'canonical_fit':canonical,
  'windows_checked':checked,'surviving_window_counts':counts,'first_survivors':first}
 out=Path(__file__).with_name('tie-breakers.json');out.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 if first:
  w=first[0];Path(__file__).with_name('input.json').write_text(json.dumps(w['input'])+'\n');Path(__file__).with_name('rival-output.json').write_text(json.dumps(w['rival_output'])+'\n')
 print(json.dumps({'canonical_fit':canonical,'windows_checked':checked,'counts':counts,'first':first[:1]},indent=2))
 return 0
if __name__=='__main__': raise SystemExit(main())
