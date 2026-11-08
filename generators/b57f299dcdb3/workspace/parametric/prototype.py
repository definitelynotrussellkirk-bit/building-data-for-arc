"""Dense plus census with a scalar or whole-object readout.

The sampler emits Python label claims. Native qualification/generation executes
and checks every admitted label through the protected Racket worker.
"""
from __future__ import annotations

from collections import Counter
import copy
import hashlib
from pathlib import Path
import random

from puzzle_generators.rule_wrap import strip_rule_wrapper

READOUTS = ('winner_color', 'winner_pluses')
PALETTE = (1, 2, 3, 5, 6, 7, 8, 9)
ARMS = ((-1, 0), (1, 0), (0, -1), (0, 1))
CANONICAL = Path(__file__).with_name('canonical.rkt').read_text(encoding='utf-8')
CANONICAL_CALLABLE = strip_rule_wrapper(CANONICAL)


def _setting(settings):
    if (type(settings) is not dict or set(settings) != {'readout'}
            or type(settings['readout']) is not str or settings['readout'] not in READOUTS):
        raise ValueError('settings must contain exactly readout=winner_color|winner_pluses')
    return settings['readout']


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')


def _rng(seed, stream):
    digest = hashlib.sha256(f'b57f299dcdb3-v1:{seed}:{stream}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def analyze(grid):
    if (type(grid) is not list or not 1 <= len(grid) <= 30
            or type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(x) is not int or not 0 <= x <= 9 for x in row) for row in grid)):
        raise ValueError('expected a rectangular integer ARC grid')
    frequencies = Counter(x for row in grid for x in row)
    top = max(frequencies.values())
    modes = [color for color, n in frequencies.items() if n == top]
    if len(modes) != 1 or modes[0] in (0, 4):
        raise ValueError('the admitted grammar requires a unique nonzero, non-yellow background')
    background = modes[0]
    centers = []
    for row in range(1, len(grid)-1):
        for col in range(1, len(grid[0])-1):
            petals = [grid[row+dr][col+dc] for dr, dc in ARMS]
            # Match the canonical detector exactly; emitted petals exclude 4.
            if grid[row][col] == 4 and len(set(petals)) == 1 and petals[0] not in (0, background):
                centers.append((row, col, petals[0]))
    counts = Counter(color for _, _, color in centers)
    if not counts:
        winner = 0
    else:
        high = max(counts.values())
        winners = [color for color, count in counts.items() if count == high]
        if len(winners) != 1:
            raise ValueError('the admitted grammar requires a unique plus-census winner')
        winner = winners[0]
    return {'background': background, 'centers': centers, 'counts': dict(counts), 'winner': winner}


def mask_for_colors(grid, centers, colors):
    result = [[0] * len(grid[0]) for _ in grid]
    for row, col, color in centers:
        if color in colors:
            result[row][col] = grid[row][col]
            for dr, dc in ARMS:
                result[row+dr][col+dc] = grid[row+dr][col+dc]
    return result


def solve_python(grid, settings):
    readout = _setting(settings)
    info = analyze(grid)
    if readout == 'winner_color':
        return [[info['winner']]]
    return mask_for_colors(grid, info['centers'], {info['winner']})


def mask_program(winner_expression):
    """Standalone Racket projection, also used for an explicit wrong-census witness."""
    return f'''(rule! (lambda (g)
      (let* ((bg (mode g))
             (winner {winner_expression})
             (selected
               (for*/list ((r (range 1 (- (rows g) 1)))
                           (c (range 1 (- (cols g) 1)))
                 #:when (and (= (at g r c) 4) (!= winner 0) (!= winner bg)
                             (= (at g (- r 1) c) winner)
                             (= (at g (+ r 1) c) winner)
                             (= (at g r (- c 1)) winner)
                             (= (at g r (+ c 1)) winner)))
                 (list r c))))
        (build-grid (rows g) (cols g) (r c)
          (if (for/or ((p selected))
                (<= (+ (abs (- r (first p))) (abs (- c (second p)))) 1))
              (at g r c) 0)))))'''


def program(settings):
    readout = _setting(settings)
    if readout == 'winner_color':
        return CANONICAL
    return mask_program(f'(at ({CANONICAL_CALLABLE} g) 0 0)')


def _axis_positions(side):
    values = list(range(1, side-1, 3))
    if values[-1] != side-2:
        if side-2-values[-1] >= 3:
            values.append(side-2)
        else:
            values[-1] = side-2
    return values


def _scene(rng, height, width, labels, *, boundary=False):
    colors = rng.sample(PALETTE, max(labels)+2)
    background, petal_colors = colors[0], colors[1:]
    counts = Counter(labels)
    winner_role = max(counts, key=counts.get)
    bad_role = max(labels)
    bad_color = petal_colors[bad_role]
    invalid_count = max(counts.values()) + 2
    false_count = max(counts.values())
    slots = [(r,c) for r in _axis_positions(height) for c in _axis_positions(width)]
    needed = len(labels) + invalid_count + false_count
    if needed > len(slots):
        raise ValueError('the requested motif count does not fit the canvas')
    if boundary:
        corners = [(1,1), (height-2,width-2)]
        chosen = corners + rng.sample([p for p in slots if p not in corners], needed-2)
    else:
        chosen = rng.sample(slots, needed)
    valid_positions = sorted(chosen[:len(labels)])
    labels = list(labels)
    if boundary:
        for position in ((1,1), (height-2,width-2)):
            index = valid_positions.index(position)
            if labels[index] != winner_role:
                donor = next(i for i, role in enumerate(labels)
                             if role == winner_role and valid_positions[i] not in ((1,1), (height-2,width-2)))
                labels[index], labels[donor] = labels[donor], labels[index]
    grid = [[0 if rng.random() < .23 else background for _ in range(width)] for _ in range(height)]
    protected = set()

    def paint(position, marker, petals):
        r,c = position
        grid[r][c] = marker
        protected.add((r,c))
        for (dr,dc), color in zip(ARMS, petals):
            grid[r+dr][c+dc] = color
            protected.add((r+dr,c+dc))

    for position, role in zip(valid_positions, labels):
        paint(position, 4, [petal_colors[role]]*4)
    offset = len(labels)
    for i, position in enumerate(chosen[offset:offset+invalid_count]):
        # Most invalid candidates suggest the wrong color even to a 3-arm
        # detector. One uses the true winner to test full-object masking.
        color = petal_colors[winner_role] if i == invalid_count-1 else bad_color
        petals = [color]*4
        petals[3] = 0 if i % 2 else background
        paint(position, 4, petals)
    for position in chosen[offset+invalid_count:]:
        paint(position, background, [bad_color]*4)
    free = [(r,c) for r in range(height) for c in range(width) if (r,c) not in protected]
    rng.shuffle(free)
    noise = [petal_colors[0]]*2 + [petal_colors[1]]*2 + [bad_color]*8
    noise += [rng.choice(petal_colors) for _ in range((height*width)//60)]
    for position, color in zip(free, noise):
        r,c = position
        grid[r][c] = color
    # Keep the background uniquely recoverable without altering any motif.
    frequency = Counter(x for row in grid for x in row)
    competitor = max(n for color,n in frequency.items() if color != background)
    for r,c in free[len(noise):]:
        if frequency[background] > competitor:
            break
        if grid[r][c] == 0:
            grid[r][c] = background
            frequency[background] += 1
    info = analyze(grid)
    expected = Counter(petal_colors[role] for role in labels)
    if info['counts'] != dict(expected):
        raise RuntimeError('constructed census differs from requested census')
    if info['background'] != background:
        raise RuntimeError('constructed field background was not recovered')
    return grid, {'positions': valid_positions, 'labels': labels, 'colors': petal_colors}


def sample_input(seed, *, height=20, width=22, counts=(3,2,1), boundary=False):
    """Explicit parametric size probe; this is not a production override."""
    _integer(seed, 0, 2**63-1, 'seed')
    _integer(height, 12, 30, 'height')
    _integer(width, 12, 30, 'width')
    if (type(counts) not in (tuple,list) or not 3 <= len(counts) <= 4
            or any(type(n) is not int or not 1 <= n <= 4 for n in counts)
            or counts[0] <= max(counts[1:]) or sum(counts) > 10):
        raise ValueError('counts need 3..4 positive groups, unique first maximum, at most ten pluses')
    labels = [i for i,n in enumerate(counts) for _ in range(n)]
    rng = _rng(seed, f'scene:{height}:{width}:{tuple(counts)}:{boundary}')
    rng.shuffle(labels)
    return _scene(rng, height, width, labels, boundary=boundary)[0]


def teaching_inputs(seed):
    rng = _rng(seed, 'teaching')
    height, width = rng.choice(((12,12), (15,18), (18,15), (20,22)))
    first, meta = _scene(rng, height, width, [1,1,0,2,0,0])
    second = copy.deepcopy(first)
    row, col = meta['positions'][2]
    for dr, dc in ARMS:
        second[row+dr][col+dc] = meta['colors'][1]
    if analyze(first)['winner'] == analyze(second)['winner']:
        raise RuntimeError('the teaching intervention must change the census winner')
    return [first, second]


def generate(seed, settings, demos, queries):
    _integer(seed, 0, 2**63-1, 'seed')
    _integer(demos, 2, 6, 'demos')
    _integer(queries, 1, 4, 'queries')
    _setting(settings)
    train = teaching_inputs(seed)
    for index in range(2, demos):
        rng = _rng(seed, f'demo:{index}')
        h,w = rng.choice(((16,20), (20,22), (24,18)))
        counts = rng.choice(((2,1,1), (3,2,1), (4,3,1)))
        train.append(sample_input(rng.randrange(2**63), height=h, width=w, counts=counts))
    test = []
    profiles = ((16,20,(2,1,1)), (20,22,(3,2,1)), (24,28,(4,3,1)), (30,30,(4,3,2,1)))
    for index, (h,w,counts) in enumerate(profiles[:queries]):
        rng = _rng(seed, f'query:{index}')
        if index < 3 and rng.randrange(2):
            h,w = w,h
        test.append(sample_input(rng.randrange(2**63), height=h, width=w,
                                 counts=counts, boundary=index==3))
    return {'train': [{'input': g, 'output': solve_python(g,settings)} for g in train],
            'test': [{'input': g, 'output': solve_python(g,settings)} for g in test],
            'program_solution': program(settings)}
