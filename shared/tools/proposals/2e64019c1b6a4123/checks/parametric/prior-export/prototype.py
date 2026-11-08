"""Task-local proposed direction parameter; no production integration or approval."""
from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import sys
import importlib.util
import types

ROOT = Path(__file__).resolve().parents[4]
DEPENDENCIES = ROOT / 'shared/runtime' if (ROOT / 'shared/runtime').is_dir() else ROOT
if str(DEPENDENCIES) not in sys.path:
    sys.path.insert(0, str(DEPENDENCIES))
# Repository layout stores runtime script modules in shared/tools. Exported
# runtimes already expose scripts; supply only the missing package search path.
if importlib.util.find_spec('scripts') is None and (ROOT / 'shared/tools').is_dir():
    scripts = types.ModuleType('scripts')
    scripts.__path__ = [str(ROOT / 'shared/tools')]
    scripts.__spec__ = importlib.util.spec_from_loader('scripts', loader=None, is_package=True)
    sys.modules['scripts'] = scripts
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, canonical_path, load_selected_generator

TASK_ID = '45922a9666b2'
DIRECTIONS = ('right', 'left')
PUBLISHED_PROFILES = ('profile_13x14_mixed', 'profile_12x13_light',
                      'profile_13x15_dense', 'profile_13x13_edge')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _direction(direction):
    if direction not in DIRECTIONS:
        raise ValueError('turn_direction must be right or left')
    return direction


@lru_cache(maxsize=1)
def selected_generator():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


@lru_cache(maxsize=1)
def canonical_rule():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
            if line.strip()]
    programs = {row['program_solution'] for row in rows if row.get('task_id') == TASK_ID}
    if len(programs) != 1:
        raise ValueError('Expected one exact canonical authority program')
    return programs.pop()


def canonical_examples():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def materialize_rule(turn_direction='right'):
    """Right is byte-exact authority; reflection conjugates only horizontal motion."""
    _direction(turn_direction)
    canonical = canonical_rule()
    if turn_direction == 'right':
        return canonical
    return '(rule! (lambda (g) (flip-lr (' + wrap_rule(canonical) + ' (flip-lr g)))))'


def evaluate(bridge, program, grid):
    """The single source of labels is execution of the exact supplied Racket."""
    bridge.define_grid('__walker_input', grid)
    return bridge.eval_text('(' + wrap_rule(program) + ' __walker_input)')


def reflect(grid):
    return [row[::-1] for row in grid]


def parameters_for_seed(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    return {'turn_direction': DIRECTIONS[seed % len(DIRECTIONS)]}


def sample_input(seed, sample_index, turn_direction='right', *, difficulty='medium', **overrides):
    _direction(turn_direction)
    generator = selected_generator()
    grid = generator.generate(seed, sample_index, difficulty=difficulty, **overrides)
    errors = generator.self_check(grid)
    if errors:
        raise ValueError('Invalid canonical-orientation input: ' + '; '.join(errors))
    return reflect(grid) if turn_direction == 'left' else grid


def make_episode(seed, *, bridge, turn_direction=None, n_train=3, n_test=2,
                 difficulty='medium', **overrides):
    """Fix one direction, reject ambiguous teaching sets, keep query answers private."""
    if type(n_train) is not int or type(n_test) is not int or n_train < 1 or n_test < 1:
        raise ValueError('Need at least one demonstration and one query')
    direction = parameters_for_seed(seed)['turn_direction'] if turn_direction is None else _direction(turn_direction)
    programs = {value: materialize_rule(value) for value in DIRECTIONS}
    pairs, indices, rivals, seen = [], [], [], set()
    # A distinguishing first demo makes every accepted episode identifiable.
    # Bounded rejection fails explicitly; it never emits an ambiguous episode.
    for index in range(256):
        grid = sample_input(seed, index, direction, difficulty=difficulty, **overrides)
        key = json.dumps(grid, separators=(',', ':'))
        if key in seen:
            continue
        outputs = {value: evaluate(bridge, program, grid) for value, program in programs.items()}
        if not pairs and outputs['right'] == outputs['left']:
            continue
        seen.add(key)
        pairs.append({'input': grid, 'output': outputs[direction]})
        rivals.append(outputs)
        indices.append(index)
        if len(pairs) == n_train + n_test:
            break
    if len(pairs) != n_train + n_test:
        raise ValueError('Could not construct a unique identifiable episode within 256 proposals')
    consistent = [value for value in DIRECTIONS
                  if all(rivals[i][value] == pairs[i]['output'] for i in range(n_train))]
    if consistent != [direction]:
        raise AssertionError('Visible demonstrations do not identify the chosen direction')
    return {'schema': 'walker-direction-prototype-v1', 'task_id': TASK_ID,
            'seed': seed, 'parameters': {'turn_direction': direction},
            'difficulty': difficulty, 'overrides': overrides, 'accepted_sample_indices': indices,
            'program': programs[direction], 'program_sha256': digest(programs[direction].encode()),
            'identifiable': True, 'declared_rivals': list(DIRECTIONS),
            'consistent_directions': consistent,
            'rival_mismatching_demo_indices': {value: [i for i in range(n_train)
                if rivals[i][value] != pairs[i]['output']] for value in DIRECTIONS},
            'train': pairs[:n_train], 'test': pairs[n_train:]}


def public_challenge(episode):
    # Round trip produces independent data, so callers cannot mutate private labels.
    return json.loads(json.dumps({'train': episode['train'],
                                 'test': [{'input': p['input']} for p in episode['test']]}))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    programs = {value: materialize_rule(value) for value in DIRECTIONS}
    for value, program in programs.items():
        (output / (value + '.rkt')).write_text(program + '\n')
    canonical_checks, profile_checks, episodes = [], [], []
    with RacketBridge() as bridge:
        runtime = bridge.runtime_identity
        for pair in canonical_examples():
            actual = evaluate(bridge, programs['right'], pair['input'])
            if actual != pair['output']:
                raise AssertionError('Canonical label mismatch')
            canonical_checks.append({'variant': pair['variant'], 'split': pair['split'],
                                     'pair_index': pair['pair_index'], 'matched': True})
        for layout in ('canonical', 'procedural'):
            for profile in PUBLISHED_PROFILES:
                grid = sample_input(42, 0, 'right', scene_profile=profile, route_layout=layout)
                canonical = evaluate(bridge, canonical_rule(), grid)
                right = evaluate(bridge, programs['right'], grid)
                left_reflected = evaluate(bridge, programs['left'], reflect(grid))
                if right != canonical or left_reflected != reflect(canonical):
                    raise AssertionError('Generated default equivalence or reflection mismatch')
                profile_checks.append({'scene_profile': profile, 'route_layout': layout,
                                       'seed': 42, 'sample_index': 0, 'matched': True})
        # A lawful canonical-orientation input on which only the semantic setting changes.
        witness_input = sample_input(42, 0, 'right', scene_profile=PUBLISHED_PROFILES[0], route_layout='canonical')
        witness = {'input': witness_input,
                   'outputs': {value: evaluate(bridge, program, witness_input)
                               for value, program in programs.items()},
                   'canonical_input_errors': selected_generator().self_check(witness_input)}
        if witness['outputs']['right'] == witness['outputs']['left']:
            raise AssertionError('Required direction witness did not distinguish settings')
        write_json(output / 'distinguishing-witness.json', witness)
        for seed in (0, 1):
            episode = make_episode(seed, bridge=bridge)
            write_json(output / f'private-episode-{seed}.json', episode)
            write_json(output / f'challenge-{seed}.json', public_challenge(episode))
            episodes.append({'seed': seed, 'parameters': episode['parameters'],
                             'train_count': len(episode['train']), 'test_count': len(episode['test']),
                             'identifiable': episode['identifiable'],
                             'consistent_directions': episode['consistent_directions'],
                             'rival_mismatching_demo_indices': episode['rival_mismatching_demo_indices']})
    generator, source, source_hash = load_selected_generator(TASK_ID, root=ROOT)
    receipt = {'schema': 'walker-direction-prototype-receipt-v1', 'status': 'prototype',
               'task_id': TASK_ID, 'parameter': {'name': 'turn_direction', 'allowed': list(DIRECTIONS), 'canonical': 'right'},
               'generator_version': generator.VERSION, 'generator_rule_hash': generator.RULE_HASH,
               'generator_sha256': source_hash, 'prototype_sha256': digest(Path(__file__).read_bytes()),
               'canonical_ledger_sha256': digest(canonical_path(ROOT).read_bytes()),
               'program_sha256': {value: digest(program.encode()) for value, program in programs.items()},
               'command_argv': sys.argv, 'cwd': str(Path.cwd()), 'runtime': runtime,
               'canonical_pairs_checked': canonical_checks, 'profile_layout_checks': profile_checks,
               'counts': {'canonical_pairs': len(canonical_checks), 'profile_layouts': len(profile_checks),
                          'episodes': len(episodes), 'episode_pairs': sum(e['train_count'] + e['test_count'] for e in episodes),
                          'same_input_distinguishing_witnesses': 1},
               'episodes': episodes,
               'limitations': ['Task-local proposed extension, not production-integrated or approved.',
                               'Finite evidence covers two episode seeds and the two declared direction rivals only.',
                               'Mirrored left inputs preserve canonical roles in reversed horizontal order; they are not canonical-profile production inputs.',
                               'Input orientation can correlate with direction; rival checks establish visible output distinction, not absence of every shortcut.',
                               'Prototype evidence exercises the four published scene profiles; no larger-grid coverage claim.'],
               'artifact_sha256': {p.name: digest(p.read_bytes()) for p in sorted(output.iterdir())
                                   if p.is_file() and (p.suffix == '.rkt' or p.name.startswith(('challenge-', 'private-episode-', 'distinguishing-witness')))}}
    write_json(output / 'receipt.json', receipt)
    print(json.dumps({'status': 'prototype', 'counts': receipt['counts'], 'output': str(output)}))


if __name__ == '__main__':
    main()
