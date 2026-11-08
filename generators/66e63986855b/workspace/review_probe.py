#!/usr/bin/env python3
"""Replayable row-front curriculum census, without private scripts imports.

From the extracted packet:
  python3 run_with_racket.py python3 generators/66e63986855b/workspace/review_probe.py \
    --seed-count 64 --axis-sweep --racket-samples 64 --out ../checks/final-probe.json

Exhausts all six default schedule starts per seed, all four holdouts, and
optionally every exact-control tuple. Fast window labels use rule_mirror;
--racket-samples supplies an independent public Catalog.apply parity receipt.
The separate shared lesson-census exercises the production sampler with Racket
labels. This tool does NOT claim its overlapping raw windows are independent
production lessons or that three declared rules exhaust all possible rivals.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys
import time

from reviewer_support import canonical_pairs, find_root

TASK = '66e63986855b'
ATTRIBUTES = ('LESSON_COMPETITORS', 'SEMANTIC_RIVALS', 'CANONICAL_SHORTCUTS')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_generator(root):
    path = root / 'generators' / TASK / 'generator.py'
    if not path.exists():
        path = root / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py'
    spec = importlib.util.spec_from_file_location('rowfront_probe_subject', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def collect_rivals(module):
    result = {}
    for attribute in ATTRIBUTES:
        declaration = getattr(module, attribute, {})
        if not isinstance(declaration, dict):
            raise ValueError(f'{attribute} must be a dictionary')
        for name, function in declaration.items():
            if not isinstance(name, str) or not callable(function):
                raise ValueError(f'Invalid declaration {attribute}:{name}')
            result[f'{attribute}:{name}'] = function
    if not result:
        raise ValueError('No declared rivals: no identifiability evidence is possible')
    return result


def score(rivals, pairs, query_index, cache):
    statuses = {}
    for name, rival in rivals.items():
        predictions = []
        for pair in pairs:
            key = (name, pair['input_sha256'])
            if key not in cache:
                cache[key] = rival(deepcopy(pair['input']))
            predictions.append(cache[key])
        fits = all(predictions[i] == pair['output'] for i, pair in enumerate(pairs) if i != query_index)
        agrees = predictions[query_index] == pairs[query_index]['output']
        statuses[name] = 'refuted' if not fits else ('survived_all' if agrees else 'ambiguous')
    return statuses


def run(args):
    started = time.monotonic()
    root = find_root(__file__)
    module, source = load_generator(root)
    rivals = collect_rivals(module)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    report = {
        'schema': 'rowfront-review-probe-v1', 'task_id': TASK,
        'generator_sha256': source_hash, 'rule_hash': module.RULE_HASH,
        'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
        'seed_range': [args.seed_base, args.seed_base + args.seed_count - 1],
        'bands': ['easy', 'medium', 'hard'], 'sample_indices': [0, 8],
        'window_starts': list(range(6)), 'query_positions': list(range(4)),
        'label_authority': 'generator.rule_mirror; independent Racket sample recorded separately',
        'rivals': list(rivals), 'canonical_rival_fit': {},
        'draws': [], 'failures': [], 'per_band': {},
        'summary': {'draws': 0, 'unique_inputs': 0, 'windows': 0,
                    'rotations': 0, 'ambiguous_windows': 0,
                    'ambiguous_rotations': 0, 'hook_disagreements': 0},
        'limits': ['Finite declared-rival evidence, not a proof of universal induction.',
                   'Raw consecutive draws are not production-sampler accepted draws.',
                   'The six overlapping windows and their rotations are not independent samples.',
                   'The exact-axis sweep uses one seed/index per tuple, not every possible seed.',
                   'Changing overrides or dropping/reordering draws removes the schedule guarantee.'],
    }
    canonical = canonical_pairs(TASK, root=root)
    for name, rival in rivals.items():
        fits = sum(rival(deepcopy(pair['input'])) == pair['output'] for pair in canonical)
        report['canonical_rival_fit'][name] = {'pairs': len(canonical), 'fits': fits}
    unique = set()
    for band in report['bands']:
        counts = Counter()
        for seed in range(args.seed_base, args.seed_base + args.seed_count):
            cache, pairs = {}, []
            for index in range(9):
                grid = module.generate(seed, index, difficulty=band)
                errors = module.self_check(grid)
                if errors:
                    raise ValueError(f'Invalid generated input {band}/{seed}/{index}: {errors}')
                output = module.rule_mirror(grid)
                record = {'seed': seed, 'sample_index': index, 'band': band,
                          'input_sha256': digest(grid), 'output_sha256': digest(output),
                          'input': grid, 'output': output}
                pairs.append(record)
                report['draws'].append(record)
                unique.add(record['input_sha256'])
                counts['draws'] += 1
            for start in range(6):
                window = pairs[start:start+4]
                counts['windows'] += 1
                for query in range(4):
                    statuses = score(rivals, window, query, cache)
                    ambiguous = any(status == 'ambiguous' for status in statuses.values())
                    counts['rotations'] += 1
                    counts['ambiguous_rotations'] += int(ambiguous)
                    if query == 3:
                        counts['ambiguous_windows'] += int(ambiguous)
                    demos = [p for i, p in enumerate(window) if i != query]
                    reasons = module.lesson_identifiable(demos, {'input': window[query]['input']})
                    mismatch = bool(reasons) != ambiguous
                    counts['hook_disagreements'] += int(mismatch)
                    if ambiguous or mismatch:
                        report['failures'].append({'band': band, 'seed': seed, 'start': start,
                            'query_index': query, 'pairs': window,
                            'rival_statuses': statuses, 'hook_reasons': reasons})
        report['per_band'][band] = dict(counts)
        for name in counts:
            report['summary'][name] += counts[name]
        print(f'{band}: {counts["windows"]} windows, {counts["rotations"]} rotations, '
              f'{counts["ambiguous_rotations"]} ambiguities', flush=True)
    report['summary']['unique_inputs'] = len(unique)
    if args.axis_sweep:
        sweep = {'seed': 983, 'sample_index_recipe': 'global zero-based tuple index',
                 'bands': [None, 'easy', 'medium', 'hard'], 'grid_h': [6, 14],
                 'grid_w': [6, 18], 'color': [1, 9],
                 'profiles': list(module.PROFILES), 'placements': list(module.PLACEMENTS),
                 'cases': 0, 'per_band': {}, 'failures': []}
        rolling = hashlib.sha256()
        for band in sweep['bands']:
            band_count = 0
            for height, width, color, profile, placement in product(
                    range(6, 15), range(6, 19), range(1, 10), module.PROFILES, module.PLACEMENTS):
                kw = dict(grid_h=height, grid_w=width, color=color, profile=profile, placement=placement)
                index = sweep['cases']
                try:
                    grid = module.generate(sweep['seed'], index, difficulty=band, **kw)
                    errors = module.self_check(grid, difficulty=band, meta={'overrides': kw})
                    observed = module.observe_overrides(grid)
                    if errors or observed != kw:
                        sweep['failures'].append({'band': band, 'sample_index': index,
                            'overrides': kw, 'input': grid, 'errors': errors, 'observed': observed})
                    rolling.update(json.dumps([band, index, kw, digest(grid)],
                                               sort_keys=True, separators=(',', ':')).encode()+b'\n')
                except Exception as exc:
                    sweep['failures'].append({'band': band, 'sample_index': index,
                        'overrides': kw, 'error': f'{type(exc).__name__}: {exc}'})
                band_count += 1
                sweep['cases'] += 1
            sweep['per_band'][str(band)] = band_count
            print(f'axis sweep {band}: {band_count} cases, {len(sweep["failures"])} failures', flush=True)
        sweep['case_stream_sha256'] = rolling.hexdigest()
        report['axis_sweep'] = sweep
    if args.racket_samples:
        from arcpuzzles import Catalog
        # Include canonical pairs and evenly spaced generated draws. These are
        # actual labels returned by the selected Racket authority, not a mirror.
        wanted = args.racket_samples - len(canonical)
        generated = [report['draws'][i * (len(report['draws'])-1) // max(1, wanted-1)]
                     for i in range(wanted)]
        chosen = canonical + generated
        receipt = Catalog(root).apply(TASK, [pair['input'] for pair in chosen])
        if receipt['generator_sha256'] != source_hash:
            raise RuntimeError('Generator changed during parity run')
        mismatches = [i for i, (pair, result) in enumerate(zip(chosen, receipt['results'], strict=True))
                      if pair['output'] != result['output']]
        report['racket_parity'] = {'pairs': len(chosen), 'mismatches': mismatches, 'receipt': receipt}
        print(f'Racket parity: {len(chosen)} pairs, {len(mismatches)} mismatches', flush=True)
    if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError('Generator source changed during probe')
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    failed = (report['failures'] or report.get('axis_sweep', {}).get('failures')
              or report.get('racket_parity', {}).get('mismatches'))
    report['status'] = 'fail' if failed else 'no_measured_failure'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed-count', type=int, default=64)
    parser.add_argument('--seed-base', type=int, default=700000)
    parser.add_argument('--axis-sweep', action='store_true')
    parser.add_argument('--racket-samples', type=int, default=0)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.seed_count < 1 or args.seed_base < 0:
        parser.error('seed-count must be positive and seed-base nonnegative')
    if args.racket_samples and not 4 <= args.racket_samples <= 64:
        parser.error('racket-samples must be 0 or 4..64')
    if args.out.exists():
        parser.error('Use a new output path; existing evidence is never overwritten')
    try:
        report = run(args)
    except Exception as exc:
        report = {'schema': 'rowfront-review-probe-v1', 'task_id': TASK, 'status': 'error',
                  'error': f'{type(exc).__name__}: {exc}', 'command': [sys.executable, *sys.argv],
                  'cwd': str(Path.cwd())}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, separators=(',', ':'))+'\n')
    print(json.dumps({k: v for k, v in report.items() if k in ('status', 'summary', 'error')}), flush=True)
    return 2 if report['status'] == 'error' else 1 if report['status'] == 'fail' else 0


if __name__ == '__main__':
    raise SystemExit(main())
