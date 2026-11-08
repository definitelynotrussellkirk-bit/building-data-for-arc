#!/usr/bin/env python3
"""Bounded replay tool; run through review.py run so Racket/runtime are pinned.

Retains two fully Racket-labeled lessons, finite-rival teaching counterexamples,
eight independently hash-named one-query public turns, and a causal ablation.
A witness is admission-bound only when --qualification names native evidence.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'shared/runtime'))
_spec = importlib.util.spec_from_file_location('_stream_verify_adapter', HERE / 'adapter.py')
adapter = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter)

DEPENDENCY = {
    'step_a': 'Follow the already-steered stream to its next first-hit bar.',
    'intermediate': 'The input-dependent reached bar coordinates and its color.',
    'step_b': 'Choose the signed lateral slide from that reached bar color and the episode handedness.',
    'why_b_depends_on_a': 'Earlier slides change the column and therefore which downstream bar is reached. The leftmost bar or a fixed color cannot choose the next direction.'}


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def bound_source(path):
    if path is None:
        return None
    qualification = json.loads(path.read_text())
    if qualification.get('task_id') != 'defba1ab4f90' or qualification.get('status') != 'qualified':
        raise ValueError('expected a qualified native report for defba1ab4f90')
    binding = qualification['source_binding']
    for row in binding['files']:
        actual = hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest()
        if actual != row['sha256']:
            raise ValueError('source changed after qualification: ' + row['path'])
    return binding


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, default=32)
    parser.add_argument('--qualification', type=Path)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 128:
        parser.error('--seeds must be 1..128')
    binding = bound_source(args.qualification)
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / 'public').mkdir()
    census = {'seeds': list(range(args.seeds)), 'demo_counts': [2, 3, 6],
              'query_count': 4, 'episodes': 0, 'failures': [], 'max_demo_attempts': 0,
              'scope': 'Python structural/finite-rival census; not a Racket replay of every census episode'}
    for seed in range(args.seeds):
        for demos in census['demo_counts']:
            matched = None
            for mode in adapter.core.MODES:
                settings = {'handedness': mode}
                episode = adapter.generate(seed, settings, demos, 4)
                inputs = [p['input'] for p in episode['train'] + episode['test']]
                if matched is not None and inputs != matched:
                    raise AssertionError('settings changed the input distribution')
                matched = inputs
                census['max_demo_attempts'] = max(census['max_demo_attempts'], episode['private']['demo_attempts'])
                census['episodes'] += 1
    from arcpuzzles.parametric_worker import _real_evaluator
    from reviewer_support import public_challenge_bytes, public_challenge_id
    apply, identity, bridge = _real_evaluator(ROOT / 'shared/runtime')
    evaluations = 0

    def execute(program, grid):
        nonlocal evaluations
        evaluations += 1
        return apply(program, deepcopy(grid))

    private = []; teaching = []
    try:
        for mode in adapter.core.MODES:
            settings = {'handedness': mode}
            episode = adapter.generate(0, settings, 3, 4)
            for pair in episode['train'] + episode['test']:
                actual = execute(episode['program_solution'], pair['input'])
                if actual != pair['output']:
                    raise AssertionError('Racket disagreed with a retained label')
                pair['output'] = actual
            competing = {'other_handedness': adapter.program({'handedness': 'reversed' if mode == 'canonical' else 'canonical'})}
            competing.update({name: adapter.core.rival_program(settings, name) for name in adapter.core.RIVALS})
            refutations = []
            for name, program in competing.items():
                differences = []
                for index, pair in enumerate(episode['train']):
                    actual = execute(program, pair['input'])
                    if actual != pair['output']:
                        differences.append({'demo_index': index, 'rival_output': actual})
                if not differences:
                    raise AssertionError('surviving Racket rival: ' + name)
                refutations.append({'rival': name, 'program': program, 'witness': differences[0]})
            teaching.append({'settings': settings, 'surviving_settings': [settings],
                             'surviving_rivals': [], 'refutations': refutations})
            single = adapter.generate(0, settings, 3, 1)
            if adapter.core.public_turn(single, 0) != adapter.core.public_turn(episode, 0):
                raise AssertionError('first turn changed with future query count')
            ids = []
            for index in range(4):
                challenge = adapter.core.public_turn(episode, index)
                public_id = public_challenge_id(challenge)
                destination = args.out / 'public' / (public_id + '.json')
                if destination.exists():
                    raise AssertionError('duplicate visible challenge')
                destination.write_bytes(public_challenge_bytes(challenge))
                ids.append(public_id)
            private.append({'episode': episode, 'public_turn_ids': ids})

        grid = [[0] * 14 for _ in range(12)]
        grid[0][5] = 2
        for row, start, color in ((2, 4, 1), (4, 6, 3), (4, 1, 1), (6, 4, 1)):
            grid[row][start:start + 3] = [color] * 3
        settings = {'handedness': 'canonical'}
        program = adapter.program(settings)
        counter = adapter.core.rival_program(settings, 'always_blue')
        output = execute(program, grid); counter_output = execute(counter, grid)
        if output == counter_output:
            raise AssertionError('causal ablation did not change output')
        if output != adapter.core.trace(grid, settings)[0]:
            raise AssertionError('causal witness Racket/Python mismatch')
        witness = {'schema': 'arcpuzzles-sequential-dependency-witness-v1',
                   'task_id': 'defba1ab4f90', 'source_binding': binding, **DEPENDENCY,
                   'racket': {key: identity[key] for key in ('backend', 'protected')},
                   'runtime_identity': identity,
                   'qualification_status': 'native-source-bound' if binding else 'diagnostic-unbound; supply --qualification',
                   'cases': [{'input': grid, 'settings': settings,
                              'intermediate_value': {'first_exit': [2, 7], 'next_hit': [4, 7],
                                                     'reached_color': 3, 'ignored_bar': {'row': 4, 'columns': [1, 2, 3], 'color': 1}},
                              'program': program, 'output': output,
                              'counterfactual_program': counter, 'counterfactual_output': counter_output,
                              'ablation': 'wrong_intermediate'}]}
        save(args.out / 'sequential-dependency.json', witness)
        save(args.out / 'private.json', {'episodes': private, 'teaching': teaching, 'racket': identity})
    finally:
        bridge.close()
    report = {'task_id': 'defba1ab4f90', 'census': census, 'racket': identity,
              'racket_evaluations': evaluations, 'retained_episodes': len(private),
              'retained_demo_counts': [3, 3], 'retained_queries_per_episode': 4,
              'public_turn_files': 8, 'tested_rivals_per_setting': list(competing),
              'source_binding': binding, 'failures': [], 'owner_accepted': False,
              'limits': 'Finite declared rules/rivals only; no training admission or universal identifiability.'}
    save(args.out / 'report.json', report)
    print(json.dumps({'episodes': census['episodes'], 'racket_evaluations': evaluations,
                      'retained_episodes': len(private), 'report': str(args.out / 'report.json')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
