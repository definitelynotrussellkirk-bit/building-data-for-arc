"""Reproducible supplement to the production lesson census.

Run through run_with_racket.py. Checks the legal joint boundary product and
all starts modulo this task's declared two-profile schedule, using actual
Racket labels and the module's actual rival declarations. This is not a
universal induction proof, nor a replacement for the production sampler.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

TASK = '28268c57c367'
BANDS = ('easy', 'medium', 'hard')


def joint_boundary_pins():
    """504 distinct valid seven-axis settings; both count axes are exhaustive."""
    for height, width in itertools.product((5, 14), (7, 18)):
        for wall in sorted({5, width - 2}):
            for count in range(1, 7):
                for colors in range(1, count + 1):
                    for gray, right in itertools.product((0, 3), repeat=2):
                        yield dict(grid_h=height, grid_w=width, wall_col=wall,
                                   n_cells=count, n_distinct_colors=colors,
                                   n_gray=gray, n_right=right)


def rotation_splits(period=2):
    """Every cyclic start, followed by every single holdout from four pairs."""
    if type(period) is not int or period < 1:
        raise ValueError('period must be a positive integer')
    for start in range(period):
        for query in range(start, start + 4):
            yield {'start': start, 'query': query,
                   'demonstrations': [i for i in range(start, start + 4) if i != query]}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def run(seed_count: int, output: Path) -> int:
    from reviewer_support import canonical_pairs, find_root
    from arcpuzzles import Catalog

    if seed_count < 1:
        raise ValueError('seed count must be positive')
    root = find_root(__file__)
    source = next(p for p in (root/'generators'/TASK/'generator.py',
                             root/'puzzle_generators'/'per_puzzle'/TASK/'generator.py') if p.is_file())
    spec = importlib.util.spec_from_file_location('wall_ray_probe_target', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
    rivals = module.LESSON_COMPETITORS
    if not rivals:
        raise ValueError('No declared competitors; cannot report a semantic pass')
    period = len(module.SCHEDULE_PROFILES)
    if period != 2 or module.EXAMPLES_NEEDED != 3:
        raise ValueError('This probe supports the documented period-2, three-demo contract')
    report = {
        'schema': 'wall-ray-review-probe/1', 'task_id': TASK,
        'generator_sha256': source_sha, 'generator_version': module.VERSION,
        'declared_rule_hash': module.RULE_HASH,
        'rivals': sorted(rivals), 'failures': [], 'boundary_draws': 0,
        'boundary_policy': {'settings': 504, 'seed': 31, 'indices': [0, 1], 'bands': list(BANDS)},
        'curriculum_policy': {'seed_range': [0, seed_count-1], 'sample_index_range': [0, 4],
                              'bands': list(BANDS), 'cyclic_starts': [0, 1],
                              'demonstrations': 3, 'query_rotations_per_window': 4,
                              'sampler': 'direct generate, no rejection or overrides'},
        'scope': 'finite named-rival and joint-boundary checks; not universal identifiability',
    }
    for pins in joint_boundary_pins():
        for band, index in itertools.product(BANDS, (0, 1)):
            grid = module.generate(31, index, difficulty=band, **pins)
            errors = module.self_check(grid)
            observed = module.observe_overrides(grid)
            report['boundary_draws'] += 1
            if errors or any(observed[k] != value for k, value in pins.items()):
                report['failures'].append({'phase': 'boundary', 'pins': pins, 'band': band,
                                           'index': index, 'input': grid, 'errors': errors,
                                           'observed': observed})
    canonical = canonical_pairs(TASK, root=root)
    report['canonical_shortcut_fit'] = {}
    for name, rival in module.CANONICAL_SHORTCUTS.items():
        matched = sum(rival(p['input']) == p['output'] for p in canonical)
        report['canonical_shortcut_fit'][name] = {'matched': matched, 'total': len(canonical)}
        if matched != len(canonical):
            report['failures'].append({'phase': 'canonical_shortcut', 'name': name})
    records = [{'band': band, 'seed': seed, 'sample_index': i,
                'input': module.generate(seed, i, difficulty=band)}
               for band in BANDS for seed in range(seed_count) for i in range(5)]
    catalog = Catalog(root)
    report['racket_batches'] = []
    for start in range(0, len(records), 64):
        batch = records[start:start+64]
        result = catalog.apply(TASK, inputs=[row['input'] for row in batch])
        labels = result['results']
        if len(labels) != len(batch) or any('output' not in row for row in labels):
            raise RuntimeError('Incomplete Racket batch')
        report['racket_batches'].append({'first_record': start, 'count': len(batch),
                                         'result_sha256': digest(result),
                                         'provenance': {k: v for k, v in result.items() if k != 'results'}})
        for record, label in zip(batch, labels):
            record['output'] = label['output']
    report['labeled_pairs'] = len(records)
    report['unique_inputs'] = len({digest(row['input']) for row in records})
    report['labeled_population_sha256'] = digest(records)
    report['rotation_views'] = 0
    report['rival_view_checks'] = 0
    for offset in range(0, len(records), 5):
        cohort = records[offset:offset+5]
        predictions = {}
        for name, rival in rivals.items():
            original = digest(cohort)
            predictions[name] = [rival(row['input']) for row in cohort]
            if digest(cohort) != original:
                raise RuntimeError(f'Rival mutated the input: {name}')
        for split in rotation_splits(period):
            report['rotation_views'] += 1
            for name, guesses in predictions.items():
                report['rival_view_checks'] += 1
                # Deliberately stronger than query-ambiguity testing: insist that
                # each named wrong rule is refuted by at least one demonstration.
                if not any(guesses[i] != cohort[i]['output'] for i in split['demonstrations']):
                    report['failures'].append({'phase': 'unrefuted_rival', 'name': name,
                                               'split': split, 'cohort': cohort,
                                               'predictions': guesses})
    report['source_unchanged'] = hashlib.sha256(source.read_bytes()).hexdigest() == source_sha
    if not report['source_unchanged']:
        report['failures'].append({'phase': 'source_changed'})
    report['status'] = 'PASS' if not report['failures'] else 'FAIL'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'generator_sha256', 'boundary_draws',
                     'labeled_pairs', 'unique_inputs', 'rotation_views', 'rival_view_checks')}))
    return int(bool(report['failures']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=20)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.seeds, args.out))
