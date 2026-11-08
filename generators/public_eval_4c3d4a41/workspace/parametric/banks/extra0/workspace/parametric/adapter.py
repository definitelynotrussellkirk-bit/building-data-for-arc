"""Upright comb insertion, with selection from the clipped intermediate.

Official puzzles and answers are never read at generation time. Python labels
are deterministic claims; the protected Racket preflight independently checks them.
"""
from __future__ import annotations
import copy
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODES = ('insert', 'longest_survivor')
CARDINAL = ((-1,0),(1,0),(0,-1),(0,1))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list
            or not 1 <= len(g[0]) <= 30):
        raise ValueError('expected a 1..30 rectangular grid')
    w = len(g[0])
    if any(type(row) is not list or len(row) != w
           or any(type(x) is not int or not 0 <= x <= 9 for x in row) for row in g):
        raise ValueError('expected rectangular exact-integer colors 0..9')
    return g


def setting(settings):
    if (type(settings) is not dict or set(settings) != {'selection'}
            or type(settings['selection']) is not str or settings['selection'] not in MODES):
        raise ValueError('settings must name one declared selection')
    return settings['selection']


def program(settings):
    mode = setting(settings)
    return (HERE / ('canonical.rkt' if mode == 'insert' else 'longest_survivor.rkt')).read_text()


def components(cells):
    pending = set(cells); answer = []
    while pending:
        p = min(pending); pending.remove(p); found = {p}; todo = [p]
        while todo:
            r,c = todo.pop()
            for dr,dc in CARDINAL:
                q = (r+dr,c+dc)
                if q in pending:
                    pending.remove(q); found.add(q); todo.append(q)
        answer.append(found)
    return answer


def bbox(cells):
    return min(r for r,c in cells), min(c for r,c in cells), max(r for r,c in cells), max(c for r,c in cells)


def extract(g):
    """Read the apparatus geometry, rejecting inputs outside the explicit grammar."""
    grid(g)
    grays = components((r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v == 5)
    frames = []
    for obj in grays:
        top,left,bottom,right = bbox(obj)
        if (right-left >= 6 and bottom-top >= 5
                and all((top,c) in obj and (bottom,c) in obj for c in range(left,right+1))):
            frames.append(obj)
    if len(frames) != 1:
        raise ValueError('expected exactly one upright gray container')
    frame = frames[0]; top,left,bottom,right = bbox(frame)
    combs = [o for o in grays if o is not frame and bbox(o)[3] < left]
    if len(combs) != 1:
        raise ValueError('expected one separate comb left of the container')
    comb = combs[0]; ct,cl,cb,cr = bbox(comb)
    if (cr-cl < 2 or (cr-cl)%2 or right-left != cr-cl+4
            or not all((cb,c) in comb for c in range(cl,cr+1))):
        raise ValueError('comb baseline and container lane counts do not match')
    openings = [r for r in range(top+1,bottom) if g[r][left] == 0]
    if not openings:
        raise ValueError('container has no side opening')
    base = max(openings); capacity = base-top-1
    if capacity < 1:
        raise ValueError('container has no stack capacity')
    lanes = []
    for i,source_col in enumerate(range(cl,cr+1,2)):
        tooth_cells = sorted(r for r,c in comb if c == source_col)
        tooth = cb-tooth_cells[0]
        if tooth_cells != list(range(cb-tooth,cb+1)) or not 0 <= tooth <= capacity:
            raise ValueError('comb teeth must be contiguous and fit the container')
        col = left+2+2*i
        stack = [(r,g[r][col]) for r in range(top+1,base) if g[r][col] != 0]
        colors = {v for r,v in stack if v not in (0,5)}
        if len(colors) != 1:
            raise ValueError('each lane requires one colored stack')
        color = next(iter(colors))
        values = [v for r,v in stack]
        cap = values.count(5); amount = values.count(color)
        if ([r for r,v in stack] != list(range(top+1,top+1+len(stack)))
                or values != [5]*cap+[color]*amount):
            raise ValueError('expected a gray cap over a contiguous colored stack')
        lanes.append({'column':col,'tooth':tooth,'stack':stack,'color':color,
                      'amount':amount,'cap':cap,'gap':capacity-len(stack)})
    return {'frame':[top,left,bottom,right],'comb_cells':sorted(comb),
            'comb_box':[ct,cl,cb,cr],'base':base,'capacity':capacity,'lanes':lanes}


def insertion(g, spec=None, *, shift_mode='minimum', keep_comb=False, reverse=False):
    spec = extract(g) if spec is None else spec
    out = [row[:] for row in g]
    if not keep_comb:
        for r,c in spec['comb_cells']: out[r][c] = 0
    top,left,_,_ = spec['frame']; base = spec['base']
    heights = [lane['tooth'] for lane in spec['lanes']]
    if reverse: heights.reverse()
    for lane,tooth in zip(spec['lanes'],heights):
        col = lane['column']; stack = lane['stack']
        shift = max(0, tooth-lane['gap'])
        if shift_mode == 'none': shift = 0
        elif shift_mode == 'full_tooth': shift = tooth
        elif shift_mode != 'minimum': raise ValueError('unknown shift mode')
        for r in range(top+1,base): out[r][col] = 0
        for r,value in stack:
            if top < r-shift < base: out[r-shift][col] = value
        for r in range(base-tooth,base+1): out[r][col] = 5
    for c in range(left+2,spec['lanes'][-1]['column']+1):out[base][c] = 5
    return out


def surviving(out, spec):
    top = spec['frame'][0]
    return [[(r,lane['column']) for r in range(top+1,spec['base'])
             if out[r][lane['column']] not in (0,5)] for lane in spec['lanes']]


def mark(out, cells):
    answer = [row[:] for row in out]
    for r,c in cells: answer[r][c] = 1
    return answer


def solve(g, mode='insert'):
    if mode not in MODES: raise ValueError('unknown selection')
    spec = extract(g); out = insertion(g,spec)
    if mode == 'insert': return out
    groups = surviving(out,spec)
    return mark(out,max(groups,key=len))  # lanes are left-to-right; ties stay leftmost


def counterfactual(g):
    """Wrong intermediate: rank source colored stacks, before clipping occurs."""
    spec = extract(g); out = insertion(g,spec)
    i = max(range(len(spec['lanes'])), key=lambda i: spec['lanes'][i]['amount'])
    return mark(out,surviving(out,spec)[i])


def rng_for(seed, label):
    from puzzle_generators.base import gen_ctx
    return gen_ctx(seed=seed,sample_index=0,version='1.0.0',task_id='public_eval_4c3d4a41').draw_rng(label)


def scene(seed, index):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    rng = rng_for(seed,f'scene:{index}')
    compact = index == 6; stress = index == 9
    n = 6 if stress else 4 if compact else rng.randint(4,6)
    capacity = 26 if stress else 4 if compact else rng.randint(7,13)
    key_left = 1 if stress or compact else rng.randint(0,1)
    gap_between = 1 if stress or compact else rng.randint(1,2)
    frame_left = key_left+(2*n-1)+gap_between
    frame_right = frame_left+2*n+2
    right_margin = 2 if stress else 0 if compact else rng.randint(0,max(0,min(2,29-frame_right)))
    top = 0 if compact or stress else rng.randint(0,2)
    base = top+capacity+1; bottom = base+2
    extra_bottom = 0 if compact or stress else rng.randint(0,2)
    h = bottom+1+extra_bottom; w = frame_right+1+right_margin
    g = [[0]*w for _ in range(h)]
    for c in range(frame_left,frame_right+1):g[top][c]=g[bottom][c]=5
    for r in range(top,bottom+1):g[r][frame_right]=5;g[r][frame_left]=5
    g[base-1][frame_left]=g[base][frame_left]=0
    # (color amount, gray cap, tooth height). The longest source loses after clipping.
    if compact:
        roles=[(4,0,3),(3,0,1),(1,2,1),(2,0,1)]
    else:
        roles=[(capacity-1,1,capacity-2),(capacity-2,1,2),
               (2,2,1),(1,capacity-3,3)]
        for _ in range(n-4):
            amount = rng.randint(1,3)
            cap = rng.randint(0,capacity-amount)
            roles.append((amount,cap,rng.randint(2,capacity-1)))
    # Do not make the post-insertion winner a fixed original rank.
    # Demo zero: second-longest source wins. Demo one: third-longest source wins.
    if index == 1:
        roles[0]=(capacity,0,capacity-1)
        roles[2]=(capacity-1,1,capacity-2)
        roles[3]=(1,2,0)
    # Another legal branch keeps the original longest column as the winner.
    if index == 7:
        roles[0]=(capacity-2,1,capacity-2)
        roles[1]=(capacity-1,1,1)
    # Lawful mechanical boundaries: a missing tooth and an entirely spilled lane.
    if index == 7:
        amount,cap,_ = roles[2];roles[2] = (amount,cap,0)
    if index == 8:
        amount,cap,_ = roles[3];roles[3] = (amount,cap,capacity)
    # Present the winner inside the lane list in the first demonstration.
    order = list(range(n));rng.shuffle(order)
    if index == 0 and order.index(1) in (0,n-1):
        i=order.index(1);j=rng.randint(1,n-2);order[i],order[j]=order[j],order[i]
    colors = rng.sample([2,3,4,6,7,8,9],n)
    if index == 0:
        winner=order.index(1); middle=sorted(colors)[n//2]; j=colors.index(middle)
        colors[winner],colors[j]=colors[j],colors[winner]
    # Move the source comb independently of its final baseline when space permits.
    max_tooth=max(t for amount,cap,t in roles)
    key_base = base if compact or stress else rng.randint(max_tooth,h-1)
    for c in range(key_left,key_left+2*n-1):g[key_base][c]=5
    for i,role in enumerate(order):
        amount,cap,tooth=roles[role];col=frame_left+2+2*i
        for r in range(top+1,top+1+cap):g[r][col]=5
        for r in range(top+1+cap,top+1+cap+amount):g[r][col]=colors[i]
        for r in range(key_base-tooth,key_base):g[r][key_left+2*i]=5
    return g


def generate(seed, settings, demos=3, queries=4):
    integer(seed,0,2**63-1,'seed');integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    mode=setting(settings)
    def pair(i):
        g=scene(seed,i);return {'input':g,'output':solve(g,mode)}
    return {'train':[pair(i) for i in range(demos)],'test':[pair(i) for i in range(6,6+queries)],
            'program_solution':program(settings),'settings':dict(settings),'seed':seed}


def query_order(presentation_seed=0):
    integer(presentation_seed,0,2**63-1,'presentation_seed')
    order=list(range(4));rng_for(presentation_seed,'presentation').shuffle(order);return order


def public_turn(episode, turn, *, presentation_seed=0):
    integer(turn,0,3,'turn')
    if (type(episode) is not dict or type(episode.get('test')) is not list or len(episode['test'])!=4
            or type(episode.get('train')) is not list or not 2<=len(episode['train'])<=6):
        raise ValueError('project from a complete four-query bank with 2..6 demonstrations')
    i=query_order(presentation_seed)[turn]
    return copy.deepcopy({'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in episode['train']],
                          'test':[{'input':grid(episode['test'][i]['input'])}]})


def rival(g, name):
    if name in MODES:return solve(g,name)
    if name=='source_longest':return counterfactual(g)
    if name=='identity':return copy.deepcopy(g)
    spec=extract(g)
    if name=='no_push':return insertion(g,spec,shift_mode='none')
    if name=='full_tooth_push':return insertion(g,spec,shift_mode='full_tooth')
    if name=='keep_source_comb':return insertion(g,spec,keep_comb=True)
    if name=='reverse_teeth':return insertion(g,spec,reverse=True)
    out=insertion(g,spec);groups=surviving(out,spec)
    if name=='top_pack':
        for lane,ps in zip(spec['lanes'],groups):
            col=lane['column'];start=spec['frame'][0]+1
            for r in range(start,spec['base']-lane['tooth']):out[r][col]=0
            for r in range(start,start+len(ps)):out[r][col]=lane['color']
        return out
    if name=='fill_capacity':
        for lane in spec['lanes']:
            for r in range(spec['frame'][0]+1,spec['base']-lane['tooth']):out[r][lane['column']]=lane['color']
        return out
    if name=='mark_all':return mark(out,[p for ps in groups for p in ps])
    n=len(groups)
    if name in ('source_second','source_third'):
        order=sorted(range(n),key=lambda i:-spec['lanes'][i]['amount'])
        i=order[min(1 if name=='source_second' else 2,n-1)]
    elif name=='first_lane':i=0
    elif name=='last_lane':i=n-1
    elif name=='shortest_tooth':i=min(range(n),key=lambda i:spec['lanes'][i]['tooth'])
    elif name=='tallest_tooth':i=max(range(n),key=lambda i:spec['lanes'][i]['tooth'])
    elif name=='largest_loss':i=max(range(n),key=lambda i:spec['lanes'][i]['amount']-len(groups[i]))
    elif name=='min_color':i=min(range(n),key=lambda i:spec['lanes'][i]['color'])
    elif name=='max_color':i=max(range(n),key=lambda i:spec['lanes'][i]['color'])
    else:raise ValueError('unknown rival: '+str(name))
    return mark(out,groups[i])


RIVALS=MODES+('identity','no_push','full_tooth_push','keep_source_comb','reverse_teeth','top_pack',
              'fill_capacity','source_longest','source_second','source_third','mark_all','first_lane','last_lane','shortest_tooth',
              'tallest_tooth','largest_loss','min_color','max_color')


def causal_intermediate(g):
    spec=extract(g);out=insertion(g,spec);groups=surviving(out,spec)
    return {'original_lengths':[l['amount'] for l in spec['lanes']],
            'surviving_lengths':list(map(len,groups)),
            'selected_lane':max(range(len(groups)),key=lambda i:len(groups[i])),
            'canonical_intermediate':out}

RACKET_RIVALS = {'no_push':'no_push.rkt', 'full_tooth_push':'full_tooth_push.rkt', 'source_longest':'wrong_order.rkt','source_second':'source_second.rkt','source_third':'source_third.rkt'}
