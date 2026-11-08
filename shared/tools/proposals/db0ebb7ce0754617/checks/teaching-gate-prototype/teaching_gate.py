#!/usr/bin/env python3
"""Policy prototype over trusted arcpuzzles-lesson-census-v1 reports.

Does not execute generators, rivals, or Racket, and does not create new labels.
"""
import argparse
import ast
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys


RIVAL_CONTRACTS = {'LESSON_COMPETITORS', 'SEMANTIC_RIVALS', 'CANONICAL_SHORTCUTS'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def evaluate(report, source_bytes, expected_rule_hash, *, require_rotations=False):
    failures = []
    counts = {'production_lessons': 0, 'query_rotations': 0, 'required_rival_ids': 0,
              'production_rival_checks': 0, 'rotation_rival_checks': 0}
    result = {'schema': 'teaching-gate-policy-prototype-v1', 'status': 'fail',
              'task_id': report.get('task_id') if isinstance(report, dict) else None,
              'source_sha256': sha(source_bytes), 'expected_canonical_rule_hash': expected_rule_hash,
              'require_rotations': require_rotations, 'counts': counts, 'failures': failures,
              'trust_scope': 'Policy over a trusted retained census; no new labels or universal induction proof.'}

    def check(ok, code, detail=None, **identity):
        if not ok:
            failures.append({'code': code, **identity, **({'detail': detail} if detail else {})})
        return bool(ok)

    try:
        check(report.get('schema') == 'arcpuzzles-lesson-census-v1', 'unsupported_schema')
        check(report.get('generator_sha256') == sha(source_bytes), 'generator_source_mismatch')
        check(report.get('declared_rule_hash') == expected_rule_hash, 'declared_rule_mismatch')
        check(report.get('catalog_provenance', {}).get('rule_hash') == expected_rule_hash, 'canonical_rule_mismatch')
        declared = set()
        pin = None
        for statement in ast.parse(source_bytes).body:
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target] if isinstance(statement, ast.AnnAssign) else []
            for target in targets:
                if isinstance(target, ast.Name):
                    declared.add(target.id)
                    if target.id == 'RULE_HASH' and isinstance(statement.value, ast.Constant):
                        pin = statement.value.value
        check(bool(declared & RIVAL_CONTRACTS), 'source_missing_rival_contract')
        check(pin == expected_rule_hash, 'source_rule_pin_missing_or_mismatch')
        check(report.get('contract') == 'rivals', 'missing_rival_contract')
        rivals = report.get('rivals', [])
        check(isinstance(rivals, list) and bool(rivals) and all(isinstance(x, str) for x in rivals), 'missing_declared_rivals')
        rivals = rivals if isinstance(rivals, list) and all(isinstance(x, str) for x in rivals) else []
        check(len(set(rivals)) == len(rivals), 'duplicate_rival_ids')
        for rival in rivals:
            check(rival.split(':', 1)[0] in declared & RIVAL_CONTRACTS, 'rival_inventory_not_bound_to_source', rival_id=rival)
        compatible = []
        fits = report.get('canonical_rival_fit', {})
        check(set(fits) == set(rivals), 'canonical_rival_inventory_mismatch')
        for rival in rivals:
            row = fits.get(rival)
            if not check(isinstance(row, dict), 'missing_canonical_rival_fit', rival_id=rival):
                continue
            valid = (type(row.get('pairs')) is int and row['pairs'] > 0
                     and row['pairs'] == report.get('canonical_pairs')
                     and type(row.get('fits')) is int and 0 <= row['fits'] <= row['pairs']
                     and row.get('errors') == [])
            check(valid, 'incomplete_or_error_canonical_fit', rival_id=rival)
            if valid and row.get('status') == 'fits_all' and row['fits'] == row['pairs']:
                compatible.append(rival)
            elif valid:
                check(row.get('status') == 'refuted' and row['fits'] < row['pairs'], 'inconsistent_canonical_fit', rival_id=rival)
        check(bool(compatible), 'missing_canonical_compatible_rivals')
        result['required_rivals'] = compatible
        counts['required_rival_ids'] = len(compatible)
        check(report.get('errors') == [], 'census_errors', str(report.get('errors')))
        check(report.get('status') == 'no_ambiguity_found', 'census_status_not_clean')
        execution = report.get('execution', {})
        check(execution.get('exit_code') == 0 and execution.get('timed_out') is False, 'incomplete_or_failed_execution')
        check(report.get('production_status') == 'no_ambiguity_found', 'production_status_not_clean')
        if require_rotations:
            check(report.get('rotation_status') == 'no_ambiguity_found', 'rotation_status_not_clean')
        manifest = report.get('runtime_manifest', {})
        entries = [x for x in manifest.get('files', []) if x.get('library_path') == f"generators/{report.get('task_id')}/generator.py"]
        check(len(entries) == 1 and entries[0].get('sha256') == sha(source_bytes), 'missing_or_mismatched_runtime_source_binding')
        check(sha((json.dumps(manifest, indent=2) + '\n').encode()) == report.get('runtime_manifest_sha256'), 'runtime_manifest_hash_mismatch')
        lessons, summary, sampler = report.get('lessons', []), report.get('summary', {}), report.get('sampler', {})
        check(isinstance(lessons, list) and bool(lessons), 'no_materialized_lessons')
        check(type(summary.get('requested')) is int and summary['requested'] > 0
              and summary['requested'] == summary.get('materialized') == len(lessons), 'incomplete_lesson_population')
        for metric in ('materialization_errors', 'scoring_errors', 'rotation_scoring_errors', 'hook_warnings', 'rotation_hook_warnings', 'ambiguous', 'ambiguous_rotations'):
            check(summary.get(metric) == 0, 'census_error_or_hook_warning', metric)
        check(type(sampler.get('n_demos')) is int and sampler['n_demos'] > 0
              and sampler.get('n_queries') == 1, 'invalid_sampler_pair_counts')
        check(type(sampler.get('rotate_query')) is bool, 'missing_rotation_setting')
        if require_rotations:
            check(sampler.get('rotate_query') is True, 'required_rotations_not_recorded')
        bands = sampler.get('bands', [])
        check(isinstance(bands, list) and bool(bands) and len(set(bands)) == len(bands), 'invalid_sampler_bands')
        check(type(sampler.get('per_band')) is int and sampler['per_band'] > 0, 'invalid_per_band_count')
        band_indices = {band: [] for band in bands}
        pair_count = 0

        def score(row, lesson_id, query_index=None):
            location = {'lesson_id': lesson_id}
            if query_index is not None:
                location['rotation_query_index'] = query_index
            check(row.get('contract') == 'rivals', 'lesson_missing_rival_contract', **location)
            check(row.get('ambiguous') is False, 'lesson_or_rotation_ambiguous', **location)
            check(row.get('errors') == [], 'lesson_or_rotation_errors', str(row.get('errors')), **location)
            check(row.get('warnings') == [], 'lesson_or_rotation_hook_warning', str(row.get('warnings')), **location)
            for rival in compatible:
                recorded = row.get('rivals', {}).get(rival)
                check(recorded == 'refuted', 'rival_not_refuted', rival_id=rival, recorded_status=recorded, **location)
                counts['production_rival_checks' if query_index is None else 'rotation_rival_checks'] += 1

        for lesson in lessons:
            lesson_id = {'band': lesson.get('band'), 'index': lesson.get('index')}
            band_indices.setdefault(lesson.get('band'), []).append(lesson.get('index'))
            instance = lesson.get('instance', {})
            instance_hash = sha(json.dumps(instance, sort_keys=True, separators=(',', ':')).encode())
            check(instance_hash == lesson.get('instance_sha256'), 'instance_hash_mismatch', lesson_id=lesson_id)
            check(instance.get('task_id') == report.get('task_id') and instance.get('rule_task_id') == report.get('rule_task_id')
                  and instance.get('rule_file') == report.get('rule_file'), 'instance_rule_binding_mismatch', lesson_id=lesson_id)
            train, tests = instance.get('train', []), instance.get('test', [])
            tests = [tests] if isinstance(tests, dict) else tests
            check(len(train) == sampler.get('n_demos') and len(tests) == 1, 'incomplete_lesson_pairs', lesson_id=lesson_id)
            for pair in [*train, *tests]:
                for name in ('input', 'output'):
                    grid = pair.get(name)
                    valid = (isinstance(grid, list) and bool(grid) and isinstance(grid[0], list) and bool(grid[0])
                             and all(isinstance(row, list) and len(row) == len(grid[0])
                                     and all(type(x) is int and 0 <= x <= 9 for x in row) for row in grid))
                    check(valid, 'missing_or_malformed_retained_pair', name, lesson_id=lesson_id)
            pair_count += len(train) + len(tests)
            counts['production_lessons'] += 1
            score(lesson, lesson_id)
            rotations = lesson.get('rotations', [])
            n = len(train) + len(tests)
            expected_queries = list(range(n)) if sampler.get('rotate_query') else []
            check([x.get('query_index') for x in rotations] == expected_queries, 'incomplete_rotation_population', lesson_id=lesson_id)
            for rotation in rotations:
                query = rotation.get('query_index')
                counts['query_rotations'] += 1
                check(rotation.get('train_indices') == [i for i in range(n) if i != query], 'incomplete_rotation_demonstrations', lesson_id=lesson_id, rotation_query_index=query)
                check(rotation.get('errors') == [], 'rotation_errors', lesson_id=lesson_id, rotation_query_index=query)
                if require_rotations:
                    score(rotation, lesson_id, query)
        check(summary.get('pairs') == pair_count, 'pair_count_mismatch')
        check(summary.get('rotations') == counts['query_rotations'], 'rotation_count_mismatch')
        check(set(band_indices) == set(bands) == set(report.get('per_band', {})), 'band_population_mismatch')
        for band, indices in band_indices.items():
            detail = report.get('per_band', {}).get(band, {})
            check(len(indices) == sampler.get('per_band') and sorted(indices) == list(range(sampler['per_band']))
                  and detail.get('requested') == detail.get('materialized') == len(indices), 'incomplete_or_duplicate_band_population', band=band)
        result['report_warnings'] = report.get('warnings', [])
    except (TypeError, ValueError, KeyError, AttributeError, SyntaxError) as error:
        failures.append({'code': 'malformed_report_or_source', 'detail': f'{type(error).__name__}: {error}'})
    result['failure_counts'] = dict(Counter(row['code'] for row in failures))
    result['status'] = 'fail' if failures else 'pass'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census', type=Path, required=True)
    parser.add_argument('--generator', type=Path, required=True)
    parser.add_argument('--expected-rule-hash', required=True)
    parser.add_argument('--require-rotations', action='store_true')
    parser.add_argument('--out', type=Path, required=True, help='Fresh JSON output; existing files are never overwritten.')
    args = parser.parse_args(argv)
    if args.out.exists():
        parser.error(f'Output already exists: {args.out}')
    try:
        raw = args.census.read_bytes()
        decoded = gzip.decompress(raw) if args.census.suffix == '.gz' else raw
        source = args.generator.read_bytes()
        result = evaluate(json.loads(decoded), source, args.expected_rule_hash, require_rotations=args.require_rotations)
        result.update(input_report_path=str(args.census.resolve()), input_report_sha256=sha(raw),
                      decoded_report_sha256=sha(decoded), generator_path=str(args.generator.resolve()),
                      cwd=str(Path.cwd()), command=[sys.executable, *sys.argv])
        exit_code = 0 if result['status'] == 'pass' else 1
    except (OSError, ValueError, EOFError) as error:
        result = {'schema': 'teaching-gate-policy-prototype-v1', 'status': 'input_error', 'error': f'{type(error).__name__}: {error}'}
        exit_code = 2
    result['exit_code'] = exit_code
    try:
        with args.out.open('x') as handle:
            json.dump(result, handle, indent=2)
            handle.write('\n')
    except OSError as error:
        parser.error(str(error))
    print(json.dumps({key: result.get(key) for key in ('status', 'counts', 'failure_counts', 'exit_code')}))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
