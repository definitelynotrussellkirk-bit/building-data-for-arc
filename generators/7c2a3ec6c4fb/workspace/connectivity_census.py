#!/usr/bin/env python3
"""Independent 4/8-component census with optional real-Racket label verification.

Uses the generator only for inputs and validation, not to derive Python labels.
Every failure is retained. Public canonical pairs and generated inputs only;
never opens a solve episode or its masked answers.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK_ID = '7c2a3ec6c4fb'
sys.path.insert(0, str(ROOT / 'shared/runtime'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def components(grid, *, diagonal=True):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    crops = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        todo, cells = [start], {start}
        while todo:
            r, c = todo.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1),
                           (-1, -1), (-1, 1), (1, -1), (1, 1)):
                if not diagonal and dr and dc:
                    continue
                p = (r + dr, c + dc)
                if p in unseen:
                    unseen.remove(p)
                    cells.add(p)
                    todo.append(p)
        r0, r1 = min(p[0] for p in cells), max(p[0] for p in cells)
        c0, c1 = min(p[1] for p in cells), max(p[1] for p in cells)
        crops.append(tuple(tuple(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]))
    return crops


def predict(grid, *, diagonal):
    crops = components(grid, diagonal=diagonal)
    counts = Counter(crops)
    return [list(row) for row in next((p for p in crops if counts[p] == 1), ())]


def load_generator(path):
    spec = importlib.util.spec_from_file_location('connectivity_census_generator', path)
    if spec is None or spec.loader is None:
        raise ValueError(f'Cannot import {path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(*, generator_path, samples, seed, racket=False, command=None):
    if samples < 1:
        raise ValueError('samples must be positive')
    gen = load_generator(generator_path)
    with (ROOT / 'shared/data/canonical/puzzles.jsonl').open() as f:
        rule = next(json.loads(line) for line in f if json.loads(line).get('task_id') == TASK_ID)
    code = rule['program_solution']
    source = {'generator_sha256': sha(generator_path),
              'generator_version': gen.VERSION,
              'rule_sha256': hashlib.sha256(code.encode()).hexdigest(),
              'prelude_sha256': sha(ROOT / 'shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt')}
    report = {'schema': 'arcpuzzles-connectivity-census-v1', 'task_id': TASK_ID,
              **source, 'seed': seed, 'sample_index_range': [0, samples - 1],
              'attempted': samples, 'successful': 0, 'racket_checked': 0,
              'strata': {}, 'failures': [], 'counterexamples': [], 'canonical': []}
    bridge = None
    if racket:
        from arc_repl.racket_bridge import RacketBridge
        bridge = RacketBridge(max_calls_before_restart=128)
        # This task has a standard Racket rule! lambda, with no custom syntax.
        # Lexically bind rule! instead of relying on staged scripts imports.
        wrapped = f"(let ([rule! (lambda (f) f)]) {code})"

    def label(grid):
        if bridge is None:
            return None
        literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
        return bridge.eval_text(f'({wrapped} {literal})')

    seen = set()
    counts = Counter()
    try:
        for split in ('train', 'test'):
            pairs = rule.get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            for index, pair in enumerate(pairs):
                pred = predict(pair['input'], diagonal=False)
                actual = label(pair['input'])
                entry = {'split': split, 'index': index,
                         'orthogonal_matches': pred == pair['output'],
                         'racket_checked': bridge is not None,
                         'racket_matches': actual == pair['output'] if bridge else None}
                report['canonical'].append(entry)
                if bridge and actual != pair['output']:
                    report['failures'].append({'kind': 'canonical_mismatch', **entry})
        witnessed = set()
        for index in range(samples):
            difficulty = ('easy', 'medium', 'hard')[(index // 3) % 3]
            profile = ('color_swap', 'shape_shift', 'mixed_signature')[index % 3]
            key = f'{difficulty}/{profile}'
            bucket = report['strata'].setdefault(key, {'attempted': 0, 'successful': 0,
                           'diagonal_answers': 0, 'orthogonal_rival_failures': 0})
            bucket['attempted'] += 1
            params = {'seed': seed, 'sample_index': index, 'difficulty': difficulty,
                      'overrides': {'pattern_profile': profile}}
            try:
                grid = gen.generate(seed, index, difficulty=difficulty, pattern_profile=profile)
                errors = gen.self_check(grid)
                if errors:
                    raise ValueError(f'validator: {errors}')
                crops = components(grid, diagonal=True)
                singleton = [p for p, n in Counter(crops).items() if n == 1]
                if len(singleton) != 1:
                    raise ValueError(f'expected one singleton, got {len(singleton)}')
                expected = [list(row) for row in singleton[0]]
                rival = predict(grid, diagonal=False)
                actual = label(grid)
                if bridge:
                    report['racket_checked'] += 1
                    if actual != expected:
                        report['failures'].append({'kind': 'racket_mismatch', **params,
                            'input': grid, 'python_output': expected, 'actual_racket_output': actual})
                diagonal = len(components(expected, diagonal=False)) > 1
                wrong = rival != expected
                bucket['successful'] += 1
                bucket['diagonal_answers'] += int(diagonal)
                bucket['orthogonal_rival_failures'] += int(wrong)
                report['successful'] += 1
                counts['diagonal_answers'] += int(diagonal)
                counts['orthogonal_rival_failures'] += int(wrong)
                seen.add(json.dumps(grid))
                if wrong and key not in witnessed:
                    witnessed.add(key)
                    report['counterexamples'].append({'task_id': TASK_ID, **source, **params,
                        'input': grid, 'actual_racket_output': actual, 'rival_output': rival,
                        'independent_python_output': expected, 'validator_errors': errors,
                        'in_documented_domain': True, 'command': command,
                        'racket_verified': bridge is not None})
            except Exception as exc:
                report['failures'].append({'kind': 'exception', **params,
                                          'error': f'{type(exc).__name__}: {exc}'})
    finally:
        if bridge is not None:
            bridge.close()
    report.update(counts)
    report['unique_inputs'] = len(seen)
    report['failure_count'] = len(report['failures'])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generator', type=Path, default=Path(__file__).resolve().parents[1] / 'generator.py')
    parser.add_argument('--samples', type=int, default=1800)
    parser.add_argument('--seed', default='connectivity-census-v1')
    parser.add_argument('--racket', action='store_true')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    command = {'cwd': 'repo', 'argv': ['python3', *sys.argv]}
    report = run(generator_path=args.generator, samples=args.samples, seed=args.seed,
                 racket=args.racket, command=command)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: report[k] for k in ('generator_version', 'attempted', 'successful',
              'unique_inputs', 'racket_checked', 'failure_count', 'diagonal_answers',
              'orthogonal_rival_failures')}, sort_keys=True))
    return int(bool(report['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
