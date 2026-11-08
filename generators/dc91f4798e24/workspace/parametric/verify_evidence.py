#!/usr/bin/env python3
"""Reproduce bounded native/Racket teaching, export, and causal evidence.

Run through this checkout's review.py or with its src and shared/runtime on
PYTHONPATH. This tool never accepts a family or admits examples to training.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import public_challenge_bytes

TASK = 'dc91f4798e24'
HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
SEQUENTIAL = {
    'step_a': 'Discover monochromatic four-connected blue (color 1) components and count them.',
    'intermediate': 'The input-dependent integer k, the number of blue components.',
    'step_b': 'Retain each target-color component whose actual cell area is at least k; count retained components by color and draw the three-row histogram.',
    'why_b_depends_on_a': 'The size cutoff is determined by the input blue-component count, so eligibility of a red, green, or blue body cannot be selected until k is known. Replacing k changes the output on the retained witness.',
}


def _load(name):
    path = HOME / (name + '.py')
    unique = '_dc91_evidence_' + name + '_' + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(unique, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique] = module
    spec.loader.exec_module(module)
    return module


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':'),
                               allow_nan=False) + '\n', encoding='utf-8')


def visible_bytes(episode, *, query_index=None):
    """Project public bytes; one-query views never include future queries."""
    queries = episode['test']
    if query_index is not None:
        if type(query_index) is not int or not 0 <= query_index < len(queries):
            raise ValueError('query_index must name one existing query with an exact integer')
        queries = [queries[query_index]]
    return public_challenge_bytes({'train': episode['train'], 'test': queries})


def write_public(episode, directory, *, query_index=None):
    raw = visible_bytes(episode, query_index=query_index)
    path = Path(directory) / (hashlib.sha256(raw).hexdigest() + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != raw:
        raise ValueError('Existing public file differs from its content identity')
    path.write_bytes(raw)
    return path


def verify_public_file(path):
    """Reject leaked fields, malformed grids, duplicates, and wrong byte IDs."""
    path = Path(path)
    raw = path.read_bytes()
    value = json.loads(raw)
    if (type(value) is not dict or set(value) != {'train', 'test'}
            or type(value['train']) is not list or type(value['test']) is not list
            or any(type(p) is not dict or set(p) != {'input', 'output'} for p in value['train'])
            or any(type(p) is not dict or set(p) != {'input'} for p in value['test'])):
        raise ValueError('Public files may contain only visible demonstration pairs and query inputs')
    if raw != public_challenge_bytes(value):
        raise ValueError('Public bytes must use the canonical serializer')
    if path.name != hashlib.sha256(raw).hexdigest() + '.json':
        raise ValueError('Public name must be the SHA-256 of its exact visible bytes')
    inputs = [json.dumps(pair['input']) for pair in value['train'] + value['test']]
    if len(inputs) != len(set(inputs)):
        raise ValueError('Demonstration and query inputs must all be distinct')
    return {'status': 'passed', 'demos': len(value['train']), 'queries': len(value['test'])}


def _rival(*, mode, fixed=None, anchor=1, a_connectivity=4, b_connectivity=4,
           binary=False, pixels=False, blue_pixels=False, blue_largest=False,
           compare='>=', bbox=False, order=None):
    """Materialize total Racket alternatives, separate from Python diagnostics."""
    aobjs = '(objects g 0)' if a_connectivity == 4 else '(objects-8 g 0)'
    bobjs = '(objects g 0)' if b_connectivity == 4 else '(objects-8 g 0)'
    color_test = '(= (obj-color o) color)'
    if binary:
        bobjs = '(objects (grid-from-fn h w (lambda (r c) (if (= (at g r c) 0) 0 1))) 0)'
        color_test = '(ormap (lambda (rc) (= (at g (first rc) (second rc)) color)) (obj-cells o))'
    selected = f'(filter (lambda (o) (= (obj-color o) {anchor})) aobjs)'
    if fixed is not None:
        threshold = str(fixed)
    elif blue_pixels:
        threshold = f'(apply + (cons 0 (map obj-size {selected})))'
    elif blue_largest:
        threshold = f'(apply max (cons 0 (map obj-size {selected})))'
    elif mode == 'all':
        threshold = '1'
    else:
        threshold = f'(length {selected})'
    area = '(* (obj-h o) (obj-w o))' if bbox else '(obj-size o)'
    if pixels:
        count = '(apply + (cons 0 (map obj-size (filter (lambda (o) (= (obj-color o) color)) aobjs))))'
    else:
        count = f'(length (filter (lambda (o) (and {color_test} ({compare} {area} k))) bobjs))'
    counts = '(map num (list 1 2 3))'
    if order:
        counts = f'(sort {counts} {order})'
    return f'''(rule!
  (let* ((aobjs {aobjs}) (bobjs {bobjs}) (k {threshold}))
    (define (num color) {count})
    (let* ((counts {counts}) (ww (apply max (cons 1 counts))))
      (grid-from-fn 3 ww
        (lambda (r c) (if (< c (list-ref counts r)) (+ r 1) 0))))))'''


def rival_programs(mode):
    rivals = {f'fixed_cutoff_{k}': _rival(mode=mode, fixed=k) for k in range(1, 10)}
    rivals.update({
        'pixel_histogram': _rival(mode=mode, pixels=True),
        'eight_neighbor_A_only': _rival(mode=mode, a_connectivity=8),
        'eight_neighbor_B_only': _rival(mode=mode, b_connectivity=8),
        'eight_neighbor_A_and_B': _rival(mode=mode, a_connectivity=8, b_connectivity=8),
        'binary_foreground_B': _rival(mode=mode, binary=True),
        'sort_counts_ascending': _rival(mode=mode, order='<'),
        'sort_counts_descending': _rival(mode=mode, order='>'),
    })
    if mode != 'all':
        rivals.update({
            'red_component_gate': _rival(mode=mode, anchor=2),
            'green_component_gate': _rival(mode=mode, anchor=3),
            'blue_pixel_gate': _rival(mode=mode, blue_pixels=True),
            'largest_blue_area_gate': _rival(mode=mode, blue_largest=True),
            'strictly_greater_gate': _rival(mode=mode, compare='>'),
            'at_most_gate': _rival(mode=mode, compare='<='),
            'bounding_box_area_gate': _rival(mode=mode, bbox=True),
        })
    return rivals


def audit(output):
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_worker import evaluate_contract, _local_imports, _real_evaluator

    out = Path(output).resolve()
    if out.exists():
        raise ValueError('Use a new evidence directory')
    adapter, prototype = _load('adapter'), _load('prototype')
    contract = json.loads((HOME / 'promotion.json').read_text())
    jobs = [{'seed': seed, 'settings': {'mode': mode}, 'demos': demos, 'queries': 4}
            for seed in (0, 17) for demos in (2, 6)
            for mode in ('all', 'blue_count_threshold')]
    execution = evaluate_contract(ROOT, TASK, contract, jobs)
    out.mkdir(parents=True)
    _write(out / 'native-execution.json', execution)
    catalog_row = Catalog(ROOT).describe(TASK)
    report = {'schema': 'dc91-parametric-teaching-and-export-v1', 'status': 'passed',
              'task_id': TASK, 'racket': execution['racket'],
              'generator_sha256': catalog_row['generator_sha256'],
              'canonical_rule_hash': catalog_row['rule_hash'],
              'native_jobs': len(jobs), 'native_racket_evaluations': execution['racket_evaluations'],
              'labels_checked': sum(row['label_count'] for row in execution['checks']),
              'teaching_checks': [], 'size_profiles': [], 'public_files': [],
              'findings': [], 'training_admitted': False,
              'limits': 'Finite declared-rival checks on the recorded seeds. No universal identifiability, owner acceptance, or measured learning-benefit claim.'}
    runtime = ROOT / 'shared/runtime'
    with _local_imports(runtime, HOME):
        apply, identity, bridge = _real_evaluator(runtime)
        cache, evaluations = {}, 0
        def execute(program, grid):
            nonlocal evaluations
            key = (program, json.dumps(grid, separators=(',', ':')))
            if key not in cache:
                cache[key] = apply(program, grid)
                evaluations += 1
            return cache[key]
        try:
            for episode in execution['episodes']:
                mode = episode['settings']['mode']
                record = {'seed': episode['seed'], 'demos': len(episode['train']),
                          'settings': episode['settings'], 'rivals': []}
                # Extra demonstrations share the same first two teaching examples.
                for name, candidate in rival_programs(mode).items():
                    predictions = [execute(candidate, pair['input']) for pair in episode['train'][:2]]
                    mismatches = [i for i, (prediction, pair) in enumerate(zip(predictions, episode['train'][:2]))
                                  if prediction != pair['output']]
                    row = {'name': name, 'program_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
                           'demo_mismatches': mismatches}
                    if not mismatches:
                        differences = [i for i, pair in enumerate(episode['test'])
                                       if execute(candidate, pair['input']) != pair['output']]
                        row['query_disagreements'] = differences
                        if differences:
                            report['findings'].append({'seed': episode['seed'], 'mode': mode,
                                'rival': name, 'query_indices': differences,
                                'reason': 'Wrong rule fits both teaching demonstrations and changes a query.'})
                    record['rivals'].append(row)
                report['teaching_checks'].append(record)
                public_path = write_public(episode, out / 'public')
                verify_public_file(public_path)
                report['public_files'].append(public_path.name)
                public = json.loads(public_path.read_bytes())
                if set(public) != {'train', 'test'} or any(set(pair) != {'input'} for pair in public['test']):
                    raise AssertionError('Public query labels or metadata leaked')
                altered = copy.deepcopy(episode)
                altered.update(seed=999, settings={'private': 'changed'}, program='changed')
                altered['test'][0]['output'] = [[0]]
                assert visible_bytes(altered) == visible_bytes(episode)
                single = adapter.generate(episode['seed'], episode['settings'], len(episode['train']), 1)
                assert visible_bytes(single, query_index=0) == visible_bytes(episode, query_index=0)
                assert len(json.loads(visible_bytes(episode, query_index=0))['test']) == 1
                for pair in episode['test']:
                    stats = prototype.grid_stats(pair['input'])
                    stats.update(seed=episode['seed'], settings=episode['settings'])
                    report['size_profiles'].append(stats)
            report['rival_racket_evaluations'] = evaluations
            report['rival_programs'] = {mode: rival_programs(mode)
                                       for mode in ('all', 'blue_count_threshold')}
            # A concrete small causal case is saved here; source binding is added
            # only by the witness subcommand after native qualification exists.
            example = next(e for e in execution['episodes'] if e['settings']['mode'] == 'blue_count_threshold')
            pair = example['train'][0]
            counterfactual = _rival(mode='blue_count_threshold', fixed=3)
            changed = execute(counterfactual, pair['input'])
            if changed == pair['output']:
                raise AssertionError('Forced wrong threshold did not change the causal witness')
            report['causal_case'] = {'input': pair['input'], 'settings': example['settings'],
                'intermediate_value': len(prototype.components(pair['input'], 1)),
                'program': example['program'], 'output': pair['output'],
                'counterfactual_program': counterfactual, 'counterfactual_output': changed,
                'ablation': 'wrong_intermediate'}
        finally:
            bridge.close()
    matched = 0
    for seed in (0, 17):
        for demos in (2, 3, 4, 5, 6):
            first = adapter.generate(seed, {'mode': 'all'}, demos, 4)
            second = adapter.generate(seed, {'mode': 'blue_count_threshold'}, demos, 4)
            assert [p['input'] for p in first['train'] + first['test']] == [p['input'] for p in second['train'] + second['test']]
            matched += 2
    report['bounded_generation'] = {'attempted_requests': 2 * len(jobs) + matched,
        'successful_requests': 2 * len(jobs) + matched, 'failed_requests': 0,
        'demos_tested': [2, 3, 4, 5, 6], 'queries_tested': [1, 4],
        'input_matching_across_settings': True,
        'note': 'Request success, not internal placement-attempt yield; the sampler bounds internal retries.'}
    report['export_checks'] = {'private_metadata_and_answers_do_not_change_public_id': True,
        'first_turn_identical_to_single_query': True, 'one_query_view_has_no_future_query': True}
    if report['findings']:
        report['status'] = 'failed'
    _write(out / 'report.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'native_jobs', 'labels_checked', 'bounded_generation', 'findings')}, indent=2))
    return 0 if report['status'] == 'passed' else 1


def witness(qualification, evidence, output):
    from arcpuzzles.catalog import Catalog
    from arcpuzzles.parametric_promotion import _ready, _raw
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    q = json.loads(Path(qualification).read_text())
    report = json.loads(Path(evidence).read_text())
    if (q.get('schema') != 'arcpuzzles-parametric-qualification-v1'
            or q.get('status') != 'qualified' or q.get('task_id') != TASK
            or report.get('status') != 'passed'):
        raise ValueError('Need an actual native qualification and passing Racket evidence')
    contract, binding = _ready(Catalog(ROOT), TASK)
    if q.get('source_binding') != binding or q.get('contract') != contract:
        raise ValueError('Qualification source binding or contract differs from the live source')
    if (report.get('racket', {}).get('backend') != 'racket'
            or report.get('racket', {}).get('protected') is not True):
        raise ValueError('Witness requires protected Racket evidence')
    case = report['causal_case']
    adapter = _load('adapter')
    if adapter.program(case['settings']) != case['program']:
        raise ValueError('The executed witness program differs from the current adapter')
    setting_key = _raw(case['settings']).decode().strip()
    if q.get('programs', {}).get(setting_key) != hashlib.sha256(case['program'].encode()).hexdigest():
        raise ValueError('The witness setting and exact program are not in this qualification')
    runtime = ROOT / 'shared/runtime'
    with _local_imports(runtime, HOME):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            actual = apply(case['program'], case['input'])
            changed = apply(case['counterfactual_program'], case['input'])
            if actual != case['output'] or changed != case['counterfactual_output'] or actual == changed:
                raise ValueError('Fresh protected-Racket causal replay disagrees with the retained labels')
        finally:
            bridge.close()
    result = {'schema': 'arcpuzzles-sequential-dependency-witness-v1',
              'source_binding': q['source_binding'],
              # The admission wire contract requires exactly these two keys.
              # Preserve the complete measured identity separately.
              'racket': {key: identity[key] for key in ('backend', 'protected')},
              'racket_identity': identity,
              **SEQUENTIAL, 'cases': [case]}
    path = Path(output)
    if path.exists():
        raise ValueError('Use a new witness destination')
    _write(path, result)
    print(json.dumps({'status': 'written', 'cases': 1, 'path': str(path)}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    audit_parser = commands.add_parser('audit')
    audit_parser.add_argument('--out', required=True)
    witness_parser = commands.add_parser('witness')
    witness_parser.add_argument('--qualification', required=True)
    witness_parser.add_argument('--evidence', required=True)
    witness_parser.add_argument('--out', required=True)
    args = parser.parse_args()
    if args.command == 'audit':
        return audit(args.out)
    return witness(args.qualification, args.evidence, args.out)


if __name__ == '__main__':
    raise SystemExit(main())
