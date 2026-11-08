#!/usr/bin/env python3
"""Source-bound lesson census worker; public entry: arcpuzzles lesson-census."""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import sys


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


RIVAL_NAMESPACES = ('LESSON_COMPETITORS', 'SEMANTIC_RIVALS', 'CANONICAL_SHORTCUTS')


def _named_callable_key(binding, fn):
    namespace, separator, name = binding.partition(':')
    local_name = name if separator and namespace in RIVAL_NAMESPACES else binding
    return local_name, id(fn)


def rival_inventory(rivals):
    """Describe exact named-callable aliases, not mathematical equivalence."""
    groups, identities = {}, {}
    for binding, fn in sorted(rivals.items()):
        key = _named_callable_key(binding, fn)
        if key not in groups:
            groups[key] = binding
            identities[binding] = {'name': key[0], 'declared_in': [], 'bindings': []}
        record = identities[groups[key]]
        namespace = binding.partition(':')[0]
        if namespace in RIVAL_NAMESPACES:
            record['declared_in'].append(namespace)
        record['bindings'].append(binding)
    return {'unique_rivals': len(identities), 'declaration_bindings': len(rivals),
            'rival_identities': identities}


def _prediction(cache, binding, fn, pair):
    input_hash = digest(pair['input'])
    key = (*_named_callable_key(binding, fn), input_hash)
    if key not in cache:
        try:
            value = _support().normalize_grid(fn(deepcopy(pair['input'])))
            cache[key] = (fn, True, value)
        except Exception as exc:
            cache[key] = (fn, False, exc)
    # Holding the callable prevents object-ID reuse while this cache is alive.
    _, ok, value = cache[key]
    # The semantic gate consumes the existing per-binding cache view directly.
    cache[(binding, input_hash)] = (ok, value)
    if not ok:
        raise value
    return value


def declared_rivals(gen):
    rivals, errors = {}, []
    for attribute in RIVAL_NAMESPACES:
        declaration = getattr(gen, attribute, None)
        if declaration is None:
            continue
        if not isinstance(declaration, dict):
            errors.append(f'{attribute}: expected dict of named callables')
            continue
        for name, fn in declaration.items():
            if not isinstance(name, str) or not callable(fn):
                errors.append(f'{attribute}:{name}: expected string name and callable')
            else:
                rivals[f'{attribute}:{name}'] = fn
    return rivals, errors


@lru_cache(maxsize=1)
def _support():
    # Resolve only this tool's own tree, never a sibling or ambient import.
    from importlib.util import spec_from_file_location, module_from_spec
    helper = Path(__file__).resolve().parents[1] / 'reviewer_support.py'
    if not helper.exists():
        helper = Path(__file__).resolve().parents[1] / 'runtime/reviewer_support.py'
    spec = spec_from_file_location('_census_support', helper)
    support = module_from_spec(spec)
    spec.loader.exec_module(support)
    return support


def score_lesson(gen, rivals, lesson, *, prediction_cache=None):
    cache = {} if prediction_cache is None else prediction_cache
    def prediction(name, fn, pair):
        return _prediction(cache, name, fn, pair)
    result = {'rivals': {}, 'rival_witnesses': {}, 'ambiguous': False, 'warnings': [], 'errors': [],
              'contract': 'rivals' if rivals else ('hook_only' if hasattr(gen, 'lesson_identifiable') else 'none')}
    for name, fn in sorted(rivals.items()):
        try:
            fits = all(prediction(name, fn, p) == p['output'] for p in lesson['train'])
            agrees = all(prediction(name, fn, p) == p['output'] for p in lesson['test'])
            status = 'refuted' if not fits else ('survived_all' if agrees else 'ambiguous')
            result['rivals'][name] = status
            result['ambiguous'] |= status == 'ambiguous'
            if status == 'ambiguous':
                for index, query in enumerate(lesson['test']):
                    value = prediction(name, fn, query)
                    if value != query['output']:
                        result['rival_witnesses'][name] = {
                            'query_index': index, 'input': deepcopy(query['input']),
                            'expected_output': deepcopy(query['output']), 'rival_output': deepcopy(value)}
                        break
        except Exception as exc:
            result['rivals'][name] = 'error'
            result['errors'].append(f'{name}: {type(exc).__name__}: {exc}')
    hook = getattr(gen, 'lesson_identifiable', None)
    if hook is not None:
        for query in lesson['test']:
            try:
                reasons = hook(deepcopy(lesson['train']), deepcopy(query))
                if not isinstance(reasons, (list, tuple)) or any(not isinstance(x, str) for x in reasons):
                    raise TypeError('lesson_identifiable must return list[str]')
                result['warnings'].extend(reasons)
            except Exception as exc:
                result['errors'].append(f'lesson_identifiable: {type(exc).__name__}: {exc}')
    from review_diagnostics import search_lesson
    result['searched_rivals'] = search_lesson(gen, lesson)
    return result


def score_rotations(gen, rivals, lesson, *, prediction_cache=None):
    """Hold out every labelled pair once, preserving the remaining pair order.

    Reuses predictions for pure, deterministic rivals; no new authority calls.
    Each result addresses the same materialized instance, not a new draw.
    """
    if len(lesson['test']) != 1:
        raise ValueError('Query rotation requires exactly one query')
    pairs = lesson['train'] + lesson['test']
    cache = {} if prediction_cache is None else prediction_cache
    rotations = []
    for query_index, query in enumerate(pairs):
        train_indices = [i for i in range(len(pairs)) if i != query_index]
        rotated = {'train': [pairs[i] for i in train_indices], 'test': [query]}
        rotations.append({'query_index': query_index, 'train_indices': train_indices,
                          **score_lesson(gen, rivals, rotated, prediction_cache=cache)})
    return rotations


SUMMARY_FIELDS = ('requested', 'materialized', 'materialization_errors', 'pairs',
                  'ambiguous', 'hook_warnings', 'scoring_errors', 'rotations',
                  'ambiguous_rotations', 'rotation_hook_warnings', 'rotation_scoring_errors')


def _verdict(scores, *, errors, contract):
    if errors or any(row.get('errors') for row in scores):
        return 'error'
    if any(row.get('ambiguous') for row in scores):
        return 'ambiguous'
    if contract == 'none':
        return 'no_contract'
    if any(row.get('warnings') for row in scores):
        return 'warning'
    return 'no_ambiguity_found' if contract == 'rivals' else 'hook_only'


def census(request, checkpoint=None):
    from puzzle_generators import runner
    task_id = request['task_id']
    bundle = runner._load_bundle(task_id)
    if bundle.kind != 'per_puzzle':
        raise ValueError('Lesson census currently supports per-puzzle generators only')
    gen = bundle.generator_module
    rivals, errors = declared_rivals(gen)
    demos = request['n_demos']
    if demos is None:
        demos = getattr(gen, 'EXAMPLES_NEEDED', 3)
    if type(demos) is not int or demos < 1:
        raise ValueError('EXAMPLES_NEEDED / n_demos must be a positive integer')
    period = request['period']
    enumerate_schedule = request.get('enumerate_schedule_period', False)
    if type(enumerate_schedule) is not bool:
        raise ValueError('enumerate_schedule_period must be a boolean')
    schedule_period = getattr(gen, 'LESSON_SCHEDULE_PERIOD', None) if enumerate_schedule else None
    schedule_seed = request.get('schedule_seed', 0)
    if enumerate_schedule:
        if type(schedule_period) is not int or schedule_period < 1:
            raise ValueError('Schedule enumeration requires an explicit positive integer LESSON_SCHEDULE_PERIOD')
        if type(schedule_seed) is not int or not 0 <= schedule_seed < 2**32:
            raise ValueError('schedule_seed must be an integer in [0, 2**32)')
    draw_count = schedule_period if enumerate_schedule else request['per_band']
    rotate = request.get('rotate_query', False)
    if type(rotate) is not bool:
        raise ValueError('rotate_query must be a boolean')
    rotate = rotate or enumerate_schedule
    if rotate and request['n_queries'] != 1:
        raise ValueError('Query rotation requires exactly one query')
    rotation_policy = request.get('rotation_policy', 'require')
    if rotation_policy not in ('require', 'diagnostic'):
        raise ValueError('rotation_policy must be require or diagnostic')
    report = {'schema': 'arcpuzzles-lesson-census-v1', 'task_id': task_id,
              'generator_sha256': hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
              'rule_source_sha256': hashlib.sha256(bundle.rule_source.encode()).hexdigest(),
              'rule_callable_sha256': hashlib.sha256(bundle.rule_callable_text.encode()).hexdigest(),
              'rule_task_id': bundle.rule_task_id, 'rule_file': str(bundle.rule_file),
              'declared_rule_hash': getattr(gen, 'RULE_HASH', None),
              'contract': 'rivals' if rivals else ('hook_only' if hasattr(gen, 'lesson_identifiable') else 'none'),
              'rivals': sorted(rivals), 'errors': errors, 'lessons': [], 'per_band': {},
              'status': 'incomplete', 'production_status': 'incomplete',
              'rotation_status': 'incomplete' if rotate else 'not_requested',
              'rotation_policy': rotation_policy, 'canonical_rival_fit': {},
              'summary': {**dict.fromkeys(SUMMARY_FIELDS, 0), 'unique_inputs': 0},
              'sampler': {**request, 'n_demos': demos, 'rotate_query': rotate, 'per_band': draw_count,
                          'rotation_recipe': 'hold out every labelled pair once; preserve remaining order' if rotate else None,
                          'seed_recipe': ("schedule_seed fixed across all starts and bands" if enumerate_schedule else
                                          "sha256('lesson-census:v1:TASK:BAND:INDEX')[:8] as uint32"),
                          'start_recipe': 'index (consecutive requested starts; accepted indices may advance)',
                          'authority': 'runner.run_one with selected canonical Racket rule'},
              'limits': ['Finite declared-rival census, not proof of identifiability.',
                         'Unique inputs are exact normalized grid hashes, not semantic equivalence.',
                         'Start residues describe requested starts. Accepted pair residues use runner-recorded indices only; missing metadata is not inferred.',
                         ('Rotations reuse each materialized bundle; they do not enumerate all cyclic windows or new draws.'
                          if rotate else 'Pairs are not rotated into alternative query positions; use --rotate-query to check them.'),
                         'Declared rivals must be pure and deterministic; predictions are cached by local rival name, exact callable object and input hash. Namespace aliases share predictions; distinct callables or names do not.',
                         'No approval or training-admission changes.']}
    report.update(rival_inventory(rivals))
    from review_diagnostics import schedule_metadata
    report.update(schedule_metadata(gen, period, enumerate_schedule))
    report['searched_rival_policy'] = 'advisory; separate from declared-rival verdict; rotations follow explicit rotation_policy'
    if enumerate_schedule:
        report['schedule_coverage'] = {
            'status': 'incomplete', 'contract': 'LESSON_SCHEDULE_PERIOD', 'period': schedule_period,
            'seed': schedule_seed, 'bands': list(request['bands']),
            'generator_sha256': report['generator_sha256'],
            'rule_source_sha256': report['rule_source_sha256'],
            'expected_lessons': schedule_period * len(request['bands']),
            'expected_rotations': schedule_period * len(request['bands']) * (demos + 1),
            'scope': 'Every declared starting residue and query position at this fixed seed and these bands only.'}
        report['limits'].append('Schedule period is a generator declaration, not independently proven; fixed-seed enumeration does not exhaust random support or rejected-pair schedules.')
    try:
        canonical = _support().canonical_pairs(bundle.rule_task_id,
                                                root=Path(__file__).resolve().parents[1],
                                                labeled_only=True)
        if not canonical:
            raise ValueError('No labeled canonical pairs available')
        report['canonical_pairs'] = len(canonical)
        canonical_cache = {}
        for name, rival in sorted(rivals.items()):
            fits, fit_errors = 0, []
            for index, pair in enumerate(canonical):
                try:
                    fits += int(_prediction(canonical_cache, name, rival, pair) == pair['output'])
                except Exception as exc:
                    fit_errors.append({'pair_index': index, 'variant': pair['variant'],
                                       'split': pair['split'], 'split_pair_index': pair['pair_index'],
                                       'error': f'{type(exc).__name__}: {exc}'})
            report['canonical_rival_fit'][name] = {
                'pairs': len(canonical), 'fits': fits, 'errors': fit_errors,
                'status': 'error' if fit_errors else 'fits_all' if fits == len(canonical) else 'refuted'}
    except Exception as exc:
        report['canonical_read_error'] = f'{type(exc).__name__}: {exc}'
        report['errors'].append(f'canonical: {type(exc).__name__}: {exc}')
    if checkpoint:
        checkpoint(report)
    bridge, fn_name = runner._open_bridge_with_rule(bundle.rule_callable_text)
    all_inputs = set()
    try:
        for band in request['bands']:
            counts, residues, unique = Counter(dict.fromkeys(SUMMARY_FIELDS, 0)), Counter(), set()
            accepted_residues = {'train': Counter(), 'test': Counter()}
            accepted_recorded = 0
            rival_counts = {name: Counter() for name in rivals}
            for index in range(draw_count):
                seed = schedule_seed if enumerate_schedule else int(hashlib.sha256(f'lesson-census:v1:{task_id}:{band}:{index}'.encode()).hexdigest()[:8], 16)
                row = {'band': band, 'index': index, 'seed': seed, 'sample_index': index}
                counts['requested'] += 1
                try:
                    instance = runner.run_one(task_id, seed=seed, sample_index=index,
                                              n_train=demos, n_test=request['n_queries'],
                                              bundle=bundle, bridge=bridge, fn_name=fn_name, difficulty=band)
                    row['instance_sha256'] = digest(instance)
                    row['instance'] = instance
                    sampling = instance.get('sampling', {})
                    for accepted in sampling.get('accepted_pairs', []):
                        accepted_residues[accepted['split']][accepted['sample_index'] % period] += 1
                        accepted_recorded += 1
                    prediction_cache = {}
                    row.update(score_lesson(gen, rivals, instance, prediction_cache=prediction_cache))
                    row['rotations'] = (score_rotations(gen, rivals, instance, prediction_cache=prediction_cache)
                                        if rotate else [])
                    for rotation in row['rotations']:
                        counts['rotations'] += 1
                        counts['ambiguous_rotations'] += int(rotation['ambiguous'])
                        counts['rotation_hook_warnings'] += int(bool(rotation['warnings']))
                        counts['rotation_scoring_errors'] += int(bool(rotation['errors']))
                    counts['materialized'] += 1
                    counts['ambiguous'] += int(row['ambiguous'])
                    counts['hook_warnings'] += int(bool(row['warnings']))
                    counts['scoring_errors'] += int(bool(row['errors']))
                    residues[index % period] += 1
                    for name, status in row['rivals'].items():
                        rival_counts[name][status] += 1
                    for pair in instance['train'] + instance['test']:
                        unique.add(digest(pair['input']))
                        counts['pairs'] += 1
                except Exception as exc:
                    row['errors'] = [f'{type(exc).__name__}: {exc}']
                    counts['materialization_errors'] += 1
                report['lessons'].append(row)
                all_inputs.update(unique)
                report['unique_inputs'] = len(all_inputs)
                report['per_band'][band] = {**dict(counts), 'unique_inputs': len(unique),
                                           'start_residues': {str(i): residues[i] for i in range(period)},
                                           'accepted_indices_recorded': accepted_recorded,
                                           'accepted_pair_residues': {split: {str(i): c[i] for i in range(period)}
                                                                      for split, c in accepted_residues.items()},
                                           'rivals': {name: dict(c) for name, c in rival_counts.items()}}
                report['summary'] = {key: sum(b[key] for b in report['per_band'].values()) for key in SUMMARY_FIELDS}
                report['summary']['unique_inputs'] = len(all_inputs)
                if checkpoint:
                    checkpoint(report)
    finally:
        bridge.shutdown()
    report['unique_inputs'] = len(all_inputs)
    from review_diagnostics import summarize_searches
    report['searched_rival_summary'] = summarize_searches([r['searched_rivals'] for row in report['lessons'] for r in [row,*row.get('rotations',[])] if 'searched_rivals' in r])
    if enumerate_schedule:
        coverage = report['schedule_coverage']
        complete = (not report['errors']
                    and not any(row['errors'] for row in report['canonical_rival_fit'].values())
                    and report['summary']['materialized'] == coverage['expected_lessons']
                    and report['summary']['rotations'] == coverage['expected_rotations']
                    and not report['summary']['materialization_errors']
                    and not report['summary']['scoring_errors']
                    and not report['summary']['rotation_scoring_errors'])
        coverage['status'] = 'complete_fixed_seed' if complete else 'incomplete'
        if not complete:
            report['errors'].append('Declared schedule census is incomplete at the requested fixed seed.')
    rotations = [score for row in report['lessons'] for score in row.get('rotations', [])]
    has_errors = bool(report['errors']) or any(row['errors'] for row in report['canonical_rival_fit'].values())
    report['production_status'] = _verdict(report['lessons'], errors=has_errors, contract=report['contract'])
    report['rotation_status'] = (_verdict(rotations, errors=has_errors, contract=report['contract'])
                                 if rotate else 'not_requested')
    scores = report['lessons'] + (rotations if rotation_policy == 'require' else [])
    report['status'] = _verdict(scores, errors=has_errors, contract=report['contract'])
    return report



# General evidence guards promoted from e937c5b85cdd/workspace/rescore_census.py.
COMPLETE_STATUSES = {
    "no_ambiguity_found", "no_declared_ambiguity", "no_contract",
    "warning", "hook_only", "ambiguous",
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def valid_grid(grid):
    return (isinstance(grid, list) and bool(grid)
            and isinstance(grid[0], list) and bool(grid[0])
            and all(isinstance(row, list) and len(row) == len(grid[0])
                    and all(type(value) is int and 0 <= value <= 9 for value in row)
                    for row in grid))


def validate_retained_census(census):
    """Validate completion and retained bindings before scoring any rival."""
    require(isinstance(census, dict), "Expected a census object")
    require(census.get("schema") == "arcpuzzles-lesson-census-v1", "Unsupported census schema")
    task = census.get("task_id")
    require(isinstance(task, str) and task.isalnum(), "Expected an alphanumeric task id")
    for key in ("status", "production_status"):
        require(census.get(key) in COMPLETE_STATUSES, f"Retained census {key} is incomplete or errored")
    require(census.get("rotation_status") in COMPLETE_STATUSES | {"not_requested"},
            "Retained rotation census is incomplete or errored")
    require(census.get("errors") == [], "Retained census contains errors")
    execution = census["execution"]
    expected_exit = 1 if census["status"] == "ambiguous" else 0
    require(execution.get("timed_out") is False
            and type(execution.get("exit_code")) is int
            and execution["exit_code"] == expected_exit, "Retained census execution did not complete")
    lessons, summary = census["lessons"], census["summary"]
    for key in ('requested', 'materialized', 'pairs', 'rotations', 'materialization_errors',
                'scoring_errors', 'rotation_scoring_errors'):
        require(type(summary.get(key)) is int and summary[key] >= 0, f'Invalid retained {key} count')
    require(isinstance(lessons, list) and bool(lessons), "Retained census has no lessons")
    require(type(summary.get("requested")) is int and summary["requested"] > 0
            and summary["requested"] == summary.get("materialized") == len(lessons),
            "Retained census is partial or has inconsistent lesson counts")
    for key in ("materialization_errors", "scoring_errors", "rotation_scoring_errors"):
        require(summary.get(key) == 0, f"Retained census reports {key}")
    manifest = census["runtime_manifest"]
    manifest_hash = hashlib.sha256((json.dumps(manifest, indent=2) + "\n").encode()).hexdigest()
    require(manifest_hash == census["runtime_manifest_sha256"], "Runtime manifest hash mismatch")
    require(manifest.get("task_id") == task, "Runtime manifest task mismatch")
    entries = [row for row in manifest["files"]
               if row.get("library_path") == f"generators/{task}/generator.py"]
    require(len(entries) == 1 and entries[0].get("sha256") == census["generator_sha256"],
            "Input generator hash is not bound to its runtime manifest")
    pair_count = rotation_count = 0
    per_band, identities = Counter(), set()
    for lesson in lessons:
        require(lesson.get("errors") == [], "Retained lesson contains scoring errors")
        identity = (lesson["band"], lesson["index"])
        require(identity not in identities, "Duplicate retained lesson identity")
        identities.add(identity)
        per_band[lesson["band"]] += 1
        instance = lesson["instance"]
        require(instance.get("task_id") == task
                and instance.get("rule_task_id") == census["rule_task_id"]
                and instance.get("rule_file") == census["rule_file"], "Retained lesson rule binding mismatch")
        train, tests = instance["train"], instance["test"]
        tests = tests if isinstance(tests, list) else [tests]
        require(isinstance(train, list) and bool(train) and len(tests) == 1,
                "Expected nonempty demonstrations and exactly one query")
        for pair in [*train, *tests]:
            require(isinstance(pair, dict) and valid_grid(pair.get("input"))
                    and valid_grid(pair.get("output")), "Missing or malformed retained input/reference output")
        instance_hash = hashlib.sha256(json.dumps(instance, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        require(instance_hash == lesson["instance_sha256"], "Retained instance hash mismatch")
        rotations = lesson.get("rotations", [])
        require(isinstance(rotations, list)
                and all(row.get("errors") == [] for row in rotations), "Retained rotation contains errors")
        pair_count += len(train) + 1
        rotation_count += len(rotations)
    require(summary.get("pairs") == pair_count and summary.get("rotations") == rotation_count,
            "Retained pair or rotation counts disagree with materialized evidence")
    require(set(census["per_band"]) == set(per_band), "Retained band coverage is inconsistent")
    for band, count in per_band.items():
        require(census["per_band"][band].get("requested")
                == census["per_band"][band].get("materialized") == count,
                f"Retained {band} census is partial")
    sampler = census['sampler']
    require(type(sampler.get('n_demos')) is int and sampler['n_demos'] > 0
            and type(sampler.get('n_queries')) is int and sampler['n_queries'] == 1,
            'Retained sampler must request demonstrations and exactly one query')
    require(type(sampler.get('rotate_query', False)) is bool, 'Invalid retained rotation setting')
    for lesson in lessons:
        require(len(lesson['instance']['train']) == sampler['n_demos'],
                'Retained lesson does not cover requested demonstrations')
        expected_rotations = sampler['n_demos'] + 1 if sampler.get('rotate_query', False) else 0
        require(len(lesson.get('rotations', [])) == expected_rotations,
                'Retained lesson does not cover requested rotations')
    require(type(sampler.get('per_band')) is int and sampler['per_band'] > 0,
            'Invalid retained sampler count')
    require(set(sampler['bands']) == set(per_band)
            and len(sampler['bands']) == len(per_band)
            and all(count == sampler['per_band'] for count in per_band.values()),
            'Retained census does not cover the requested sampler population')
    for band in per_band:
        require({row['index'] for row in lessons if row['band'] == band}
                == set(range(sampler['per_band'])), 'Retained lesson indices are incomplete')
    if sampler.get('enumerate_schedule_period', False):
        coverage = census.get('schedule_coverage', {})
        require(coverage.get('status') == 'complete_fixed_seed', 'Retained schedule coverage is incomplete')
        require(type(coverage.get('period')) is int and coverage['period'] > 0
                and coverage['period'] == sampler['per_band']
                and coverage.get('contract') == 'LESSON_SCHEDULE_PERIOD', 'Invalid retained schedule contract')
        require(coverage.get('seed') == sampler.get('schedule_seed', 0)
                and coverage.get('bands') == sampler['bands']
                and coverage.get('generator_sha256') == census['generator_sha256']
                and coverage.get('rule_source_sha256') == census['rule_source_sha256'],
                'Retained schedule source or population mismatch')
        require(sampler['rotate_query'] and coverage.get('expected_lessons') == len(lessons)
                and coverage.get('expected_rotations') == rotation_count,
                'Retained schedule population is incomplete')
        for lesson in lessons:
            instance = lesson['instance']
            require(lesson['seed'] == instance.get('seed') == coverage['seed']
                    and lesson['index'] == lesson['sample_index'] == instance.get('sample_index')
                    == instance.get('sampling', {}).get('requested_start'),
                    'Retained schedule seed or starting residue mismatch')
            n = sampler['n_demos'] + 1
            require([r.get('query_index') for r in lesson['rotations']] == list(range(n))
                    and all(r.get('train_indices') == [i for i in range(n) if i != r['query_index']]
                            for r in lesson['rotations']), 'Retained schedule rotations are incomplete')
    return task



def validate_schedule_receipt(census, *, task_id, binding, period, seed, bands, n_demos):
    """Validate reported finite coverage against current source and population.

    This consumes evidence; it neither regenerates labels nor proves a declared
    period, all-seed coverage, audit resolution or training eligibility.
    """
    require(type(period) is int and period > 0, 'Invalid current schedule period')
    require(type(seed) is int and 0 <= seed < 2**32, 'Invalid requested schedule seed')
    require(type(n_demos) is int and n_demos > 0, 'Invalid current demonstration count')
    require(validate_retained_census(census) == task_id, 'Schedule receipt task mismatch')
    for field in ('generator_sha256', 'rule_source_sha256', 'rule_callable_sha256',
                  'rule_task_id', 'rule_file', 'declared_rule_hash'):
        require(field in binding and field in census and census[field] == binding[field],
                f'Schedule receipt current source mismatch: {field}')
    for field in ('generator_sha256', 'rule_source_sha256', 'rule_callable_sha256'):
        require(isinstance(binding[field], str) and len(binding[field]) == 64,
                f'Incomplete current source binding: {field}')
    for field in ('rule_task_id', 'rule_file', 'declared_rule_hash'):
        require(isinstance(binding[field], str) and bool(binding[field]),
                f'Incomplete current source binding: {field}')
    sampler, coverage = census['sampler'], census.get('schedule_coverage', {})
    require(sampler.get('enumerate_schedule_period') is True,
            'Schedule receipt must enumerate the declared period')
    require(type(coverage.get('seed')) is int and type(sampler.get('schedule_seed')) is int
            and coverage['seed'] == sampler['schedule_seed'] == seed,
            'Schedule receipt requested seed mismatch')
    require(coverage.get('period') == period, 'Schedule receipt current period mismatch')
    require(coverage.get('bands') == sampler.get('bands') == list(bands),
            'Schedule receipt requested bands mismatch')
    require(sampler.get('n_demos') == n_demos, 'Schedule receipt demonstration count mismatch')
    require(census.get('rotation_policy') == sampler.get('rotation_policy', 'require') == 'require',
            'Schedule receipt requires blocking query-rotation policy')
    require(all(census.get(k) in ('no_ambiguity_found', 'no_declared_ambiguity', 'hook_only')
                for k in ('status', 'production_status', 'rotation_status')),
            'Schedule receipt reports ambiguity, warnings or missing contract')
    summary = census['summary']
    for field in ('ambiguous', 'hook_warnings', 'ambiguous_rotations', 'rotation_hook_warnings'):
        require(type(summary.get(field)) is int and summary[field] == 0,
                f'Schedule receipt reports {field}')
    require(census.get('contract') in ('rivals', 'hook_only'), 'Schedule receipt has no semantic contract')
    rivals = census.get('rivals')
    require(isinstance(rivals, list) and len(rivals) == len(set(rivals))
            and all(isinstance(name, str) for name in rivals), 'Invalid schedule rival inventory')
    require(rivals == binding.get('rivals'), 'Schedule receipt current rival inventory mismatch')
    for lesson in census['lessons']:
        require(all(type(lesson.get(k)) is int for k in ('seed', 'index', 'sample_index')),
                'Invalid schedule lesson identity types')
        for row in [lesson, *lesson['rotations']]:
            require(row.get('ambiguous') is False and row.get('warnings') == []
                    and row.get('errors') == [], 'Schedule receipt lesson/rotation did not pass')
            require(row.get('contract') == census['contract'], 'Schedule receipt contract mismatch')
            outcomes = row.get('rivals')
            require(isinstance(outcomes, dict) and set(outcomes) == set(rivals)
                    and all(value in ('refuted', 'survived_all') for value in outcomes.values()),
                    'Schedule receipt rival outcomes disagree with successful verdict')
    return task_id


def rescore_census(retained, bundle, checkpoint=None):
    """Recheck saved labels using current rivals, never materialize new draws."""
    task = validate_retained_census(retained)
    gen = bundle.generator_module
    source = Path(gen.__file__)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    require(bundle.kind == 'per_puzzle' and getattr(gen, 'TASK_ID', None) == task,
            'Retained census and current rivals refer to different tasks')
    require(getattr(gen, 'RULE_HASH', None) == retained['declared_rule_hash']
            and bundle.rule_task_id == retained['rule_task_id']
            and hashlib.sha256(bundle.rule_source.encode()).hexdigest() == retained['rule_source_sha256']
            and hashlib.sha256(bundle.rule_callable_text.encode()).hexdigest() == retained['rule_callable_sha256'],
            'Retained labels and current rivals refer to different rules')
    rivals, errors = declared_rivals(gen)
    require(not errors, '; '.join(errors))
    require(bool(rivals), 'No rivals declared; not a rival pass')
    report = {'schema': 'arcpuzzles-lesson-rescore-v1', 'task_id': task,
              'status': 'incomplete', 'production_status': 'incomplete', 'rotation_status': 'incomplete',
              'rotation_policy': 'require', 'errors': [], 'lessons': [],
              'input_generator_sha256': retained['generator_sha256'],
              'rival_generator_sha256': source_hash,
              'retained_runtime_manifest_sha256': retained['runtime_manifest_sha256'],
              'retained_rule_source_sha256': retained['rule_source_sha256'],
              'retained_rule_callable_sha256': retained['rule_callable_sha256'],
              'new_reference_executions': 0, 'new_generated_instances': 0,
              'rival_summary': {name: {'production': {}, 'rotations': {}, 'counterexample': None}
                                for name in sorted(rivals)},
              'summary': {'lessons': 0, 'rotations': 0, 'ambiguous': 0, 'ambiguous_rotations': 0},
              'limits': ['Saved authoring labels are hash-checked, not independently re-executed.',
                         'Input generator hash describes original draws; current source describes rivals only.',
                         'Each saved pair is held out once with remaining pairs in original order; no new draws.',
                         'Finite declared-rival evidence, not universal identifiability or approval.',
                         'Rivals must be pure and deterministic; predictions are cached within each lesson.']}
    report.update(rival_inventory(rivals))
    for lesson in retained['lessons']:
        instance = deepcopy(lesson['instance'])
        if isinstance(instance['test'], dict):
            instance['test'] = [instance['test']]
        cache = {}
        score = score_lesson(gen, rivals, instance, prediction_cache=cache)
        rotations = score_rotations(gen, rivals, instance, prediction_cache=cache)
        row = {key: deepcopy(lesson[key]) for key in ('band', 'index', 'seed', 'sample_index', 'instance_sha256', 'instance')}
        row.update(score, rotations=rotations)
        report['lessons'].append(row)
        report['summary']['lessons'] += 1
        report['summary']['rotations'] += len(rotations)
        report['summary']['ambiguous'] += int(score['ambiguous'])
        report['summary']['ambiguous_rotations'] += sum(int(r['ambiguous']) for r in rotations)
        for name in rivals:
            summary = report['rival_summary'][name]
            for field, scores in (('production', [score]), ('rotations', rotations)):
                for result in scores:
                    status = result['rivals'][name]
                    summary[field][status] = summary[field].get(status, 0) + 1
            if summary['counterexample'] is None:
                for rotation in rotations:
                    if rotation['rivals'][name] == 'ambiguous':
                        query_index = rotation['query_index']
                        query = (instance['train'] + instance['test'])[query_index]
                        summary['counterexample'] = {
                            **{key: row[key] for key in ('band', 'index', 'seed', 'sample_index', 'instance_sha256', 'instance')},
                            'query_index': query_index, 'train_indices': rotation['train_indices'],
                            'prediction': deepcopy(_prediction(cache, name, rivals[name], query))}
                        break
        if checkpoint:
            checkpoint(report)
    require(hashlib.sha256(source.read_bytes()).hexdigest() == source_hash,
            'Current rival source changed during rescoring')
    report['rival_source_stable'] = True
    rotations = [r for row in report['lessons'] for r in row['rotations']]
    report['production_status'] = _verdict(report['lessons'], errors=False, contract='rivals')
    report['rotation_status'] = _verdict(rotations, errors=False, contract='rivals')
    report['status'] = _verdict(report['lessons'] + rotations, errors=False, contract='rivals')
    return report


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))
    request = json.loads(Path(sys.argv[1]).read_text())
    try:
        def checkpoint(value):
            temporary = Path(sys.argv[2] + '.tmp')
            with temporary.open('w') as stream:
                stream.write(json.dumps(value, indent=2) + '\n')
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(sys.argv[2])
        if request.get('retained_census'):
            retained = json.loads(Path(request['retained_census']).read_text())
            require(validate_retained_census(retained) == request['task_id'], 'Retained census task mismatch')
            from puzzle_generators import runner
            report = rescore_census(retained, runner._load_bundle(request['task_id']), checkpoint=checkpoint)
        else:
            report = census(request, checkpoint=checkpoint)
    except Exception as exc:
        report_path = Path(sys.argv[2])
        report = json.loads(report_path.read_text()) if report_path.exists() else {
            'schema': 'arcpuzzles-lesson-census-v1', 'task_id': request['task_id'], 'errors': []}
        report['status'] = 'error'
        report['errors'].append(f'{type(exc).__name__}: {exc}')
    checkpoint(report)
    return 2 if report['status'] == 'error' else 1 if report['status'] == 'ambiguous' else 0


if __name__ == '__main__':
    raise SystemExit(main())
