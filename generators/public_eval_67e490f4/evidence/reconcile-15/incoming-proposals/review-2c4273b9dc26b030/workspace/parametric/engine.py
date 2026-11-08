from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
import random

BG=0
MODES=('dihedral','translation_only')
SHAPES={
 'square':[(0,0),(0,1),(1,0),(1,1)],
 'domino':[(0,0),(0,1)],
 'plus':[(0,1),(1,0),(1,1),(1,2),(2,1)],
 'ell3':[(0,0),(1,0),(1,1)],
 'ell5':[(0,0),(1,0),(2,0),(2,1),(2,2)],
 'singleton':[(0,0)],
 'tee4':[(0,0),(0,1),(0,2),(1,1)],
}

def grid(g):
    if type(g) is not list or not g or type(g[0]) is not list or not g[0] or len(g)>30 or len(g[0])>30: raise ValueError('grid')
    w=len(g[0])
    if any(type(r) is not list or len(r)!=w or any(type(v) is not int or not 0<=v<=9 for v in r) for r in g):raise ValueError('grid')
    return deepcopy(g)

def components(g, color=None):
    h,w=len(g),len(g[0]); seen=set(); out=[]
    for r in range(h):
      for c in range(w):
        if (r,c) in seen: continue
        v=g[r][c]
        if color is None:
          if v==0: continue
          target=v
        else:
          if v!=color: continue
          target=color
        st=[(r,c)]; seen.add((r,c)); pts=[]
        while st:
          x,y=st.pop();pts.append((x,y))
          for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if 0<=q[0]<h and 0<=q[1]<w and q not in seen and g[q[0]][q[1]]==target:
              seen.add(q);st.append(q)
        out.append((target,pts))
    return out

def norm(pts):
    r0=min(r for r,c in pts);c0=min(c for r,c in pts)
    return tuple(sorted((r-r0,c-c0) for r,c in pts))

def variants(pts):
    s=list(norm(pts)); variants=set()
    for flip in (False,True):
      for rot in range(4):
        q=[]
        for r,c in s:
          x,y=r,(-c if flip else c)
          for _ in range(rot): x,y=y,-x
          q.append((x,y))
        variants.add(norm(q))
    return variants

def equivalent(a,b,mode='dihedral'):
    if mode=='translation_only': return norm(a)==norm(b)
    return norm(a) in variants(b)

def derive(g,mode='dihedral'):
    g=grid(g)
    bg=Counter(v for row in g for v in row).most_common(1)[0][0]
    comps=[];h,w=len(g),len(g[0]);seen=set()
    for r in range(h):
      for c in range(w):
        if (r,c) in seen or g[r][c]==bg:continue
        col=g[r][c]; st=[(r,c)];seen.add((r,c));pts=[]
        while st:
          x,y=st.pop();pts.append((x,y))
          for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if 0<=q[0]<h and 0<=q[1]<w and q not in seen and g[q[0]][q[1]]==col:
              seen.add(q);st.append(q)
        comps.append((col,pts))
    main=max(comps,key=lambda z:len(z[1])); canvas=main[0]
    rs=[r for r,c in main[1]];cs=[c for r,c in main[1]];box=(min(rs),min(cs),max(rs),max(cs));r0,c0,r1,c1=box
    # enclosed bg components inside box
    holes=[]; seen=set()
    for r in range(r0,r1+1):
      for c in range(c0,c1+1):
        if (r,c) in seen or g[r][c]!=bg: continue
        st=[(r,c)];seen.add((r,c));pts=[];touch=False
        while st:
          x,y=st.pop();pts.append((x,y));touch |= x in (r0,r1) or y in (c0,c1)
          for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=(x+dx,y+dy)
            if r0<=q[0]<=r1 and c0<=q[1]<=c1 and q not in seen and g[q[0]][q[1]]==bg:
              seen.add(q);st.append(q)
        if not touch: holes.append(pts)
    outside=[(col,pts) for col,pts in comps if pts is not main[1] and all(not(r0<=r<=r1 and c0<=c<=c1) for r,c in pts)]
    votes=[]
    for hole in holes:
      matched=[col for col,pts in outside if equivalent(hole,pts,mode)]
      cnt=Counter(matched)
      winner=(max(dict.fromkeys(matched), key=lambda x:cnt[x]) if cnt else bg)
      votes.append({'hole':hole,'counts':dict(cnt),'winner':winner})
    return {'background':bg,'canvas':canvas,'box':box,'holes':votes,'outside':outside}

def solve(g,mode='dihedral'):
    st=derive(g,mode);r0,c0,r1,c1=st['box']; out=[row[c0:c1+1] for row in g[r0:r1+1]]
    for rec in st['holes']:
      for r,c in rec['hole']:out[r-r0][c-c0]=rec['winner']
    return out

def transform(shape,rot=0,flip=False):
    q=[]
    for r,c in shape:
      x,y=r,(-c if flip else c)
      for _ in range(rot%4): x,y=y,-x
      q.append((x,y))
    n=norm(q);return list(n)

def make(seed,index,stress=False):
    rng=random.Random(f'67e490f4:{seed}:{index}:{int(stress)}')
    h=w=30 if stress else rng.randint(22,28)
    bg=rng.choice(range(10)); canvas=rng.choice([x for x in range(10) if x!=bg])
    palette=[x for x in range(10) if x not in (bg,canvas)];rng.shuffle(palette)
    selected=rng.sample(list(SHAPES),3 if not stress else 4)
    # template size fixed roomy; place distinct holes on lattice
    th=13 if stress else 11;tw=13 if stress else 11
    r0=1;c0=w-tw-1
    g=[[bg]*w for _ in range(h)]
    for r in range(r0,r0+th):
      for c in range(c0,c0+tw): g[r][c]=canvas
    slots=[(2,2),(2,7),(6,2),(6,7),(9,5)]
    winners={}; hole_records=[]
    for j,name in enumerate(selected):
      shp=transform(SHAPES[name],rng.randrange(4),bool(rng.randrange(2)))
      sr,sc=slots[j]
      for dr,dc in shp:g[r0+sr+dr][c0+sc+dc]=bg
      winners[name]=palette[j]
      hole_records.append((name,shp))
    # outside cues in left/lower field; winner has 3, distractor 1 or 2.
    slots_out=[(r,c) for r in range(1,h-2,4) for c in (1,5)]
    slot_i=0
    def place(shape,col):
      nonlocal slot_i
      if slot_i>=len(slots_out): raise ValueError('cue packing exhausted')
      r,c=slots_out[slot_i]; slot_i+=1
      for dr,dc in shape:
        if r+dr>=h or c+dc>=c0-1: raise ValueError('cue packing collision')
        g[r+dr][c+dc]=col
    for j,name in enumerate(selected):
      for k in range(2): place(transform(SHAPES[name],rng.randrange(4),bool(rng.randrange(2))),winners[name])
      dcol=palette[(j+len(selected))%len(palette)]
      place(transform(SHAPES[name],rng.randrange(4),bool(rng.randrange(2))),dcol)
    return g

def self_check(g):
    try:
      st=derive(g)
      if len(st['holes'])<3:return ['need >=3 hole classes']
      if any(not h['counts'] for h in st['holes']):return ['unmatched hole']
      if any(list(h['counts'].values()).count(max(h['counts'].values()))>1 for h in st['holes']):return ['tie']
      return []
    except Exception as e:return [str(e)]
