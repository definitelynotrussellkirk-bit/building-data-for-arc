"""Two-stage completion of a partially erased symmetric color table.

Zero denotes a missing observation.  Stage A copies visible transpose partners.
Stage B consumes that intermediate and closes the remaining holes under the
suffix mirrors that leave the first two row/column indices fixed.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import random

VALUES=('closure','transpose_only')
RIVALS=(
    'other_setting','identity','fold_only','row_only','column_only','double_only',
    'stage_b_original','wrong_prefix_one','wrong_prefix_three','anti_diagonal','fill_one',
)
DEMO_DIMS=(12,16,18,22,26,28)
QUERY_DIMS=(14,20,24,30)


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}; bool is forbidden')
    return value


def grid_check(g):
    if (type(g) is not list or not 8 <= len(g) <= 30 or len(g) % 2
            or type(g[0]) is not list or len(g[0]) != len(g)):
        raise ValueError('Expected an even square grid from 8x8 through 30x30')
    n=len(g)
    if any(type(row) is not list or len(row) != n
           or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g):
        raise ValueError('Expected a square exact-integer color grid; bool is forbidden')
    return n


def mirror_index(i, n, prefix=2):
    if type(prefix) is not int or not 0 <= prefix <= n:
        raise ValueError('Invalid fixed prefix')
    return i if i < prefix else n + prefix - 1 - i


def orbit(r, c, n, prefix=2):
    mr,mc=mirror_index(r,n,prefix),mirror_index(c,n,prefix)
    return tuple(sorted({(r,c),(mr,c),(r,mc),(mr,mc),(c,r),(mc,r),(c,mr),(mc,mr)}))


def all_orbits(n, prefix=2):
    seen=set();answer=[]
    for r in range(n):
        for c in range(n):
            if (r,c) in seen: continue
            cells=orbit(r,c,n,prefix);seen.update(cells);answer.append(cells)
    return answer


def validate_scene(g):
    n=grid_check(g)
    if not any(v == 0 for row in g for v in row):
        raise ValueError('Expected at least one erased zero cell')
    for cells in all_orbits(n):
        visible={g[r][c] for r,c in cells if g[r][c] != 0}
        if not visible:
            raise ValueError('Every symmetry orbit needs at least one visible donor')
        if len(visible) != 1:
            raise ValueError('Visible cells disagree inside a canonical symmetry orbit')
    return n


def transpose_stage(g, *, anti=False):
    n=grid_check(g);out=[row[:] for row in g]
    for r in range(n):
        for c in range(n):
            if g[r][c] != 0: continue
            rr,cc=(n-1-c,n-1-r) if anti else (c,r)
            if g[rr][cc] != 0: out[r][c]=g[rr][cc]
    return out


def candidate_cells(r,c,n,prefix=2,mode='full'):
    mr,mc=mirror_index(r,n,prefix),mirror_index(c,n,prefix)
    if mode=='row': return ((mr,c),)
    if mode=='column': return ((r,mc),)
    if mode=='double': return ((mr,mc),)
    if mode!='full': raise ValueError('Unknown closure candidate mode')
    return ((mr,c),(r,mc),(mr,mc))


def closure_stage(stage_a, *, source=None, prefix=2, mode='full'):
    n=grid_check(stage_a);source=stage_a if source is None else source
    grid_check(source);out=[row[:] for row in stage_a]
    for r in range(n):
        for c in range(n):
            if stage_a[r][c] != 0: continue
            for rr,cc in candidate_cells(r,c,n,prefix,mode):
                if source[rr][cc] != 0:
                    out[r][c]=source[rr][cc];break
    return out


def solve(g, value='closure', rival=None):
    validate_scene(g)
    if value not in VALUES: raise ValueError('Unknown completion setting')
    if rival is not None and rival not in RIVALS: raise ValueError('Unknown rival')
    if rival=='identity': return [row[:] for row in g]
    if rival=='fill_one': return [[1 if v==0 else v for v in row] for row in g]
    effective=VALUES[1-VALUES.index(value)] if rival=='other_setting' else value
    anti=rival=='anti_diagonal'
    stage1=[row[:] for row in g] if rival=='fold_only' else transpose_stage(g,anti=anti)
    force_closure=rival in {'fold_only','row_only','column_only','double_only','stage_b_original',
                             'wrong_prefix_one','wrong_prefix_three'}
    if effective=='transpose_only' and not force_closure:
        return stage1
    prefix=1 if rival=='wrong_prefix_one' else 3 if rival=='wrong_prefix_three' else 2
    mode={'row_only':'row','column_only':'column','double_only':'double'}.get(rival,'full')
    source=g if rival=='stage_b_original' else stage1
    return closure_stage(stage1,source=source,prefix=prefix,mode=mode)


def derive(g):
    validate_scene(g);n=len(g)
    a=transpose_stage(g);b=closure_stage(a)
    a_filled=[];b_filled=[];dependent=[]
    for r in range(n):
        for c in range(n):
            if g[r][c]==0 and a[r][c]!=0:
                a_filled.append({'cell':[r,c],'value':a[r][c],'transpose':[c,r]})
            if a[r][c]==0 and b[r][c]!=0:
                chosen=next(([rr,cc] for rr,cc in candidate_cells(r,c,n) if a[rr][cc]!=0),None)
                record={'cell':[r,c],'value':b[r][c],'source':chosen}
                b_filled.append(record)
                if chosen is not None and g[chosen[0]][chosen[1]]==0:
                    dependent.append(record)
    return {'stage_a':a,'stage_b':b,'stage_a_filled':a_filled,'stage_b_filled':b_filled,
            'stage_b_from_stage_a_only':dependent}


def self_check(g):
    try:
        validate_scene(g)
        if any(v==0 for row in solve(g,'closure') for v in row):
            return ['Full closure left an erased cell']
    except (ValueError,TypeError,IndexError) as error:
        return [str(error)]
    return []


def stream(seed, kind, index=0):
    integer(seed,0,2**63-1,'seed');integer(index,0,2**63-1,'index')
    payload=f'981571dc:{seed}:{kind}:{index}'.encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(),'big'))


def index_classes(n):
    grid_check([[1]*n for _ in range(n)])
    groups=[(0,),(1,)];seen={0,1}
    for i in range(2,n):
        if i in seen: continue
        j=mirror_index(i,n);groups.append(tuple(sorted((i,j))));seen.update((i,j))
    return groups


def complete_grid(rng,n):
    groups=index_classes(n);k=len(groups)
    table=[[0]*k for _ in range(k)]
    for i in range(k):
        for j in range(i,k):
            # Mixed arithmetic plus RNG avoids trivial rows while remaining deterministic.
            color=1+((rng.randrange(9)+3*i+5*j+i*j)%9)
            table[i][j]=table[j][i]=color
    owner={x:i for i,g in enumerate(groups) for x in g}
    return [[table[owner[r]][owner[c]] for c in range(n)] for r in range(n)]


def basis_for_orbit(cells,n):
    cellset=set(cells)
    for r,c in cells:
        mr,mc=mirror_index(r,n),mirror_index(c,n)
        named={(r,c),(c,r),(mr,c),(r,mc),(mr,mc),(c,mr),(mc,r),(mc,mr)}
        if len(named)==8 and named==cellset:
            return r,c
    raise ValueError('Expected a generic eight-cell orbit')


def named_cells(r,c,n):
    mr,mc=mirror_index(r,n),mirror_index(c,n)
    return {'x':(r,c),'t':(c,r),'r':(mr,c),'c':(r,mc),'d':(mr,mc),
            'tr':(c,mr),'tc':(mc,r),'td':(mc,mr)}


def apply_teaching_masks(g,rng,extra_target):
    n=len(g);generic=[cells for cells in all_orbits(n) if len(cells)==8];rng.shuffle(generic)
    if len(generic)<5: raise ValueError('Canvas too small for teaching masks')
    patterns=(
        # Genuine A -> B chain: B sees donors manufactured by transpose repair.
        ('chain',('x','t','r','c','d')),
        # A-only cell: fold-only cannot recover x from the original grid.
        ('direct',('x','r','c','d')),
        # Candidate-specific holes keep the three suffix mirrors distinguishable.
        ('row',('x','t','c','tc','d','td')),
        ('column',('x','t','r','tr','d','td')),
        ('double',('x','t','r','tr','c','tc')),
    )
    used=set()
    for cells,(_,keys) in zip(generic,patterns):
        coords=named_cells(*basis_for_orbit(cells,n),n)
        for key in keys:
            g[coords[key][0]][coords[key][1]]=0;used.add(coords[key])
    candidates=generic[len(patterns):]
    rng.shuffle(candidates)
    for cells in candidates:
        if sum(v==0 for row in g for v in row)>=extra_target: break
        available=[p for p in cells if p not in used];rng.shuffle(available)
        count=rng.randint(1,min(3,len(available),len(cells)-1))
        for r,c in available[:count]:g[r][c]=0;used.add((r,c))
    return g


def make_input(seed,index,kind='ordinary',n=None,stress=False):
    rng=stream(seed,kind,index)
    if n is None:
        n=30 if stress else rng.choice((12,14,16,18,20,22,24,26,28))
    if type(n) is not int or not 8<=n<=30 or n%2: raise ValueError('n must be even in 8..30')
    complete=complete_grid(rng,n)
    target=max(16,n*n//7) if stress else max(12,n*n//12)
    g=apply_teaching_masks([row[:] for row in complete],rng,target)
    if solve(g,'closure')!=complete: raise ValueError('Mask construction did not recover its complete table')
    if solve(g,'closure')==solve(g,'transpose_only'): raise ValueError('Settings unexpectedly agree')
    if self_check(g): raise ValueError('Generated scene failed its own grammar')
    return g


@lru_cache(maxsize=128)
def input_bank(seed):
    integer(seed,0,2**63-1,'seed')
    first=make_input(seed,0,'teach',DEMO_DIMS[0])
    survivors=[]
    for value in VALUES:
        gold=solve(first,value)
        survivors.extend((value,r) for r in RIVALS if solve(first,value,r)==gold)
    for i in range(1,513):
        second=make_input(seed,i,'teach',DEMO_DIMS[1])
        if second!=first and all(solve(second,v,r)!=solve(second,v) for v,r in survivors): break
    else: raise ValueError(f'Bounded teaching search exhausted with {survivors!r}')
    demos=[first,second]
    for i,n in enumerate(DEMO_DIMS[2:],start=2):demos.append(make_input(seed,i,'extra_demo',n))
    queries=[make_input(seed,i,'query',n,stress=n==30) for i,n in enumerate(QUERY_DIMS)]
    if len({json.dumps(g,separators=(',',':')) for g in demos+queries})!=10:
        raise ValueError('Unexpected duplicate generated input')
    # The minimum prefix must reject every retained shortcut for both settings.
    for value in VALUES:
        for rival in RIVALS:
            if all(solve(g,value,rival)==solve(g,value) for g in demos[:2]):
                raise ValueError(f'Teaching prefix retains rival {value}/{rival}')
    return (tuple(json.dumps(g,separators=(',',':')) for g in demos),
            tuple(json.dumps(g,separators=(',',':')) for g in queries))
