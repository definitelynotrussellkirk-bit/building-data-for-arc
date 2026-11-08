"""Source-bound, Racket-labelled cyclic lesson probe for exact override cases.

This supplements the shared census, whose CLI does not accept overrides. It
scores raw consecutive generator draws (no production rejection/resampling),
retains all inputs and authority receipts, and checks every query rotation.
Run through run_with_racket.py; never use this authoring tool during a solve.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import find_root


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', default='b86607f34b8b')
    parser.add_argument('--case', action='append', help='JSON override object; repeatable')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--starts', type=int, default=6)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output already exists; choose a new report path')
    if args.starts < 1:
        parser.error('--starts must be positive')
    cases = [json.loads(case) for case in args.case] if args.case else [{'n_colors': n} for n in (3, 4, 5)]
    if any(not isinstance(case, dict) for case in cases):
        parser.error('--case must be a JSON object')
    root = find_root(__file__)
    catalog = Catalog(root)
    description = catalog.describe(args.task)
    source = root / description['generator']
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location('override_lesson_subject', source)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    declarations = [(space, name, fn)
                    for space in ('SEMANTIC_RIVALS', 'LESSON_COMPETITORS', 'CANONICAL_SHORTCUTS')
                    for name, fn in getattr(generator, space, {}).items()]
    if not declarations:
        raise ValueError('no declared rivals; this cannot certify lesson evidence')
    report = {'schema': 'override-lesson-probe-v1', 'task_id': args.task,
              'generator_sha256': before, 'seed': args.seed, 'cases': cases,
              'sampling': 'raw consecutive calls, no rejection/resampling; every 3-demo/1-query rotation',
              'command': {'cwd': 'repo', 'argv': [sys.executable, *sys.argv]},
              'status': 'running', 'draws': [], 'authority_batches': [], 'lessons': [], 'errors': []}
    args.out.parent.mkdir(parents=True, exist_ok=True)

    def checkpoint():
        args.out.write_text(json.dumps(report, indent=2) + '\n')

    grids = {}
    groups = []
    for case in cases:
        for band in ('easy', 'medium', 'hard'):
            indexes = []
            for index in range(args.starts + 3):
                grid = generator.generate(args.seed, index, difficulty=band, **case)
                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    raise ValueError(f'generator validator rejected {case}/{band}/{index}: {errors}')
                key = digest(grid)
                grids.setdefault(key, grid)
                indexes.append(key)
                report['draws'].append({'case': case, 'band': band, 'sample_index': index, 'input_sha256': key})
            groups.append((case, band, indexes))
    checkpoint()
    labels = {}
    keys = list(grids)
    for offset in range(0, len(keys), 64):
        chunk = keys[offset:offset + 64]
        receipt = catalog.apply(args.task, [grids[key] for key in chunk], timeout=180)
        report['authority_batches'].append(receipt)
        if receipt['generator_sha256'] != before or not receipt['rule_hash_matches_catalog']:
            raise ValueError('source/authority changed during probe')
        for key, row in zip(chunk, receipt['results'], strict=True):
            if row.get('output') is None:
                raise ValueError(f'Racket failed on input {key}')
            labels[key] = row['output']
        checkpoint()
    predictions = {}
    total_rotations = ambiguous = hook_errors = 0
    for case, band, indexes in groups:
        for start in range(args.starts):
            window = indexes[start:start + 4]
            outcomes = []
            for query in range(4):
                demos = [index for index in range(4) if index != query]
                statuses = {}
                for space, name, rival in declarations:
                    matches = []
                    for key in window:
                        cache_key = (space, name, key)
                        if cache_key not in predictions:
                            predictions[cache_key] = rival(copy.deepcopy(grids[key]))
                        matches.append(predictions[cache_key] == labels[key])
                    fits = all(matches[index] for index in demos)
                    statuses[f'{space}.{name}'] = ('ambiguous' if fits and not matches[query]
                                                 else 'survived_all' if fits else 'refuted')
                bad = [name for name, status in statuses.items() if status == 'ambiguous']
                reasons = []
                hook = getattr(generator, 'lesson_identifiable', None)
                if hook:
                    pairs = [{'input': grids[key], 'output': labels[key]} for key in window]
                    reasons = hook([pairs[index] for index in demos], pairs[query])
                    if not isinstance(reasons, list) or any(not isinstance(reason, str) for reason in reasons):
                        raise ValueError('lesson hook must return list[str]')
                total_rotations += 1
                ambiguous += bool(bad)
                hook_errors += bool(reasons)
                outcomes.append({'query_index': query, 'demo_indices': demos,
                                 'statuses': statuses, 'ambiguous_rivals': bad, 'hook_reasons': reasons})
            report['lessons'].append({'case': case, 'band': band, 'start': start,
                                      'input_hashes': window, 'rotations': outcomes})
    if hashlib.sha256(source.read_bytes()).hexdigest() != before:
        raise ValueError('generator changed during probe')
    report['summary'] = {'draws': len(report['draws']), 'unique_inputs': len(grids),
                         'windows': len(report['lessons']), 'query_rotations': total_rotations,
                         'ambiguous_rotations': ambiguous, 'hook_warning_rotations': hook_errors,
                         'distinct_rival_names': len({name for space, name, fn in declarations})}
    report['status'] = 'no_ambiguity_found' if not ambiguous and not hook_errors else 'findings'
    checkpoint()
    print(json.dumps({'status': report['status'], **report['summary'], 'out': str(args.out)}))
    return int(bool(ambiguous or hook_errors))


if __name__ == '__main__':
    raise SystemExit(main())
