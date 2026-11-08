#!/usr/bin/env python3
"""Proposed, task-local denser/sparser reflection episodes; labels execute Racket.

Only public/*.json is model-visible. Production generator and authority are
unchanged. The sampler deliberately uses straight guides with a unique modal
payload color and informative nonempty sides; see README.md for exact limits.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import sys

from reviewer_support import (
    canonical_pairs, canonical_path, find_root, load_selected_generator,
    public_challenge_bytes, public_challenge_id,
)
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK_ID = 'cbf77aa253ac'
SETTINGS = ('denser', 'sparser')
ROOT = find_root(__file__)
CANONICAL_PROGRAM_SHA256 = 'e86c8f2c6f08d2c511e0606a486816bb3c58cd4020293e4ae0fb90abcd0933ee'
base, BASE_PATH, BASE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n').encode()


def _bounded_int(name, value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{name} must be an exact integer in [{low}, {high}]')
    return value


def _setting(value):
    if type(value) is not str or value not in SETTINGS:
        raise ValueError(f'side_policy must be one of {SETTINGS}')
    return value


@lru_cache(maxsize=1)
def canonical_program():
    programs = []
    with canonical_path(ROOT).open(encoding='utf-8') as stream:
        for line in stream:
            if line.strip():
                record = json.loads(line)
                if record.get('task_id') == TASK_ID:
                    programs.append(record['program_solution'])
    if not programs or len(set(programs)) != 1:
        raise ValueError('canonical rule is missing or ambiguous')
    if _sha(programs[0].encode()) != CANONICAL_PROGRAM_SHA256:
        raise ValueError('canonical source changed; review substitutions before authoring')
    return programs[0]


def _replace_once(program, old, new):
    if program.count(old) != 1:
        raise ValueError(f'expected one exact rule anchor: {old}')
    return program.replace(old, new)


def program_for(side_policy):
    _setting(side_policy)
    program = canonical_program()
    if side_policy == 'sparser':
        program = _replace_once(program, '(>= above below)', '(<= above below)')
        program = _replace_once(program, '(>= left right)', '(<= left right)')
    return program


def select_setting(seed):
    _bounded_int('seed', seed, 0, 2**64 - 1)
    digest = hashlib.sha256(f'{TASK_ID}/policy/v1/{seed}'.encode()).digest()
    return SETTINGS[int.from_bytes(digest, 'big') % len(SETTINGS)]


def _grow_shape(rng, count, length, depth):
    """Connected payload rooted next to the guide, in local (depth, column)."""
    selected = [(1, rng.randrange(length))]
    occupied = set(selected)
    while len(selected) < count:
        frontier = sorted({(d + dd, c + dc) for d, c in occupied
                           for dd, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                           if 1 <= d + dd <= depth and 0 <= c + dc < length
                           and (d + dd, c + dc) not in occupied})
        if not frontier:
            raise ValueError('payload shape capacity exhausted')
        cell = rng.choice(frontier)
        selected.append(cell)
        occupied.add(cell)
    return selected


def _draw_input(rng, horizontal, negative_dense, query):
    """One noninteracting straight-guide component, safe for both policies."""
    low, high, depth = (18, 30, 4) if query else (13, 18, 3)
    height, width = rng.randint(low, high), rng.randint(low, high)
    length = rng.randint(7 if query else 5, min(12 if query else 9, width - 4))
    axis = rng.randint(depth + 1, height - depth - 2)
    left = rng.randint(1, width - length - 1)
    main, secondary = rng.sample([1, 2, 3, 5, 6, 7, 8, 9], 2)
    dense_count, sparse_count = rng.randint(5, 8), rng.randint(2, 4)
    # Main is uniquely modal globally, but total occupancy favors its sparse
    # side. Thus the demos teach modal-color counting, not total area counting.
    secondary_count = dense_count - sparse_count + 2
    dense = _grow_shape(rng, dense_count, length, depth)
    sparse = _grow_shape(rng, sparse_count + secondary_count, length, depth)
    grid = [[0] * width for _ in range(height)]
    for col in range(left, left + length):
        grid[axis][col] = 4
    dense_sign = -1 if negative_dense else 1
    for d, c in dense:
        grid[axis + dense_sign * d][left + c] = main
    for index, (d, c) in enumerate(sparse):
        grid[axis - dense_sign * d][left + c] = main if index < sparse_count else secondary
    return grid if horizontal else [list(row) for row in zip(*grid)]


def sample_inputs(seed, *, demo_count=4, query_count=4, attempt_limit=64):
    _bounded_int('seed', seed, 0, 2**64 - 1)
    _bounded_int('demo_count', demo_count, 4, 12)
    _bounded_int('query_count', query_count, 1, 8)
    _bounded_int('attempt_limit', attempt_limit, 1, 512)
    # Four required cases prevent a fixed-side or orientation-only shortcut.
    roles = ((True, True), (True, False), (False, True), (False, False))
    sampled = {'train': [], 'test': [], 'roles': {'train': [], 'test': []}}
    seen = set()
    for split, count in (('train', demo_count), ('test', query_count)):
        for index in range(count):
            horizontal, negative_dense = roles[index % len(roles)]
            for attempt in range(attempt_limit):
                token = f'{TASK_ID}/inputs/v1/{seed}/{split}/{index}/{attempt}'
                rng = random.Random(int.from_bytes(hashlib.sha256(token.encode()).digest(), 'big'))
                grid = _draw_input(rng, horizontal, negative_dense, split == 'test')
                signature = _sha(_json_bytes(grid))
                if signature not in seen:
                    break
            else:
                raise ValueError(f'could not draw distinct {split} input {index} after {attempt_limit} attempts')
            seen.add(signature)
            sampled[split].append(grid)
            sampled['roles'][split].append({'orientation': 'horizontal' if horizontal else 'vertical',
                                             'modal_dense_side': 'negative' if negative_dense else 'positive',
                                             'attempt': attempt})
    return sampled


def _validate_grid(grid):
    # Reuse the exact public grid contract: lists and int cells (not bool).
    public_challenge_bytes({'train': [{'input': grid, 'output': grid}], 'test': [{'input': grid}]})


@lru_cache(maxsize=64)
def _wrapped(program):
    return wrap_rule(program)


def execute(bridge, program, grid):
    _validate_grid(grid)
    literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
    output = bridge.eval_text(f'({_wrapped(program)} {literal})')
    _validate_grid(output)
    return output


def python_prediction(grid, side_policy, *, with_clipped=False):
    """Independent check only; this never supplies exported labels."""
    _setting(side_policy)
    _validate_grid(grid)
    plans = []
    for cells in base._components(grid):
        plan = base._component_plan(grid, cells)
        if plan is None:
            continue
        if side_policy == 'sparser':
            negative = plan['negative_count'] <= plan['positive_count']
            coordinate = 0 if plan['horizontal'] else 1
            axis = plan['axis']
            plan['source'] = {cell for cell in cells if cell[coordinate] == axis
                              or (cell[coordinate] < axis if negative else cell[coordinate] > axis)}
        plans.append(plan)
    result = base._execute(grid, plans)
    return result if with_clipped else result[0]


def candidate_programs(side_policy):
    program = program_for(side_policy)
    cmp = '>=' if side_policy == 'denser' else '<='

    def fixed(horizontal, vertical):
        changed = _replace_once(program, f'({cmp} above below)', horizontal)
        return _replace_once(changed, f'({cmp} left right)', vertical)

    def orientation_only(horizontal):
        compare = '>' if horizontal else '<='
        filter_expression = (
            '(filter (lambda (o) '
            '(let* ((fs (filter (lambda (p) (= (cell-color p) 4)) (obj-cells o))) '
            '(rs (map first fs)) (cs (map second fs))) '
            f'({compare} (- (max-list cs) (min-list cs)) (- (max-list rs) (min-list rs))))) comps)')
        return _replace_once(program, '((comp comps))', f'((comp {filter_expression}))')

    modal_test = '(= (cell-color p) main-color)'
    if program.count(modal_test) != 4:
        raise ValueError('modal-count rival requires four exact source anchors')
    return {
        'setting:denser': program_for('denser'),
        'setting:sparser': program_for('sparser'),
        'identity': '(rule! (lambda (g) g))',
        'horizontal_only': orientation_only(True),
        'vertical_only': orientation_only(False),
        'always_negative': fixed('#t', '#t'),
        'always_positive': fixed('#f', '#f'),
        'horizontal_negative_vertical_positive': fixed('#t', '#f'),
        'horizontal_positive_vertical_negative': fixed('#f', '#t'),
        'total_payload': program.replace(modal_test, '#t'),
    }


def lesson_certificate(predictions, demo_count, chosen_name):
    """Eliminate candidates only on demonstrations, then compare query predictions."""
    if chosen_name not in predictions:
        raise ValueError('chosen rule must belong to the declared candidate set')
    chosen = predictions[chosen_name]
    _bounded_int('demo_count', demo_count, 1, len(chosen) - 1)
    if any(len(values) != len(chosen) for values in predictions.values()):
        raise ValueError('candidate prediction counts differ')
    mismatches = {name: [i for i in range(demo_count) if outputs[i] != chosen[i]]
                  for name, outputs in sorted(predictions.items())}
    survivors = [name for name, wrong in mismatches.items() if not wrong]
    identifiable = [len({_sha(_json_bytes(predictions[name][i])) for name in survivors}) == 1
                    for i in range(demo_count, len(chosen))]
    return {'candidate_count': len(predictions), 'demo_count': demo_count,
            'demo_mismatches': mismatches, 'survivors': survivors,
            'query_identifiable': identifiable,
            'scope': 'finite declared candidates; survivors depend only on demonstration labels'}


@lru_cache(maxsize=1)
def source_hashes():
    relative_paths = [
        f'generators/{TASK_ID}/generator.py',
        f'generators/{TASK_ID}/workspace/parametric/prototype.py',
        'shared/runtime/reviewer_support.py',
        'shared/runtime/puzzle_generators/rule_wrap.py',
        'shared/runtime/arc_repl/racket_bridge.py',
        'shared/data/canonical/puzzles.jsonl',
    ]
    return {name: _sha((ROOT / name).read_bytes()) for name in relative_paths}


def check_canonical(bridge):
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    program = program_for('denser')
    records = []
    for pair in pairs:
        actual = execute(bridge, program, pair['input'])
        if actual != pair['output']:
            raise AssertionError(f'canonical parity failed: {pair["variant"]}/{pair["split"]}/{pair["pair_index"]}')
        records.append({key: pair[key] for key in ('variant', 'split', 'pair_index')} |
                       {'input_sha256': _sha(_json_bytes(pair['input'])), 'output_sha256': _sha(_json_bytes(actual))})
    return {'pair_count': len(pairs), 'matched': len(records),
            'unique_inputs': len({row['input_sha256'] for row in records}),
            'program_sha256': _sha(program.encode()), 'pairs': records}


def build_episode(seed, *, side_policy=None, demo_count=4, query_count=4, attempt_limit=64, bridge=None):
    sampled = sample_inputs(seed, demo_count=demo_count, query_count=query_count, attempt_limit=attempt_limit)
    policy = select_setting(seed) if side_policy is None else _setting(side_policy)
    if bridge is None:
        with RacketBridge(timeout=10) as owned:
            return build_episode(seed, side_policy=policy, demo_count=demo_count, query_count=query_count,
                                 attempt_limit=attempt_limit, bridge=owned)
    programs = candidate_programs(policy)
    inputs = sampled['train'] + sampled['test']
    predictions = {name: [execute(bridge, program, grid) for grid in inputs]
                   for name, program in programs.items()}
    chosen_name = 'setting:' + policy
    labels = predictions[chosen_name]
    for grid, output in zip(inputs, labels):
        if output != python_prediction(grid, policy):
            raise AssertionError('Racket/Python disagreement on sampled input')
    certificate = lesson_certificate(predictions, demo_count, chosen_name)
    if certificate['survivors'] != [chosen_name] or not all(certificate['query_identifiable']):
        raise ValueError('lesson failed to distinguish the declared rule and shortcut candidates')
    paired = [{'input': deepcopy(grid), 'output': output} for grid, output in zip(inputs, labels)]
    program = programs[chosen_name]
    return {'schema': 'cbf77aa253ac-side-policy-prototype-v1', 'status': 'proposed',
            'parent_family': 'training:5b692c0f', 'task_id': TASK_ID,
            'seed': seed, 'side_policy': policy, 'demo_count': demo_count, 'query_count': query_count,
            'train': paired[:demo_count], 'test': paired[demo_count:],
            'program': program, 'program_sha256': _sha(program.encode()),
            'sources': source_hashes(), 'roles': sampled['roles'],
            'certificate': certificate, 'candidate_programs': programs,
            'candidate_predictions': predictions,
            'limitations': ['one straight guide and one component per sampled scene',
                            'unique modal payload color; unequal nonempty side counts',
                            'both policy reflections stay in bounds',
                            'finite rival set only; no production or training approval']}


def write_batch(episodes, output):
    """Public names depend only on exact public bytes; all provenance is private."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    prepared = sorted(((public_challenge_id(ep), public_challenge_bytes(ep), ep) for ep in episodes),
                      key=lambda row: row[0])
    if not prepared:
        raise ValueError('empty episode batch')
    ids = [row[0] for row in prepared]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate public challenge payload')
    output.mkdir(parents=True)
    (output / 'public').mkdir()
    (output / 'private/programs').mkdir(parents=True)
    manifest = {'schema': 'cbf77aa253ac-parametric-export-v1', 'status': 'proposed',
                'model_visible': 'public/*.json only', 'episodes': [], 'files': {},
                'command': sys.argv, 'cwd': str(Path.cwd()), 'sources': source_hashes()}

    def write(relative, data):
        path = output / relative
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f'conflicting export artifact: {relative}')
        path.write_bytes(data)
        manifest['files'][relative] = {'sha256': _sha(data), 'bytes': len(data)}

    for public_id, visible, episode in prepared:
        public_path, private_path = f'public/{public_id}.json', f'private/{public_id}.json'
        write(public_path, visible)
        write(private_path, _json_bytes(episode))
        for program in episode['candidate_programs'].values():
            raw = program.encode()
            write(f'private/programs/{_sha(raw)}.rkt', raw)
        manifest['episodes'].append({'public_id': public_id, 'public_path': public_path,
                                     'private_path': private_path, 'side_policy': episode['side_policy'],
                                     'seed': episode['seed'], 'demo_count': len(episode['train']),
                                     'query_count': len(episode['test']),
                                     'program_sha256': episode['program_sha256']})
    (output / 'manifest.json').write_bytes(_json_bytes(manifest))
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument('--side-policy', choices=SETTINGS)
    selection.add_argument('--all-settings', action='store_true')
    parser.add_argument('--demo-count', type=int, default=4)
    parser.add_argument('--query-count', type=int, default=4)
    parser.add_argument('--attempt-limit', type=int, default=64)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    # Check count and scalar contracts before starting the executable runtime.
    sample_inputs(args.seed, demo_count=args.demo_count, query_count=args.query_count,
                  attempt_limit=args.attempt_limit)
    policies = SETTINGS if args.all_settings else (args.side_policy or select_setting(args.seed),)
    with RacketBridge(timeout=10) as bridge:
        canonical = check_canonical(bridge)
        episodes = [build_episode(args.seed, side_policy=policy, demo_count=args.demo_count,
                                  query_count=args.query_count, attempt_limit=args.attempt_limit,
                                  bridge=bridge) for policy in policies]
    manifest = write_batch(episodes, args.out)
    canonical_path_out = args.out / 'private/canonical-check.json'
    canonical_path_out.write_bytes(_json_bytes(canonical))
    manifest['files']['private/canonical-check.json'] = {
        'sha256': _sha(canonical_path_out.read_bytes()), 'bytes': canonical_path_out.stat().st_size}
    (args.out / 'manifest.json').write_bytes(_json_bytes(manifest))
    print(json.dumps({'status': 'ok', 'out': str(args.out), 'episodes': len(episodes),
                      'demo_count': args.demo_count, 'query_count': args.query_count,
                      'canonical_pairs_matched': canonical['matched'],
                      'survivors': [ep['certificate']['survivors'] for ep in episodes]}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
