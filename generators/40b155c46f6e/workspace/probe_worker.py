"""Portable, stdlib-only review driver run inside an independently copied runtime.

Never import a sibling checkout. All authoritative outputs are executed by the
runtime's Racket bridge; no Python fallback is permitted.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
TASK = '40b155c46f6e'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def norm(grid):
    return [[int(v) for v in row] for row in grid]


def get_canonical(task):
    with (HERE / 'data/canonical/puzzles.jsonl').open() as stream:
        for line in stream:
            item = json.loads(line)
            if item.get('task_id') == task:
                test = item.get('test', [])
                pairs = item['train'] + ([test] if isinstance(test, dict) else test)
                return item, [{'input': norm(p['input']), 'output': norm(p['output'])} for p in pairs]
    raise ValueError(f'no canonical row for {task}')


def load_from_file(path):
    spec = importlib.util.spec_from_file_location('review_baseline_generator', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_reference(grid):
    result = deepcopy(grid)
    for r, row in enumerate(grid):
        counts = Counter(v for v in row if v)
        if len(counts) == 2:
            common, rare = sorted(counts, key=counts.get, reverse=True)
            if counts[rare] == 1 and counts[common] > 1:
                result[r] = [common if v == rare else v for v in row]
    return result


def bridge_for(task):
    from puzzle_generators import runner
    canonical, pairs = get_canonical(task)
    program = canonical['program_solution']
    loaded = runner._load_bundle(task)
    # Explicit canonical binding: never allow the loader's archival preference
    # to silently choose a different authority for a measured comparison.
    bundle = replace(loaded, rule_source=program, rule_callable_text=runner.wrap_rule(program),
                     rule_file='data/canonical/puzzles.jsonl')
    bridge, name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    return runner, bundle, bridge, name, pairs


def canonical_checks(runner, bundle, bridge, name, pairs, rivals):
    fits = {rival: 0 for rival in rivals}
    failures = []
    for index, pair in enumerate(pairs):
        actual = runner._apply_rule(bridge, name, pair['input'])
        if actual != pair['output']:
            failures.append({'kind': 'canonical_authority_mismatch', 'pair_index': index,
                             'input': pair['input'], 'actual': actual, 'expected': pair['output']})
        for rival, fn in rivals.items():
            if fn(deepcopy(pair['input'])) == actual:
                fits[rival] += 1
    return {'pairs': len(pairs), 'rival_fit_counts': fits, 'failures': failures}


def coverage(request):
    from puzzle_generators import runner
    runtime_module = importlib.import_module(f'puzzle_generators.per_puzzle.{TASK}.generator')
    module = runtime_module
    if request['mode'] == 'baseline':
        module = load_from_file(HERE / 'baseline_generator.py')
    runner, bundle, bridge, name, canonical_pairs = bridge_for(TASK)
    bundle = replace(bundle, generator_module=module)
    # Before/after use the same declared diagnostic family, bound to the final
    # diagnostic-source hash. Do not claim that the baseline declared hooks.
    rivals = dict(runtime_module.LESSON_COMPETITORS)
    shortcuts = dict(runtime_module.CANONICAL_SHORTCUTS)
    source = Path(module.__file__)
    result = {
        'schema': 'arcpuzzles-task-lesson-probe-v1', 'task_id': TASK, 'phase': request['mode'],
        'generator_sha256': sha(source), 'diagnostic_generator_sha256': sha(runtime_module.__file__),
        'worker_sha256': sha(__file__), 'rule_sha256': hashlib.sha256(bundle.rule_source.encode()).hexdigest(),
        'runtime_directory': str(HERE), 'sampler': 'puzzle_generators.runner.run_one',
        'sampler_policy': '3 demos + 1 query; each seed tested at starts 0,1,2; overlapping windows, not independent lessons',
        'seeds_per_band': request['seeds_per_band'], 'base_seed': request['seed'],
        'canonical_shortcuts': sorted(shortcuts), 'lesson_competitors': sorted(rivals),
        'bands': {}, 'counterexamples': {}, 'failures': [],
    }
    global_unique = set()
    try:
        result['canonical'] = canonical_checks(runner, bundle, bridge, name, canonical_pairs, shortcuts)
        result['failures'].extend(result['canonical']['failures'])
        if any(n != len(canonical_pairs) for n in result['canonical']['rival_fit_counts'].values()):
            result['failures'].append({'kind': 'declared_shortcut_not_canonical_perfect'})
        for band_index, band in enumerate(('easy', 'medium', 'hard')):
            unique = set()
            tally = Counter()
            witness_hits = Counter()
            rival_stats = {r: Counter() for r in rivals}
            replays = []
            for offset in range(request['seeds_per_band']):
                seed = request['seed'] + band_index*100000 + offset
                for start in range(3):
                    inst = runner.run_one(TASK, seed=seed, sample_index=start, n_train=3, n_test=1,
                                          bundle=bundle, bridge=bridge, fn_name=name, difficulty=band)
                    tally['lessons'] += 1
                    tally['pair_slots'] += 4
                    rejected = inst.get('rejections', [])
                    tally['rejections'] += len(rejected)
                    pairs = inst['train'] + inst['test']
                    replay = {'seed': seed, 'sample_index': start,
                              'input_sha256': [grid_hash(p['input']) for p in pairs],
                              'surviving_rivals': [], 'rejections': rejected}
                    replays.append(replay)
                    for pair_index, pair in enumerate(pairs):
                        grid, actual = pair['input'], pair['output']
                        key = grid_hash(grid)
                        new = key not in unique
                        unique.add(key); global_unique.add(key)
                        if not new:
                            continue
                        tally['unique_inputs'] += 1
                        if module.self_check(grid):
                            result['failures'].append({'kind': 'self_check', 'band': band, 'seed': seed,
                                                       'sample_index': start, 'pair_index': pair_index,
                                                       'input': grid, 'errors': module.self_check(grid)})
                        if row_reference(grid) != actual:
                            result['failures'].append({'kind': 'python_racket_mismatch', 'input': grid,
                                                       'actual': actual, 'python': row_reference(grid)})
                        tally['racket_python_agreements'] += row_reference(grid) == actual
                        tally['positive_even_active_inputs'] += any(r > 0 and r % 2 == 0 and any(row)
                                                                   for r, row in enumerate(grid))
                        for witness, fn in runtime_module.SEMANTIC_WITNESSES.items():
                            if fn(grid):
                                witness_hits[witness] += 1
                                if not any(runtime_module.SEMANTIC_RIVALS[r](deepcopy(grid)) != actual
                                           for r in runtime_module.WITNESS_RIVALS[witness]):
                                    result['failures'].append({'kind': 'false_witness', 'witness': witness,
                                                               'input': grid, 'actual': actual})
                        for rival, fn in rivals.items():
                            predicted = fn(deepcopy(grid))
                            if predicted != actual and rival not in result['counterexamples']:
                                result['counterexamples'][rival] = {
                                    'task_id': TASK, 'generator_sha256': result['generator_sha256'],
                                    'rule_sha256': result['rule_sha256'], 'seed': seed, 'sample_index': start,
                                    'difficulty': band, 'pair_index': pair_index, 'rejections': rejected,
                                    'sampler': 'runner.run_one', 'input': grid, 'actual_racket_output': actual,
                                    'rival_output': predicted, 'self_check_errors': module.self_check(grid),
                                    'in_documented_generator_domain': not bool(module.self_check(grid)),
                                }
                    for rival, fn in rivals.items():
                        fits = all(fn(deepcopy(p['input'])) == p['output'] for p in inst['train'])
                        query = inst['test'][0]
                        agrees = fn(deepcopy(query['input'])) == query['output']
                        key = 'refuted' if not fits else 'survived_all' if agrees else 'query_discriminates'
                        rival_stats[rival][key] += 1
                        if fits:
                            replay['surviving_rivals'].append(rival)
                    if request['mode'] == 'final' and replay['surviving_rivals']:
                        result['failures'].append({'kind': 'lesson_surviving_rivals', 'band': band,
                                                   **replay, 'pairs': pairs})
            result['bands'][band] = {
                'seed_range_inclusive': [request['seed'] + band_index*100000,
                                         request['seed'] + band_index*100000 + request['seeds_per_band']-1],
                'cyclic_starts': [0, 1, 2], **dict(tally), 'witness_hits_on_unique_inputs': dict(witness_hits),
                'rivals': {r: {k: counts.get(k, 0) for k in ('refuted', 'survived_all', 'query_discriminates')}
                           for r, counts in rival_stats.items()}, 'replays': replays,
            }
        # Reproduce the predecessor audit's concrete validator-accepted witness.
        shifted = deepcopy(canonical_pairs[0]['input'])
        shifted[0], shifted[2] = shifted[1], shifted[3]
        shifted[1], shifted[3] = [0]*len(shifted[0]), [0]*len(shifted[0])
        result['shifted_canonical_witness'] = {
            'task_id': TASK, 'generator_sha256': result['generator_sha256'],
            'rule_sha256': result['rule_sha256'], 'input': shifted,
            'actual_racket_output': runner._apply_rule(bridge, name, shifted),
            'rival_output': rivals['restricted_rows'](deepcopy(shifted)),
            'self_check_errors': module.self_check(shifted),
            'in_documented_generator_domain': not bool(module.self_check(shifted)),
            'construction': 'canonical train[0] active rows shifted from [1,3] to [0,2]',
        }
        result['global_unique_inputs'] = len(global_unique)
        result['passed'] = not result['failures']
        return result
    finally:
        bridge.close()


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    if request['mode'] not in ('baseline', 'final'):
        raise ValueError('coverage worker supports only baseline/final')
    result = coverage(request)
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'mode': request['mode'], 'passed': result['passed'],
                      'report': sys.argv[2], 'failures': len(result.get('failures', []))}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
