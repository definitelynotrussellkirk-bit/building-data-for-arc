"""Public controller for the opt-in, source-bound reviewer lesson census."""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

from .catalog import sha256
from .runtime import prepare_runtime, run_process


def census_companion(report, *, full_report_sha256, full_report_path, invocation):
    """Project authoring evidence without rescoring, relabelling or certifying it.

    All failing/warning production and rotation recipes remain. Successful
    instances and the copied runtime inventory stay in the bound full report.
    """
    if report.get('schema') not in ('arcpuzzles-lesson-census-v1', 'arcpuzzles-lesson-rescore-v1'):
        raise ValueError('Unsupported census schema for companion')
    companion = {
        'schema': 'arcpuzzles-lesson-census-companion-v1', 'task_id': report['task_id'],
        'full_report': {'path': full_report_path, 'sha256': full_report_sha256},
        'source_binding': {k: deepcopy(v) for k, v in report.items()
                           if k.endswith('_sha256') or k in ('declared_rule_hash', 'rule_task_id', 'rule_file')},
        'invocation': {'argv': list(invocation), 'cwd': str(Path.cwd())},
        'findings': [], 'first_witnesses': {}, 'training_admitted': False,
        'scope': 'Compact authoring evidence only; not a full rescore or schedule receipt. '
                 'Reported verdicts and counts are copied, not independently verified. '
                 'Query labels are authoring data, not model-visible challenges.',
    }
    for key in ('status', 'production_status', 'rotation_status', 'rotation_policy',
                'summary', 'per_band', 'errors', 'contract', 'rivals', 'sampler',
                'schedule_coverage', 'canonical_rival_fit', 'canonical_read_error',
                'searched_rival_summary', 'limits', 'new_reference_executions',
                'new_generated_instances', 'rival_source_stable', 'unique_rivals',
                'declaration_bindings', 'rival_identities'):
        if key in report:
            companion[key] = deepcopy(report[key])
    execution = report.get('execution')
    if isinstance(execution, dict):
        companion['execution'] = {k: deepcopy(v) for k, v in execution.items() if k not in ('stdout', 'stderr')}
        for key in ('stdout', 'stderr'):
            if key in execution:
                raw = execution[key].encode('utf-8')
                companion['execution'][key + '_sha256'] = hashlib.sha256(raw).hexdigest()
                companion['execution'][key + '_bytes'] = len(raw)
    if 'materializer_rejection_logs' in report:
        companion['materializer_rejection_logs'] = {
            name: {'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                   'bytes': len(text.encode('utf-8'))}
            for name, text in report['materializer_rejection_logs'].items()}

    for row in report.get('lessons', []):
        recipe = {k: deepcopy(row[k]) for k in ('band', 'index', 'seed', 'sample_index', 'instance_sha256') if k in row}
        instance = row.get('instance')
        if isinstance(instance, dict) and 'accepted_pairs' in instance.get('sampling', {}):
            recipe['accepted_pairs'] = deepcopy(instance['sampling']['accepted_pairs'])
        for scope, score in [('production', row), *[('rotation', r) for r in row.get('rotations', [])]]:
            searched = score.get('searched_rivals', {})
            candidates = {name: {k: deepcopy(v) for k, v in value.items() if k != 'witness'}
                          for name, value in searched.get('candidates', {}).items()
                          if value.get('status') in ('ambiguous', 'error')}
            search_issue = candidates or searched.get('errors') or searched.get('truncated')
            if not (score.get('ambiguous') or score.get('warnings') or score.get('errors') or search_issue):
                continue
            finding = {'scope': scope, 'recipe': deepcopy(recipe)}
            for key in ('query_index', 'train_indices', 'ambiguous', 'rivals', 'warnings', 'errors', 'contract'):
                if key in score:
                    finding[key] = deepcopy(score[key])
            if search_issue:
                finding['searched_rivals'] = {k: deepcopy(v) for k, v in searched.items() if k != 'candidates'}
                finding['searched_rivals']['candidates'] = candidates
            companion['findings'].append(finding)
            # Keep one exact materialized witness per declared rival, including
            # predictions already measured by the worker. Older reports must
            # explicitly say when a prediction was not captured.
            for name, outcome in score.get('rivals', {}).items():
                key = 'declared:' + name
                if outcome != 'ambiguous' or key in companion['first_witnesses']:
                    continue
                witness = {**deepcopy(finding), 'basis': 'declared_rival'}
                if instance is not None:
                    witness['instance'] = deepcopy(instance)
                prediction = score.get('rival_witnesses', {}).get(name)
                witness['prediction_status'] = 'recorded' if prediction is not None else 'not_recorded'
                if prediction is not None:
                    witness['prediction'] = deepcopy(prediction)
                companion['first_witnesses'][key] = witness
            for name, value in searched.get('candidates', {}).items():
                key = 'searched:' + name
                if value.get('status') == 'ambiguous' and key not in companion['first_witnesses']:
                    witness = {**deepcopy(finding), 'basis': 'advisory_search'}
                    if value.get('witness') is not None:
                        witness['instance'] = deepcopy(value['witness'])
                    elif instance is not None:
                        witness['instance'] = deepcopy(instance)
                    companion['first_witnesses'][key] = witness
    return companion


def lesson_census(catalog, task_id, *, per_band=20, n_demos=None, n_queries=1,
                  period=6, bands=('easy', 'medium', 'hard'), timeout=330, rotate_query=False,
                  rotation_policy='require', rescore=None, enumerate_schedule_period=False, schedule_seed=0):
    """Return finite Racket-backed evidence; never change generator approval.

    The full manifest and each materialized instance are retained in the result.
    ``period`` is a reporting modulus, not an inferred generator contract.
    """
    for name, value in (('per_band', per_band), ('n_queries', n_queries), ('period', period)):
        if type(value) is not int or value < 1:
            raise ValueError(f'{name} must be a positive integer')
    if n_demos is not None and (type(n_demos) is not int or n_demos < 1):
        raise ValueError('n_demos must be a positive integer')
    if type(enumerate_schedule_period) is not bool:
        raise ValueError('enumerate_schedule_period must be a boolean')
    if type(schedule_seed) is not int or not 0 <= schedule_seed < 2**32:
        raise ValueError('schedule_seed must be an integer in [0, 2**32)')
    if enumerate_schedule_period and rescore is not None:
        raise ValueError('Schedule enumeration requires fresh generation, not rescore')
    if type(rotate_query) is not bool:
        raise ValueError('rotate_query must be a boolean')
    if (rotate_query or enumerate_schedule_period) and n_queries != 1:
        raise ValueError('Query rotation requires exactly one query')
    if rotation_policy not in ('require', 'diagnostic'):
        raise ValueError('rotation_policy must be require or diagnostic')
    if not bands or len(set(bands)) != len(bands) or any(b not in ('easy', 'medium', 'hard') for b in bands):
        raise ValueError('bands must be distinct easy/medium/hard values')
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError('timeout must be finite and positive')
    retained_bytes = Path(rescore).read_bytes() if rescore is not None else None
    row = catalog.describe(task_id)
    request = {'task_id': row['id'], 'per_band': per_band, 'n_demos': n_demos,
               'n_queries': n_queries, 'period': period, 'bands': list(bands), 'rotate_query': rotate_query,
               'rotation_policy': rotation_policy, 'enumerate_schedule_period': enumerate_schedule_period,
               'schedule_seed': schedule_seed}
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-lesson-census-') as directory:
        stage = Path(directory)
        manifest = prepare_runtime(catalog, stage, row['id'])
        if retained_bytes is not None:
            (stage / 'retained.json').write_bytes(retained_bytes)
            request['retained_census'] = 'retained.json'
        (stage / 'request.json').write_text(json.dumps(request))
        execution = run_process([sys.executable, '-B', 'scripts/lesson_census.py',
                                 'request.json', 'report.json'], stage, timeout=timeout)
        path = stage / 'report.json'
        report = json.loads(path.read_text()) if path.exists() else {
            'schema': 'arcpuzzles-lesson-census-v1', 'task_id': row['id'],
            'status': 'error', 'errors': ['Worker did not produce a report; inspect execution logs.']}
        expected_exit = {'no_ambiguity_found': 0, 'no_declared_ambiguity': 0, 'no_contract': 0, 'warning': 0,
                         'hook_only': 0, 'ambiguous': 1, 'error': 2}.get(report.get('status'))
        if execution['timed_out'] or expected_exit is None or execution['exit_code'] != expected_exit:
            report['status'] = 'error'
            if 'schedule_coverage' in report:
                report['schedule_coverage']['status'] = 'incomplete'
            report.setdefault('errors', []).append('Worker interrupted or failed; retained census may be partial.')
        report['runtime_manifest'] = manifest
        report['runtime_manifest_sha256'] = sha256(stage / 'RUNTIME_MANIFEST.json')
        report['controller_sha256'] = sha256(Path(__file__))
        report['execution'] = execution
        if retained_bytes is not None:
            import hashlib
            report['input_census_sha256'] = hashlib.sha256(retained_bytes).hexdigest()
            report['input_census_path'] = str(Path(rescore).resolve())
        rejected = stage / 'data/generated/.rejected'
        report['materializer_rejection_logs'] = {str(p.relative_to(stage)): p.read_text()
                                                for p in sorted(rejected.glob('*.jsonl'))} if rejected.exists() else {}
        report['catalog_provenance'] = {key: row.get(key) for key in
                                        ('approved', 'train_safety', 'rule_hash', 'family', 'split')}
        return report
