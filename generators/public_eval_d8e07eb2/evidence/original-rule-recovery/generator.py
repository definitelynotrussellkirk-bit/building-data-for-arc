"""General colored-symbol matching and board-line completion.

Self-contained portable sampler. Original examples/gold are never read here.
The known original train[0] header mutation is NOT encoded as an exception.
"""
from __future__ import annotations
from collections import Counter
import copy
import hashlib
import itertools
import random

RULE_TASK_ID = 'ee_d8e07eb2'
GENERATOR_ID = TASK_ID = 'public_eval_d8e07eb2'
VERSION = '1.0.0'
EXAMPLES_NEEDED = 4
AXES = {}
SUMMARY = 'Match selected symbols to a board, then classify completed rows/columns'
INVARIANTS = ['No source-data lookup; portable generator-only operation',
              'Exact-color and silhouette settings share their input grammar',
              'Preserve symbol cells, highlight selected tile backgrounds']
SETTINGS = ('color_shape', 'shape_only')
RIVALS = ('color_only', 'size_only', 'bbox_only', 'opposite_match',
          'rows_only', 'columns_only', 'always_success', 'always_failure',
          'header_always_green', 'footer_only', 'perimeter_only')


def _grid(g):
    if type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list or not 1 <= len(g[0]) <= 30:
        raise ValueError('Expected a nonempty ARC grid')
    if any(type(row) is not list or len(row) != len(g[0]) or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g):
        raise ValueError('Expected rectangular exact integer colors')
    return g


def _runs(values):
    result = []
    for v in values:
        if result and v == result[-1][1] + 1:
            result[-1] = (result[-1][0], v)
        else:
            result.append((v, v))
    return result


def _symbol(g, bg, r1, c1, r2, c2):
    cells = [(r, c, g[r][c]) for r in range(r1, r2 + 1)
             for c in range(c1, c2 + 1) if g[r][c] != bg]
    if not cells:
        raise ValueError('Every board slot must contain a symbol')
    mr = min(r for r, c, v in cells)
    mc = min(c for r, c, v in cells)
    return tuple((r - mr, c - mc, v) for r, c, v in cells)


def _key(symbol, mode):
    if mode == 'color_shape':
        return symbol
    if mode == 'shape_only':
        return tuple((r, c) for r, c, v in symbol)
    if mode == 'color_only':
        return tuple(sorted({v for r, c, v in symbol}))
    if mode == 'size_only':
        return len(symbol)
    if mode == 'bbox_only':
        return (max(r for r, c, v in symbol) + 1, max(c for r, c, v in symbol) + 1)
    raise ValueError('Unknown symbol key')


def parse(g):
    _grid(g)
    counts = Counter(v for row in g for v in row)
    bg = min(counts, key=lambda c: (-counts[c], c))
    separators = [r for r, row in enumerate(g) if len(set(row)) == 1 and row[0] != bg]
    if len(separators) != 2:
        raise ValueError('Expected two full-width nonbackground separator rows')
    top, bottom = separators
    if top < 2 or bottom <= top + 3 or bottom >= len(g) - 1:
        raise ValueError('Missing header, board, or footer')
    rows = _runs(r for r in range(top + 1, bottom) if any(v != bg for v in g[r]))
    cols = _runs(c for c in range(len(g[0])) if any(g[r][c] != bg for r in range(top + 1, bottom)))
    header_cols = _runs(c for c in range(len(g[0])) if any(g[r][c] != bg for r in range(top)))
    if len(rows) < 2 or len(cols) < 2 or not header_cols:
        raise ValueError('Expected a rectangular board and a nonempty selection')
    if any(r1 <= top + 1 or r2 >= bottom - 1 for r1, r2 in rows) or any(c1 < 1 or c2 >= len(g[0]) - 1 for c1, c2 in cols):
        raise ValueError('Board slots require a one-cell highlight margin')
    header = [_symbol(g, bg, 0, c1, top - 1, c2) for c1, c2 in header_cols]
    symbols = [[_symbol(g, bg, r1, c1, r2, c2) for c1, c2 in cols] for r1, r2 in rows]
    flat = [s for row in symbols for s in row]
    if len(set(flat)) != len(flat):
        raise ValueError('Colored board symbols must be unique')
    if any(s not in flat for s in header):
        raise ValueError('Every selected colored symbol must occur on the board')
    return dict(bg=bg, separators=(top, bottom), rows=rows, cols=cols,
                header=header, symbols=symbols)


def matched_positions(d, mode):
    selected = {_key(s, mode) for s in d['header']}
    return {(r, c) for r, row in enumerate(d['symbols']) for c, s in enumerate(row)
            if _key(s, mode) in selected}


def solve(g, match='color_shape', *, rival=None):
    if match not in SETTINGS or (rival is not None and rival not in RIVALS):
        raise ValueError('Unknown setting or rival')
    d = parse(g)
    mode = match
    if rival in ('color_only', 'size_only', 'bbox_only'):
        mode = rival
    elif rival == 'opposite_match':
        mode = SETTINGS[1 - SETTINGS.index(match)]
    chosen = matched_positions(d, mode)
    nr, nc = len(d['rows']), len(d['cols'])
    row_win = any(all((r, c) in chosen for c in range(nc)) for r in range(nr))
    col_win = any(all((r, c) in chosen for r in range(nr)) for c in range(nc))
    win = row_win or col_win
    if rival == 'rows_only':win = row_win
    if rival == 'columns_only':win = col_win
    if rival == 'always_success':win = True
    if rival == 'always_failure':win = False
    out = copy.deepcopy(g)
    top, bottom = d['separators']
    if rival != 'footer_only':
        for r, c in sorted(chosen):
            r1, r2 = d['rows'][r];c1, c2 = d['cols'][c]
            for y in range(r1 - 1, r2 + 2):
                for x in range(c1 - 1, c2 + 2):
                    rim = y in (r1 - 1, r2 + 1) or x in (c1 - 1, c2 + 1)
                    if out[y][x] == d['bg'] and (rival != 'perimeter_only' or rim):
                        out[y][x] = 3
        if win or rival == 'header_always_green':
            for r in range(top):
                out[r] = [3 if v == d['bg'] else v for v in out[r]]
    for r in range(bottom + 1, len(g)):
        out[r] = [3 if win else 2] * len(g[0])
    return out


def _rng(seed, split, index):
    return random.Random(int.from_bytes(hashlib.sha256(f'd8-v1:{seed}:{split}:{index}'.encode()).digest(), 'big'))


def _masks(h, w):
    # Enumerated shape grammar, not any source challenge or label.
    masks = []
    for bits in range(1, 1 << (h * w)):
        cells = tuple((r, c) for r in range(h) for c in range(w) if bits & (1 << (r * w + c)))
        if (len({r for r, c in cells}) == h and len({c for r, c in cells}) == w
                and 2 <= len(cells) < h * w):
            masks.append(cells)
    return masks


# Four small grammars are immutable, independent of seed and settings.
_MASKS = {(h, w): tuple(_masks(h, w)) for h, w in ((2, 3), (2, 4), (3, 3), (3, 4))}


def sample(seed, split, index):
    if type(seed) is not int or seed < 0 or split not in ('train', 'test') or type(index) is not int or not 0 <= index < (6 if split == 'train' else 4):
        raise ValueError('Invalid deterministic scene request')
    rng = _rng(seed, split, index)
    if split == 'test':
        n, mh, mw, width = ((3, 3, 3, 23), (4, 2, 4, 28), (4, 3, 3, 26), (4, 3, 4, 30))[index]
        kinds = ['row', 'column', 'alias', 'negative']
        _rng(seed, 'query-kind', 0).shuffle(kinds)
        kind = kinds[index]
    else:
        n = rng.choice((3, 4));mh = rng.choice((2, 3));mw = rng.choice((3, 4))
        width = n * (mw + 2) + 2 + rng.randrange(31 - (n * (mw + 2) + 2))
        kind = ('row', 'column', 'alias', 'negative', 'row', 'negative')[index]
    height = (n + 1) * (mh + 2) + 5
    bg = rng.choice((0, 8, 9))
    sep = rng.choice([c for c in range(10) if c not in (bg, 2, 3)])
    palette = [c for c in range(10) if c not in (bg, 3)]
    masks = rng.sample(_MASKS[mh, mw], n * n - 1)
    target = (rng.randrange(n), rng.randrange(n))
    other = (rng.choice([r for r in range(n) if r != target[0]]), rng.randrange(n))
    # One exact duplicate silhouette, with distinct source colors. All other
    # silhouettes are unique, and color names intentionally repeat elsewhere.
    shape_map = {};j = 0
    for p in itertools.product(range(n), repeat=2):
        if p == other:continue
        shape_map[p] = masks[j];j += 1
    shape_map[other] = shape_map[target]
    colors = {p: rng.choice(palette) for p in shape_map}
    colors[other] = rng.choice([c for c in palette if c != colors[target]])
    if kind == 'row':selected = [(target[0], c) for c in range(n)]
    elif kind == 'column':selected = [(r, target[1]) for r in range(n)]
    elif kind == 'alias':selected = [(target[0], c) for c in range(n) if c != target[1]] + [other]
    else:
        shift = (target[1] - target[0]) % n
        selected = [(r, (r + shift) % n) for r in range(n)]
    rng.shuffle(selected)
    g = [[bg] * width for _ in range(height)]
    top = mh + 2;bottom = top + n * (mh + 2) + 2
    g[top] = [sep] * width;g[bottom] = [sep] * width
    margin = 2 + (width - (n * (mw + 2) + 2)) // 2
    def stamp(p, row, col):
        for y, x in shape_map[p]:g[row + y][col + x] = colors[p]
    for r in range(n):
        for c in range(n):stamp((r, c), top + 3 + r * (mh + 2), margin + c * (mw + 2))
    for j, p in enumerate(selected):stamp(p, 1, margin + j * (mw + 2))
    return g


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if overrides:raise ValueError('This family has no override axes')
    if type(seed) is not int or seed < 0 or type(sample_index) is not int or sample_index < 0:
        raise ValueError('Nonnegative exact seed/index required')
    if difficulty not in (None, 'easy', 'medium', 'hard'):raise ValueError('Unknown difficulty')
    return sample(seed + 1000003 * (sample_index // 6), 'train', sample_index % 6)


def self_check(grid):
    try:parse(grid)
    except (ValueError, TypeError, IndexError) as e:return [str(e)]
    return []
