#!/usr/bin/env python3
"""Pinned, Racket-backed shortcut/lesson census in an isolated runtime copy.

Run from packet root through run_with_racket.py. This probe evaluates input-only
baseline or final generators, never substitutes a Python mirror for labels, and
retains a complete concrete counterexample for each refuted rival.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

TASK = '4a3ababcaceb'
BANDS = (None, 'easy', 'medium', 'hard')
NAMES = ('largest_nonzero_tile', 'first_red_tile', 'copy_all_source_nonzero',
         'overlay_target', 'center_marker_only', 'least_occupied_red_tile',
         'purest_red_tile', 'last_red_tile')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def views(grid):
    width = (len(grid[0]) + 1) // 4
    tiles = [[grid[r+i][c+j] for i in range(3) for j in range(3)]
             for r in range(0, len(grid), 4) for c in range(0, len(grid[0]), 4)]
    source = max(range(len(tiles)), key=lambda i: tiles[i].count(2))
    target = next(i for i, tile in enumerate(tiles) if 3 in tile)
    return width, tiles, source, target


def prediction(grid, mode='correct'):
    cols, tiles, source, target = views(grid)
    if mode == 'largest_nonzero_tile':
        source = max((i for i in range(len(tiles)) if i != target),
                     key=lambda i: sum(v != 0 for v in tiles[i]))
    elif mode == 'first_red_tile':
        source = next(i for i, tile in enumerate(tiles) if 2 in tile)
    elif mode == 'least_occupied_red_tile':
        source = min((i for i,t in enumerate(tiles) if 2 in t), key=lambda i: sum(v != 0 for v in tiles[i]))
    elif mode == 'purest_red_tile':
        source = max((i for i,t in enumerate(tiles) if 2 in t), key=lambda i: tiles[i].count(2) / sum(v != 0 for v in tiles[i]))
    elif mode == 'last_red_tile':
        source = max(i for i,t in enumerate(tiles) if 2 in t)
    elif mode == 'center_marker_only' and tiles[target][4] != 3:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    for offset, value in enumerate(tiles[source]):
        mark = value != 0 if mode in ('largest_nonzero_tile', 'copy_all_source_nonzero') else value == 2
        r, c = 4 * (target // cols) + offset // 3, 4 * (target % cols) + offset % 3
        if mark or mode != 'overlay_target':
            out[r][c] = 8 if mark else 0
    return out


def refutation_gate_errors(report):
    """Require every named rival to be contradicted in every measured lesson.

    This is stricter than detecting rivals that survive AND change a sampled
    query. It deliberately checks only this task's finite declared rival class.
    """
    errors = []
    if report.get('failures') != []:
        errors.append('reference/validator evidence is missing or contains failures')
    for band in BANDS:
        data = report.get('bands', {}).get(str(band), {})
        count = data.get('lesson_count')
        if type(count) is not int or count <= 0:
            errors.append(f'{band}: a positive measured lesson count is required')
            continue
        survival = data.get('three_demo_rival_survivals', {})
        for name in NAMES:
            value = survival.get(name)
            if type(value) is not int or not 0 <= value <= count:
                errors.append(f'{band}/{name}: missing or invalid survival count')
            elif value:
                errors.append(f'{band}/{name}: survives {value}/{count} three-demo lessons')
    return errors


def worker(config_path):
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_rule_source
    config = json.loads(Path(config_path).read_text())
    spec = importlib.util.spec_from_file_location('probe_generator', config['generator'])
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    source = canonical_rule_source(TASK)
    bridge, rule_name = runner._open_bridge_with_rule(runner.wrap_rule(source))
    report = {
        'schema': 'source-bound-contrast-census-v1', 'task_id': TASK,
        'generator_sha256': digest(config['generator']),
        'rule_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'normalized_rule_sha256': hashlib.sha256(' '.join(source.split()).encode()).hexdigest(),
        'runtime_cwd': str(Path.cwd()), 'python_executable': sys.executable,
        'sys_path': sys.path, 'config': config,
        'bands': {}, 'failures': [], 'counterexamples': {}, 'canonical': {},
    }
    seen = set()
    def execute(grid, context):
        actual = runner._apply_rule(bridge, rule_name, grid)
        errors = gen.self_check(grid)
        if errors or actual != prediction(grid):
            report['failures'].append(dict(context, self_check=errors, input=grid,
                                            actual_racket_output=actual, mirror=prediction(grid)))
        seen.add(hashlib.sha256(json.dumps(grid).encode()).hexdigest())
        return actual
    try:
        for line in Path('data/canonical/puzzles.jsonl').read_text().splitlines():
            task = json.loads(line)
            if task['task_id'] == TASK:
                test = task['test'] if isinstance(task['test'], list) else [task['test']]
                pairs = task['train'] + test
                agreements = Counter()
                for i, pair in enumerate(pairs):
                    actual = execute(pair['input'], {'split': 'canonical', 'index': i})
                    if actual != pair['output']:
                        report['failures'].append({'canonical_label_mismatch': i})
                    for name in NAMES:
                        agreements[name] += prediction(pair['input'], name) == actual
                report['canonical'] = {'count': len(pairs), 'rival_agreements': dict(agreements)}
                break
        for band in BANDS:
            agree = Counter({name: 0 for name in NAMES})
            sizes, shapes, palettes, markers = Counter(), Counter(), Counter(), Counter()
            for j in range(config['samples']):
                seed, index = 12000 + j, 7*j + 2
                grid = gen.generate(seed, index, difficulty=band)
                context = {'band': band, 'seed': seed, 'sample_index': index, 'overrides': {}}
                actual = execute(grid, context)
                _, tiles, src, target = views(grid)
                sizes[str(tiles[src].count(2))] += 1
                shapes[f'{len(grid)}x{len(grid[0])}'] += 1
                palettes[','.join(map(str, sorted({v for row in grid for v in row})))] += 1
                markers[str(tiles[target].index(3))] += 1
                for name in NAMES:
                    rival = prediction(grid, name)
                    agree[name] += rival == actual
                    if rival != actual and name not in report['counterexamples']:
                        report['counterexamples'][name] = dict(
                            context, input=grid, actual_racket_output=actual, rival_output=rival,
                            passes_validator=not gen.self_check(grid), generated_in_domain=True)
            # Non-overlapping index windows per seed; not included in ordinary-draw counts.
            survivors, ambiguous = Counter({name: 0 for name in NAMES}), Counter({name: 0 for name in NAMES})
            for j in range(config['lessons']):
                seed, start = 22000 + j, 11*j
                grids = [gen.generate(seed, start+i, difficulty=band) for i in range(4)]
                outputs = [execute(g, {'band': band, 'lesson': j, 'seed': seed, 'sample_index': start+i})
                           for i, g in enumerate(grids)]
                for name in NAMES:
                    survives = all(prediction(g, name) == a for g, a in zip(grids[:3], outputs[:3]))
                    survivors[name] += survives
                    ambiguous[name] += survives and prediction(grids[3], name) != outputs[3]
            report['bands'][str(band)] = {
                'ordinary_count': config['samples'], 'ordinary_seed_range': [12000, 12000+config['samples']-1],
                'sample_index_formula': '7*j+2 for j=0..samples-1', 'rival_agreements': dict(agree),
                'source_sizes': dict(sizes), 'grid_shapes': dict(shapes), 'palettes': dict(palettes),
                'marker_offsets': dict(markers), 'lesson_count': config['lessons'],
                'lesson_seed_range': [22000, 22000+config['lessons']-1], 'lesson_start_formula': '11*j',
                'three_demo_rival_survivals': dict(survivors), 'ambiguous_queries': dict(ambiguous),
            }
    finally:
        bridge.shutdown()
    report['unique_inputs_across_all_checks'] = len(seen)
    report['racket_calls'] = 3 + len(BANDS)*(config['samples'] + 4*config['lessons'])
    gate_errors = refutation_gate_errors(report)
    report['refutation_gate'] = {'required': config.get('require_refutation', False),
                                  'passed': not gate_errors, 'errors': gate_errors}
    Path(config['out']).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('generator_sha256', 'racket_calls', 'unique_inputs_across_all_checks')}))
    print('semantic failures:', len(report['failures']))
    print('lesson refutation gate:', report['refutation_gate'])
    return 1 if report['failures'] or (config.get('require_refutation') and gate_errors) else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path.cwd())
    parser.add_argument('--generator', type=Path)
    parser.add_argument('--samples', type=int, default=120)
    parser.add_argument('--lessons', type=int, default=30)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--require-refutation', action='store_true',
                        help='exit nonzero unless every measured lesson refutes every named rival')
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker)
    if args.samples < 1 or args.lessons < 1 or args.out is None:
        parser.error('positive samples/lessons and --out are required')
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / 'src'))
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.runtime import prepare_runtime
    out = args.out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='contrast-isolated-') as temp:
        root = Path(temp)
        prepare_runtime(Catalog(repo), root, TASK)
        generator = root / f'puzzle_generators/per_puzzle/{TASK}/generator.py'
        if args.generator:
            shutil.copy2(args.generator.resolve(), generator)
        shutil.copy2(__file__, root / 'contrast_probe.py')
        config = dict(samples=args.samples, lessons=args.lessons, generator=str(generator), out=str(out),
                      require_refutation=args.require_refutation)
        (root / 'config.json').write_text(json.dumps(config))
        env = dict(os.environ)
        env.pop('PYTHONPATH', None)
        env.pop('PYTHONHOME', None)
        env['PYTHONNOUSERSITE'] = '1'
        result = subprocess.run([sys.executable, str(root / 'contrast_probe.py'), '--worker', str(root / 'config.json')],
                                cwd=root, env=env, timeout=900, check=False)
        return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
