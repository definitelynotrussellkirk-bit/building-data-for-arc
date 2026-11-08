"""Fresh waypoint scenes; exact Racket programs supply every returned label."""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from puzzle_generators.base import gen_ctx

HOME=Path(__file__).resolve().parents[2]
SETTINGS=('follow_final_leg','keep_initial_heading')
DIRS=((-1,0),(0,1),(1,0),(0,-1))
# Tip at origin, pointing north. Includes every supplied original motif class.
MOTIFS=(((0,0),(1,-1),(1,1)),((0,0),(1,-1),(1,0),(1,1)),
        ((0,0),(1,0),(2,-1),(2,1)),((0,0),(1,-1),(1,0),(1,1),(2,-1),(2,1)))

def cw(p):return (p[1],-p[0])
def spin(p,n):
    for _ in range(n):p=cw(p)
    return p

def cells_at(motif,tip,direction):
    n=DIRS.index(direction)
    return {(tip[0]+spin(p,n)[0],tip[1]+spin(p,n)[1]) for p in motif}

def components(cells):
    todo=set(cells);out=[]
    while todo:
        first=min(todo);todo.remove(first);component={first};queue=[first]
        while queue:
            r,c=queue.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    q=(r+dr,c+dc)
                    if q in todo:todo.remove(q);component.add(q);queue.append(q)
        out.append(component)
    return out

def heading(cells):
    candidates=[]
    for d in DIRS:
        dot=lambda p:p[0]*d[0]+p[1]*d[1]
        end=[p for p in cells if dot(p)==max(map(dot,cells))]
        if len(end)!=1 or sum(dot(p)==min(map(dot,cells)) for p in cells)<2:continue
        tip=end[0];perp=cw(d)
        reflected={(p[0]-2*((p[0]-tip[0])*perp[0]+(p[1]-tip[1])*perp[1])*perp[0],p[1]-2*((p[0]-tip[0])*perp[0]+(p[1]-tip[1])*perp[1])*perp[1]) for p in cells}
        if reflected==cells:candidates.append((tip,d))
    if len(candidates)!=1:raise ValueError('ambiguous cursor heading')
    return candidates[0]

def analyze(g):
    h,w=len(g),len(g[0]);bg=Counter(sum(g,[])).most_common(1)[0][0]
    sep=[c for c in range(w) if g[0][c]!=bg and all(row[c]==g[0][c] for row in g)]
    first=[row[:min(sep)] for row in g] if sep else g
    panel=[row[max(sep)+1:] for row in g] if sep else g
    chunks=[x for x in components({(r,c) for r,row in enumerate(first) for c,v in enumerate(row) if v!=bg}) if len(x)>1]
    if len(chunks)!=1:raise ValueError('one isolated first-panel motif required')
    template=chunks[0];t,d=heading(template);ink={(r,c) for r,row in enumerate(panel) for c,v in enumerate(row) if v!=bg};matches=[]
    for n in range(4):
        rel={spin((r-t[0],c-t[1]),n) for r,c in template}
        for anchor in sorted(ink):
            moved={(anchor[0]+r,anchor[1]+c) for r,c in rel}
            if moved<=ink:matches.append((anchor,spin(d,n),moved))
    if len(matches)!=1:raise ValueError('last-panel motif match must be unique')
    tip,d,cells=matches[0];todo=ink-cells;route=[tip];directions=[d];branch=False
    while todo:
        aligned=[p for p in todo if p[0]==route[-1][0] or p[1]==route[-1][1]]
        if not aligned:raise ValueError('broken aligned route')
        dist=lambda p:abs(p[0]-route[-1][0])+abs(p[1]-route[-1][1])
        aligned.sort(key=dist)
        if len(aligned)>1:
            if dist(aligned[0])==dist(aligned[1]):raise ValueError('tied nearest waypoint')
            branch=True
        nxt=aligned[0];dr=nxt[0]-route[-1][0];dc=nxt[1]-route[-1][1];z=abs(dr)+abs(dc)
        directions.append((dr//z,dc//z));route.append(nxt);todo.remove(nxt)
    return dict(bg=bg,panel=panel,tip=tip,heading=d,cells=cells,color=panel[tip[0]][tip[1]],route=route,directions=directions,nearest_choice=branch)

def render(info,mode='follow_final_leg',rival=None):
    target=info['route'][-1];direction=info['directions'][-1] if mode=='follow_final_leg' else info['heading'];cells=info['cells'];tip=info['tip']
    if rival=='farthest_aligned':
        remaining=set(info['route'][1:]);pos=info['tip'];last=info['heading']
        while remaining:
            aligned=[p for p in remaining if p[0]==pos[0] or p[1]==pos[1]]
            if not aligned:break
            nxt=max(aligned,key=lambda p:abs(p[0]-pos[0])+abs(p[1]-pos[1]))
            dr,dc=nxt[0]-pos[0],nxt[1]-pos[1];z=abs(dr)+abs(dc);last=(dr//z,dc//z);pos=nxt;remaining.remove(nxt)
        target=pos;direction=last if mode=='follow_final_leg' else info['heading']
    if rival=='copy_last':return deepcopy(info['panel'])
    if rival=='one_step':target=info['route'][1];direction=info['directions'][1] if mode=='follow_final_leg' else direction
    if rival=='no_translation':target=tip
    if rival=='reverse_heading':direction=(-direction[0],-direction[1])
    if rival and rival.startswith('fixed_heading_'):direction=DIRS[int(rival[-1])]
    if rival=='fixed_three_cells':cells=cells_at(MOTIFS[0],tip,info['heading'])
    turns=(DIRS.index(direction)-DIRS.index(info['heading']))%4
    moved={(target[0]+spin((r-tip[0],c-tip[1]),turns)[0],target[1]+spin((r-tip[0],c-tip[1]),turns)[1]) for r,c in cells}
    out=[[info['bg']]*len(info['panel'][0]) for _ in info['panel']]
    if rival=='erase_all':return out
    if rival=='retain_waypoints':
        for r,c in info['route'][1:]:out[r][c]=info['color']
    for r,c in moved:
        if not(0<=r<len(out) and 0<=c<len(out[0])):raise ValueError('motif leaves output')
        out[r][c]=info['color']
    return out

RIVALS=('farthest_aligned','copy_last','one_step','no_translation','reverse_heading','fixed_three_cells','erase_all','retain_waypoints')+tuple('fixed_heading_'+str(i) for i in range(4))

def _scene(seed,label,profile,attempt):
    ctx=gen_ctx(seed=seed,sample_index=attempt,version='1',task_id='public_eval_5545f144')
    rng=ctx.draw_rng(label);h,w,n=profile;bg,color,sep=rng.sample(range(10),3);motif=rng.choice(MOTIFS)
    points=[(rng.randrange(2,h-2),rng.randrange(2,w-2))];horizontal=bool(rng.randrange(2));legs=rng.randint(4,6)
    for step in range(legs):
        r,c=points[-1]
        opts=[x for x in range(2,(w if horizontal else h)-2) if abs(x-(c if horizontal else r))>=3]
        rng.shuffle(opts)
        chosen=None
        for x in opts:
            q=(r,x) if horizontal else (x,c)
            if all(max(abs(q[0]-p[0]),abs(q[1]-p[1]))>=2 for p in points):chosen=q;break
        if chosen is None:raise ValueError('route construction exhausted')
        points.append(chosen);horizontal=not horizontal
    # Subdivide a long leg. Nearest-vs-farthest is then a real input-derived choice.
    eligible=[i for i,(a,b) in enumerate(zip(points,points[1:])) if abs(a[0]-b[0])+abs(a[1]-b[1])>=6]
    if eligible:
        i=rng.choice(eligible);a,b=points[i:i+2];points.insert(i+1,((a[0]+b[0])//2,(a[1]+b[1])//2))
    def direction(a,b):
        dr,dc=b[0]-a[0],b[1]-a[1];z=abs(dr)+abs(dc);return(dr//z,dc//z)
    panels=[]
    for k in range(n):
        d=direction(points[k-1],points[k]) if k else direction(points[0],points[1])
        cells=cells_at(motif,points[k],d);remaining=set(points[k+1:])
        if cells&remaining:raise ValueError('cursor overlaps waypoint')
        panel=[[bg]*w for _ in range(h)]
        for r,c in cells|remaining:panel[r][c]=color
        panels.append(panel)
    grid=[sum(([sep]+panel[r] if k else panel[r] for k,panel in enumerate(panels)),[]) for r in range(h)]
    info=analyze(grid)
    if info['route']!=points[n-1:]:raise ValueError('unintended route')
    if info['heading']==info['directions'][-1]:raise ValueError('setting contrast absent')
    for mode in SETTINGS:
        for rival in (None,)+RIVALS:render(info,mode,rival)
    return grid

@lru_cache(maxsize=64)
def inputs(seed):
    profiles=((12,13,2),(16,14,2),(20,11,2),(30,30,1))
    ctx=gen_ctx(seed=seed,sample_index=0,version='1',task_id='public_eval_5545f144')
    qp=list(profiles);ctx.draw_rng('query-profiles').shuffle(qp)
    result=[]
    for i in range(10):
        profile=qp[i-6] if i>=6 else profiles[ctx.draw_rng('demo-profile.'+str(i)).randrange(3)]
        for attempt in range(512):
            try:g=_scene(seed,'query.'+str(i-6) if i>=6 else 'demo.'+str(i),profile,attempt);info=analyze(g)
            except (ValueError,IndexError):continue
            if i==0 and (len(info['cells'])==3 or not info['nearest_choice']):continue
            if i==1:
                old=analyze(result[0])
                if info['heading']==old['heading'] or info['directions'][-1]==old['directions'][-1]:continue
                if any(all(render(analyze(x),mode)==render(analyze(x),mode,rival) for x in [result[0],g]) for mode in SETTINGS for rival in RIVALS):continue
            result.append(g);break
        else:raise RuntimeError('bounded scene search exhausted '+str((seed,i,profile)))
    return result

def setting(settings):
    if settings is None:return SETTINGS[0]
    if type(settings)!=dict or set(settings)!={'orientation'} or settings['orientation'] not in SETTINGS:raise ValueError('unknown orientation settings')
    return settings['orientation']

def program(settings=None):
    mode=setting(settings)
    return (Path(__file__).with_name('canonical.rkt') if mode==SETTINGS[0] else Path(__file__).with_name('keep-heading.rkt')).read_text()

def execute(source,grids):
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    with RacketBridge() as bridge:
        bridge.eval_text('(define route-rule '+wrap_rule(source)+')')
        out=[]
        for g in grids:
            bridge.define_grid('route-input',g);out.append(bridge.eval_text('(route-rule route-input)'))
        return out

def generate(seed,settings=None,demos=3,queries=4):
    for name,value,lo,hi in (('seed',seed,0,2**63-1),('demos',demos,2,6),('queries',queries,1,4)):
        if type(value)!=int or not lo<=value<=hi:raise ValueError('invalid '+name)
    mode=setting(settings);bank=inputs(seed);gs=deepcopy(bank[:demos]+bank[6:6+queries]);source=program(settings);ys=execute(source,gs)
    for g,y in zip(gs,ys):
        if y!=render(analyze(g),mode):raise RuntimeError('Racket/Python disagreement')
    pairs=[{'input':g,'output':y} for g,y in zip(gs,ys)]
    return {'train':pairs[:demos],'test':pairs[demos:],'program_solution':source}

def rival_program(mode,name):
    """Executable finite counterfactuals; never used to label correct examples."""
    source=program({'orientation':mode})
    if name=='copy_last':return source.replace('(paint-cells (empty-grid (rows panel) (cols panel) bg) moved (obj-color cursor))','panel')
    if name=='erase_all':return source.replace('moved (obj-color cursor)','(list) (obj-color cursor)')
    if name=='no_translation':return source.replace('(define target (first trace))','(define target tip)')
    if name=='one_step':
        return source.replace('(if (empty? todo) (list pos direction)','(if (or (empty? todo) (< (length todo) (length dots))) (list pos direction)')
    if name=='farthest_aligned':
        source=source.replace('(if (empty? todo) (list pos direction)','(if (or (empty? todo) (empty? (filter (lambda (p) (or (= (first p) (first pos)) (= (second p) (second pos)))) todo))) (list pos direction)')
        return source.replace('(< (distance a pos) (distance b pos))','(> (distance a pos) (distance b pos))')
    base='(second trace)' if mode==SETTINGS[0] else 'heading'
    if name=='reverse_heading':
        return source.replace('(define final-heading '+base+')','(define final-heading (map (lambda (x) (- x)) '+base+'))')
    if name.startswith('fixed_heading_'):
        dr,dc=DIRS[int(name[-1])]
        return source.replace('(define final-heading '+base+')',f'(define final-heading (list {dr} {dc}))')
    if name=='retain_waypoints':
        return source.replace('(paint-cells (empty-grid (rows panel) (cols panel) bg) moved','(paint-cells (paint-cells (empty-grid (rows panel) (cols panel) bg) dots (obj-color cursor)) moved')
    if name=='fixed_three_cells':
        v='''(list tip
          (list (+ (- (first tip) (first heading)) (second heading)) (- (- (second tip) (second heading)) (first heading)))
          (list (- (- (first tip) (first heading)) (second heading)) (+ (- (second tip) (second heading)) (first heading))))'''
        prefix,suffix=source.rsplit(' cells))',1)
        return prefix+' '+v+'))'+suffix
    raise ValueError('unknown rival')
