"""Uniform shielded-ray hypothesis. NOT fully validated against public parent.

Known unresolved parent train[2] omission is retained in tests and diagnostics.
Groups move along piecewise rational directions. Intersecting forward beams
bend together in the normalized sum direction, retaining separate color lanes.
"""
from collections import Counter
import math,random

def validate(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or
        any(type(r) is not list or len(r)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in r) for r in g)):
        raise ValueError('rectangular 1..30 exact-integer grid required')

def emitters(g):
    validate(g);h,w=len(g),len(g[0]);counts=Counter(v for row in g for v in row)
    bg=min(counts,key=lambda v:(-counts[v],v));cores=[];groups=[]
    for r in range(h-1):
        for c in range(w-1):
            co=g[r][c]
            if co==bg or any(g[r+a][c+b]!=co for a in (0,1) for b in (0,1)):continue
            frame=[(r+a,c+b) for a in range(-1,3) for b in range(-1,3)
                   if not(0<=a<=1 and 0<=b<=1) and 0<=r+a<h and 0<=c+b<w]
            if any(g[y][x]==co for y,x in frame) or sum(g[y][x]!=bg for y,x in frame)<4:continue
            cores.append((r,c,co))
            for y,x in frame:
                if g[y][x]==bg:
                    dr=-1 if y<r else 1 if y>r+1 else 0
                    dc=-1 if x<c else 1 if x>c+1 else 0
                    groups.append({'p':[(y,x,co)],'v':(dr,dc)})
    return bg,cores,groups

def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def trunc(n,d):return (1 if n>=0 else -1)*(abs(n)//d)
def point(p,v,n):
    m=max(map(abs,v));return (p[0]+trunc(n*v[0],m),p[1]+trunc(n*v[1],m),p[2])

def intersection(p,v,q,u,h,w):
    den=cross(v,u)
    if den==0:return None
    delta=(q[0]-p[0],q[1]-p[1]);tn=cross(delta,u);sn=cross(delta,v)
    if den<0:den,tn,sn=-den,-tn,-sn
    if tn<=0 or sn<=0:return None
    rr=p[0]*den+tn*v[0];cc=p[1]*den+tn*v[1]
    if not(0<=rr<h*den and 0<=cc<w*den):return None
    ka=(tn*max(map(abs,v))+den-1)//den-1
    kb=(sn*max(map(abs,u))+den-1)//den-1
    return ka,kb

def trace(g,*,rival=None):
    bg,cores,groups=emitters(g);h,w=len(g),len(g[0]);segments=[];events=[]
    if rival=='cardinal_only':groups=[x for x in groups if 0 in x['v']]
    if rival=='diagonal_only':groups=[x for x in groups if 0 not in x['v']]
    for iteration in range(128):
        candidates=[]
        if rival!='no_merge':
            for i,a in enumerate(groups):
                for j,b in enumerate(groups[:i]):
                    for p in a['p']:
                        for q in b['p']:
                            k=intersection(p,a['v'],q,b['v'],h,w)
                            if k is not None:
                                ka,kb=k;candidates.append((max(ka,kb),ka+kb,i,j,ka,kb))
        if not candidates:break
        mins={i:10**9 for i in range(len(groups))}
        for _,_,i,j,ka,kb in candidates:mins[i]=min(mins[i],ka);mins[j]=min(mins[j],kb)
        eligible=[c for c in candidates if c[4]==mins[c[2]] and c[5]==mins[c[3]]]
        _,_,i,j,ka,kb=min(eligible or candidates);a,b=groups[i],groups[j]
        new=[]
        for grp,k in ((a,ka),(b,kb)):
            cells=[point(p,grp['v'],n) for p in grp['p'] for n in range(k+1)]
            segments.append({'cells':cells,'colors':sorted({p[2] for p in grp['p']})})
            new.extend(point(p,grp['v'],k) for p in grp['p'])
        v,u=a['v'],b['v'];m,n=max(map(abs,v)),max(map(abs,u))
        nv=(v[0]*n+u[0]*m,v[1]*n+u[1]*m);div=math.gcd(*nv)
        if not div:raise ValueError('opposed head-on collision is outside the admitted grammar')
        nv=tuple(x//div for x in nv)
        if rival=='ignore_fraction':nv=tuple((x>0)-(x<0) for x in nv)
        events.append({'fronts_a':a['p'],'fronts_b':b['p'],'steps_a':ka,'steps_b':kb,'direction':nv})
        groups=[x for k,x in enumerate(groups) if k not in (i,j)]+[{'p':new,'v':nv}]
    else:raise ValueError('collision budget exceeded')
    for grp in groups:
        segments.append({'cells':[point(p,grp['v'],n) for p in grp['p'] for n in range(2*max(h,w)+1)],
                         'colors':sorted({p[2] for p in grp['p']})})
    return bg,segments,events

def solve(g,finish='trace',*,rival=None):
    if finish not in ('trace','mark_merged'):raise ValueError('unknown finish')
    bg,segments,_=trace(g,rival=rival);out=[r[:] for r in g];h,w=len(g),len(g[0])
    for seg in segments:
        mark=finish=='mark_merged' and len(seg['colors'])>=2
        if rival=='no_finish':mark=False
        elif rival=='mark_all' and finish=='mark_merged':mark=True
        elif rival=='pair_only' and finish=='mark_merged':mark=len(seg['colors'])==2
        for r,c,co in seg['cells']:
            if 0<=r<h and 0<=c<w and g[r][c] in (bg,co):out[r][c]=5 if mark else co
    return out

def rivals(finish):
    return ['no_merge','ignore_fraction','cardinal_only','diagonal_only']+(['no_finish','mark_all','pair_only'] if finish=='mark_merged' else [])

def rotate(g,n):
    for _ in range(n%4):g=[list(r) for r in zip(*g[::-1])]
    return g

def scene(seed,index,size):
    rng=random.Random(seed*1000003+index*7907+19);bg,shield=(8,3) if index%2==0 else (0,8)
    palette=[1,2,4,6,7,9];rng.shuffle(palette);g=[[bg]*size for _ in range(size)]
    r=size//2-1;cols=(3,size//2,size-4)
    def core(y,x,color,ports):
        for a in range(-1,3):
            for b in range(-1,3):
                g[y+a][x+b]=color if 0<=a<=1 and 0<=b<=1 else bg if (a,b) in ports else shield
    diagonals={(-1,-1),(-1,2),(2,-1),(2,2)}
    for j,c in enumerate(cols):core(r,c,palette[j],diagonals if j<2 else {(-1,0),(2,0)})
    core(size-4,1,palette[3],{(0,2)})
    g=rotate(g,seed%4)
    if index%3==2:g=[row[::-1] for row in g]
    return g

def bank(seed):
    for attempt in range(64):
        s=seed+attempt*104729
        demos=[scene(s,i,20+2*(i%3)) for i in range(6)]
        if all(any(solve(g,mode,rival=r)!=solve(g,mode) for g in demos[:2])
               for mode in ('trace','mark_merged') for r in rivals(mode)):
            queries=[scene(s,20+i,n) for i,n in enumerate((18,22,26,30))]
            random.Random(seed^0xE12F9A14).shuffle(queries)
            return demos,queries
    raise ValueError('no distinguishing pair within bounded teaching search')
