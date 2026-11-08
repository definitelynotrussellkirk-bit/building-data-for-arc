#!/usr/bin/env python3
"""Task-local finite support/lesson probe. Does not generate authoritative labels.

Run from a packet with run_with_racket.py; no private script imports. The public
lesson-census remains the Racket-labelled production check. This probe separately
covers every start of short same-seed sequences, and legal joint override corners.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parent.parent
TASK = '2ab8c1aaa3e2'
_spec = importlib.util.spec_from_file_location('vertical_probe_generator', HOME / 'generator.py')
gen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gen)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def oracle(grid):
    """Independent diagnostic oracle, NOT dataset label authority."""
    out = [list(row) for row in grid]
    for c in range(len(grid[0])):
        positions = {}
        for r, row in enumerate(grid):
            if row[c]:
                positions.setdefault(row[c], []).append(r)
        for color, hits in positions.items():
            if len(hits) == 2:
                for r in range(hits[0], hits[1] + 1):
                    out[r][c] = color
    return out


def declared_rivals():
    return {f'{namespace}:{name}': rival
            for namespace in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS', 'SEMANTIC_RIVALS')
            for name, rival in getattr(gen, namespace, {}).items()}


def feasible(pairs, colors, width):
    """Independent closed-form feasibility for the two documented motif layouts."""
    core = pairs <= width and colors <= pairs
    contrast = pairs + 2 <= width and 2 <= colors <= (pairs + 3 if pairs >= 2 else 5)
    return core or contrast


def check_joint_corners():
    report = {'attempted': 0, 'accepted': 0, 'structured_rejections': 0, 'per_band': {}}
    for band in ('easy', 'medium', 'hard'):
        stats = Counter()
        for phase, h, w, p, k in itertools.product(range(3), (4, 22), (4, 20), range(1, 13), range(1, 10)):
            ovs = dict(grid_h=h, grid_w=w, pairs=p, n_distinct_colors=k)
            stats['attempted'] += 1
            allowed = feasible(p, k, w)
            try:
                grid = gen.generate(409, phase, difficulty=band, **ovs)
            except ValueError as exc:
                assert not allowed, (band, phase, ovs, str(exc))
                axes = getattr(exc, 'incompatible_axes', ())
                assert len(axes) >= 2 and set(axes) <= set(ovs), (ovs, str(exc))
                stats['structured_rejections'] += 1
            else:
                assert allowed, (band, phase, ovs)
                assert not gen.self_check(grid), (ovs, gen.self_check(grid))
                assert gen.observe_overrides(grid) == ovs, ovs
                stats['accepted'] += 1
        report['per_band'][band] = dict(stats)
        for key in ('attempted', 'accepted', 'structured_rejections'):
            report[key] += stats[key]
    return report


def run(seeds=10, samples=30, joint=True):
    if seeds < 1 or samples < 4:
        raise ValueError('Need positive seeds and at least four samples')
    rivals = declared_rivals()
    if not rivals:
        raise ValueError('No rival declarations; this cannot establish rival coverage')
    pairs = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)
    report = {
        'task_id': TASK, 'generator_sha256': hashlib.sha256((HOME / 'generator.py').read_bytes()).hexdigest(),
        'rule_hash': gen.RULE_HASH, 'basis': 'independent Python diagnostic oracle; production Racket labels are checked separately',
        'population': {'seeds': list(range(seeds)), 'sample_indices': [0, samples - 1],
                       'bands': ['easy', 'medium', 'hard'], 'train': 3, 'test': 1,
                       'lesson_starts': [0, samples - 4], 'overlapping_windows': True},
        'canonical_fit': {}, 'per_band': {}, 'rival_counterexamples': {}, 'errors': [],
    }
    for name, rival in rivals.items():
        fits = sum(rival(p['input']) == p['output'] for p in pairs)
        report['canonical_fit'][name] = {'fits': fits, 'total': len(pairs)}
        assert fits == len(pairs), name
    all_inputs = set()
    for band in report['population']['bands']:
        stats = Counter()
        for seed in range(seeds):
            grids = [gen.generate(seed, i, difficulty=band) for i in range(samples)]
            outputs = []
            predictions = {name: [] for name in rivals}
            for index, grid in enumerate(grids):
                assert gen.self_check(grid) == [], (band, seed, index)
                assert grid == gen.generate(seed, index, difficulty=band)
                out = oracle(grid)
                assert out != grid, (band, seed, index, 'identity default draw')
                outputs.append(out)
                all_inputs.add(digest(grid))
                stats['draws'] += 1
                stats['strict'] += not bool(gen.strict_canonical_like(grid))
                for name, rival in rivals.items():
                    old = digest(grid)
                    pred = rival(grid)
                    assert digest(grid) == old, ('rival mutated input', name)
                    predictions[name].append(pred)
                    if pred != out and name not in report['rival_counterexamples']:
                        report['rival_counterexamples'][name] = dict(seed=seed, sample_index=index,
                            difficulty=band, input=grid, diagnostic_output=out, rival_output=pred)
            for start in range(samples - 3):
                indices = range(start, start + 4)
                stats['windows'] += 1
                for query in indices:
                    stats['rotations'] += 1
                    for name, preds in predictions.items():
                        refuted = any(preds[i] != outputs[i] for i in indices if i != query)
                        assert refuted, (name, band, seed, start, query)
        report['per_band'][band] = dict(stats)
    report['unique_inputs'] = len(all_inputs)
    report['totals'] = {key: sum(x[key] for x in report['per_band'].values())
                        for key in ('draws', 'strict', 'windows', 'rotations')}
    if joint:
        report['joint_override_corners'] = check_joint_corners()
    report['status'] = 'passed_finite_diagnostic'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, default=10)
    parser.add_argument('--samples', type=int, default=30)
    parser.add_argument('--skip-joint', action='store_true')
    args = parser.parse_args()
    if args.out.exists():
        parser.error('Use a new output path; retain earlier evidence')
    report = run(args.seeds, args.samples, not args.skip_joint)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'totals', 'unique_inputs')}))
    if 'joint_override_corners' in report:
        print(json.dumps(report['joint_override_corners']))


if __name__ == '__main__':
    main()
