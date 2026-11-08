"""Bounded same-checkout protected-Racket audit for the native tile family.

Run from the packet outer directory::

  WORK/.venv/bin/python review.py run python3 \
    generators/997c17fd6870/workspace/parametric/audit_native.py \
    --out generators/997c17fd6870/workspace/parametric/evidence/native-v2

Output paths must be new. This is finite authoring evidence, never acceptance.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
RUNTIME = ROOT / 'shared/runtime'
sys.path[:0] = [str(ROOT / 'src'), str(RUNTIME)]
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from reviewer_support import public_challenge_bytes

_spec = importlib.util.spec_from_file_location('_audit_native_tile_family', HOME / 'native_family.py')
family = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(family)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def checked_episode(episode, demos, queries):
    if type(episode) is not dict or len(episode['train']) != demos or len(episode['test']) != queries:
        raise ValueError('wrong episode/counts')
    keys = []
    for pair in episode['train'] + episode['test']:
        for key in ('input', 'output'):
            _grid(pair[key])
        keys.append(json.dumps(pair['input']))
    if len(keys) != len(set(keys)):
        raise ValueError('demonstration/query inputs must all differ')
    return episode


def first_bytes(episode):
    # Validate labels too: public projection intentionally omits test answers.
    checked_episode(episode, len(episode['train']), len(episode['test']))
    return public_challenge_bytes({'train': episode['train'], 'test': episode['test'][:1]})


def facts(grid):
    height, width = len(grid), len(grid[0])
    points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return {'shape': [height, width], 'nonzero_cells': len(points),
            'density': len(points) / (height * width),
            'occupied_rows': len({r for r, _ in points}),
            'occupied_columns': len({c for _, c in points}),
            'nonzero_bbox': [min(r for r, _ in points), min(c for _, c in points),
                            max(r for r, _ in points), max(c for _, c in points)],
            'contacts': {'top': any(r == 0 for r, _ in points),
                         'bottom': any(r == height - 1 for r, _ in points),
                         'left': any(c == 0 for _, c in points),
                         'right': any(c == width - 1 for _, c in points)},
            'quadrant_nonzero': [sum((r >= height // 2) == bottom and
                                      (c >= width // 2) == right for r, c in points)
                                 for bottom, right in ((False, False), (False, True),
                                                       (True, False), (True, True))]}


def negatives():
    records = []
    def reject(name, action):
        try:
            action()
        except (ValueError, TypeError) as error:
            records.append({'case': name, 'rejected': True, 'error': str(error)})
        else:
            raise AssertionError('invalid request accepted: ' + name)
    for key, value in (('seed', True), ('demos', True), ('queries', False),
                       ('demos', 1), ('demos', 7), ('queries', 0), ('queries', 5)):
        args = dict(seed=0, settings=deepcopy(family.DEFAULT), demos=2, queries=4)
        args[key] = value
        reject(f'{key}={value!r}', lambda args=args: family.generate(**args))
    for setting in ({'tile_width': True, 'order_mode': 'reverse'},
                    {'tile_width': 2, 'order_mode': True},
                    {'tile_width': 4, 'order_mode': 'reverse'},
                    {'tile_width': 2, 'order_mode': 'unknown'},
                    {'tile_width': 2}, dict(family.DEFAULT, extra=1)):
        reject('invalid settings: ' + repr(setting), lambda setting=setting: family.generate(0, setting))
    for bad in ([[True]], [[1.0]], [[10]], [[-1]], [[1], []], [], [[0] * 31]):
        episode = {'train': [{'input': [[0]], 'output': [[0]]}],
                   'test': [{'input': [[1]], 'output': bad}]}
        reject('bad private output export: ' + repr(bad), lambda episode=episode: first_bytes(episode))
        episode = {'train': [{'input': [[0]], 'output': bad}],
                   'test': [{'input': [[1]], 'output': [[0]]}]}
        reject('bad visible output export: ' + repr(bad), lambda episode=episode: first_bytes(episode))
    return records


def run(out):
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / 'public').mkdir()
    (out / 'private').mkdir()
    source_files = [HOME / name for name in ('audit_native.py', 'native_family.py', 'adapter.py',
                    'prototype.py', 'canonical.rkt', 'promotion.json')]
    source_files += [ROOT / 'src/arcpuzzles/parametric_worker.py',
                     RUNTIME / 'reviewer_support.py', RUNTIME / 'arc_repl/racket_bridge.py',
                     RUNTIME / 'puzzle_generators/rule_wrap.py']
    binding = {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in source_files}
    report = {'schema': '997c17fd6870-native-finite-audit-v1', 'status': 'running',
              'source_files_sha256': binding, 'seeds': [0, 17],
              'counts': {'demos': 2, 'queries': 4}, 'episodes': [],
              'scope': 'Finite declared settings/rivals and bounded seeds only; no owner acceptance, '
                       'qualification, universal uniqueness, or training admission.',
              'negative_cases': negatives()}
    executions = 0
    def execute(program, grid, expected):
        nonlocal executions
        _grid(grid)
        result = _grid(apply(program, deepcopy(grid)))
        executions += 1
        if result != _grid(expected):
            raise AssertionError('Protected Racket output differs from Python claim')
        return result
    with _local_imports(RUNTIME, HOME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        report['racket'] = identity
        try:
            for seed in (0, 17):
                shared_inputs = None
                for settings in family.SETTINGS:
                    episode = checked_episode(family.generate(seed, deepcopy(settings), 2, 4), 2, 4)
                    program = family.program(settings)
                    assert episode['program_solution'] == program
                    inputs = [p['input'] for p in episode['train'] + episode['test']]
                    if shared_inputs is None:
                        shared_inputs = inputs
                    assert inputs == shared_inputs, 'setting-dependent input sampler'
                    for pair in episode['train'] + episode['test']:
                        execute(program, pair['input'], pair['output'])
                    visible = first_bytes(episode)
                    single = family.generate(seed, deepcopy(settings), 2, 1)
                    assert visible == first_bytes(single), 'single-query first turn differs'
                    decoded = json.loads(visible)
                    assert set(decoded) == {'train', 'test'}
                    assert len(decoded['test']) == 1 and set(decoded['test'][0]) == {'input'}
                    assert decoded == {'train': episode['train'], 'test': [{'input': episode['test'][0]['input']}]}
                    # Changing controller-private metadata and all query answers must not change bytes.
                    changed = deepcopy(episode)
                    changed['settings'] = {'private': 'changed'}
                    changed['program_solution'] = 'PRIVATE'
                    changed['test'] = [dict(p, output=[[9]]) for p in changed['test']]
                    assert first_bytes(changed) == visible
                    changed['test'][1:] = [{'input': [[8]], 'output': [[7]]}]
                    assert first_bytes(changed) == visible
                    public_id = digest(visible)
                    public_path = out / 'public' / (public_id + '.json')
                    if public_path.exists():
                        assert public_path.read_bytes() == visible
                    else:
                        public_path.write_bytes(visible)
                    rival_records, survivors = [], []
                    for name in family.rivals(settings):
                        rival_program = family.rival_program(settings, name)
                        outputs = [execute(rival_program, p['input'],
                                           family.rival_reference(p['input'], settings, name))
                                   for p in episode['train'] + episode['test']]
                        rejects = [i for i, (result, pair) in enumerate(zip(outputs[:2], episode['train']))
                                   if result != pair['output']]
                        disagreement = [i for i, (result, pair) in enumerate(zip(outputs[2:], episode['test']))
                                        if result != pair['output']]
                        if not rejects:
                            survivors.append(name)
                            assert not disagreement, 'demo survivor disagrees on query'
                        if name.startswith('setting:'):
                            assert rejects, 'another declared setting survives demonstrations'
                        rival_records.append({'name': name, 'program': rival_program,
                                              'program_sha256': digest(rival_program.encode()),
                                              'demo_outputs': outputs[:2], 'query_outputs': outputs[2:],
                                              'rejected_by_demo_indices': rejects,
                                              'query_disagreement_indices': disagreement})
                    for pair in episode['test']:
                        execute(program, pair['input'], pair['output'])
                    query_facts = [facts(p['input']) for p in episode['test']]
                    assert query_facts[0]['shape'] == [6, 6] and query_facts[-1]['shape'] == [30, 30]
                    assert all(all(f['contacts'].values()) for f in query_facts)
                    assert all(query_facts[-1]['quadrant_nonzero']), '30x30 stress lacks broad content'
                    private = {'seed': seed, 'settings': settings, 'program': program,
                               'program_sha256': digest(program.encode()), 'train': episode['train'],
                               'test': episode['test'], 'sampling': episode['sampling'],
                               'rivals': rival_records, 'surviving_extra_rivals': survivors,
                               'public_id': public_id, 'query_facts': query_facts}
                    private_name = f'episode-{len(report["episodes"]):02d}.json'
                    write_json(out / 'private' / private_name, private)
                    report['episodes'].append({'seed': seed, 'settings': settings,
                        'public_id': public_id, 'private_path': 'private/' + private_name,
                        'declared_rivals': len(rival_records), 'surviving_extra_rivals': survivors,
                        'per_demo_rejections': [[r['name'] for r in rival_records if i in r['rejected_by_demo_indices']]
                                                for i in range(2)], 'query_facts': query_facts})
                    print(json.dumps({'seed': seed, 'settings': settings, 'executions': executions}), flush=True)
            # Additional count boundaries are generation checks, not duplicate Racket evidence.
            boundaries = []
            for demos in (3, 6):
                ep = checked_episode(family.generate(0, deepcopy(family.DEFAULT), demos, 4), demos, 4)
                boundaries.append({'seed': 0, 'settings': family.DEFAULT, 'demos': len(ep['train']),
                                   'queries': len(ep['test']), 'execution': 'not_reexecuted; count-only generation check'})
            report['demo_count_boundaries'] = boundaries
            successes, failures = [], []
            for seed in range(16):
                try:
                    checked_episode(family.generate(seed, deepcopy(family.DEFAULT), 2, 4), 2, 4)
                except (RuntimeError, ValueError) as error:
                    failures.append({'seed': seed, 'error': str(error)})
                else:
                    successes.append(seed)
            report['bounded_python_sampling'] = {'attempts': 16, 'successes': len(successes),
                'successful_seeds': successes, 'failures': failures,
                'scope': 'Python generation only, default setting, 2 demos/4 queries; other settings share inputs.'}
            witness_settings = {'tile_width': 2, 'order_mode': 'densest_prefix'}
            witness = []
            for kind, grid in [('leftmost_maximum_tie', [[1, 0, 2, 0, 3, 0], [0, 4, 0, 5, 0, 0]]),
                               ('unique_maximum', [[1, 0, 2, 3, 4, 0], [0, 0, 5, 0, 0, 0]])]:
                program = family.program(witness_settings)
                rival = family.rival_program(witness_settings, 'rightmost')
                result = execute(program, grid, family.reference(grid, witness_settings))
                alternative = execute(rival, grid, family.rival_reference(grid, witness_settings, 'rightmost'))
                witness.append({'kind': kind, 'input': grid, 'settings': witness_settings,
                    'scores': family.tile_scores(grid, 2), 'program': program, 'output': result,
                    'rival_name': 'rightmost', 'rival_program': rival, 'rival_output': alternative,
                    'distinguishes_rightmost': result != alternative})
            assert witness[0]['distinguishes_rightmost'] and not witness[1]['distinguishes_rightmost']
            write_json(out / 'private/teaching-witness.json', {'racket': identity,
                'scope': 'Small broad typed tile-grammar witness; not a sampled motif episode.', 'cases': witness})
            assert all(digest(p.read_bytes()) == binding[str(p.relative_to(ROOT))] for p in source_files), 'source changed during audit'
            report.update(status='passed', racket_evaluations=executions,
                          query_replay_evaluations=32, teaching_witness_path='private/teaching-witness.json',
                          first_turn_public_only=True, matched_inputs_across_settings=True)
        except BaseException as error:
            report.update(status='failed', racket_evaluations=executions,
                          failure={'type': type(error).__name__, 'message': str(error)})
            write_json(out / 'audit.json', report)
            raise
        finally:
            bridge.close()
    write_json(out / 'audit.json', report)
    print(json.dumps({'status': report['status'], 'episodes': len(report['episodes']),
                      'racket_evaluations': executions, 'negative_cases': len(report['negative_cases']),
                      'python_sampling_successes': len(successes), 'out': str(out)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    run(parser.parse_args().out)
