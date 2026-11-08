"""Independent contour assembly model; no original examples or generated labels stored."""
from collections import deque


def grid_check(g):
    if type(g) is not list or not 1<=len(g)<=30 or type(g[0]) is not list or not 1<=len(g[0])<=30:
        raise ValueError('Expected a nonempty <=30x30 grid')
    if any(type(row) is not list or len(row)!=len(g[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in g):
        raise ValueError('Expected rectangular exact integer colors 0..9')


def transpose(g):
    return [list(row) for row in zip(*g)]


def components(g):
    unseen={(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v!=0}
    out=[]
    while unseen:
        start=min(unseen);unseen.remove(start);q=deque([start]);cells=[];color=g[start[0]][start[1]]
        while q:
            r,c=q.popleft();cells.append((r,c))
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen and g[p[0]][p[1]]==color:unseen.remove(p);q.append(p)
        out.append({'color':color,'cells':cells})
    return out


def parts(g):
    grid_check(g);objects=components(g);h=len(g);w=len(g[0])
    walls=[o for o in objects if (min(r for r,c in o['cells'])==0 and max(r for r,c in o['cells'])==h-1) or (min(c for r,c in o['cells'])==0 and max(c for r,c in o['cells'])==w-1)]
    if len(walls)!=1:raise ValueError('Expected exactly one connected full-span wall')
    wall=walls[0];vertical=max(r for r,c in wall['cells'])-min(r for r,c in wall['cells'])==h-1
    work=transpose(g) if vertical else [row[:] for row in g]
    objects=components(work);wall=next(o for o in objects if len({c for r,c in o['cells']})==len(work[0]))
    pieces=[]
    for obj in objects:
        if obj is wall:continue
        r0=min(r for r,c in obj['cells']);c0=min(c for r,c in obj['cells'])
        cells=[(r-r0,c-c0) for r,c in obj['cells']];width=1+max(c for r,c in cells)
        top=[min(r for r,c in cells if c==j) for j in range(width)]
        bottom=[max(r for r,c in cells if c==j) for j in range(width)]
        if any(sum(c==j for r,c in cells)!=bottom[j]-top[j]+1 for j in range(width)):
            raise ValueError('Pieces must be convex along the wall-normal axis')
        pieces.append({**obj,'local':cells,'origin':(r0,c0),'width':width,'top':top,'bottom':bottom})
    if not pieces:raise ValueError('At least one loose piece required')
    return work,wall,pieces,vertical


def analyze(g):
    work,wall,pieces,vertical=parts(g);h=len(work);w=len(work[0])
    out=[[0]*w for _ in range(h)];depth_grid=[[0]*w for _ in range(h)];owners=[[-1]*w for _ in range(h)]
    for r,c in wall['cells']:out[r][c]=wall['color'];owners[r][c]=0
    nodes=[0]
    def search(pending,out,depth_grid,owners,steps):
        nodes[0]+=1
        if nodes[0]>20000:raise ValueError('Assembly search budget exceeded')
        if not pending:return out,steps

        frontier={side:[(min if side=='up' else max)(r for r in range(h) if out[r][c]!=0) for c in range(w)] for side in ('up','down')}
        available=[]
        for i in pending:
            obj=pieces[i];matches=[]
            for side in ('up','down'):
                profile=obj['bottom'] if side=='up' else obj['top'];sgn=-1 if side=='up' else 1
                for col in range(w-obj['width']+1):
                    boundary=frontier[side][col:col+obj['width']]
                    if len(set(boundary))==1:continue  # flat contact is not an interlocking socket
                    row=boundary[0]+sgn-profile[0]
                    if any(row+profile[j]!=v+sgn for j,v in enumerate(boundary)):continue
                    moved=[(row+r,col+c) for r,c in obj['local']]
                    if any(not (0<=r<h and 0<=c<w) or out[r][c]!=0 for r,c in moved):continue
                    contact={owners[r][col+j] for j,r in enumerate(boundary)}
                    if len(contact)!=1:continue
                    predecessor=next(iter(contact))
                    if predecessor and pieces[predecessor-1]['width']!=obj['width']:continue
                    depth=1+max(depth_grid[r][col+j] for j,r in enumerate(boundary))
                    matches.append({'id':i,'cells':moved,'depth':depth,'side':side,'origin':(row,col)})
            if matches:available.extend(matches)
        for step in available:
            i=step['id'];next_out=[row[:] for row in out];next_depth=[row[:] for row in depth_grid];next_owners=[row[:] for row in owners]
            for r,c in step['cells']:
                next_out[r][c]=pieces[i]['color'];next_depth[r][c]=step['depth'];next_owners[r][c]=i+1
            result=search([j for j in pending if j!=i],next_out,next_depth,next_owners,steps+[step])
            if result is not None:return result
        return None
    result=search(list(range(len(pieces))),out,depth_grid,owners,[])
    if result is None:raise ValueError('No complete interlocking assembly')
    out,steps=result
    return {'output':transpose(out) if vertical else out,'work_output':out,'wall':wall,'pieces':pieces,'steps':steps,'vertical':vertical}


def render(info,selected=None,keep=None):
    out=[row[:] for row in info['work_output']]
    if keep is not None:
        for step in info['steps']:
            if not keep(step):
                for r,c in step['cells']:out[r][c]=0
    if selected is not None:
        for step in info['steps']:
            if selected(step):
                for r,c in step['cells']:out[r][c]=9
    return transpose(out) if info['vertical'] else out


def solve(g,finish='assemble_only'):
    if finish not in ('assemble_only','highlight_deepest'):raise ValueError('Invalid finish')
    info=analyze(g)
    if finish=='assemble_only':return info['output']
    deepest=max(s['depth'] for s in info['steps'])
    return render(info,lambda s:s['depth']==deepest)


BASE_RIVALS=('identity','erase_loose','first_wave','one_side','opposite_setting')
SELECTOR_RIVALS=('largest_piece','highest_color','first_reading','last_reading')


def rivals(finish):
    return BASE_RIVALS+(SELECTOR_RIVALS if finish=='highlight_deepest' else ())


def rival(g,finish,name):
    if name=='identity':return [r[:] for r in g]
    if name=='opposite_setting':return solve(g,'highlight_deepest' if finish=='assemble_only' else 'assemble_only')
    info=analyze(g);deep=max(s['depth'] for s in info['steps'])
    select=(lambda s:s['depth']==deep) if finish=='highlight_deepest' else None
    if name=='erase_loose':return render(info,keep=lambda s:False)
    if name=='first_wave':return render(info,select,lambda s:s['depth']==1)
    if name=='one_side':return render(info,select,lambda s:s['side']=='down')
    p=info['pieces']
    if name=='largest_piece':ids={i for i,o in enumerate(p) if len(o['cells'])==max(len(x['cells']) for x in p)}
    elif name=='highest_color':ids={i for i,o in enumerate(p) if o['color']==max(x['color'] for x in p)}
    elif name=='first_reading':ids={0}
    elif name=='last_reading':ids={len(p)-1}
    else:raise ValueError('Unknown rival')
    return render(info,lambda s:s['id'] in ids)
