"""General perforated-template matching and fresh, constructive teaching scenes.

No official grids or labels are accessed here. The admitted grammar has one
perforated rectangular frame, a common integer piece scale, and unambiguous
shape-to-color matches up to the eight square symmetries.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
import random

HERE = Path(__file__).resolve().parent
SETTINGS = ('assemble_only', 'highlight_largest_fitted_cluster')


def strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30 or any(type(row) is not list or len(row) != len(grid[0])
        or any(type(c) is not int or not 0 <= c <= 9 for c in row) for row in grid)):
        raise ValueError('Expected a rectangular 1..30 grid of exact integer colors 0..9')
    return [row[:] for row in grid]


def components(grid, background=0, diagonal=False):
    seen = set(); found = []
    steps = [(a,b) for a in (-1,0,1) for b in (-1,0,1)
             if (a or b) and (diagonal or abs(a)+abs(b)==1)]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == background or (r,c) in seen:
                continue
            todo = [(r,c)]; seen.add((r,c)); cells = []
            while todo:
                a,b = todo.pop(); cells.append((a,b))
                for dr,dc in steps:
                    q = (a+dr,b+dc)
                    if (0 <= q[0] < len(grid) and 0 <= q[1] < len(row)
                        and q not in seen and grid[q[0]][q[1]] == color):
                        seen.add(q); todo.append(q)
            found.append({'color':color, 'cells':sorted(cells)})
    return found


def bbox(cells):
    return min(r for r,c in cells), min(c for r,c in cells), max(r for r,c in cells), max(c for r,c in cells)


def norm(cells):
    cells = list(cells)
    r,c,_,_ = bbox(cells)
    return tuple(sorted((a-r,b-c) for a,b in cells))


def transform_shape(cells, rotation=0, reflection=False):
    cells = norm(cells)
    if reflection:
        cells = norm((r,-c) for r,c in cells)
    for _ in range(rotation % 4):
        cells = norm((c,-r) for r,c in cells)
    return cells


def forms(cells):
    return {transform_shape(cells,k,flip) for k in range(4) for flip in (False, True)}


def enlarge_shape(cells, scale):
    return norm([(r*scale+a,c*scale+b) for r,c in norm(cells)
                 for a in range(scale) for b in range(scale)])


def upscale(grid, scale):
    return [[v for v in row for _ in range(scale)] for row in grid for _ in range(scale)]


def analyze(grid):
    grid = strict_grid(grid); objs = components(grid)
    frames = []
    for obj in objs:
        r,c,r2,c2 = bbox(obj['cells']); color = obj['color']
        if r2-r < 2 or c2-c < 2: continue
        edge = [(a,b) for a in range(r,r2+1) for b in range(c,c2+1)
                if a in (r,r2) or b in (c,c2)]
        crop = [row[c:c2+1] for row in grid[r:r2+1]]
        if (all(grid[a][b]==color for a,b in edge)
            and any(0 in row for row in crop)
            and all(v in (0,color) for row in crop for v in row)):
            frames.append((obj,crop))
    if len(frames)!=1: raise ValueError('Expected exactly one perforated full-border frame')
    frame, crop = frames[0]; color = frame['color']
    holes = components(crop, color)
    outside = [o for o in objs if o is not frame]
    piece_forms = [(o,forms(o['cells'])) for o in outside]
    solutions = []
    for scale in range(1, 30//max(len(crop),len(crop[0]))+1):
        matches=[]
        for hole in holes:
            shape=enlarge_shape(hole['cells'],scale)
            colors={p['color'] for p,fs in piece_forms if shape in fs}
            if len(colors)!=1: break
            matches.append(next(iter(colors)))
        if len(matches)==len(holes):solutions.append((scale,matches))
    if len(solutions)!=1:raise ValueError('Expected a unique common scale and unambiguous shape colors')
    scale, matches=solutions[0]
    filled=[row[:] for row in crop]
    for hole,fill in zip(holes,matches):
        hole['matched_color']=fill
        for r,c in hole['cells']:filled[r][c]=fill
    assembled=upscale(filled,scale)
    clusters=components(assembled,color,diagonal=True)
    return {'frame_color':color, 'template':crop, 'scale':scale, 'holes':holes,
            'outside':outside, 'filled_unit':filled, 'assembled':assembled,
            'clusters':clusters, 'cluster_sizes':sorted((len(x['cells']) for x in clusters),reverse=True)}


def solve(grid, finish='assemble_only'):
    if finish not in SETTINGS:raise ValueError('Unknown finish')
    info=analyze(grid); out=[row[:] for row in info['assembled']]
    if finish==SETTINGS[1]:
        winner=max(info['clusters'],key=lambda x:len(x['cells']))
        for r,c in winner['cells']:out[r][c]=9
    return out


def program(settings):
    if type(settings) is not dict or set(settings)!={'finish'} or settings['finish'] not in SETTINGS:
        raise ValueError('Expected exactly one declared finish setting')
    path = HERE.parents[1]/'reference.rkt' if settings['finish']==SETTINGS[0] else HERE/'highlight.rkt'
    return path.read_text(encoding='utf-8')


def _rng(seed, domain):
    token=hashlib.sha256(f'cavity-v1:{seed}:{domain}'.encode()).digest()
    return random.Random(int.from_bytes(token,'big'))


def _turn(grid, rotation, reflection=False):
    out=[row[::-1] if reflection else row[:] for row in grid]
    for _ in range(rotation % 4):out=[list(row) for row in zip(*out[::-1])]
    return out


def scene(seed, domain, scale=2, bent=True):
    """Constructively place six holes, their pieces and nonmatching noise.

    Slots have explicit separation; there are no retries or count fallbacks.
    Template and piece orientations are independently varied.
    """
    rng=_rng(seed,domain)
    frame, lc, tc, ic, sc, noise=rng.sample(range(1,9),6)
    L=((0,0),(0,1),(1,0))
    T=((0,0),(1,0),(1,1),(1,2)) if bent else ((0,0),(0,1),(0,2),(1,1))
    I=((0,0),(1,0),(2,0),(3,0))
    if rng.randrange(2):I=transform_shape(I,1)
    hole_specs=[(L,(1,1),lc),(L,(3,2),lc),(L,(7,1),lc),
                (T,(1,5),tc),(I,(4,6) if len({r for r,c in I})==4 else (5,5),ic),
                (((0,0),),(8,8),sc)]
    extra_h=rng.randrange(3) if scale==2 else 0
    extra_w=rng.randrange(3) if scale==2 else 0
    dh=rng.randrange(extra_h+1);dw=rng.randrange(extra_w+1)
    template=[[frame]*(10+extra_w) for _ in range(10+extra_h)]
    for shape,(r,c),color in hole_specs:
        for a,b in shape:template[r+a+dh][c+b+dw]=0
    template_rotation=rng.randrange(4);template_flip=bool(rng.randrange(2))
    template=_turn(template,template_rotation,template_flip)
    n=24 if scale==2 else 30
    g=[[0]*n for _ in range(n)]
    inventory=[template]
    for idx,(shape,_,color) in enumerate(hole_specs):
        if idx==3:
            base=transform_shape(shape,template_rotation,template_flip)
            oriented=transform_shape(base,1,True)
        else:
            oriented=transform_shape(shape,rng.randrange(4),bool(rng.randrange(2)))
        expanded=enlarge_shape(oriented,scale)
        ph=max(r for r,c in expanded)+1;pw=max(c for r,c in expanded)+1
        item=[[0]*pw for _ in range(ph)]
        for r,c in expanded:item[r][c]=color
        inventory.append(item)
    # Exhaust the tiny finite two-shelf partition space. Every admitted profile
    # has a legal partition, so this is constructive, not retry/fallback sampling.
    partitions=[]
    for mask in range(1,2**len(inventory)-1):
        if not mask&1:continue
        groups=[[i for i in range(len(inventory)) if bool(mask&(1<<i))==side]
                for side in (True,False)]
        widths=[sum(len(inventory[i][0]) for i in group)+len(group)-1 for group in groups]
        heights=[max(len(inventory[i]) for i in group) for group in groups]
        if max(widths)<=n and sum(heights)+1<=n:partitions.append(groups)
    if not partitions:raise AssertionError('No legal constructive inventory partition')
    groups=rng.choice(partitions);rng.shuffle(groups)
    heights=[max(len(inventory[i]) for i in group) for group in groups]
    vslack=n-sum(heights)-1
    top=rng.randrange(vslack+1);between=1+rng.randrange(vslack-top+1)
    starts=[top,top+heights[0]+between]
    for group,base_row,shelf_height in zip(groups,starts,heights):
        rng.shuffle(group)
        slack=n-sum(len(inventory[i][0]) for i in group)-(len(group)-1)
        gaps=[0]*(len(group)+1)
        for _ in range(slack):gaps[rng.randrange(len(gaps))]+=1
        c=gaps[0]
        for pos,i in enumerate(group):
            item=inventory[i];r=base_row+rng.randrange(shelf_height-len(item)+1)
            for a,row in enumerate(item):
                for b,value in enumerate(row):g[r+a][c+b]=value
            if i==0:tr,tc0=r,c
            c+=len(item[0])+1+gaps[pos+1]
    # One- and two-cell noise cannot match any scale-2/3 hole.
    candidates=[(r,c) for r in range(n) for c in range(n) if g[r][c]==0
                and not (tr<=r<tr+len(template) and tc0<=c<tc0+len(template[0]))]
    rng.shuffle(candidates); occupied_noise=set()
    for r,c in candidates:
        if len(occupied_noise)>=rng.randrange(6,11):break
        if all(abs(r-a)+abs(c-b)>1 for a,b in occupied_noise):g[r][c]=noise;occupied_noise.add((r,c))
    return _turn(g,rng.randrange(4),bool(rng.randrange(2)))


def generate(seed, settings, demos, queries):
    text=program(settings)
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('seed must be a nonnegative 63-bit integer')
    if type(demos) is not int or not 2<=demos<=6:raise ValueError('demos must be 2..6')
    if type(queries) is not int or queries!=4:raise ValueError('exactly four private queries are required')
    train=[scene(seed,f'demo:{i}',2+i%2,bent=(i%2==0)) for i in range(demos)]
    bank=[scene(seed,f'query:{i}',2+i%2,bent=(i%3!=1)) for i in range(4)]
    _rng(seed,'presentation').shuffle(bank)
    label=lambda grid:{'input':grid,'output':solve(grid,settings['finish'])}
    return {'train':list(map(label,train)), 'test':list(map(label,bank)), 'program_solution':text}


def rival_names(finish):
    common=['opposite_setting','no_scale','skip_fit','area_only','no_rotation','rotations_only','source_order']
    return common+(['four_connected','whole_winner_color','largest_source_color'] if finish==SETTINGS[1] else [])


def rival(grid, finish, name):
    info=analyze(grid);out=[row[:] for row in info['assembled']]
    if name=='opposite_setting':return solve(grid,SETTINGS[finish==SETTINGS[0]])
    if name=='no_scale':
        return [row[::info['scale']] for row in solve(grid,finish)[::info['scale']]]
    if name=='skip_fit':return upscale(info['template'],info['scale'])
    if name in ('area_only','no_rotation','rotations_only','source_order'):
        unit=[row[:] for row in info['template']]
        ps=[o for o in info['outside'] if len(o['cells'])>=info['scale']**2]
        for i,hole in enumerate(info['holes']):
            target=enlarge_shape(hole['cells'],info['scale'])
            matches=([o for o in ps if len(o['cells'])==len(target)] if name=='area_only' else
                     [o for o in ps if target in {transform_shape(o['cells'],k) for k in range(4)}] if name=='rotations_only' else
                     [o for o in ps if norm(o['cells'])==target])
            color=(ps[i%len(ps)]['color'] if name=='source_order' else (matches[0]['color'] if matches else 0))
            for r,c in hole['cells']:unit[r][c]=color
        out=upscale(unit,info['scale'])
        if finish==SETTINGS[0]:return out
        comps=components(out,info['frame_color'],True)
        winner=max(comps,key=lambda o:len(o['cells']))
        for r,c in winner['cells']:out[r][c]=9
        return out
    if name=='four_connected':
        winner=max(components(out,info['frame_color']),key=lambda o:len(o['cells']))
        for r,c in winner['cells']:out[r][c]=9
        return out
    if name in ('whole_winner_color','largest_source_color'):
        source=info['clusters'] if name=='whole_winner_color' else info['outside']
        color=max(source,key=lambda o:len(o['cells']))['color']
        return [[9 if v==color else v for v in row] for row in out]
    raise ValueError('Unknown rival')


def surviving_rivals(episode):
    finish=next(v for v in SETTINGS if program({'finish':v})==episode['program_solution'])
    return [name for name in rival_names(finish)
            if all(rival(p['input'],finish,name)==p['output'] for p in episode['train'])]


def public_view(episode, query_index=0):
    if type(query_index) is not int or not 0<=query_index<len(episode['test']):raise ValueError('Invalid query index')
    visible={'train':[{'input':strict_grid(p['input']),'output':strict_grid(p['output'])} for p in episode['train']],
             'test':[{'input':strict_grid(episode['test'][query_index]['input'])}]}
    return (json.dumps(visible,sort_keys=True,separators=(',',':'))+'\n').encode()

COUNTERFACTUAL_FILE='counterfactual-four.rkt'

def dependency():
    return {
        'step_a':'Infer the common piece scale and match each template cavity under D4, then assemble the correctly colored enlarged board.',
        'intermediate':'The fitted board and its same-color eight-connected components, including diagonal unions of separate cavities.',
        'step_b':'Select the largest fitted component by occupied-cell count and recolor only that component to 9.',
        'why_b_depends_on_a':'Connectivity depends on the fitted colors, not raw scattered-piece adjacency. Separate diagonal cavities of the same matched color merge and jointly beat a larger individual piece; an isolated occurrence of that color must remain unchanged.'}

def causal_value(grid):
    info=analyze(grid)
    return {'scale':info['scale'],'hole_color_and_unit_size':[[h['matched_color'],len(h['cells'])] for h in info['holes']],
            'correct_eight_component_sizes':info['cluster_sizes'],
            'wrong_four_component_sizes':sorted((len(c['cells']) for c in components(info['assembled'],info['frame_color'])),reverse=True)}
