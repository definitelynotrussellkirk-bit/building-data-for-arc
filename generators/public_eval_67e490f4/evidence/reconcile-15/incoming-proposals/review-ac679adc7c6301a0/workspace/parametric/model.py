"""Shape-class vote transfer for public parent 67e490f4.

The input contains one large, full-border monochrome template whose background
holes are shape slots.  Same-color components outside the template are votes:
components are grouped with slots up to the eight square symmetries.  The
canonical rule fills every slot with the modal component color in its class.
The alternate rule uses the unique rarest color.  Fresh scenes are constructive
and never read official ARC data.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json
import random

HERE = Path(__file__).resolve().parent
SETTINGS = ('modal', 'rarest')


def strict_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30 or type(grid[0]) is not list
            or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError('expected a rectangular 1..30 grid of exact integer colors 0..9')
    return [row[:] for row in grid]


def _components_by(grid, predicate):
    h, w = len(grid), len(grid[0]); seen = set(); result = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or not predicate(r, c):
                continue
            stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                a, b = stack.pop(); cells.append((a, b))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (a + dr, b + dc)
                    if (0 <= q[0] < h and 0 <= q[1] < w and q not in seen
                            and predicate(*q)):
                        seen.add(q); stack.append(q)
            result.append(sorted(cells))
    return result


def components(grid, background):
    found = []
    for color in range(10):
        if color == background:
            continue
        for cells in _components_by(grid, lambda r, c, color=color: grid[r][c] == color):
            found.append({'color': color, 'cells': cells})
    return found


def bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def norm(cells):
    cells = list(cells)
    r0, c0, _, _ = bbox(cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def transform_shape(cells, rotation=0, reflection=False):
    points = list(norm(cells))
    if reflection:
        points = [(r, -c) for r, c in points]
    for _ in range(rotation % 4):
        points = [(c, -r) for r, c in points]
    return norm(points)


def canonical(cells):
    return min(transform_shape(cells, k, flip) for k in range(4) for flip in (False, True))


def rotation_canonical(cells):
    return min(transform_shape(cells, k, False) for k in range(4))


def _background(grid):
    counts = Counter(v for row in grid for v in row)
    return min(counts, key=lambda color: (-counts[color], color))


def analyze(grid):
    grid = strict_grid(grid); bg = _background(grid); objs = components(grid, bg)
    if not objs:
        raise ValueError('expected a perforated template and outside vote pieces')
    max_size = max(len(o['cells']) for o in objs)
    candidates = [o for o in objs if len(o['cells']) == max_size]
    if len(candidates) != 1:
        raise ValueError('expected a unique largest template component')
    template = candidates[0]; base = template['color']; r0, c0, r1, c1 = bbox(template['cells'])
    if r1 - r0 < 2 or c1 - c0 < 2:
        raise ValueError('template must have a nontrivial rectangular crop')
    perimeter = [(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                 if r in (r0, r1) or c in (c0, c1)]
    if not all(grid[r][c] == base for r, c in perimeter):
        raise ValueError('template needs a complete monochrome perimeter')
    crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    if any(v not in (bg, base) for row in crop for v in row):
        raise ValueError('template crop may contain only base and background slots')
    holes = _components_by(crop, lambda r, c: crop[r][c] == bg)
    if not holes:
        raise ValueError('template needs at least one slot')
    # Perforations can isolate small islands of the template color.  They
    # belong to the crop, not to the outside vote population.
    outside = [o for o in objs if o is not template and
               all(not (r0 <= r <= r1 and c0 <= c <= c1) for r, c in o['cells'])]
    shape_votes = defaultdict(Counter)
    for obj in outside:
        shape_votes[canonical(obj['cells'])][obj['color']] += 1
    hole_keys = [canonical(h) for h in holes]
    for key in set(hole_keys):
        votes = shape_votes.get(key)
        if not votes:
            raise ValueError('every slot class needs outside vote pieces')
        if len(votes) < 1:
            raise ValueError('empty vote histogram')
    return {
        'background': bg, 'template_color': base, 'template_bbox': (r0, c0, r1, c1),
        'template': crop, 'holes': holes, 'hole_keys': hole_keys, 'outside': outside,
        'shape_votes': dict(shape_votes),
    }


def _winner(votes, policy):
    if policy == 'modal':
        score = max(votes.values())
    elif policy == 'rarest':
        score = min(votes.values())
    else:
        raise ValueError('unknown vote policy')
    return min(color for color, count in votes.items() if count == score)


def solve(grid, vote_policy='modal'):
    if vote_policy not in SETTINGS:
        raise ValueError('unknown vote policy')
    info = analyze(grid); out = [row[:] for row in info['template']]
    for cells, key in zip(info['holes'], info['hole_keys']):
        color = _winner(info['shape_votes'][key], vote_policy)
        for r, c in cells:
            out[r][c] = color
    return out


def program(settings):
    if (type(settings) is not dict or set(settings) != {'vote_policy'}
            or settings['vote_policy'] not in SETTINGS):
        raise ValueError('settings must name exactly one declared vote_policy')
    source = (HERE / 'canonical.rkt').read_text(encoding='utf-8')
    if settings['vote_policy'] == 'modal':
        return source
    marker = '(define vote-policy "modal")'
    if source.count(marker) != 1:
        raise ValueError('canonical vote-policy marker missing or duplicated')
    return source.replace(marker, '(define vote-policy "rarest")', 1)


def _rng(seed, domain):
    token = hashlib.sha256(f'slot-vote-v1:{seed}:{domain}'.encode()).digest()
    return random.Random(int.from_bytes(token, 'big'))


def _turn(grid, rotation=0, reflection=False):
    out = [row[::-1] if reflection else row[:] for row in grid]
    for _ in range(rotation % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


SHAPES = (
    ((0, 1), (0, 2), (1, 0), (1, 1)),                 # S tetromino (chiral)
    ((0, 0), (0, 1), (0, 2), (1, 1)),                 # T tetromino
    ((0, 0), (1, 0), (1, 1)),                         # L triomino
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),         # V pentomino
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),         # plus pentomino
)


def _place_shape(grid, cells, color, top, left):
    for r, c in cells:
        grid[top + r][left + c] = color


def _free_with_buffer(grid, cells, top, left, background, forbidden):
    h, w = len(grid), len(grid[0]); absolute = {(top + r, left + c) for r, c in cells}
    if any(not (0 <= r < h and 0 <= c < w) or (r, c) in forbidden or grid[r][c] != background
           for r, c in absolute):
        return False
    for r, c in absolute:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (r + dr, c + dc)
            if 0 <= q[0] < h and 0 <= q[1] < w and q not in absolute and grid[q[0]][q[1]] != background:
                return False
    return True


def _hole_placements(shapes, th, tw, rng):
    """Choose two separated oriented holes per class with deterministic backtracking.

    The previous first-fit sampler could paint itself into a corner even though a
    legal packing existed.  Candidate order remains seed-shuffled, but a failed
    suffix now backtracks instead of rejecting a valid scene.
    """
    specs = []
    for class_index, shape in enumerate(shapes):
        for _copy_index in range(2):
            oriented = transform_shape(shape, rng.randrange(4), bool(rng.randrange(2)))
            candidates = []
            anchors = [(r, c) for r in range(2, th - 2) for c in range(2, tw - 2)]
            rng.shuffle(anchors)
            for r, c in anchors:
                cells = frozenset((r + a, c + b) for a, b in oriented)
                if max(a for a, _ in cells) >= th - 1 or max(b for _, b in cells) >= tw - 1:
                    continue
                guard = set(cells)
                for a, b in cells:
                    guard.update(((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)))
                candidates.append((r, c, oriented, cells, frozenset(guard)))
            specs.append((class_index, oriented, candidates))

    # Most-constrained-first reduces the search tree; chosen is restored to the
    # original class/copy order so scene construction stays straightforward.
    order = sorted(range(len(specs)), key=lambda i: (len(specs[i][2]), -len(specs[i][1]), i))
    chosen = [None] * len(specs)

    def search(depth, occupied_guard):
        if depth == len(order):
            return True
        spec_index = order[depth]
        for candidate in specs[spec_index][2]:
            cells = candidate[3]
            if not cells.isdisjoint(occupied_guard):
                continue
            chosen[spec_index] = candidate
            if search(depth + 1, occupied_guard | candidate[4]):
                return True
        chosen[spec_index] = None
        return False

    if not search(0, frozenset()):
        raise AssertionError('constructive template hole placement failed')
    return [(specs[i][0], chosen[i][2], chosen[i][3]) for i in range(len(specs))]


def scene(seed, domain, stress=False):
    rng = _rng(seed, domain); n = 30
    colors = list(range(10)); rng.shuffle(colors)
    bg, base = colors[:2]; palette = colors[2:8]
    # Two same-area classes force real shape matching; a third/fourth adds diversity.
    class_count = 4 if stress or rng.randrange(2) else 3
    shapes = list(SHAPES[:class_count])
    th = 13 + (1 if stress else rng.randrange(2)); tw = 15 + (1 if stress else rng.randrange(2))
    tr, tc = 1, 1
    grid = [[bg] * n for _ in range(n)]
    for r in range(tr, tr + th):
        for c in range(tc, tc + tw):
            grid[r][c] = base
    # Place two differently oriented holes per class. Candidate order is
    # randomized, but backtracking prevents a greedy dead end from rejecting a
    # seed whose template has ample legal space.
    for _class_index, _oriented, cells in _hole_placements(shapes, th, tw, rng):
        for a, b in cells:
            grid[tr + a][tc + b] = bg
    # Vary the three-color ranking by class.  Counts 3/2/1 make both policies unique.
    class_hist = []
    for i in range(class_count):
        ordered = (palette[i % len(palette)], palette[(i + 2) % len(palette)], palette[(i + 4) % len(palette)])
        class_hist.append(((ordered[0], 3), (ordered[1], 2), (ordered[2], 1)))
    forbidden = {(r, c) for r in range(tr - 1, tr + th + 1) for c in range(tc - 1, tc + tw + 1)
                 if 0 <= r < n and 0 <= c < n}
    for class_index, shape in enumerate(shapes):
        copies = []
        for color, count in class_hist[class_index]:
            copies.extend([color] * count)
        rng.shuffle(copies)
        for j, color in enumerate(copies):
            # Class zero is deliberately reflected relative to its holes; rotations-only fails.
            reflection = True if class_index == 0 else bool(rng.randrange(2))
            oriented = transform_shape(shape, rng.randrange(4), reflection)
            h = max(r for r, _ in oriented) + 1; w = max(c for _, c in oriented) + 1
            candidates = [(r, c) for r in range(n - h + 1) for c in range(n - w + 1)]
            rng.shuffle(candidates); placed = False
            for r, c in candidates:
                if _free_with_buffer(grid, oriented, r, c, bg, forbidden):
                    _place_shape(grid, oriented, color, r, c); placed = True; break
            if not placed:
                raise AssertionError('constructive outside-piece placement failed')
    return _turn(grid, rng.randrange(4), bool(rng.randrange(2)))


def generate(seed, settings, demos, queries):
    if type(seed) is not int or isinstance(seed, bool) or not 0 <= seed < 2**63:
        raise ValueError('seed must be a nonnegative 63-bit integer')
    if (type(settings) is not dict or set(settings) != {'vote_policy'}
            or settings['vote_policy'] not in SETTINGS):
        raise ValueError('settings must name exactly one declared vote_policy')
    if type(demos) is not int or isinstance(demos, bool) or not 2 <= demos <= 6:
        raise ValueError('demos must be 2..6')
    if type(queries) is not int or isinstance(queries, bool) or queries != 4:
        raise ValueError('exactly four private queries are required')
    train_grids = [scene(seed, f'demo:{i}', stress=(i == 5)) for i in range(demos)]
    bank = [scene(seed, f'query:{i}', stress=(i == 3)) for i in range(4)]
    _rng(seed, 'presentation').shuffle(bank)
    label = lambda g: {'input': g, 'output': solve(g, settings['vote_policy'])}
    return {'train': [label(g) for g in train_grids], 'test': [label(g) for g in bank],
            'program_solution': program(settings)}


def surviving_settings(episode):
    return [setting for setting in SETTINGS
            if all(solve(pair['input'], setting) == pair['output'] for pair in episode['train'])]


def _solve_with_key(grid, vote_policy, key_fn, area_only=False):
    info = analyze(grid); out = [row[:] for row in info['template']]
    votes = defaultdict(Counter)
    for obj in info['outside']:
        key = len(obj['cells']) if area_only else key_fn(obj['cells'])
        votes[key][obj['color']] += 1
    for cells in info['holes']:
        key = len(cells) if area_only else key_fn(cells)
        if key not in votes:
            continue
        color = _winner(votes[key], vote_policy)
        for r, c in cells:
            out[r][c] = color
    return out


def rival(grid, vote_policy, name):
    if name == 'opposite_setting':
        return solve(grid, SETTINGS[1 - SETTINGS.index(vote_policy)])
    if name == 'no_reflection':
        return _solve_with_key(grid, vote_policy, rotation_canonical)
    if name == 'area_only':
        return _solve_with_key(grid, vote_policy, canonical, area_only=True)
    if name == 'global_vote':
        info = analyze(grid); all_votes = Counter(o['color'] for o in info['outside'])
        color = _winner(all_votes, vote_policy); out = [row[:] for row in info['template']]
        for cells in info['holes']:
            for r, c in cells: out[r][c] = color
        return out
    raise ValueError('unknown rival')


def public_view(episode, query_index=0):
    if type(query_index) is not int or not 0 <= query_index < len(episode['test']):
        raise ValueError('invalid query index')
    visible = {
        'train': [{'input': strict_grid(p['input']), 'output': strict_grid(p['output'])}
                  for p in episode['train']],
        'test': [{'input': strict_grid(episode['test'][query_index]['input'])}],
    }
    return (json.dumps(visible, sort_keys=True, separators=(',', ':')) + '\n').encode()


def dependency():
    return {
        'step_a': 'Normalize every outside component and template slot under D4, then build the per-shape color histogram.',
        'intermediate': 'A mapping from each slot shape class to exact color vote counts.',
        'step_b': 'Select the modal or rarest color from that class-specific histogram and fill each slot.',
        'why_b_depends_on_a': 'The winning color differs by shape class; a global histogram or a histogram from the wrong class changes the filled template.',
    }
