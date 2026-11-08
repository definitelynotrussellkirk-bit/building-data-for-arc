"""Template-blueprint expansion family for public ARC parent 65b59efc."""
from __future__ import annotations
from collections import Counter
import copy, hashlib, random


def integer(value,low,high,name):
    if type(value) is not int or not low<=value<=high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def check_grid(grid):
    if type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30:
        raise ValueError('grid dimensions must be 1..30')
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid):
        raise ValueError('rectangular exact integer colors required')


def parse(grid):
    """Decode templates, their recolor legend, and the overlaid placement blueprint."""
    check_grid(grid);h,w=len(grid),len(grid[0])
    five_counts=[row.count(5) for row in grid]
    sep_rows=[r for r,n in enumerate(five_counts) if n>4]
    if len(sep_rows)<2:raise ValueError('two horizontal separator rows required')
    size=sep_rows[0];lower=sep_rows[1]
    if not 3<=size<=5 or lower!=2*size+1:raise ValueError('separator geometry must encode equal square template and blueprint bands')
    starts=[s for s in range(0,w-size+1,size+1)
            if any(grid[r][c] not in (0,5) for r in range(size) for c in range(s,s+size))]
    if not 3<=len(starts)<=4:raise ValueError('three or four template panels required')
    templates=[]
    for start in starts:
        colors=sorted({grid[r][c] for r in range(size) for c in range(start,start+size) if grid[r][c] not in (0,5)})
        if len(colors)!=1:raise ValueError('each template must use exactly one color')
        color=colors[0]
        mask=[[grid[r][start+c]==color for c in range(size)] for r in range(size)]
        legends=sorted({grid[r][c] for r in range(lower+1,h) for c in range(start,start+size) if grid[r][c] not in (0,5)})
        if len(legends)!=1:raise ValueError('each template panel needs exactly one recolor singleton')
        templates.append({'start':start,'color':color,'legend':legends[0],'mask':mask,'area':sum(map(sum,mask))})
    by_color={t['color']:t for t in templates}
    placements=[];at_coord={}
    for start in starts:
        for rr in range(size):
            for cc in range(size):
                color=grid[size+1+rr][start+cc]
                if color in (0,5):continue
                if color not in by_color:raise ValueError('blueprint references unknown template color')
                if (rr,cc) in at_coord and at_coord[(rr,cc)]!=color:raise ValueError('blueprint coordinates must not conflict')
                at_coord[(rr,cc)]=color;placements.append({'row':rr,'col':cc,'color':color,'panel_start':start})
    if not placements or any(t['color'] not in [p['color'] for p in placements] for t in templates):
        raise ValueError('every template must appear in the blueprint')
    counts=Counter(p['color'] for p in placements);best=max(counts.values())
    modal=[t['color'] for t in templates if counts[t['color']]==best]
    return {'size':size,'separator_rows':sep_rows[:2],'panel_starts':starts,'templates':templates,
            'placements':placements,'placement_map':at_coord,'placement_counts':dict(counts),
            'modal_color':modal[0],'modal_unique':len(modal)==1}


def solve(grid,placement_scope='all',selected_color=None):
    if placement_scope not in ('all','modal_template','selected'):raise ValueError('unknown placement scope')
    data=parse(grid);size=data['size'];templates={t['color']:t for t in data['templates']}
    keep=None
    if placement_scope=='modal_template':keep=data['modal_color']
    elif placement_scope=='selected':
        if selected_color not in templates:raise ValueError('selected color not present')
        keep=selected_color
    out=[[0]*(size*size) for _ in range(size*size)]
    for (mr,mc),color in data['placement_map'].items():
        if keep is not None and color!=keep:continue
        t=templates[color]
        for r in range(size):
            for c in range(size):
                if t['mask'][r][c]:out[mr*size+r][mc*size+c]=t['legend']
    return out


def intermediate(grid):
    d=parse(grid)
    return {'template_colors':[t['color'] for t in d['templates']],
            'template_areas':{str(t['color']):t['area'] for t in d['templates']},
            'legend_by_template':{str(t['color']):t['legend'] for t in d['templates']},
            'placement_counts':{str(k):v for k,v in d['placement_counts'].items()},
            'modal_template_color':d['modal_color'],
            'blueprint':[[d['placement_map'].get((r,c),0) for c in range(d['size'])] for r in range(d['size'])]}


def _rng(seed,tag):return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{tag}'.encode()).digest(),'big'))


def _patterns(size):
    mid=size//2
    masks=[]
    masks.append([[r in (0,size-1) or c in (0,size-1) for c in range(size)] for r in range(size)])
    masks.append([[r==mid or c==mid for c in range(size)] for r in range(size)])
    masks.append([[r==c or r+c==size-1 for c in range(size)] for r in range(size)])
    masks.append([[(r+c)%2==0 or (r==size-1 and c<mid) for c in range(size)] for r in range(size)])
    return masks


def make_scene(seed,index,height,width,*,size=None,templates=None):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    integer(height,12,30,'height');integer(width,11,30,'width')
    rng=_rng(seed,f'scene:{index}:{height}:{width}')
    candidates=[]
    for s in (3,4,5):
        for n in (3,4):
            active_h=2*s+4;active_w=n*s+n-1
            if active_h<=height and active_w<=width:candidates.append((s,n))
    if size is not None:candidates=[p for p in candidates if p[0]==size]
    if templates is not None:candidates=[p for p in candidates if p[1]==templates]
    if not candidates:raise ValueError('requested canvas cannot hold a lawful scene')
    candidates.sort()
    s,n=(candidates[-1] if index%4==3 else candidates[index%len(candidates)])
    active_w=n*s+n-1;sep1=s;sep2=2*s+1
    grid=[[0]*width for _ in range(height)]
    starts=[i*(s+1) for i in range(n)]
    for c in [st+s for st in starts[:-1]]:
        for r in list(range(s))+list(range(s+1,2*s+1)):grid[r][c]=5
    for r in (sep1,sep2):
        for st in starts:
            for dc in range(s):grid[r][st+dc]=5 if dc in (0,s-1) else 0
        for c in [st+s for st in starts[:-1]]:grid[r][c]=5
    palette=[v for v in range(1,10) if v!=5];rng.shuffle(palette)
    template_colors=palette[:n];legend_colors=palette[n:2*n]
    masks=_patterns(s)[:n]
    order=list(range(n));rng.shuffle(order)
    # Vary which structural mask belongs to which color and panel.
    masks=[masks[i] for i in order]
    for i,st in enumerate(starts):
        for r in range(s):
            for c in range(s):
                if masks[i][r][c]:grid[r][st+c]=template_colors[i]
    # Unique modal count; its identity rotates independently of panel order.
    if s==3:base_counts=[4,2,2,1][:n]
    elif s==4:base_counts=[5,4,3,2][:n]
    else:base_counts=[7,5,4,3][:n]
    modal_index=1+(index%(n-1))
    counts=base_counts[:]
    counts[0],counts[modal_index]=counts[modal_index],counts[0]
    positions=[(r,c) for r in range(s) for c in range(s)];rng.shuffle(positions)
    assignments=[];cursor=0
    for i,count in enumerate(counts):
        for p in positions[cursor:cursor+count]:assignments.append((p,template_colors[i]))
        cursor+=count
    rng.shuffle(assignments)
    placement_panels=list(range(n));rng.shuffle(placement_panels)
    color_panel={template_colors[i]:placement_panels[i] for i in range(n)}
    for (r,c),color in assignments:
        st=starts[color_panel[color]];grid[s+1+r][st+c]=color
    legend_row=sep2+2
    for i,st in enumerate(starts):grid[legend_row][st+s//2]=legend_colors[i]
    scene={'input':grid,'all_output':solve(grid,'all'),'modal_output':solve(grid,'modal_template'),
           'size':s,'template_count':n,'modal_color':parse(grid)['modal_color']}
    problems=self_check_scene(scene)
    if problems:raise ValueError('; '.join(problems))
    return scene


def self_check_scene(scene):
    try:d=parse(scene['input'])
    except (ValueError,TypeError,IndexError) as e:return [str(e)]
    problems=[]
    if not d['modal_unique']:problems.append('modal template must be unique')
    if solve(scene['input'],'all')!=scene['all_output']:problems.append('all label mismatch')
    if solve(scene['input'],'modal_template')!=scene['modal_output']:problems.append('modal label mismatch')
    if scene['all_output']==scene['modal_output']:problems.append('settings do not separate')
    if d['modal_color'] in (d['templates'][0]['color'],d['templates'][-1]['color']):
        # Allowed outside the minimum lesson, but the first two profiles avoid it.
        pass
    return problems


def sample(seed,index,height,width):return make_scene(seed,index,height,width)['input']


from puzzle_generators.base import gen_ctx
GENERATOR_ID=TASK_ID='public_eval_65b59efc'
RULE_TASK_ID='ee_65b59efc'
VERSION='1.0.0'
SUMMARY='Expand a color-coded blueprint with recolored template panels.'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
AXES={'height':{'type':'int','valid':'12..30'},'width':{'type':'int','valid':'11..30'}}
INVARIANTS=['two separator rows','three or four monochrome templates','overlaid color-coded blueprint','one recolor singleton per template']
RULE_HASH='8a6e0ce1c7fe'


def generate(seed,sample_index,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('unknown override')
    for k,v in overrides.items():integer(v,12 if k=='height' else 11,30,k)
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    height=ctx.draw_int_strict('height',12,30);width=ctx.draw_int_strict('width',11,30)
    return sample(seed,sample_index,height,width)


def self_check(grid,*,difficulty=None,meta=None):
    try:parse(grid)
    except (ValueError,TypeError,IndexError) as e:return [str(e)]
    if isinstance(meta,dict):
        observed=observe_overrides(grid)
        return [f'{k} override not realized' for k,v in meta.get('overrides',{}).items() if observed.get(k)!=v]
    return []


def observe_overrides(grid):check_grid(grid);return {'height':len(grid),'width':len(grid[0])}
def rule_mirror(grid):return solve(grid,'all')
