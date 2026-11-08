"""Color-keyed template expansion with episode-fixed coarse placement.

Top panels define monochrome micro-templates. Middle panels contain disjoint
coarse placement masks whose colors identify templates even when panel order is
permuted. A bottom swatch beneath each top panel recolors that template. The
canonical setting places expanded tiles at the mask coordinates; the alternate
transposes only the coarse coordinates while leaving template pixels unchanged.
"""
from __future__ import annotations
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import random

PARAMETER='coarse_placement'
VALUES=('identity','transpose')
DEFAULT={PARAMETER:'identity'}
RIVALS=('other_setting','column_match','wrong_swatch','solid_tiles','ignore_swatches',
        'transpose_template','first_template_only','mask_pixels_only','blank')
HERE=Path(__file__).resolve().parent


def integer(value,lo,hi,name):
    if type(value) is not int or not lo<=value<=hi:
        raise ValueError(f'{name} must be an exact integer in {lo}..{hi}')
    return value


def grid(value):
    if type(value) is not list or not 1<=len(value)<=30 or type(value[0]) is not list or not 1<=len(value[0])<=30:
        raise ValueError('Expected a nonempty grid of at most 30x30')
    width=len(value[0])
    if any(type(row) is not list or len(row)!=width or any(type(v) is not int or not 0<=v<=9 for v in row) for row in value):
        raise ValueError('Expected rectangular exact integer colors 0..9')
    return deepcopy(value)


def settings(value):
    if type(value) is not dict or set(value)!={PARAMETER} or type(value[PARAMETER]) is not str or value[PARAMETER] not in VALUES:
        raise ValueError(f'Expected exactly {PARAMETER} in {VALUES}')
    return value[PARAMETER]


def program(setting):
    mode=settings(setting);name='canonical.rkt' if mode=='identity' else 'transpose.rkt'
    return (HERE/name).read_text(encoding='utf-8')


def counterfactual_program(setting):
    settings(setting);return (HERE/'column_match.rkt').read_text(encoding='utf-8')


def derive(value):
    g=grid(value);width=len(g[0])
    if 5 not in g[0]:raise ValueError('First template must be followed by a gray separator')
    size=g[0].index(5)
    if size not in (3,4,5) or len(g)<2*size+4:
        raise ValueError('Supported template sizes are 3, 4, and 5')
    panels=[];occupied=set();role_cells=set();saw_empty=False
    for left in range(0,width-size+1,size+1):
        template=[row[left:left+size] for row in g[:size]]
        colors={v for row in template for v in row if v}
        if not colors:
            saw_empty=True;continue
        if saw_empty or len(colors)!=1 or 5 in colors:
            raise ValueError('Templates must be consecutive, monochrome, and non-gray')
        source=next(iter(colors))
        mask=[row[left:left+size] for row in g[size+1:2*size+1]]
        mask_colors={v for row in mask for v in row if v}
        if len(mask_colors)!=1 or 5 in mask_colors:
            raise ValueError('Every middle panel needs one non-gray mask color')
        swatches={g[r][c] for r in range(2*size+2,2*size+4)
                  for c in range(left,left+size) if g[r][c] not in (0,5)}
        if len(swatches)!=1:raise ValueError('Each aligned swatch band needs one non-gray color')
        cells=[]
        for r in range(size):
            for c in range(size):
                if mask[r][c]:
                    if (r,c) in occupied:raise ValueError('Middle masks must have disjoint coarse locations')
                    occupied.add((r,c));cells.append([r,c])
        if len(cells)<1:raise ValueError('Every mask must occupy at least one coarse cell')
        for r in list(range(size))+list(range(size+1,2*size+1))+[2*size+2,2*size+3]:
            role_cells.update((r,c) for c in range(left,left+size))
        panels.append({'left':left,'source':source,'template':template,'mask':mask,
                       'mask_color':next(iter(mask_colors)),'mask_cells':cells,
                       'swatch':next(iter(swatches))})
    if len(panels) not in (3,4):raise ValueError('Expected three or four template panels')
    sources=[p['source'] for p in panels]
    if len(set(sources))!=len(sources):raise ValueError('Template source colors must be distinct')
    if sorted(sources)!=sorted(p['mask_color'] for p in panels):
        raise ValueError('Mask colors must match template keys exactly once each')
    if len({p['swatch'] for p in panels})!=len(panels):raise ValueError('Target swatches must be distinct')
    for r in range(len(g)):
        for c in range(width):
            if (r,c) not in role_cells and g[r][c] not in (0,5):
                raise ValueError('Outside role panels only background and gray separators are allowed')
    return {'size':size,'panels':panels,'height':len(g),'width':width,
            'occupied_coarse_cells':[list(x) for x in sorted(occupied)]}


def solve(value,placement='identity',*,rival=None):
    g=grid(value)
    if type(placement) is not str or placement not in VALUES:raise ValueError('Unknown coarse placement')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    if rival=='other_setting':placement='transpose' if placement=='identity' else 'identity'
    state=derive(g);n=state['size'];panels=state['panels'];keyed={p['source']:p for p in panels}
    out=[[0]*(n*n) for _ in range(n*n)]
    if rival=='blank':return out
    for panel_index,panel in enumerate(panels):
        for r,c in panel['mask_cells']:
            template=panel if rival=='column_match' else keyed[panel['mask_color']]
            if rival=='first_template_only':template=panels[0]
            target=panel['swatch'] if rival=='wrong_swatch' else template['swatch']
            if rival=='ignore_swatches':target=template['source']
            rr,cc=(c,r) if placement=='transpose' else (r,c)
            for a in range(n):
                for b in range(n):
                    if rival=='mask_pixels_only':
                        pixel=panel['mask'][a][b]
                    elif rival=='transpose_template':pixel=template['template'][b][a]
                    else:pixel=template['template'][a][b]
                    out[rr*n+a][cc*n+b]=target if (pixel or rival=='solid_tiles') else 0
    return out


def _digest(value):
    return hashlib.sha256((json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()


def _sample_input(seed,index,*,size,count):
    rng=random.Random(int(_digest(['65b59efc-input-v2',seed,index]),16))
    palette=[1,2,3,4,6,7,8,9]
    sources=rng.sample(palette,count);swatches=rng.sample(palette,count)
    if sources==swatches:swatches=swatches[1:]+swatches[:1]
    shapes=[]
    for source in sources:
        for _ in range(128):
            shape=[[source if rng.random()<0.64 else 0 for _ in range(size)] for _ in range(size)]
            bits=tuple(v!=0 for row in shape for v in row)
            if (any(bits) and not all(bits)
                    and any(shape[r][c]!=shape[c][r] for r in range(size) for c in range(size))
                    and bits not in [tuple(v!=0 for row in old for v in row) for old in shapes]):
                shapes.append(shape);break
        else:raise ValueError('Shape sampling exhausted')
    order=rng.sample(range(count),count)
    if order==list(range(count)):order=order[1:]+order[:1]
    for _ in range(128):
        positions=[(r,c) for r in range(size) for c in range(size)];rng.shuffle(positions)
        occupied_count=rng.randint(max(2*count,size+1),size*size)
        owners=list(range(count))*2+[rng.randrange(count) for _ in range(occupied_count-2*count)]
        coarse=[[0]*size for _ in range(size)]
        for (r,c),owner in zip(positions,owners):coarse[r][c]=sources[owner]
        supports=[[coarse[r][c]==source for r in range(size) for c in range(size)] for source in sources]
        if coarse!=[list(row) for row in zip(*coarse)] and all(sum(s)>=2 for s in supports):break
    else:raise ValueError('Coarse mask sampling exhausted')
    height,width=2*size+4,count*(size+1)-1
    g=[[0]*width for _ in range(height)]
    for divider in (size,2*size+1):
        for c in range(width):
            if c%(size+1) in (0,size-1,size) or c%2==0:g[divider][c]=5
    for divider in range(size,width,size+1):
        for r in range(height):
            if r%(size+1) in (0,size-1,size) or r%2==0:g[r][divider]=5
    for i in range(count):
        left=i*(size+1);mask_source=sources[order[i]]
        for r in range(size):
            g[r][left:left+size]=shapes[i][r]
            for c in range(size):
                if coarse[r][c]==mask_source:g[size+1+r][left+c]=mask_source
        for c in range((size-1)//2,size//2+1):g[2*size+3][left+c]=swatches[i]
    derive(g);return g


def _pad30(g):
    out=[[0]*30 for _ in range(30)]
    for r,row in enumerate(g):out[r][:len(row)]=row
    return out


def _raw(seed,role,index,attempt):
    if role=='query':profiles=((3,3),(4,4),(5,3),(5,4))
    else:profiles=((3,3),(4,4),(5,3),(3,4),(4,3),(5,4))
    size,count=profiles[index];g=_sample_input(seed,index+attempt*97+(1000 if role=='query' else 0),size=size,count=count)
    if role=='query' and index==3:g=_pad30(g)
    if solve(g,'identity')==solve(g,'transpose'):raise ValueError('Settings alias')
    return g


def _raw_scene(seed,role,index):
    for attempt in range(256):
        try:return _raw(seed,role,index,attempt)
        except ValueError:pass
    raise ValueError('Bounded template scene search exhausted')


@lru_cache(maxsize=512)
def teaching(seed):
    integer(seed,0,2**63-1,'seed')
    for attempt in range(256):
        pair=(_raw(seed,'demo',0,attempt),_raw(seed,'demo',1,attempt))
        if all(survivors([{'input':deepcopy(g),'output':solve(g,value)} for g in pair],{PARAMETER:value})==['intended'] for value in VALUES):
            return deepcopy(pair)
    raise ValueError('Bounded teaching search could not refute declared rivals')


def sample(seed,role,index):
    integer(seed,0,2**63-1,'seed')
    if role not in ('demo','query'):raise ValueError('role must be demo or query')
    integer(index,0,5 if role=='demo' else 3,'index')
    if role=='demo' and index<2:return deepcopy(teaching(seed)[index])
    return _raw_scene(seed,role,index)


def generate(seed,setting,demos,queries):
    integer(seed,0,2**63-1,'seed');placement=settings(setting)
    integer(demos,2,6,'demos');integer(queries,1,4,'queries')
    demo_inputs=[sample(seed,'demo',i) for i in range(demos)]
    query_inputs=[sample(seed,'query',i) for i in range(queries)]
    pairs=lambda values:[{'input':g,'output':solve(g,placement)} for g in values]
    return {'train':pairs(demo_inputs),'test':pairs(query_inputs),'program_solution':program(setting)}


def survivors(train,setting):
    placement=settings(setting);out=['intended']
    for rival in RIVALS:
        if all(solve(p['input'],placement,rival=rival)==p['output'] for p in train):out.append(rival)
    return out


def input_errors(value):
    try:derive(value);return []
    except ValueError as exc:return [str(exc)]


def public_view(episode,query_index):
    integer(query_index,0,len(episode['test'])-1,'query index')
    return {'train':[{'input':grid(p['input']),'output':grid(p['output'])} for p in episode['train']],
            'test':[{'input':grid(episode['test'][query_index]['input'])}]}


def presentation_order(seed):
    integer(seed,0,2**63-1,'presentation seed');order=list(range(4))
    random.Random(f'65b59efc-presentation-v1:{seed}').shuffle(order);return order


def public_turns(seed,setting,demos,presentation_seed=0,count=4):
    integer(count,1,4,'presentation count');integer(presentation_seed,0,2**63-1,'presentation seed')
    episode=generate(seed,setting,demos,4)
    return [public_view(episode,i) for i in presentation_order(seed^presentation_seed)[:count]]


def intermediate(value,setting):
    placement=settings(setting);state=derive(value)
    keyed={p['source']:p for p in state['panels']};records=[]
    for panel in state['panels']:
        template=keyed[panel['mask_color']]
        records.append({'mask_panel_left':panel['left'],'mask_color':panel['mask_color'],
                        'coarse_cells':deepcopy(panel['mask_cells']),'template_source':template['source'],
                        'template_left':template['left'],'swatch':template['swatch'],
                        'placement':placement})
    return {'size':state['size'],'records':records}


def dependency():
    return {'step_a':'Parse the top template dictionary, match each permuted middle mask to a template by source color, and attach the swatch aligned under that template.',
            'intermediate':'For every mask panel: its coarse occupied cells, the color-matched micro-template, and that template column\'s output swatch.',
            'step_b':'Place a recolored copy of the matched template at each coarse cell, using the episode\'s identity or transposed coarse coordinates.',
            'why_b_depends_on_a':'The mask panel order is deliberately permuted. Substituting same-column matching changes both template geometry and swatch ownership, so B cannot render the correct mosaic without A\'s color-keyed records.'}
