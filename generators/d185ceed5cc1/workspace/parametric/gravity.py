#!/usr/bin/env python3
"""Isolated episode-level gravity proposal; canonical execution stays rightward."""
from __future__ import annotations
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid

TASK_ID = 'd185ceed5cc1'
GENERATOR_SHA256 = '77ecaed15d25d11dba9d95a1857f98a28f229b4ad3023f69da354b874ed210de'
DIRECTIONS = ('right', 'left')


def choose_direction(seed, direction=None):
    if type(seed) is not int or seed < 0:
        raise ValueError('seed must be a nonnegative literal integer')
    if direction is None:
        digest = hashlib.sha256(f'{TASK_ID}:gravity-v1:{seed}'.encode()).digest()
        return DIRECTIONS[digest[0] % 2]
    if type(direction) is not str or direction not in DIRECTIONS:
        raise ValueError('gravity must be right or left')
    return direction


def python_pack(grid, direction):
    """Independent row/segment oracle preserving wall positions and pebble order."""
    choose_direction(0, direction)
    source = normalize_grid(grid)
    output = []
    for row in source:
        result = list(row)
        start = 0
        for end in range(len(row) + 1):
            if end < len(row) and row[end] != 8:
                continue
            pebbles = [v for v in row[start:end] if v != 0]
            empty = [0] * (end - start - len(pebbles))
            result[start:end] = empty + pebbles if direction == 'right' else pebbles + empty
            start = end + 1
        output.append(result)
    return output


def materialize_program(direction='right', *, root=None):
    choose_direction(0, direction)
    root = Path(root) if root is not None else find_root(__file__)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()
            if json.loads(line).get('task_id') == TASK_ID]
    if len(rows) != 1:
        raise ValueError('expected one selected canonical program')
    canonical = rows[0]['program_solution']
    if direction == 'right':
        return canonical
    if not canonical.startswith('(rule! ') or not canonical.endswith(')'):
        raise ValueError('canonical wrapper changed; review the adapter')
    body = canonical[len('(rule! '):-1]
    # Conjugation reverses gravity while restoring input wall positions and order.
    return '(rule! (flip-lr (let ((g (flip-lr g))) ' + body + ')))'


def execute(bridge, program, grid):
    bridge.define_grid('__gravity_input__', normalize_grid(grid))
    return normalize_grid(bridge.eval_text(
        '(let ((g __gravity_input__) (rule! (lambda (value) value))) ' + program + ')'))


def public_challenge(episode):
    return {'train': deepcopy(episode['train']),
            'test': [{'input': deepcopy(pair['input'])} for pair in episode['test']]}


def generate_episode(seed, *, direction=None, bridge, root=None):
    chosen = choose_direction(seed, direction)
    root = Path(root) if root is not None else find_root(__file__)
    generator, _, source_hash = load_selected_generator(TASK_ID, root=root)
    if source_hash != GENERATOR_SHA256:
        raise ValueError('selected generator changed; recheck this prototype')
    grids = [generator.generate(seed, index, difficulty='medium') for index in range(4)]
    programs = {name: materialize_program(name, root=root) for name in DIRECTIONS}
    outputs = {name: [execute(bridge, programs[name], grid) for grid in grids] for name in DIRECTIONS}
    for name in DIRECTIONS:
        assert outputs[name] == [python_pack(grid, name) for grid in grids]
    separating = [i for i in range(4) if outputs['left'][i] != outputs['right'][i]]
    if separating != list(range(4)):
        raise ValueError('all demonstrations and the query must distinguish gravity')
    pairs = [{'input': deepcopy(grid), 'output': outputs[chosen][i]} for i, grid in enumerate(grids)]
    return {'schema': 'arcpuzzles-gravity-prototype-episode-v1', 'task_id': TASK_ID,
            'seed': seed, 'parameter': {'gravity': chosen}, 'program': programs[chosen],
            'program_sha256': hashlib.sha256(programs[chosen].encode()).hexdigest(),
            'generator_sha256': source_hash, 'train': pairs[:3], 'test': pairs[3:],
            'alternative_outputs': outputs['left' if chosen == 'right' else 'right'],
            'separating_pair_indices': separating, 'variant_approved': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = find_root(__file__)
    args.out.mkdir(parents=True, exist_ok=False)
    def write(name, value):
        p = args.out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')
    with RacketBridge(timeout=15, startup_timeout=60) as bridge:
        canonical = materialize_program(root=root)
        anchors = canonical_pairs(TASK_ID, root=root)
        for pair in anchors:
            assert execute(bridge, canonical, pair['input']) == pair['output']
        episodes = [generate_episode(seed, direction=setting, bridge=bridge, root=root)
                    for seed, setting in [(17, 'right'), (18, 'left')]]
    for i, episode in enumerate(episodes):
        write(f'private/episode-{i:03d}.json', episode)
        write(f'public/episode-{i:03d}.json', public_challenge(episode))
    for name in DIRECTIONS:
        p = args.out / f'private/{name}.rkt'
        p.write_text(materialize_program(name, root=root))
    files = [{'path': str(p.relative_to(args.out)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
              'bytes': p.stat().st_size} for p in sorted(args.out.rglob('*')) if p.is_file()]
    report = {'schema': 'arcpuzzles-gravity-prototype-verification-v1', 'task_id': TASK_ID,
              'generator_sha256': GENERATOR_SHA256, 'canonical_rule_hash': 'a1ebff603893',
              'canonical_ledger_sha256': hashlib.sha256(canonical_path(root).read_bytes()).hexdigest(),
              'parameters': {'gravity': ['right', 'left']}, 'chosen_once_per_episode': True,
              'canonical_pairs_executed': len(anchors), 'episodes': 2, 'racket_evaluations': len(anchors) + 16,
              'pairs_per_episode': {'demonstrations': 3, 'queries': 1},
              'all_pairs_separate_settings': True, 'all_racket_labels_match_independent_python': True,
              'runtime': racket_runtime_status(), 'files': files, 'variant_approved': False,
              'production_parametric_api': False,
              'limits': 'Two deterministic episodes and two settings; canonical-profiled full-palette sampler. No universal identifiability or training improvement claim.'}
    write('report.json', report)
    print(json.dumps({'episodes': 2, 'racket_evaluations': report['racket_evaluations'],
                      'all_pairs_separate_settings': True, 'report': str(args.out / 'report.json')}))


if __name__ == '__main__':
    main()
