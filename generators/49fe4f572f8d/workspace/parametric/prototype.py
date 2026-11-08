"""Column gravity, optionally followed by one simultaneous clear and re-settle.

Python labels are claims until the protected Racket runtime re-executes them.
The exporter performs that execution before writing any public examples.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = '49fe4f572f8d'
MODES = ('down', 'settle_clear_once')
HOME = Path(__file__).resolve().parent


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in {low}..{high}')
    return value


def _mode(settings):
    if (type(settings) is not dict or set(settings) != {'mode'}
            or type(settings['mode']) is not str or settings['mode'] not in MODES):
        raise ValueError('settings must contain only mode: down or settle_clear_once')
    return settings['mode']


def program(settings):
    if _mode(settings) == 'down':
        return HOME.joinpath('canonical.rkt').read_text(encoding='utf-8')
    return '''(rule! (lambda (g)
  (let* ((settled (gravity g "down"))
         (targets (filter (lambda (o) (>= (obj-size o) 3)) (objects settled 0)))
         (cleared (erase-cells settled (flatmap obj-cells targets) 0)))
    (gravity cleared "down"))))'''


def _gravity(grid, variant='down'):
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for col in range(width):
        if variant == 'freeze_bottom_supported_columns' and grid[-1][col]:
            for row in range(height):
                out[row][col] = grid[row][col]
            continue
        values = [row[col] for row in grid if row[col]]
        if variant == 'reverse_column_order':
            values.reverse()
        if variant == 'cap_three_cells_per_column':
            values = values[:3]
        for row, value in enumerate(values, height - len(values)):
            out[row][col] = value
    return out


def _components(grid, diagonal=False):
    """Same-color components, in row-major first-cell order."""
    height, width = len(grid), len(grid[0])
    steps = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
             if (dr or dc) and (diagonal or abs(dr) + abs(dc) == 1)]
    seen, groups = set(), []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if not color or (row, col) in seen:
                continue
            seen.add((row, col))
            cells, pending = [], [(row, col)]
            while pending:
                r, c = pending.pop()
                cells.append((r, c))
                for dr, dc in steps:
                    p = r + dr, c + dc
                    if (0 <= p[0] < height and 0 <= p[1] < width
                            and p not in seen and grid[p[0]][p[1]] == color):
                        seen.add(p)
                        pending.append(p)
            groups.append((color, cells))
    return groups


def _clear(grid, *, threshold=3, diagonal=False, exact=False, whole_colors=False,
           orientation=None, first_only=False):
    groups = [(color, cells) for color, cells in _components(grid, diagonal)
              if (len(cells) == threshold if exact else len(cells) >= threshold)
              and (orientation != 'vertical' or len({c for _, c in cells}) == 1)
              and (orientation != 'horizontal' or len({r for r, _ in cells}) == 1)]
    if first_only:
        groups = groups[:1]
    selected = {cell for _, cells in groups for cell in cells}
    colors = {color for color, _ in groups}
    return [[0 if ((row, col) in selected or (whole_colors and value in colors)) else value
             for col, value in enumerate(values)] for row, values in enumerate(grid)]


def predict(grid, mode):
    _mode({'mode': mode})
    settled = _gravity(grid)
    return settled if mode == 'down' else _gravity(_clear(settled))


def _repeat_clear(grid, *, sequential=False):
    current = _gravity(grid)
    # Every nonterminal iteration removes at least three cells, so this is finite.
    while True:
        cleared = _clear(current, first_only=sequential)
        if cleared == current:
            return current
        current = _gravity(cleared)


def rival_predictions(grid, mode):
    """Declared finite rival family; it cannot establish universal uniqueness."""
    _mode({'mode': mode})
    out = {'other_setting': predict(grid, MODES[mode == 'down']), 'identity': deepcopy(grid)}
    for name in ('reverse_column_order', 'freeze_bottom_supported_columns',
                 'cap_three_cells_per_column'):
        first = _gravity(grid, name)
        out[name] = first if mode == 'down' else _gravity(_clear(first))
    if mode == 'settle_clear_once':
        settled = _gravity(grid)
        out.update({
            'clear_before_gravity': _gravity(_clear(grid)),
            'omit_final_gravity': _clear(settled),
            'repeat_until_stable': _repeat_clear(grid),
            'threshold_two': _gravity(_clear(settled, threshold=2)),
            'threshold_four': _gravity(_clear(settled, threshold=4)),
            'exactly_three': _gravity(_clear(settled, exact=True)),
            'eight_connected': _gravity(_clear(settled, diagonal=True)),
            'clear_whole_colors': _gravity(_clear(settled, whole_colors=True)),
            'sequential_clearing': _repeat_clear(grid, sequential=True),
            'vertical_only': _gravity(_clear(settled, orientation='vertical')),
            'horizontal_only': _gravity(_clear(settled, orientation='horizontal')),
        })
    return out


def teaching_check(episode, mode):
    demos, queries = episode['train'], episode['test']
    rivals = [rival_predictions(pair['input'], mode) for pair in demos]
    survivors = [name for name in rivals[0]
                 if all(pair['output'] == predictions[name]
                        for pair, predictions in zip(demos, rivals))]
    # Query labels never participate in fitting or selecting demonstrations.
    harmful = [name for name in survivors
               if any(pair['output'] != rival_predictions(pair['input'], mode)[name]
                      for pair in queries)]
    settings = [value for value in MODES
                if all(predict(pair['input'], value) == pair['output'] for pair in demos)]
    return {'setting_survivors': settings, 'rivals': list(rivals[0]),
            'demo_survivors': survivors, 'query_changing_survivors': harmful,
            'scope': 'Only the named finite rivals; no universal uniqueness claim.'}


def _rng(seed, tag):
    digest = hashlib.sha256(f'{TASK_ID}/settle-clear-v1/{seed}/{tag}'.encode()).digest()
    return random.Random(int.from_bytes(digest, 'big'))


def _scatter(height, width, stacks, rng, *, supported=None, borders=False):
    """Scatter each stack into increasing row positions, preserving its order."""
    grid = [[0] * width for _ in range(height)]
    for col, values in sorted(stacks.items()):
        n = len(values)
        if borders and col == 0:
            rows = [0] + sorted(rng.sample(range(1, height - 1), n - 2)) + [height - 1]
        elif col == supported:
            rows = sorted(rng.sample(range(height - 1), n - 1)) + [height - 1]
        else:
            rows = sorted(rng.sample(range(height), n))
        for row, value in zip(rows, values):
            grid[row][col] = value
    return grid


def _motif(seed, tag, kind, *, shape=None):
    rng = _rng(seed, tag)
    height, width = shape or (rng.randint(12, 18), rng.randint(9, 22))
    colors = rng.sample(range(1, 10), 6)
    a, b, c, d, e, f = colors
    if kind == 'cascade':
        stacks = {0: [b, a, a, a], 1: [b, b], 3: [a], 4: [b, a]}
    else:
        # Left: components of sizes four and three must clear simultaneously.
        # Right: three e cells touch only diagonally and therefore must survive.
        stacks = {0: [a, a, c], 1: [b, a, a], 2: [b, b, d],
                  4: [e, f], 5: [e, f, e]}
    offset = rng.randrange(width - max(stacks))
    stacks = {col + offset: values for col, values in stacks.items()}
    return _scatter(height, width, stacks, rng, supported=offset)


def _demonstrations(seed):
    # This gate uses only demonstration inputs and predictions under BOTH modes.
    # Private mode and requested query count cannot affect the chosen inputs.
    for attempt in range(48):
        grids = [_motif(seed, f'demo0/{attempt}', 'cascade'),
                 _motif(seed, f'demo1/{attempt}', 'simultaneous')]
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


def _random_scene(seed, tag, height, width, *, dense=False):
    rng = _rng(seed, tag)
    columns = list(range(width)) if dense else sorted(rng.sample(range(width), rng.randint(3, width)))
    palette = rng.sample(range(1, 10), rng.randint(3, 9))
    stacks = {}
    for col in columns:
        n = rng.randint(12, 24) if dense else rng.randint(2, min(height - 1, 10))
        stacks[col] = [rng.choice(palette) for _ in range(n)]
    # A scattered stack always has room to move; dense coverage spans the canvas.
    return _scatter(height, width, stacks, rng, supported=columns[-1], borders=dense)


def generate(seed, settings, demos=3, queries=4):
    mode = _mode(settings)
    _integer(seed, 0, 2**63 - 1, 'seed')
    _integer(demos, 2, 6, 'demos')
    _integer(queries, 1, 8, 'queries')
    train_inputs, attempts = _demonstrations(seed)
    for index in range(2, demos):
        rng = _rng(seed, f'demo-size/{index}')
        train_inputs.append(_random_scene(seed, f'extra-demo/{index}',
                                         rng.randint(9, 24), rng.randint(8, 25)))
    query_inputs = []
    for index in range(queries):
        if index == 0:
            grid = _motif(seed, 'query/0', 'cascade', shape=(6, 7))
        else:
            if index == 1:
                height, width = 30, 30
            elif index == 2:
                height, width = 6, 30
            elif index == 3:
                height, width = 30, 7
            else:
                rng = _rng(seed, f'query-size/{index}')
                height, width = rng.randint(6, 30), rng.randint(7, 30)
            grid = _random_scene(seed, f'query/{index}', height, width, dense=index == 1)
        query_inputs.append(grid)
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
    """One visible query, with neither answers nor a future-query count hint."""
    _integer(query_index, 0, len(episode['test']) - 1, 'query_index')
    return public_challenge_bytes({'train': episode['train'], 'test': [episode['test'][query_index]]})


def write_examples(destination, episodes):
    """Validate every exact-integer grid and execute labels before writing."""
    from arcpuzzles.parametric_worker import _grid, _real_evaluator
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    rows = deepcopy(list(episodes))
    if not rows:
        raise ValueError('at least one episode is required')
    apply, identity, bridge = _real_evaluator(find_root(__file__) / 'shared/runtime')
    try:
        if identity.get('backend') != 'racket' or identity.get('protected') is not True:
            raise ValueError('live protected Racket execution is required')
        for episode in rows:
            if episode['program_solution'] != program(episode['settings']):
                raise ValueError('episode program/settings mismatch')
            _integer(len(episode['train']), 2, 6, 'demos')
            _integer(len(episode['test']), 1, 8, 'queries')
            for pair in episode['train'] + episode['test']:
                _grid(pair['input'])
                _grid(pair['output'])
                executed = _grid(apply(episode['program_solution'], pair['input']))
                if executed != pair['output']:
                    raise ValueError('claimed label differs from protected Racket')
                pair['output'] = executed
            episode['teaching'] = teaching_check(episode, _mode(episode['settings']))
            if episode['teaching']['setting_survivors'] != [episode['settings']['mode']]:
                raise ValueError('demonstrations do not identify exactly the selected mode')
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
    episodes = [generate(args.seed, {'mode': mode}, args.demos, args.queries) for mode in MODES]
    print(json.dumps(write_examples(args.out, episodes), indent=2))


if __name__ == '__main__':
    main()
