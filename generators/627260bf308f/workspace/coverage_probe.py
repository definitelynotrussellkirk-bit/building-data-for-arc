"""Replay coverage and lesson ambiguity using dynamic task rival declarations.

Run via the packet wrapper. This is an AUTHORING probe, not a solve tool.
Its independent Python rank calculation is diagnostic, not a label authority;
use the shared lesson-census for production/Racket evidence. --baseline samples
this packet's immutable baseline while retaining current rival-source identity.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root

TASK = '627260bf308f'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def groups(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if r > 0 and v == 8}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack, group = [start], [start]
        while stack:
            r, c = stack.pop()
            for cell in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if cell in remaining:
                    remaining.remove(cell); group.append(cell); stack.append(cell)
        result.append(group)
    return result


def expected(grid):
    out = [row[:] for row in grid]
    palette = [v for v in grid[0] if v]
    def key(group):
        return len(group), (min(r for r,c in group), min(c for r,c in group),
                            max(r for r,c in group), max(c for r,c in group))
    for color, group in zip(palette, sorted(groups(grid), key=key)):
        for r, c in group:
            out[r][c] = color
    return out


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def analyze(source, contracts, root, seeds, joint_axes=False):
    # Read declarations, not a hand-copied rival-name list. Namespaces remain
    # visible; the same callable can legitimately belong to two contracts.
    rivals = {f'{namespace}.{name}': function
              for namespace in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS')
              for name, function in getattr(contracts, namespace, {}).items()}
    pairs = canonical_pairs(TASK, root=root)
    canonical_fit = {name: {'passed': sum(fn(p['input']) == p['output'] for p in pairs),
                            'total': len(pairs)} for name, fn in rivals.items()}
    counts, unique, counterexamples = Counter(), set(), {}
    marginal = {key: Counter() for key in ('shapes', 'component_counts', 'sizes', 'witnesses', 'palette_order')}
    rival_counts = {name: Counter() for name in rivals}
    source_failures = []
    for band in ('easy', 'medium', 'hard'):
        for seed in range(seeds):
            grids = [source.generate(seed, index, difficulty=band) for index in range(11)]
            labels = [expected(g) for g in grids]
            predictions = {name: [fn(g) for g in grids] for name, fn in rivals.items()}
            for index, grid in enumerate(grids):
                unique.add(digest(grid)); counts['draws'] += 1
                errors = source.self_check(grid)
                if errors:
                    source_failures.append({'band': band, 'seed': seed, 'index': index, 'errors': errors})
                sizes = sorted(len(group) for group in groups(grid))
                marginal['shapes'][f'{len(grid)}x{len(grid[0])}'] += 1
                marginal['component_counts'][str(len(sizes))] += 1
                marginal['sizes'].update(map(str, sizes))
                palette = [v for v in grid[0] if v]
                marginal['palette_order']['sorted' if palette == sorted(palette) else 'unsorted'] += 1
                for name, fn in getattr(contracts, 'SEMANTIC_WITNESSES', {}).items():
                    marginal['witnesses'][name] += int(fn(grid))
            for start in range(8):
                window = list(range(start, start+4))
                counts['lessons'] += 1
                prod_bad, bad_rotations = False, set()
                for name, values in predictions.items():
                    for query in window:
                        demos = [i for i in window if i != query]
                        fits = all(values[i] == labels[i] for i in demos)
                        bad = fits and values[query] != labels[query]
                        scope = 'production' if query == window[-1] else 'other_rotation'
                        rival_counts[name][scope + ('_ambiguous' if bad else '_not_ambiguous')] += 1
                        if bad:
                            bad_rotations.add(query)
                            prod_bad |= scope == 'production'
                            counterexamples.setdefault(name, {
                                'band': band, 'seed': seed, 'start': start, 'query_index': query,
                                'demo_indices': demos, 'input_indices': window,
                                'inputs': [grids[i] for i in window],
                                'diagnostic_outputs': [labels[i] for i in window],
                                'rival_outputs': [values[i] for i in window],
                                'label_authority': 'independent Python diagnostic; not Racket-certified',
                            })
                counts['production_ambiguous_lessons'] += int(prod_bad)
                counts['rotation_checks'] += 4
                counts['ambiguous_rotations'] += len(bad_rotations)
    axis_failures, axis_count = [], 0
    if joint_axes:
        for band, index, h, w, n, order in itertools.product(
                ('easy', 'medium', 'hard'), (0, 1), range(8,25), range(10,25), range(2,6), ('sorted', 'unsorted')):
            overrides = dict(grid_h=h, grid_w=w, n_components=n, palette_order=order)
            axis_count += 1
            try:
                grid = source.generate(867, index, difficulty=band, **overrides)
                actual = {'grid_h': len(grid), 'grid_w': len(grid[0]), 'n_components': len(groups(grid)),
                          'palette_order': 'sorted' if [v for v in grid[0] if v] == sorted(v for v in grid[0] if v) else 'unsorted'}
                errors = source.self_check(grid)
                if actual != overrides or errors or len({len(g) for g in groups(grid)}) != n:
                    axis_failures.append({'band': band, 'index': index, 'overrides': overrides, 'actual': actual, 'errors': errors})
            except Exception as exc:
                axis_failures.append({'band': band, 'index': index, 'overrides': overrides, 'error': f'{type(exc).__name__}: {exc}'})
    return {
        'schema': 'palette-rank-coverage-v1', 'task_id': TASK,
        'label_authority': 'independent Python diagnostics; see shared Racket census for authority',
        'seed_range': [0, seeds-1], 'sample_index_range': [0, 10], 'bands': ['easy','medium','hard'],
        'lesson_policy': '3 demonstrations, 1 query; starts 0..7; all 4 single-query holdouts; windows overlap',
        'period': 2, 'counts': dict(counts), 'unique_inputs': len(unique),
        'canonical_fit': canonical_fit, 'marginals': {k: dict(v) for k,v in marginal.items()},
        'rival_counts': {k: dict(v) for k,v in rival_counts.items()},
        'first_counterexamples': counterexamples, 'source_failures': source_failures,
        'joint_axes': {'seed': 867, 'sample_indices': [0,1], 'case_count': axis_count,
                       'failures': axis_failures, 'domains': {'grid_h':'8..24','grid_w':'10..24','n_components':'2..5','palette_order':['sorted','unsorted']}},
        'status': 'findings' if counterexamples or source_failures or axis_failures else 'no_findings',
        'limits': 'Finite explicit rivals and seed range, not universal identifiability. Overlapping windows are not independent inputs.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seeds', type=int, default=32)
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--joint-axes', action='store_true')
    args = parser.parse_args()
    if args.seeds < 1 or args.out.exists():
        parser.error('Use a positive seed count and a new output filename')
    root = find_root(__file__)
    current = root / 'generators' / TASK / 'generator.py'
    if not current.is_file():
        current = root / 'puzzle_generators' / 'per_puzzle' / TASK / 'generator.py'
    source_path = root.parent / '.review/baseline/repo/generators' / TASK / 'generator.py' if args.baseline else current
    if not source_path.is_file():
        parser.error(f'No source at {source_path}; baseline mode requires the original extracted packet')
    source, contracts = load(source_path, 'sampled_palette_generator'), load(current, 'rival_palette_generator')
    report = analyze(source, contracts, root, args.seeds, args.joint_axes)
    report.update(source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                  rival_source_sha256=hashlib.sha256(current.read_bytes()).hexdigest(),
                  rule_hash=contracts.RULE_HASH, baseline=args.baseline,
                  argv=sys.argv, cwd=str(Path.cwd()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('status','counts','unique_inputs','source_sha256')}, indent=2))
    print('joint axes:', report['joint_axes']['case_count'], 'failures:', len(report['joint_axes']['failures']))
    return int(report['status'] != 'no_findings')


if __name__ == '__main__':
    raise SystemExit(main())
