"""Independent beam-relay interpreter; no supplied grids or labels are embedded."""
from collections import deque

DIRS = ((-1, 0), (0, 1), (1, 0), (0, -1))
RIVALS = ('paint_all_objects', 'only_initial_hit', 'ignore_markers',
          'bbox_beams', 'highlight_largest', 'highlight_first', 'opposite_finish')


def grid_check(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
            or not 1 <= len(g[0]) <= 30 or any(type(row) is not list or len(row) != len(g[0])
            or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g)):
        raise ValueError('Expected a rectangular 1..30 exact-integer grid')


def parts(g):
    grid_check(g)
    if any(v not in (1, 2, 3, 4, 8) for row in g for v in row):
        raise ValueError('Beam input palette is 1,2,3,4,8')
    h, w = len(g), len(g[0]); todo={(r,c) for r in range(h) for c in range(w) if g[r][c] in (1,3)}
    objects=[]
    while todo:
        start=min(todo); todo.remove(start); stack=[start];cells={start}
        while stack:
            r,c=stack.pop()
            for dr,dc in DIRS:
                p=(r+dr,c+dc)
                if p in todo: todo.remove(p);cells.add(p);stack.append(p)
        markers=sorted(p for p in cells if g[p[0]][p[1]]==3)
        blue=cells-set(markers)
        if not blue or not markers: raise ValueError('Each relay needs blue body and green port')
        r0,c0=min(p[0] for p in cells),min(p[1] for p in cells)
        r1,c1=max(p[0] for p in cells),max(p[1] for p in cells)
        candidates=[]
        for dr,dc in DIRS:
            boundary=all((r==r0 if dr<0 else r==r1 if dr>0 else c==c0 if dc<0 else c==c1) for r,c in markers)
            if boundary and all((r-dr,c-dc) in blue for r,c in markers):candidates.append((dr,dc))
        if len(candidates)!=1:raise ValueError('Green port must identify a unique outward normal')
        if len(markers)>1 and any(abs(a[0]-b[0])+abs(a[1]-b[1])!=1 for a,b in zip(markers,markers[1:])):
            raise ValueError('Green port must be contiguous')
        objects.append({'cells':sorted(cells),'markers':markers,'direction':candidates[0],'bbox':(r0,c0,r1,c1)})
    gun=[(r,c) for r in range(h) for c in range(w) if g[r][c]==4]
    if len(gun)!=1:raise ValueError('Exactly one yellow emitter is required')
    r,c=gun[0];dirs=[(-dr,-dc) for dr,dc in DIRS if 0<=r+dr<h and 0<=c+dc<w and g[r+dr][c+dc]==2]
    if len(dirs)!=1:raise ValueError('Emitter needs exactly one adjacent red tail direction')
    dr,dc=dirs[0]
    red={(rr,cc) for rr in range(h) for cc in range(w) if g[rr][cc]==2}
    tail=set();rr,cc=r-dr,c-dc
    while 0<=rr<h and 0<=cc<w and g[rr][cc]==2:tail.add((rr,cc));rr-=dr;cc-=dc
    if red!=tail:raise ValueError('All red cells must form the emitter tail')
    return objects,gun[0],dirs[0]


def analyze(g, *, mode='normal'):
    objects,gun,direction=parts(g);h,w=len(g),len(g[0])
    lookup={p:i for i,o in enumerate(objects) for p in o['cells']}
    out=[[2 if v in (2,4) else 8 for v in row] for row in g]
    q=deque([(gun,direction,0)]);depths={};rays=[]
    while q:
        (r,c),(dr,dc),depth=q.popleft();r+=dr;c+=dc;path=[];hit=None
        while 0<=r<h and 0<=c<w:
            path.append((r,c));out[r][c]=2
            if (r,c) in lookup:hit=lookup[(r,c)];break
            r+=dr;c+=dc
        rays.append({'cells':path,'target':hit,'parent_depth':depth})
        if hit is None or hit in depths:continue
        depths[hit]=depth+1;o=objects[hit]
        for rr,cc in o['cells']:out[rr][cc]=2
        if mode=='only_initial_hit':continue
        if mode=='ignore_markers':
            r0,c0,r1,c1=o['bbox'];origin=(r0 if dr<0 else r1 if dr>0 else r,c0 if dc<0 else c1 if dc>0 else c)
            q.append((origin,(dr,dc),depth+1));continue
        markers=o['markers']
        if mode=='bbox_beams':
            r0,c0,r1,c1=o['bbox'];er,ec=o['direction']
            markers=[(r0 if er<0 else r1,cc) for cc in range(c0,c1+1)] if er else [(rr,c0 if ec<0 else c1) for rr in range(r0,r1+1)]
        q.extend((p,o['direction'],depth+1) for p in markers)
    return {'objects':objects,'depths':depths,'rays':rays,'output':out}


def solve(g, finish='trace_only', *, mode='normal'):
    if finish not in ('trace_only','highlight_deepest'):raise ValueError('Undeclared finish')
    info=analyze(g,mode=mode);out=info['output'];depths=info['depths']
    if finish=='highlight_deepest' and depths:
        deepest=max(depths.values())
        for i,d in depths.items():
            if d==deepest:
                for r,c in info['objects'][i]['cells']:out[r][c]=9
    return out


def rival(g,finish,name):
    if name not in RIVALS:raise ValueError('Unknown rival')
    if name in ('only_initial_hit','ignore_markers','bbox_beams'):return solve(g,finish,mode=name)
    if name=='opposite_finish':return solve(g,'trace_only' if finish=='highlight_deepest' else 'highlight_deepest')
    info=analyze(g);out=[row[:] for row in info['output']]
    if name=='paint_all_objects':
        for o in info['objects']:
            for r,c in o['cells']:out[r][c]=2
        if finish=='highlight_deepest' and info['depths']:
            for i,d in info['depths'].items():
                if d==max(info['depths'].values()):
                    for r,c in info['objects'][i]['cells']:out[r][c]=9
        return out
    # Wrong global selection is an added 9 highlight under either setting;
    # default demos refute the extra operation, alternative demos refute its key.
    if info['depths']:
        selected=max(info['depths'],key=lambda i:len(info['objects'][i]['cells'])) if name=='highlight_largest' else min(info['depths'])
        for r,c in info['objects'][selected]['cells']:out[r][c]=9
    return out
