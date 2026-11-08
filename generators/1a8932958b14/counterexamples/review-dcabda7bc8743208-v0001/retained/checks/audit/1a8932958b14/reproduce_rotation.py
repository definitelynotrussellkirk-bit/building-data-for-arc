#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
REPO = PACKET / 'repo'
TASK = '1a8932958b14'
SOURCE = REPO / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_1a8932958b14', SOURCE)
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)
racket = json.loads((HERE / 'racket.json').read_text())
pairs = [{'input': item['input'], 'output': item['output']} for item in racket['results']]
demos = [pairs[0], pairs[2]]
query = pairs[1]
rivals = {}
for name in ('canonical_up_right', 'translate_modal_payload_color'):
    fn = gen.SEMANTIC_RIVALS[name]
    rivals[name] = {
        'matches_all_demos': all(fn(pair['input']) == pair['output'] for pair in demos),
        'query_output': fn(query['input']),
        'differs_on_query': fn(query['input']) != query['output'],
    }
report = {
    'schema': 'arcpuzzles-audit-counterexample-v1',
    'task_id': TASK,
    'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'rule_hash': gen.RULE_HASH,
    'seed': 20261008,
    'difficulty': 'medium',
    'sample_indices': [6, 7, 8],
    'train_pair_indices': [0, 2],
    'query_pair_index': 1,
    'profiles': [gen.semantic_profile(pair['input']) for pair in pairs],
    'validator_results': [gen.self_check(pair['input']) for pair in pairs],
    'racket_rule_hash': racket['executed_rule_hash'],
    'racket_outputs_match_python_mirror': [
        gen.rule_mirror(pair['input']) == pair['output'] for pair in pairs
    ],
    'lesson_identifiable': gen.lesson_identifiable(demos, query),
    'rivals': rivals,
    'pairs': pairs,
    'finding': (
        'Under arbitrary query rotation, holding out schedule slot 7 leaves slots 6 and 0 as '
        'the two demonstrations. Both are monochrome up-right anchors, so both public-data '
        'shortcuts fit every demonstration and disagree on the multicolor downward query.'
    ),
}
(HERE / 'counterexample.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
(HERE / 'rival.json').write_text(json.dumps({
    'task_id': TASK,
    'generator_sha256': report['generator_sha256'],
    'rule_hash': report['rule_hash'],
    'authority_output': query['output'],
    'rivals': rivals,
}, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: report[k] for k in (
    'task_id','generator_sha256','rule_hash','sample_indices','train_pair_indices',
    'query_pair_index','profiles','validator_results','racket_outputs_match_python_mirror',
    'lesson_identifiable','rivals'
)}, indent=2))
assert all(report['racket_outputs_match_python_mirror'])
assert all(not errors for errors in report['validator_results'])
assert all(item['matches_all_demos'] and item['differs_on_query'] for item in rivals.values())
assert any('canonical_up_right' in reason for reason in report['lesson_identifiable'])
assert any('translate_modal_payload_color' in reason for reason in report['lesson_identifiable'])
