"""Source-bound default-position and geometric-role audit for c5f62271ea44.

Run from the packet with its supplied runtime wrapper, or from an installed
checkout with Racket on PATH. All execution happens in a fresh copied runtime.
Use --generator PATH to compare a retained baseline without editing the repo.
The JSON report records actual Racket calls, input hashes and held-out scores.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib
import itertools
import json
from pathlib import Path
import shutil
import sys
import tempfile

TASK_ID = 'c5f62271ea44'
TRANSFORMS = ('identity', 'transpose', 'flip_lr', 'rot_cw', 'flip_ud',
              'anti_transpose', 'rot180', 'rot_ccw')
SWAPPING = {'transpose', 'anti_transpose', 'rot_cw', 'rot_ccw'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def transform(grid, name):
    """Independent coordinate implementation, not the generator's mirror."""
    h, w = len(grid), len(grid[0])
    if name == 'identity':
        return deepcopy(grid)
    if name == 'transpose':
        return [[grid[c][r] for c in range(h)] for r in range(w)]
    if name == 'flip_lr':
        return [[grid[r][w - 1 - c] for c in range(w)] for r in range(h)]
    if name == 'rot_cw':
        return [[grid[h - 1 - c][r] for c in range(h)] for r in range(w)]
    if name == 'flip_ud':
        return [[grid[h - 1 - r][c] for c in range(w)] for r in range(h)]
    if name == 'anti_transpose':
        return [[grid[h - 1 - c][w - 1 - r] for c in range(h)] for r in range(w)]
    if name == 'rot180':
        return [[grid[h - 1 - r][w - 1 - c] for c in range(w)] for r in range(h)]
    if name == 'rot_ccw':
        return [[grid[c][w - 1 - r] for c in range(h)] for r in range(w)]
    raise ValueError(name)


def components(cells, eight=False):
    unseen = set(cells)
    sizes = []
    while unseen:
        todo, size = [unseen.pop()], 0
        while todo:
            r, c = todo.pop()
            size += 1
            neighbors = {(r + dr, c + dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                         if (dr or dc) and (eight or abs(dr) + abs(dc) == 1)} & unseen
            unseen -= neighbors
            todo.extend(neighbors)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def geometry(grid):
    """Observe roles independently of self_check/observe_overrides."""
    ones = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    r0, c0 = min(r for r, _ in ones), min(c for _, c in ones)
    r1, c1 = max(r for r, _ in ones), max(c for _, c in ones)
    panel = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
    ph, pw = len(panel), len(panel[0])
    markers = {(1, 1), (1, pw - 2), (ph - 2, 1), (ph - 2, pw - 2)}
    body = {(r, c) for r, row in enumerate(panel) for c, v in enumerate(row)
            if v != 1 and (r, c) not in markers}
    outside = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row)
               if v and not (r0 <= r <= r1 and c0 <= c <= c1)]
    kr0, kc0 = min(r for r, _, _ in outside), min(c for _, c, _ in outside)
    kr1, kc1 = max(r for r, _, _ in outside), max(c for _, c, _ in outside)
    return {
        'input_shape': [len(grid), len(grid[0])], 'panel_shape': [ph, pw],
        'palette': sorted({v for row in grid for v in row}),
        'body_area': len(body), 'components4': components(body), 'components8': components(body, True),
        'key_span': [kr1 - kr0 + 1, kc1 - kc0 + 1],
        'panel': panel, 'outside': outside, 'key_box': [kr0, kc0, kr1, kc1],
    }


def key_intervention(grid, info, name):
    result = deepcopy(grid)
    for r, c, _ in info['outside']:
        result[r][c] = 0
    expected = transform(info['panel'], name)
    h, w = len(expected), len(expected[0])
    corners = (expected[1][1], expected[1][w - 2], expected[h - 2][1], expected[h - 2][w - 2])
    r0, c0, r1, c1 = info['key_box']
    for (r, c), value in zip(((r0, c0), (r0, c1), (r1, c0), (r1, c1)), corners):
        if value != 1:
            result[r][c] = value
    return result, expected


def worker(args):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from puzzle_generators import runner
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source
    gen = importlib.import_module(f'puzzle_generators.per_puzzle.{TASK_ID}.generator')
    out = Path(args.out)
    failures, exceptions, counts = [], [], Counter()
    source = canonical_rule_source(TASK_ID)
    report = {
        'schema': 'c5f62271ea44-role-position-audit-v1', 'task_id': TASK_ID,
        'python': sys.version, 'generator_version': gen.VERSION,
        'generator_sha256': file_hash(gen.__file__), 'probe_sha256': file_hash(__file__),
        'reference_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'reference_rule_hash': hashlib.sha256(' '.join(source.split()).encode()).hexdigest()[:12],
        'seed_range': [0, args.seeds - 1], 'sample_indices': list(range(8)),
        'label_authority': 'selected canonical Racket; Python mirrors only compared',
    }
    bridge, rule = runner._open_bridge_with_rule(runner.wrap_rule(source))

    def execute(grid):
        counts['racket_calls'] += 1
        return runner._apply_rule(bridge, rule, grid)

    def check(grid, context, expected=None):
        try:
            saved = deepcopy(grid)
            actual = execute(grid)
            errors = gen.self_check(grid) + gen.strict_canonical_like(grid)
            if errors:
                raise AssertionError(errors)
            if gen.rule_mirror(grid) != actual:
                raise AssertionError('Python mirror differs from canonical Racket')
            if expected is not None and actual != expected:
                raise AssertionError('Racket differs from independent expected output')
            if grid != saved:
                raise AssertionError('input mutated by check or execution')
            return actual
        except Exception as exc:
            counts['case_failures'] += 1
            if len(exceptions) < 20:
                exceptions.append({'context': context, 'error': f'{type(exc).__name__}: {exc}', 'input': grid})
            return None

    observed = {i: [] for i in range(8)}
    body_counts, key_counts, profile_roles = Counter(), Counter(), Counter()
    example_rows, interventions = [], []
    try:
        canonical = canonical_pairs(TASK_ID)
        unique = {}
        canonical_rows = []
        for i, pair in enumerate(canonical):
            check(pair['input'], {'canonical': i}, pair['output'])
            counts['canonical_rows'] += 1
            pair_hash = digest(pair)
            unique[pair_hash] = pair
            info = geometry(pair['input'])
            canonical_rows.append({**{k: info[k] for k in ('input_shape', 'panel_shape', 'palette', 'body_area', 'components4', 'components8', 'key_span')},
                                   'pair_sha256': pair_hash})
        report['canonical'] = canonical_rows
        report['canonical_unique_pairs'] = len(unique)
        for seed in range(args.seeds):
            for index in range(8):
                grid = gen.generate(seed, index, difficulty='medium')
                output = check(grid, {'seed': seed, 'sample_index': index, 'difficulty': 'medium'})
                counts['default_samples'] += 1
                if output is None:
                    continue
                info = geometry(grid)
                matches = [name for name in TRANSFORMS if transform(info['panel'], name) == output]
                if len(matches) != 1:
                    failures.append(f'nonunique output orientation at seed={seed}, index={index}: {matches}')
                    continue
                label = matches[0]
                observed[index].append(label)
                if label != gen.schedule_profile(seed, index, 'medium'):
                    failures.append(f'observed/scheduled transform mismatch at {seed}/{index}')
                body_counts[str(len(info['components4']))] += 1
                key_counts['x'.join(map(str, info['key_span']))] += 1
                profile_roles[str((tuple(info['input_shape']), tuple(info['panel_shape']), tuple(info['palette']), len(info['components4']), tuple(info['key_span'])))] += 1
                if seed < 2:
                    example_rows.append({'seed': seed, 'sample_index': index, 'symmetry': label,
                                         'input': grid, 'output': output, 'pair_sha256': digest([grid, output])})
                    interventions.append((grid, info))
        report['default_body_component_counts'] = dict(body_counts)
        report['default_key_span_counts'] = dict(key_counts)
        report['joint_role_counts'] = dict(profile_roles)
        if not any(int(k) > 1 for k in body_counts):
            failures.append('default distribution never reaches a fragmented body (3/4 unique canonical bodies are fragmented)')
        if not any(max(map(int, k.split('x'))) > 5 for k in key_counts):
            failures.append('default distribution never reaches canonical-scale external keys')
        position_rows = []
        for index, labels in observed.items():
            split = args.seeds // 2
            train, test = labels[:split], labels[split:]
            if not train or not test:
                failures.append(f'insufficient successful position observations at {index}')
                continue
            majority = Counter(train).most_common(1)[0][0]
            correct = sum(label == majority for label in test)
            accuracy = correct / len(test)
            position_rows.append({'sample_index': index, 'counts': dict(Counter(labels)),
                                  'fit_seed_range': [0, split - 1], 'test_seed_range': [split, args.seeds - 1],
                                  'fitted_fixed_transform': majority, 'heldout_correct': correct,
                                  'heldout_count': len(test), 'heldout_accuracy': accuracy})
            if len(set(labels)) < 8 or accuracy >= .5:
                failures.append(f'position-only shortcut at index {index}: {majority}, held-out {correct}/{len(test)}, {len(set(labels))}/8 transforms observed')
        report['position_only_baseline'] = position_rows
        report['query_position_notes'] = {'3_demo_query': 3, '4_demo_query': 4,
            'scope': 'held-out generator seeds, not held-out puzzle families or a trained Qwen model'}
        canonical_scores = {}
        for n_train in (3, 4):
            row = next(r for r in position_rows if r['sample_index'] == n_train)
            name = row['fitted_fixed_transform']
            correct = sum(transform(geometry(p['input'])['panel'], name) == p['output'] for p in unique.values())
            canonical_scores[str(n_train)] = {'transform': name, 'correct': correct, 'count': len(unique)}
        report['fixed_transform_on_unique_canonical'] = canonical_scores
        for seed in range(args.seeds):
            order = [gen.schedule_profile(seed, i) for i in range(8)]
            if set(order) != set(TRANSFORMS):
                failures.append(f'incomplete eight-transform schedule at seed {seed}')
            for start in range(8):
                window = {order[(start + j) % 8] for j in range(4)}
                if len(window) < 4 or not window & SWAPPING or not window - SWAPPING:
                    failures.append(f'invalid teaching window at {seed}/{start}')
        domains = {k: gen.AXES[k]['valid'].split('|') for k in gen.AXES}
        for case_id, values in enumerate(itertools.product(*domains.values())):
            overrides = dict(zip(domains, values))
            for difficulty in ('easy', 'medium', 'hard'):
                context = {'matrix_case': case_id, 'seed': 10000 + case_id,
                           'sample_index': case_id % 8, 'difficulty': difficulty, 'overrides': overrides}
                try:
                    grid = gen.generate(10000 + case_id, case_id % 8, difficulty=difficulty, **overrides)
                    output = check(grid, context)
                    observed_axes = gen.observe_overrides(grid)
                    if any(observed_axes.get(k) != v for k, v in overrides.items()):
                        raise AssertionError(f'override mismatch: {observed_axes}')
                    if gen.self_check(grid, meta={'overrides': overrides}):
                        raise AssertionError('self_check rejects matching override metadata')
                except Exception as exc:
                    counts['case_failures'] += 1
                    if len(exceptions) < 20:
                        exceptions.append({'context': context, 'error': f'{type(exc).__name__}: {exc}'})
                counts['override_matrix_samples'] += 1
        for case_id, (grid, info) in enumerate(interventions):
            for name in TRANSFORMS:
                changed, expected = key_intervention(grid, info, name)
                check(changed, {'key_intervention': case_id, 'transform': name}, expected)
                counts['key_interventions'] += 1
        # A full lesson is checked against Racket labels, not Python-only labels.
        for seed in (0, 1, 17, 77):
            for start in range(8):
                pairs = []
                for index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                    grid = gen.generate(seed, index, difficulty='medium')
                    pairs.append({'input': grid, 'output': execute(grid)})
                errors = gen.lesson_identifiable(pairs[:-1], pairs[-1])
                if errors:
                    failures.append(f'lesson failed at {seed}/{start}: {errors}')
                counts['lessons'] += 1
    finally:
        bridge.shutdown()
    if counts['case_failures']:
        failures.append(f"{counts['case_failures']} failed execution/grammar/override cases")
    report.update(counts=dict(counts), failures=failures, exception_examples=exceptions,
                  status='failed' if failures else 'passed')
    (out / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    (out / 'examples.json').write_text(json.dumps(example_rows, separators=(',', ':')) + '\n')
    print(json.dumps({'status': report['status'], 'counts': dict(counts), 'failures': failures}, indent=2))
    return int(bool(failures))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--generator', type=Path, help='optional retained baseline implementation')
    parser.add_argument('--seeds', default=128, type=int)
    parser.add_argument('--tests', action='store_true', help='also execute the current task-local pytest file')
    parser.add_argument('--worker', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.seeds < 64:
        parser.error('--seeds must be at least 64 for the held-out concentration gate')
    if args.worker:
        return worker(args)
    library = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(library / 'src'))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='arc-role-position-') as temporary:
        stage = Path(temporary)
        prepare_runtime(Catalog(library), stage, TASK_ID)
        if args.generator:
            shutil.copyfile(args.generator.resolve(), stage / f'puzzle_generators/per_puzzle/{TASK_ID}/generator.py')
        shutil.copyfile(__file__, stage / 'scripts/task_review_probe.py')
        command = [sys.executable, 'scripts/task_review_probe.py', '--worker', '--out', str(out), '--seeds', str(args.seeds)]
        run = run_process(command, stage, timeout=300)
        (out / 'process.json').write_text(json.dumps(run, indent=2) + '\n')
        print(run['stdout'], end='')
        if run['stderr']:
            print(run['stderr'], file=sys.stderr, end='')
        rc = int(run['exit_code'] != 0 or run['timed_out'])
        if args.tests:
            test = library / f'generators/{TASK_ID}/tests/test_generator_{TASK_ID}.py'
            shutil.copyfile(test, stage / 'test_review_main.py')
            result = run_process([sys.executable, '-m', 'pytest', '-q', 'test_review_main.py'], stage, timeout=180)
            result['test_source_sha256'] = file_hash(test)
            (out / 'pytest.json').write_text(json.dumps(result, indent=2) + '\n')
            print(result['stdout'], end='')
            if result['stderr']:
                print(result['stderr'], file=sys.stderr, end='')
            rc |= int(result['exit_code'] != 0 or result['timed_out'])
        return rc


if __name__ == '__main__':
    raise SystemExit(main())
