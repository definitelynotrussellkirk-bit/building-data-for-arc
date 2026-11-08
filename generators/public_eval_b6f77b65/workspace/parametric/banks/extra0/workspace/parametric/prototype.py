"""Colored posts and beams: erase cue colors and re-settle the support graph."""
from collections import Counter


def validate_grid(grid):
    if (type(grid) is not list or not 3<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30 or
        any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('expected exact-integer rectangular support scene')
    if any(grid[1]):raise ValueError('row one must separate the cue from the scene')
    return grid


def extract(grid):
    """Recover beams first so a same-color arriving post does not steal a joint.

    Horizontal beams are interiors of nonzero row runs, with a downward post
    at each endpoint. Posts end immediately before a beam in the raster. Such
    a support (or the floor) occludes one terminal stroke cell; retain that
    cell in the geometric post, clipping it when it rests on the floor again.
    A later post-on-post landing can expose the formerly occluded endpoint.
    """
    h,w=len(grid),len(grid[0]);beams=[];used=set()
    for r in range(2,h-1):
        c=0
        while c<w:
            if not grid[r][c]:c+=1;continue
            end=c+1
            while end<w and grid[r][end]:end+=1
            if (end-c>=3 and grid[r+1][c]==grid[r][c] and grid[r+1][end-1]==grid[r][end-1]
                    and len(set(grid[r][c+1:end-1]))==1):
                beams.append({'kind':'beam','color':grid[r][c+1],'r':r,'c':c+1,'length':end-c-2})
                used.update((r,j) for j in range(c+1,end-1))
            c=end
    posts=[]
    for c in range(w):
        r=2
        while r<h:
            if not grid[r][c] or (r,c) in used:r+=1;continue
            end=r+1
            while end<h and (end,c) not in used and grid[end][c]==grid[r][c]:end+=1
            hidden=end==h or (end,c) in used
            posts.append({'kind':'post','color':grid[r][c],'r':r,'c':c,'length':end-r+int(hidden),'hidden_endpoint':hidden})
            r=end
    return posts+beams


def settle(objects,height,removed,either=False,raw_support=False):
    survivors=[dict(x) for x in objects if x['color'] not in removed]
    def bottom(o):return o['r']+(o['length']-1 if o['kind']=='post' else 0)
    survivors.sort(key=lambda o:(-bottom(o),0 if o['kind']=='beam' else 1,o['c']))
    placed=[]
    for obj in survivors:
        original=obj['r'];obj['source_r']=original
        if obj['kind']=='post':
            end=height if obj['hidden_endpoint'] else height-1
            for lower in placed:
                if lower['kind']=='beam' and lower['c']<=obj['c']<lower['c']+lower['length']:
                    end=min(end,lower['r'])
                elif lower['kind']=='post' and lower['c']==obj['c']:
                    end=min(end,lower['r']-1)
            obj['r']=end-obj['length']+1
        else:
            r=height-1;left=obj['c'];right=left+obj['length']-1
            for lower in placed:
                lo=lower['c'];hi=lo+(lower['length']-1 if lower['kind']=='beam' else 0)
                if not (hi<left or lo>right):r=min(r,lower['r']-1)
            lp=[p for p in placed if p['kind']=='post' and p['c']==left-1]
            rp=[p for p in placed if p['kind']=='post' and p['c']==right+1]
            if raw_support:
                lp=[dict(p,r=p['source_r']) for p in lp]
                rp=[dict(p,r=p['source_r']) for p in rp]
            if either:
                for p in lp+rp:
                    if max(original,p['r'])<=bottom(p):r=min(r,max(original,p['r']))
            for a in ([] if either else lp):
                for b in rp:
                    support=max(original,a['r'],b['r'])
                    if support<=min(bottom(a),bottom(b)):r=min(r,support)
            obj['r']=r
        if obj['r']<original:raise ValueError('support graph requires upward motion')
        placed.append(obj)
    return placed


def render(grid,objects):
    out=[[0]*len(grid[0]) for _ in grid];out[0]=grid[0][:]
    for kind in ('post','beam'):
        for o in objects:
            if o['kind']!=kind:continue
            for i in range(o['length']):
                r=o['r']+(i if kind=='post' else 0);c=o['c']+(i if kind=='beam' else 0)
                if r<len(grid):out[r][c]=o['color']
    return out


def solve(grid,either=False,raw_support=False):
    validate_grid(grid)
    removed={v for v in grid[0] if v}
    return render(grid,settle(extract(grid),len(grid),removed,either,raw_support))


def scene(seed,index,stress=False):
    """Sample fresh nested/crossing support graphs, never load public fixtures.

    Coordinate intervals and member lengths are sampled before rasterization;
    colors are arbitrary roles, not hard-coded physical properties. Every
    minimum two-demo curriculum has a collapsing-base nested graph and a two-cue
    crossing graph. Query streams begin at 100, independently of demo count.
    """
    import random
    rng=random.Random(f'support-graphs-v1:{seed}:{index}')
    split=index%2==1
    if stress:
        h=w=30;ground=middle=upper=8;L=0;R=29
    else:
        ground=rng.randint(2,5);middle=rng.randint(2,5);upper=rng.randint(2,5)
        h=ground+middle+upper+rng.randint(3,8)
        w=rng.randint(23,30);L=rng.randint(0,1);R=w-1-rng.randint(0,1)
    b=h-ground;m=b-middle;t=m-upper
    palette=list(range(1,10));rng.shuffle(palette)
    a,bb,c,d,e,f,gg,hh,i=palette
    pieces=[]
    def post(col,top,stop,color):
        if stop-top<2:raise ValueError('each input support must have a visible downward leg')
        pieces.append({'kind':'post','color':color,'r':top,'c':col,'length':stop-top})
    def beam(left,right,row,color):
        if right-left<2:raise ValueError('beam needs nonempty interior')
        pieces.append({'kind':'beam','color':color,'r':row,'c':left+1,'length':right-left-1})
    if not split:
        divider=rng.randint(L+9,R-9)
        post(L,b,h,a);post(R,b,h,c);beam(L,R,b,bb)
        ll=L+1;lr=divider-1;rl=divider+1;rr=R-1
        post(ll,m,b,d);post(lr,m,b,e);beam(ll,lr,m,e)
        post(rl,m,b,f);post(rr,m,b,c);beam(rl,rr,m,f)
        tl=rng.randint(ll+1,lr-1);tr=rng.randint(rl+1,rr-1)
        # The minimum lesson must teach direct obstruction as well as side
        # support. In demo zero both top posts are selected for removal, so
        # the surviving top beam lands on the settled middle geometry. All
        # query profiles and the second demo retain their original palettes.
        post(tl,t,m,a if index==0 else f)
        post(tr,t,m,bb if index==0 else gg)
        beam(tl,tr,t,gg)
        cue=[a,bb] if index%4==0 else [a]
        if index>=100 and index%4==2:cue=[i]  # absent-color/no-op stressor
    else:
        left_end=L+rng.randint(4,7);right_start=left_end+rng.randint(2,4)
        post(L,b,h,a);post(left_end,b,h,bb);beam(L,left_end,b,bb)
        post(right_start,b,h,c);post(R,b,h,e);beam(right_start,R,b,d)
        ml=L+1;mr=right_start+1;nl=right_start+3;nr=R
        post(ml,m,b,f);post(mr,m,b,d);beam(ml,mr,m,e)
        post(nl,m,b,gg);post(nr,m,b,hh);beam(nl,nr,m,hh)
        tl=right_start;tr=rng.randint(nl+1,nr-1)
        post(tl,t,m,gg);post(tr,t,m,i);beam(tl,tr,t,bb)
        cue=[e,a]  # both cue colors matter: not a first-marker-only curriculum
        if index>=100 and index%4==3:cue=[bb,d]
    empty=[[0]*w for _ in range(h)]
    grid=render(empty,pieces)
    if rng.getrandbits(1):grid=[row[::-1] for row in grid]
    rng.shuffle(cue)
    for j,color in enumerate(cue):grid[0][j]=color
    return grid
