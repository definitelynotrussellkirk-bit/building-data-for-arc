"""Proposed, task-local odd-gap ownership variants; labels execute in Racket.

The canonical rule is retained byte-for-byte for center='preserve'.  No
production generator, approval, catalog entry, or training boundary is changed.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import re
import sys

TASK_ID = '613be474907a'
CENTER_VALUES = ('preserve', 'near', 'far')
ROOT = Path(__file__).resolve().parents[4]
# A normal library and the public task-test runtime both carry these helpers.
for candidate in (ROOT / 'shared/runtime', ROOT):
    if (candidate / 'reviewer_support.py').is_file():
        sys.path.insert(0, str(candidate))
        break
from reviewer_support import (canonical_pairs, canonical_path, load_selected_generator,
                              public_challenge_bytes, public_challenge_id)

GENERATOR, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def canonical_program():
    programs = {row['program_solution'] for row in
                (json.loads(line) for line in canonical_path(ROOT).read_text().splitlines())
                if row.get('task_id') == TASK_ID}
    if len(programs) != 1:
        raise ValueError('Expected one unambiguous canonical program for this prototype')
    program = programs.pop()
    if _sha(' '.join(program.split()).encode())[:12] != 'adc52fde010d':
        raise ValueError('Canonical authority changed; reassess this proposed extension')
    return program


def canonical_rule_hash():
    return _sha(' '.join(canonical_program().split()).encode())[:12]


def canonical_examples():
    seen, pairs = set(), []
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        digest = _sha(_json_bytes(pair['input']))
        if digest not in seen:
            seen.add(digest)
            pairs.append(pair)
    return pairs


def materialize_program(center='preserve'):
    if center not in CENTER_VALUES:
        raise ValueError(f'center must be one of {CENTER_VALUES}')
    program = canonical_program()
    if center == 'preserve':
        return program
    # Insert a middle-line case in each of the four existing spatial branches.
    # Geometry, half-gap extent, original cells, and branch precedence stay exact.
    roles = iter((('c', 'c1', 'c2'), ('c', 'c2', 'c1'),
                  ('r', 'c1', 'c2'), ('r', 'c2', 'c1')))
    def middle(match):
        axis, near, far = next(roles)
        owner = near if center == 'near' else far
        return f'((and (!= (* half 2) gl) (= {axis} (+ gs half))) {owner})\n                            (else v)'
    if program.count('(else v)') != 4:
        raise ValueError('Canonical branch structure changed')
    return re.sub(r'\(else v\)', middle, program)


def transform(grid, center='preserve'):
    """Python oracle for tests/rivals only; never supplies an emitted label."""
    if center not in CENTER_VALUES:
        raise ValueError('Unknown center policy')
    output = GENERATOR.rule_mirror(grid)
    facts, errors = GENERATOR._branch_facts(grid)
    if errors:
        raise ValueError('; '.join(errors))
    if center != 'preserve' and facts['gap'] % 2:
        line = facts['gap_start'] + facts['gap'] // 2
        color = facts['near_color' if center == 'near' else 'far_color']
        if facts['orientation'] == 'horizontal':
            for row in output:
                row[line] = color
        else:
            output[line] = [color] * len(output[0])
    return output


class RacketReference:
    """One protected bridge, with exact-program/input caching and fresh returns."""
    def __init__(self):
        from arc_repl.racket_bridge import RacketBridge
        self.bridge = RacketBridge(timeout=10, startup_timeout=30)
        self.identity = self.bridge.runtime_identity
        self.cache, self.calls = {}, 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.bridge.shutdown()

    def apply(self, program, grid):
        text = program.strip()
        if not text.startswith('(rule! ') or not text.endswith(')'):
            raise ValueError('Expected a complete rule! program')
        key = (_sha(program.encode()), _sha(_json_bytes(grid)))
        if key not in self.cache:
            body = text[len('(rule! '):-1].strip()
            if not body.startswith('(lambda '):
                raise ValueError('This task-local reference accepts lambda-form rules only')
            self.bridge.define_grid('g', grid)
            self.cache[key] = self.bridge.eval_text(f'({body} g)')
            self.calls += 1
        return copy.deepcopy(self.cache[key])


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _shortcut(grid, center, name):
    facts, errors = GENERATOR._branch_facts(grid)
    if errors:
        raise ValueError('; '.join(errors))
    if name == 'identity':
        return copy.deepcopy(grid)
    if name in ('horizontal_only', 'vertical_only') and facts['orientation'] != name.split('_')[0]:
        return copy.deepcopy(grid)
    if name == 'vertical_first':
        return _transpose(transform(_transpose(grid), center))
    output = transform(grid, center)
    if name == 'bounded_span':
        boxes = facts['boxes']
        axis = 0 if facts['orientation'] == 'horizontal' else 1
        lo, hi = min(b[axis] for b in boxes), max(b[axis + 2] for b in boxes)
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if not lo <= (row if axis == 0 else col) <= hi:
                    output[row][col] = grid[row][col]
    if name == 'lower_color_near' and facts['near_color'] > facts['far_color']:
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                along = col if facts['orientation'] == 'horizontal' else row
                if facts['gap_start'] <= along <= facts['gap_end']:
                    value = output[row][col]
                    if value == facts['near_color']:
                        output[row][col] = facts['far_color']
                    elif value == facts['far_color']:
                        output[row][col] = facts['near_color']
    return output


def assess_teaching(train, query_inputs, center, reference):
    """Select rivals using demonstration pairs ONLY, then compare predictions.

    Query answers are not accepted as arguments. Agreement of this finite,
    declared hypothesis set is evidence, not a proof of general identifiability.
    """
    programs = {value: materialize_program(value) for value in CENTER_VALUES}
    consistent = [value for value in CENTER_VALUES if all(
        reference.apply(programs[value], pair['input']) == pair['output'] for pair in train)]
    names = ('identity', 'horizontal_only', 'vertical_only', 'vertical_first',
             'bounded_span', 'lower_color_near')
    shortcut_rows = {}
    for name in names:
        mismatches = [i for i, pair in enumerate(train)
                      if _shortcut(pair['input'], center, name) != pair['output']]
        shortcut_rows[name] = {'fits_demonstrations': not mismatches,
                               'first_demo_counterexample': mismatches[0] if mismatches else None}
    queries = []
    for index, grid in enumerate(query_inputs):
        answers = [_json_bytes(reference.apply(programs[value], grid)) for value in consistent]
        answers.extend(_json_bytes(_shortcut(grid, center, name)) for name in names
                       if shortcut_rows[name]['fits_demonstrations'])
        queries.append({'query_index': index, 'input_sha256': _sha(_json_bytes(grid)),
                        'distinct_surviving_predictions': len(set(answers)),
                        'identifiable': bool(consistent) and len(set(answers)) == 1})
    return {'scope': 'finite declared rivals; selection uses demonstrations only',
            'consistent_settings': consistent, 'shortcut_rivals': shortcut_rows,
            'queries': queries}


def _scene(rng, orientation, odd, height, width, reverse, diagonal, large_gap):
    length = width if orientation == 'horizontal' else height
    cross = height if orientation == 'horizontal' else width
    choices = [g for g in range(3, length - 1) if bool(g % 2) == odd]
    if large_gap:
        choices = [g for g in choices if g >= length // 2] or choices
    gap = rng.choice(choices)
    first_len = rng.randint(1, min(2, length - gap - 1))
    second_len = rng.randint(1, min(2, length - gap - first_len))
    start = rng.randint(0, length - gap - first_len - second_len)
    second = start + first_len + gap
    background, a, b = rng.sample(range(10), 3)
    near, far = sorted((a, b), reverse=reverse)
    if diagonal and orientation == 'horizontal':
        cross_a, cross_b = (1, 1), (cross - 2, cross - 2)
    else:
        pivot = rng.randint(1, cross - 2)
        cross_a = GENERATOR._interval_containing(cross, pivot, rng)
        cross_b = GENERATOR._interval_containing(cross, pivot, rng)
    grid = [[background] * width for _ in range(height)]
    for along, extent, span, color in ((start, first_len, cross_a, near),
                                      (second, second_len, cross_b, far)):
        for x in range(along, along + extent):
            for y in range(span[0], span[1] + 1):
                row, col = (y, x) if orientation == 'horizontal' else (x, y)
                grid[row][col] = color
    errors = GENERATOR.self_check(grid)
    if errors:
        raise ValueError('Prototype sampled an invalid input: ' + '; '.join(errors))
    return grid


def generate_episode(seed, *, center='preserve', n_train=4, n_test=4,
                     height=None, width=None, reference=None):
    if type(seed) is not int or center not in CENTER_VALUES:
        raise ValueError('An integer seed and declared center policy are required')
    for name, value, low in (('n_train', n_train, 2), ('n_test', n_test, 1)):
        if type(value) is not int or not low <= value <= 32:
            raise ValueError(f'{name} must be an integer in {low}..32')
    for name, value in (('height', height), ('width', width)):
        if value is not None and (type(value) is not int or not 7 <= value <= 30):
            raise ValueError(f'{name} must be an integer in 7..30')
    if reference is None:
        with RacketReference() as owned:
            return generate_episode(seed, center=center, n_train=n_train, n_test=n_test,
                                    height=height, width=width, reference=owned)
    rng = random.Random(seed)
    grids, seen = [], set()
    for position in range(n_train + n_test):
        query = position >= n_train
        local = position - n_train if query else position
        orientation = 'horizontal' if local % 2 == 0 else 'vertical'
        odd = local % 4 < 2
        demo_shapes = ((9, 13), (13, 9), (9, 14), (14, 9))
        query_shapes = ((30, 30), (29, 23), (15, 27), (27, 15))
        h, w = (query_shapes if query else demo_shapes)[local % 4]
        h, w = height if height is not None else h, width if width is not None else w
        for attempt in range(128):
            grid = _scene(rng, orientation, odd, h, w, bool(local % 2),
                          local % 4 == 0, query and max(h, w) > 20)
            digest = _sha(_json_bytes(grid))
            if digest not in seen:
                seen.add(digest); grids.append(grid); break
        else:
            raise ValueError('Distinct input budget exhausted; refusing a short episode')
    program = materialize_program(center)
    pairs = [{'input': grid, 'output': reference.apply(program, grid)} for grid in grids]
    if any(pair['output'] != transform(pair['input'], center) for pair in pairs):
        raise AssertionError('Python oracle disagrees with executed Racket')
    train, test = pairs[:n_train], pairs[n_train:]
    teaching = assess_teaching(train, [pair['input'] for pair in test], center, reference)
    if not all(row['identifiable'] for row in teaching['queries']):
        raise ValueError('Demonstrations leave a declared rival with a different query prediction')
    return {'train': train, 'test': test, 'private': {
        'status': 'proposed prototype; not production approval or training admission',
        'task_id': TASK_ID, 'seed': seed, 'parameters': {'center': center},
        'counts': {'train': n_train, 'test': n_test},
        'program': program, 'program_sha256': _sha(program.encode()),
        'canonical_rule_hash': canonical_rule_hash(),
        'generator_sha256': GENERATOR_SHA256,
        'prototype_sha256': _sha(Path(__file__).read_bytes()),
        'canonical_file_sha256': _sha(canonical_path(ROOT).read_bytes()),
        'input_sha256': [_sha(_json_bytes(grid)) for grid in grids],
        'labels': 'executed through matching Racket program for every pair',
        'python_oracle_checks': len(pairs), 'teaching': teaching}}


def write_batch(episodes, out):
    """Write only visible-byte hashes to public names; private maps stay private."""
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    records, seen = [], set()
    for episode in episodes:
        payload = public_challenge_bytes(episode)
        public_id = public_challenge_id(episode)
        if public_id in seen:
            raise ValueError('duplicate visible payload in batch')
        seen.add(public_id)
        records.append((public_id, payload, episode))
    if not records:
        raise ValueError('Cannot write an empty batch')
    records.sort(key=lambda row: row[0])
    (out / 'public').mkdir(parents=True)
    (out / 'private/programs').mkdir(parents=True)
    manifest = {'schema': 'bridge-parameter-prototype-v1', 'episodes': []}
    for public_id, payload, episode in records:
        (out / 'public' / f'{public_id}.json').write_bytes(payload)
        private_bytes = _json_bytes(episode)
        (out / 'private' / f'{public_id}.json').write_bytes(private_bytes)
        metadata = episode.get('private', {})
        program = metadata.get('program')
        if isinstance(program, str):
            (out / 'private/programs' / f'{_sha(program.encode())}.rkt').write_text(program)
        manifest['episodes'].append({'public_id': public_id,
            'private_sha256': _sha(private_bytes), 'parameters': metadata.get('parameters'),
            'seed': metadata.get('seed')})
    (out / 'private/manifest.json').write_bytes(_json_bytes(manifest))
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--center', choices=(*CENTER_VALUES, 'all'), default='preserve')
    parser.add_argument('--train', type=int, default=4)
    parser.add_argument('--test', type=int, default=4)
    parser.add_argument('--height', type=int)
    parser.add_argument('--width', type=int)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    settings = CENTER_VALUES if args.center == 'all' else (args.center,)
    with RacketReference() as reference:
        episodes = [generate_episode(args.seed, center=center, n_train=args.train,
            n_test=args.test, height=args.height, width=args.width, reference=reference)
            for center in settings]
        manifest = write_batch(episodes, args.out)
        receipt = {'schema': 'bridge-prototype-execution-v1', 'status': 'pass',
            'episodes': len(episodes), 'demonstrations': sum(len(e['train']) for e in episodes),
            'queries': sum(len(e['test']) for e in episodes),
            'racket_executions': reference.calls, 'runtime': reference.identity,
            'all_queries_identifiable_within_declared_rivals': True,
            'public_ids': [row['public_id'] for row in manifest['episodes']],
            'prototype_sha256': _sha(Path(__file__).read_bytes()),
            'generator_sha256': GENERATOR_SHA256,
            'canonical_rule_hash': canonical_rule_hash()}
        (args.out / 'private/execution.json').write_bytes(_json_bytes(receipt))
    print(json.dumps({key: value for key, value in receipt.items() if key != 'runtime'}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
