"""Missing-center tile reconstruction and outward projection for public parent db0c5428."""
from __future__ import annotations
from collections import Counter
import hashlib, random


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


def _mode(values):
    counts=Counter(values);best=max(counts.values())
    return next(v for v in values if counts[v]==best)


def _tile(grid,r0,c0,size,ir,ic):
    return [row[c0+ic*size:c0+(ic+1)*size] for row in grid[r0+ir*size:r0+(ir+1)*size]]


def _inward_coordinate(size,ir,ic):
    mid=size//2
    return (size-1 if ir==0 else 0 if ir==2 else mid,
            size-1 if ic==0 else 0 if ic==2 else mid)


def parse(grid):
    """Decode the 3x3 macro-tile source, missing center, and inward samples."""
    check_grid(grid);h,w=len(grid),len(grid[0]);flat=[v for row in grid for v in row]
    bg=_mode(flat);fg=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=bg]
    if not fg:raise ValueError('foreground macro-tile source required')
    r0=min(r for r,c in fg);r1=max(r for r,c in fg);c0=min(c for r,c in fg);c1=max(c for r,c in fg)
    bh,bw=r1-r0+1,c1-c0+1
    if bh!=bw or bh%3 or not 3<=bh//3<=5 or (bh//3)%2==0:
        raise ValueError('foreground bounding box must be a 3x3 array of odd square tiles')
    size=bh//3
    if r0<size or c0<size or r0+4*size>h or c0+4*size>w:
        raise ValueError('canvas must hold the centered 5x5 projection')
    tiles={(ir,ic):_tile(grid,r0,c0,size,ir,ic) for ir in range(3) for ic in range(3)}
    if any(v!=bg for row in tiles[(1,1)] for v in row):raise ValueError('center macro tile must be blank')
    if any(v==bg for key,tile in tiles.items() if key!=(1,1) for row in tile for v in row):
        raise ValueError('surrounding source tiles must be fully occupied')
    source_values=[v for key,tile in tiles.items() if key!=(1,1) for row in tile for v in row]
    base=_mode(source_values)
    records=[]
    for ir in range(3):
        for ic in range(3):
            if (ir,ic)==(1,1):continue
            sr,sc=_inward_coordinate(size,ir,ic)
            records.append({'index':len(records),'tile_row':ir,'tile_col':ic,
                            'sample':tiles[(ir,ic)][sr][sc],'sample_row':sr,'sample_col':sc})
    counts=Counter(r['sample'] for r in records);best=max(counts.values())
    modal=next(r['sample'] for r in records if counts[r['sample']]==best)
    summary=[[base]*size for _ in range(size)]
    summary[0][0]=tiles[(0,0)][size-1][size-1]
    summary[0][size-1]=tiles[(0,2)][size-1][0]
    summary[size-1][0]=tiles[(2,0)][0][size-1]
    summary[size-1][size-1]=tiles[(2,2)][0][0]
    for c in range(1,size-1):
        summary[0][c]=tiles[(0,1)][size-1][c]
        summary[size-1][c]=tiles[(2,1)][0][c]
    for r in range(1,size-1):
        summary[r][0]=tiles[(1,0)][r][size-1]
        summary[r][size-1]=tiles[(1,2)][r][0]
    return {'background':bg,'base_color':base,'bbox':[r0,c0,r1,c1],'size':size,'tiles':tiles,
            'records':records,'sample_counts':dict(counts),'modal_inward_color':modal,
            'modal_unique':sum(v==best for v in counts.values())==1,'summary_tile':summary,
            'output_origin':[r0-size,c0-size]}


def render(grid,selected_indices=None):
    d=parse(grid);h,w=len(grid),len(grid[0]);s=d['size'];or0,oc0=d['output_origin'];bg=d['background']
    out=[[bg]*w for _ in range(h)]
    def place(tile,mr,mc):
        rr=or0+mr*s;cc=oc0+mc*s
        for r,row in enumerate(tile):out[rr+r][cc:cc+s]=row[:]
    for ir in range(3):
        for ic in range(3):
            place(d['summary_tile'] if (ir,ic)==(1,1) else d['tiles'][(ir,ic)],ir+1,ic+1)
    keep=None if selected_indices is None else set(selected_indices)
    for record in d['records']:
        if keep is not None and record['index'] not in keep:continue
        ir,ic=record['tile_row'],record['tile_col']
        place(d['tiles'][(ir,ic)],4-2*ir,4-2*ic)
    return out


def solve(grid,outer_scope='all',selected_color=None,selected_indices=None):
    d=parse(grid)
    if outer_scope=='all':indices=None
    elif outer_scope=='modal_inward':indices=[r['index'] for r in d['records'] if r['sample']==d['modal_inward_color']]
    elif outer_scope=='selected_color':
        indices=[r['index'] for r in d['records'] if r['sample']==selected_color]
    elif outer_scope=='selected_indices':indices=list(selected_indices or [])
    elif outer_scope=='none':indices=[]
    else:raise ValueError('unknown outer scope')
    return render(grid,indices)


def intermediate(grid):
    d=parse(grid)
    return {'tile_size':d['size'],'background':d['background'],'base_color':d['base_color'],
            'inward_samples':[r['sample'] for r in d['records']],
            'sample_counts':{str(k):v for k,v in d['sample_counts'].items()},
            'modal_inward_color':d['modal_inward_color'],'summary_tile':d['summary_tile']}


def _rng(seed,tag):return random.Random(int.from_bytes(hashlib.sha256(f'{seed}:{tag}'.encode()).digest(),'big'))


def make_scene(seed,index,height,width,*,size=None):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'index')
    integer(height,15,30,'height');integer(width,15,30,'width')
    candidates=[s for s in (3,5) if 5*s<=height and 5*s<=width]
    if size is not None:candidates=[s for s in candidates if s==size]
    if not candidates:raise ValueError('requested canvas cannot hold the 5x5 projection')
    s=candidates[-1] if index%4==3 else candidates[index%len(candidates)]
    rng=_rng(seed,f'scene:{index}:{height}:{width}:{s}')
    palette=list(range(10));rng.shuffle(palette)
    bg,base=palette[:2];pair=sorted(palette[2:4]);modal=pair[index%2];other=pair[1-index%2]
    deco1,deco2=palette[4:6]
    modal_sets=[{1,2,3,4,7},{0,2,4,5,6},{1,3,4,5,7},{0,1,3,6,7}]
    modal_indices=modal_sets[index%len(modal_sets)]
    r0=s+rng.randrange(height-5*s+1);c0=s+rng.randrange(width-5*s+1)
    grid=[[bg]*width for _ in range(height)]
    records=[];record_index=0
    for ir in range(3):
        for ic in range(3):
            if (ir,ic)==(1,1):continue
            tile=[[base]*s for _ in range(s)]
            # Distinct but sparse tile decorations; the base remains globally modal.
            positions=[((record_index+1)%s,(2*record_index+1)%s),
                       ((2*record_index+1)%s,(record_index+2)%s),
                       ((record_index+2)%s,(3*record_index+1)%s)]
            for j,(rr,cc) in enumerate(positions):tile[rr][cc]=deco1 if j%2==0 else deco2
            sr,sc=_inward_coordinate(s,ir,ic);tile[sr][sc]=modal if record_index in modal_indices else other
            rr0=r0+ir*s;cc0=c0+ic*s
            for rr,row in enumerate(tile):grid[rr0+rr][cc0:cc0+s]=row
            records.append((record_index,ir,ic,tile[sr][sc]));record_index+=1
    scene={'input':grid,'all_output':solve(grid,'all'),'modal_output':solve(grid,'modal_inward'),
           'size':s,'modal_color':modal,'records':records}
    problems=self_check_scene(scene)
    if problems:raise ValueError('; '.join(problems))
    return scene


def self_check_scene(scene):
    try:d=parse(scene['input'])
    except (ValueError,TypeError,IndexError) as e:return [str(e)]
    problems=[]
    if not d['modal_unique']:problems.append('inward sample mode must be unique')
    if d['sample_counts'].get(d['modal_inward_color'])!=5:problems.append('modal inward sample must occur five times')
    if solve(scene['input'],'all')!=scene['all_output']:problems.append('all label mismatch')
    if solve(scene['input'],'modal_inward')!=scene['modal_output']:problems.append('modal label mismatch')
    if scene['all_output']==scene['modal_output']:problems.append('settings do not separate')
    return problems


def sample(seed,index,height,width):return make_scene(seed,index,height,width)['input']


from puzzle_generators.base import gen_ctx
GENERATOR_ID=TASK_ID='public_eval_db0c5428'
RULE_TASK_ID='ee_db0c5428'
VERSION='1.0.0'
SUMMARY='Reconstruct the missing center tile and project surrounding tiles outward.'
EXAMPLES_NEEDED=2
MIN_STRICT_FRAC=1.0
AXES={'height':{'type':'int','valid':'15..30'},'width':{'type':'int','valid':'15..30'}}
INVARIANTS=['modal background','3x3 macro-tile source','blank center tile','odd square tile size','centered 5x5 output fits canvas']
RULE_HASH='b61f6e73ae6f'


def generate(seed,sample_index,*,difficulty=None,**overrides):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES):raise ValueError('unknown override')
    for k,v in overrides.items():integer(v,15,30,k)
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    height=ctx.draw_int_strict('height',15,30);width=ctx.draw_int_strict('width',15,30)
    return sample(seed,sample_index,height,width)


def self_check(grid,*,difficulty=None,meta=None):
    try:d=parse(grid)
    except (ValueError,TypeError,IndexError) as e:return [str(e)]
    problems=[]
    if not d['modal_unique']:problems.append('inward sample mode must be unique')
    if isinstance(meta,dict):
        observed=observe_overrides(grid)
        problems.extend(f'{k} override not realized' for k,v in meta.get('overrides',{}).items() if observed.get(k)!=v)
    return problems


def observe_overrides(grid):check_grid(grid);return {'height':len(grid),'width':len(grid[0])}
def rule_mirror(grid):return solve(grid,'all')
