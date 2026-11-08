"""Exhaust the finite advertised axis cross-product at both cycle phases.

This is input-contract/diagnostic-mirror evidence, not a Racket proof. The
production census supplies independent Racket comparisons. Authoring use only.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
from color_cycle_probe import fingerprint, load_generator, numeric_predecessor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        parser.error('output already exists; use a new evidence path')
    source, gen = load_generator()
    report = {
        'schema': 'joint-axis-probe-v1', 'task_id': gen.TASK_ID,
        'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'rule_hash': gen.RULE_HASH, 'authority': 'strict input contract and Python diagnostic mirror',
        'seed': 77199, 'sample_indexes': [0, 1],
        'axis_values': {'grid_h': list(range(8, 13)), 'layout': list(gen.LAYOUTS), 'bg_color': list(range(10))},
        'bands': {}, 'failures': [], 'draws': 0, 'unique_inputs': 0,
    }
    unique = set()
    for band in ('easy', 'medium', 'hard'):
        counts = Counter()
        for h, layout, bg in product(range(8, 13), gen.LAYOUTS, range(10)):
            overrides = {'grid_h': h, 'layout': layout, 'bg_color': bg}
            fits = {'numeric_successor': [], 'numeric_predecessor': []}
            for index in (0, 1):
                counts['draws'] += 1; report['draws'] += 1
                try:
                    grid = gen.generate(77199, index, difficulty=band, **overrides)
                    errors = gen.strict_canonical_like(grid)
                    if errors:
                        raise ValueError(errors)
                    if gen.observe_overrides(grid) != overrides:
                        raise ValueError('joint override not honored')
                    out = gen.rule_mirror(grid)
                    fits['numeric_successor'].append(gen._numeric_color_cycle(grid) == out)
                    fits['numeric_predecessor'].append(numeric_predecessor(grid) == out)
                    counts['strict_valid'] += 1; counts['exact_observation'] += 1
                    unique.add(fingerprint(grid))
                except Exception as exc:
                    report['failures'].append({'band': band, 'overrides': overrides, 'sample_index': index,
                                               'error': f'{type(exc).__name__}: {exc}'})
            counts['axis_combinations'] += 1
            for rival, matches in fits.items():
                if len(matches) == 2 and sum(matches) == 1:
                    counts[rival + '_balanced'] += 1
                else:
                    report['failures'].append({'band': band, 'overrides': overrides, 'rival': rival,
                                               'matches': matches})
        report['bands'][band] = dict(counts)
    report['unique_inputs'] = len(unique)
    report['passed'] = not report['failures']
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('generator_sha256', 'draws', 'unique_inputs', 'passed')}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
