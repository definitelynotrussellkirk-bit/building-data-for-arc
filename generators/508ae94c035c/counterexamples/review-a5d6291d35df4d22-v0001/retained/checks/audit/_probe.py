import importlib.util, json, hashlib
from pathlib import Path

def load(t):
 p=Path('generators')/t/'generator.py'
 spec=importlib.util.spec_from_file_location('g_'+t,p)
 m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m,p
m,p=load('cdc2954e8f80')
base=m.generate(123,7)
try:
    alt=m.generate(123,7,palette_size=1,n_distinct_colors=1,palette_kind='warm',banana=7)
    print('unknown accepted',True,'same',base==alt)
except Exception as e:
    print('unknown accepted',False,type(e).__name__,e)
print('base selfcheck',m.self_check(base))
cross=[[0]*7 for _ in range(7)]; cross[1][1]=2;cross[3][5]=2
print('cross check',m.self_check(cross))
print('hash',hashlib.sha256(p.read_bytes()).hexdigest())

m2,p2=load('508ae94c035c')
g=m2.generate(75,75,difficulty='hard',n_horiz=3,n_vert=3)
print('508 dims',len(g),len(g[0]), 'self',m2.self_check(g))
h,w=len(g),len(g[0]);seen=set(); comps=[]
for r in range(h):
 for c in range(w):
  if g[r][c] and (r,c) not in seen:
   st=[(r,c)];seen.add((r,c)); cells=[]
   while st:
    x,y=st.pop();cells.append((x,y))
    for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
     xx,yy=x+dx,y+dy
     if 0<=xx<h and 0<=yy<w and g[xx][yy] and (xx,yy) not in seen:
      seen.add((xx,yy));st.append((xx,yy))
   comps.append(cells)
print('comps',[(len(c),len({r for r,_ in c}),len({cc for _,cc in c}),sorted({g[r][cc] for r,cc in c})) for c in comps])
print('hash2',hashlib.sha256(p2.read_bytes()).hexdigest())
