"""Opt-in, source-bound mass/palette conservation check for a7d4df2828a0.

Run from any directory with --library /path/to/ARCpuzzles. Requires the library's
normal dependencies and Racket on PATH or RACKET_PATH. Exits 1 on any observed
failure; never changes approval, rules, labels, or shared tooling.

This task deletes one control cell, then losslessly transforms its motif. The
Counter assertion is reusable for OTHER explicitly lossless tasks only after
reviewing their background/control masks. It is NOT a corpus-wide rule.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time

TASK_ID = 'a7d4df2828a0'


def _valid_grid(g):
    return (isinstance(g, list) and len(g) > 0
            and all(isinstance(row, list) for row in g) and len(g[0]) > 0
            and all(len(row) == len(g[0]) for row in g)
            and all(type(v) is int and 0 <= v <= 9 for row in g for v in row))


def conservation_issues(grid, output):
    """Compare color multiplicities, excluding ONLY the input control cell."""
    if not _valid_grid(grid):
        return ['malformed_input']
    if not _valid_grid(output):
        return ['malformed_output']
    issues = []
    if (len(grid), len(grid[0])) != (len(output), len(output[0])):
        issues.append('canvas_shape_changed')
    expected = Counter(value for r, row in enumerate(grid) for c, value in enumerate(row)
                       if value != 0 and (r, c) != (0, 0))
    actual = Counter(value for row in output for value in row if value != 0)
    if expected != actual:
        issues.append('motif_color_counts_changed')
    return issues


def geometry_issues(grid):
    if not _valid_grid(grid):
        return ['malformed_input']
    cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row)
             if v and (r, c) != (0, 0)]
    if not cells:
        return ['missing_motif']
    r0, c0 = min(r for r, c in cells), min(c for r, c in cells)
    height = max(r for r, c in cells) - r0 + 1
    width = max(c for r, c in cells) - c0 + 1
    out_h, out_w = (width, height) if grid[0][0] == 1 else (height, width)
    return (['transformed_footprint_clips']
            if r0 + out_h > len(grid) or c0 + out_w > len(grid[0]) else [])


def _literal(grid):
    return "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--generator-source', type=Path, help='Optional inspected baseline generator.py')
    parser.add_argument('--samples-per-band', type=int, default=1000)
    parser.add_argument('--racket-per-band', type=int, default=1000,
                        help='First N inputs per band receive real Racket labels; 0 is geometry-only')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.samples_per_band <= 0 or not 0 <= args.racket_per_band <= args.samples_per_band:
        parser.error('require samples-per-band > 0 and 0 <= racket-per-band <= samples-per-band')
    if args.out.exists():
        parser.error(f'refusing to overwrite evidence: {args.out}')
    library = args.library.resolve()
    source = (args.generator_source or library / f'generators/{TASK_ID}/generator.py').resolve()
    sys.path.insert(0, str(library / 'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime
    started = time.monotonic()
    counts = Counter()
    first_failures = []
    selected = []
    report = {'schema': 'a7d4df2828a0-conservation-v1', 'task_id': TASK_ID,
              'generator_sha256': _sha(source), 'generator_source': str(source),
              'samples_per_band': args.samples_per_band, 'racket_per_band': args.racket_per_band,
              'python': sys.version, 'canonical_ledger_sha256': _sha(library / 'shared/data/canonical/puzzles.jsonl')}

    def fail(record, issues):
        counts['failed_cases'] += 1
        for issue in issues:
            counts['issue:' + issue] += 1
        if len(first_failures) < 24:
            first_failures.append({**record, 'issues': issues})

    # A fresh copied runtime supplies all helpers; no borrowed predecessor paths.
    with tempfile.TemporaryDirectory(prefix='arc-conservation-') as directory:
        runtime = Path(directory)
        receipt = prepare_runtime(Catalog(library), runtime, TASK_ID)
        report['runtime_file_count'] = len(receipt['files'])
        report['runtime_manifest_sha256'] = _sha(runtime / 'RUNTIME_MANIFEST.json')
        sys.path.insert(0, str(runtime))
        spec = importlib.util.spec_from_file_location('reviewed_generator', source)
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        with (runtime / 'data/canonical/puzzles.jsonl').open() as handle:
            rows = [row for line in handle if (row := json.loads(line))['task_id'] == TASK_ID]
        if len(rows) != 1:
            raise ValueError('expected exactly one canonical row')
        task = rows[0]
        report['rule_sha256'] = hashlib.sha256(task['program_solution'].encode()).hexdigest()
        for band in ('easy', 'medium', 'hard'):
            for seed in range(args.samples_per_band):
                record = {'band': band, 'seed': seed, 'sample_index': seed}
                counts[band + ':attempted'] += 1
                try:
                    grid = gen.generate(seed, seed, difficulty=band)
                except Exception as exc:
                    fail(record, ['generate:' + type(exc).__name__ + ':' + str(exc)])
                    continue
                counts[band + ':generated'] += 1
                record['input'] = grid
                issues = geometry_issues(grid)
                errors = gen.self_check(grid)
                if errors:
                    issues += ['self_check:' + str(error) for error in errors]
                if issues:
                    fail(record, issues)
                    counts[band + ':geometry_failures'] += 1
                counts[f'{band}:code_{grid[0][0]}'] += 1
                if seed < args.racket_per_band:
                    selected.append(record)

        if args.racket_per_band:
            from arc_repl.racket_bridge import RacketBridge
            from puzzle_generators.rule_wrap import wrap_rule
            wrapped = wrap_rule(task['program_solution'])
            bridge = RacketBridge(timeout=30.0, max_calls_before_restart=48)
            report['racket_path'] = os.environ.get('RACKET_PATH', 'PATH lookup')
            try:
                canon = [{'canonical_pair': i, 'input': p['input'], 'expected': p['output']}
                         for i, p in enumerate(task['train'] + task['test'])]
                all_cases = canon + selected
                for start in range(0, len(all_cases), 16):
                    records = all_cases[start:start + 16]
                    expression = '(let ([f ' + wrapped + ']) (list ' + ' '.join(
                        '(f ' + _literal(record['input']) + ')' for record in records) + '))'
                    try:
                        outputs = bridge.eval_text(expression)
                        if not isinstance(outputs, list) or len(outputs) != len(records):
                            raise ValueError('Racket returned an invalid batch')
                    except Exception as exc:
                        for record in records:
                            fail(record, ['racket:' + type(exc).__name__ + ':' + str(exc)])
                        continue
                    for record, output in zip(records, outputs):
                        counts['racket_pairs_checked'] += 1
                        issues = conservation_issues(record['input'], output)
                        if 'expected' in record:
                            counts['canonical_pairs_checked'] += 1
                            if record['expected'] != output:
                                issues.append('canonical_output_mismatch')
                        if issues:
                            counts['racket_pair_failures'] += 1
                            fail({**record, 'racket_output': output}, issues)
            finally:
                bridge.close()
    report.update(counts=dict(counts), first_failures=first_failures,
                  failure_examples_truncated=counts['failed_cases'] > len(first_failures),
                  passed=counts['failed_cases'] == 0,
                  elapsed_seconds=round(time.monotonic() - started, 3))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation makes accidental evidence replacement visible.
    with args.out.open('x') as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(json.dumps({key: report[key] for key in ['passed', 'counts', 'elapsed_seconds']}, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
