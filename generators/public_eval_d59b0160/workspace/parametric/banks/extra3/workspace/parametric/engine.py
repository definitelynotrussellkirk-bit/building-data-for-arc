"""Color-key panels: complete palette matching and non-key palette propagation.

The solver reads only the grid. Sampling metadata never participates in labels.
"""
from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
import random

D4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
D8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)
COLORS = (1, 2, 4, 5, 6, 8, 9)
POLICIES = ('matching', 'palette_cascade', 'identity', 'any_key', 'exact_palette',
            'nonzero_count', 'largest', 'smallest', 'first', 'erase_marks_only',
            'one_wave', 'global_palette', 'include_key_colors', 'eight_connected',
            'cascade_eight', 'fixed_three', 'key_multiplicity', 'erase_all', 'two_best_keycounts')


def grid_check(g):
    if (type(g) is not list or not 1 <= len(g) <= 30 or type(g[0]) is not list or
        not 1 <= len(g[0]) <= 30 or any(type(row) is not list or len(row) != len(g[0]) or
        any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in g)):
        raise ValueError('expected exact-integer rectangular ARC grid bounded by 30')


def parse(g, diagonal=False):
    """Read the top-left green L frame and 4-connected mixed-color panels."""
    grid_check(g)
    h, w = len(g), len(g[0])
    fh = next((r for r in range(h) if g[r][0] == 3), None)
    fw = next((c for c in range(w) if g[0][c] == 3), None)
    if (fh is None or fw is None or fh < 1 or fw < 1 or
        any(g[fh][c] != 3 for c in range(fw+1)) or
        any(g[r][fw] != 3 for r in range(fh+1))):
        raise ValueError('complete top-left green L frame required')
    key_counts = Counter(g[r][c] for r in range(fh) for c in range(fw) if g[r][c] != 7)
    if not key_counts or any(v not in COLORS for v in key_counts):
        raise ValueError('key cells must be palette markers or orange background')
    keys = set(key_counts)
    free = {(r, c) for r in range(h) for c in range(w)
            if not (r <= fh and c <= fw) and g[r][c] != 7}
    if any(g[r][c] == 3 for r, c in free):
        raise ValueError('green is reserved for the key frame')
    panels = []
    while free:
        start = min(free); free.remove(start); cells = {start}; queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in (D8 if diagonal else D4):
                q = (r+dr, c+dc)
                if q in free:
                    free.remove(q); cells.add(q); queue.append(q)
        palette = Counter(g[r][c] for r, c in cells if g[r][c] != 0)
        panels.append({'cells': sorted(cells), 'counts': palette,
                       'colors': set(palette), 'area': len(cells)})
    if not panels:
        raise ValueError('at least one non-orange panel required')
    seeds = [i for i, p in enumerate(panels) if keys <= p['colors']]
    return {'keys': keys, 'key_counts': key_counts, 'frame': (fh, fw),
            'panels': panels, 'seeds': seeds}


def cascade(cert, *, one_wave=False, global_palette=False, include_keys=False):
    keys, panels = cert['keys'], cert['panels']
    selected = set(cert['seeds']); waves = [sorted(selected)]
    palettes = [p['colors'] - (set() if include_keys else keys) for p in panels]
    while True:
        active = set().union(*(palettes[i] for i in (range(len(panels)) if global_palette else selected)))
        added = {i for i, palette in enumerate(palettes) if palette & active} - selected
        if not added:
            break
        selected |= added; waves.append(sorted(added))
        if one_wave:
            break
    return selected, waves


def predict(g, policy='matching'):
    if policy not in POLICIES:
        raise ValueError('unknown rule policy')
    cert = parse(g, diagonal=policy in ('eight_connected', 'cascade_eight'))
    keys, panels = cert['keys'], cert['panels']; selected = set(cert['seeds'])
    if policy == 'identity':
        selected = set()
    elif policy == 'any_key':
        selected = {i for i, p in enumerate(panels) if keys & p['colors']}
    elif policy == 'exact_palette':
        selected = {i for i, p in enumerate(panels) if keys == p['colors']}
    elif policy == 'nonzero_count':
        selected = {i for i, p in enumerate(panels) if sum(p['counts'].values()) >= len(keys)}
    elif policy in ('largest', 'smallest'):
        target = (max if policy == 'largest' else min)(p['area'] for p in panels)
        selected = {i for i, p in enumerate(panels) if p['area'] == target}
    elif policy == 'two_best_keycounts':
        selected = set(sorted(range(len(panels)), key=lambda i: (-len(keys & panels[i]['colors']), i))[:2])
    elif policy == 'first':
        selected = set(sorted(selected)[:1])
    elif policy == 'fixed_three':
        selected = {i for i, p in enumerate(panels) if len(keys & p['colors']) >= 3}
    elif policy == 'key_multiplicity':
        selected = {i for i, p in enumerate(panels)
                    if all(p['counts'][k] >= n for k, n in cert['key_counts'].items())}
    elif policy == 'erase_all':
        selected = set(range(len(panels)))
    elif policy in ('palette_cascade', 'cascade_eight', 'one_wave', 'global_palette', 'include_key_colors'):
        selected, _ = cascade(cert, one_wave=policy == 'one_wave', global_palette=policy == 'global_palette',
                              include_keys=policy == 'include_key_colors')
    out = deepcopy(g)
    for i in selected:
        for r, c in panels[i]['cells']:
            if policy != 'erase_marks_only' or g[r][c] != 0:
                out[r][c] = 7
    return out


def _bands(n):
    sizes = [(n-4)//3 + (i < (n-4) % 3) for i in range(3)]
    out = []; start = 0
    for size in sizes:
        out.append((start, start+size)); start += size+2
    return out


def _scene(seed, index):
    rng = random.Random(f'd59b0160:geometry:{seed}:{index}')
    large = index == 9
    h, w = (30, 30) if large else (rng.randrange(16, 29), rng.randrange(16, 29))
    if index == 6:
        h, w = 16, 16
    g = [[7]*w for _ in range(h)]
    colors = list(COLORS); rng.shuffle(colors)
    nkeys = (3, 2, 4, 2, 3, 4, 2, 3, 4, 3)[index]
    keys, extras = colors[:nkeys], colors[nkeys:]
    x, y, z = extras[:3]; disconnected = extras[-1]
    # Four non-key colors allow a three-hop path. With four key colors,
    # keep a two-hop path and reserve the third non-key color for a decoy.
    if nkeys == 4:
        z = y
    palettes = [keys+[x], keys[:-1]+[x,y], keys[1:2]+[y,z], keys[-1:]+[z],
                keys[:-1]+[disconnected], list(keys), [], [keys[0]]]
    roots = (2,1,3,2,1,3,1,3,2,2)[index]
    if roots == 1:
        palettes[0] = keys[:-1]+[x]
        palettes[5] = keys+[x]
    elif roots == 3:
        palettes[7] = list(keys)
    for c in range(4):
        g[3][c] = 3
    for r in range(4):
        g[r][3] = 3
    key_spots = [(r, c) for r in range(3) for c in range(3)]; rng.shuffle(key_spots)
    for (r, c), color in zip(key_spots, keys+[keys[0], keys[-1]]):
        g[r][c] = color
    row_bands, col_bands = _bands(h), _bands(w)
    slots = [(r, c) for r in range(3) for c in range(3) if (r,c) != (0,0)]
    # The pure complete-key panel has space for a diagonally touching island.
    pure_slot = rng.choice([s for s in slots if s[0] > 0 and s[1] > 0]); slots.remove(pure_slot)
    rng.shuffle(slots); placement = slots[:5]+[pure_slot]+slots[5:]
    bounds = []
    for role, (sr, sc) in enumerate(placement):
        rlo, rhi = row_bands[sr]; clo, chi = col_bands[sc]
        ph = rhi-rlo if large else rng.randrange(3, rhi-rlo+1)
        pw = chi-clo if large else rng.randrange(3, chi-clo+1)
        r0 = rng.randrange(rlo, rhi-ph+1); c0 = rng.randrange(clo, chi-pw+1)
        cells = [(r,c) for r in range(r0,r0+ph) for c in range(c0,c0+pw)]
        # An L-notch varies topology without fragmenting a component.
        if role != 5 and (index+role) % 3 == 0:
            cells.remove((r0+ph-1,c0+pw-1))
        for r,c in cells:
            g[r][c] = 0
        rng.shuffle(cells)
        values = list(dict.fromkeys(palettes[role]))
        if role == 7 and roots != 3:
            values = [keys[0]]*(nkeys+2)
        elif role not in (5,6) and index % 2:
            values += rng.choices(values,k=min(3,len(cells)-len(values)))
        for (r,c),color in zip(cells,values):
            g[r][c] = color
        bounds.append((r0,c0,ph,pw))
    r0,c0,_,_ = bounds[5]
    assert g[r0-1][c0-1] == 7
    g[r0-1][c0-1] = keys[0]
    cert = parse(g)
    selected, waves = cascade(cert)
    assert len(cert['seeds']) == roots and len(waves) >= 3
    return g, {'profile':index,'keys':list(keys),'propagation_waves':waves,
               'panel_count':len(cert['panels']),'large':large,
               'erased_canonical':len(cert['seeds']),'erased_cascade':len(selected)}


@lru_cache(maxsize=32)
def _cached_bank(seed):
    return [_scene(seed,i) for i in range(10)]


def bank(seed):
    """Return detached data so callers cannot poison deterministic cached scenes."""
    return deepcopy(_cached_bank(seed))
