#!/usr/bin/env python3
"""Portable bounded maze-authoring census; Python diagnostics are not labels.

Run from any directory, in the library or copied runtime:
  python3 PATH/maze_probe.py --seed 0 --per-band 200 --out NEW_REPORT.json
Only the standard library and this checkout's public reviewer_support are used.
No Racket execution or training-data creation occurs in this tool.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

for ancestor in Path(__file__).resolve().parents:
    support = next((p for p in (ancestor / 'reviewer_support.py',
                               ancestor / 'shared/runtime/reviewer_support.py')
                    if p.is_file()), None)
    if support is not None:
        sys.path.insert(0, str(support.parent))
        break
else:
    raise ImportError('No local reviewer_support.py; keep this tool with its task')

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

TASK_ID = '675dcb932594'
BANDS = ('easy', 'medium', 'hard')
DIRECTIONS = ((-1, 0), (0, 1), (1, 0), (0, -1))
LABEL_BASIS = ('Independent Python predecessor-frontier diagnostic; generated '
               'outputs are not canonical Racket labels or training labels.')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_sha256(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def analyze_grid(grid):
    """Backtrack all equal-distance predecessors of the goal from one BFS.

    Count paths and possible vertical move counts on the predecessor DAG.
    Horizontal counts are D minus vertical counts; no path enumeration occurs.
    """
    grid = normalize_grid(grid)
    endpoints = []
    for marker in (2, 3):
        positions = [(r, c) for r, row in enumerate(grid)
                     for c, value in enumerate(row) if value == marker]
        if len(positions) != 1:
            raise ValueError(f'expected exactly one marker {marker}, found {len(positions)}')
        endpoints.append(positions[0])
    start, goal = endpoints
    h, w = len(grid), len(grid[0])
    distances, parents = {start: 0}, {start: []}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIRECTIONS:
            cell = r + dr, c + dc
            if not (0 <= cell[0] < h and 0 <= cell[1] < w):
                continue
            if grid[cell[0]][cell[1]] == 5:
                continue
            distance = distances[r, c] + 1
            if cell not in distances:
                distances[cell] = distance
                parents[cell] = [(r, c)]
                queue.append(cell)
            elif distances[cell] == distance:
                parents[cell].append((r, c))
    union, pending = set(), [goal] if goal in distances else []
    while pending:
        cell = pending.pop()
        if cell not in union:
            union.add(cell)
            pending.extend(parents[cell])
    paths, vertical = {start: 1}, {start: {0}}
    # Dict insertion order is BFS discovery order, hence distance order.
    for cell in distances:
        if cell == start:
            continue
        paths[cell] = sum(paths[p] for p in parents[cell])
        vertical[cell] = {n + int(cell[0] != p[0])
                          for p in parents[cell] for n in vertical[p]}
    output = [row[:] for row in grid]
    painted = 0
    for r, c in union:
        if grid[r][c] == 0:
            output[r][c] = 8
            painted += 1
    distance = distances.get(goal)
    vcounts = sorted(vertical.get(goal, set()))
    hcounts = sorted({distance - n for n in vcounts}) if distance is not None else []
    nonwall = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 5}
    unseen, components = set(nonwall), 0
    while unseen:
        components += 1
        frontier = [unseen.pop()]
        while frontier:
            r, c = frontier.pop()
            for dr, dc in DIRECTIONS:
                point = r + dr, c + dc
                if point in unseen:
                    unseen.remove(point)
                    frontier.append(point)
    frame = grid[0] + grid[-1] + [row[0] for row in grid] + [row[-1] for row in grid]
    zero_count = sum(v == 0 for row in grid for v in row)
    return {
        'shape': [h, w], 'start': list(start), 'goal': list(goal),
        'input_palette': sorted({v for row in grid for v in row}),
        'complete_wall_frame': all(v == 5 for v in frame),
        'nonwall_components': components, 'shortest_distance': distance,
        'manhattan_distance': abs(start[0] - goal[0]) + abs(start[1] - goal[1]),
        'shortest_path_count': paths.get(goal, 0), 'vertical_move_counts': vcounts,
        'horizontal_move_counts': hcounts,
        'move_count_pairs_vertical_horizontal': [[n, distance - n] for n in vcounts]
            if distance is not None else [],
        'union_zero_count': painted, 'preserved_zero_count': zero_count - painted,
        'reachable_zero_count': sum(grid[r][c] == 0 for r, c in distances),
        'diagnostic_output': output,
    }


def _load_generator(root):
    paths = (root / 'generators' / TASK_ID / 'generator.py',
             root / 'puzzle_generators/per_puzzle' / TASK_ID / 'generator.py')
    path = next((p for p in paths if p.is_file()), None)
    if path is None:
        raise FileNotFoundError(f'No selected generator for {TASK_ID} under {root}')
    runtime = root / 'shared/runtime' if (root / 'shared/runtime').is_dir() else root
    sys.path.insert(0, str(runtime))
    spec = spec_from_file_location('_maze_probe_selected_generator', path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _rule_identity(root):
    records = []
    with canonical_path(root).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get('task_id') == TASK_ID:
                    records.append(row)
    sources = {row.get('program_solution') for row in records}
    if len(sources) != 1 or not all(isinstance(s, str) and s.strip() for s in sources):
        raise ValueError('canonical rule is absent or ambiguous')
    source = sources.pop()
    # This is the reference worker's whitespace normalization, not raw-byte SHA.
    normalized = ' '.join(source.split())
    return {'rule_hash': hashlib.sha256(normalized.encode()).hexdigest()[:12],
            'canonical_rule_text_sha256': hashlib.sha256(source.encode()).hexdigest()}


def _profile(stats):
    """Exact observed morphology profile, independent of the generator hook."""
    return (tuple(stats['shape']), tuple(stats['input_palette']),
            stats['complete_wall_frame'], stats['nonwall_components'],
            stats['union_zero_count'] > 0, stats['preserved_zero_count'] > 0)


def _hook_accepts(module, grid):
    hook = getattr(module, 'strict_canonical_like', None)
    if not callable(hook):
        return None
    result = hook(deepcopy(grid))
    if type(result) is bool:
        return result
    if isinstance(result, (list, tuple)) and all(isinstance(x, str) for x in result):
        return not result
    raise ValueError('strict_canonical_like returned neither bool nor reason strings')


def census(seed=0, per_band=200, *, start_index=0):
    root = find_root(__file__)
    module, generator_path = _load_generator(root)
    generator_sha = sha256(generator_path)
    identity = _rule_identity(root)
    declarations = {}
    for namespace in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS'):
        declared = getattr(module, namespace, {})
        if not isinstance(declared, dict):
            raise ValueError(f'{namespace} must be a dictionary')
        for name, fn in declared.items():
            if not isinstance(name, str) or not callable(fn):
                raise ValueError(f'invalid {namespace} entry: {name!r}')
            declarations[f'{namespace}:{name}'] = fn
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_stats = [analyze_grid(p['input']) for p in pairs]
    profiles = {_profile(s) for s in canonical_stats}
    shapes = {tuple(s['shape']) for s in canonical_stats}
    canonical_fit = {}
    for name, fn in declarations.items():
        if name.startswith('CANONICAL_SHORTCUTS:'):
            matches, errors = [], []
            for i, pair in enumerate(pairs):
                try:
                    matches.append(normalize_grid(fn(deepcopy(pair['input']))) == pair['output'])
                except Exception as exc:
                    matches.append(False)
                    errors.append({'canonical_pair': i, 'error': f'{type(exc).__name__}: {exc}'})
            canonical_fit[name] = {'fits_every_labeled_canonical_pair': all(matches),
                                   'matches': matches, 'errors': errors}
    canonical = []
    for pair, stats in zip(pairs, canonical_stats):
        canonical.append({**{k: pair[k] for k in ('variant', 'split', 'pair_index')},
                          'input_sha256': grid_sha256(pair['input']),
                          'diagnostic_matches_canonical_label': stats['diagnostic_output'] == pair['output'],
                          'strict_hook_accepts': _hook_accepts(module, pair['input']),
                          'stats': {k: v for k, v in stats.items() if k != 'diagnostic_output'}})
    report = {
        'schema': '675dcb932594-maze-authoring-census-v1', 'task_id': TASK_ID,
        'label_basis': LABEL_BASIS, 'root_layout': 'library' if (root / 'shared').is_dir() else 'runtime',
        'generator_path': str(generator_path.relative_to(root)),
        'generator_sha256': generator_sha, 'generator_version': getattr(module, 'VERSION', None),
        **identity, 'declared_rule_hash': getattr(module, 'RULE_HASH', None),
        'tool_sha256': sha256(__file__), 'canonical_ledger_sha256': sha256(canonical_path(root)),
        'seed': seed, 'sample_index_start': start_index,
        'sample_index_stop_exclusive': start_index + per_band, 'per_band': per_band,
        'total_requested_draws': per_band * len(BANDS), 'canonical_pairs': canonical,
        'canonical_shortcut_fit': canonical_fit, 'declared_rivals': sorted(declarations),
        'canonical_profile_definition': ['shape', 'input palette', 'complete wall frame',
                                         'nonwall component count', 'has painted zero', 'has preserved zero'],
        'bands': {}, 'first_counterexamples': {}, 'errors': [],
    }
    for band in BANDS:
        unique, counts, schedule_counts, shape_counts = set(), Counter(), Counter(), Counter()
        rival_counts = {name: 0 for name in declarations}
        rival_errors = {name: 0 for name in declarations}
        for index in range(start_index, start_index + per_band):
            try:
                grid = normalize_grid(module.generate(seed, index, difficulty=band))
                stats = analyze_grid(grid)
                input_sha = grid_sha256(grid)
                unique.add(input_sha)
                counts['successful_draws'] += 1
                counts['strict_hook_acceptance_count'] += _hook_accepts(module, grid) is True
                counts['canonical_shape_count'] += tuple(stats['shape']) in shapes
                counts['canonical_profile_count'] += _profile(stats) in profiles
                counts['multiple_shortest_paths_count'] += stats['shortest_path_count'] > 1
                counts['multiple_move_count_signatures_count'] += len(stats['vertical_move_counts']) > 1
                counts['painted_and_preserved_zero_count'] += stats['union_zero_count'] > 0 and stats['preserved_zero_count'] > 0
                counts['disconnected_open_components_count'] += stats['nonwall_components'] > 1
                counts['distance_above_manhattan_count'] += (stats['shortest_distance'] is not None and
                                                            stats['shortest_distance'] > stats['manhattan_distance'])
                schedule = getattr(module, 'schedule_profile', None)
                if callable(schedule):
                    schedule_counts[str(schedule(seed, index, difficulty=band))] += 1
                shape_counts[f"{stats['shape'][0]}x{stats['shape'][1]}"] += 1
                for name, fn in declarations.items():
                    try:
                        prediction = normalize_grid(fn(deepcopy(grid)))
                        differs = prediction != stats['diagnostic_output']
                        rival_counts[name] += differs
                        if differs and name in canonical_fit and name not in report['first_counterexamples']:
                            report['first_counterexamples'][name] = {
                                'band': band, 'seed': seed, 'sample_index': index,
                                'input_sha256': input_sha, 'input': grid,
                                'diagnostic_output': stats['diagnostic_output'], 'rival_output': prediction,
                                'label_basis': LABEL_BASIS,
                                'stats': {k: v for k, v in stats.items() if k != 'diagnostic_output'},
                            }
                    except Exception as exc:
                        rival_errors[name] += 1
                        report['errors'].append({'band': band, 'sample_index': index,
                                                 'rival': name, 'error': f'{type(exc).__name__}: {exc}'})
            except Exception as exc:
                report['errors'].append({'band': band, 'sample_index': index,
                                         'error': f'{type(exc).__name__}: {exc}'})
        # Explicit zeros matter when comparing against the baseline receipt.
        count_names = ('successful_draws', 'strict_hook_acceptance_count', 'canonical_shape_count',
                       'canonical_profile_count', 'multiple_shortest_paths_count',
                       'multiple_move_count_signatures_count', 'painted_and_preserved_zero_count',
                       'disconnected_open_components_count', 'distance_above_manhattan_count')
        report['bands'][band] = {
            'requested_draws': per_band, 'unique_input_count': len(unique),
            **{name: counts[name] for name in count_names},
            'schedule_profile_counts': dict(sorted(schedule_counts.items())),
            'shape_counts': dict(sorted(shape_counts.items())),
            'rival_refutation_counts': rival_counts, 'rival_error_counts': rival_errors,
        }
    if sha256(generator_path) != generator_sha:
        raise RuntimeError('selected generator changed during census; no report written')
    report['status'] = 'diagnostic_errors' if report['errors'] else 'completed_python_diagnostic'
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--per-band', type=int, default=200)
    parser.add_argument('--start-index', type=int, default=0)
    parser.add_argument('--out', type=Path, required=True, help='new JSON path; existing files are refused')
    args = parser.parse_args(argv)
    if not 1 <= args.per_band <= 10000 or args.start_index < 0:
        parser.error('per-band must be 1..10000 and start-index must be nonnegative')
    if args.out.exists():
        parser.error(f'output already exists: {args.out}')
    report = census(args.seed, args.per_band, start_index=args.start_index)
    report['replay'] = {'argv': list(sys.argv if argv is None else [str(Path(__file__)), *argv]),
                        'cwd': str(Path.cwd())}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)
        handle.write('\n')
    print(json.dumps({'status': report['status'], 'generator_sha256': report['generator_sha256'],
                      'rule_hash': report['rule_hash'], 'draws': report['total_requested_draws'],
                      'output': str(args.out), 'label_basis': LABEL_BASIS}))
    return 1 if report['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
