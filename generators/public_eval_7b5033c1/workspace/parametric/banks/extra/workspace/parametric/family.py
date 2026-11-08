"""General simple-path linearization and length-addressed run selection.

The canonical rule uses no supplied grids or labels. The authoring grammar is a
unique four-neighbor induced path on a uniquely modal background, length 2..30.
"""
from __future__ import annotations
from collections import Counter

TASK_ID = GENERATOR_ID = 'public_eval_7b5033c1'
VERSION = '1.0.0'
SUMMARY = 'Trace a colored path from its row-major first endpoint into a column.'
DIRECTIONS = ((-1, 0), (0, -1), (0, 1), (1, 0))
FINISHES = ('unroll', 'length_addressed_run')


def validate_grid(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
        or any(type(row) is not list or len(row) != len(grid[0])
               or any(type(v) is not int or not 0 <= v <= 9 for v in row)
               for row in grid)):
        raise ValueError('Expected an ARC integer grid of size 1..30')


def trace(grid):
    """Return the unique path, independently of color boundaries along it."""
    validate_grid(grid)
    counts = Counter(v for row in grid for v in row)
    maximum = max(counts.values())
    modes = [v for v, count in counts.items() if count == maximum]
    if len(modes) != 1:
        raise ValueError('Background must be uniquely modal')
    background = modes[0]
    cells = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v != background}
    if not 2 <= len(cells) <= 30:
        raise ValueError('A path must have 2..30 cells for a lawful column output')
    adjacency = {p: sorted((p[0]+dr, p[1]+dc) for dr, dc in DIRECTIONS
                          if (p[0]+dr, p[1]+dc) in cells) for p in cells}
    endpoints = sorted(p for p in cells if len(adjacency[p]) == 1)
    if len(endpoints) != 2 or any(len(n) not in (1, 2) for n in adjacency.values()):
        raise ValueError('Expected exactly one nonbranching open path')
    path = []
    previous = None
    current = endpoints[0]
    while current is not None:
        if current in path:
            raise ValueError('A cycle is not an open path')
        path.append(current)
        following = [p for p in adjacency[current] if p != previous]
        previous, current = current, following[0] if following else None
    if len(path) != len(cells):
        raise ValueError('Disconnected foreground is not one path')
    return background, path


def split_runs(sequence):
    result = []
    for color in sequence:
        if result and result[-1][0] == color:
            result[-1].append(color)
        else:
            result.append([color])
    return result


def stages(grid, order='path'):
    background, path = trace(grid)
    if order == 'row_major':
        ordered = sorted(path)
    elif order == 'column_major':
        ordered = sorted(path, key=lambda p: (p[1], p[0]))
    elif order == 'reverse':
        ordered = path[::-1]
    elif order in ('path', 'histogram'):
        ordered = path
    else:
        raise ValueError('Unknown sequence order')
    sequence = [grid[r][c] for r, c in ordered]
    if order == 'histogram':
        sequence.sort()
    runs = split_runs(sequence)
    return {'background': background, 'path': [list(p) for p in path],
            'sequence': sequence, 'runs': runs, 'address': len(runs[0])}


def solve(grid, finish='unroll', *, order='path', selector='header', paint='run'):
    if finish not in FINISHES:
        raise ValueError('Unknown finish')
    state = stages(grid, order)
    sequence = state['sequence']
    if finish == 'unroll':
        return [[v] for v in sequence]
    runs = state['runs']
    if selector == 'header':
        address = state['address']
    elif type(selector) is int and selector in (1, 2, 3, 4):
        address = selector
    elif selector == 'largest':
        address = max(range(1, len(runs)), key=lambda i: (len(runs[i]), -i)) if len(runs) > 1 else 0
    elif selector == 'all_header_color':
        address = sequence.count(sequence[0])
    elif selector == 'last':
        address = len(runs)-1
    else:
        raise ValueError('Unknown run selector')
    if paint not in ('run', 'all_matching'):
        raise ValueError('Unknown paint mode')
    selected_color = runs[address][0] if address < len(runs) else None
    return [[9 if (i == address or (paint == 'all_matching' and color == selected_color)) else color]
            for i, run in enumerate(runs) for color in run]


def _integer(value, lower, upper, name):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f'{name} must be an exact integer in {lower}..{upper}')


def _walk(rng, height, width, length):
    """Bounded induced walk: a new cell may touch only its predecessor."""
    for _ in range(80):
        path = [(rng.randrange(height), rng.randrange(width))]
        used = set(path)
        while len(path) < length:
            r, c = path[-1]
            choices = []
            for dr, dc in DIRECTIONS:
                p = (r+dr, c+dc)
                if not (0 <= p[0] < height and 0 <= p[1] < width) or p in used:
                    continue
                if sum((p[0]+vr, p[1]+vc) in used for vr, vc in DIRECTIONS) == 1:
                    choices.append(p)
            if not choices:
                break
            p = rng.choice(choices); path.append(p); used.add(p)
        if len(path) == length:
            return path
    raise ValueError('Induced walk exhausted its bounded construction budget')


def _stress_walk(rng):
    # Exactly 30 cells is the lawful maximum: canonical output is a column.
    # A long folded path, touching two canvas boundaries, tests maximum output,
    # non-row-major traversal, turns and endpoint selection. The sparsity is
    # intrinsic to this source task, not a claim of dense 30x30 coverage.
    down = rng.randint(12, 18)
    up = rng.randint(3, 6)
    across = 29-down-up
    path = [(0, 0)]
    for dr, dc, count in ((1, 0, down), (0, 1, across), (-1, 0, up)):
        for _ in range(count):
            r, c = path[-1]; path.append((r+dr, c+dc))
    if rng.randrange(2):
        path = [(r, -c) for r, c in path]
    for _ in range(rng.randrange(4)):
        path = [(c, -r) for r, c in path]
    r0, c0 = min(r for r, c in path), min(c for r, c in path)
    path = [(r-r0, c-c0) for r, c in path]
    height = max(r for r, c in path)+1
    width = max(c for r, c in path)+1
    top = rng.choice((0, 30-height)); left = rng.choice((0, 30-width))
    return [(r+top, c+left) for r, c in path]


def construct(seed, sample_index, *, stress=False, difficulty=None):
    """Return a fresh grid and an independent constructor oracle, kept private."""
    import hashlib
    import random
    _integer(seed, 0, 2**63-1, 'seed')
    _integer(sample_index, 0, 2**63-1, 'sample_index')
    if type(stress) is not bool:
        raise ValueError('stress must be an exact boolean')
    if difficulty not in (None, 'easy', 'medium', 'hard'):
        raise ValueError('Unsupported difficulty')
    entropy = hashlib.sha256(f'{TASK_ID}:{VERSION}:{seed}:{sample_index}:{difficulty}:{stress}'.encode()).digest()
    rng = random.Random(int.from_bytes(entropy, 'big'))
    # Any consecutive two demos teach different input-derived addresses.
    address = 2 + (seed+sample_index) % 3
    for attempt in range(128):
        number = address+4+rng.randrange(2)
        lengths = [rng.randint(1, 4) for _ in range(number)]
        lengths[0] = address
        lengths[address] = rng.choice((2, 3))
        others = [i for i in range(1, number) if i != address]
        large, small = rng.sample(others, 2)
        lengths[large] = rng.choice((5, 6)); lengths[small] = 1
        while sum(lengths) > 30:
            options = [i for i in others if i not in (large, small) and lengths[i] > 1]
            if not options:
                raise ValueError('Run budget construction is infeasible')
            lengths[rng.choice(options)] -= 1
        target = 30 if stress else max(18, sum(lengths))
        while sum(lengths) < target:
            lengths[rng.choice([i for i in others if i != small])] += 1
        background = rng.randrange(9)
        palette = rng.sample([c for c in range(9) if c != background], rng.choice((4, 5, 6)))
        header_color = rng.choice(palette)
        selected_color = rng.choice([c for c in palette if c != header_color])
        # A second occurrence of the header color defeats total-color-count
        # addressing. Vary its position instead of making it always terminal.
        header_return = rng.choice((address+1, number-1))
        required = {0: header_color, address: selected_color,
                    address+2: selected_color, header_return: header_color}
        colors = []
        for i in range(number):
            if i in required:
                color = required[i]
            else:
                color = rng.choice([c for c in palette
                                    if (not colors or c != colors[-1])
                                    and c != required.get(i+1)])
            colors.append(color)
        sequence = [color for color, length in zip(colors, lengths) for _ in range(length)]
        if stress:
            height = width = 30; path = _stress_walk(rng)
        else:
            dimensions = ((10, 12), (12, 16), (16, 16), (18, 24), (24, 30))
            height, width = rng.choice(dimensions)
            if rng.randrange(2): height, width = width, height
            path = _walk(rng, height, width, len(sequence))
        if path[-1] < path[0]:
            path.reverse()
        grid = [[background]*width for _ in range(height)]
        for (r, c), color in zip(path, sequence):
            grid[r][c] = color
        # The intended sequence comes from construction, not the solver.
        if solve(grid) != [[c] for c in sequence]:
            raise ValueError('Independent constructor and general trace disagree')
        alternate = solve(grid, 'length_addressed_run')
        if any(solve(grid, order=mode) == [[c] for c in sequence]
               or solve(grid, 'length_addressed_run', order=mode) == alternate
               for mode in ('row_major', 'column_major', 'reverse', 'histogram')):
            continue
        return grid, {'path': [list(p) for p in path], 'sequence': sequence,
                      'run_colors': colors, 'run_lengths': lengths,
                      'selected_run_index': address, 'attempt': attempt,
                      'background': background, 'stress': stress}
    raise ValueError('Exhausted bounded path/order-discrimination construction')


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if set(overrides)-{'stress'}:
        raise ValueError('Only the stress override is supported')
    return construct(seed, sample_index, difficulty=difficulty,
                     stress=overrides.get('stress', False))[0]


def self_check(grid, *, difficulty=None, meta=None):
    try:
        state = stages(grid)
        if 9 in {v for row in grid for v in row}:
            return ['The parametric sampling grammar reserves color 9']
        k = state['address']; runs = state['runs']
        if not 2 <= k <= 4 or k >= len(runs):
            return ['Header length must address a following run']
        if sum(run[0] == runs[k][0] for run in runs) < 2:
            return ['Need a repeated selected color to teach run-local painting']
        return []
    except ValueError as exc:
        return [str(exc)]
