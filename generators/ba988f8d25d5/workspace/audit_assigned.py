#!/usr/bin/env python3
"""Replay this review's findings-only audits in an isolated copied Racket runtime.

Run from the packet root: python3 repo/generators/ba988f8d25d5/workspace/audit_assigned.py
No audited source is edited. Exact cases and labels are written below checks/audits.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

TARGETS = ('9536d5aef3f6', 'aa14c6a9f111')


def independent_output(task, grid):
    if task == TARGETS[0]:
        return [[grid[c][r] or grid[r][c] for c in range(len(grid))]
                for r in range(len(grid))]
    out = [[0] * len(grid[0]) for _ in grid]
    colors = dict.fromkeys(v for row in grid for v in row if v)
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) != 2 or cells[0][0] == cells[1][0] or cells[0][1] == cells[1][1]:
            continue
        rs, cs = zip(*cells)
        for r in range(min(rs), max(rs) + 1):
            for c in range(min(cs), max(cs) + 1):
                if r in (min(rs), max(rs)) or c in (min(cs), max(cs)):
                    out[r][c] = color
    return out


def worker(runtime, out):
    sys.path.insert(0, str(runtime))
    from puzzle_generators.runner import _load_generator_module
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source
    from scripts.generator_semantic_gate import _RuleOracle
    report = {'schema': 'review-assigned-audits-v1', 'seed': 42, 'targets': {}}
    for task in TARGETS:
        gen = _load_generator_module(task)
        source = canonical_rule_source(task)
        rec = {'generator_sha256': hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
               'rule_sha256': hashlib.sha256(source.encode()).hexdigest(),
               'canonical': [], 'cohort': {}, 'override_cases': [], 'malformed_cases': []}
        oracle = _RuleOracle(task)
        try:
            if not oracle.ready:
                raise RuntimeError(oracle.error)
            for index, pair in enumerate(canonical_pairs(task)):
                actual, error = oracle.apply(pair['input'])
                assert not error and actual == pair['output'], (task, index, error)
                assert actual == independent_output(task, pair['input'])
                rec['canonical'].append({'index': index, 'racket_matches': True,
                                         'self_check': gen.self_check(copy.deepcopy(pair['input']))})
            for band in ('easy', 'medium', 'hard'):
                inputs, outputs = set(), set()
                for index in range(100):
                    grid = gen.generate(42, index, difficulty=band)
                    assert not gen.self_check(grid), (task, band, index)
                    actual, error = oracle.apply(grid)
                    assert not error and actual == independent_output(task, grid), (task, band, index, error)
                    assert grid == gen.generate(42, index, difficulty=band)
                    inputs.add(json.dumps(grid)); outputs.add(json.dumps(actual))
                rec['cohort'][band] = {'checked': 100, 'racket_python_matches': 100,
                                       'unique_inputs': len(inputs), 'unique_outputs': len(outputs)}
            cases = ([{'size': 3}, {'markers': 1}, {'n_distinct_colors': 1},
                      {'palette_kind': 'invalid'}, {'nonsense': 999}]
                     if task == TARGETS[0] else
                     [{'grid_h': 7.9}, {'rectangles': 2.9}, {'grid_h': '8'},
                      {'grid_h': True}, {'palette_kind': 'invalid'}])
            for overrides in cases:
                item = {'seed': 42, 'sample_index': 0, 'difficulty': None, 'overrides': overrides}
                try:
                    grid = gen.generate(42, 0, **overrides)
                    output, error = oracle.apply(grid)
                    assert not error, error
                    item.update(accepted=True, input=grid, racket_output=output,
                                dimensions=[len(grid), len(grid[0])],
                                colors=sorted({v for row in grid for v in row if v}),
                                self_check=gen.self_check(grid, meta={'overrides': overrides}))
                except (ValueError, TypeError) as exc:
                    item.update(accepted=False, exception=f'{type(exc).__name__}: {exc}')
                rec['override_cases'].append(item)
            for grid in ([[0, 1], [0]], [[0, 12], [0, 0]], [[0, True], [0, 0]]):
                try:
                    result = {'errors': gen.self_check(copy.deepcopy(grid))}
                except Exception as exc:
                    result = {'exception': f'{type(exc).__name__}: {exc}'}
                rec['malformed_cases'].append({'input': grid, **result})
        finally:
            oracle.close()
        report['targets'][task] = rec
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({task: {'canonical': len(r['canonical']), 'cohort': r['cohort'],
                           'overrides': [{k: v for k, v in c.items() if k not in ('input', 'racket_output')}
                                         for c in r['override_cases']]}
                      for task, r in report['targets'].items()}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('checks/audits/assigned.json'))
    parser.add_argument('--worker-runtime', type=Path)
    args = parser.parse_args()
    if args.worker_runtime:
        worker(args.worker_runtime, args.out)
        return
    root = next(p for p in Path(__file__).resolve().parents if (p/'src/arcpuzzles').is_dir())
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError('Preserve evidence; choose a new --out path')
    contract = json.loads((root.parent/'AUDIT_ASSIGNMENT.json').read_text())
    assert tuple(t['task_id'] for t in contract['targets']) == TARGETS
    for target in contract['targets']:
        path = root/'generators'/target['task_id']/'generator.py'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == target['generator_sha256']
    sys.path.insert(0, str(root/'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    env = dict(os.environ)
    binary = env.get('RACKET_PATH', str(root.parent/'.review/racket-runtime/racket/bin/racket'))
    env['RACKET_PATH'] = binary
    env['PATH'] = str(Path(binary).resolve().parent) + os.pathsep + env.get('PATH', '')
    with tempfile.TemporaryDirectory(prefix='review-audits-') as temporary:
        prepare_runtime(Catalog(root), Path(temporary), task_ids=list(TARGETS))
        subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker-runtime', temporary,
                        '--out', str(out)], cwd=temporary, env=env, timeout=180, check=True)


if __name__ == '__main__':
    main()
