"""General independent model: infer color roles, expand, then inspect connectivity."""
from collections import Counter,deque


def grid_check(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('Expected a nonempty <=30x30 grid')
    if any(type(r) is not list or len(r)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in r) for r in g):
        raise ValueError('Expected rectangular exact integer colors')


def bbox(cells):
    return min(r for r,c in cells),min(c for r,c in cells),max(r for r,c in cells),max(c for r,c in cells)


def overlap(a,b):
    return not (a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])


def crop(g,bb):
    r,c,R,C=bb;return [row[c:C+1] for row in g[r:R+1]]


def parts(g):
    grid_check(g);counts=Counter(v for row in g for v in row);most=max(counts.values())
    backgrounds=[v for v,n in counts.items() if n==most]
    if len(backgrounds)!=1:raise ValueError('Background must be uniquely modal')
    bg=backgrounds[0];colors=sorted(v for v in counts if v!=bg)
    positions={v:{(r,c) for r,row in enumerate(g) for c,x in enumerate(row) if x==v} for v in colors}
    boxes={v:bbox(positions[v]) for v in colors}
    def related(a,b):
        return overlap(boxes[a],boxes[b]) or any(q in positions[b] for r,c in positions[a] for q in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)))
    isolated=[v for v in colors if all(v==u or not related(v,u) for u in colors)]
    if len(isolated)!=1 or len(colors)<3:raise ValueError('Expected one monochrome layout and one disjoint multicolor motif')
    layout_color=isolated[0]
    motif_box=bbox([(r,c) for r,row in enumerate(g) for c,x in enumerate(row) if x not in (bg,layout_color)])
    if overlap(boxes[layout_color],motif_box):raise ValueError('Layout and motif bounding boxes must be disjoint')
    layout=crop(g,boxes[layout_color]);motif=crop(g,motif_box)
    if len(layout)*len(motif)>30 or len(layout[0])*len(motif[0])>30:raise ValueError('Expanded grid exceeds 30x30')
    return bg,layout_color,layout,motif


def expand(layout,motif,bg,layout_color):
    mh,mw=len(motif),len(motif[0])
    return [[motif[r%mh][c%mw] if layout[r//mh][c//mw]==layout_color else bg
             for c in range(len(layout[0])*mw)] for r in range(len(layout)*mh)]


def components(g,bg,same_color=False):
    unseen={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=bg};groups=[]
    while unseen:
        p=min(unseen);unseen.remove(p);q=deque([p]);cells=[];color=g[p[0]][p[1]]
        while q:
            r,c=q.popleft();cells.append((r,c))
            for v in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if v in unseen and (not same_color or g[v[0]][v[1]]==color):unseen.remove(v);q.append(v)
        groups.append(cells)
    return groups


def analyze(g):
    bg,color,layout,motif=parts(g);out=expand(layout,motif,bg,color)
    return {'background':bg,'layout_color':color,'layout':layout,'motif':motif,'output':out,'components':components(out,bg)}


def highlighted(out,groups):
    result=[row[:] for row in out];maximum=max(map(len,groups))
    for cells in groups:
        if len(cells)==maximum:
            for r,c in cells:result[r][c]=9
    return result


def solve(g,finish='expand_only'):
    if finish not in ('expand_only','highlight_largest'):raise ValueError('Invalid finish')
    info=analyze(g)
    return info['output'] if finish=='expand_only' else highlighted(info['output'],info['components'])


BASE_RIVALS=('identity','opposite_setting','solid_mask','mirror_layout','monochrome_motif','zero_background')
SELECTOR_RIVALS=('preexpansion_component','samecolor_components','first_component','last_component')

def rivals(finish):
    return BASE_RIVALS+(SELECTOR_RIVALS if finish=='highlight_largest' else ())


def rival(g,finish,name):
    if name=='identity':return [r[:] for r in g]
    if name=='opposite_setting':return solve(g,'highlight_largest' if finish=='expand_only' else 'expand_only')
    info=analyze(g);bg=info['background'];color=info['layout_color'];layout=info['layout'];motif=info['motif'];out=info['output']
    if name=='solid_mask':out=expand([[color]*len(layout[0]) for _ in layout],motif,bg,color)
    elif name=='mirror_layout':out=expand([row[::-1] for row in layout],motif,bg,color)
    elif name=='monochrome_motif':
        v=Counter(v for row in motif for v in row if v!=bg).most_common(1)[0][0]
        out=expand(layout,[[v if x!=bg else bg for x in row] for row in motif],bg,color)
    elif name=='zero_background':return [[0 if v==bg else v for v in row] for row in solve(g,finish)]
    elif name=='preexpansion_component':
        groups=components(layout,bg);large=max(map(len,groups));selected={p for cells in groups if len(cells)==large for p in cells}
        mh,mw=len(motif),len(motif[0])
        return [[9 if v!=bg and (r//mh,c//mw) in selected else v for c,v in enumerate(row)] for r,row in enumerate(out)]
    elif name=='samecolor_components':return highlighted(out,components(out,bg,True))
    elif name in ('first_component','last_component'):
        cells=set(info['components'][0 if name=='first_component' else -1])
        return [[9 if (r,c) in cells else v for c,v in enumerate(row)] for r,row in enumerate(out)]
    else:raise ValueError('Unknown rival')
    return out if finish=='expand_only' else highlighted(out,components(out,bg))
