#!/usr/bin/env python3
"""Exhaustive direct cyclic-window support, supplementing the production census.

Run through the packet wrapper or with this tree's src/runtime on PYTHONPATH.
Uses public Catalog.apply (1..64 inputs), never private reference runners.
The default requests every advertised schedule start and all three bands.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root
from arcpuzzles import Catalog

TASK = 'c39bef185e7e'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def load_generator(root, source=None):
    if source is None:
        source = root / 'generators' / TASK / 'generator.py'
        if not source.is_file():
            source = root / 'puzzle_generators' / f'{TASK}.py'
    source = Path(source).resolve()
    spec = importlib.util.spec_from_file_location('cyclic_curriculum_generator', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def declarations(gen):
    """Keep namespace identity; inspect current declarations without name lists."""
    rivals = {}
    for attribute in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS'):
        declaration = getattr(gen, attribute)
        if not isinstance(declaration, dict) or not declaration:
            raise ValueError(f'{attribute} must declare named rival callables')
        for name, fn in declaration.items():
            if not isinstance(name, str) or not callable(fn):
                raise ValueError(f'{attribute}: invalid rival declaration')
            rivals[f'{attribute}:{name}'] = fn
    return rivals


def analyze_window(pairs, predictions, query_index):
    """Retain exact query-changing rivals and the remaining demonstration indices."""
    demos = [i for i in range(len(pairs)) if i != query_index]
    statuses, ambiguities = {}, []
    for name, outputs in predictions.items():
        refuting = [pairs[i]['sample_index'] for i in demos if outputs[i] != pairs[i]['output']]
        query = pairs[query_index]
        agrees = outputs[query_index] == query['output']
        status = 'refuted' if refuting else 'survived_all' if agrees else 'ambiguous'
        statuses[name] = {'status': status, 'refuting_sample_indices': refuting}
        if status == 'ambiguous':
            ambiguities.append({'rival': name, 'query_sample_index': query['sample_index'],
                                'demo_sample_indices': [pairs[i]['sample_index'] for i in demos],
                                'rival_query_output': outputs[query_index],
                                'reference_query_output': query['output']})
    return {'query_index': query_index, 'query_sample_index': pairs[query_index]['sample_index'],
            'demo_sample_indices': [pairs[i]['sample_index'] for i in demos],
            'rivals': statuses, 'ambiguous': bool(ambiguities), 'ambiguities': ambiguities}


def run(*, seed=17, period=None, bands=('easy', 'medium', 'hard'), source=None, root=None):
    root = find_root(__file__) if root is None else find_root(root)
    gen = load_generator(root, source)
    source_path = Path(gen.__file__)
    source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
    period = getattr(gen, 'SCHEDULE_PERIOD', len(gen.SCHEDULE_PROFILES)) if period is None else period
    if type(period) is not int or period < 1:
        raise ValueError('period must be positive')
    demos_n = gen.EXAMPLES_NEEDED
    if type(demos_n) is not int or demos_n < 1:
        raise ValueError('EXAMPLES_NEEDED must be positive')
    width = demos_n + 1
    rivals = declarations(gen)
    catalog = Catalog(root)
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    report = {'schema': 'c39bef185e7e-cyclic-curriculum-v1', 'task_id': TASK,
              'generator_source': str(source_path), 'generator_sha256': source_hash,
              'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'generator_version': gen.VERSION, 'declared_rule_hash': gen.RULE_HASH,
              'seed': seed, 'period': period, 'difficulty_bands': list(bands),
              'demonstrations': demos_n, 'queries': 1, 'declared_rivals': sorted(rivals),
              'assembly': f'direct consecutive generator indices i..i+{demos_n}; each held out once; remaining order preserved',
              'production_policy': 'ordered direct window uses final pair as query; production sampler itself is covered by shared lesson-census',
              'authority': 'selected canonical Racket outputs via public Catalog.apply in batches <=64',
              'canonical_rival_fit': {}, 'reference_batches': [], 'bands': {},
              'limits': ['Finite current declared-rival comparison, not universal identifiability.',
                         'Direct windows extend the production census; they do not reproduce its retry/seed assembly.',
                         'Unique inputs count exact grid hashes, not distinct semantic shapes.',
                         'All retained generated labels execute the selected rule, including an explicit historical source when supplied.']}
    for name, fn in rivals.items():
        fits = [fn(deepcopy(pair['input'])) == pair['output'] for pair in canonical]
        report['canonical_rival_fit'][name] = {'pairs': len(canonical), 'fits': sum(fits), 'fits_all': all(fits),
             'refuted_pairs': [{'variant': p['variant'], 'split': p['split'], 'pair_index': p['pair_index']}
                               for p, fit in zip(canonical, fits) if not fit]}
    all_input_hashes = set()
    production_count = rotation_count = production_ambiguous = rotation_ambiguous = 0
    all_ambiguities = []
    for band in bands:
        pairs = []
        for index in range(period + demos_n):
            grid = gen.generate(seed, index, difficulty=band)
            errors = gen.self_check(grid, difficulty=band)
            if errors:
                raise ValueError(f'{band} sample {index} fails validator: {errors}')
            pairs.append({'seed': seed, 'sample_index': index, 'difficulty': band,
                          'input': grid, 'input_sha256': digest(grid),
                          'observed': gen.observe_overrides(grid), 'self_check': errors})
        for first in range(0, len(pairs), 64):
            batch_pairs = pairs[first:first+64]
            applied = catalog.apply(TASK, [p['input'] for p in batch_pairs])
            report['reference_batches'].append({k: v for k, v in applied.items() if k != 'results'} |
                                               {'band': band, 'sample_indices': [p['sample_index'] for p in batch_pairs]})
            for pair, result in zip(batch_pairs, applied['results'], strict=True):
                if not result.get('output'):
                    raise ValueError(f'Reference did not label {band} sample {pair["sample_index"]}: {result}')
                pair['output'] = result['output']
                pair['output_sha256'] = result['output_sha256']
                pair['mirror_agrees'] = gen.rule_mirror(pair['input']) == pair['output']
                pair['reference_input_sha256'] = result['input_sha256']
        input_hashes = {p['input_sha256'] for p in pairs}
        all_input_hashes.update(input_hashes)
        predictions = {name: [fn(deepcopy(p['input'])) for p in pairs] for name, fn in rivals.items()}
        windows = []
        rival_support = {name: {'refuting_pairs': sum(pred != p['output'] for pred, p in zip(outputs, pairs)),
                               'production': Counter(), 'rotations': Counter()} for name, outputs in predictions.items()}
        for start in range(period):
            window = pairs[start:start+width]
            scores = [analyze_window(window, {name: outputs[start:start+width] for name, outputs in predictions.items()}, qi)
                      for qi in range(width)]
            for score in scores:
                query = window[score['query_index']]
                demos = [p for i, p in enumerate(window) if i != score['query_index']]
                score['hook_reasons'] = gen.lesson_identifiable(deepcopy(demos), deepcopy(query))
                for name, verdict in score['rivals'].items():
                    rival_support[name]['rotations'][verdict['status']] += 1
                all_ambiguities.extend(dict(a, band=band, start=start, seed=seed) for a in score['ambiguities'])
            production = scores[-1]
            for name, verdict in production['rivals'].items():
                rival_support[name]['production'][verdict['status']] += 1
            windows.append({'start': start, 'pair_sample_indices': [p['sample_index'] for p in window],
                            'production': production, 'rotations': scores})
        production_count += len(windows)
        rotation_count += width * len(windows)
        production_ambiguous += sum(w['production']['ambiguous'] for w in windows)
        rotation_ambiguous += sum(s['ambiguous'] for w in windows for s in w['rotations'])
        joint = Counter((p['observed']['unique_quadrant'],
                         _size_relation(gen, p),
                         p['observed']['common_count']) for p in pairs[:period])
        report['bands'][band] = {'pairs': pairs, 'windows': windows, 'unique_inputs': len(input_hashes),
                                 'joint_support': [{'unique_quadrant': q, 'size_relation': r, 'common_count': c, 'draws': n}
                                                  for (q, r, c), n in sorted(joint.items())],
                                 'rival_support': rival_support}
    report['summary'] = {'ordered_windows': production_count, 'ambiguous_ordered_windows': production_ambiguous,
                         'rotations': rotation_count, 'ambiguous_rotations': rotation_ambiguous,
                         'unique_inputs': len(all_input_hashes),
                         'materialized_draws': sum(len(b['pairs']) for b in report['bands'].values()),
                         'production_hook_warnings': sum(bool(w['production']['hook_reasons']) for b in report['bands'].values() for w in b['windows']),
                         'rotation_hook_warnings': sum(bool(s['hook_reasons']) for b in report['bands'].values() for w in b['windows'] for s in w['rotations']),
                         'mirror_disagreements': sum(not p['mirror_agrees'] for b in report['bands'].values() for p in b['pairs'])}
    report['exact_ambiguities'] = all_ambiguities
    report['production_status'] = 'ambiguous' if production_ambiguous else 'no_declared_ambiguity'
    report['rotation_status'] = 'ambiguous' if rotation_ambiguous else 'no_declared_ambiguity'
    report['status'] = 'ambiguous' if production_ambiguous or rotation_ambiguous else 'no_declared_ambiguity'
    if report['summary']['mirror_disagreements']:
        report['status'] = 'mirror_disagreement'
    elif report['summary']['production_hook_warnings'] or report['summary']['rotation_hook_warnings']:
        report['status'] = 'warning'
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != source_hash:
        raise RuntimeError('Generator source changed during probe')
    return report


def _size_relation(gen, pair):
    # The selected reference identifies the singleton directly, even on baseline
    # source which has no size_relation observer. No mirror provides these labels.
    output = pair['output']
    unique_size = sum(cell == 8 for row in output for cell in row)
    common_size = pair['observed']['motif_size']
    return 'equal' if unique_size == common_size else 'different'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--period', type=int)
    parser.add_argument('--band', choices=('easy', 'medium', 'hard'), action='append')
    parser.add_argument('--source', type=Path, help='Optional historical generator source; rule stays selected canonical')
    parser.add_argument('--out', type=Path, required=True, help='New JSON output path')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('--out must be a new path')
    report = run(seed=args.seed, period=args.period, bands=tuple(args.band or ('easy', 'medium', 'hard')), source=args.source)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(report, stream, separators=(',', ':'))
        stream.write('\n')
    print(json.dumps({k: report[k] for k in ('generator_sha256', 'period', 'summary', 'production_status', 'rotation_status')}))
    return 0 if report['status'] == 'no_declared_ambiguity' else 1


if __name__ == '__main__':
    raise SystemExit(main())
