#!/usr/bin/env python3
"""Bounded, unapproved mapping-direction prototype; labels come from Racket.

No production generator/runtime interfaces are changed. Use --help for the
single-file CLI; import generate_episode / RuleExecutor for task-local reuse.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import shlex
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = 'c5f62271ea44'
DIRECTIONS = ('forward', 'inverse')
TRANSFORMS = ('identity', 'transpose', 'flip_lr', 'rot_cw', 'flip_ud',
              'anti_transpose', 'rot180', 'rot_ccw')
INVERSE = {'rot_cw': 'rot_ccw', 'rot_ccw': 'rot_cw'}


def sha256_text(source):
    return hashlib.sha256(source.encode()).hexdigest()


def digest(value):
    return sha256_text(json.dumps(value, sort_keys=True, separators=(',', ':')))


def _validate_seed(seed):
    if type(seed) is not int or seed < 0:
        raise ValueError('seed must be a nonnegative Python int')


def _validate_direction(mapping_direction):
    if mapping_direction not in DIRECTIONS:
        raise ValueError(f'mapping_direction must be one of {DIRECTIONS}')


def choose_direction(seed):
    """Draw exactly one reproducible hidden direction for an episode seed."""
    _validate_seed(seed)
    return DIRECTIONS[int(sha256_text(f'{TASK_ID}:direction:v1:{seed}'), 16) % 2]


def canonical_source(root):
    """Read the selected first canonical program without scripts.* aliases.

    reviewer_support owns location/encoding for pairs; no copied grids or
    archives are interpreted as executable source. Match Catalog's selected
    first program_solution row, preserving its exact text including comments.
    """
    with canonical_path(root).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get('task_id') == TASK_ID and row.get('program_solution'):
                    return str(row['program_solution'])
    raise FileNotFoundError(f'No selected canonical Racket source for {TASK_ID}')


def rule_source(root, mapping_direction='forward'):
    """Materialize source; inverse reverses the two quarter-turn actions only."""
    _validate_direction(mapping_direction)
    source = canonical_source(root)
    if mapping_direction == 'forward':
        return source
    clockwise = '(list (list C A D B) rotate-cw)'
    counterclockwise = '(list (list B D A C) rotate-ccw)'
    if source.count(clockwise) != 1 or source.count(counterclockwise) != 1:
        raise ValueError('canonical rotation arms changed; review inverse materialization')
    source = source.replace(clockwise, '(list (list C A D B) rotate-ccw)')
    source = source.replace(counterclockwise, '(list (list B D A C) rotate-cw)')
    return (';; Proposed mapping_direction=inverse: infer the same key transform;\n'
            ';; apply its inverse to the complete panel. Not canonical approval.\n' + source)


def transform(grid, name):
    """Independent coordinate mirror used for verification, never labels."""
    h, w = len(grid), len(grid[0])
    if name == 'identity':
        return deepcopy(grid)
    if name == 'transpose':
        return [[grid[c][r] for c in range(h)] for r in range(w)]
    if name == 'flip_lr':
        return [[grid[r][w - 1 - c] for c in range(w)] for r in range(h)]
    if name == 'rot_cw':
        return [[grid[h - 1 - c][r] for c in range(h)] for r in range(w)]
    if name == 'flip_ud':
        return [[grid[h - 1 - r][c] for c in range(w)] for r in range(h)]
    if name == 'anti_transpose':
        return [[grid[h - 1 - c][w - 1 - r] for c in range(h)] for r in range(w)]
    if name == 'rot180':
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if name == 'rot_ccw':
        return [[grid[c][w - 1 - r] for c in range(h)] for r in range(w)]
    raise ValueError(f'unknown transform {name}')


def infer(grid):
    """Locate blue panel, interpret absent key corner as blue, match D4."""
    ones = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1]
    r0, c0 = min(r for r, _ in ones), min(c for _, c in ones)
    r1, c1 = max(r for r, _ in ones), max(c for _, c in ones)
    panel = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    outside = {(r, c): value for r, row in enumerate(grid) for c, value in enumerate(row)
               if value and not (r0 <= r <= r1 and c0 <= c <= c1)}
    if len(outside) != 3:
        raise ValueError('expected three external key dots')
    kr0, kc0 = min(r for r, _ in outside), min(c for _, c in outside)
    kr1, kc1 = max(r for r, _ in outside), max(c for _, c in outside)
    signature = tuple(outside.get(point, 1) for point in
                      ((kr0, kc0), (kr0, kc1), (kr1, kc0), (kr1, kc1)))
    matches = []
    for name in TRANSFORMS:
        oriented = transform(panel, name)
        h, w = len(oriented), len(oriented[0])
        if (oriented[1][1], oriented[1][w - 2], oriented[h - 2][1], oriented[h - 2][w - 2]) == signature:
            matches.append(name)
    if len(matches) != 1:
        raise ValueError(f'nonunique D4 signature: {matches}')
    return panel, matches[0]


def mirror(grid, mapping_direction='forward'):
    _validate_direction(mapping_direction)
    panel, name = infer(grid)
    return transform(panel, INVERSE.get(name, name) if mapping_direction == 'inverse' else name)


class RuleExecutor:
    """One actual included Racket bridge; public bridge methods only."""

    def __init__(self, root):
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
        self.root = Path(root).resolve()
        self.sources = {direction: rule_source(root, direction) for direction in DIRECTIONS}
        self.calls = 0
        self.bridge = RacketBridge()
        try:
            for direction, source in self.sources.items():
                # This task's rule is already a complete lambda, with no DSL
                # for-shorthand or implicit h/w. Peel just rule! and comments;
                # generic wrap_rule imports unavailable scripts.* in a library.
                callable_text = strip_rule_wrapper(strip_line_comments(source))
                if not callable_text.startswith('(lambda (g)'):
                    raise ValueError('canonical rule is no longer the supported explicit lambda')
                self.bridge.eval_text(f'(define __direction_{direction} {callable_text})')
        except BaseException:
            self.bridge.shutdown()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.bridge.shutdown()

    def apply(self, grid, mapping_direction='forward'):
        _validate_direction(mapping_direction)
        self.bridge.define_grid('__direction_input', grid)
        output = self.bridge.eval_text(f'(__direction_{mapping_direction} __direction_input)')
        self.calls += 1
        if output != mirror(grid, mapping_direction):
            raise AssertionError('executed Racket disagrees with independent Python check')
        return output


def generate_episode(seed, mapping_direction='forward', *, root=None, executor=None):
    """Create four demos plus one query. None chooses once from seed.

    All five pairs encode quarter turns, with both directions represented. Thus
    all four-demo holdouts distinguish both declared parameter settings. The
    sampling constraint strengthens instruction without changing scene grammar.
    """
    _validate_seed(seed)
    if mapping_direction is None:
        mapping_direction = choose_direction(seed)
    _validate_direction(mapping_direction)
    root = find_root(__file__) if root is None else Path(root).resolve()
    if executor is None:
        with RuleExecutor(root) as active:
            return generate_episode(seed, mapping_direction, root=root, executor=active)
    if executor.root != root:
        raise ValueError('executor belongs to a different source root')
    gen, source_path, source_hash = load_selected_generator(TASK_ID, root=root)
    order = ['rot_cw', 'rot_ccw', 'rot_cw', 'rot_ccw', 'rot_cw']
    random.Random(int(sha256_text(f'{TASK_ID}:episode-order:v1:{seed}'), 16)).shuffle(order)
    pairs, predictions = [], {direction: [] for direction in DIRECTIONS}
    for index, name in enumerate(order):
        grid = gen.generate(seed, index, difficulty='medium', symmetry=name)
        errors = gen.self_check(grid) + gen.strict_canonical_like(grid)
        if errors:
            raise AssertionError(f'prototype input violates canonical grammar: {errors}')
        for direction in DIRECTIONS:
            predictions[direction].append(executor.apply(grid, direction))
        pairs.append({'input': grid, 'output': predictions[mapping_direction][-1]})
    rotations = []
    for heldout in range(5):
        demo_indices = [i for i in range(5) if i != heldout]
        surviving = [direction for direction in DIRECTIONS
                     if all(predictions[direction][i] == pairs[i]['output'] for i in demo_indices)]
        unresolved = [direction for direction in surviving
                      if predictions[direction][heldout] != pairs[heldout]['output']]
        if surviving != [mapping_direction] or unresolved:
            raise AssertionError('demonstrations fail to distinguish declared parameter rivals')
        rotations.append({'query_pair_index': heldout, 'demonstration_pair_indices': demo_indices,
                          'surviving_directions': surviving, 'unresolved_query_rivals': unresolved,
                          'rivals': {direction: {'demo_mismatches': [i for i in demo_indices
                                     if predictions[direction][i] != pairs[i]['output']],
                                     'query_matches': predictions[direction][heldout] == pairs[heldout]['output']}
                                     for direction in DIRECTIONS}})
    source = executor.sources[mapping_direction]
    return {'public': {'train': deepcopy(pairs[:4]), 'test': [{'input': deepcopy(pairs[4]['input'])}]},
            'private': {'schema': 'c5f62271ea44-parametric-direction-v1', 'status': 'prototype',
                        'task_id': TASK_ID, 'source_task_id': '94133066', 'seed': seed,
                        'parameters': {'mapping_direction': mapping_direction},
                        'generator_version': gen.VERSION, 'generator_source': str(source_path.relative_to(root)),
                        'generator_sha256': source_hash, 'prototype_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        'canonical_ledger_sha256': hashlib.sha256(canonical_path(root).read_bytes()).hexdigest(),
                        'racket_source': source, 'racket_source_sha256': sha256_text(source),
                        'racket_rule_hash': sha256_text(' '.join(source.split()))[:12],
                        'canonical_racket_source_sha256': sha256_text(executor.sources['forward']),
                        'label_authority': 'actual RacketBridge execution; Python mirror only checked',
                        'encoded_transforms': order, 'query_output': deepcopy(pairs[4]['output']),
                        'pair_sha256': [digest(pair) for pair in pairs], 'query_rotations': rotations}}


def write_suite(out, *, seeds, root=None):
    """Retain two settings, canonical parity, and same-input intervention."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    seeds = list(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('supply at least one unique seed')
    for seed in seeds:
        _validate_seed(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    with RuleExecutor(root) as executor:
        for direction, source in executor.sources.items():
            (out / f'{direction}.rkt').write_text(source, encoding='utf-8')
        canonical = canonical_pairs(TASK_ID, root=root)
        for pair in canonical:
            if executor.apply(pair['input'], 'forward') != pair['output']:
                raise AssertionError('default does not preserve canonical pair')
        episodes = []
        for seed in seeds:
            for direction in DIRECTIONS:
                episode = generate_episode(seed, direction, root=root, executor=executor)
                folder = out / f'{direction}-seed{seed}'
                folder.mkdir()
                for filename, value in (('challenge.json', episode['public']), ('private.json', episode['private'])):
                    (folder / filename).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
                episodes.append({'path': folder.name, 'seed': seed, 'mapping_direction': direction,
                                 'challenge_sha256': hashlib.sha256((folder / 'challenge.json').read_bytes()).hexdigest(),
                                 'private_sha256': hashlib.sha256((folder / 'private.json').read_bytes()).hexdigest()})
        gen, _, generator_hash = load_selected_generator(TASK_ID, root=root)
        witness_input = gen.generate(seeds[0], 0, symmetry='rot_cw')
        witness = {'input': witness_input, 'encoded_transform': 'rot_cw',
                   'forward_output': executor.apply(witness_input, 'forward'),
                   'inverse_output': executor.apply(witness_input, 'inverse')}
        witness['outputs_differ'] = witness['forward_output'] != witness['inverse_output']
        if not witness['outputs_differ']:
            raise AssertionError('intervention does not change output')
        (out / 'intervention-witness.json').write_text(json.dumps(witness, indent=2) + '\n')
        report = {'schema': 'c5f62271ea44-parametric-direction-evidence-v1', 'status': 'passed',
                  'scope': 'bounded task-local prototype; variants are not approved production rules',
                  'generator_sha256': generator_hash,
                  'prototype_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'parameter': {'name': 'mapping_direction', 'allowed': list(DIRECTIONS), 'default': 'forward'},
                  'seeds': seeds, 'episodes': len(episodes), 'episode_files': episodes,
                  'canonical_parity_pairs': len(canonical), 'query_rotations_checked': 5 * len(episodes),
                  'racket_calls': executor.calls, 'intervention_witness': {'path': 'intervention-witness.json',
                                                                           'outputs_differ': True},
                  'rules': {direction: {'sha256': sha256_text(source),
                                        'rule_hash': sha256_text(' '.join(source.split()))[:12]}
                            for direction, source in executor.sources.items()},
                  'limitations': ['Only two declared parameter rivals tested; not all possible ARC hypotheses.',
                                  'Episodes deliberately use quarter turns to teach the direction.',
                                  'Finite seeds; no training admission or canonical authority changes.']}
    (out / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path, help='new output directory')
    parser.add_argument('--seeds', default='0,17,71,103', help='comma-separated nonnegative episode seeds')
    args = parser.parse_args()
    report = write_suite(args.out, seeds=[int(seed) for seed in args.seeds.split(',')])
    report['payload_command'] = shlex.join([sys.executable, *sys.argv])
    (args.out / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({key: report[key] for key in ('status', 'episodes', 'canonical_parity_pairs',
                                                 'query_rotations_checked', 'racket_calls')}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
