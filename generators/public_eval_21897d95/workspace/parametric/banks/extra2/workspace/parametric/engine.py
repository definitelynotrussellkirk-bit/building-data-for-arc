"""Execute embedded region-routing arrows, then an optional quarter-turn.

Blue T symbols point from a source region toward the first other region on the
ray. A nonblue center supplies the destination ink; a blue center uses the
source region's original ink. Decode and erase every symbol before routing,
then recolor simultaneously. A five-cell burgundy top-corner command turns the
canvas clockwise (left corner) or counterclockwise (right corner).
"""
from collections import Counter
import random
RULE_TASK_ID = 'ee_21897d95'
TASK_ID = 'public_eval_21897d95'
VERSION = '1.0.0'
SETTINGS = ('payload','source_color')
DIRECTIONS=((-1,0),(1,0),(0,-1),(0,1))

def integer(v,lo,hi,name):
 if type(v) is not int or not lo<=v<=hi:raise ValueError(name+' must be an exact bounded integer')
 return v

def grid_check(g):
 if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or
     any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
  raise ValueError('expected rectangular integer-color grid with dimensions 1..30')

def components(g):
 h,w=len(g),len(g[0]);todo={(r,c) for r in range(h) for c in range(w)};out=[]
 while todo:
  start=min(todo);todo.remove(start);co=g[start[0]][start[1]];stack=[start];pts=[]
  while stack:
   r,c=stack.pop();pts.append((r,c))
   for dr,dc in DIRECTIONS:
    p=(r+dr,c+dc)
    if p in todo and g[p[0]][p[1]]==co:todo.remove(p);stack.append(p)
  out.append({'color':co,'cells':sorted(pts)})
 return out

def rotate(g,k):
 out=[row[:] for row in g]
 for _ in range(k%4):out=[list(row) for row in zip(*out[::-1])]
 return out

def analyze(g):
 grid_check(g);h,w=len(g),len(g[0]);arrows=[];covered=set()
 def at(r,c):return g[r][c] if 0<=r<h and 0<=c<w else -1
 for r in range(h):
  for c in range(w):
   arms=[(dr,dc) for dr,dc in DIRECTIONS if at(r+dr,c+dc)==1]
   if len(arms)!=3:continue
   missing=next(d for d in DIRECTIONS if d not in arms);dr,dc=-missing[0],-missing[1]
   # The two corners ahead of the crossbar recover the underlying source,
   # even when the symbol touches the rear boundary or the canvas edge.
   corners=[at(r+dr+dc,c+dc+dr),at(r+dr-dc,c+dc-dr)]
   if corners[0]!=corners[1] or corners[0] in (-1,1):continue
   source=corners[0];pts={(r,c)}|{(r+dy,c+dx) for dy,dx in arms}
   if covered&pts:raise ValueError('overlapping or ambiguous arrow symbols')
   covered|=pts
   arrows.append({'center':(r,c),'direction':(dr,dc),'source':source,'payload':source if g[r][c]==1 else g[r][c],'cells':sorted(pts)})
 if not arrows:raise ValueError('at least one blue arrow required')
 if any(g[r][c]==1 and (r,c) not in covered for r in range(h) for c in range(w)):
  raise ValueError('blue ink outside a recognized symbol')
 turns=[]
 for obj in components(g):
  if obj['color']!=9 or len(obj['cells'])!=5:continue
  pts=set(obj['cells']);rs,cs=zip(*pts);r0,c0,r1,c1=min(rs),min(cs),max(rs),max(cs)
  if r1-r0!=2 or c1-c0!=2:continue
  for corner,k in ((c0,1),(c1,-1)):
   shape={(r0,c) for c in range(c0,c1+1)}|{(r,corner) for r in range(r0,r1+1)}
   if pts!=shape:continue
   votes=Counter(at(r+dr,c+dc) for r,c in pts for dr,dc in DIRECTIONS if (r+dr,c+dc) not in pts and at(r+dr,c+dc) not in (-1,1,9))
   if not votes:raise ValueError('rotation command has no region color')
   top=votes.most_common();
   if len(top)>1 and top[0][1]==top[1][1]:raise ValueError('rotation background is ambiguous')
   turns.append({'cells':obj['cells'],'source':top[0][0],'turn':k})
 if len(turns)>1:raise ValueError('only one quarter-turn command is admitted')
 clean=[row[:] for row in g]
 for sym in arrows+turns:
  for r,c in sym['cells']:clean[r][c]=sym['source']
 regions=components(clean);lookup={p:i for i,obj in enumerate(regions) for p in obj['cells']}
 for a in arrows:
  r,c=a['center'];dr,dc=a['direction'];y,x=r+dr,c+dc
  while 0<=y<h and 0<=x<w and clean[y][x]==a['source']:y+=dr;x+=dc
  if not (0<=y<h and 0<=x<w):raise ValueError('arrow exits canvas without a destination')
  a['target']=lookup[y,x];a['source_region']=lookup[r,c];a['hit']=(y,x)
 for mode in SETTINGS:
  assignments={}
  for a in arrows:
   color=a['payload'] if mode=='payload' else a['source']
   if a['target'] in assignments and assignments[a['target']]!=color:raise ValueError('conflicting arrows target one region')
   assignments[a['target']]=color
 return {'arrows':arrows,'turns':turns,'turn':sum(t['turn'] for t in turns),'clean':clean,'regions':regions}

def render(info,mode='payload',*,target_source=False,color_global=False,turn_override=None,cascade=False,keep_symbols=None):
 out=[row[:] for row in (keep_symbols if keep_symbols is not None else info['clean'])]
 for a in info['arrows']:
  target=a['source_region'] if target_source else a['target']
  color=a['payload'] if mode=='payload' else a['source']
  if cascade and a['payload']==a['source']:
   r,c=a['center'];color=out[r][c]
  cells=info['regions'][target]['cells']
  if color_global:
   co=info['regions'][target]['color'];cells=[p for obj in info['regions'] if obj['color']==co for p in obj['cells']]
  for r,c in cells:out[r][c]=color
 return rotate(out,info['turn'] if turn_override is None else turn_override)

def solve(g,mode='payload'):
 if type(mode) is not str or mode not in SETTINGS:raise ValueError('unknown ink mode')
 return render(analyze(g),mode)

def rule_mirror(g):return solve(g)

def self_check(g,difficulty=None):
 try:analyze(g)
 except (ValueError,TypeError,IndexError) as e:return [str(e)]
 return []

def _construct(rng,h,w,turn,islands):
    palette=rng.sample([0,2,3,4,5,6,7,8],8)
    # Two separated cells use the same background color, preventing a global
    # color-replacement shortcut from standing in for connected-region routing.
    colors=[[palette[0],palette[1],palette[0]],[palette[2],palette[3],palette[4]]]
    mid=h//2;b1=w//3;b2=2*w//3
    offsets=[rng.choice((-1,0,1)) for _ in range(h)]
    borders=[rng.choice((-1,0,1)) for _ in range(w)]
    g=[]
    for r in range(h):
        row=[]
        for c in range(w):
            ri=int(r>=mid+borders[c]);ci=0 if c<b1+offsets[r] else 1 if c<b2+offsets[r] else 2
            row.append(colors[ri][ci])
        g.append(row)
    # A Hamiltonian route through six blocks has unique destinations. Markers
    # stay well within their source; jagged region boundaries vary separately.
    cycle=[(0,0),(0,1),(0,2),(1,2),(1,1),(1,0)]
    starts=[0,b1,b2];placed=[]
    for i,(ri,ci) in enumerate(cycle):
        ni,nj=cycle[(i+1)%6];dr,dc=ni-ri,nj-ci
        r=(0 if ri==0 else mid)+2;c=starts[ci]+2;source=colors[ri][ci]
        payload=palette[5] if i==0 else (9 if i==3 else source)
        arms=[d for d in DIRECTIONS if d!=(-dr,-dc)]
        for dy,dx in arms:g[r+dy][c+dx]=1
        g[r][c]=1 if payload==source else payload
        placed.append((r,c,dr,dc))
    if islands:
        # First-hit and four-connectivity witness: a one-cell destination and a
        # same-color diagonal satellite; only the first cell is actually hit.
        r,c,_,_=placed[0]
        g[r][c+3]=palette[6];g[r+1][c+4]=palette[6]
    if rng.randrange(2):g=[row[::-1] for row in g]
    if rng.randrange(2):g=g[::-1]
    if rng.randrange(2):g=[list(row) for row in zip(*g)]
    h,w=len(g),len(g[0])
    if turn:
        candidates=[]
        for r in range(h-2):
            for c in range(w-2):
                co=g[r][c]
                if co in (1,9) or any(g[y][x]!=co for y in range(r,r+3) for x in range(c,c+3)):continue
                corner=c if turn==1 else c+2;pts={(r,x) for x in range(c,c+3)}|{(y,corner) for y in range(r,r+3)}
                if any(0<=y+dy<h and 0<=x+dx<w and g[y+dy][x+dx]==1 for y,x in pts for dy in (-1,0,1) for dx in (-1,0,1)):continue
                if any(0<=y+dy<h and 0<=x+dx<w and g[y+dy][x+dx]==9 for y,x in pts for dy,dx in DIRECTIONS):continue
                votes=Counter(g[y+dy][x+dx] for y,x in pts for dy,dx in DIRECTIONS if (y+dy,x+dx) not in pts and 0<=y+dy<h and 0<=x+dx<w and g[y+dy][x+dx] not in (1,9))
                top=votes.most_common()
                if top and top[0][0]==co and (len(top)==1 or top[0][1]>top[1][1]):candidates.append(pts)
        if not candidates:raise ValueError('no legal quarter-turn symbol placement')
        for r,c in rng.choice(candidates):g[r][c]=9
    return g

def scene(seed,index,kind):
 integer(seed,0,2**63-1,'seed');integer(index,0,5 if kind=='demo' else 3,'index')
 if kind not in ('demo','query'):raise ValueError('invalid scene kind')
 dims=((18,24),(20,27),(22,26),(24,28),(26,29),(28,30)) if kind=='demo' else ((19,25),(23,27),(26,28),(30,30))
 turn=(1,-1,0,1,-1,0)[index] if kind=='demo' else (0,-1,1,0)[index]
 return _construct(random.Random(f'21897d95:v1:{seed}:{kind}:{index}'),*dims[index],turn,index%2==0)

def generate(seed=0,sample_index=0,difficulty='medium'):
 integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**63-1,'sample_index')
 if difficulty is None:difficulty='medium'
 if difficulty not in ('easy','medium','hard','mixed'):raise ValueError('unsupported difficulty')
 rng=random.Random(f'21897d95:base:{seed}:{sample_index}:{difficulty}')
 dims={'easy':(18,24),'medium':(24,27),'hard':(30,30),'mixed':rng.choice(((18,24),(24,27),(30,30)))}[difficulty]
 return _construct(rng,*dims,(1,-1,0)[sample_index%3],sample_index%2==0)
