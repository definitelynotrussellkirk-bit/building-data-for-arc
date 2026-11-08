#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
SOURCE = WORK / 'repo' / 'generators' / '1a8932958b14' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_current_1a8932958b14', SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec.loader is not None
spec.loader.exec_module(module)
receipt = json.loads((HERE / 'racket-fresh.json').read_text())
inputs = json.loads((HERE / 'input.json').read_text())
pairs = [
    {'input': grid, 'output': result['output']}
    for grid, result in zip(inputs, receipt['results'])
]
demos = [pairs[0], pairs[2]]
query = pairs[1]
rivals = {}
for name in ('canonical_up_right', 'translate_modal_payload_color'):
    fn = module.SEMANTIC_RIVALS[name]
    rivals[name] = {
        'matches_all_demos': all(fn(pair['input']) == pair['output'] for pair in demos),
        'differs_on_query': fn(query['input']) != query['output'],
        'query_output': fn(query['input']),
    }
report = {
    'schema': 'arcpuzzles-audit-counterexample-v1',
    'task_id': '1a8932958b14',
    'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'rule_hash': module.RULE_HASH,
    'racket_executed_rule_hash': receipt['executed_rule_hash'],
    'seed': 20261008,
    'difficulty': 'medium',
    'sample_indices': [6, 7, 8],
    'demo_pair_indices': [0, 2],
    'query_pair_index': 1,
    'profiles': [module.semantic_profile(pair['input']) for pair in pairs],
    'validator_results': [module.self_check(pair['input']) for pair in pairs],
    'mirror_matches_racket': [module.rule_mirror(pair['input']) == pair['output'] for pair in pairs],
    'lesson_identifiable': module.lesson_identifiable(demos, query),
    'rivals': rivals,
    'command': 'python3 checks/audit/1a8932958b14/reproduce_rotation.py',
    'working_directory': str(WORK),
    'finding': 'Holding out scheduled slot 7 as query leaves slots 6 and 8 as monochrome up-right demos; both canonical-only shortcuts fit the demos and disagree on the multicolor downward query.',
}
assert all(not errors for errors in report['validator_results'])
assert all(report['mirror_matches_racket'])
assert all(item['matches_all_demos'] and item['differs_on_query'] for item in rivals.values())
assert any('canonical_up_right' in reason for reason in report['lesson_identifiable'])
assert any('translate_modal_payload_color' in reason for reason in report['lesson_identifiable'])
(HERE/'fresh_rotation_summary.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
print(json.dumps({k: report[k] for k in ('task_id','generator_sha256','rule_hash','sample_indices','demo_pair_indices','query_pair_index','profiles','validator_results','mirror_matches_racket','lesson_identifiable','rivals')}, indent=2))
