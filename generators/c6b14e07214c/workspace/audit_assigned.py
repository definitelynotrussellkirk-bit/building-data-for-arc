#!/usr/bin/env python3
"""Read-only, hash-bound reproducer for this packet's two assigned audits.

Deliberately incomplete Python candidates are diagnostic rivals, never labels.
All positive outputs are obtained from the selected canonical Racket program.
The command stages both unmodified targets into an isolated portable runtime.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from collections import Counter

TARGETS = ('57f77441c9cd', '2f8ecb96521c')
BANDS = ('easy', 'medium', 'hard')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def gh_one_two_sources():
    grid = [[0, 0, 0, 0, 2, 8] for _ in range(6)]
    grid[0][0] = 5
    return grid


def clamped_cycle_rival(grid):
    """Consume source columns once, then repeat the last; intentionally wrong."""
    h, w = len(grid), len(grid[0])
    gh = next((r for r in range(h) if grid[r][0] != 5), h)
    cs = next(c for c in range(w) if grid[0][c] not in (0, 5))
    out = [[0] * w for _ in range(h)]
    for r in range(h):
        if r < gh: out[r][0] = 5
        out[r][cs - 1] = grid[0][min(cs + r // gh, w - 1)]
    return out


def rect_boxes(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4}
    result = []
    while remaining:
        todo = [min(remaining)]; remaining.remove(todo[0]); cells = []
        while todo:
            r, c = todo.pop(); cells.append((r, c))
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in remaining:
                    remaining.remove(p); todo.append(p)
        result.append((min(r for r, c in cells), min(c for r, c in cells),
                       max(r for r, c in cells), max(c for r, c in cells), len(cells)))
    return sorted(result)


def overlapping_rectangles():
    grid = [[0] * 10 for _ in range(10)]
    for r in range(3):
        for c in range(3, 6): grid[r][c] = 4
    for r in range(5, 8):
        for c in range(2, 6): grid[r][c] = 4
    return grid


def column_projection_rival(grid):
    """Segment by blank columns instead of 2-D connectivity, then rank areas."""
    occupied = [any(row[c] == 4 for row in grid) for c in range(len(grid[0]))]
    runs = []
    for c, active in enumerate(occupied):
        if active and (c == 0 or not occupied[c-1]): runs.append([])
        if active: runs[-1].append(c)
    out = copy.deepcopy(grid)
    if len(runs) != 2:
        return out
    objects = []
    for run in runs:
        cells = [(r, c) for r, row in enumerate(grid) for c in run if row[c] == 4]
        objects.append(cells)
    for color, cells in enumerate(sorted(objects, key=len), 1):
        top, bottom = min(r for r, c in cells), max(r for r, c in cells)
        left, right = min(c for r, c in cells), max(c for r, c in cells)
        for r, c in cells:
            if top < r < bottom and left < c < right: out[r][c] = color
    return out


def _worker(request):
    from puzzle_generators import runner
    from arcpuzzles_worker import canonical_bundle
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

    outdir = Path(request['out_dir'])
    report = {'schema': 'assigned-read-only-audits-v1', 'source': request['sources'],
              'runtime_directory': str(Path.cwd()), 'reproduction': request['reproduction'],
              'sampler': {'bands': list(BANDS), 'seeds': [0, request['seeds']-1],
                          'sample_index': '11 * seed + 3', 'overrides': {},
                          'policy': 'direct generate, no retries; one input per seed per band'},
              'targets': {}, 'harness_failures': []}
    for tid in TARGETS:
        gen = importlib.import_module(f'puzzle_generators.per_puzzle.{tid}.generator')
        source = request['sources'][tid]
        if source['rule_hash'] != canonical_rule_hash(tid):
            raise ValueError('selected authority hash changed')
        bridge, rule_name = runner._open_bridge_with_rule(canonical_bundle(runner, tid, gen).rule_callable_text)
        rival = clamped_cycle_rival if tid == TARGETS[0] else column_projection_rival
        counts = Counter(); hashes = set(); ledger = []; canonical = []
        target = {'generator_unchanged': True, 'source': source,
                  'rival': rival.__name__, 'canonical_pairs': canonical,
                  'counts': counts, 'ledger': ledger, 'override_probes': []}
        report['targets'][tid] = target
        try:
            for i, pair in enumerate(canonical_pairs(tid)):
                if pair.get('output') is None: continue
                actual = runner._apply_rule(bridge, rule_name, pair['input'])
                canonical.append({'pair_index': i, 'input_sha256': digest(pair['input']),
                                  'racket_matches_stored': actual == pair['output'],
                                  'self_check': gen.self_check(copy.deepcopy(pair['input'])),
                                  'rival_matches': rival(copy.deepcopy(pair['input'])) == actual})
                if actual != pair['output']:
                    report['harness_failures'].append(f'{tid}: canonical output {i} differs')
            for band in BANDS:
                for seed in range(request['seeds']):
                    index = 11*seed + 3
                    grid = gen.generate(seed, index, difficulty=band)
                    actual = runner._apply_rule(bridge, rule_name, grid)
                    checks = gen.self_check(copy.deepcopy(grid))
                    candidate = rival(copy.deepcopy(grid))
                    hashes.add(digest(grid)); counts['generated'] += 1
                    counts['validator_passes'] += not checks
                    counts['rival_matches'] += candidate == actual
                    entry = {'seed': seed, 'sample_index': index, 'difficulty': band,
                             'input_sha256': digest(grid), 'racket_output_sha256': digest(actual),
                             'rival_matches': candidate == actual}
                    if tid == TARGETS[0]:
                        gh = next((r for r in range(len(grid)) if grid[r][0] != 5), len(grid))
                        cs = next(c for c, v in enumerate(grid[0]) if v not in (0, 5))
                        entry.update(gh=gh, n_sources=len(grid[0])-cs)
                        counts['gh_one'] += gh == 1
                        counts['two_source_columns'] += len(grid[0])-cs == 2
                        counts['wrap_reached'] += len(grid) > gh*(len(grid[0])-cs)
                    else:
                        boxes = rect_boxes(grid)
                        overlap = max(b[1] for b in boxes) <= min(b[3] for b in boxes)
                        entry['column_spans_overlap'] = overlap
                        counts['overlapping_column_spans'] += overlap
                    ledger.append(entry)
                    if checks: report['harness_failures'].append({'task': tid, 'seed': seed, 'check': checks})
            counts['unique_inputs'] = len(hashes)
            probe_overrides = ([{'gh': 1}, {'cs': 7}, {'anchor_corner': True}, {'anchor_corner': False}]
                               if tid == TARGETS[0] else
                               [{'grid_w': 10}, {'position_bias': 'stacked'}, {'position_bias': 'diagonal'},
                                {'blob1_w': 3}, {'blob1_w': 6}])
            for overrides in probe_overrides:
                try:
                    grid = gen.generate(17, 3, difficulty='medium', **overrides)
                    result = {'input_sha256': digest(grid), 'input': grid,
                              'self_check': gen.self_check(copy.deepcopy(grid))}
                    if tid == TARGETS[1]: result['boxes'] = rect_boxes(grid)
                except Exception as exc:
                    result = {'error': f'{type(exc).__name__}: {exc}'}
                target['override_probes'].append({'seed': 17, 'sample_index': 3, 'difficulty': 'medium',
                                                 'overrides': overrides, **result})
            grid = gh_one_two_sources() if tid == TARGETS[0] else overlapping_rectangles()
            actual = runner._apply_rule(bridge, rule_name, grid)
            candidate = rival(copy.deepcopy(grid))
            fixture = {'task_id': tid, **source, 'seed': None, 'sample_index': None, 'overrides': None,
                       'origin': 'hand-constructed documented-domain counterexample; not a claimed generated draw',
                       'input': grid, 'actual_racket_output': actual, 'rival_output': candidate,
                       'rival_name': rival.__name__, 'self_check': gen.self_check(copy.deepcopy(grid)),
                       'belongs_to_documented_generator_domain': True,
                       'generated_default_support': 'absent by source constraints, corroborated by census',
                       'reproduction': request['reproduction'], 'runtime_directory': str(Path.cwd())}
            fixture['differs'] = actual != candidate
            target['counterexample'] = f'{tid}-counterexample.json'
            (outdir / target['counterexample']).write_text(json.dumps(fixture, indent=2)+'\n')
            if not fixture['differs'] or fixture['self_check']:
                report['harness_failures'].append({'task': tid, 'counterexample_failed': True})
        finally:
            bridge.close()
        print(tid, json.dumps(dict(counts)), flush=True)
    report['harness_passed'] = not report['harness_failures']
    report['scope'] = 'Reproduced findings only; neither audited target is patched or approved. Finite census, not training results.'
    (outdir / 'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return 0 if report['harness_passed'] else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path)
    parser.add_argument('--seeds', type=int, default=100)
    parser.add_argument('--worker', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker: return _worker(json.loads(args.worker.read_text()))
    if args.out_dir is None or args.seeds < 1: parser.error('--out-dir and positive --seeds required')
    out = args.out_dir.resolve()
    if out.exists(): parser.error('refusing to overwrite retained audit evidence')
    out.mkdir(parents=True)
    root = next(p for p in Path(__file__).resolve().parents if (p/'catalog/puzzles.jsonl').is_file())
    sys.path.insert(0, str(root/'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    catalog = Catalog(root)
    sources = {}
    for tid in TARGETS:
        info = catalog.describe(tid)
        sources[tid] = {'generator_sha256': info['generator_sha256'], 'rule_hash': info['rule_hash']}
    request = {'out_dir': str(out), 'sources': sources, 'seeds': args.seeds,
               'reproduction': {'cwd': 'packet_root', 'argv': ['python3','run_with_racket.py','python3',
                   'generators/c6b14e07214c/workspace/audit_assigned.py','--seeds',str(args.seeds),
                   '--out-dir', str(args.out_dir)]}}
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-assigned-audit-') as tmp:
        stage = Path(tmp)
        prepare_runtime(catalog, stage, task_ids=list(TARGETS))
        shutil.copy2(__file__, stage/'audit_probe.py')
        (stage/'request.json').write_text(json.dumps(request))
        result = run_process([sys.executable,'-E','-s','audit_probe.py','--worker','request.json'],
                             stage, timeout=3600, on_output=lambda text: print(text,end='',flush=True))
        if not (out/'report.json').exists():
            (out/'report.json').write_text(json.dumps({'harness_passed': False, 'worker_failure': result,
                                                      'runtime_directory': str(stage)}, indent=2)+'\n')
        for tid in TARGETS:
            if Catalog(root).describe(tid)['generator_sha256'] != sources[tid]['generator_sha256']:
                raise RuntimeError('audit target changed during read-only probe')
        return result['exit_code'] if result['exit_code'] is not None else 2


if __name__ == '__main__':
    raise SystemExit(main())
