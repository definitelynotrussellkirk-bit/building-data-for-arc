"""Hollow-cross contour spirals for public parent da515329.

Recover the common arm length and center. Four chiral paths extend the arms,
leaving one background cell between successive contours. The smallest seed
(radius one) expands to spacing radius two. Segments continue outside the
canvas: a later segment can re-enter. This module is deliberately standalone
for the ordinary copied worker; the native engine is an exact snapshot.
Python outputs are claims; reference.rkt is the independent label authority.
"""
import random

RULE_TASK_ID = 'ee_da515329'
TASK_ID = 'public_eval_da515329'
VERSION = '1.0.0'
SETTINGS = ('clockwise', 'counterclockwise')
DIRECTIONS = ((-1,0),(0,1),(1,0),(0,-1))


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def grid_check(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
        or any(type(row) is not list or len(row) != len(grid[0])
               or any(type(v) is not int or not 0 <= v <= 9 for v in row)
               for row in grid)):
        raise ValueError('expected a rectangular 1..30 exact-integer color grid')


def analyze(grid):
    """Validate and measure a monochrome, equal-armed hollow cross."""
    grid_check(grid)
    cells={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v}
    colors={grid[r][c] for r,c in cells}
    if not cells or len(colors)!=1:
        raise ValueError('one nonzero cross color required')
    top,bottom=min(r for r,c in cells),max(r for r,c in cells)
    left,right=min(c for r,c in cells),max(c for r,c in cells)
    if bottom-top != right-left or (bottom-top)%2:
        raise ValueError('equal integer-radius arms required')
    radius=(bottom-top)//2;cr=(top+bottom)//2;cc=(left+right)//2
    expected={(cr+t*dr,cc+t*dc) for dr,dc in DIRECTIONS for t in range(1,radius+1)}
    if radius<1 or cells!=expected:
        raise ValueError('a single hollow cross without distractors is required')
    return {'center':[cr,cc],'arm_length':radius,'color':next(iter(colors))}


def render(height, width, center, radius, color, turn='clockwise'):
    """Consume the measured intermediate; clip paint, never path movement."""
    if turn not in SETTINGS:
        raise ValueError('unknown turning direction')
    out=[[0]*width for _ in range(height)]
    sign=1 if turn=='clockwise' else -1
    k=max(2,radius)

    def segment(r,c,d,n):
        dr,dc=DIRECTIONS[d%4];rr,cc=r+n*dr,c+n*dc
        if n:
            if dc==0 and 0<=c<width:
                lo=max(0,min(r+dr,rr));hi=min(height-1,max(r+dr,rr))
                for row in range(lo,hi+1):out[row][c]=color
            elif dr==0 and 0<=r<height:
                lo=max(0,min(c+dc,cc));hi=min(width-1,max(c+dc,cc))
                for col in range(lo,hi+1):out[r][col]=color
        return rr,cc

    for start in range(4):
        r,c=segment(*center,start,k);direction=(start+sign)%4
        # Every four groups the contour expands by eight on each side.
        # h+w groups safely exceed all possible re-entry of this <=30 grid.
        for layer in range(height+width):
            r,c=segment(r,c,direction,2+4*layer)
            r,c=segment(r,c,direction+sign,k-2)
            r,c=segment(r,c,direction,k)
            direction=(direction+sign)%4
    return out


def solve(grid, mode='clockwise'):
    if type(mode) is not str or mode not in SETTINGS:
        raise ValueError('mode must be clockwise or counterclockwise')
    info=analyze(grid)
    return render(len(grid),len(grid[0]),info['center'],info['arm_length'],info['color'],mode)


def rule_mirror(grid):
    return solve(grid,'clockwise')


def _cross(rng,height,width,radius,*,off_center=False):
    centers=[(r,c) for r in range(radius,height-radius) for c in range(radius,width-radius)
             if not off_center or (2*r!=height-1 and 2*c!=width-1)]
    cr,cc=rng.choice(centers);color=rng.randrange(1,10)
    g=[[0]*width for _ in range(height)]
    for dr,dc in DIRECTIONS:
        for t in range(1,radius+1):g[cr+t*dr][cc+t*dc]=color
    return g


def scene(seed, index, kind):
    integer(seed,0,2**63-1,'seed')
    if kind not in ('demo','query'):
        raise ValueError('kind must be demo or query')
    integer(index,0,5 if kind=='demo' else 3,'index')
    rng=random.Random(f'da515329:v1:{seed}:{kind}:{index}')
    dimensions=((11,13),(17,19),(20,16),(15,23),(23,17),(26,22)) if kind=='demo' else ((14,16),(19,23),(24,27),(30,30))
    h,w=dimensions[index]
    if rng.randrange(2):h,w=w,h
    radius=(1 if index==0 else rng.choice((3,4))) if kind=='demo' and index<2 else rng.randint(1,min(6,(min(h,w)-3)//2))
    return _cross(rng,h,w,radius,off_center=True)


def generate(seed=0, sample_index=0, difficulty='medium'):
    integer(seed,0,2**63-1,'seed');integer(sample_index,0,2**63-1,'sample_index')
    if difficulty is None:difficulty='medium'
    if difficulty not in ('easy','medium','hard','mixed'):
        raise ValueError('unsupported difficulty')
    rng=random.Random(f'da515329:base:{seed}:{sample_index}:{difficulty}')
    if difficulty=='mixed':difficulty=rng.choice(('easy','medium','hard'))
    h,w,cap={'easy':(11,13,2),'medium':(19,23,4),'hard':(30,30,6)}[difficulty]
    if rng.randrange(2):h,w=w,h
    return _cross(rng,h,w,rng.randint(1,cap))


def self_check(grid, difficulty=None):
    try:analyze(grid)
    except (ValueError,TypeError) as exc:return [str(exc)]
    return []
