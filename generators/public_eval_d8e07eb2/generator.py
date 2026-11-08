"""Portable symbol matching and bingo-line prototype.

The known supplied-header discrepancy is deliberately not special-cased here.
This core is copied byte-for-byte into the native adapter's adjacent kernel.py.
"""
from collections import Counter
from functools import lru_cache
import random

RULE_TASK_ID = 'ee_d8e07eb2'
SETTINGS = ('color_shape', 'shape_only')
RIVALS = ('color_only', 'pixel_count', 'shape_only', 'color_shape',
          'row_only', 'column_only', 'any_match', 'count_threshold',
          'always_success', 'never_success', 'diagonal_counts',
          'winning_slots_only', 'tight_highlight')


def _grid(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or
            any(type(row) is not list for row in g) or not 1 <= len(g[0]) <= 30 or
            any(len(row) != len(g[0]) for row in g) or
            any(type(v) is not int or not 0 <= v <= 9 for row in g for v in row)):
        raise ValueError('Expected a rectangular 1..30 strict integer-color grid')
    return [row[:] for row in g]


def _runs(indices):
    bands = []
    for n in indices:
        if bands and n == bands[-1][1]+1:
            bands[-1] = (bands[-1][0],n)
        else:
            bands.append((n,n))
    return bands


def parse(grid):
    g = _grid(grid)
    h,w = len(g),len(g[0])
    counts = Counter(v for row in g for v in row)
    bg = max(counts, key=lambda v:(counts[v],-v))
    separators = [r for r,row in enumerate(g) if row[0] != bg and len(set(row)) == 1]
    if len(separators) != 2:
        raise ValueError('Expected exactly two full-width non-background separator rows')
    top,bottom = separators
    if top < 2 or bottom <= top+3 or bottom >= h-1:
        raise ValueError('Header, board and footer must all be present')
    rows = _runs(r for r in range(top+1,bottom) if any(v != bg for v in g[r]))
    cols = _runs(c for c in range(w) if any(g[r][c] != bg for r in range(top+1,bottom)))
    header_cols = _runs(c for c in range(w) if any(g[r][c] != bg for r in range(top)))
    if not rows or not cols or not header_cols:
        raise ValueError('Board symbols and header keys are required')
    if any(lo < 1 or hi >= bottom-1 for lo,hi in rows) or any(lo < 1 or hi >= w-1 for lo,hi in cols):
        raise ValueError('Board slots need one background margin on each side')
    def signature(r0,c0,r1,c1):
        cells = [(r,c,g[r][c]) for r in range(r0,r1+1) for c in range(c0,c1+1) if g[r][c] != bg]
        if not cells:
            raise ValueError('Every board slot and header symbol must be nonempty')
        mr,mc = min(p[0] for p in cells),min(p[1] for p in cells)
        return tuple((r-mr,c-mc,x) for r,c,x in cells)
    board = {(r,c):signature(y0,x0,y1,x1) for r,(y0,y1) in enumerate(rows)
             for c,(x0,x1) in enumerate(cols)}
    header = [signature(0,c0,top-1,c1) for c0,c1 in header_cols]
    return {'grid':g,'bg':bg,'top':top,'bottom':bottom,'rows':rows,'cols':cols,
            'header':header,'board':board}


def _key(signature, mode):
    if mode == 'shape_only':
        return tuple((r,c,1) for r,c,x in signature)
    if mode == 'color_only':
        return tuple(sorted({x for r,c,x in signature}))
    if mode == 'pixel_count':
        return len(signature)
    return signature


def matched_positions(data, mode='color_shape'):
    if mode not in SETTINGS+('color_only','pixel_count'):
        raise ValueError('Unknown matching mode')
    wanted = {_key(signature,mode) for signature in data['header']}
    return {position for position,signature in data['board'].items() if _key(signature,mode) in wanted}


def solve(grid, mode='color_shape', *, rival=None):
    if type(mode) is not str or mode not in SETTINGS:
        raise ValueError('Unknown matching setting')
    if rival is not None and rival not in RIVALS:
        raise ValueError('Unknown declared rival')
    d = parse(grid)
    match_mode = rival if rival in ('color_only','pixel_count','shape_only','color_shape') else mode
    matched = matched_positions(d,match_mode)
    nr,nc = len(d['rows']),len(d['cols'])
    full_rows = {r for r in range(nr) if all((r,c) in matched for c in range(nc))}
    full_cols = {c for c in range(nc) if all((r,c) in matched for r in range(nr))}
    success = bool(full_rows or full_cols)
    if rival == 'row_only':success = bool(full_rows)
    elif rival == 'column_only':success = bool(full_cols)
    elif rival == 'any_match':success = bool(matched)
    elif rival == 'count_threshold':success = len(matched) >= min(nr,nc)
    elif rival == 'always_success':success = True
    elif rival == 'never_success':success = False
    elif rival == 'diagonal_counts' and nr == nc:
        success |= all((i,i) in matched for i in range(nr)) or all((i,nr-1-i) in matched for i in range(nr))
    out = [row[:] for row in d['grid']]
    paint = matched
    if rival == 'winning_slots_only':
        paint = {(r,c) for r,c in matched if r in full_rows or c in full_cols}
    margin = 0 if rival == 'tight_highlight' else 1
    for r,c in paint:
        y0,y1 = d['rows'][r];x0,x1 = d['cols'][c]
        for y in range(y0-margin,y1+margin+1):
            for x in range(x0-margin,x1+margin+1):
                if d['grid'][y][x] == d['bg']:
                    out[y][x] = 3
    if success:
        for r in range(d['top']):
            out[r] = [3 if v == d['bg'] else v for v in out[r]]
    for r in range(d['bottom']+1,len(out)):
        out[r] = [3 if success else 2]*len(out[0])
    return out


def _integer(value,name,lo=0,hi=None):
    if type(value) is not int or value < lo or (hi is not None and value > hi):
        raise ValueError(f'{name} must be an exact integer within its declared range')
    return value


@lru_cache(maxsize=1)
def _masks():
    result = []
    for bits in range(1,1 << 9):
        cells = tuple((r,c) for r in range(3) for c in range(3) if bits & (1 << (3*r+c)))
        if (3 <= len(cells) <= 8 and {r for r,c in cells} == {0,1,2}
                and {c for r,c in cells} == {0,1,2}):
            result.append(cells)
    return tuple(result)


def _scene(rng, kind, nr, nc, *, stress=False):
    # Shape masks cover every local row and column, including disconnected forms.
    # This makes axis-separated slot parsing faithful without requiring connectivity.
    bg = rng.choice((0,4,5,7,8,9))
    separator = rng.choice([x for x in range(10) if x not in (bg,2,3)])
    palette = [x for x in range(10) if x not in (bg,2,3)]
    rng.shuffle(palette)
    shapes = rng.sample(_masks(),nr*nc)
    board = {(r,c):[shapes[r*nc+c],palette[(r*nc+c)%len(palette)]]
             for r in range(nr) for c in range(nc)}
    if kind in ('row','near_row'):
        row = rng.randrange(nr)
        selected = [(row,c) for c in range(nc)]
        if kind == 'near_row':
            missing = selected.pop(rng.randrange(nc))
            extra = ((row+1)%nr,missing[1])
            selected.append(extra)
            board[missing][0] = board[extra][0]
            board[missing][1] = next(x for x in palette if x != board[extra][1])
    elif kind in ('column','near_column'):
        col = rng.randrange(nc)
        selected = [(r,col) for r in range(nr)]
        if kind == 'near_column':
            missing = selected.pop(rng.randrange(nr))
            extra = (missing[0],(col+1)%nc)
            selected.append(extra)
            board[missing][0] = board[extra][0]
            board[missing][1] = next(x for x in palette if x != board[extra][1])
    elif kind == 'dispersed':
        selected = [(i,i) for i in range(min(nr,nc))]
        if rng.randrange(2):
            selected = [(r,nc-1-c) for r,c in selected]
    else:
        raise ValueError('Unknown scene profile')
    # A same-color, same-area but different-mask distractor defeats color/count
    # shortcuts while leaving both genuine matching settings unchanged.
    available = [p for p in board if p not in selected and
                 (kind not in ('near_row','near_column') or p != missing)]
    source = selected[0]
    other_masks = [m for m in _masks() if len(m) == len(board[source][0]) and
                   m not in [entry[0] for entry in board.values()]]
    if available and other_masks:
        distractor = rng.choice(available)
        board[distractor] = [rng.choice(other_masks),board[source][1]]
    header = list(selected)
    rng.shuffle(header)
    if stress:
        height,width = 30,30
        top,bottom = 5,27
        ys = [8+5*r for r in range(nr)]
        xs = [2+7*c for c in range(nc)]
    else:
        top = 5+(rng.randrange(2) if nr < 4 else 0)
        ys = [top+3+5*r for r in range(nr)]
        bottom = ys[-1]+4
        height = bottom+3
        width = max(5*nc+2,5*len(header)+2)+rng.randrange(3)
        xs = [2+5*c for c in range(nc)]
    if height > 30 or width > 30:
        raise AssertionError('Scene profile outside ARC bounds')
    g = [[bg]*width for _ in range(height)]
    g[top] = [separator]*width;g[bottom] = [separator]*width
    for (r,c),(mask,color) in board.items():
        for y,x in mask:
            g[ys[r]+y][xs[c]+x] = color
    header_offset = (width-(5*len(header)-2))//2
    for index,position in enumerate(header):
        mask,color = board[position]
        for y,x in mask:
            g[1+y][header_offset+5*index+x] = color
    return g


@lru_cache(maxsize=512)
def _sample(seed,split,index):
    rng = random.Random(f'd8e07eb2-symbol-board:{seed}:{split}:{index}')
    if split == 'train':
        profiles = [('row',3,3),('column',3,4),('near_row',3,3),
                    ('dispersed',4,4),('row',3,4),('near_column',4,3)]
        kind,nr,nc = profiles[index]
    else:
        order = list(range(4))
        random.Random(f'd8-query-order:{seed}').shuffle(order)
        index = order[index]
        profiles = [('column',3,3),('near_column',4,3),('dispersed',4,4),
                    ('near_row' if seed % 2 else 'row',4,4)]
        kind,nr,nc = profiles[index]
    g = _scene(rng,kind,nr,nc,stress=(split == 'test' and index == 3))
    # Validate the actual rendering rather than trusting latent coordinates.
    d = parse(g)
    exact = matched_positions(d,'color_shape')
    broad = matched_positions(d,'shape_only')
    def wins(positions):
        return (any(all((r,c) in positions for c in range(nc)) for r in range(nr)) or
                any(all((r,c) in positions for r in range(nr)) for c in range(nc)))
    expected = ((False,True) if kind.startswith('near_') else
                ((False,False) if kind == 'dispersed' else (True,True)))
    if (wins(exact),wins(broad)) != expected:
        raise AssertionError('Rendered scene does not realize the requested teaching profile')
    return tuple(tuple(row) for row in g)


def sample(seed, split, index):
    _integer(seed,'seed')
    if type(split) is not str or split not in ('train','test'):
        raise ValueError('split must be train or test')
    _integer(index,'index',0,5 if split == 'train' else 3)
    return [list(row) for row in _sample(seed,split,index)]


def generate(seed=0,sample_index=0,difficulty='medium'):
    _integer(seed,'seed');_integer(sample_index,'sample_index')
    if difficulty is None:
        difficulty = 'medium'
    if difficulty not in ('easy','medium','hard'):
        raise ValueError('Unknown difficulty')
    # Standalone input API covers the same curriculum without importing adapter.
    return sample(seed+sample_index//6,'train',sample_index%6)


def self_check(grid,difficulty='medium'):
    try:
        solve(grid)
    except ValueError as error:
        return [str(error)]
    return []
