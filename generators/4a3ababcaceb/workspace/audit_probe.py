#!/usr/bin/env python3
"""Findings-only, source-bound audit of the packet's two immutable audit draws.

Runs actual canonical Racket in a relocated runtime; does not edit audit targets.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TARGETS = ('e46c2557ad08', 'bb41378fe3c8')


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def domino(grid, color_sensitive=True):
    out = [r[:] for r in grid]
    seen = set()
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not value or (r, c) in seen:
                continue
            component, stack = set(), [(r, c)]
            seen.add((r, c))
            while stack:
                a, b = stack.pop()
                component.add((a, b))
                for x, y in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if (0 <= x < len(grid) and 0 <= y < len(row) and
                            (x,y) not in seen and grid[x][y] == value):
                        stack.append((x,y));seen.add((x,y))
            if len(component) == 2 and len({a for a,b in component}) == 1:
                if not color_sensitive or value == 5:
                    for a,b in component:
                        out[a][b] = 8
    return out


def shadow(grid, overwrite=False):
    out = [r[:] for r in grid]
    for r in range(len(grid)-1):
        for c in range(len(grid[0])-1):
            if grid[r][c] == 2 and (overwrite or grid[r+1][c+1] == 0):
                out[r+1][c+1] = 5
    return out


def worker(out):
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_rule_source
    rows = {r['task_id']: r for r in map(json.loads, Path('data/canonical/puzzles.jsonl').read_text().splitlines())
            if r['task_id'] in TARGETS}
    reports = {'schema': 'source-bound-audit-v1', 'runtime_cwd': str(Path.cwd()),
               'argv': sys.argv, 'sys_path': sys.path, 'targets': {}}
    for tid in TARGETS:
        gen = importlib.import_module(f'puzzle_generators.per_puzzle.{tid}.generator')
        rule = canonical_rule_source(tid)
        bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(rule))
        report = {'task_id': tid, 'generator_sha256': hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
                  'rule_sha256': sha(rule), 'normalized_rule_sha256': sha(' '.join(rule.split())),
                  'cases': [], 'failures': [], 'bands': {}, 'canonical': {}}
        correct = domino if tid == TARGETS[0] else shadow
        rival = (lambda g: domino(g, False)) if tid == TARGETS[0] else (lambda g: shadow(g, True))
        def run_case(grid, context, *, documented_domain=True):
            actual = runner._apply_rule(bridge, name, grid)
            guess = rival(grid)
            checker = getattr(gen, 'self_check', None)
            return dict(context, input=grid, actual_racket_output=actual, rival_output=guess,
                        generator_sha256=report['generator_sha256'], rule_sha256=report['rule_sha256'],
                        validator_available=callable(checker),
                        validator_findings=checker(grid) if callable(checker) else None,
                        belongs_to_documented_generator_domain=documented_domain,
                        correct_mirror_matches=(correct(grid) == actual))
        try:
            test = rows[tid]['test'] if isinstance(rows[tid]['test'], list) else [rows[tid]['test']]
            pairs = rows[tid]['train'] + test
            canonical_agree = canonical_match = 0
            for pair in pairs:
                grid = [[int(v) for v in row] for row in pair['input']]
                answer = [[int(v) for v in row] for row in pair['output']]
                case = run_case(grid, {'origin': 'canonical'})
                canonical_agree += case['actual_racket_output'] == case['rival_output']
                canonical_match += case['actual_racket_output'] == answer
                if not case['correct_mirror_matches']:
                    report['failures'].append(case)
            report['canonical'] = {'count': len(pairs), 'rival_agreements': canonical_agree,
                                   'racket_matches_published': canonical_match}
            for band in (None, 'easy', 'medium', 'hard'):
                agree = valid = correct_count = 0
                for seed in range(64):
                    grid = gen.generate(seed, 0, difficulty=band)
                    case = run_case(grid, dict(origin='ordinary', seed=seed, sample_index=0, difficulty=band, overrides={}))
                    agree += case['actual_racket_output'] == case['rival_output']
                    valid += case['validator_findings'] in (None, [])
                    correct_count += case['correct_mirror_matches']
                    if not case['correct_mirror_matches']:
                        report['failures'].append(case)
                report['bands'][str(band)] = dict(count=64, seed_range=[0,63], sample_index=0,
                                                  rival_agreements=agree, validator_clean_or_absent=valid,
                                                  mirror_matches_racket=correct_count)
            if tid == TARGETS[0]:
                grid = [[0]*9 for _ in range(7)]
                grid[1][1] = grid[1][2] = 5
                grid[4][5] = grid[4][6] = 1
                report['cases'].append(run_case(grid, {'finding_id': 'A1-color', 'origin': 'constructed',
                    'description': 'Color-blind horizontal domino rival; rule-lawful extension, outside all-gray input promise.'},
                    documented_domain=False))
                try:
                    gen.generate(0, 0, domino_count=6)
                    error = None
                except (TypeError, ValueError) as exc:
                    error = f'{type(exc).__name__}: {exc}'
                report['override_reproducer'] = dict(finding_id='A1-axis', seed=0, sample_index=0,
                    difficulty=None, overrides={'domino_count': 6}, declared_valid=gen.AXES['domino_count']['valid'], error=error)
            else:
                underfill = Counter()
                for seed in range(200):
                    grid = gen.generate(seed, 0, grid_h=6, grid_w=6, n_markers=7)
                    underfill[str(sum(row.count(2) for row in grid))] += 1
                report['marker_count_census'] = dict(count=200, seed_range=[0,199], sample_index=0,
                    overrides={'grid_h':6,'grid_w':6,'n_markers':7}, observed_counts=dict(underfill))
                grid = gen.generate(1, 0, grid_h=6, grid_w=6, n_markers=7)
                case = run_case(grid, dict(finding_id='A2-count', origin='generated', seed=1, sample_index=0,
                    overrides={'grid_h':6,'grid_w':6,'n_markers':7}, requested_marker_count=7,
                    actual_marker_count=sum(row.count(2) for row in grid)))
                report['cases'].append(case)
                grid = gen.generate(13, 0)
                report['cases'].append(run_case(grid, dict(finding_id='A2-block', origin='generated', seed=13,
                    sample_index=0, overrides={}, description='A default nuisance cell occupies a red marker shadow; Racket preserves it.'),
                    documented_domain=False))
                report['blocked_case_domain_note'] = ('Generated on the default path and accepted by self_check, but violates '
                    'the summary/comment claim that shadow destinations are empty and decoys never block them.')
        finally:
            bridge.shutdown()
        reports['targets'][tid] = report
    Path(out).write_text(json.dumps(reports, indent=2)+'\n')
    print(json.dumps({tid: {'failures': len(r['failures']), 'canonical': r['canonical']} for tid,r in reports['targets'].items()}))
    return 1 if any(r['failures'] for r in reports['targets'].values()) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--worker', action='store_true')
    args = parser.parse_args()
    if args.worker:
        return worker(args.out)
    repo = Path.cwd()
    sys.path.insert(0, str(repo / 'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='audit-isolated-') as temp:
        root = Path(temp)
        prepare_runtime(Catalog(repo), root, task_ids=list(TARGETS))
        shutil.copy2(__file__, root / 'audit_probe.py')
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        env['PYTHONNOUSERSITE'] = '1'
        return subprocess.run([sys.executable, str(root/'audit_probe.py'), '--worker', '--out', str(out)],
                              cwd=root, env=env, timeout=900, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
