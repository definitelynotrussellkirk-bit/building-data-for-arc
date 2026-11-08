#!/usr/bin/env python3
"""Passive, bounded exact-override replay; no labels, reference calls, or source edits."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import math
import multiprocessing
import sys
import time
import types
from pathlib import Path


def strict_json(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(',', ':'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    def reject(value):
        raise ValueError(f'Non-finite JSON number: {value}')
    return json.loads(path.read_text(), parse_constant=reject)


def generate_input(module, *, seed, sample_index, difficulty, overrides):
    """Local adapter to the documented per-puzzle module.generate interface."""
    return module.generate(seed, sample_index, difficulty=difficulty, **overrides)


def declared_incompatible(module, overrides, exc):
    for entry in getattr(module, 'INCOMPATIBLE_OVERRIDE_COMBINATIONS', ()) or ():
        if isinstance(entry, (list, tuple, set, frozenset)):
            entry = dict.fromkeys(entry)
        if isinstance(entry, dict) and len(entry) >= 2:
            if all(key in overrides and (value is None or overrides[key] in
                   (value if isinstance(value, (list, tuple, set, frozenset)) else [value]))
                   for key, value in entry.items()):
                return True
    for attribute in ('incompatible_axes', 'axes', 'override_axes'):
        axes = getattr(exc, attribute, ())
        if isinstance(axes, (list, tuple, set, frozenset)):
            if len(axes) >= 2 and set(axes) <= set(overrides):
                return True
    return False


def evaluate(module, arguments, expected):
    overrides = arguments['overrides']
    try:
        grid = generate_input(module, **arguments)
    except BaseException as exc:
        incompatible = isinstance(exc, ValueError) and declared_incompatible(module, overrides, exc)
        outcome = 'incompatible' if incompatible else 'error'
        return {'outcome': outcome, 'issues': [] if outcome == expected else
                [{'kind': 'unexpected_rejection', 'expected': expected}],
                'exception': {'type': type(exc).__name__, 'message': str(exc)[:2000]}}
    result = {'outcome': 'accepted', 'issues': []}
    if expected != 'accepted':
        result['issues'].append({'kind': 'unexpected_acceptance', 'expected': expected})
    try:
        if (not isinstance(grid, (list, tuple)) or not 1 <= len(grid) <= 30
            or not all(isinstance(row, (list, tuple)) and 1 <= len(row) <= 30 for row in grid)
            or len({len(row) for row in grid}) != 1
            or any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row)):
            raise ValueError('expected a rectangular 1..30 ARC integer grid')
        grid = [list(row) for row in grid]
        result['input_sha256'] = sha(strict_json(grid).encode())
    except BaseException as exc:
        result['issues'].append({'kind': 'invalid_input', 'message': str(exc)[:1000]})
        return result
    try:
        checker = module.self_check
        parameters = inspect.signature(checker).parameters
        keywords = {}
        if 'difficulty' in parameters:
            keywords['difficulty'] = arguments['difficulty']
        if 'meta' in parameters:
            keywords['meta'] = {**overrides, **arguments}
        messages = checker(grid, **keywords)
        if not isinstance(messages, (list, tuple)):
            raise TypeError('self_check must return a list/tuple of messages')
        if messages:
            result['issues'].append({'kind': 'self_check', 'messages': [str(x) for x in messages]})
    except BaseException as exc:
        result['issues'].append({'kind': 'self_check_error', 'message': f'{type(exc).__name__}: {exc}'[:2000]})
    try:
        observed = module.observe_overrides(grid)
        if not isinstance(observed, dict) or not all(isinstance(k, str) for k in observed):
            raise TypeError('observe_overrides must return a dict with string keys')
        strict_json(observed)
        result['observed'] = observed
        axes = getattr(module, 'AXES', {})
        for name, wanted in overrides.items():
            if wanted is None:
                continue
            spec = axes.get(name, {})
            spec = spec if isinstance(spec, dict) else {}
            required = name in observed or spec.get('type') in ('int', 'bool', 'color') or spec.get('exact') is True
            if required and name not in observed:
                result['issues'].append({'kind': 'missing_observation', 'axis': name, 'requested': wanted})
            elif required and (observed[name] != wanted or isinstance(observed[name], bool) != isinstance(wanted, bool)):
                result['issues'].append({'kind': 'override_mismatch', 'axis': name,
                                         'requested': wanted, 'observed': observed[name]})
    except BaseException as exc:
        result['issues'].append({'kind': 'observer_error', 'message': f'{type(exc).__name__}: {exc}'[:2000]})
    if result['issues']:
        result['input'] = grid
    return result


def worker(connection, module, arguments, expected):
    try:
        result = evaluate(module, arguments, expected)
        # A strict serialization check also prevents accidental non-finite evidence.
        strict_json(result)
        connection.send(result)
    except BaseException as exc:
        connection.send({'outcome': 'error', 'issues': [{'kind': 'probe_worker_error',
                         'message': f'{type(exc).__name__}: {exc}'[:2000]}]})
    finally:
        connection.close()


def bounded_case(context, module, arguments, expected, seconds):
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=worker, args=(child, module, arguments, expected))
    process.start()
    child.close()
    try:
        if parent.poll(seconds):
            try:
                result = parent.recv()
            except EOFError:
                result = {'outcome': 'error', 'issues': [{'kind': 'worker_exited_without_result'}]}
        else:
            result = {'outcome': 'error', 'issues': [{'kind': 'case_timeout', 'seconds': seconds}]}
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join(timeout=1)
        parent.close()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task_id')
    parser.add_argument('--library', type=Path, default=Path.cwd())
    parser.add_argument('--generator-file', type=Path)
    parser.add_argument('--cases', type=Path, required=True)
    parser.add_argument('--seed-start', type=int, default=0)
    parser.add_argument('--seed-stop', type=int, required=True, help='exclusive upper bound')
    parser.add_argument('--seed-step', type=int, default=1)
    parser.add_argument('--sample-index', type=int, action='append')
    parser.add_argument('--difficulty', action='append', help='repeatable; none becomes Python None')
    parser.add_argument('--max-cases', type=int, default=5000)
    parser.add_argument('--max-seconds', type=float, default=120)
    parser.add_argument('--case-timeout', type=float, default=2)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if (args.seed_step <= 0 or args.seed_stop <= args.seed_start or args.max_cases <= 0
        or not math.isfinite(args.max_seconds) or not 0 < args.max_seconds <= 3600
        or not math.isfinite(args.case_timeout) or not 0 < args.case_timeout <= 60):
        parser.error('require a nonempty increasing seed range and finite positive limits')
    if args.out.exists():
        parser.error('--out must be a new file')
    if args.cases.stat().st_size > 65536:
        parser.error('cases JSON exceeds 64 KiB')
    cases = read_json(args.cases)
    if not isinstance(cases, list) or not cases or len(cases) > 128:
        parser.error('cases must be a nonempty list of at most 128 objects')
    for index, case in enumerate(cases):
        if (not isinstance(case, dict) or set(case) - {'id', 'overrides', 'expect'}
            or not isinstance(case.get('id'), str) or not isinstance(case.get('overrides'), dict)
            or case.get('expect', 'accepted') not in ('accepted', 'incompatible')
            or not all(isinstance(k, str) for k in case['overrides'])):
            parser.error(f'invalid case at index {index}')
        case.setdefault('expect', 'accepted')
    if len({case['id'] for case in cases}) != len(cases):
        parser.error('case IDs must be unique')
    seeds = range(args.seed_start, args.seed_stop, args.seed_step)
    indices = args.sample_index or [0]
    bands = [None if band == 'none' else band for band in (args.difficulty or ['none'])]
    planned = len(seeds) * len(indices) * len(bands) * len(cases)
    if planned > args.max_cases:
        parser.error(f'{planned} cases exceed --max-cases {args.max_cases}')
    if 'fork' not in multiprocessing.get_all_start_methods():
        parser.error('this passive prototype requires POSIX fork for per-case timeouts')
    library = args.library.resolve()
    sys.path[:0] = [str(library/'src'), str(library/'shared/runtime')]
    from arcpuzzles import Catalog
    from reviewer_support import find_root
    library = find_root(library)
    descriptor = Catalog(library).describe(args.task_id)
    source = args.generator_file.resolve() if args.generator_file else library/descriptor['generator']
    source_hash = sha(source.read_bytes())
    # A local package name supports task-relative imports without copying any runtime.
    package = types.ModuleType('_exact_override_subject')
    package.__path__ = [str(source.parent)]
    sys.modules[package.__name__] = package
    spec = importlib.util.spec_from_file_location(package.__name__+'.generator', source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    if not callable(getattr(module, 'generate', None)):
        parser.error('target does not expose the documented per-puzzle generate API')
    rows, failures = [], []
    counts = dict(accepted=0, incompatible=0, error=0, failed=0)
    context = multiprocessing.get_context('fork')
    started = time.monotonic()
    for seed in seeds:
        for index in indices:
            for band in bands:
                for case in cases:
                    remaining = args.max_seconds - (time.monotonic() - started)
                    if remaining <= 0:
                        break
                    arguments = dict(seed=seed, sample_index=index, difficulty=band, overrides=case['overrides'])
                    row = bounded_case(context, module, arguments, case['expect'], min(args.case_timeout, remaining))
                    row.update(seed=seed, sample_index=index, difficulty=band, case_id=case['id'])
                    counts[row['outcome']] += 1
                    if row['outcome'] == 'error' or row['issues']:
                        counts['failed'] += 1
                        failures.append({'arguments': arguments, 'expect': case['expect'], **row})
                    rows.append(row)
                if time.monotonic() - started >= args.max_seconds:
                    break
            if time.monotonic() - started >= args.max_seconds:
                break
        if time.monotonic() - started >= args.max_seconds:
            break
    complete = len(rows) == planned
    unchanged = sha(source.read_bytes()) == source_hash
    passed = complete and unchanged and not counts['failed']
    report = {
        'schema': 'passive-exact-override-probe-v1', 'task_id': descriptor['id'],
        'source_file': str(source), 'source_sha256': source_hash,
        'selected_generator_sha256': descriptor['generator_sha256'],
        'source_changed_during_sweep': not unchanged,
        'generator_version': getattr(module, 'VERSION', None),
        'declared_rule_hash': getattr(module, 'RULE_HASH', None),
        'tool_sha256': sha(Path(__file__).read_bytes()), 'cases_sha256': sha(args.cases.read_bytes()),
        'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
        'limits': {'seed_start': args.seed_start, 'seed_stop_exclusive': args.seed_stop,
                   'seed_step': args.seed_step, 'sample_indices': indices, 'difficulties': bands,
                   'planned_cases': planned, 'max_cases': args.max_cases,
                   'case_timeout_seconds': args.case_timeout, 'sweep_seconds': args.max_seconds,
                   'input_grid_max_cells': 900},
        'cases': cases, 'counts': counts, 'executed_cases': len(rows),
        'complete': complete, 'passed': passed, 'elapsed_seconds': round(time.monotonic()-started, 3),
        'input_hash_encoding': 'SHA-256 of compact ASCII JSON list-of-lists; allow_nan=False',
        'first_failure': failures[0] if failures else None, 'failures': failures, 'rows': rows,
        'scope': 'Exact integer/bool/color overrides and all supplied observer keys are compared. '
                 'Other strings/floats are generation controls unless observed or declared exact. '
                 'No reference labels, production resampling, curriculum claims, or full battery. '
                 'Each case runs in a fresh fork after trusted source import.',
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        handle.write(strict_json(report)+'\n')
    print(strict_json({'out': str(args.out), 'source_sha256': source_hash, 'counts': counts,
                      'complete': complete, 'passed': passed, 'first_failure': failures[0] if failures else None}))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
