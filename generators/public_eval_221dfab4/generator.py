"""General geometry/oracle for public ARC parent 221dfab4.

No supplied example or answer is read here. Racket is the independent label
execution authority; these functions produce deterministic claims for replay.
"""
from __future__ import annotations
from collections import Counter
from typing import Any


def check_grid(grid: Any) -> None:
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30):
        raise ValueError('grid dimensions must be 1..30')
    if any(type(row) is not list or len(row) != len(grid[0])
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('grid must be rectangular with exact integer colors 0..9')


def frame(grid: list[list[int]]) -> dict:
    """Recover the background and directed coordinate frame from yellow cells."""
    check_grid(grid)
    counts = Counter(v for row in grid for v in row)
    bg, n = counts.most_common(1)[0]
    if list(counts.values()).count(n) != 1 or bg in (3, 4):
        raise ValueError('unique modal background distinct from green/yellow required')
    marker = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4]
    if len(marker) < 2:
        raise ValueError('yellow edge segment must contain at least two cells')
    rows, cols = [p[0] for p in marker], [p[1] for p in marker]
    horizontal = min(rows) == max(rows)
    if horizontal:
        if rows[0] not in (0, len(grid) - 1):
            raise ValueError('horizontal marker must be on top or bottom edge')
        lo, hi = min(cols), max(cols)
        reverse = rows[0] != 0
    else:
        if min(cols) != max(cols) or cols[0] not in (0, len(grid[0]) - 1):
            raise ValueError('vertical marker must be on left or right edge')
        lo, hi = min(rows), max(rows)
        reverse = cols[0] != 0
    if hi - lo + 1 != len(marker):
        raise ValueError('marker must be contiguous')
    if 3 in counts:
        raise ValueError('green is an output-only color')
    return dict(bg=bg, horizontal=horizontal, reverse=reverse, lo=lo, hi=hi,
                height=len(grid), width=len(grid[0]))


def depth(f: dict, r: int, c: int) -> int:
    value = r if f['horizontal'] else c
    size = f['height'] if f['horizontal'] else f['width']
    return size - 1 - value if f['reverse'] else value


def solve(grid: list[list[int]], extension: str = 'slice') -> list[list[int]]:
    if type(extension) is not str or extension not in ('slice', 'component'):
        raise ValueError('extension must be slice or component')
    f = frame(grid)
    selected = {p for comp in components(grid, f['bg'])
                if any(depth(f, *p) % 6 == 4 for p in comp) for p in comp}
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            d = depth(f, r, c)
            t = c if f['horizontal'] else r
            if f['lo'] <= t <= f['hi']:
                out[r][c] = 3 if d % 6 == 4 else (4 if d % 2 == 0 else f['bg'])
            elif ((d % 6 == 4 and v != f['bg']) if extension == 'slice'
                  else (r, c) in selected):
                out[r][c] = 3
    return out


def components(grid: list[list[int]], bg: int) -> list[list[tuple[int, int]]]:
    """Original same-color 4-connected components, excluding the yellow marker."""
    todo = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (bg,4)}
    result = []
    while todo:
        first = min(todo)
        todo.remove(first)
        cells, stack = [first], [first]
        color = grid[first[0]][first[1]]
        while stack:
            r,c = stack.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in todo and grid[p[0]][p[1]] == color:
                    todo.remove(p); cells.append(p); stack.append(p)
        result.append(sorted(cells))
    return result


def intermediate(grid: list[list[int]]) -> dict:
    f = frame(grid)
    comps = components(grid, f['bg'])
    return dict(frame=f, green_depths=list(range(4, (f['height'] if f['horizontal'] else f['width']), 6)),
                components=[dict(cells=[list(p) for p in comp],
                     hit=any(depth(f,*p)%6==4 for p in comp)) for comp in comps])


def integer(value, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an integer in {low}..{high}, not bool/coercible')
    return value


def sample(seed: int, index: int, height: int, width: int, *, side: int | None = None,
           palette: str = 'mono') -> list[list[int]]:
    """Construct fresh irregular blobs plus decisive touched/untouched controls.

    side = top/right/bottom/left encoded 0/1/2/3. palette='mono' preserves
    the previous sampler; 'contacts' adds touching differently colored objects.
    Random draws are keyed through
    the repository GenCtx, never global random state. No corpus data is loaded.
    """
    from puzzle_generators.base import gen_ctx
    if type(palette) is not str or palette not in ('mono', 'contacts'):
        raise ValueError('palette must be mono or contacts')
    integer(seed,0,2**63-1,'seed'); integer(index,0,2**31-1,'index')
    integer(height,12,30,'height'); integer(width,12,30,'width')
    if side is None: side = (index + seed % 4) % 4
    integer(side,0,3,'side')
    rng = gen_ctx(seed=seed,sample_index=index,version='1.0.0',task_id='public_eval_221dfab4').draw_rng('scene')
    bg, fg = rng.sample([0,1,2,5,6,7,8,9],2)
    dep, trans = (height,width) if side in (0,2) else (width,height)
    mw = rng.randint(2,min(8,trans-6))
    lo = rng.randint(3,trans-mw-3)
    g = [[bg]*trans for _ in range(dep)]
    g[0][lo:lo+mw] = [4]*mw
    # Same-color four-connected hit and miss objects; an 8-only diagonal
    # bridge connects them, so color-global and 8-connected shortcuts disagree.
    core = {(3,0),(4,0),(5,0),(5,1),(6,2),(7,0),(7,1),(8,1),
            (3,trans-2),(4,trans-2),(5,trans-2),(5,trans-1),
            (1,lo+mw//2)}
    for d,t in core: g[d][t] = fg
    if palette == 'contacts':
        # A differently colored bridge must NOT join the upper hit object to
        # the lower missed object. Add a separate hit of the second color too;
        # color identity alone cannot predict which components are selected.
        other = rng.choice([v for v in range(10) if v not in (bg, fg, 3, 4)])
        secondary = {(6,1), (3,trans-1), (9,trans-1), (10,trans-1), (11,trans-1)}
        for d,t in secondary: g[d][t] = other
        core |= secondary
    reserved = set(core) | {(4,2),(4,trans-3)}
    for d,t in list(core):
        reserved.update(((d-1,t),(d+1,t),(d,t-1),(d,t+1)))
    # Dense bounded random walks provide varied topology and boundary stress,
    # without joining or deleting the guaranteed teaching controls.
    target = int(dep*trans*rng.uniform(.20,.29))
    occupied = set(core)
    for attempt in range(400):
        if len(occupied) >= target: break
        d,t = rng.randrange(1,dep),rng.randrange(trans)
        for _ in range(rng.randint(3,16)):
            if 1 <= d < dep and 0 <= t < trans and (d,t) not in reserved:
                g[d][t]=fg; occupied.add((d,t))
            dd,dt = rng.choice(((-1,0),(1,0),(0,-1),(0,1)))
            d,t = d+dd,t+dt
    out = [[bg]*width for _ in range(height)]
    for d in range(dep):
        for t in range(trans):
            r,c = ((d,t) if side==0 else (t,width-1-d) if side==1 else
                   (height-1-d,t) if side==2 else (t,d))
            out[r][c] = g[d][t]
    frame(out)  # Defensive grammar validation, not label execution.
    return out


# Canonical registration entry point. All dependencies below are mapped shared runtime.
from puzzle_generators.base import gen_ctx
GENERATOR_ID = TASK_ID = 'public_eval_221dfab4'
RULE_TASK_ID = 'ee_221dfab4'
VERSION = '1.0.0'
SUMMARY = 'Project a border yellow marker as periodic stripes and extend every third stripe onto foreground.'
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 1.0
AXES = {'height':{'type':'int','valid':'12..30'},'width':{'type':'int','valid':'12..30'},
        'side':{'type':'int','valid':'0..3: top/right/bottom/left'}}
INVARIANTS = ['unique modal background distinct from 3/4','one contiguous yellow edge segment',
              'green absent from input','same-color touched and untouched components']
RULE_HASH = 'be42209e5ac3'

def generate(seed, sample_index, *, difficulty=None, **overrides):
    integer(seed,0,2**63-1,'seed'); integer(sample_index,0,2**31-1,'sample_index')
    if difficulty not in (None,'easy','medium','hard'): raise ValueError('unknown difficulty')
    if set(overrides)-set(AXES): raise ValueError('unknown override')
    for key,value in overrides.items():
        integer(value,0 if key=='side' else 12,3 if key=='side' else 30,key)
    ctx = gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=difficulty,overrides=overrides)
    height=ctx.draw_int_strict('height',12,30);width=ctx.draw_int_strict('width',12,30)
    side=ctx.draw_int_strict('side',0,3)
    return sample(seed,sample_index,height,width,side=side)


def self_check(grid, *, difficulty=None, meta=None):
    try: frame(grid)
    except (ValueError,TypeError) as exc: return [str(exc)]
    if meta and isinstance(meta,dict):
        expected=meta.get('overrides',{})
        observed=observe_overrides(grid)
        return [f'{k} override not realized' for k,v in expected.items() if observed.get(k)!=v]
    return []


def observe_overrides(grid):
    f=frame(grid)
    side=(2 if f['reverse'] else 0) if f['horizontal'] else (1 if f['reverse'] else 3)
    return {'height':len(grid),'width':len(grid[0]),'side':side}


def rule_mirror(grid):
    return solve(grid,'slice')
