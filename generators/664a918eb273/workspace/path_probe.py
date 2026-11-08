#!/usr/bin/env python3
"""Independent path-domain census and actual-Racket conservation probe.

Run from any directory with --repo-root pointing to the library or portable
runtime. No model, network, or GPU dependencies. JSON retains exact witnesses.
This is diagnostic geometry, not an authoritative label generator.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = '664a918eb273'
D4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
D8 = tuple((r, c) for r in (-1, 0, 1) for c in (-1, 0, 1) if r or c)


def components(grid):
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        stack, cells = [start], {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in D8:
                other = r + dr, c + dc
                if other in unseen:
                    unseen.remove(other)
                    cells.add(other)
                    stack.append(other)
        result.append(cells)
    return sorted(result, key=lambda cells: min(c for _, c in cells))


def inspect_grid(grid):
    parts = components(grid)
    problems, placements = [], []
    previous = None
    occupied = set()
    for cells in parts:
        deg = {p: sum((p[0] + dr, p[1] + dc) in cells for dr, dc in D4) for p in cells}
        endpoints = [p for p in sorted(cells) if deg[p] == 1]
        entry = min(cells, key=lambda p: (p[1], p[0]))
        if len(endpoints) != 2 or any(d not in (1, 2) for d in deg.values()):
            problems.append('not_simple_path')
        if entry not in endpoints:
            problems.append('entry_not_endpoint')
        others = [p for p in endpoints if p != entry]
        exit_cell = others[0] if others else entry
        if exit_cell[1] != max(c for _, c in cells):
            problems.append('exit_not_rightmost')
        if len({grid[r][c] for r, c in cells}) != 1:
            problems.append('multicolor_component')
        dr, dc = (0, 0) if previous is None else (previous[0] - entry[0], previous[1] + 1 - entry[1])
        placed = {(r + dr, c + dc) for r, c in cells}
        if any(r < 0 or r >= len(grid) or c < 0 for r, c in placed):
            problems.append('packed_out_of_bounds')
        if placed & occupied:
            problems.append('packed_overlap')
        occupied.update(placed)
        placements.append((placed, grid[entry[0]][entry[1]]))
        previous = exit_cell[0] + dr, exit_cell[1] + dc
    colors = [grid[next(iter(p))[0]][next(iter(p))[1]] for p in parts]
    result = {'problems': sorted(set(problems)), 'n_paths': len(parts),
              'repeated_color': len(set(colors)) < len(colors),
              'path_lengths': [len(p) for p in parts], 'shape': [len(grid), len(grid[0])],
              'input_mass': sum(bool(v) for row in grid for v in row)}
    if not problems:
        width = max(c for r, c in occupied) + 1
        output = [[0] * width for _ in grid]
        for cells, color in placements:
            for r, c in cells:
                output[r][c] = color
        result['geometric_output'] = output
    return result


def load_generator(path):
    spec = importlib.util.spec_from_file_location('reviewed_generator', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical(root):
    location = root / 'shared/data/canonical/puzzles.jsonl'
    if not location.exists():
        location = root / 'data/canonical/puzzles.jsonl'
    for line in location.open():
        row = json.loads(line)
        if row.get('task_id') == TASK:
            return row
    raise ValueError(f'canonical task {TASK} missing')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo-root', required=True, type=Path)
    ap.add_argument('--generator', type=Path)
    ap.add_argument('--samples', type=int, default=600)
    ap.add_argument('--racket-samples', type=int, default=100)
    ap.add_argument('--out', required=True, type=Path)
    args = ap.parse_args()
    root = args.repo_root.resolve()
    sys.path.insert(0, str(root / 'shared/runtime' if (root / 'shared/runtime').exists() else root))
    path = args.generator or root / 'generators' / TASK / 'generator.py'
    gen = load_generator(path)
    counts, shapes, number, lengths, witnesses, errors = Counter(), Counter(), Counter(), Counter(), {}, []
    rows = []
    for index in range(args.samples):
        band = ('easy', 'medium', 'hard')[index % 3]
        seed, sample = index // 30, index % 10
        try:
            grid = gen.generate(seed, sample, difficulty=band)
            info = inspect_grid(grid)
            if gen.generate(seed, sample, difficulty=band) != grid:
                info['problems'].append('nondeterministic')
            counts.update(info['problems'])
            counts['invalid_geometry'] += bool(info['problems'])
            counts['selfcheck_rejects'] += bool(gen.self_check(grid))
            counts['repeated_color'] += info['repeated_color']
            number[str(info['n_paths'])] += 1
            shapes[str(info['shape'])] += 1
            lengths.update(map(str, info['path_lengths']))
            row = {'seed': seed, 'sample_index': sample, 'difficulty': band, 'input': grid, 'analysis': info}
            rows.append(row)
            for defect in info['problems']:
                witnesses.setdefault(defect, row)
        except Exception as exc:
            errors.append({'seed': seed, 'sample_index': sample, 'difficulty': band,
                           'error': f'{type(exc).__name__}: {exc}'})
    actual = {'checked': 0, 'pixel_loss': 0, 'geometric_mismatches': 0, 'errors': [], 'canonical_matches': 0}
    if args.racket_samples:
        from arc_repl.executor import ArcExecutor
        from arc_repl.builtins import Grid, _unwrap
        task = canonical(root)
        with ArcExecutor(task, use_racket=True) as executor:
            response = executor.step(task['program_solution'])
            if response.startswith('ERROR'):
                raise RuntimeError(response)
            for pair in task['train'] + task['test']:
                actual['canonical_matches'] += _unwrap(executor._apply_rule(Grid(pair['input']))) == pair['output']
            for row in rows[:args.racket_samples]:
                try:
                    output = _unwrap(executor._apply_rule(Grid(row['input'])))
                    actual['checked'] += 1
                    lost = sum(bool(v) for r in output for v in r) != row['analysis']['input_mass']
                    actual['pixel_loss'] += lost
                    if lost and 'racket_pixel_loss' not in witnesses:
                        witnesses['racket_pixel_loss'] = {**row, 'actual_output': output}
                    expected = row['analysis'].get('geometric_output')
                    actual['geometric_mismatches'] += expected is not None and output != expected
                except Exception as exc:
                    actual['errors'].append({'seed': row['seed'], 'sample_index': row['sample_index'], 'error': str(exc)})
    report = {'schema': 'path-domain-probe-v1', 'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'samples_requested': args.samples, 'samples_generated': len(rows), 'counts': dict(counts),
              'shape_count': len(shapes), 'component_counts': dict(number), 'path_lengths': dict(lengths),
              'generation_errors': errors, 'racket': actual, 'witnesses': witnesses}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'witnesses'}, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
