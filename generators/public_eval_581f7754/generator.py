"""Self-contained ordinary generator for unapproved public parent 581f7754."""
from __future__ import annotations
from collections import Counter,deque
import hashlib,json,random
RULE_TASK_ID='ee_581f7754';TASK_ID='public_eval_581f7754';MIN_TRAIN=2;MAX_TRAIN=6
D4=((-1,0),(1,0),(0,-1),(0,1));MARK=(2,4,6);FILL=(1,3,5,7,9)
SHAPES=(
 ((-1,0),(-1,1),(0,0),(0,1),(1,0),(1,1)),
 ((-1,-1),(-1,0),(0,-1),(0,0),(0,1),(1,-1),(1,0)),
 tuple((r,c)for r in(-1,0,1)for c in(-1,0,1)),
 ((-1,0),(0,-1),(0,0),(0,1),(1,0),(1,1)),
 ((-1,-1),(-1,0),(-1,1),(0,-1),(0,0),(1,-1),(1,0)))
def integer(v,lo,hi,n):
 if type(v)is not int or not lo<=v<=hi:raise ValueError(f'{n} invalid')
def comps(cells):
 rem=set(cells);out=[]
 while rem:
  s=min(rem);rem.remove(s);q=[s];co={s}
  for r,c in q:
   for dr,dc in D4:
    p=(r+dr,c+dc)
    if p in rem:rem.remove(p);co.add(p);q.append(p)
  out.append(co)
 return sorted(out,key=lambda x:min(x))
def analyze(g):
 h=len(g);w=len(g[0]);bg=Counter(v for row in g for v in row).most_common(1)[0][0]
 cs=comps((r,c)for r in range(h)for c in range(w)if g[r][c]!=bg);anchors=[];objs=[]
 for co in cs:
  if len(co)==1:
   p=next(iter(co))
   if p[0]in(0,h-1)or p[1]in(0,w-1):anchors.append(p);continue
  objs.append(co)
 ac={g[r][c]for r,c in anchors};recs=[]
 for co in objs:
  counts=Counter(g[r][c]for r,c in co if g[r][c]in ac);mc=min(counts,key=lambda x:(counts[x],x));m=min(p for p in co if g[p[0]][p[1]]==mc)
  recs.append((co,m,mc))
 return h,w,bg,sorted(anchors),recs
def rule_mirror(g):
 h,w,bg,anchors,recs=analyze(g);out=[r[:]for r in g]
 for co,m,mc in recs:
  for r,c in co:out[r][c]=bg
 for co,m,mc in recs:
  aa=[a for a in anchors if g[a[0]][a[1]]==mc];a=min(aa,key=lambda p:(abs(p[0]-m[0])+abs(p[1]-m[1]),p));dr=dc=0
  if a[1]in(0,w-1):dr=a[0]-m[0]
  else:dc=a[1]-m[1]
  rs=[r for r,c in co];cs=[c for r,c in co];special=len(co)==9 and max(rs)-min(rs)==2 and max(cs)-min(cs)==2 and m==((min(rs)+max(rs))//2,(min(cs)+max(cs))//2)
  if special:
   if a[1]==0:dc-=1
   elif a[1]==w-1:dc+=1
   elif a[0]==0:dr-=1
   else:dr+=1
  for r,c in sorted(co):out[r+dr][c+dc]=g[r][c]
 return out
def rng(seed,tag):return random.Random(int.from_bytes(hashlib.sha256(json.dumps([seed,tag],sort_keys=True).encode()).digest()[:16],'big'))
def lanes(n,k):return [round(2+i*(n-6)/(k-1))for i in range(k)]
def vertical_lanes(n,k):return [round(3+i*(n-7)/(k-1))for i in range(k)]
def scene(seed,tag,h,w,rows=True,stress=False):
 q=rng(seed,tag);bg=8 if(seed+int(q.random()*1000))%2==0 else 0;g=[[bg]*w for _ in range(h)];n=5 if stress else 3;colors=list(MARK);q.shuffle(colors)
 if rows:
  targets=[2,h//2,h-3];edge=0 if q.randrange(2)==0 else w-1
  for i,r in enumerate(targets):g[r][edge]=colors[i]
  for i,c in enumerate(lanes(w,n)):
   mr=targets[(i+1)%3]
   for dr,dc in SHAPES[i]:g[mr+dr][c+dc]=FILL[i]
   g[mr][c]=colors[i%3]
 else:
  targets=[2,w//2,w-3];edge=0 if q.randrange(2)==0 else h-1
  for i,c in enumerate(targets):g[edge][c]=colors[i]
  for i,r in enumerate(vertical_lanes(h,n)):
   mc=targets[(i+1)%3]
   for dr,dc in SHAPES[i]:g[r+dr][mc+dc]=FILL[i]
   g[r][mc]=colors[i%3]
 return g
def generate(seed,sample_index=0,difficulty=None):
 integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
 if difficulty not in(None,'easy','medium','hard'):raise ValueError('unknown difficulty')
 hard=difficulty=='hard'or sample_index%4==3;size=30 if hard else 12+2*(sample_index%6)
 return scene(seed,['ordinary',sample_index],size,min(30,size+2),sample_index%2==0,hard)
def self_check(g):
 issues=[]
 try:
  h,w,bg,a,o=analyze(g)
  if len(a)<3:issues.append('few anchors')
  if len(o)<3:issues.append('few objects')
 except Exception as e:issues.append(str(e))
 return issues
