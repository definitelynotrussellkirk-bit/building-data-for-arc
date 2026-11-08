"""Count objects, then route histogram columns by an episode-fixed rule.

Python labels are claims until a protected Racket worker re-executes them.
The CLI writes examples only after that execution. No production rule is edited.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import (find_root, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)

TASK_ID = 'c2cd365ed4fa'
COLORS = (5, 2, 8, 9, 6)
MODES = ('fixed', 'count_ascending')
HOME = Path(__file__).resolve().parent


@lru_cache(maxsize=1)
def base():
    return load_selected_generator(TASK_ID, root=find_root(__file__))[0]


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {'column_order'}
            or type(settings['column_order']) is not str
            or settings['column_order'] not in MODES):
        raise ValueError('settings must contain only column_order: fixed or count_ascending')
    return settings['column_order']


def program(settings):
    mode = _mode(settings)
    if mode == 'fixed':
        return HOME.joinpath('canonical.rkt').read_text(encoding='utf-8')
    return '''(rule! (lambda (g)
  (let* ((colors (list 5 2 8 9 6))
         (counts (map (lambda (c)
           (list c (length (objects-8 (cellmap g (r cc v) (if (= v c) c 7)) 7)))) colors))
         (ordered (sort-by counts second))
         (height (max-of second counts)))
    (reduce (lambda (out col)
      (let* ((entry (list-ref ordered col)) (color (first entry)) (n (second entry)))
        (reduce (lambda (acc i) (set-cell acc (- (- height 1) i) col color))
                out (range 0 n))))
      (empty-grid height 5 7) (range 0 5)))))'''


def analyze(grid):
    """Independent per-color segmentation; area is deliberately not a count."""
    counts = {c: len(base()._components(grid, c, diagonal=True)) for c in COLORS}
    four = {c: len(base()._components(grid, c, diagonal=False)) for c in COLORS}
    pixels = {c: sum(row.count(c) for row in grid) for c in COLORS}
    first_seen = {c: len(grid) * len(grid[0]) for c in COLORS}
    for r, row in enumerate(grid):
        for col, value in enumerate(row):
            if value in first_seen:
                first_seen[value] = min(first_seen[value], r * len(row) + col)
    return {'counts': counts, 'four': four, 'pixels': pixels, 'first_seen': first_seen}


def _order(counts, mode):
    return list(COLORS) if mode == 'fixed' else sorted(COLORS, key=counts.__getitem__)


def _render(counts, order, *, top=False):
    height = max(counts.values())
    if height < 1:
        raise ValueError('at least one active component is required')
    return [[c if (r < counts[c] if top else r >= height - counts[c]) else 7
             for c in order] for r in range(height)]


def predict(grid, mode):
    data = analyze(grid)
    return _render(data['counts'], _order(data['counts'], mode))


def rival_predictions(grid, mode):
    """Finite, declared shortcut family. This is not a uniqueness proof."""
    data = analyze(grid)
    counts = data['counts']
    order = _order(counts, mode)
    out = {
        'four_connected': _render(data['four'], _order(data['four'], mode)),
        'pixel_count': _render(data['pixels'], _order(data['pixels'], mode)),
        'presence': _render({c: int(counts[c] > 0) for c in COLORS}, order),
        'other_setting': _render(counts, _order(counts, MODES[mode == 'fixed'])),
        'descending': _render(counts, sorted(COLORS, key=lambda c: -counts[c])),
        'drop_absent': _render(counts, [c for c in order if counts[c]]),
        'top_aligned': _render(counts, order, top=True),
    }
    compacted = _render(counts, [c for c in order if counts[c]])
    out['compact_pad_right'] = [row + [7] * (5 - len(row)) for row in compacted]
    for cap in range(1, 6):
        clipped = {c: min(cap, counts[c]) for c in COLORS}
        out[f'count_cap_{cap}'] = _render(clipped, _order(clipped, mode))
    if mode == 'count_ascending':
        out.update({
            'tie_numeric': _render(counts, sorted(COLORS, key=lambda c: (counts[c], c))),
            'tie_reverse': _render(counts, sorted(COLORS, key=lambda c: (counts[c], -COLORS.index(c)))),
            'tie_encounter': _render(counts, sorted(COLORS, key=lambda c: (counts[c], data['first_seen'][c]))),
            'pixel_order': _render(counts, sorted(COLORS, key=data['pixels'].__getitem__)),
            'four_connected_order': _render(counts, sorted(COLORS, key=data['four'].__getitem__)),
        })
    else:
        out['numeric_columns'] = _render(counts, sorted(COLORS))
    return out


def teaching_check(episode, mode):
    demos, queries = episode['train'], episode['test']
    rivals = [rival_predictions(pair['input'], mode) for pair in demos]
    survivors = [name for name in rivals[0]
                 if all(p['output'] == predictions[name] for p, predictions in zip(demos, rivals))]
    query_rivals = [rival_predictions(pair['input'], mode) for pair in queries]
    harmful = [name for name in survivors
               if any(p['output'] != predictions[name] for p, predictions in zip(queries, query_rivals))]
    settings = [s for s in MODES if all(predict(p['input'], s) == p['output'] for p in demos)]
    return {'setting_survivors': settings, 'rivals': list(rivals[0]),
            'demo_survivors': survivors, 'query_changing_survivors': harmful,
            'scope': 'Only the named finite rivals; no universal uniqueness claim.'}


def _rng(seed, tag):
    digest = hashlib.sha256(f'{TASK_ID}/histogram-v1/{seed}/{tag}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def _scatter(height, width, specs, rng):
    """Bounded irregular placement; first four objects touch different borders."""
    grid = [[7] * width for _ in range(height)]
    occupied = {c: set() for c in COLORS}
    for index, spec in enumerate(sorted(specs, key=lambda item: item.size, reverse=True)):
        shape = (base()._diagonal_shape(spec.size, rng) if spec.diagonal_only_join
                 else base()._connected_shape(spec.size, rng))
        sh = max(r for r, _ in shape) + 1
        sw = max(c for _, c in shape) + 1
        offsets = [(r, c) for r in range(height - sh + 1) for c in range(width - sw + 1)]
        if index < 4:
            offsets = [(r, c) for r, c in offsets if
                       (r == 0, r == height - sh, c == 0, c == width - sw)[index]]
        rng.shuffle(offsets)
        for r, c in offsets:
            cells = {(r + dr, c + dc) for dr, dc in shape}
            if any(grid[y][x] != 7 for y, x in cells) or base()._touches(cells, occupied[spec.color]):
                continue
            for y, x in cells:
                grid[y][x] = spec.color
            occupied[spec.color].update(cells)
            break
        else:
            return None
    return grid


def _scene(seed, tag, height, width, values, *, dense=False, diagonal=True):
    rng = _rng(seed, tag)
    counts = list(values)
    rng.shuffle(counts)
    colors = [c for c, n in zip(COLORS, counts) if n]
    diagonal_color = rng.choice(colors)
    # Size is sampled per component, independently of the color's object count.
    specs = []
    for color, count in zip(COLORS, counts):
        for i in range(count):
            witness = diagonal and color == diagonal_color and i == 0
            size = rng.randint(8, 16) if dense else rng.randint(1, 6)
            if witness:
                size = 12 if dense else 6
            specs.append(base()._ComponentSpec(color, size, witness))
    # Keep size variation and a singleton even in the large, dense case.
    ordinary = [i for i, s in enumerate(specs) if not s.diagonal_only_join]
    i = rng.choice(ordinary)
    specs[i] = base()._ComponentSpec(specs[i].color, 1, False)
    if dense and sum(s.size for s in specs) < 150:
        raise AssertionError('dense construction must contain substantive content')
    for attempt in range(64):
        grid = _scatter(height, width, specs, _rng(seed, f'{tag}/placement/{attempt}'))
        if grid is not None:
            observed = analyze(grid)
            if list(observed['counts'].values()) != counts:
                raise AssertionError('placement merged or lost an object')
            return grid
    raise ValueError(f'bounded scene placement exhausted: {height}x{width}, {tag}')


def _demonstrations(seed):
    # Selection uses demonstrations only, and checks BOTH settings. Query count,
    # query labels, and private mode cannot affect the chosen visible inputs.
    for attempt in range(48):
        rng = _rng(seed, f'demo-sizes/{attempt}')
        grids = [
            _scene(seed, f'demo0/{attempt}', rng.randint(18, 24), rng.randint(18, 24),
                   [6, 2, 2, 3, 1], diagonal=True),
            _scene(seed, f'demo1/{attempt}', rng.randint(18, 24), rng.randint(18, 24),
                   [0, 3, 5, 5, 1], diagonal=True),
        ]
        valid = True
        for mode in MODES:
            targets = [predict(grid, mode) for grid in grids]
            rivals = [rival_predictions(grid, mode) for grid in grids]
            if any(all(target == row[name] for target, row in zip(targets, rivals))
                   for name in rivals[0]):
                valid = False
                break
        if valid:
            return grids, attempt + 1
    raise ValueError('bounded distinguishing demonstration construction exhausted')


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, 'seed')
    _integer(demos, 2, 6, 'demos')
    _integer(queries, 1, 8, 'queries')
    train_inputs, attempts = _demonstrations(seed)
    for i in range(2, demos):
        rng = _rng(seed, f'extra-demo-size/{i}')
        train_inputs.append(_scene(seed, f'extra-demo/{i}', rng.randint(16, 26),
                                   rng.randint(16, 26), [0, 1, 2, 4, 6], diagonal=bool(i % 2)))
    query_inputs = []
    for i in range(queries):
        if i == 0:
            h, w, values, dense = 10, 10, [6, 2, 1, 0, 0], False
        elif i == 1:
            h, w, values, dense = 30, 30, [6, 5, 4, 3, 2], True
        elif i in (2, 3):
            h, w = (10, 30) if i == 2 else (30, 10)
            values, dense = [0, 6, 4, 3, 2], False
        else:
            rng = _rng(seed, f'query-size/{i}')
            h, w, values, dense = rng.randint(14, 30), rng.randint(14, 30), [1, 2, 3, 4, 6], False
        query_inputs.append(_scene(seed, f'query/{i}', h, w, values, dense=dense, diagonal=i != 3))
    inputs = train_inputs + query_inputs
    if len({json.dumps(grid) for grid in inputs}) != len(inputs):
        raise ValueError('duplicate input: no short or repeated episode is emitted')
    def labeled(grids):
        return [{'input': grid, 'output': predict(grid, mode)} for grid in grids]
    return {'train': labeled(train_inputs), 'test': labeled(query_inputs),
            'program_solution': program(settings), 'settings': dict(settings), 'seed': seed,
            'sampling': {'demonstration_attempts': attempts}}


def public_id(episode):
    return public_challenge_id(episode)


def turn_bytes(episode, query_index):
    """Existing consumer projection: exactly one query, with no count hint."""
    _integer(query_index, 0, len(episode['test']) - 1, 'query_index')
    return public_challenge_bytes({'train': episode['train'], 'test': [episode['test'][query_index]]})


def write_examples(destination, episodes):
    """Protected execution first; public IDs depend on exact visible bytes only."""
    from arcpuzzles.parametric_worker import _real_evaluator
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    rows = deepcopy(list(episodes))
    if not rows:
        raise ValueError('at least one episode is required')
    apply, identity, bridge = _real_evaluator(find_root(__file__) / 'shared/runtime')
    try:
        for episode in rows:
            if episode['program_solution'] != program(episode['settings']):
                raise ValueError('episode program/settings mismatch')
            for pair in episode['train'] + episode['test']:
                executed = apply(episode['program_solution'], pair['input'])
                if executed != pair['output']:
                    raise ValueError('claimed label differs from protected Racket')
                pair['output'] = executed
            episode['teaching'] = teaching_check(episode, _mode(episode['settings']))
            if episode['teaching']['query_changing_survivors']:
                raise ValueError('query-changing rival survives demonstrations')
    finally:
        bridge.close()
    by_id = {}
    for episode in rows:
        key = public_id(episode)
        if key in by_id:
            raise ValueError('duplicate visible challenge payload')
        by_id[key] = episode
    (destination / 'public').mkdir(parents=True)
    (destination / 'private').mkdir()
    for key, episode in sorted(by_id.items()):
        (destination / 'public' / f'{key}.json').write_bytes(public_challenge_bytes(episode))
        (destination / 'private' / f'{key}.json').write_text(json.dumps(episode, sort_keys=True) + '\n')
        # Turn bytes are a checked projection, not another controller or trainer.
    manifest = {'task_id': TASK_ID, 'ids': sorted(by_id), 'racket': identity,
                'episodes': len(rows), 'labels': sum(len(e['train']) + len(e['test']) for e in rows),
                'training_admitted': False}
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    return manifest


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--demos', type=int, default=3)
    parser.add_argument('--queries', type=int, default=4)
    args = parser.parse_args()
    episodes = [generate(args.seed, {'column_order': mode}, args.demos, args.queries) for mode in MODES]
    print(json.dumps(write_examples(args.out, episodes), indent=2))


if __name__ == '__main__':
    main()
