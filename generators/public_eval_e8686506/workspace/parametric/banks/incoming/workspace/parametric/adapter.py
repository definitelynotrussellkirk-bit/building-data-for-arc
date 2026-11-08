"""Translation-only colored exact cover, with post-assembly component selection.

Python outputs are authoring claims. The independent stored Racket rule is the
label authority. No official puzzle or answer file is read by this module.
"""
from __future__ import annotations
from collections import Counter
import copy
from functools import lru_cache
from pathlib import Path

HERE=Path(__file__).resolve().parent
MODES=('assemble','largest_inserted')
CARDINAL=((-1,0),(1,0),(0,-1),(0,1))
EIGHT=tuple((r,c)for r in (-1,0,1)for c in (-1,0,1)if r or c)


def integer(x,lo,hi,name):
    if type(x)is not int or not lo<=x<=hi:raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return x


def grid(g):
    if (type(g)is not list or not 1<=len(g)<=30 or type(g[0])is not list or not 1<=len(g[0])<=30
            or any(type(row)is not list or len(row)!=len(g[0])or any(type(v)is not int or not 0<=v<=9 for v in row)for row in g)):
        raise ValueError('expected an exact-integer rectangular 1..30 grid')
    return g


def setting(settings):
    if type(settings)is not dict or set(settings)!={'selection'} or type(settings['selection'])is not str or settings['selection']not in MODES:
        raise ValueError('settings must name exactly one declared selection')
    return settings['selection']


def program(settings):
    return (HERE/('canonical.rkt'if setting(settings)=='assemble'else'largest_inserted.rkt')).read_text()


def components(cells,deltas=CARDINAL):
    remaining=set(cells);out=[]
    while remaining:
        start=min(remaining);remaining.remove(start);obj={start};stack=[start]
        while stack:
            r,c=stack.pop()
            for dr,dc in deltas:
                p=(r+dr,c+dc)
                if p in remaining:remaining.remove(p);obj.add(p);stack.append(p)
        out.append(obj)
    return out


def objects(g,bg,deltas=EIGHT):
    found=[]
    for v in sorted(set(x for row in g for x in row)-{bg}):
        found.extend((v,s)for s in components({(r,c)for r,row in enumerate(g)for c,x in enumerate(row)if x==v},deltas))
    return sorted(found,key=lambda item:min(item[1]))


def normalize(cells):
    r0=min(r for r,c in cells);c0=min(c for r,c in cells)
    return tuple(sorted((r-r0,c-c0)for r,c in cells))


@lru_cache(maxsize=2048)
def _pack(key,limit):
    g=[list(row)for row in key];counts=Counter(v for row in g for v in row)
    maximum=max(counts.values());modes=[v for v,n in counts.items()if n==maximum]
    if len(modes)!=1:raise ValueError('cover grammar requires a unique dominant background')
    bg=modes[0];os=objects(g,bg)
    if not os:raise ValueError('cover grammar requires foreground objects')
    size=max(len(s)for v,s in os);frames=[(v,s)for v,s in os if len(s)==size]
    rawpieces=[(v,s)for v,s in os if len(s)!=size]
    allframe=set().union(*(s for v,s in frames));r0=min(r for r,c in allframe);c0=min(c for r,c in allframe)
    h=max(r for r,c in allframe)-r0+1;w=max(c for r,c in allframe)-c0+1
    walls=tuple(sorted((r-r0,c-c0,v)for v,s in frames for r,c in s));mask={(r,c)for r,c,v in walls}
    pieces=tuple((i,v,normalize(s))for i,(v,s)in enumerate(rawpieces))
    free={(r,c)for r in range(h)for c in range(w)}-mask
    if sum(len(s)for _,_,s in pieces)!=len(free):raise ValueError('pieces cannot cover the target area')
    base=[[bg]*w for _ in range(h)]
    for r,c,v in walls:base[r][c]=v
    results={};nodes=0
    def search(remaining,empty,placed):
        nonlocal nodes
        nodes+=1
        if nodes>200000:raise ValueError('cover search budget exceeded; outside admitted grammar')
        if len(results)>=limit:return
        if not empty:
            if remaining:return
            output=[row[:]for row in base]
            for _,v,cells in placed:
                for r,c in cells:output[r][c]=v
            frozen=tuple(tuple(row)for row in output)
            results.setdefault(frozen,tuple(placed));return
        anchor=min(empty);seen=set()
        for i,v,shape in remaining:
            if (v,shape)in seen:continue
            seen.add((v,shape))
            for ar,ac in shape:
                dr,dc=anchor[0]-ar,anchor[1]-ac
                cells=frozenset((r+dr,c+dc)for r,c in shape)
                if cells<=empty:
                    search(tuple(p for p in remaining if p[0]!=i),empty-cells,placed+[(i,v,tuple(sorted(cells)))])
                    if len(results)>=limit:return
    search(pieces,free,[])
    if not results:raise ValueError('no translation-only exact cover')
    return bg,tuple(tuple(row)for row in base),walls,pieces,tuple(results.items()),nodes


def details(g,limit=1):
    grid(g);return _pack(tuple(tuple(row)for row in g),limit)


def describe(g):
    bg,base,walls,pieces,solutions,nodes=details(g)
    return {'background':bg,'target_shape':[len(base),len(base[0])],'frame_cells':len(walls),
            'piece_sizes':[len(p[2])for p in pieces],'search_nodes_first_cover':nodes}


def color_solution_count(g,limit=2):
    integer(limit,1,16,'limit');return len(details(g,limit)[4])


def payload_groups(output,walls,bg,connectivity=CARDINAL):
    mask={(r,c)for r,c,v in walls}
    groups=[]
    for value in sorted({v for row in output for v in row}-{bg}):
        cells={(r,c)for r,row in enumerate(output)for c,v in enumerate(row)if v==value and (r,c)not in mask}
        groups.extend((value,obj)for obj in components(cells,connectivity))
    return sorted(groups,key=lambda item:min(item[1]))


def selected_output(base,output,selected):
    result=[list(row)for row in base]
    for r,c in selected:result[r][c]=output[r][c]
    return result


def solve(g,mode='assemble'):
    if mode not in MODES:raise ValueError('undeclared selection')
    bg,base,walls,pieces,solutions,_=details(g);output,placements=solutions[0]
    if mode=='assemble':return [list(row)for row in output]
    groups=payload_groups(output,walls,bg)
    return selected_output(base,output,max(groups,key=lambda item:len(item[1]))[1]if groups else set())


def counterfactual(g):
    """Select one largest loose source piece before the pieces can join."""
    bg,base,walls,pieces,solutions,_=details(g);output,placements=solutions[0]
    chosen=max(pieces,key=lambda p:len(p[2]))[0]
    cells=next(s for i,v,s in placements if i==chosen)
    return selected_output(base,output,cells)


def causal_intermediate(g):
    bg,base,walls,pieces,solutions,_=details(g);output,_=solutions[0];groups=payload_groups(output,walls,bg)
    chosen=max(groups,key=lambda item:len(item[1]))
    return {'source_piece_sizes':[len(p[2])for p in pieces],
            'assembled_components':[{'color':v,'size':len(s),'first_cell':list(min(s))}for v,s in groups],
            'selected_color':chosen[0],'selected_component_size':len(chosen[1]),'selected_first_cell':list(min(chosen[1]))}


def rng_for(seed,label):
    from puzzle_generators.base import gen_ctx
    return gen_ctx(seed=seed,sample_index=0,version='1.0.0',task_id='public_eval_e8686506').draw_rng(label)


def rotate(g,n):
    for _ in range(n%4):g=[list(row)for row in zip(*g[::-1])]
    return g


def template(seed,index):
    rng=rng_for(seed,f'template:{index}');palette=list(range(10));rng.shuffle(palette)
    bg,f1,f2,alpha,beta,gamma,delta,epsilon=palette[:8]
    small=index==7
    if small:
        rh=2;h,w=rh+3,5;scale=1;split=False
        slots=[('rectangle',alpha,{(r,c)for r in range(1,rh+1)for c in range(1,4)}),
               ('middle',alpha if rng.randrange(2)else beta,{(h-2,2),(h-1,2)})]
        for i,p in enumerate(((0,2),(h-2,0),(h-2,4))):slots.append((f'dot{i}',delta,{p}))
    else:
        h=9 if index==0 else 10 if index==1 else 8 if index in (6,8)else rng.choice((8,9,10,11,12))
        if index==9:h=rng.choice((10,12))
        w=5;scale=2 if index==9 else 1
        stem=2 if index in (1,6) else 1 if index in (0,8,9)else rng.choice((1,2))
        notch=1 if index==6 else 0 if index in (0,1,8,9)else rng.randrange(2)
        notch=min(notch,stem-1)  # Otherwise differently colored bars share one shape.
        split=(h%2==0 and (index in (1,6,9)or rng.randrange(2)==0))
        bottom=beta if index in (0,1,6)else alpha if index==8 else rng.choice((alpha,beta))
        middle=epsilon if index==1 else alpha
        slots=[('top',alpha,{(1,c)for c in range(1,4)}|{(r,2)for r in range(2,2+stem)}),
               ('bottom',bottom,{(h-2,c)for c in range(1,4)}|{(r,2)for r in range(h-2-stem,h-2)}),
               ('left',gamma,{(r,0)for r in range(2+notch,h-2-notch)}),
               ('right',gamma,{(r,4)for r in range(2+notch,h-2-notch)})]
        center={(r,2)for r in range(2+stem,h-2-stem)}
        if center:slots.append(('middle',delta if len(center)==1 else middle,center))
        for i,p in enumerate(((0,0),(0,4),(h-1,0),(h-1,4))):slots.append((f'dot{i}',delta,{p}))
    holes=set().union(*(s for _,_,s in slots))
    frame={(r,c):(f2 if split and r>=h//2 else f1)for r in range(h)for c in range(w)if (r,c)not in holes}
    def expand(s):return {(r*scale+dr,c*scale+dc)for r,c in s for dr in range(scale)for dc in range(scale)}
    grown={(r*scale+dr,c*scale+dc):v for (r,c),v in frame.items()for dr in range(scale)for dc in range(scale)}
    pieces=[(tag,v,set(normalize(expand(s))))for tag,v,s in slots]
    return bg,grown,pieces,h*scale,w*scale,small,scale


def random_layout(bg,frame,pieces,fh,fw,rng):
    h,w=rng.randint(21,27),rng.randint(21,27)
    g=[[bg]*w for _ in range(h)];r0=rng.randrange(h-fh+1);c0=rng.randrange(w-fw+1)
    blocked={(r,c)for r in range(max(0,r0-1),min(h,r0+fh+1))for c in range(max(0,c0-1),min(w,c0+fw+1))}
    for (r,c),v in frame.items():g[r0+r][c0+c]=v
    for tag,value,cells in sorted(pieces,key=lambda p:-len(p[2])):
        ph=max(r for r,c in cells)+1;pw=max(c for r,c in cells)+1;placed=None
        for _ in range(80):
            rr=rng.randrange(h-ph+1);cc=rng.randrange(w-pw+1);test={(rr+r,cc+c)for r,c in cells}
            if not test&blocked:placed=test;break
        if placed is None:return None
        for r,c in placed:
            g[r][c]=value
            blocked.update((r+dr,c+dc)for dr in (-1,0,1)for dc in (-1,0,1))
    return g


def scene(seed,index):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    bg,frame,pieces,fh,fw,small,scale=template(seed,index);rng=rng_for(seed,f'layout:{index}')
    g=None
    if index in (2,3,4,5,8):g=random_layout(bg,frame,pieces,fh,fw,rng)
    if g is None:
        if small:
            h=w=13;r0,c0=2,1
            positions={'rectangle':(9,1),'middle':(9,7),'dot0':(0,9),'dot1':(5,11),'dot2':(12,12)}
        elif scale==2:
            h=w=30;r0=c0=0
            positions={'left':(0,12),'right':(0,15),'top':(0,18),'bottom':(8,18),'middle':(0,26),
                       'dot0':(28,0),'dot1':(28,7),'dot2':(28,14),'dot3':(28,28)}
        else:
            h,w=fh+2,16;r0=c0=0
            positions={'left':(0,7),'right':(0,9),'top':(0,11),'bottom':(4,11),'middle':(0,15),
                       'dot0':(fh+1,0),'dot1':(fh+1,5),'dot2':(fh+1,10),'dot3':(fh+1,15)}
        if not small and rng.randrange(2):positions['top'],positions['bottom']=positions['bottom'],positions['top']
        g=[[bg]*w for _ in range(h)]
        for (r,c),value in frame.items():g[r0+r][c0+c]=value
        for tag,value,cells in pieces:
            rr,cc=positions[tag]
            for r,c in cells:
                if g[rr+r][cc+c]!=bg:raise AssertionError('constructive source overlap')
                g[rr+r][cc+c]=value
    if rng.randrange(2):g=[row[::-1]for row in g]
    return rotate(g,0 if index==0 else 1 if index==1 else rng.randrange(4))


def generate(seed,settings,demos=2,queries=4):
    integer(seed,0,2**63-1,'seed');integer(demos,2,6,'demos');integer(queries,1,4,'queries');mode=setting(settings)
    def pair(i):
        g=scene(seed,i);return {'input':g,'output':solve(g,mode)}
    return {'train':[pair(i)for i in range(demos)],'test':[pair(i)for i in range(6,6+queries)],
            'program_solution':program(settings),'settings':dict(settings),'seed':seed}


def query_order(presentation_seed=0):
    integer(presentation_seed,0,2**63-1,'presentation_seed');order=list(range(4));rng_for(presentation_seed,'presentation').shuffle(order);return order


def public_turn(episode,turn,*,presentation_seed=0):
    integer(turn,0,3,'turn')
    if type(episode)is not dict or type(episode.get('test'))is not list or len(episode['test'])!=4:
        raise ValueError('project from the complete four-query private bank')
    if type(episode.get('train'))is not list or not 2<=len(episode['train'])<=6:raise ValueError('invalid demonstrations')
    i=query_order(presentation_seed)[turn]
    return copy.deepcopy({'train':[{'input':grid(p['input']),'output':grid(p['output'])}for p in episode['train']],
                         'test':[{'input':grid(episode['test'][i]['input'])}]})


def rival(g,name):
    if name in MODES:return solve(g,name)
    if name=='largest_source_piece':return counterfactual(g)
    bg,base,walls,pieces,solutions,_=details(g);out,placements=solutions[0]
    groups=payload_groups(out,walls,bg);allcells={(r,c)for _,s in groups for r,c in s}
    if name=='skeleton_only':return [list(row)for row in base]
    if name=='horizontal_flip':return [list(row[::-1])for row in out]
    if name=='vertical_flip':return [list(row)for row in out[::-1]]
    if name=='rotate_result':return rotate([list(row)for row in out],1)
    if name=='fill_largest_piece_color':
        color=max(pieces,key=lambda p:len(p[2]))[1];res=[list(row)for row in base]
        for r,c in allcells:res[r][c]=color
        return res
    if name=='largest_global_color':
        counts=Counter(out[r][c]for r,c in sorted(allcells));color=max(counts,key=counts.get)
        chosen={p for p in allcells if out[p[0]][p[1]]==color}
    elif name=='selected_color_everywhere':
        color=max(groups,key=lambda item:len(item[1]))[0];chosen={p for p in allcells if out[p[0]][p[1]]==color}
    elif name=='first_inserted':chosen=groups[0][1]
    elif name=='last_inserted':chosen=groups[-1][1]
    elif name=='smallest_inserted':chosen=min(groups,key=lambda item:len(item[1]))[1]
    elif name=='largest_bbox':
        chosen=max(groups,key=lambda item:(max(r for r,c in item[1])-min(r for r,c in item[1])+1)*(max(c for r,c in item[1])-min(c for r,c in item[1])+1))[1]
    elif name=='eight_connected':chosen=max(payload_groups(out,walls,bg,EIGHT),key=lambda item:len(item[1]))[1]
    elif name=='largest_all_foreground':chosen=max(objects(out,bg,CARDINAL),key=lambda item:len(item[1]))[1]
    elif name=='largest_source_color':
        color=max(pieces,key=lambda p:len(p[2]))[1];chosen={p for p in allcells if out[p[0]][p[1]]==color}
    else:raise ValueError(name)
    return selected_output(base,out,chosen)

RIVALS=MODES+('largest_source_piece','skeleton_only','horizontal_flip','vertical_flip','rotate_result','fill_largest_piece_color',
              'largest_global_color','selected_color_everywhere','first_inserted','last_inserted','smallest_inserted',
              'largest_bbox','eight_connected','largest_all_foreground','largest_source_color')
