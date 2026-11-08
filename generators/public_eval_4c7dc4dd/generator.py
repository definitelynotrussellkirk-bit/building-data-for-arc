"""Noisy framed analogies: learn a patch operation, then transfer it.

A complete outer group supplies the input/output relation. The other group
contains a new pattern and one empty square. Supported operators are routed
endpoint completion, two-axis reflection closure, and periodic-texture mask
complement. No original grids or answers are consulted by this implementation.
"""
import random
RULE_TASK_ID = 'ee_4c7dc4dd'
TASK_ID = 'public_eval_4c7dc4dd'
VERSION = '1.0.0'
SETTINGS = ('complete','changes_only')

def integer(v,lo,hi,name):
    if type(v) is not int or not lo<=v<=hi: raise ValueError(name+' must be an exact bounded integer')
    return v

def grid_check(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or
        any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g)):
        raise ValueError('expected rectangular integer-color grid with dimensions 1..30')

def line_complete(g):
    """The unique orthogonal chain has two equal-color terminal nodes."""
    n=len(g);nodes=[(r,c) for r in range(n) for c in range(n) if g[r][c]]
    if len(nodes)<3: raise ValueError('a routed chain needs endpoints and a bend')
    adjacent={p:[] for p in nodes};edges=[]
    for i,p in enumerate(nodes):
        for q in nodes[i+1:]:
            if p[0]!=q[0] and p[1]!=q[1]:continue
            between=[t for t in nodes if t not in (p,q) and
                     ((p[0]==q[0]==t[0] and min(p[1],q[1])<t[1]<max(p[1],q[1])) or
                      (p[1]==q[1]==t[1] and min(p[0],q[0])<t[0]<max(p[0],q[0])))]
            if not between:edges.append((p,q));adjacent[p].append(q);adjacent[q].append(p)
    ends=[p for p in nodes if len(adjacent[p])==1]
    if len(ends)!=2 or any(len(adjacent[p]) not in (1,2) for p in nodes) or len(edges)!=len(nodes)-1:
        raise ValueError('markers are not a single orthogonal chain')
    seen=set();stack=[ends[0]]
    while stack:
        p=stack.pop()
        if p not in seen:seen.add(p);stack.extend(adjacent[p])
    color=g[ends[0][0]][ends[0][1]]
    if len(seen)!=len(nodes) or g[ends[1][0]][ends[1][1]]!=color or any(g[r][c]==color for r,c in nodes if (r,c) not in ends):
        raise ValueError('terminal and bend roles must be distinguished')
    out=[row[:] for row in g]
    for (r,c),(rr,cc) in edges:
        for y in range(min(r,rr),max(r,rr)+1):
            for x in range(min(c,cc),max(c,cc)+1):
                if not out[y][x]:out[y][x]=color
    return out

def reflect_complete(g):
    n=len(g);out=[[0]*n for _ in range(n)]
    for r in range(n):
        for c in range(n):
            vals={g[y][x] for y in (r,n-1-r) for x in (c,n-1-c)}-{0}
            if len(vals)>1:raise ValueError('inconsistent reflected colors')
            out[r][c]=next(iter(vals),0)
    return out

def complement(g,texture):
    n=len(g);mapping={}
    for r in range(n):
        for c in range(n):
            if g[r][c]:
                key=texture[r][c]
                if key in mapping and mapping[key]!=g[r][c]:raise ValueError('texture palette is inconsistent')
                mapping[key]=g[r][c]
    colors={v for row in texture for v in row}
    if 0 in colors or set(mapping)!=colors or len(set(mapping.values()))!=len(mapping):
        raise ValueError('query does not specify every texture color')
    return [[0 if g[r][c] else mapping[texture[r][c]] for c in range(n)] for r in range(n)]

def texture_of(a,b):
    n=len(a)
    if any(bool(a[r][c])==bool(b[r][c]) for r in range(n) for c in range(n)):raise ValueError('not complementary masks')
    t=[[a[r][c] or b[r][c] for c in range(n)] for r in range(n)]
    if not any(all(t[r][c]==t[r%pr][c%pc] for r in range(n) for c in range(n)) for pr in (1,2) for pc in (1,2)):
        raise ValueError('complement texture is not a small periodic tile')
    return t

def transforms(g):
    for flip in (False,True):
        a=[row[::-1] for row in g] if flip else [row[:] for row in g]
        for k in range(4):
            yield a
            a=[list(row) for row in zip(*a[::-1])]

def transfer_predictions(src,dst,q):
    # Recover an injective palette map and rigid orientation from a matched
    # sparse key; consume that map to transform the complete partner.
    if sum(v!=0 for row in src for v in row)>=sum(v!=0 for row in dst for v in row):return []
    answers=[]
    for a,b in zip(transforms(src),transforms(dst)):
        mapping={0:0};ok=True
        for ar,qr in zip(a,q):
            for v,u in zip(ar,qr):
                if (v==0)!=(u==0) or (v in mapping and mapping[v]!=u):ok=False
                mapping[v]=u
        if ok and len(set(mapping.values()))==len(mapping) and all(v in mapping for row in b for v in row):
            answers.append([[mapping[v] for v in row] for row in b])
    return answers

def infer(a,b,q):
    candidates=[]
    for name,func in (('route',line_complete),('reflect',reflect_complete)):
        for src,dst in ((a,b),(b,a)):
            try:
                if src!=dst and func(src)==dst:candidates.append((name,func(q)))
            except ValueError:pass
    for src,dst in ((a,b),(b,a)):
        candidates.extend(('transfer',out) for out in transfer_predictions(src,dst,q))
    try:candidates.append(('complement',complement(q,texture_of(a,b))))
    except ValueError:pass
    if not candidates or any(out!=candidates[0][1] for _,out in candidates):
        raise ValueError('reference relation absent or ambiguous on query')
    return candidates[0]

def analyze(g):
    grid_check(g);h,w=len(g),len(g[0])
    def border(r,c,rr,cc):
        color=g[r][c]
        return color!=0 and all(g[r][x]==color and g[rr][x]==color for x in range(c,cc+1)) and all(g[y][c]==color and g[y][cc]==color for y in range(r,rr+1))
    frames=[]
    for size in range(min(h,w),4,-1):
        found=[]
        for r in range(h-size+1):
            for c in range(w-size+1):
                if border(r,c,r+size-1,c+size-1):
                    patch=[row[c+1:c+size-1] for row in g[r+1:r+size-1]]
                    if any(0 in row for row in patch):found.append((r,c,r+size-1,c+size-1,patch))
        if len(found)==4:
            frames=found;break
    if len(frames)!=4:raise ValueError('need four equal framed patches')
    if any(not (a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1]) for i,a in enumerate(frames) for b in frames[i+1:]):
        raise ValueError('patch frames overlap')
    blanks=[i for i,f in enumerate(frames) if not any(v for row in f[4] for v in row)]
    if len(blanks)!=1:raise ValueError('need one blank patch')
    blank=blanks[0];choices=[]
    for mate in range(4):
        if mate==blank:continue
        pair=(frames[blank],frames[mate]);rlo=min(f[0] for f in pair);clo=min(f[1] for f in pair);rhi=max(f[2] for f in pair);chi=max(f[3] for f in pair)
        for r in range(rlo):
            for c in range(clo):
                if not g[r][c]:continue
                for rr in range(rhi+1,h):
                    if g[rr][c]!=g[r][c]:continue
                    for cc in range(chi+1,w):
                        if any(r<f[0] and c<f[1] and f[2]<rr and f[3]<cc for i,f in enumerate(frames) if i not in (blank,mate)):continue
                        if border(r,c,rr,cc):choices.append(((rr-r+1)*(cc-c+1),mate,(r,c,rr,cc)))
    if not choices:raise ValueError('cannot find outer query group')
    choices.sort();_,mate,outer=choices[0];ref=[f[4] for i,f in enumerate(frames) if i not in (blank,mate)];q=frames[mate][4]
    op,out=infer(*ref,q)
    return {'frames':frames,'blank':blank,'mate':mate,'outer':outer,'reference':ref,'query':q,'operator':op,'completed':out}

def render(q,out,mode):
    return out if mode=='complete' else [[v if v!=q[r][c] else 0 for c,v in enumerate(row)] for r,row in enumerate(out)]

def solve(g,mode='complete'):
    if type(mode) is not str or mode not in SETTINGS:raise ValueError('unknown output view')
    a=analyze(g);return render(a['query'],a['completed'],mode)

def rule_mirror(g):return solve(g)

def _patches(rng,n,kind,refcols,qcols):
    def route(cols):
        a,b=cols;g=[[0]*n for _ in range(n)]
        row=rng.randrange(1,n-1)
        pts=[(0,0),(row,0),(row,n-1),(n-1,n-1)] if rng.randrange(2) else [(0,n-1),(0,0),(n-1,0)]
        for i,(r,c) in enumerate(pts):g[r][c]=a if i in (0,len(pts)-1) else b
        for _ in range(rng.randrange(4)):g=[list(row) for row in zip(*g[::-1])]
        return g
    def sym(cols):
        g=[[0]*n for _ in range(n)];k=max(2,n//2)
        # Off-center asymmetry and two colors defeat single-axis completion.
        cells=[(0,1,cols[0]),(1,0,cols[1]),(1,1,cols[0])]
        for r,c,v in cells:g[r][c]=v
        if k>2:
            for r in range(k):
                for c in range(k):
                    if rng.random()<0.45:g[r][c]=rng.choice(cols)
        for _ in range(rng.randrange(4)):g=[list(row) for row in zip(*g[::-1])]
        return g
    if kind=='route':
        a=route(refcols);b=line_complete(a);q=route(qcols)
    elif kind=='reflect':
        a=[[0]*n for _ in range(n)];a[0][1]=a[1][0]=refcols[0];a[1][1]=a[1][2]=refcols[1]
        b=[[refcols[1]]*n for _ in range(n)]
        for r,c,v in ((0,0,0),(0,1,refcols[0]),(1,0,refcols[0])):
            for rr in (r,n-1-r):
                for cc in (c,n-1-c):b[rr][cc]=v
        # The completed exemplar, not a fixed learned bitmap, specifies texture.
        for r in range(2,n-2):
            for c in range(2,n-2):
                if rng.random()<0.2:
                    for rr in (r,n-1-r):
                        for cc in (c,n-1-c):b[rr][cc]=refcols[0]
        turn=rng.randrange(8);a=list(transforms(a))[turn];b=list(transforms(b))[turn]
        q=[[0 if not v else qcols[refcols.index(v)] for v in row] for row in list(transforms(a))[rng.randrange(8)]]
    else:
        tile=rng.choice(('solid','checker','rows','columns'))
        def color(r,c,cols):return cols[0] if tile=='solid' else cols[(r+c if tile=='checker' else r if tile=='rows' else c)%2]
        mask={(r,c) for r in range(n) for c in range(n) if rng.random()<0.4};mask|={(0,0),(0,1),(1,0)};mask.discard((n-1,n-1))
        a=[[color(r,c,refcols) if (r,c) in mask else 0 for c in range(n)] for r in range(n)]
        b=[[0 if (r,c) in mask else color(r,c,refcols) for c in range(n)] for r in range(n)]
        qm={(r,c) for r in range(n) for c in range(n) if rng.random()<0.35};qm|={(0,0),(0,1),(1,0)};qm.discard((n-1,n-1))
        q=[[color(r,c,qcols) if (r,c) in qm else 0 for c in range(n)] for r in range(n)]
    return a,b,q

def _construct(rng,h,w,n,kind):
    cols=rng.sample(list(range(1,10)),9);frame,outer0,outer1=cols[:3];a,b,q=_patches(rng,n,kind,cols[3:5],cols[5:7])
    noise=cols[1:];g=[[noise[(r*3+c)%len(noise)] for c in range(w)] for r in range(h)]
    for r in range(h):
        for c in range(w):
            if rng.random()<0.12:g[r][c]=rng.choice(noise+[0])
    groups=[[a,b],[q,[[0]*n for _ in range(n)]]];rng.shuffle(groups)
    for gi,patches in enumerate(groups):
        r0=0 if gi==0 else h-n-4;r1=r0+n+3;co=(outer0,outer1)[gi]
        for c in range(w):g[r0][c]=g[r1][c]=co
        for r in range(r0,r1+1):g[r][0]=g[r][w-1]=co
        rng.shuffle(patches)
        for j,p in enumerate(patches):
            y=r0+1;x=1 if j==0 else w-n-3
            for r in range(n+2):
                for c in range(n+2):g[y+r][x+c]=frame if r in (0,n+1) or c in (0,n+1) else p[r-1][c-1]
    if rng.randrange(2):g=[row[::-1] for row in g]
    if rng.randrange(2):g=g[::-1]
    if h==w and rng.randrange(2):g=[list(row) for row in zip(*g)]
    return g

def scene(seed,index,kind):
    integer(seed,0,2**63-1,'seed');integer(index,0,5 if kind=='demo' else 3,'index')
    if kind not in ('demo','query'):raise ValueError('invalid kind')
    dims=((21,22,5),(24,25,6),(25,27,6),(27,28,7),(28,29,7),(29,28,7)) if kind=='demo' else ((23,24,5),(25,26,6),(28,29,7),(30,30,8))
    h,w,n=dims[index];op=('route','reflect','complement','reflect','route','complement')[index] if kind=='demo' else ('complement','route','reflect','complement')[index]
    rng=random.Random(f'4c7dc4dd:v1:{seed}:{kind}:{index}')
    return _construct(rng,h,w,n,op)

def generate(seed=0,sample_index=0,difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**63-1,'sample_index')
    if difficulty is None:difficulty='medium'
    if difficulty not in ('easy','medium','hard','mixed'):raise ValueError('unsupported difficulty')
    rng=random.Random(f'4c7dc4dd:base:{seed}:{sample_index}:{difficulty}')
    dims={'easy':(21,22,5),'medium':(26,27,6),'hard':(30,30,8),'mixed':rng.choice(((21,22,5),(26,27,6),(30,30,8)))}[difficulty]
    return _construct(rng,*dims,('route','reflect','complement')[sample_index%3])

def self_check(g,difficulty=None):
    try:analyze(g)
    except (ValueError,TypeError,IndexError) as e:return [str(e)]
    return []
