import hashlib
import importlib.util
import json
from pathlib import Path

here = Path(__file__).resolve().parent
case = json.loads((here / 'rotated-largest-room-counterexample.json').read_text())
repo = here.parents[2] / 'repo'
source = repo / 'generators' / case['task_id'] / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_1484', source)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

pairs = case['pairs']
train = [pairs[i] for i in case['train_indices']]
query = pairs[case['query_index']]
rival = gen.SEMANTIC_RIVALS['largest_room']
rival_output = rival(query['input'])
report = {
    'task_id': case['task_id'],
    'version': gen.VERSION,
    'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'train_indices': case['train_indices'],
    'query_index': case['query_index'],
    'rival_matches_all_demos': all(rival(p['input']) == p['output'] for p in train),
    'rival_differs_on_query': rival_output != query['output'],
    'lesson_identifiable': gen.lesson_identifiable(train, query),
    'demo_target_vs_largest': [],
}
for p in train:
    facts = gen.analyze_scene(p['input'])
    largest = max(range(len(facts['rooms'])), key=lambda i: facts['rooms'][i]['area'])
    report['demo_target_vs_largest'].append([facts['target_index'], largest])
facts = gen.analyze_scene(query['input'])
largest = max(range(len(facts['rooms'])), key=lambda i: facts['rooms'][i]['area'])
report['query_target_vs_largest'] = [facts['target_index'], largest]
(here / 'rival.json').write_text(json.dumps({
    'schema': 'arc-audit-rival-output-v1',
    'task_id': case['task_id'],
    'generator_sha256': report['generator_sha256'],
    'rule_hash': case['declared_rule_hash'],
    'query_index': case['query_index'],
    'authority_output': query['output'],
    'rival': 'largest_room',
    'rival_output': rival_output,
    'differs': report['rival_differs_on_query'],
}, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, indent=2))
assert report['rival_matches_all_demos']
assert report['rival_differs_on_query']
assert any('largest_room' in reason for reason in report['lesson_identifiable'])
