#!/usr/bin/env python3
"""Offline finite canonical-distinction gate for arcpuzzles-lesson-census-v1.

Usage: python canonical_distinction_coverage.py CENSUS.json --required-bands
easy medium hard --expected-task-id TASK --expected-generator-sha256 SHA256
[--out REPORT.json]. Exit 0: covered, 1: missing distinction, 2: incomplete.

No generator, canonical answer helper, private labels, Racket or external package
is imported. This validates retained bindings and trusts the census scorer's
statuses; it does not replay them. 'refuted' proves a mismatch somewhere in the
candidate demonstrations, not a mismatch on every candidate. A single-query
'ambiguous' status identifies that query as the only mismatching labelled pair.
Counts are finite observed coverage, never universal induction/identifiability.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


SCHEMA = 'arcpuzzles-canonical-distinction-coverage-v1'
FIELDS = ('requested', 'materialized', 'materialization_errors', 'pairs', 'ambiguous',
          'hook_warnings', 'scoring_errors', 'rotations', 'ambiguous_rotations',
          'rotation_hook_warnings', 'rotation_scoring_errors')
STATUSES = {'refuted', 'survived_all', 'ambiguous'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def positive(value):
    return type(value) is int and value > 0


def grid(value):
    return (isinstance(value, list) and 1 <= len(value) <= 30
            and isinstance(value[0], list) and 1 <= len(value[0]) <= 30
            and all(isinstance(row, list) and len(row) == len(value[0])
                    and all(type(c) is int and 0 <= c <= 9 for c in row) for row in value))


def score_valid(score, rivals):
    need(score.get('contract') == 'rivals' and score.get('errors') == [], 'Missing rival score or scoring errors')
    need(isinstance(score.get('warnings'), list), 'Missing score warning record')
    need(isinstance(score.get('rivals'), dict) and set(score['rivals']) == set(rivals), 'Missing or unknown rival name')
    need(all(s in STATUSES for s in score['rivals'].values()), 'Unknown/errored rival status')
    need(type(score.get('ambiguous')) is bool
         and score['ambiguous'] == any(s == 'ambiguous' for s in score['rivals'].values()), 'Inconsistent ambiguity flag')


def validate(census, bands, task, generator):
    need(isinstance(census, dict) and census.get('schema') == 'arcpuzzles-lesson-census-v1', 'Unsupported census schema')
    need(census.get('task_id') == task and isinstance(task, str) and task.isalnum(), 'Expected task/source binding mismatch')
    need(bands and len(set(bands)) == len(bands) and set(bands) <= {'easy', 'medium', 'hard'}, 'Explicit distinct required bands are mandatory')
    need(census.get('generator_sha256') == generator, 'Expected generator source binding mismatch')
    for field in ('generator_sha256', 'controller_sha256', 'rule_source_sha256', 'rule_callable_sha256', 'runtime_manifest_sha256'):
        need(isinstance(census.get(field), str) and re.fullmatch('[0-9a-f]{64}', census[field]), 'Missing/malformed source hash: ' + field)
    need(census.get('contract') == 'rivals' and census.get('errors') == [], 'Census lacks declared rivals or contains errors')
    need(isinstance(census.get('rule_task_id'), str) and census['rule_task_id'].isalnum()
         and isinstance(census.get('rule_file'), str) and bool(census['rule_file']), 'Missing rule task/source identity')
    manifest = census['runtime_manifest']
    need(hashlib.sha256((json.dumps(manifest, indent=2) + '\n').encode()).hexdigest()
         == census['runtime_manifest_sha256'], 'Runtime manifest hash mismatch')
    need(manifest.get('schema') == 'arcpuzzles-runtime-v1' and manifest.get('task_id') == task, 'Runtime manifest task/schema mismatch')
    entries = manifest['files']
    need(isinstance(entries, list) and entries, 'Missing runtime source inventory')
    need(len({e['runtime_path'] for e in entries}) == len(entries), 'Duplicate runtime source inventory')
    for entry in entries:
        need(isinstance(entry.get('library_path'), str) and isinstance(entry.get('runtime_path'), str)
             and re.fullmatch('[0-9a-f]{64}', entry.get('sha256', '')), 'Malformed runtime source entry')
    selected = [e for e in entries if e['library_path'] == f'generators/{task}/generator.py']
    need(len(selected) == 1 and selected[0]['sha256'] == generator, 'Generator not bound to runtime manifest')
    rivals = census['rivals']
    need(isinstance(rivals, list) and rivals and len(set(rivals)) == len(rivals)
         and all(isinstance(r, str) and ':' in r for r in rivals), 'Missing/duplicate declared rivals')
    fit = census['canonical_rival_fit']
    need(isinstance(fit, dict) and set(fit) == set(rivals), 'Missing or unknown canonical rival fit')
    need(positive(census['canonical_pairs']), 'Missing canonical labelled pair count')
    for row in fit.values():
        need(row.get('errors') == [] and row.get('pairs') == census['canonical_pairs']
             and type(row.get('fits')) is int and 0 <= row['fits'] <= row['pairs'], 'Canonical fit errors or incomplete counts')
        need(row.get('status') == ('fits_all' if row['fits'] == row['pairs'] else 'refuted'), 'Canonical rival status/count mismatch')
    sampler = census['sampler']
    need(sampler.get('task_id') == task and positive(sampler.get('per_band'))
         and positive(sampler.get('n_demos')) and sampler.get('n_queries') == 1, 'Incomplete/unsupported sampler population; exactly one query required')
    population = sampler['bands']
    need(isinstance(population, list) and len(set(population)) == len(population)
         and set(population) <= {'easy', 'medium', 'hard'} and set(bands) <= set(population), 'Required band missing from sampler')
    need(type(sampler.get('rotate_query')) is bool and census.get('rotation_policy') in {'require', 'diagnostic'}, 'Missing rotation policy/settings')
    need(type(sampler.get('enumerate_schedule_period', False)) is bool, 'Invalid schedule enumeration flag')
    lessons = census['lessons']
    need(isinstance(lessons, list) and len(lessons) == len(population) * sampler['per_band'], 'Partial/missing census lessons')
    need(set(census['per_band']) == set(population), 'Incomplete band records')
    identities, labels, all_inputs = set(), {}, set()
    derived = {band: {**dict.fromkeys(FIELDS, 0), 'rivals': {r: Counter() for r in rivals}, 'inputs': set()} for band in population}
    for lesson in lessons:
        band, index = lesson['band'], lesson['index']
        need(band in derived and type(index) is int and 0 <= index < sampler['per_band']
             and (band, index) not in identities, 'Missing/duplicate lesson identity')
        identities.add((band, index))
        score_valid(lesson, rivals)
        instance = lesson['instance']
        need(instance.get('task_id') == task and instance.get('rule_task_id') == census['rule_task_id']
             and instance.get('rule_file') == census['rule_file'], 'Lesson rule binding mismatch')
        need(type(lesson.get('seed')) is int and instance.get('seed') == lesson['seed']
             and type(lesson.get('sample_index')) is int, 'Missing lesson seed/sample binding')
        need(digest(instance) == lesson['instance_sha256'], 'Retained instance hash mismatch')
        train, tests = instance['train'], instance['test']
        need(isinstance(train, list) and len(train) == sampler['n_demos']
             and isinstance(tests, list) and len(tests) == 1, 'Missing requested demonstration/query population')
        pairs = train + tests
        for pair in pairs:
            need(isinstance(pair, dict) and grid(pair.get('input')) and grid(pair.get('output')), 'Missing/malformed input/reference-output witness')
            input_hash, output_hash = digest(pair['input']), digest(pair['output'])
            need(input_hash not in labels or labels[input_hash] == output_hash, 'Conflicting retained reference labels for identical input')
            labels[input_hash] = output_hash
            all_inputs.add(input_hash)
            derived[band]['inputs'].add(input_hash)
        rotations = lesson['rotations']
        expected = len(pairs) if sampler['rotate_query'] else 0
        need(isinstance(rotations, list) and len(rotations) == expected, 'Missing requested query rotations')
        for query, rotation in enumerate(rotations):
            need(rotation.get('query_index') == query
                 and rotation.get('train_indices') == [i for i in range(len(pairs)) if i != query], 'Invalid/incomplete rotation indices')
            score_valid(rotation, rivals)
        counts = derived[band]
        counts['requested'] += 1
        counts['materialized'] += 1
        counts['pairs'] += len(pairs)
        counts['ambiguous'] += int(lesson['ambiguous'])
        counts['hook_warnings'] += int(bool(lesson['warnings']))
        counts['rotations'] += len(rotations)
        counts['ambiguous_rotations'] += sum(int(r['ambiguous']) for r in rotations)
        counts['rotation_hook_warnings'] += sum(int(bool(r['warnings'])) for r in rotations)
        for rival, status in lesson['rivals'].items():
            counts['rivals'][rival][status] += 1
    for band, counts in derived.items():
        saved = census['per_band'][band]
        need(all(type(saved.get(k)) is int and saved[k] == counts[k] for k in FIELDS), 'Incomplete/inconsistent band counts: ' + band)
        need(saved.get('unique_inputs') == len(counts['inputs']) and saved.get('rivals') == {r: dict(c) for r, c in counts['rivals'].items()}, 'Inconsistent band input/rival counts')
    summary = census['summary']
    need(all(type(summary.get(k)) is int and summary[k] == sum(c[k] for c in derived.values()) for k in FIELDS), 'Partial/errored/inconsistent summary counts')
    need(summary.get('unique_inputs') == census.get('unique_inputs') == len(all_inputs), 'Inconsistent unique-input totals')
    def verdict(scores):
        return 'ambiguous' if any(s['ambiguous'] for s in scores) else 'warning' if any(s['warnings'] for s in scores) else 'no_ambiguity_found'
    rotations = [r for lesson in lessons for r in lesson['rotations']]
    expected_statuses = {'production_status': verdict(lessons),
                         'rotation_status': verdict(rotations) if sampler['rotate_query'] else 'not_requested',
                         'status': verdict(lessons + (rotations if census['rotation_policy'] == 'require' else []))}
    need(all(census.get(k) == v for k, v in expected_statuses.items()), 'Census incomplete/errored or inconsistent status')
    execution = census['execution']
    need(execution.get('timed_out') is False and type(execution.get('exit_code')) is int
         and execution['exit_code'] == (1 if census['status'] == 'ambiguous' else 0), 'Worker did not complete honestly')
    if sampler.get('enumerate_schedule_period', False):
        schedule = census.get('schedule_coverage', {})
        need(schedule.get('status') == 'complete_fixed_seed' and schedule.get('contract') == 'LESSON_SCHEDULE_PERIOD'
             and schedule.get('period') == sampler['per_band'] and schedule.get('bands') == population
             and schedule.get('generator_sha256') == generator and schedule.get('rule_source_sha256') == census['rule_source_sha256']
             and schedule.get('seed') == sampler.get('schedule_seed', 0)
             and schedule.get('expected_lessons') == len(lessons) and schedule.get('expected_rotations') == len(rotations), 'Incomplete schedule/source coverage')
        need(sampler['rotate_query'] and type(schedule.get('seed')) is int
             and 0 <= schedule['seed'] < 2**32, 'Invalid schedule seed/rotation contract')
        for row in lessons:
            instance = row['instance']
            need(row['seed'] == instance.get('seed') == schedule['seed']
                 and row['index'] == row['sample_index'] == instance.get('sample_index')
                 == instance.get('sampling', {}).get('requested_start'), 'Schedule start/seed evidence is not bound')
    return rivals, lessons


def mismatch_identity(observations, rival):
    """Return exact mismatching pair indices if status constraints determine them."""
    statuses = [score['rivals'][rival] for _, _, score in observations]
    if 'survived_all' in statuses:
        need(all(s == 'survived_all' for s in statuses), 'Contradictory survived/refuted status on same instance')
        return set()
    indices = {query for _, query, score in observations if score['rivals'][rival] == 'ambiguous'}
    if indices:
        need(len(indices) == 1, 'Contradictory single-query ambiguity witnesses')
        index = next(iter(indices))
        for train, query, score in observations:
            need(score['rivals'][rival] == ('refuted' if index in train else 'ambiguous'), 'Contradictory rival statuses across query rotations')
        return {index}
    return None  # refuted-only statuses locate no particular pair


def analyze_census(census, *, required_bands, expected_task_id, expected_generator_sha256):
    base = {'schema': SCHEMA, 'universal_induction_claimed': False,
            'limits': ['Finite retained status evidence only; no rival/authority replay or universal induction.',
                       'refuted identifies a candidate demonstration set, not every candidate input.',
                       'null exact counts mean pair-level refutation identities are unavailable.',
                       'Canonical fits_all means no distinction required by these canonical pairs, not universal equivalence.',
                       'Coverage is not an identifiability or semantic approval pass; input census status remains separate.']}
    try:
        bands = list(required_bands)
        rivals, lessons = validate(census, bands, expected_task_id, expected_generator_sha256)
        required = [r for r in rivals if census['canonical_rival_fit'][r]['status'] == 'refuted']
        coverage = {r: {} for r in required}
        missing = []
        for rival in required:
            for band in bands:
                evidence, lesson_ids, sets, confirmed = [], set(), set(), set()
                exact = True
                for row in lessons:
                    if row['band'] != band:
                        continue
                    pairs = row['instance']['train'] + row['instance']['test']
                    n = len(row['instance']['train'])
                    observations = [(list(range(n)), n, row)] + [(r['train_indices'], r['query_index'], r) for r in row['rotations']]
                    known = mismatch_identity(observations, rival)
                    exact &= known is not None
                    if known is not None:
                        confirmed.update(digest(pairs[i]['input']) for i in known)
                    for position, (train, query, score) in enumerate(observations):
                        status = score['rivals'][rival]
                        if status == 'survived_all':
                            continue
                        candidates = sorted({digest(pairs[i]['input']) for i in (train if status == 'refuted' else [query])})
                        need(candidates, 'Missing refutation witness candidates')
                        sets.add(tuple(candidates))
                        lesson_ids.add(row['index'])
                        evidence.append({'band': band, 'index': row['index'], 'seed': row['seed'],
                                         'sample_index': row['sample_index'], 'instance_sha256': row['instance_sha256'],
                                         'source': 'production' if position == 0 else 'rotation', 'query_index': query,
                                         'status': status, 'candidate_input_hashes': candidates,
                                         'confirmed_query_input_hash': candidates[0] if status == 'ambiguous' else None})
                lower = max(len(confirmed), int(bool(evidence)))
                coverage[rival][band] = {'refuting_lesson_count': len(lesson_ids), 'refuting_set_count': len(sets),
                                         'refuting_observation_count': len(evidence),
                                         'unique_input_refuting_count': len(confirmed) if exact else None,
                                         'unique_input_refuting_lower_bound': lower, 'confirmed_input_hashes': sorted(confirmed),
                                         'evidence': evidence}
                if not evidence:
                    missing.append({'rival': rival, 'band': band})
        # Also reject contradictory scorer records for canonically fitting rivals.
        for rival in set(rivals) - set(required):
            for row in lessons:
                n = len(row['instance']['train'])
                mismatch_identity([(list(range(n)), n, row)] + [(r['train_indices'], r['query_index'], r) for r in row['rotations']], rival)
        return {**base, 'status': 'missing_distinction' if missing else 'covered', 'errors': [],
                'task_id': expected_task_id, 'generator_sha256': expected_generator_sha256,
                'rule_source_sha256': census['rule_source_sha256'], 'controller_sha256': census['controller_sha256'],
                'runtime_manifest_sha256': census['runtime_manifest_sha256'], 'input_census_status': census['status'],
                'input_production_status': census['production_status'], 'input_rotation_status': census['rotation_status'],
                'input_rotation_policy': census['rotation_policy'],
                'required_bands': bands, 'canonical_refuted_rivals': required,
                'canonical_fitting_rivals': [r for r in rivals if r not in required],
                'coverage': coverage, 'missing_distinctions': missing}
    except (ValueError, KeyError, TypeError, AttributeError, IndexError) as exc:
        return {**base, 'status': 'incomplete', 'errors': [f'{type(exc).__name__}: {exc}']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('census', type=Path)
    parser.add_argument('--required-bands', nargs='+', required=True, choices=['easy', 'medium', 'hard'])
    parser.add_argument('--expected-task-id', required=True)
    parser.add_argument('--expected-generator-sha256', required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.census.read_bytes()
        result = analyze_census(json.loads(raw), required_bands=args.required_bands,
                                expected_task_id=args.expected_task_id,
                                expected_generator_sha256=args.expected_generator_sha256)
        result['input_census_sha256'] = hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError) as exc:
        result = {'schema': SCHEMA, 'status': 'incomplete', 'errors': [f'{type(exc).__name__}: {exc}'], 'universal_induction_claimed': False}
    rendered = json.dumps(result, indent=2) + '\n'
    if args.out:
        try:
            with args.out.open('x') as stream:
                stream.write(rendered)
        except OSError as exc:
            print(json.dumps({'schema': SCHEMA, 'status': 'incomplete', 'errors': [str(exc)], 'universal_induction_claimed': False}))
            return 2
    else:
        print(rendered, end='')
    return {'covered': 0, 'missing_distinction': 1, 'incomplete': 2}[result['status']]


if __name__ == '__main__':
    raise SystemExit(main())
