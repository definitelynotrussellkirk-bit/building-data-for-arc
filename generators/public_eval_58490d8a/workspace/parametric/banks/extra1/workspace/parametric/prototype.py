"""Explicit object records, occupied-area selection, and a finite rival vocabulary."""
from collections import Counter
SCOPES=('all','largest_per_color')
RIVALS=('all','largest_per_color','smallest_per_color','modal_size_class','bbox_largest',
        'all_4connected','largest_4connected','pixel_count','distinct_shapes','largest_distinct_shapes',
        'count_legend','global_max_area','one_per_color','paint_contiguous','sort_legend_numeric',
        'reverse_legend','foreground_count')


def checked_grid(g):
    if (type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30 or
        any(type(row) is not list or len(row)!=len(g[0]) for row in g) or
        any(type(v) is not int or not 0<=v<=9 for row in g for v in row)):
        raise ValueError('rectangular exact-integer 0..9 grid required')


def extract(g,connectivity=8):
    checked_grid(g)
    zeros=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==0]
    if not zeros:raise ValueError('black chart missing')
    r0=min(r for r,c in zeros);r1=max(r for r,c in zeros);c0=min(c for r,c in zeros);c1=max(c for r,c in zeros)
    counts=Counter(v for row in g for v in row)
    bg=min(counts,key=lambda v:(-counts[v],v))
    if bg==0:raise ValueError('canvas background must dominate the black chart')
    seeds=[{'row':r-r0,'column':c-c0,'color':g[r][c]} for r in range(r0,r1+1) for c in range(c0,c1+1) if g[r][c]!=0]
    if not seeds or len({s['row'] for s in seeds})!=len(seeds) or len({s['color'] for s in seeds})!=len(seeds):
        raise ValueError('one legend seed per unique row/color required')
    remaining={(r,c) for r,row in enumerate(g) for c,v in enumerate(row)
               if v not in (0,bg) and not(r0<=r<=r1 and c0<=c<=c1)}
    deltas=[(dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if (dr or dc) and (connectivity==8 or abs(dr)+abs(dc)==1)]
    objects=[]
    while remaining:
        start=min(remaining);remaining.remove(start);cells={start};stack=[start];color=g[start[0]][start[1]]
        while stack:
            r,c=stack.pop()
            for dr,dc in deltas:
                p=r+dr,c+dc
                if p in remaining and g[p[0]][p[1]]==color:
                    remaining.remove(p);cells.add(p);stack.append(p)
        top=min(r for r,c in cells);left=min(c for r,c in cells);hh=max(r for r,c in cells)-top+1;ww=max(c for r,c in cells)-left+1
        objects.append({'color':color,'cells':sorted(cells),'area':len(cells),'bbox_area':hh*ww,
                        'shape':tuple(sorted((r-top,c-left) for r,c in cells))})
    return {'background':bg,'top':r0,'left':c0,'height':r1-r0+1,'width':c1-c0+1,'seeds':seeds,'objects':objects}


def solve(g,scope='all',rival=None):
    if scope not in SCOPES:raise ValueError('unknown count_scope')
    policy=rival or scope
    if policy not in RIVALS:raise ValueError('unknown rival')
    info=extract(g,4 if policy in ('all_4connected','largest_4connected') else 8)
    out=[[0]*info['width'] for _ in range(info['height'])];seeds=info['seeds'];objects=info['objects']
    colors=[s['color'] for s in seeds]
    if policy=='sort_legend_numeric':colors=sorted(colors)
    if policy=='reverse_legend':colors=colors[::-1]
    for seed,color in zip(seeds,colors):
        obs=[o for o in objects if o['color']==color]
        mode=scope if policy in ('paint_contiguous','sort_legend_numeric','reverse_legend') else policy
        chosen=obs
        if obs and mode in ('largest_per_color','largest_4connected','largest_distinct_shapes'):
            maximum=max(o['area'] for o in obs);chosen=[o for o in obs if o['area']==maximum]
        elif obs and mode=='bbox_largest':
            maximum=max(o['bbox_area'] for o in obs);chosen=[o for o in obs if o['bbox_area']==maximum]
        elif obs and mode=='smallest_per_color':
            minimum=min(o['area'] for o in obs);chosen=[o for o in obs if o['area']==minimum]
        elif obs and mode=='modal_size_class':
            histogram=Counter(o['area'] for o in obs);area=max(histogram,key=lambda a:(histogram[a],a));chosen=[o for o in obs if o['area']==area]
        elif mode=='global_max_area':
            maximum=max((o['area'] for o in objects),default=0);chosen=[o for o in obs if o['area']==maximum]
        number=len(chosen)
        if mode=='pixel_count':number=sum(o['area'] for o in obs)
        elif mode in ('distinct_shapes','largest_distinct_shapes'):number=len({o['shape'] for o in chosen})
        elif mode=='count_legend':number=len(obs)+1
        elif mode=='one_per_color':number=int(bool(obs))
        elif mode=='foreground_count':number=len(objects)
        step=1 if policy=='paint_contiguous' else 2
        for index in range(number):
            c=seed['column']+step*index
            if c<info['width']:out[seed['row']][c]=color
    return out
