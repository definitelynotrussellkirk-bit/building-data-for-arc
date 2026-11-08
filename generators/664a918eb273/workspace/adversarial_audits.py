#!/usr/bin/env python3
"""Read-only, reproducible probes for the two immutable audit assignments.

Also records the assigned path generator's canonical-fitting anchor shortcut.
Only JSON evidence is written; audited generators are never patched.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from path_probe import components, inspect_grid, load_generator


def rows_for(root, task_id):
    data = root / 'shared/data/canonical/puzzles.jsonl'
    if not data.exists():
        data = root / 'data/canonical/puzzles.jsonl'
    rows = [json.loads(line) for line in data.open() if json.loads(line).get('task_id') == task_id]
    for row in rows:
        if isinstance(row.get('test'), dict):
            row['test'] = [row['test']]
    return rows


def vertical_runs(grid):
    runs = []
    for c in range(len(grid[0])):
        r = 0
        while r < len(grid):
            if grid[r][c] != 3:
                r += 1
                continue
            start = r
            while r < len(grid) and grid[r][c] == 3:
                r += 1
            runs.append((start, c, r - start))
    return runs


def sliding_centers(grid):
    result = [row[:] for row in grid]
    for r in range(1, len(grid) - 1):
        for c in range(len(grid[0])):
            if grid[r - 1][c] == grid[r][c] == grid[r + 1][c] == 3:
                result[r][c] = 4
    return result


def left_justify_rival(grid):
    out = inspect_grid(grid)['geometric_output']
    margin = min(c for r, row in enumerate(out) for c, v in enumerate(row) if v)
    return [row[margin:] for row in out]


def run_rule(executor, grid):
    from arc_repl.builtins import Grid, _unwrap
    try:
        return {'output': _unwrap(executor._apply_rule(Grid(grid)))}
    except Exception as exc:
        return {'error': f'{type(exc).__name__}: {exc}'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo-root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = args.repo_root.resolve()
    sys.path.insert(0, str(root / 'shared/runtime' if (root / 'shared/runtime').exists() else root))
    from arc_repl.executor import ArcExecutor
    report = {'schema': 'review-adversarial-probes-v1', 'audits': {}}
    for task_id in ('ce40117f40f9', 'c3649bc17348'):
        path = root / 'generators' / task_id / 'generator.py'
        gen = load_generator(path)
        task = rows_for(root, task_id)[0]
        info = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'cases': {}}
        with ArcExecutor(task, use_racket=True) as executor:
            load = executor.step(task['program_solution'])
            if load.startswith('ERROR'):
                raise RuntimeError(load)
            if task_id == 'ce40117f40f9':
                for name in ('no_marker', 'no_blob', 'marker_on_blob'):
                    grid = gen.generate(0, 0, texture=name)
                    info['cases'][name] = {'input': grid, 'self_check': gen.self_check(grid), **run_rule(executor, grid)}
                grid = [[0] * 8 for _ in range(8)]
                info['cases']['blank'] = {'input': grid, 'self_check': gen.self_check(grid), **run_rule(executor, grid)}
                grid = gen.generate(0, 0, blob_size=6)
                info['cases']['ignored_blob_size'] = {'seed':0, 'sample_index':0, 'overrides':{'blob_size':6},
                    'input':grid, 'actual_blob_size':sum(v not in (0,9) for row in grid for v in row), 'self_check':gen.self_check(grid)}
                counters = Counter()
                for i in range(300):
                    grid = gen.generate(i // 10, i % 10)
                    blob = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (0,9)]
                    markers = [(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==9]
                    counters['draws'] += 1
                    counters['valid_presence'] += bool(blob) and len(markers)==1
                    if blob and len(markers)==1:
                        counters['destination_down_and_right'] += markers[0][0]>min(r for r,c in blob) and markers[0][1]>min(c for r,c in blob)
                info['census'] = dict(counters)
            else:
                # Exact 3, 4, and 5 green runs side-by-side. This is deliberately
                # a rival-rule probe, not an accidental failed solution.
                grid = [[0] * 8 for _ in range(7)]
                for c, length in ((1,3),(3,4),(5,5)):
                    for r in range(1, 1+length):
                        grid[r][c] = 3
                info['cases']['length_contrast'] = {'input':grid, 'self_check':gen.self_check(grid),
                    'sliding_center_rival':sliding_centers(grid), **run_rule(executor, grid)}
                counters = Counter()
                for i in range(300):
                    sample = gen.generate(i//10, i%10)
                    counters['draws'] += 1
                    counters['all_runs_exactly_three'] += all(length==3 for _,_,length in vertical_runs(sample))
                    if i < 60:
                        result = run_rule(executor, sample)
                        counters['racket_checked'] += 1
                        counters['rival_matches_racket'] += result.get('output') == sliding_centers(sample)
                canonical_pairs = [p for t in rows_for(root,task_id) for p in t['train']+t['test']]
                counters['canonical_pairs'] = len(canonical_pairs)
                counters['rival_matches_canonical'] = sum(sliding_centers(p['input'])==p['output'] for p in canonical_pairs)
                info['census'] = dict(counters)
        report['audits'][task_id] = info
    task_id = '664a918eb273'
    task = rows_for(root,task_id)[0]
    gen = load_generator(root / 'generators' / task_id / 'generator.py')
    grid = gen.generate(17, 1, grid_h=3, grid_w=11, n_paths=3,
                        n_distinct_colors=2, gap=1, anchor_col=1)
    with ArcExecutor(task, use_racket=True) as executor:
        executor.step(task['program_solution'])
        pairs = [p for t in rows_for(root,task_id) for p in t['train']+t['test']]
        counters = Counter()
        for i in range(300):
            sample = gen.generate(i//10, i%10)
            expected = inspect_grid(sample)['geometric_output']
            counters['draws'] += 1
            counters['refutes_left_justify'] += expected != left_justify_rival(sample)
        report['assigned_shortcut'] = {'name':'left_justify_packed_chain',
            'canonical_pairs':len(pairs), 'canonical_matches':sum(left_justify_rival(p['input'])==p['output'] for p in pairs),
            'seed':17, 'sample_index':1, 'overrides':{'grid_h':3,'grid_w':11,'n_paths':3,'n_distinct_colors':2,'gap':1,'anchor_col':1},
            'input':grid, 'self_check':gen.self_check(grid), 'rival_output':left_justify_rival(grid),
            'default_census':dict(counters), **run_rule(executor, grid)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'audits':{k: v['census'] for k,v in report['audits'].items()},
                      'shortcut':{k:v for k,v in report['assigned_shortcut'].items() if k not in ('input','output','rival_output')}},indent=2))

if __name__ == '__main__':
    main()
