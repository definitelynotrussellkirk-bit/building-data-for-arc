"""Independent Python claims for marked orthogonal path repair.

Racket is the label authority. This module also exposes recovered topology for
source-bound counterfactuals and finite shortcut tests.
"""
from __future__ import annotations
from collections import Counter, deque

DIRECTIONS=((-1,0),(1,0),(0,-1),(0,1))
MODES=('reverse_marked','preserve_visible')


def checked_grid(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('grid dimensions must lie in 1..30')
    width=len(grid[0])
    if any(type(row) is not list or len(row)!=width or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('rectangular exact-integer colors required')
    return len(grid),width


def recover_paths(grid):
    h,w=checked_grid(grid)
    def at(p):return grid[p[0]][p[1]] if 0<=p[0]<h and 0<=p[1]<w else -1
    def plus(p,d):return p[0]+d[0],p[1]+d[1]
    colors=sorted({v for row in grid for v in row}-{0,2,4})
    records=[]
    for color in colors:
        def compatible(p):return at(p) in (color,2)
        def corner(p,d):
            def support(e):
                q=plus(p,e)
                return compatible(q) or (compatible(plus(q,e)) and (compatible(plus(plus(q,e),e)) or compatible(plus(plus(plus(q,e),e),e))))
            return at(p)==2 or (at(p)==color and any(support(e) for e in ((d[1],d[0]),(-d[1],-d[0]))))
        def end(p,d):
            if corner(p,d):return p
            last=p;q=plus(p,d)
            while at(q)!=-1:
                if compatible(q):
                    last=q
                    if corner(q,d):return q
                q=plus(q,d)
            return last
        mask={(r,c) for r in range(h) for c in range(w) if grid[r][c]==color}
        for r in range(h):
            for c in range(w):
                p=(r,c)
                for d in ((0,1),(1,0)):
                    for distance in (1,2):
                        q=plus(p,(distance*d[0],distance*d[1]))
                        evidence=distance==1 or compatible(plus(p,(-2*d[0],-2*d[1]))) or compatible(plus(q,(2*d[0],2*d[1])))
                        def transverse(x):return any(compatible(plus(x,e)) for e in ((d[1],d[0]),(-d[1],-d[0])))
                        evidence=evidence and not (distance==2 and transverse(p) and transverse(q))
                        if evidence and compatible(p) and compatible(q) and (at(p)==color or at(q)==color):
                            a=end(p,(-d[0],-d[1]));b=end(q,d)
                            mask.update((rr,cc) for rr in range(a[0],b[0]+1) for cc in range(a[1],b[1]+1))
        records.append({'color':color,'cells':mask,'marked':any(at(p)==2 for p in mask)})
    return records


def observed_precedence(grid,records):
    relations=[]
    for i,a in enumerate(records):
        for b in records[i+1:]:
            votes=Counter(grid[r][c] for r,c in a['cells']&b['cells'] if grid[r][c] in (a['color'],b['color']))
            if votes:
                # A majority is a deterministic out-of-grammar extension.
                # The generated grammar requires consistent visible crossings.
                top=min(votes,key=lambda color:(-votes[color],color))
                relations.append((b['color'] if top==a['color'] else a['color'],top))
    return relations


def routed_cells(grid,record,*,ignore_yellow=False):
    if ignore_yellow:return set(record['cells'])
    h,w=len(grid),len(grid[0]);mask=record['cells'];removed=set();added=set()
    for r in range(h):
        for c in range(w):
            if grid[r][c]!=4:continue
            for dr,dc in DIRECTIONS:
                anchor=(r-dr,c-dc);old=(r-2*dr,c-2*dc)
                if anchor not in mask or old not in mask or (r,c) in mask:continue
                if not any((anchor[0]+er,anchor[1]+ec) in mask for er,ec in ((dc,dr),(-dc,-dr))):continue
                # The old arm must be terminal: removing the pivot separates it.
                todo=[old];seen={anchor};branch=set()
                while todo:
                    p=todo.pop()
                    if p in seen or p not in mask:continue
                    seen.add(p);branch.add(p)
                    todo.extend((p[0]+er,p[1]+ec) for er,ec in DIRECTIONS)
                removed.update(branch)
                rr,cc=anchor
                while 0<=rr<h and 0<=cc<w:
                    added.add((rr,cc));rr+=dr;cc+=dc
    return (mask-removed)|added


def order_for(records,relations,mode):
    marked={r['color']:r['marked'] for r in records}
    edges=[(b,a) if mode=='reverse_marked' and (marked[a] or marked[b]) else (a,b) for a,b in relations]
    pending=sorted(marked);order=[]
    while pending:
        available=[c for c in pending if not any(a in pending and b==c for a,b in edges)]
        # Cyclic or unobserved orders have a deterministic numeric fallback only.
        choice=available[0] if available else pending[0]
        order.append(choice);pending.remove(choice)
    return order


def analyze(grid):
    paths=recover_paths(grid)
    relations=observed_precedence(grid,paths)
    return {'paths':paths,'observed_under_over':relations}


def render(grid,data,mode='reverse_marked',*,ignore_yellow=False,reverse_relations=False):
    if mode not in MODES:raise ValueError('unknown crossing policy')
    relations=data['observed_under_over']
    if reverse_relations:relations=[(b,a)for a,b in relations]
    order=order_for(data['paths'],relations,mode)
    out=[[0]*len(grid[0]) for _ in grid]
    by_color={p['color']:p for p in data['paths']}
    for color in order:
        for r,c in routed_cells(grid,by_color[color],ignore_yellow=ignore_yellow):out[r][c]=color
    return out


def solve(grid,mode='reverse_marked'):
    return render(grid,analyze(grid),mode)


def validate(grid):
    """Reject missing topology/marker/precedence evidence, without mutating input."""
    data=analyze(grid);h,w=len(grid),len(grid[0])
    if not 2<=len(data['paths'])<=7:raise ValueError('at least two recoverable paths required')
    for rec in data['paths']:
        mask=rec['cells'];degrees={p:sum((p[0]+dr,p[1]+dc)in mask for dr,dc in DIRECTIONS)for p in mask}
        ends=[p for p,n in degrees.items()if n==1]
        if len(ends)!=2 or any(n not in (1,2)for n in degrees.values()):raise ValueError('a simple nonbranching path is required')
        if any(r not in (0,h-1) and c not in (0,w-1)for r,c in ends):raise ValueError('path ends must reach a boundary')
        todo=[ends[0]];seen=set()
        while todo:
            p=todo.pop()
            if p in seen:continue
            seen.add(p);todo.extend((p[0]+dr,p[1]+dc)for dr,dc in DIRECTIONS if (p[0]+dr,p[1]+dc)in mask and (p[0]+dr,p[1]+dc)not in seen)
        if seen!=mask:raise ValueError('disconnected path')
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            if v==2 and sum((r,c)in p['cells']for p in data['paths'])!=1:raise ValueError('red vertex must have one path owner')
            if v==4:
                owners=[]
                for rec in data['paths']:
                    mask=rec['cells']
                    for dr,dc in DIRECTIONS:
                        anchor=(r-dr,c-dc);old=(r-2*dr,c-2*dc)
                        if anchor in mask and old in mask and (r,c)not in mask and any((anchor[0]+er,anchor[1]+ec)in mask for er,ec in ((dc,dr),(-dc,-dr))):owners.append(rec['color'])
                if len(owners)!=1:raise ValueError('yellow direction must identify one pivot and path')
    for i,a in enumerate(data['paths']):
        for b in data['paths'][i+1:]:
            overlap=a['cells']&b['cells']
            votes={grid[r][c]for r,c in overlap if grid[r][c]in (a['color'],b['color'])}
            if overlap and len(votes)!=1:raise ValueError('crossing order must be visibly consistent')
    for mode in MODES:
        order=order_for(data['paths'],data['observed_under_over'],mode)
        marked={p['color']:p['marked']for p in data['paths']}
        for a,b in data['observed_under_over']:
            if mode=='reverse_marked' and (marked[a]or marked[b]):a,b=b,a
            if order.index(a)>=order.index(b):raise ValueError('cyclic crossing order')
    return data
