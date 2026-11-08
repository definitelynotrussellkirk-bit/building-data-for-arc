"""Source-bound palette-cycle regression probe; no private runtime imports.

Run from the packet root via run_with_racket.py. The optional census audit uses
materialized Racket labels, never the Python diagnostic mirror. Do not use while
performing a visible-only solve: this is authoring tooling with reference data.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from reviewer_support import canonical_pairs, find_root


def load_generator():
    source = Path(__file__).resolve().parents[1] / 'generator.py'
    spec = importlib.util.spec_from_file_location('cycle_probe_generator', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return source, module


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def numeric_predecessor(grid):
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    palette = sorted({v for row in grid for v in row} - {bg})
    out = [row[:] for row in grid]
    for c in range(len(grid[0])):
        foreground = {row[c] for row in grid} - {bg}
        if not foreground:
            continue
        color, = foreground
        replacement = palette[(palette.index(color) - 1) % len(palette)]
        for r, row in enumerate(grid):
            if row[c] == bg:
                out[r][c] = replacement
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--per-band', type=int, default=200)
    parser.add_argument('--phase', required=True)
    args = parser.parse_args()
    if args.per_band < 4:
        parser.error('--per-band must be at least 4')
    if args.out.exists():
        parser.error('output already exists; retain prior evidence under another name')
    source, gen = load_generator()
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    rivals = {}
    for namespace in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS', 'SEMANTIC_RIVALS'):
        for name, fn in getattr(gen, namespace, {}).items():
            rivals[f'{namespace}:{name}'] = fn
    rivals['independent_probe:numeric_predecessor'] = numeric_predecessor
    report = {
        'schema': 'cyclic-color-support-v1', 'phase': args.phase,
        'task_id': gen.TASK_ID, 'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'rule_hash': gen.RULE_HASH, 'comparison_authority': 'canonical labels; generated diagnostic Python mirror',
        'canonical_pairs': len(pairs), 'unique_canonical_inputs': len({fingerprint(p['input']) for p in pairs}),
        'canonical_fit_counts': {name: sum(fn(p['input']) == p['output'] for p in pairs)
                                 for name, fn in rivals.items()},
        'bands': {},
    }
    unique = set()
    for band in ('easy', 'medium', 'hard'):
        rows = []; orders = Counter(); fit = Counter(); unique_band = set(); example = None
        for i in range(args.per_band):
            grid = gen.generate(600123, i, difficulty=band)
            errors = gen.strict_canonical_like(grid)
            if errors:
                raise ValueError((band, i, errors))
            expected = gen.rule_mirror(grid)
            unique.add(fingerprint(grid)); unique_band.add(fingerprint(grid))
            _, _, _, colors = gen._analyze(grid)
            rank = ''.join(str(sorted(colors).index(c)) for c in colors)
            orders[rank] += 1
            for name, fn in rivals.items():
                fit[name] += fn(grid) == expected
            rows.append({'input': grid, 'output': expected})
            if example is None and numeric_predecessor(grid) != expected:
                example = {'seed': 600123, 'sample_index': i, 'difficulty': band,
                           'input': grid, 'mirror_output': expected,
                           'rival_output': numeric_predecessor(grid)}
        window_survivors = Counter()
        for i in range(len(rows) - 2):
            for name, fn in rivals.items():
                window_survivors[name] += all(fn(p['input']) == p['output'] for p in rows[i:i+3])
        report['bands'][band] = {
            'seed': 600123, 'sample_index_range': [0, args.per_band - 1],
            'draws': args.per_band, 'strict_valid': args.per_band, 'unique_inputs': len(unique_band),
            'rank_orders': dict(orders), 'rival_fit_counts': dict(fit),
            'three_demo_windows': args.per_band - 2,
            'three_demo_survived_counts': dict(window_survivors), 'first_counterexample': example,
        }
    report['unique_inputs_total'] = len(unique)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('phase', 'generator_sha256', 'canonical_pairs', 'unique_canonical_inputs', 'unique_inputs_total')}, indent=2))
    for band, row in report['bands'].items():
        print(band, 'orders=', row['rank_orders'], 'predecessor_fit=', row['rival_fit_counts']['independent_probe:numeric_predecessor'])


if __name__ == '__main__':
    main()
