from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3] / 'repo'
TASK = '8af64ebfaf77'
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_8af', SOURCE)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def foreground_choice(grid):
    info = mod._analysis(grid)
    panels = info['panels'][1:]
    totals = [sum(v != 0 for row in p for v in row) for p in panels]
    return [row[:] for row in panels[max(range(3), key=lambda i: totals[i])]]

seed = 123
pairs = []
for index in range(5):
    grid = mod.generate(seed, index, difficulty='medium')
    pairs.append({'input': grid, 'output': mod.rule_mirror(grid)})
query_index = 1  # the schedule's only count-trap pair in indices 0..4
query = pairs[query_index]
demos = [p for i,p in enumerate(pairs) if i != query_index]
report = {
    'task_id': TASK,
    'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'seed': seed,
    'sample_indices': list(range(5)),
    'query_index': query_index,
    'query_generated_call': {'seed': seed, 'sample_index': query_index, 'difficulty': 'medium', 'overrides': {}},
    'query_self_check': mod.self_check(query['input']),
    'query_in_documented_generator_domain': mod.self_check(query['input']) == [],
    'observed': [mod.observe_overrides(p['input']) for p in pairs],
    'lesson_identifiable': mod.lesson_identifiable(demos, query),
    'foreground_rule_fits_all_demos': all(foreground_choice(p['input']) == p['output'] for p in demos),
    'foreground_rule_changes_query': foreground_choice(query['input']) != query['output'],
    'query_input': query['input'],
    'canonical_query_output': query['output'],
    'foreground_query_output': foreground_choice(query['input']),
    'differing_query_cells': sum(
        left != right
        for canonical_row, rival_row in zip(query['output'], foreground_choice(query['input']))
        for left, right in zip(canonical_row, rival_row)
    ),
}
assert report['foreground_rule_fits_all_demos']
assert report['foreground_rule_changes_query']
assert any('most_foreground_panel' in x for x in report['lesson_identifiable'])
print(json.dumps(report, indent=2, sort_keys=True))
