from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
PACKET=Path(__file__).resolve().parents[2]
REPO=PACKET/'repo'
sys.path.insert(0,str(REPO/'shared/runtime'))

def load(task):
    p=REPO/'generators'/task/'generator.py'
    s=importlib.util.spec_from_file_location('audit_gen_'+task,p)
    m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def rival50(g,grid):
    cs=g._components(grid); out=[]
    for i,a in enumerate(cs):
      row=[]
      for j,b in enumerate(cs):
        same=g._canon(a['shape'])==g._canon(b['shape'])
        rot=g._norm(a['shape']) in g._all_rotations(b['shape'])
        row.append(8 if i==j or (same and not rot) else 0)
      out.append(row)
    return out

def comps(grid):
    h=len(grid); w=len(grid[0]); seen=set(); out=[]
    for r in range(h):
      for c in range(w):
        if grid[r][c]==0 or (r,c) in seen: continue
        color=grid[r][c]; st=[(r,c)]; seen.add((r,c)); cells=[]
        while st:
          rr,cc=st.pop(); cells.append((rr,cc))
          for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr,nc=rr+dr,cc+dc
            if 0<=nr<h and 0<=nc<w and (nr,nc) not in seen and grid[nr][nc]==color:
              seen.add((nr,nc)); st.append((nr,nc))
        rs=[x for x,_ in cells]; cs=[y for _,y in cells]
        out.append((color,min(rs),min(cs),max(rs),max(cs)))
    return out

def outline(grid):
    out=[[0]*len(row) for row in grid]
    for color,r0,c0,r1,c1 in comps(grid):
      for r in range(r0,r1+1):
        for c in range(c0,c1+1):
          if r in (r0,r1) or c in (c0,c1): out[r][c]=color
    return out

def rival99(grid):
    out=outline(grid)
    for color,r0,c0,r1,c1 in comps(grid):
      if min(r1-r0+1,c1-c0+1)<=2:
        out[(r0+r1)//2][(c0+c1)//2]=0
    return out

# 64 easy draws for 50.
g=load('50b66a854306')
grids=[g.generate(918273,i,difficulty='easy') for i in range(64)]
base=PACKET/'checks/audit/50b66a854306'
(base/'generated_input.json').write_text(json.dumps(grids,separators=(',',':'))+'\n')
(base/'generated_rival.json').write_text(json.dumps([rival50(g,x) for x in grids],separators=(',',':'))+'\n')
(base/'generated_meta.json').write_text(json.dumps({'seed':918273,'difficulty':'easy','sample_indices':[0,63],'count':64},indent=2)+'\n')

# 64 draws across all three bands for 99.
g=load('99a1cb372ca4')
plan=[('easy',i) for i in range(22)]+[('medium',i) for i in range(21)]+[('hard',i) for i in range(21)]
grids=[g.generate(12345,i,difficulty=d) for d,i in plan]
base=PACKET/'checks/audit/99a1cb372ca4'
(base/'generated_input.json').write_text(json.dumps(grids,separators=(',',':'))+'\n')
(base/'generated_rival.json').write_text(json.dumps([rival99(x) for x in grids],separators=(',',':'))+'\n')
(base/'generated_meta.json').write_text(json.dumps({'seed':12345,'plan':[{'difficulty':d,'sample_index':i} for d,i in plan],'count':64},indent=2)+'\n')
