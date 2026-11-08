#!/usr/bin/env python3
"""Findings-only, reproducible adversarial audits for this packet's two targets.

Does not modify either target. Executes canonical Racket in a fresh copied
runtime. Reports domain restrictions separately from generated defects.
"""
from __future__ import annotations
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

TASKS = ('9c75b1456763', 'cdf26af5c935')


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bbox_fill_by_color(grid):
    """Rival: fill one bounding box per color, even with more than four markers."""
    out = [list(row) for row in grid]
    for color in sorted({v for row in grid for v in row} - {0}):
        points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
        for r in range(min(p[0] for p in points), max(p[0] for p in points) + 1):
            for c in range(min(p[1] for p in points), max(p[1] for p in points) + 1):
                out[r][c] = color
    return out


def bbox_interior_network_rival(grid):
    """Rival: ignore interior holes when filling each component's bounding box."""
    left = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    out = [list(row) for row in grid]
    while left:
        origin = min(left); left.remove(origin); component = {origin}; todo = [origin]
        while todo:
            r, c = todo.pop()
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in left:
                    left.remove(p); component.add(p); todo.append(p)
        markers = [grid[r][c] for r, c in sorted(component) if grid[r][c] not in (0, 1)]
        if not markers:
            continue
        for r in range(min(p[0] for p in component) + 1, max(p[0] for p in component)):
            for c in range(min(p[1] for p in component) + 1, max(p[1] for p in component)):
                out[r][c] = markers[0]
    return out


def worker():
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs, _pinned_seed
    rows = {d['task_id']: d for d in map(json.loads, Path('data/canonical/puzzles.jsonl').read_text().splitlines()) if d.get('task_id') in TASKS}
    reports = {}
    for task in TASKS:
        bundle = runner._load_bundle(task); gen = bundle.generator_module
        program = rows[task]['program_solution']
        source = {'task_id': task, 'generator_sha256': file_sha(gen.__file__),
                  'rule_sha256': hashlib.sha256(program.encode()).hexdigest(),
                  'rule_hash': hashlib.sha256(program.encode()).hexdigest()[:12]}
        bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(program))
        def evidence(grid, rival, *, seed=None, sample_index=None, overrides=None, domain=None):
            actual = runner._apply_rule(bridge, name, grid)
            return dict(source, seed=seed, sample_index=sample_index, overrides=overrides or {},
                        input=grid, actual_racket_output=actual, rival_output=rival(grid),
                        self_check_errors=gen.self_check(grid), documented_generator_domain=domain,
                        rival_disagrees=rival(grid) != actual)
        try:
            if task == TASKS[0]:
                ov = {'grid_h': 18, 'grid_w': 18, 'n_rects': 3, 'rect_h': 7, 'rect_w': 7}
                grid = gen.generate(0, 0, difficulty='hard', **ov)
                underfill = evidence(grid, bbox_interior_network_rival, seed=0, sample_index=0,
                                     overrides={'difficulty': 'hard', **ov}, domain=True)
                underfill.update(requested_rectangles=3,
                                 realized_markers=sum(v not in (0, 1) for row in grid for v in row))
                hole = [[0]*10 for _ in range(10)]
                for r in range(2, 8):
                    for c in range(2, 8):
                        hole[r][c] = 1
                hole[6][6] = 5; hole[3][3] = 0
                hole_report = evidence(hole, bbox_interior_network_rival, domain=False)
                hole_report['construction'] = '10x10; 6x6 blue rectangle [2:8,2:8], marker 5 at (6,6), interior hole (3,3)'
                assert underfill['realized_markers'] == 2 and underfill['self_check_errors'] == []
                assert hole_report['self_check_errors'] == [] and hole_report['rival_disagrees']
                reports[task] = dict(source, underfilled_override=underfill,
                                     validator_accepts_nonsolid_rectangle=hole_report,
                                     classification='two reproduced defects; target unchanged')
            else:
                pairs = canonical_pairs(task)
                canon_matches = sum(bbox_fill_by_color(p['input']) == p['output'] for p in pairs)
                extension = [[0]*9 for _ in range(9)]
                for a, b in ((1, 3), (5, 7)):
                    for r in (a, b):
                        for c in (a, b):
                            extension[r][c] = 2
                outside = evidence(extension, bbox_fill_by_color, domain=False)
                outside['construction'] = 'color-2 corners of [1..3]x[1..3] and [5..7]x[5..7]'
                stats, failures, ledger = {}, {}, []
                all_inputs = set()
                for band in ('easy', 'medium', 'hard'):
                    counts, starts = Counter(), Counter()
                    unique = set()
                    for k in range(100):
                        seed, start = _pinned_seed(task, f'lesson:{band}', k), k * 11
                        inst = runner.run_one(task, seed, start, n_train=gen.EXAMPLES_NEEDED, n_test=1,
                                              bundle=bundle, bridge=bridge, fn_name=name, difficulty=band)
                        reasons = gen.lesson_identifiable(inst['train'], inst['test'][0])
                        counts['lessons'] += 1; counts['lesson_contract_failures'] += bool(reasons)
                        starts[start % 6] += 1
                        if reasons:
                            failures.setdefault(band, dict(source, band=band, seed=seed,
                                sample_index=start, reasons=reasons, actual_racket_instance=inst,
                                documented_generator_domain=True,
                                self_check_errors=[gen.self_check(p['input']) for p in inst['train']+inst['test']]))
                        for p in inst['train'] + inst['test']:
                            digest = hashlib.sha256(json.dumps(p['input'], separators=(',', ':')).encode()).hexdigest()
                            unique.add(digest); all_inputs.add(digest)
                            counts['pairs'] += 1
                            counts['self_check_failures'] += bool(gen.self_check(p['input']))
                            counts['bbox_rival_matches'] += bbox_fill_by_color(p['input']) == p['output']
                        ledger.append({'band': band, 'seed': seed, 'start_sample_index': start, 'reasons': reasons})
                    stats[band] = dict(counts, unique_inputs=len(unique), start_residue_counts=dict(starts))
                assert canon_matches == len(pairs) and outside['rival_disagrees'] and outside['self_check_errors']
                reports[task] = dict(source, canonical_bbox_rival_matches=canon_matches,
                    canonical_pair_denominator=len(pairs), same_color_two_rectangle_extension=outside,
                    lesson_sampler='runner.run_one, EXAMPLES_NEEDED=3, n_test=1; gate pinned seed; start=k*11; k=0..99',
                    bands=stats, first_failing_lesson_per_band=failures, lessons=ledger,
                    unique_inputs_all_bands=len(all_inputs),
                    classification='generated lesson-contract failures plus separately scoped domain limitation; target unchanged')
        finally:
            bridge.close()
    print(json.dumps({'schema': 'assignment-adversarial-audits-v1', 'probe_sha256': file_sha(__file__),
                      'runtime_directory': str(Path.cwd()), 'tasks': reports}, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    ap.add_argument('--out', type=Path)
    args = ap.parse_args()
    if args.worker:
        return worker()
    if args.out is None or args.out.exists():
        ap.error('--out must name a new file')
    root = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(root/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    with tempfile.TemporaryDirectory(prefix='assigned-audits-') as folder:
        stage = Path(folder); prepare_runtime(Catalog(root), stage, task_ids=list(TASKS))
        shutil.copy2(__file__, stage/'audit_probe.py')
        result = run_process([sys.executable, '-B', 'audit_probe.py', '--worker'], stage, timeout=300)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if result['exit_code'] or result['timed_out']:
        args.out.write_text(json.dumps(result, indent=2)+'\n'); return 2
    report = json.loads(result['stdout']); report['worker_stderr'] = result['stderr']
    args.out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({task: {'classification': r['classification'], 'bands': r.get('bands')}
                      for task, r in report['tasks'].items()}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
