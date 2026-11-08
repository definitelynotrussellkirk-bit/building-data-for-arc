"""Pure oracle and bounded constructive grammar for patterned cardinal beams.

Racket remains label authority. This module makes deterministic label claims;
protected execution is performed by tests, audits, and authoring preflight.
"""
from __future__ import annotations
import random

BG, ANCHOR = 8, 1
COLORS = (0, 2, 3, 4, 5, 6, 7, 9)
DIRECTIONS = ((-1, 0), (1, 0), (0, -1), (0, 1))
RIVALS = ('identity', 'opposite_mode', 'period_one', 'period_two', 'reverse_word',
          'mirror_lanes', 'phase_shift', 'short_extension', 'first_anchor', 'background_only', 'skip_wide')


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in [{low}, {high}]')
    return value


def grid_copy(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or
        type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30 or
        any(type(row) is not list or len(row) != len(grid[0]) or
            any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid)):
        raise ValueError('Expected a rectangular integer-color grid within 30x30')
    return [row[:] for row in grid]


def anchors(grid):
    """Four-connected blue components, sorted by their row-major first cell."""
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == ANCHOR}
    result = []
    while remaining:
        first = min(remaining); remaining.remove(first); stack=[first]; cells=[]
        while stack:
            r,c=stack.pop(); cells.append((r,c))
            for dr,dc in DIRECTIONS:
                q=(r+dr,c+dc)
                if q in remaining: remaining.remove(q); stack.append(q)
        result.append(sorted(cells))
    return result


def analyze(grid):
    grid_copy(grid); H,W=len(grid),len(grid[0]); result=[]
    for cells in anchors(grid):
        r1=min(r for r,c in cells);r2=max(r for r,c in cells)
        c1=min(c for r,c in cells);c2=max(c for r,c in cells)
        for dr,dc in DIRECTIONS:
            face = ([(r1 if dr<0 else r2,c) for c in range(c1,c2+1)] if dr else
                    [(r,c1 if dc<0 else c2) for r in range(r1,r2+1)])
            starts=[(r+dr,c+dc) for r,c in face if grid[r][c]==ANCHOR and
                    0<=r+dr<H and 0<=c+dc<W and grid[r+dr][c+dc] not in (BG,ANCHOR)]
            if not starts: continue
            strips=[];k=0
            while all(0<=r+k*dr<H and 0<=c+k*dc<W and grid[r+k*dr][c+k*dc] not in (BG,ANCHOR) for r,c in starts):
                strips.append([grid[r+k*dr][c+k*dc] for r,c in starts]);k+=1
            period=next(p for p in range(1,len(strips)+1) if all(strip==strips[i%p] for i,strip in enumerate(strips)))
            result.append({'direction':[dr,dc], 'starts':[list(p) for p in starts],
                           'strips':strips, 'period':period, 'bbox':[r1,c1,r2,c2]})
    return result


def solve(grid, mode='repeat', rival=None):
    out=grid_copy(grid);H,W=len(out),len(out[0])
    if mode not in ('repeat','bounce'):raise ValueError('Unknown continuation')
    if rival is not None and rival not in RIVALS:raise ValueError('Unknown rival')
    if rival=='identity':return out
    if rival=='opposite_mode':mode='bounce' if mode=='repeat' else 'repeat'
    records=analyze(grid)
    if rival=='first_anchor':records=records[:1]
    if rival=='skip_wide':records=[r for r in records if len(r['starts'])<3]
    for rec in records:
        dr,dc=rec['direction'];starts=rec['starts'];strips=rec['strips'];period=rec['period']
        if rival=='period_one':period=1
        if rival=='period_two':period=min(2,len(strips))
        word=[row[:] for row in strips[:period]]
        if rival=='reverse_word':word.reverse()
        if rival=='mirror_lanes':word=[row[::-1] for row in word]
        k=len(strips)
        while all(0<=r+k*dr<H and 0<=c+k*dc<W for r,c in starts):
            if rival=='short_extension' and k>=len(strips)+2:break
            phase=k+(1 if rival=='phase_shift' else 0)
            if mode=='bounce' and period>1:
                phase%=2*period-2;index=phase if phase<period else 2*period-2-phase
            else:index=phase%period
            for lane,(r,c) in enumerate(starts):
                rr,cc=r+k*dr,c+k*dc
                if rival!='background_only' or grid[rr][cc]==BG:out[rr][cc]=word[index][lane]
            k+=1
    return out


def _place(g, r, c, width, depth, direction, word, full=False):
    """Draw a cap-ended blue anchor and its observed strip word."""
    def xy(x,y):
        if direction=='down':return r+x,c+y
        if direction=='up':return r-x,c+y
        if direction=='right':return r+y,c+x
        return r+y,c-x
    for x in range(depth):
        for y in range(0 if x in (0,depth-1) else -1, width if x in (0,depth-1) else width+1):
            rr,cc=xy(x,y)
            if not 0<=rr<len(g) or not 0<=cc<len(g[0]) or g[rr][cc]!=BG:
                raise ValueError('Anchor placement collision or boundary error')
            g[rr][cc]=ANCHOR
    k=0
    while True:
        positions=[xy(depth+k,lane) for lane in range(width)]
        if not all(0<=rr<len(g) and 0<=cc<len(g[0]) for rr,cc in positions):break
        if not full and k>=len(word):break
        for lane,(rr,cc) in enumerate(positions):
            if g[rr][cc]!=BG:raise ValueError('Observed seed collision')
            g[rr][cc]=word[k%len(word)][lane]
        k+=1


def _word(rng, width, period, colors=COLORS):
    colors=list(colors);rng.shuffle(colors)
    return [[colors[(i+j)%len(colors)] for j in range(width)] for i in range(period)]


def _cross(rng,H,W,width=2):
    g=[[BG]*W for _ in range(H)];colors=list(COLORS);rng.shuffle(colors)
    _place(g,H//3,1,1,3,'right',[[colors[0]],[colors[1]]],True)
    _place(g,H-2,W-width-3,width,3,'up',_word(rng,width,3,colors[2:]))
    return g


def _stripes(rng,H,W,n,stress=False):
    g=[[BG]*W for _ in range(H)]
    for j in range(n):
        width=3 if stress else 1+(j%3)
        c=2+j*(W//n)
        # Leave one wing cell and at least one separator between independent anchors.
        if c+width>=W: c=W-width-2
        direction='down' if j%2==0 else 'up'
        depth=5 if stress else 3
        r=1 if direction=='down' else H-2
        period=3+(j%2)
        _place(g,r,c,width,depth,direction,_word(rng,width,period),full=(j==n-1 and n>=3))
    return g


def rotate(grid,k):
    for _ in range(k%4):grid=[list(row) for row in zip(*grid[::-1])]
    return grid


def sample_input(seed,index,kind='demo',difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**31-1,'sample_index')
    if kind not in ('demo','query','base'):raise ValueError('Unknown input stream')
    if difficulty not in ('easy','medium','hard'):raise ValueError('Unknown difficulty')
    rng=random.Random(f'53fb4810:{seed}:{kind}:{index}')
    if kind=='query':
        if not 0<=index<4:raise ValueError('Query source index must be 0..3')
        if index==0:g=_stripes(rng,22,20,2)
        elif index==1:g=_cross(rng,24,28,3)
        elif index==2:g=_stripes(rng,26,24,3)
        else:g=_stripes(rng,30,30,4,True)
    elif kind=='demo':
        if index==0:g=_cross(rng,18+seed%2,22+(seed//2)%2,3)
        elif index==1:g=_stripes(rng,20,24,3)
        else:g=_stripes(rng,18+index,24+index%3,2+index%2)
    else:
        if difficulty=='hard':g=_stripes(rng,30,30,4,True)
        else:g=_cross(rng,18 if difficulty=='easy' else 23,22 if difficulty=='easy' else 26)
    # Separate structural stream from rotation; demonstrations 0 and 1 are orthogonal.
    rotation=(seed+index)%4
    return rotate(g,rotation)
