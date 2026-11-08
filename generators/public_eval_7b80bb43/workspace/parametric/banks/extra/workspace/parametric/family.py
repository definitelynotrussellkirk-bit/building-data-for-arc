"""General line-straightening grammar for official public parent 7b80bb43."""
from __future__ import annotations
from collections import Counter

TASK_ID=GENERATOR_ID='public_eval_7b80bb43'
VERSION='1.0.0'
SUMMARY='Erase diagonal spurs, repair hinge-cued collinear breaks, preserve uncued breaks.'
DIRECTIONS=((-1,0),(0,-1),(0,1),(1,0))
DIAGONALS=((-1,-1),(-1,1),(1,-1),(1,1))

def validate_grid(grid):
    if (type(grid) is not list or not 1<=len(grid)<=30 or type(grid[0]) is not list or not 1<=len(grid[0])<=30 or
        any(type(row) is not list or len(row)!=len(grid[0]) or any(type(v) is not int or not 0<=v<=9 for v in row) for row in grid)):
        raise ValueError('Expected an integer-color rectangular grid of size 1..30')

def stages(grid, repair_mode='cued'):
    validate_grid(grid)
    height,width=len(grid),len(grid[0]);counts=Counter(v for row in grid for v in row)
    bg=min(counts,key=lambda c:(-counts[c],c))
    colors=sorted(set(counts)-{bg})
    if len(colors)>1:raise ValueError('The line grammar requires exactly two colors')
    fg=colors[0] if colors else bg
    def at(g,r,c):return g[r][c] if 0<=r<height and 0<=c<width else bg
    spurs={(r,c) for r in range(height) for c in range(width) if grid[r][c]!=bg
           and not any(at(grid,r+dr,c+dc)==fg for dr,dc in DIRECTIONS)
           and any(at(grid,r+dr,c+dc)==fg for dr,dc in DIAGONALS)}
    # A diagonal twig can begin orthogonally adjacent to the middle of a
    # stroke. That first pixel is not an axis endpoint: its sole attachment
    # lies on a line continuing in BOTH perpendicular directions.
    extra=set()
    for r in range(height):
        for c in range(width):
            if grid[r][c]!=fg or not any((r+dr,c+dc) in spurs for dr,dc in DIAGONALS):continue
            support=[(dr,dc) for dr,dc in DIRECTIONS if at(grid,r+dr,c+dc)==fg]
            if len(support)==1:
                dr,dc=support[0];rr,cc=r+dr,c+dc
                if (at(grid,rr+dc,cc+dr)==fg and at(grid,rr-dc,cc-dr)==fg
                    and not any(at(grid,r-k*dr,c-k*dc)==fg for k in range(1,max(height,width)))):
                    extra.add((r,c))
    spurs.update(extra)
    cleaned=[[bg if (r,c) in spurs else v for c,v in enumerate(row)] for r,row in enumerate(grid)]
    filled=set()
    for r in range(height):
        for c in range(width):
            if cleaned[r][c]==bg:continue
            for dr,dc in DIRECTIONS:
                if repair_mode=='horizontal' and dr:continue
                if repair_mode=='vertical' and dc:continue
                if repair_mode=='none':continue
                if at(cleaned,r-dr,c-dc)!=fg or at(cleaned,r+dr,c+dc)!=bg:continue
                has_spur=((r+dr+dc,c+dc+dr) in spurs or (r+dr-dc,c+dc-dr) in spurs)
                if repair_mode!='all_gaps' and not has_spur:continue
                rr,cc=r+dr,c+dc;gap=[]
                while 0<=rr<height and 0<=cc<width and cleaned[rr][cc]==bg:
                    gap.append((rr,cc));rr+=dr;cc+=dc
                if 0<=rr<height and 0<=cc<width:filled.update(gap)
    completed=[row[:] for row in cleaned]
    for r,c in filled:completed[r][c]=fg
    return dict(background=bg,foreground=fg,spurs=sorted(spurs),repaired=sorted(filled),
                cleaned=cleaned,completed=completed)

def solve(grid,finish='straighten',repair_mode='cued',junction_mode='new'):
    if finish not in ('straighten','mark_new_junctions'):raise ValueError('Unknown finish')
    state=stages(grid,repair_mode);out=[row[:] for row in state['completed']]
    if finish=='straighten':return out
    bg,fg=state['background'],state['foreground']
    neighborhood=state['cleaned'] if junction_mode=='before' else state['completed']
    candidates=state['repaired'] if junction_mode!='all_junctions' else [(r,c)for r,row in enumerate(out)for c,v in enumerate(row)if v==fg]
    for r,c in candidates:
        degree=sum(0<=r+dr<len(out) and 0<=c+dc<len(out[0]) and neighborhood[r+dr][c+dc]==fg for dr,dc in DIRECTIONS)
        should=degree>=3 if junction_mode!='cross_only' else degree==4
        if junction_mode=='all_repaired':should=True
        if should:out[r][c]=7
    return out


def generate(seed,sample_index,*,difficulty=None,**overrides):
    """Construct line networks with explicit repaired/uncued breaks and noisy bends.

    The layout oracle is the unbent network constructed before corruption, not
    an official example. Every returned scene is checked against that oracle.
    Orthogonal branches create new T junctions after repair; old frame junctions
    and genuine breaks refute mark-all and close-all shortcuts.
    """
    from puzzle_generators.base import gen_ctx
    if type(seed) is not int or not 0<=seed<2**63:raise ValueError('Invalid integer seed')
    if type(sample_index) is not int or sample_index<0:raise ValueError('Invalid sample index')
    if difficulty not in (None,'easy','medium','hard'):raise ValueError('Invalid difficulty')
    if set(overrides)-{'stress'} or ('stress' in overrides and type(overrides['stress']) is not bool):
        raise ValueError('Only an exact boolean stress override is supported')
    ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,
                difficulty=difficulty,overrides=overrides)
    rng=ctx.draw_rng('line-network');stress=overrides.get('stress',False)
    tile=14 if stress else rng.choice((12,13,14));size=2*tile+2
    bg,fg=rng.sample([v for v in range(10) if v!=7],2)
    count=4 if stress or difficulty=='hard' else rng.choice((2,3,4))
    slots=[(1,1),(tile+1,tile+1),(1,tile+1),(tile+1,1)]
    expected=[[bg]*size for _ in range(size)];grid=[row[:] for row in expected]
    for index,(top,left) in enumerate(slots[:count]):
        # Tiled regions are only a construction device; no separators/role codes
        # are published. Line position, gap length, orientation and frame vary.
        patch=[[bg]*tile for _ in range(tile)]
        row=rng.choice((tile//2-1,tile//2))
        for c in range(tile):patch[row][c]=fg
        for r in range(tile):patch[r][0]=patch[r][-1]=fg
        for c in range(tile):patch[-1][c]=fg
        # One deliberately uncued break, with an isolated/short retained fragment.
        patch[row][1]=patch[row][2]=bg
        start=5;length=rng.choice((3,4,5)) if tile>=14 else 3
        end=start+length-1
        junction=start+1 if length<5 else start+3
        for r in range(row-3,row):patch[r][junction]=fg
        # Four-neighbor crosses are optional; T junctions are always included
        # among the other modules, defeating a cross-only shortcut.
        cross=(index%2==1 and length==5)
        if cross:
            for r in range(row+1,row+4):patch[r][junction]=fg
        corrupted=[line[:] for line in patch]
        for c in range(start,end+1):corrupted[row][c]=bg
        for k in (1,2):corrupted[row+k][start-1+k]=fg
        turns=(index+(sample_index%4))%4
        for _ in range(turns):
            patch=[list(line) for line in zip(*patch[::-1])]
            corrupted=[list(line) for line in zip(*corrupted[::-1])]
        for r in range(tile):
            expected[top+r][left:left+tile]=patch[r]
            grid[top+r][left:left+tile]=corrupted[r]
    # Detached diagonal clutter is placed only when the complete chain is
    # separated from all existing strokes, making the constructor oracle exact.
    candidates=[]
    for r in range(2,size-4):
        for c in range(2,size-4):
            chain=[(r,c),(r+1,c+1)]
            if all(grid[rr+dr][cc+dc]==bg for rr,cc in chain for dr in (-1,0,1) for dc in (-1,0,1)):
                candidates.append(chain)
    if candidates:
        for r,c in rng.choice(candidates):grid[r][c]=fg
    # Derive the general rule afresh, not from construction metadata.
    actual=solve(grid)
    if actual!=expected:
        raise ValueError('Constructed network violates the general line grammar')
    if actual==solve(grid,'mark_new_junctions'):
        raise ValueError('No new junction: settings are not distinguishable')
    return grid


def self_check(grid,*,difficulty=None,meta=None):
    try:
        state=stages(grid)
        if not state['spurs'] or not state['repaired']:return ['Need both spurs and cued repairs']
        if solve(grid)==solve(grid,'mark_new_junctions'):return ['Need a newly created junction']
        return []
    except (ValueError,IndexError) as exc:return [str(exc)]
