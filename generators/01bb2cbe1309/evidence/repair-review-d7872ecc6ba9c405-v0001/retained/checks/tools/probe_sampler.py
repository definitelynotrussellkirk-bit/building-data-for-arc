#!/usr/bin/env python3
"""Bounded Python-only native-adapter sampler audit; no Racket label claim.

From WORK/repo: python ../checks/tools/probe_sampler.py --adapter PATH/adapter.py
  --contract PATH/promotion.json --out ../checks/NAME/sampler.json [--seed INT ...]
Each adapter operation has a 15-second POSIX alarm; at most 64 supplied seeds,
16 Cartesian settings, three count choices and one replay per setting are used.
Only this exact adapter file is loaded: its parent is never added to sys.path.
"""
import argparse
from collections import Counter
import copy
from contextlib import contextmanager, redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import signal
import sys


DEFAULT_SEEDS = [0, 1, 2, 3, 7, 17, 31, 63, 127, 255, 1024, 65535,
                 2**31 - 1, 2**32, 2**62, 2**63 - 1]
COUNTS = [(2, 1), (3, 4), (6, 4)]
CALL_TIMEOUT_SECONDS = 15
INVENTORY_EXCLUDED_DIRECTORIES = {'evidence', 'public', 'examples', '__pycache__'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adjacent_inventory(home, contract):
    """Snapshot adjacent regular files, without following directory/file symlinks."""
    paths = set()
    for directory, directories, filenames in os.walk(home, followlinks=False):
        directories[:] = sorted(name for name in directories
                                 if name not in INVENTORY_EXCLUDED_DIRECTORIES
                                 and not (Path(directory) / name).is_symlink())
        for name in filenames:
            path = Path(directory) / name
            if (path.suffix in {'.py', '.rkt', '.json'} and path.is_file()
                    and not path.is_symlink()):
                paths.add(path)
    resources = contract.get('resources', [])
    if not isinstance(resources, list):
        raise ValueError('promotion resources must be a list of file paths')
    for resource in resources:
        if not isinstance(resource, str):
            raise ValueError('promotion resources must be file path strings')
        # Native contracts use repository-relative resources; also support
        # adjacent relative names for standalone adapter fixtures/tool reuse.
        candidates = [Path.cwd() / resource, home / resource]
        path = next((candidate for candidate in candidates
                     if candidate.is_file() and candidate.resolve().is_relative_to(home)), None)
        if path is None:
            raise ValueError(f'promotion resource is not a regular file inside adapter home: {resource}')
        relative = path.relative_to(home) if path.is_relative_to(home) else path.resolve().relative_to(home)
        if any(part in INVENTORY_EXCLUDED_DIRECTORIES for part in relative.parts[:-1]):
            continue
        if any((home / Path(*relative.parts[:index])).is_symlink()
               for index in range(1, len(relative.parts) + 1)):
            raise ValueError(f'promotion resource must not traverse symlinks: {resource}')
        paths.add(home / relative)
    return [{'path': path.relative_to(home).as_posix(), 'sha256': file_hash(path),
             'size_bytes': path.stat().st_size} for path in sorted(paths)]


@contextmanager
def bounded_call():
    def expired(signum, frame):
        raise TimeoutError(f'adapter operation exceeded {CALL_TIMEOUT_SECONDS}s')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, CALL_TIMEOUT_SECONDS)
    try:
        # Adapter chatter must not make console output or retained reports huge.
        with open(os.devnull, 'w') as sink, redirect_stdout(sink), redirect_stderr(sink):
            yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def settings_from(contract):
    if not isinstance(contract, dict):
        raise ValueError('contract must be an object')
    parameters = contract.get('parameters')
    if not isinstance(parameters, dict) or not parameters:
        raise ValueError('parameters must be a nonempty object')
    total = 1
    for name, values in parameters.items():
        if not isinstance(name, str) or not isinstance(values, list) or not values:
            raise ValueError('each parameter must have a nonempty values list')
        if any(type(v) not in (str, int, bool) for v in values):
            raise ValueError('parameter values must be JSON strings, integers or booleans')
        if len({digest(v) for v in values}) != len(values):
            raise ValueError('parameter values must be distinct')
        total *= len(values)
        if total > 16:
            raise ValueError('Cartesian settings exceed the bound of 16')
    if contract.get('limits') != {'demos': [2, 6], 'queries': [1, 4]}:
        raise ValueError('this probe requires limits demos=[2,6], queries=[1,4]')
    names = sorted(parameters)
    return [dict(zip(names, values)) for values in
            itertools.product(*(parameters[name] for name in names))]


def valid_grid(grid):
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        return False
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        return False
    width = len(grid[0])
    return all(type(row) is list and len(row) == width and
               all(type(cell) is int and 0 <= cell <= 9 for cell in row)
               for row in grid)


def probe(adapter_path, contract_path, seeds):
    report = {'schema': 'arcpuzzles-bounded-native-sampler-probe-v1',
              'status': 'failed', 'adapter': str(adapter_path),
              'contract': str(contract_path), 'adapter_sha256': None,
              'contract_sha256': None, 'request_count': 0, 'success_count': 0,
              'replay_count': 0, 'failures': [],
              'adjacent_source_files': {
                  'scope': 'Adjacent files inventory; not complete Python dependency authentication. '
                           'Recursive regular .py/.rkt/.json files plus declared promotion resources '
                           'inside adapter home; symlinks and evidence/public/examples/__pycache__ directories excluded.',
                  'before': None, 'after': None, 'unchanged': None},
              'requested': {'seeds': seeds, 'settings': [], 'counts': COUNTS},
              'execution': {'python_only': True, 'racket_executed': False,
                            'claim': 'Python sampler/claim-label structure only; no Racket execution or label correctness certification.',
                            'call_timeout_seconds': CALL_TIMEOUT_SECONDS,
                            'replay_policy': 'first seed, (6,4), once per setting'},
              'limitations': ['Finite seed and count coverage only.',
                              'Matched input checks assume settings share an input grammar.',
                              'Input size/content statistics are observations, not diversity acceptance gates.']}
    failed = set()
    def fail(kind, message, key=None, **context):
        item = {'kind': kind, 'message': str(message)[:800], **context}
        if key is not None:
            failed.add(key)
            item.update(setting_index=key[0], seed=key[1], demos=key[2], queries=key[3])
        report['failures'].append(item)

    contract = None
    def finish():
        inventory = report['adjacent_source_files']
        if inventory['before'] is not None:
            try:
                inventory['after'] = adjacent_inventory(adapter_path.parent, contract)
                inventory['unchanged'] = inventory['before'] == inventory['after']
                if not inventory['unchanged']:
                    before = {row['path']: row for row in inventory['before']}
                    after = {row['path']: row for row in inventory['after']}
                    changed = sorted(path for path in before.keys() | after.keys()
                                     if before.get(path) != after.get(path))
                    fail('adjacent_source_changed', 'Adjacent files changed during the probe',
                         changed_paths=changed)
                    report['success_count'] = 0
            except Exception as exc:
                inventory['unchanged'] = False
                fail('adjacent_inventory_error', f'{type(exc).__name__}: {exc}')
                report['success_count'] = 0
        report['status'] = 'passed' if not report['failures'] else 'failed'
        return report

    try:
        report['adapter_sha256'] = file_hash(adapter_path)
        report['contract_sha256'] = file_hash(contract_path)
        if adapter_path.parent != contract_path.parent:
            raise ValueError('adapter and promotion contract must be adjacent')
        if not 1 <= len(seeds) <= 64:
            raise ValueError('supply between 1 and 64 seeds')
        contract = json.loads(contract_path.read_text())
        settings = settings_from(contract)
        report['requested']['settings'] = settings
        report['adjacent_source_files']['before'] = adjacent_inventory(adapter_path.parent, contract)
    except Exception as exc:
        fail('invalid_contract', f'{type(exc).__name__}: {exc}')
        return finish()
    try:
        name = '_native_sampler_' + hashlib.sha256(str(adapter_path).encode()).hexdigest()[:24]
        spec = importlib.util.spec_from_file_location(name, adapter_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        with bounded_call():
            spec.loader.exec_module(module)
        if not callable(module.program) or not callable(module.generate):
            raise TypeError('adapter must expose callable program and generate')
    except Exception as exc:
        fail('adapter_load_error', f'{type(exc).__name__}: {exc}')
        return finish()

    # Store only typed-grid fingerprints for comparisons and compact statistics.
    records = {}
    observed = {}
    distinct_by_split = {'train': set(), 'test': set()}
    occurrences = Counter()
    def validate(episode, key, expected):
        if type(episode) is not dict:
            fail('invalid_episode', 'generate must return a dictionary', key)
            return None
        if episode.get('program_solution') != expected or type(episode.get('program_solution')) is not str:
            fail('program_mismatch', 'program_solution differs from program(settings)', key)
        inputs = {}
        all_inputs = []
        for split, count in [('train', key[2]), ('test', key[3])]:
            pairs = episode.get(split)
            if type(pairs) is not list:
                fail('count_mismatch', f'{split} must be a list of {count} pairs', key)
                return None
            if len(pairs) != count:
                fail('count_mismatch', f'{split}: requested {count}, got {len(pairs)}', key)
            fingerprints = []
            # Reject oversized episodes without traversing an unbounded pair tail.
            if len(pairs) > 10:
                return None
            for index, pair in enumerate(pairs):
                if type(pair) is not dict:
                    fail('invalid_pair', f'{split}[{index}] must be an object', key)
                    return None
                for side in ('input', 'output'):
                    if not valid_grid(pair.get(side)):
                        fail('invalid_grid', f'{split}[{index}].{side}: expected rectangular 1..30 grid of exact int colors 0..9', key)
                        return None
                grid = pair['input']
                fingerprint = digest(grid)
                fingerprints.append(fingerprint)
                distinct_by_split[split].add(fingerprint)
                occurrences[f'{len(grid)}x{len(grid[0])}'] += 1
                if fingerprint not in observed:
                    colors = Counter(cell for row in grid for cell in row)
                    observed[fingerprint] = (len(grid), len(grid[0]), colors)
            inputs[split] = fingerprints
            all_inputs.extend(fingerprints)
        if len(set(all_inputs)) != len(all_inputs):
            fail('duplicate_inputs', 'demonstration/query inputs must all be distinct within an episode', key)
        return inputs

    for setting_index, setting in enumerate(settings):
        try:
            with bounded_call():
                expected = module.program(copy.deepcopy(setting))
            if type(expected) is not str or not expected.strip():
                raise TypeError('program(settings) must return nonempty str')
        except Exception as exc:
            fail('program_error', f'{type(exc).__name__}: {exc}', setting_index=setting_index)
            expected = None
        for seed in seeds:
            for demos, queries in COUNTS:
                key = (setting_index, seed, demos, queries)
                report['request_count'] += 1
                try:
                    if expected is None:
                        raise ValueError('setting program failed')
                    with bounded_call():
                        episode = module.generate(seed, copy.deepcopy(setting), demos, queries)
                    inputs = validate(episode, key, expected)
                    # Fingerprint immediately; mutable adapter return buffers cannot
                    # turn an earlier episode into a false deterministic match.
                    records[key] = {'inputs': inputs, 'episode': digest(episode),
                                    'pairs': {split: [digest(pair) for pair in episode[split]]
                                              for split in ('train', 'test')}
                                    if inputs is not None else None}
                except Exception as exc:
                    fail('generation_error', f'{type(exc).__name__}: {exc}', key)
        replay_key = (setting_index, seeds[0], 6, 4)
        report['replay_count'] += 1
        try:
            with bounded_call():
                replay = module.generate(seeds[0], copy.deepcopy(setting), 6, 4)
            if replay_key in records and digest(replay) != records[replay_key]['episode']:
                fail('nondeterminism', 'identical request changed on bounded replay', replay_key)
        except Exception as exc:
            fail('replay_error', f'{type(exc).__name__}: {exc}', replay_key)

    for key, record in records.items():
        inputs = record['inputs']
        if inputs is None:
            continue
        setting_index, seed, demos, queries = key
        baseline_key = (0, seed, demos, queries)
        baseline = records.get(baseline_key, {}).get('inputs')
        if setting_index and baseline is not None and inputs != baseline:
            fail('setting_input_mismatch', 'same seed/counts produced different inputs across settings', key,
                 compared_with_setting_index=0)
            failed.add(baseline_key)
        for other_demos, other_queries in COUNTS:
            other_key = (setting_index, seed, other_demos, other_queries)
            if other_key <= key:
                continue
            other = records.get(other_key, {}).get('inputs')
            if other is None:
                continue
            for split in ('train', 'test'):
                length = min(len(inputs[split]), len(other[split]))
                if record['pairs'][split][:length] != records[other_key]['pairs'][split][:length]:
                    fail('count_prefix_drift', f'{split} prefix changed with demo/query counts', key,
                         compared_counts=[other_demos, other_queries])
                    failed.add(other_key)

    dimensions = Counter()
    colors = Counter()
    for height, width, histogram in observed.values():
        dimensions[f'{height}x{width}'] += 1
        colors.update(histogram)
    report['input_statistics'] = {
        'basis': 'unique typed inputs across all requests/settings; replay excluded',
        'distinct_inputs': len(observed),
        'distinct_demo_inputs': len(distinct_by_split['train']),
        'distinct_query_inputs': len(distinct_by_split['test']),
        'dimensions_unique': dict(sorted(dimensions.items())),
        'dimensions_occurrences': dict(sorted(occurrences.items())),
        'max_height': max((h for h, w, c in observed.values()), default=0),
        'max_width': max((w for h, w, c in observed.values()), default=0),
        'max_area': max((h*w for h, w, c in observed.values()), default=0),
        'grids_30x30': sum(h == 30 and w == 30 for h, w, c in observed.values()),
        'large_grids_area_at_least_400': sum(h*w >= 400 for h, w, c in observed.values()),
        'color_cell_counts': dict(sorted(colors.items())),
        'nonzero_cells': sum(n for color, n in colors.items() if color != 0),
        'total_cells': sum(colors.values()),
        'distinct_inputs_per_setting': [len({fingerprint
            for key, row in records.items() if key[0] == index and row['inputs'] is not None
            for split in ('train', 'test') for fingerprint in row['inputs'][split]})
            for index in range(len(settings))]}
    report['success_count'] = report['request_count'] - len(failed)
    return finish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--adapter', required=True, type=Path)
    parser.add_argument('--contract', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--seed', action='append', type=int)
    args = parser.parse_args()
    report = probe(args.adapter.resolve(), args.contract.resolve(),
                   args.seed if args.seed is not None else DEFAULT_SEEDS)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(f"{report['status']}: {report['success_count']}/{report['request_count']} requests; "
          f"{len(report['failures'])} failures; report={args.out}")
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
