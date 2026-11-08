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
TASK = '1484fc8ec47b'
SOURCE = REPO / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_1484fc8ec47b', SOURCE)
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)
prior = json.loads((HERE / 'prior-counterexample.json').read_text())
racket = json.loads((HERE / 'racket.json').read_text())
pairs = [{'input': item['input'], 'output': item['output']} for item in racket['results']]
train_indices = prior['train_indices']
query_index = prior['query_index']
demos = [pairs[index] for index in train_indices]
query = pairs[query_index]
rival = gen.SEMANTIC_RIVALS['largest_room']
rival_output = rival(query['input'])
room_facts = []
for index, pair in enumerate(pairs):
    facts = gen.analyze_scene(pair['input'])
    largest = max(range(len(facts['rooms'])), key=lambda i: facts['rooms'][i]['area'])
    room_facts.append({
        'pair_index': index,
        'target_index': facts['target_index'],
        'largest_room_index': largest,
        'marker_counts': [room['marker_count'] for room in facts['rooms']],
        'areas': [room['area'] for room in facts['rooms']],
    })
report = {
    'schema': 'arcpuzzles-audit-counterexample-v1',
    'task_id': TASK,
    'generator_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'rule_hash': gen.RULE_HASH,
    'prior_return_used_as_lead': 'review-675f7467c23483e3:v0001',
    'prior_return_zip_sha256': '104b627085fba38b269d3d785560393eeb9278dbfc5f5070d2d6afb8f2c5c5dc',
    'seed': prior['seed'],
    'band': prior['band'],
    'lesson_index': prior['lesson_index'],
    'sample_indices': [item['sample_index'] for item in prior['accepted_pairs']],
    'train_pair_indices': train_indices,
    'query_pair_index': query_index,
    'validator_results': [gen.self_check(pair['input']) for pair in pairs],
    'racket_outputs_match_python_mirror': [gen.rule_mirror(pair['input']) == pair['output'] for pair in pairs],
    'racket_outputs_match_prior_saved_labels': [pairs[i]['output'] == prior['pairs'][i]['output'] for i in range(len(pairs))],
    'room_facts': room_facts,
    'rival': {
        'name': 'largest_room',
        'matches_all_demos': all(rival(pair['input']) == pair['output'] for pair in demos),
        'query_output': rival_output,
        'differs_on_query': rival_output != query['output'],
    },
    'lesson_identifiable': gen.lesson_identifiable(demos, query),
    'pairs': pairs,
    'finding': (
        'Under arbitrary query rotation, holding out pair 1 leaves demonstrations 0, 2, and 3. '
        'In each demonstration the maximum-marker room is also the first largest-area room, so '
        'largest_room fits every demonstration. The held-out query separates raw marker count '
        'from room area, and the rival fills a different room.'
    ),
}
(HERE / 'counterexample.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
(HERE / 'rival.json').write_text(json.dumps({
    'task_id': TASK,
    'generator_sha256': report['generator_sha256'],
    'rule_hash': report['rule_hash'],
    'authority_output': query['output'],
    'rival': 'largest_room',
    'rival_output': rival_output,
    'differs': report['rival']['differs_on_query'],
}, indent=2, sort_keys=True) + '\n')
summary = {k: report[k] for k in (
    'task_id','generator_sha256','rule_hash','seed','band','lesson_index','sample_indices',
    'train_pair_indices','query_pair_index','validator_results',
    'racket_outputs_match_python_mirror','racket_outputs_match_prior_saved_labels',
    'room_facts','rival','lesson_identifiable'
)}
print(json.dumps(summary, indent=2))
assert all(not errors for errors in report['validator_results'])
assert all(report['racket_outputs_match_python_mirror'])
assert all(report['racket_outputs_match_prior_saved_labels'])
assert report['rival']['matches_all_demos']
assert report['rival']['differs_on_query']
assert any('largest_room' in reason for reason in report['lesson_identifiable'])
