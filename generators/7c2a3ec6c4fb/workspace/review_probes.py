#!/usr/bin/env python3
"""Reproduce assigned audit findings and a source-isolated runtime smoke.

Run from the repository via the packet's run_with_racket.py wrapper. Copies the
three selected tasks and shared runtime through prepare_runtime, then executes
this file from the copy with no source checkout on Python's import path.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MAIN = '7c2a3ec6c4fb'
ROW_TASK = '40b155c46f6e'
PANEL_TASK = 'bb1b1e111e1a'
IDS = [MAIN, ROW_TASK, PANEL_TASK]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def row_rule(grid, *, restricted=False):
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        if restricted and r > 0 and r % 2 == 0:
            continue
        counts = Counter(v for v in row if v)
        if len(counts) == 2 and min(counts.values()) == 1 and max(counts.values()) > 1:
            major = max(counts, key=counts.get)
            out[r] = [major if v else 0 for v in row]
    return out


def panels(grid):
    pw = (len(grid[0]) - 2) // 3
    return ([[*row[:pw]] for row in grid],
            [[*row[pw + 1:2 * pw + 1]] for row in grid],
            [[*row[2 * pw + 2:]] for row in grid])


def worker(out, forbidden_source):
    runtime = Path.cwd().resolve()
    # Refuse accidental source fallback. The worker itself lives in this copy.
    assert Path(__file__).resolve().parent == runtime
    assert all(not Path(p).resolve().is_relative_to(forbidden_source) for p in sys.path if p)
    manifest = json.loads((runtime / 'RUNTIME_MANIFEST.json').read_text())
    gen_paths = {tid: next(runtime / x['runtime_path'] for x in manifest['files']
                         if x['library_path'] == f'generators/{tid}/generator.py') for tid in IDS}
    modules = {}
    for tid, path in gen_paths.items():
        spec = importlib.util.spec_from_file_location(f'probe_{tid}', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules[tid] = module
    rules = {}
    for line in (runtime / 'data/canonical/puzzles.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row.get('task_id') in IDS:
            rules[row['task_id']] = row
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule
    wrapped = {tid: wrap_rule(rules[tid]['program_solution']) for tid in IDS}
    identities = {tid: {'task_id': tid, 'generator_sha256': sha(gen_paths[tid]),
                       'rule_sha256': hashlib.sha256(rules[tid]['program_solution'].encode()).hexdigest()}
                  for tid in IDS}
    invocation = {'cwd': str(runtime), 'argv': ['python3', 'review_probes.py', '--worker',
                  '--out', str(out), '--forbidden-source', str(forbidden_source)]}
    out.mkdir(parents=True, exist_ok=True)
    with RacketBridge(max_calls_before_restart=128) as bridge:
        def actual(tid, grid):
            literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
            return bridge.eval_text(f'({wrapped[tid]} {literal})')

        # Fresh copied selected source; all 60 labels checked with Racket.
        failures = []
        for index in range(60):
            difficulty = ('easy', 'medium', 'hard')[index % 3]
            g = modules[MAIN].generate('portable-smoke', index, difficulty=difficulty)
            py = modules[MAIN].rule_mirror(g)
            result = actual(MAIN, g)
            if modules[MAIN].self_check(g) or result != py:
                failures.append({'index': index, 'difficulty': difficulty, 'input': g,
                                 'racket_output': result, 'python_output': py})
        module_paths = {name: str(Path(module.__file__).resolve()) for name, module in sys.modules.items()
                        if name.startswith(('arc_repl', 'puzzle_generators', 'scripts')) and getattr(module, '__file__', None)}
        assert all(Path(p).is_relative_to(runtime) for p in module_paths.values())
        portable = {**identities[MAIN], 'runtime_directory': str(runtime), 'command': invocation,
                    'seed': 'portable-smoke', 'sample_index_range': [0, 59], 'samples': 60,
                    'racket_checked': 60, 'failures': failures, 'import_paths': module_paths,
                    'source_checkout_imported': False}
        (out / 'portable.json').write_text(json.dumps(portable, indent=2) + '\n')

        # Audit 1: missing interior even-row support; validator accepts a shift.
        tid = ROW_TASK
        gen = modules[tid]
        original = rules[tid]['train'][0]['input']
        shifted = [[0] * len(original[0]) for _ in original]
        shifted[0] = original[1][:]
        shifted[2] = original[3][:]
        counter = {**identities[tid], 'input': shifted, 'actual_racket_output': actual(tid, shifted),
                   'rival_output': row_rule(shifted, restricted=True), 'validator_errors': gen.self_check(shifted),
                   'seed': None, 'sample_index': None, 'overrides': None,
                   'construction': 'canonical train[0], move active rows 1->0 and 3->2 (zero-based)',
                   'in_documented_domain': True, 'emitted_by_default_generator': False, 'command': invocation}
        assert counter['actual_racket_output'] == row_rule(shifted)
        assert counter['actual_racket_output'] != counter['rival_output']
        assert not counter['validator_errors']
        canonical_hits = 0
        canonical_total = 0
        for split in ('train', 'test'):
            pairs = rules[tid].get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            for pair in pairs:
                canonical_total += 1
                canonical_hits += row_rule(pair['input'], restricted=True) == pair['output']
                assert actual(tid, pair['input']) == pair['output']
        sample_failures = []
        positive_even_rows = 0
        for index in range(90):
            difficulty = ('easy', 'medium', 'hard')[index % 3]
            grid = gen.generate('audit-rows', index, difficulty=difficulty)
            result = actual(tid, grid)
            positive_even_rows += any(any(row) for r, row in enumerate(grid) if r > 0 and r % 2 == 0)
            if gen.self_check(grid) or result != row_rule(grid, restricted=True):
                sample_failures.append({'index': index, 'input': grid, 'racket_output': result,
                                        'rival_output': row_rule(grid, restricted=True), 'errors': gen.self_check(grid)})
        counter['census'] = {'seed': 'audit-rows', 'sample_index_range': [0, 89], 'samples': 90,
                 'canonical_hits': canonical_hits, 'canonical_pairs': canonical_total,
                 'samples_using_positive_even_rows': positive_even_rows, 'sample_failures': sample_failures}
        (out / f'{tid}.json').write_text(json.dumps(counter, indent=2) + '\n')

        # Audit 2: declared density control is inert; identical_panels are not identical.
        tid = PANEL_TASK
        gen = modules[tid]
        equal_inputs = 0
        for index in range(30):
            a = gen.generate('audit-density', index, mask_density=0.1)
            b = gen.generate('audit-density', index, mask_density=0.9)
            equal_inputs += a == b
        grid = gen.generate('audit-identical', 0, texture='identical_panels')
        mask, a, b = panels(grid)
        result = actual(tid, grid)
        counter = {**identities[tid], 'seed': 'audit-identical', 'sample_index': 0,
                   'overrides': {'texture': 'identical_panels'}, 'input': grid,
                   'actual_racket_output': result, 'rival_output': a,
                   'rival_description': 'The documented identical-panels degeneracy should output A regardless of mask.',
                   'panels_equal': a == b, 'validator_errors': gen.self_check(grid),
                   'in_documented_domain': True, 'emitted_by_declared_texture': True, 'command': invocation,
                   'density_control': {'seed': 'audit-density', 'sample_index_range': [0, 29],
                     'pairs': 30, 'low': 0.1, 'high': 0.9, 'identical_input_pairs': equal_inputs}}
        assert a != b and result != a
        normal_failures = []
        for index in range(90):
            difficulty = ('easy', 'medium', 'hard')[index % 3]
            grid = gen.generate('audit-panels', index, difficulty=difficulty)
            mask, a, b = panels(grid)
            expected = [[a[r][c] if mask[r][c] else b[r][c] for c in range(len(a[0]))] for r in range(len(a))]
            result = actual(tid, grid)
            if gen.self_check(grid) or result != expected:
                normal_failures.append({'index': index, 'input': grid, 'racket_output': result,
                                        'python_output': expected, 'errors': gen.self_check(grid)})
        counter['normal_census'] = {'seed': 'audit-panels', 'sample_index_range': [0, 89],
                                   'samples': 90, 'racket_checked': 90, 'failures': normal_failures}
        (out / f'{tid}.json').write_text(json.dumps(counter, indent=2) + '\n')
        assert not failures and not sample_failures and not normal_failures
    print(json.dumps({'portable_racket_pairs': 60, 'audit_row_pairs': 90,
                      'audit_panel_pairs': 90, 'density_identical_pairs': equal_inputs,
                      'runtime': str(runtime)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    parser.add_argument('--forbidden-source', type=Path)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.worker:
        worker(out, args.forbidden_source.resolve())
        return 0
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / 'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-review-') as tmp:
        runtime = Path(tmp)
        prepare_runtime(Catalog(root), runtime, task_ids=IDS)
        shutil.copy2(__file__, runtime / 'review_probes.py')
        env = {key: value for key, value in os.environ.items() if key not in ('PYTHONPATH', 'ARCPUZZLES_HOME')}
        result = subprocess.run([sys.executable, 'review_probes.py', '--worker', '--out', str(out),
                                 '--forbidden-source', str(root)], cwd=runtime, env=env, check=False)
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
