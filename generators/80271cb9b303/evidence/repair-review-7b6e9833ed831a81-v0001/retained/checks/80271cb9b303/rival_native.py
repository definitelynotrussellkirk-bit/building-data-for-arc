#!/usr/bin/env python3
"""Eight retained inputs only: native parity for the longest-period rival."""
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1] / 'repo'
sys.path.insert(0, str(ROOT / 'shared/runtime'))
from reviewer_support import canonical_pairs, canonical_path
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

TASK = '80271cb9b303'
prior_path = HERE / 'result.json'
prior = json.loads(prior_path.read_text())
source_path = ROOT / 'generators' / TASK / 'generator.py'
source_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
assert source_hash == prior['generator_sha256']
canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
rows = []
for line in canonical_path(ROOT).read_text().splitlines():
    row = json.loads(line)
    if row.get('task_id') == TASK:
        rows.append(row)
assert len(rows) == 1
original = rows[0]['program_solution']
assert hashlib.sha256(original.encode()).hexdigest() == prior['rule_exact_sha256']
old = '(range 1 (+ R 2))'
new = '(append (reverse (range 1 (+ R 1))) (list (+ R 1)))'
assert original.count(old) == 1
rival_program = original.replace(old, new)

def python_rival(grid):
    output = [row[:] for row in grid]
    for r, row in enumerate(grid):
        nonzero = [c for c, value in enumerate(row) if value]
        if not nonzero:
            continue
        right = nonzero[-1]
        periods = [p for p in range(1, right + 1)
                   if all(row[c] == row[c % p] for c in range(right + 1))]
        period = max(periods) if periods else right + 1
        output[r] = [row[c % period] for c in range(len(row))]
    return output

witness = prior['witnesses']['longest_repeated_period']
inputs = [('canonical', i, pair) for i, pair in enumerate(canonical)]
inputs.extend(('longest_repeated_period', i, pair)
              for i, pair in enumerate([*witness['demos'], witness['query']]))
assert len(inputs) == 8
prior_native = {(row['context'], row['index']): row for row in prior['native_checks']}
report = {
    'schema': 'bounded-peer-native-rival-parity-v1',
    'assignment_id': 'review-7b6e9833ed831a81', 'task_id': TASK,
    'generator_sha256': source_hash,
    'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'prior_report_path': 'checks/80271cb9b303/result.json',
    'prior_report_sha256': hashlib.sha256(prior_path.read_bytes()).hexdigest(),
    'original_rule_exact_sha256': hashlib.sha256(original.encode()).hexdigest(),
    'rival_program_sha256': hashlib.sha256(rival_program.encode()).hexdigest(),
    'original_program': original, 'rival_program': rival_program,
    'replacement': {'from': old, 'to': new, 'count': 1},
    'scope': {'new_search': False, 'generated_grids': 0, 'native_rule_applications': 8,
              'inputs': 'four canonical pairs and four previously retained witness pairs'},
    'checks': [],
    'limits': ['The original eight authority executions remain in result.json unchanged.',
               'Only the rival program is executed here, using retained authority labels.',
               'No source/rule/index edits, no broad battery, and no acceptance claim.'],
}
with RacketBridge(timeout=10) as bridge:
    report['runtime_identity'] = bridge.runtime_identity
    for context, index, pair in inputs:
        retained = prior_native[(context, index)]
        input_hash = hashlib.sha256(json.dumps(pair['input']).encode()).hexdigest()
        assert input_hash == retained['input_sha256']
        assert retained['matches_expected'] and retained['actual_output'] == pair['output']
        expected_rival = python_rival(pair['input'])
        literal = "'(" + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in pair['input']) + ')'
        actual = bridge.eval_text(f'({wrap_rule(rival_program)} {literal})')
        report['checks'].append({'context': context, 'index': index,
            'input': pair['input'], 'input_sha256': input_hash,
            'retained_authority_output': retained['actual_output'],
            'python_rival_output': expected_rival, 'native_rival_output': actual,
            'native_matches_python_rival': actual == expected_rival,
            'rival_matches_authority': actual == retained['actual_output']})
report['native_python_parity_passed'] = all(row['native_matches_python_rival'] for row in report['checks'])
report['authority_match_vectors'] = {
    context: [row['rival_matches_authority'] for row in report['checks'] if row['context'] == context]
    for context in ('canonical', 'longest_repeated_period')}
out = HERE / 'rival-native-result.json'
out.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({'native_rule_applications': len(report['checks']),
    'native_python_parity_passed': report['native_python_parity_passed'],
    'authority_match_vectors': report['authority_match_vectors'],
    'rival_program_sha256': report['rival_program_sha256']}, indent=2))
assert report['native_python_parity_passed']
assert report['authority_match_vectors'] == {
    'canonical': [True, True, True, False],
    'longest_repeated_period': [True, True, True, False]}
