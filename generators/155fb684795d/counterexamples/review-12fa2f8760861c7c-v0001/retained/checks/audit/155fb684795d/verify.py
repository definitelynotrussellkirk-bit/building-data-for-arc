#!/usr/bin/env python3
"""Bind the retained lesson ambiguity to actual public Racket apply outputs."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import probe

folder = Path(__file__).resolve().parent


def read(name):
    return json.loads((folder / name).read_text())


def write(name, value):
    (folder / name).write_text(json.dumps(value, indent=2) + '\n')


meta = read('probe.json')
applied = read('racket.json')
inputs = read('input.json')
retained_rivals = read('rival.json')
assert applied['generator_sha256'] == meta['generator_sha256']
assert hashlib.sha256(probe.SOURCE.read_bytes()).hexdigest() == meta['generator_sha256']
assert applied['executed_rule_hash'] == meta['rule_hash']
assert applied['rule_hash_matches_catalog']
assert len(applied['results']) == len(inputs) == 4
assert all(row['valid_output'] and row['error'] is None for row in applied['results'])
assert [row['input'] for row in applied['results']] == inputs
actual = [row['output'] for row in applied['results']]
assert actual == read('diagnostic_outputs.json')
gen = probe.load()
witness = meta['witness']
regenerated = [gen.generate(witness['seed'], i, difficulty=witness['difficulty'])
               for i in witness['sample_indices']]
assert regenerated == inputs
assert all(gen.self_check(grid) == [] for grid in inputs)
rivals = [probe.rightmost_raw_unique(grid)[0] for grid in inputs]
assert retained_rivals == rivals
agreements = [truth == rival for truth, rival in zip(actual, rivals)]
assert agreements == [True, True, True, False]
lesson = [{'input': grid, 'output': truth} for grid, truth in zip(inputs, actual)]
hook = gen.lesson_identifiable(lesson[:3], lesson[3])
assert hook == []
query_actual, query_rival = actual[-1], rivals[-1]
assert len(query_actual) == len(query_rival)
assert all(len(a) == len(b) for a, b in zip(query_actual, query_rival))
differences = [{'row': r, 'column': c, 'actual': a, 'rival': b}
               for r, (left, right) in enumerate(zip(query_actual, query_rival))
               for c, (a, b) in enumerate(zip(left, right)) if a != b]
comparison = {
    'schema': 'audit-racket-lesson-ambiguity-v1', 'task_id': probe.TASK_ID,
    'status': 'reproduced', 'generator_sha256': meta['generator_sha256'],
    'executed_rule_hash': applied['executed_rule_hash'],
    'seed': witness['seed'], 'difficulty': witness['difficulty'], 'overrides': {},
    'demo_indices': witness['demo_indices'], 'query_index': witness['query_index'],
    'sample_indices': witness['sample_indices'], 'validator_errors': [[], [], [], []],
    'regenerated_inputs_match': True, 'all_racket_outputs_valid': True,
    'all_diagnostic_outputs_match_racket': True, 'rival_matches_racket': agreements,
    'native_lesson_identifiable_reasons': hook,
    'query_actual': query_actual, 'query_rival': query_rival,
    'query_different_cells': len(differences), 'query_differences_zero_based': differences,
    'input_json_sha256': hashlib.sha256((folder / 'input.json').read_bytes()).hexdigest(),
    'racket_json_sha256': hashlib.sha256((folder / 'racket.json').read_bytes()).hexdigest(),
    'rival_json_sha256': hashlib.sha256((folder / 'rival.json').read_bytes()).hexdigest(),
    'domain': 'Direct no-override ordinary generator outputs; every input passes self_check and is distinct',
    'claim': 'This canonical-fit rival agrees with three actual Racket demonstrations and disagrees on the actual Racket query',
}
write('actual_outputs.json', actual)
write('query_actual.json', query_actual)
write('comparison.json', comparison)
print(json.dumps({k: comparison[k] for k in ('status', 'generator_sha256', 'executed_rule_hash',
                                            'rival_matches_racket', 'query_different_cells',
                                            'native_lesson_identifiable_reasons')}, sort_keys=True))
