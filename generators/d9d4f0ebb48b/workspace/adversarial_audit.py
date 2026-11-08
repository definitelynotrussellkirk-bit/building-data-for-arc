#!/usr/bin/env python3
"""Findings-only audit of the packet's two assigned targets; never patches them.

From packet root:
python3 run_with_racket.py python3 generators/d9d4f0ebb48b/workspace/adversarial_audit.py --out ../checks/audits
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TARGETS = ('2fb8d019f6ca', 'bc005ea27dae')


def components(grid):
    visited = set()
    result = []
    for r, row in enumerate(grid):
        for c, v in enumerate(row):
            if not v or (r, c) in visited:
                continue
            cells = {(r, c)}
            queue = deque(cells)
            visited.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < len(grid) and 0 <= nc < len(row)
                            and (nr, nc) not in visited and grid[nr][nc] == v):
                        visited.add((nr, nc)); cells.add((nr, nc)); queue.append((nr, nc))
            edges = sum((rr+dr, cc+dc) not in cells for rr, cc in cells
                        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
            result.append({'color': v, 'area': len(cells), 'edge_perimeter': edges})
    return result


def worker(out, samples):
    from arc_repl.racket_bridge import RacketBridge
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, normalized_rule_hash
    from scripts.rule_smoke import rule_application
    out.mkdir(parents=True, exist_ok=True)
    bridge = RacketBridge(max_calls_before_restart=48)
    reports = []
    try:
        for task in TARGETS:
            gen = importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')
            rule = canonical_rule_source(task)
            counters = Counter()
            witnesses = {}
            seen = set()
            def save(kind, grid, band, seed, index, overrides, details):
                if kind in witnesses:
                    return
                try:
                    actual = bridge.eval_text(rule_application(rule, grid))
                    error = None
                except Exception as exc:
                    actual = None
                    error = f'{type(exc).__name__}: {exc}'
                witnesses[kind] = {
                    'task_id': task, 'generator_sha256': hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
                    'rule_hash': normalized_rule_hash(rule), 'rule_source_sha256': hashlib.sha256(rule.encode()).hexdigest(),
                    'band': band, 'seed': seed, 'sample_index': index, 'overrides': overrides,
                    'input': grid, 'actual_racket_output': actual, 'racket_error': error,
                    'rival_output': None, 'rival_not_applicable': 'Generator/validator contract audit, not a competing transformation.',
                    'validator_findings': gen.self_check(grid), 'details': details,
                    'generated_ordinary_draw': not bool(overrides),
                    'documented_domain': False,
                    'domain_note': 'Returned by generate; violates the cited advertised constraint.',
                }
            for band in ('easy', 'medium', 'hard'):
                for seed in range(samples):
                    index = 1000 + seed
                    grid = gen.generate(seed, index, difficulty=band)
                    counters['generated_grids'] += 1
                    seen.add(json.dumps(grid))
                    counters['self_check_rejections'] += bool(gen.self_check(grid))
                    if task == 'bc005ea27dae':
                        objs = components(grid)
                        perimeters = sorted((o['edge_perimeter'] for o in objs), reverse=True)
                        if len(objs) < 3:
                            counters['fewer_than_three_components'] += 1
                            save('dropped_components', grid, band, seed, index, {}, {'components': objs})
                        if len(perimeters) >= 2 and perimeters[0] == perimeters[1]:
                            counters['non_strict_maximum'] += 1
                            save('perimeter_tie', grid, band, seed, index, {}, {'components': objs})
                    else:
                        template = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v not in (0, 8)}
                        anchors = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
                        stamps = [{(ar+r, ac+c) for r, c in template} for ar, ac in anchors]
                        overlap = set()
                        for i, cells in enumerate(stamps):
                            for later in stamps[i+1:]:
                                overlap |= cells & later
                        if overlap:
                            counters['overlapping_stamped_nonzero_cells'] += 1
                            save('stamp_overlap', grid, band, seed, index, {},
                                 {'anchors': anchors, 'overlap_cells': sorted(overlap),
                                  'scope': 'Collision-free distribution claim, not a Racket execution error.'})
            # Deterministic direct probes of advertised override contracts.
            overrides = {'palette_size': 4, 'n_distinct_colors': 4} if task == TARGETS[0] else {'grid_h': 9, 'grid_w': 11, 'n_objects': 6}
            grid = gen.generate(7, 19, difficulty='medium', **overrides)
            normal = gen.generate(7, 19, difficulty='medium')
            details = {
                'same_as_no_overrides': grid == normal,
                'actual_height': len(grid), 'actual_width': len(grid[0]),
                'actual_nonzero_palette_size': len({v for row in grid for v in row if v}),
                'actual_component_count': len(components(grid)),
            }
            save('ignored_overrides', grid, 'medium', 7, 19, overrides, details)
            canonical_results = []
            for index, pair in enumerate(canonical_pairs(task)):
                try:
                    actual = bridge.eval_text(rule_application(rule, pair['input']))
                    error = None
                except Exception as exc:
                    actual = None; error = f'{type(exc).__name__}: {exc}'
                canonical_results.append({'index': index, 'validator_findings': gen.self_check(pair['input']),
                                          'racket_error': error, 'matches_canonical': actual == pair['output']})
            counters['unique_generated_inputs'] = len(seen)
            report = {'task_id': task, 'generator_sha256': hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
                      'rule_hash': normalized_rule_hash(rule), 'rule_source_sha256': hashlib.sha256(rule.encode()).hexdigest(),
                      'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                      'phase': 'audit-only unchanged source', 'seed_range_inclusive': [0, samples-1],
                      'sample_index_formula': '1000 + seed', 'bands': ['easy', 'medium', 'hard'],
                      'runtime_cwd': str(Path.cwd()), 'counts': dict(counters), 'witnesses': witnesses,
                      'canonical_results': canonical_results}
            (out / f'{task}.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
            reports.append({k: report[k] for k in ('task_id','counts','canonical_results')})
    finally:
        bridge.close()
    print(json.dumps(reports, indent=2))
    return 0  # Findings-only census. Read the reports, not this exit code, for semantic status.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=64)
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.samples <= 0:
        parser.error('--samples must be positive')
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    if args.worker:
        return worker(out, args.samples)
    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo/'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-assigned-audits-') as name:
        runtime = Path(name)
        prepare_runtime(Catalog(repo), runtime, task_ids=list(TARGETS))
        shutil.copy2(__file__, runtime/'adversarial_audit.py')
        command = [sys.executable, 'adversarial_audit.py', '--worker', '--out', str(out), '--samples', str(args.samples)]
        env = dict(os.environ); env.pop('PYTHONPATH', None); env['TERM'] = 'dumb'
        with (out/'run.log').open('w') as log:
            result = subprocess.run(command, cwd=runtime, env=env, stdout=log,
                                    stderr=subprocess.STDOUT, check=False, timeout=600)
        (out/'receipt.json').write_text(json.dumps({'runtime_cwd': name, 'runtime_removed_after_run': True,
                                                   'command': command, 'exit_code': result.returncode}, indent=2)+'\n')
        print((out/'run.log').read_text())
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
