"""Check an actual exported lesson against Racket and every declared rival.

Run from the outer packet directory (authoring only, never a visible-only solve)::

    python3 review.py run python3 generators/d377a54f20c6/workspace/check_four_queries.py --task d377a54f20c6 --input ../checks/four-query.jsonl --out ../checks/four-query-check.json --demos 3 --queries 4

Accepts one JSON episode, a JSON list of episodes, or JSONL episodes. Each episode
must contain labelled train/test pairs. Exit 0 means these finite checks pass;
exit 1 means a failed gate; exit 2 means an infrastructure/contract error. The
output must be new. No source, authority, approval or training status is changed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def valid_grid(grid):
    return (isinstance(grid, list) and 0 < len(grid) <= 30
            and isinstance(grid[0], list) and 0 < len(grid[0]) <= 30
            and all(isinstance(row, list) and len(row) == len(grid[0])
                    and all(type(v) is int and 0 <= v <= 9 for v in row) for row in grid))


def parse_episodes(raw):
    try:
        value = json.loads(raw)
        episodes = value if isinstance(value, list) else [value]
    except json.JSONDecodeError:
        episodes = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not episodes or any(not isinstance(episode, dict) for episode in episodes):
        raise ValueError('Input must contain one or more episode objects')
    return episodes


def inspect_layout(episode, *, demos, queries):
    errors = []
    train, test = episode.get('train'), episode.get('test')
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError('Episode needs train and test lists')
    if len(train) != demos:
        errors.append('demo_count')
    if len(test) != queries:
        errors.append('query_count')
    for split, pairs in [('train', train), ('test', test)]:
        for index, pair in enumerate(pairs):
            if not isinstance(pair, dict) or not valid_grid(pair.get('input')):
                errors.append(f'{split}[{index}].invalid_input')
            if not isinstance(pair, dict) or not valid_grid(pair.get('output')):
                errors.append(f'{split}[{index}].missing_or_invalid_label')
    train_hashes = [digest(pair['input']) for pair in train
                    if isinstance(pair, dict) and valid_grid(pair.get('input'))]
    test_hashes = [digest(pair['input']) for pair in test
                   if isinstance(pair, dict) and valid_grid(pair.get('input'))]
    if len(set(test_hashes)) != len(test_hashes):
        errors.append('duplicate_query_input')
    if set(train_hashes) & set(test_hashes):
        errors.append('demo_query_input_reuse')
    return {'passed': not errors, 'errors': errors, 'demo_count': len(train),
            'query_count': len(test), 'distinct_demo_inputs': len(set(train_hashes)),
            'distinct_query_inputs': len(set(test_hashes)),
            'demo_input_sha256': train_hashes, 'query_input_sha256': test_hashes}


def label_mismatches(pairs, reference_outputs):
    if len(pairs) != len(reference_outputs):
        raise ValueError('Reference result count differs from pair count')
    return [i for i, (pair, output) in enumerate(zip(pairs, reference_outputs))
            if pair.get('output') != output]


def assess_predictions(demo_outputs, query_outputs, predictions):
    """Demo fit is computed solely from the demo prefix, never query labels."""
    if len(predictions) != len(demo_outputs) + len(query_outputs):
        raise ValueError('Rival prediction count differs from pair count')
    n = len(demo_outputs)
    refuting = [i for i, (got, expected) in enumerate(zip(predictions[:n], demo_outputs))
                if got != expected]
    differing = [i for i, (got, expected) in enumerate(zip(predictions[n:], query_outputs))
                 if got != expected]
    return {'fits_demonstrations': not refuting, 'refuting_demo_indices': refuting,
            'differing_query_indices': differing,
            'ambiguous_query_indices': differing if not refuting else []}


def declared_rivals(module):
    rivals, declarations = {}, {}
    for group in ('CANONICAL_SHORTCUTS', 'LESSON_COMPETITORS'):
        entries = getattr(module, group, {})
        if not isinstance(entries, dict):
            raise ValueError(f'{group} must be a name-to-callable dictionary')
        for name, rival in entries.items():
            if not isinstance(name, str) or not name or not callable(rival):
                raise ValueError(f'Invalid callable declaration in {group}: {name!r}')
            if name in rivals and rivals[name] is not rival:
                raise ValueError(f'Conflicting rival declarations: {name}')
            rivals[name] = rival
            declarations.setdefault(name, []).append(group)
    if not rivals:
        raise ValueError('No declared rivals: identifiability cannot be checked')
    return rivals, declarations


def inspect_episode(episode, *, task, demos, queries, catalog, source_hash, rivals, timeout):
    from arcpuzzles.runtime import apply_rule
    layout = inspect_layout(episode, demos=demos, queries=queries)
    result = {'layout': layout, 'passed': False, 'errors': list(layout['errors']),
              'metadata': {k: episode[k] for k in ('task_id', 'seed', 'episode_index') if k in episode}}
    if not layout['passed']:
        return result
    if episode.get('task_id', task) != task:
        result['errors'].append('episode_task_mismatch')
        return result
    provenance = episode.get('provenance', {})
    if not isinstance(provenance, dict):
        raise ValueError('Episode provenance must be an object')
    if provenance.get('generator_sha256', source_hash) != source_hash:
        result['errors'].append('exported_generator_hash_mismatch')
        return result
    pairs = episode['train'] + episode['test']
    grids = [pair['input'] for pair in pairs]
    # This is the supported authority API. The receipt includes every actual
    # input/output hash, selected source/rule hashes, and validator verdict.
    receipt = apply_rule(catalog, task, grids, check_generator_domain=True, timeout=timeout)
    result['racket_receipt'] = receipt
    if receipt['generator_sha256'] != source_hash:
        result['errors'].append('executed_generator_hash_mismatch')
    if not receipt.get('rule_hash_matches_catalog'):
        result['errors'].append('executed_rule_hash_mismatch')
    for declared in (episode.get('executed_rule_hash'), provenance.get('rule_hash'),
                     provenance.get('catalog_rule_hash')):
        if declared is not None and declared != receipt['executed_rule_hash']:
            result['errors'].append('exported_rule_hash_mismatch')
    applied = receipt['results']
    if len(applied) != len(pairs):
        raise ValueError('Racket returned an incorrect number of results')
    invalid = [i for i, row in enumerate(applied)
               if not row.get('valid_output') or row.get('error') or not valid_grid(row.get('output'))]
    domain_invalid = [i for i, row in enumerate(applied)
                      if row.get('generator_domain', {}).get('status') != 'valid']
    result['invalid_racket_pair_indices'] = invalid
    result['invalid_domain_pair_indices'] = domain_invalid
    if invalid:
        result['errors'].append('invalid_racket_output')
    if domain_invalid:
        result['errors'].append('generator_domain_not_valid')
    if invalid:
        return result
    outputs = [row['output'] for row in applied]
    mismatches = label_mismatches(pairs, outputs)
    result['label_mismatch_pair_indices'] = mismatches
    result['labels_checked'] = len(outputs)
    result['labels_exact'] = len(outputs) - len(mismatches)
    if mismatches:
        result['errors'].append('exported_label_mismatch')
    if result['errors']:
        # A label/source/domain failure cannot establish that the exported
        # demonstrations teach anything, even if corrected labels would do so.
        result['queries'] = [{'query_index': i,
                              'identifiable_against_declared_rivals': None,
                              'reason': 'source/domain/label prerequisite failed'}
                             for i in range(queries)]
        return result
    result['rivals'] = {}
    ambiguous = {i: [] for i in range(queries)}
    for name, rival in sorted(rivals.items()):
        try:
            predictions = []
            for grid in grids:
                copied = deepcopy(grid)
                predicted = rival(copied)
                if copied != grid:
                    raise ValueError('Declared rival mutates its input')
                if not valid_grid(predicted):
                    raise ValueError('Declared rival returned an invalid grid')
                predictions.append(predicted)
            verdict = assess_predictions(outputs[:demos], outputs[demos:], predictions)
            verdict['prediction_sha256'] = [digest(grid) for grid in predictions]
            if verdict['ambiguous_query_indices']:
                verdict['ambiguous_query_predictions'] = {
                    str(i): predictions[demos+i] for i in verdict['ambiguous_query_indices']}
            result['rivals'][name] = verdict
            for i in verdict['ambiguous_query_indices']:
                ambiguous[i].append(name)
        except Exception as exc:
            result['rivals'][name] = {'error': f'{type(exc).__name__}: {exc}'}
            result['errors'].append(f'rival_execution_error:{name}')
    result['queries'] = [{'query_index': i, 'ambiguous_rivals': names,
                          'identifiable_against_declared_rivals': not names
                          and not any(e.startswith('rival_execution_error:') for e in result['errors'])}
                         for i, names in ambiguous.items()]
    if any(ambiguous.values()):
        result['errors'].append('query_ambiguity')
    result['passed'] = not result['errors']
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', default='d377a54f20c6')
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--demos', type=int, default=3)
    parser.add_argument('--queries', type=int, default=4)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args(argv)
    if args.out.exists() or args.out.is_symlink():
        parser.error('--out must name a new file; keep earlier failed receipts')
    started = time.monotonic()
    report = {'schema': 'arcpuzzles-four-query-inspection-v1', 'task_id': args.task,
              'status': 'error', 'passed': False, 'expected_demos': args.demos,
              'expected_queries': args.queries, 'episodes': [], 'errors': [],
              'command': [sys.executable, *sys.argv], 'cwd': str(Path.cwd()),
              'input_path': str(args.input.resolve()),
              'limitations': 'Finite check of actual exported episodes against declared callable rivals only. '
                             'No proof against undeclared hypotheses, other seeds, rotations, or parameter settings; '
                             'passing does not approve a source or admit training data.'}
    exit_code = 2
    try:
        if args.demos < 1 or args.queries < 1 or args.demos + args.queries > 64:
            raise ValueError('Require positive demo/query counts totaling at most 64 per episode')
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError('Timeout must be finite and positive')
        from reviewer_support import find_root, load_selected_generator
        from arcpuzzles.catalog import Catalog
        root = find_root(__file__)
        module, source, source_hash = load_selected_generator(args.task, root=root)
        rivals, declarations = declared_rivals(module)
        raw = args.input.read_bytes()
        episodes = parse_episodes(raw.decode('utf-8'))
        report.update({'input_sha256': hashlib.sha256(raw).hexdigest(),
                       'generator_source': str(source.relative_to(root)),
                       'generator_sha256': source_hash, 'root': str(root),
                       'checker_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       'rival_declarations': declarations, 'rival_count': len(rivals),
                       'episode_count': len(episodes),
                       'runtime': {'python': sys.executable, 'racket_path': os.environ.get('RACKET_PATH'),
                                   'tmpdir': os.environ.get('TMPDIR')}})
        catalog = Catalog(root)
        for index, episode in enumerate(episodes):
            checked = inspect_episode(episode, task=args.task, demos=args.demos, queries=args.queries,
                                      catalog=catalog, source_hash=source_hash,
                                      rivals=rivals, timeout=args.timeout)
            checked['episode_index_in_file'] = index
            report['episodes'].append(checked)
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
            raise RuntimeError('Generator source changed during inspection')
        report['passed'] = all(item['passed'] for item in report['episodes'])
        report['status'] = 'passed' if report['passed'] else 'failed'
        report['total_labels_checked'] = sum(e.get('labels_checked', 0) for e in report['episodes'])
        report['total_labels_exact'] = sum(e.get('labels_exact', 0) for e in report['episodes'])
        report['total_queries'] = sum(e['layout']['query_count'] for e in report['episodes'])
        exit_code = 0 if report['passed'] else 1
    except Exception as exc:
        report['errors'].append(f'{type(exc).__name__}: {exc}')
        if hasattr(exc, 'run'):
            report['failed_execution_receipt'] = exc.run
    report['elapsed_seconds'] = round(time.monotonic() - started, 6)
    report['exit_code'] = exit_code
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as handle:
        json.dump(report, handle, sort_keys=True, separators=(',', ':'), allow_nan=False)
        handle.write('\n')
    print(json.dumps({'status': report['status'], 'episodes': len(report['episodes']),
                      'out': str(args.out), 'exit_code': exit_code}, sort_keys=True))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
