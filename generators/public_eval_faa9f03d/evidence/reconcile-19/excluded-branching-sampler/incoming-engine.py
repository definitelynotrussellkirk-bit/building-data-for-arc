import numpy as np
from collections import deque
DIRS4=((-1,0),(1,0),(0,-1),(0,1))
def get_bg(g):
 vals,c=np.unique(g,return_counts=True); return int(vals[np.argmax(c)])
def comps(mask):
 H,W=mask.shape; seen=set(); out=[]
 for r,c in zip(*np.where(mask)):
  if (int(r),int(c)) in seen: continue
  q=[(int(r),int(c))]; seen.add(q[0]); cc=[]
  while q:
   p=q.pop();cc.append(p); rr,cl=p
   for dr,dc in DIRS4:
    n=(rr+dr,cl+dc)
    if 0<=n[0]<H and 0<=n[1]<W and n not in seen and mask[n]:seen.add(n);q.append(n)
  out.append(cc)
 return out
def pts(mask): return {tuple(map(int,rc)) for rc in np.argwhere(mask)}
def axis_support(mask,r,c,axis): return ((r,c-1) in mask or (r,c+1) in mask) if axis==0 else ((r-1,c) in mask or (r+1,c) in mask)
def perp_support(mask,r,c,axis): return ((r-1,c) in mask or (r+1,c) in mask) if axis==0 else ((r,c-1) in mask or (r,c+1) in mask)
def component_count(shape,p):
 m=np.zeros(shape,bool)
 for q in p:m[q]=1
 return len(comps(m))
def solve(grid, policy="fragmented"):
 if policy not in ("fragmented","complete"): raise ValueError("policy")
 g=np.asarray(grid,dtype=int); bg=get_bg(g); H,W=g.shape
 colors=set(map(int,g.ravel()))-{bg}; marker_colors=set()
 for color in colors:
  cs=comps(g==color)
  if max(len(x) for x in cs)==1:marker_colors.add(color)
 line_colors=colors-marker_colors
 original={color:pts(g==color) for color in line_colors}
 assignment={};assign_dir={}
 marker_mask=np.isin(g,list(marker_colors))
 for r0,c0 in pts(marker_mask):
  candidates=[]
  for dr,dc in DIRS4:
   r,c=r0+dr,c0+dc; dist=1
   while 0<=r<H and 0<=c<W:
    value=int(g[r,c])
    if value in line_colors:
     axis=0 if dr==0 else 1; supported=axis_support(original[value],r,c,axis)
     candidates.append((dist,0 if supported else 1,value,dr,dc));break
    if value==bg or value in marker_colors:r+=dr;c+=dc;dist+=1;continue
    break
  if not candidates: raise AssertionError(('no marker view',(r0,c0)))
  candidates.sort();_,_,color,dr,dc=candidates[0]; assignment[(r0,c0)]=color;assign_dir[(r0,c0)]=(dr,dc)
 masks={color:set(p) for color,p in original.items()}; marker_pts={color:set() for color in line_colors}
 for p,color in assignment.items():masks[color].add(p);marker_pts[color].add(p)
 comp_count={color:component_count(g.shape,masks[color]) for color in line_colors}
 def has_axis_support(color,r,c,axis):return (r,c) in marker_pts[color] or axis_support(masks[color],r,c,axis)
 def should_fill(color,a,b,axis):
  r1,c1=a;r2,c2=b;gap=c2-c1-1 if axis==0 else r2-r1-1
  if gap<=0:return False
  aa=has_axis_support(color,r1,c1,axis);bb=has_axis_support(color,r2,c2,axis)
  if gap==1:
   if aa or bb:return True
   ap=perp_support(masks[color],r1,c1,axis);bp=perp_support(masks[color],r2,c2,axis)
   return not(ap and bp)
  if a in marker_pts[color] and b in marker_pts[color]:return False
  return aa and bb
 for _round in range(12):
  changed=False
  for color in sorted(line_colors):
   additions=set()
   for r in range(H):
    cs=sorted(c for rr,c in masks[color] if rr==r)
    for c1,c2 in zip(cs,cs[1:]):
     gap=c2-c1-1
     if (_round==0 or gap>1) and should_fill(color,(r,c1),(r,c2),0): additions.update((r,c) for c in range(c1+1,c2))
   for c in range(W):
    rs=sorted(r for r,cc in masks[color] if cc==c)
    for r1,r2 in zip(rs,rs[1:]):
     gap=r2-r1-1
     if (_round==0 or gap>1) and should_fill(color,(r1,c),(r2,c),1): additions.update((r,c) for r in range(r1+1,r2))
   before=len(masks[color]); masks[color].update(additions); changed |= len(masks[color])>before
  if not changed: break
 control_ray={color:set() for color in line_colors}
 if 4 in marker_colors:
  for control in pts(g==4):
   color=assignment[control];dr,dc=assign_dir[control]
   r,c=control[0]+dr,control[1]+dc;pivot=None
   while 0<=r<H and 0<=c<W:
    if (r,c) in masks[color]:pivot=(r,c);break
    r+=dr;c+=dc
   if pivot is None:raise AssertionError('no pivot')
   old_start=(pivot[0]+dr,pivot[1]+dc)
   if old_start in masks[color]:
    stack=[old_start];old_arm=set()
    while stack:
     q=stack.pop()
     if q==pivot or q in old_arm or q not in masks[color]:continue
     old_arm.add(q);qr,qc=q
     for ndr,ndc in DIRS4:stack.append((qr+ndr,qc+ndc))
    for q in old_arm:masks[color].discard(q);marker_pts[color].discard(q);control_ray[color].discard(q)
   pr,pc=-dr,-dc;r,c=pivot
   while 0<=r<H and 0<=c<W:
    masks[color].add((r,c));control_ray[color].add((r,c));r+=pr;c+=pc
 claims={}
 for color,p in masks.items():
  for q in p:claims.setdefault(q,[]).append(color)
 out=np.full_like(g,bg)
 def marker_brackets(color,p):
  r,c=p; same_row=[mc for mr,mc in marker_pts[color] if mr==r]
  if any(mc<c for mc in same_row) and any(mc>c for mc in same_row):return True
  same_col=[mr for mr,mc in marker_pts[color] if mc==c]
  return any(mr<r for mr in same_col) and any(mr>r for mr in same_col)
 for p,colors_here in claims.items():
  if len(colors_here)==1:out[p]=colors_here[0];continue
  original_crossing=[color for color in colors_here if int(g[p])==color]
  if original_crossing:out[p]=min(colors_here,key=(lambda color: (-(comp_count[color] + (1 if p in control_ray[color] else 0)), color)) if policy=="fragmented" else (lambda color: ((comp_count[color] + (1 if p in control_ray[color] else 0)), color)))
  else:
   bracketed=[color for color in colors_here if marker_brackets(color,p)]
   if bracketed:out[p]=min(bracketed,key=(lambda color: (-(comp_count[color] + (1 if p in control_ray[color] else 0)), color)) if policy=="fragmented" else (lambda color: ((comp_count[color] + (1 if p in control_ray[color] else 0)), color)))
   else:out[p]=min(colors_here)
 return out.tolist()


import random

def _blank(n=12): return [[0]*n for _ in range(n)]
def _seg(g,a,b,color):
 r0,c0=a;r1,c1=b
 if r0==r1:
  for c in range(min(c0,c1),max(c0,c1)+1): g[r0][c]=color
 elif c0==c1:
  for r in range(min(r0,r1),max(r0,r1)+1): g[r][c0]=color
 else: raise ValueError('axis')

def make(seed=0,index=0,stress=False):
 rng=random.Random(f'faa9f03d:{seed}:{index}:{int(stress)}')
 n=12
 # Two visible path colors; numeric ordering is shuffled so the structural vote matters.
 a,b=rng.sample([1,3,5,6,7,8,9],2)
 rows3=sorted(rng.sample(range(2,10),3))
 c_left=rng.choice([1,2]); c_right=rng.choice([9,10])
 cross=rng.randint(c_left+2,c_right-2)
 logical=_blank(n)
 # A is a single serpentine path crossing the vertical B path three times.
 pts=[]
 r0,r1,r2=rows3
 _seg(logical,(r0,0),(r0,c_right),a); _seg(logical,(r0,c_right),(r1,c_right),a)
 _seg(logical,(r1,c_left),(r1,c_right),a); _seg(logical,(r1,c_left),(r2,c_left),a)
 _seg(logical,(r2,c_left),(r2,11),a)
 # B spans top to bottom through the shared crossing column. At crossings target A owns the cell.
 for r in range(n):
  if logical[r][cross]==0: logical[r][cross]=b
 # Build input from logical: display B at crossings, then add isolated red markers on A.
 inp=[row[:] for row in logical]
 for r in rows3: inp[r][cross]=b
 # Remove 2-3 A cells as red markers, chosen away from crossings and one another.
 candidates=[]
 for r in rows3:
  for c in range(2,10):
   if c==cross or logical[r][c]!=a: continue
   if c in (c_left,c_right): continue
   candidates.append((r,c))
 rng.shuffle(candidates); chosen=[]
 for p in candidates:
  if all(abs(p[0]-q[0])+abs(p[1]-q[1])>1 and p[1]!=q[1] for q in chosen): chosen.append(p)
  if len(chosen)>=3: break
 for r,c in chosen: inp[r][c]=2
 # Ensure marker color is singleton and line colors have non-singleton components.
 if solve(inp,'fragmented')==inp: raise RuntimeError('degenerate')
 return inp

def transform(g,policy='fragmented'): return solve(g,policy)
def self_check(g):
 errs=[]
 try:
  a=solve(g,'fragmented'); b=solve(g,'complete')
  if a==g: errs.append('identity')
  if a==b: errs.append('counterfactual_not_distinct')
 except Exception as e: errs.append(type(e).__name__+':'+str(e))
 return errs

def intermediate(g,policy='fragmented'):
 # Compact explanatory intermediate for witness tooling: marker ownership and changed cells.
 out=solve(g,policy)
 markers=[(r,c,g[r][c]) for r in range(len(g)) for c in range(len(g[0])) if g[r][c] in (2,4)]
 changed=[(r,c,g[r][c],out[r][c]) for r in range(len(g)) for c in range(len(g[0])) if g[r][c]!=out[r][c]]
 return {'markers':markers,'repairs':changed}
